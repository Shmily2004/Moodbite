/**
 * Ảnh đại diện: ảnh mặc định sinh sẵn + cho phép tải ảnh của mình lên.
 *
 * ⚠️ ĐÂY LÀ CHỖ NGUY HIỂM NHẤT CỦA CẢ APP VỀ MẶT BẢO MẬT.
 * Nhận file từ người lạ rồi đem hiển thị lại chính là đường vào kinh điển của tấn công
 * XSS lưu trữ: kẻ xấu tải lên một file `.svg` hay `.html` chứa `<script>`, web hiện nó ra
 * và mã đó chạy trong phiên của người khác.
 *
 * BỐN LỚP CHẶN, ĐỘC LẬP NHAU (chỉ một lớp là chưa đủ):
 *
 *   1. LỌC THEO ĐUÔI/MIME    — chỉ nhận png, jpeg, webp. TỪ CHỐI SVG dù nó cũng là ảnh:
 *                              SVG là XML, chạy được `<script>` bên trong.
 *   2. ĐỌC "SỐ MA THUẬT"     — kiểm mấy byte đầu file, vì MIME do TRÌNH DUYỆT đoán từ
 *                              đuôi file, mà đuôi thì người dùng đổi tuỳ ý. File tên
 *                              `hack.png` nhưng ruột là HTML sẽ bị chặn ở đây.
 *   3. GIẢI MÃ RỒI VẼ LẠI    — quan trọng nhất. Ảnh được `<img>` giải mã rồi VẼ LẠI vào
 *      QUA CANVAS              canvas và xuất ra PNG mới. Thứ lưu lại là PIXEL do trình
 *                              duyệt tự vẽ, KHÔNG còn một byte nào của file gốc — mọi mã
 *                              nhúng, EXIF, payload đính kèm đều biến mất.
 *   4. CHẶN KÍCH THƯỚC       — file quá lớn bị từ chối trước khi giải mã, tránh "bom nén"
 *                              (ảnh 10KB giải nén thành 40.000×40.000 điểm ảnh).
 *
 * VÌ SAO LƯU Ở TRÌNH DUYỆT, KHÔNG GỬI LÊN SERVER: backend chưa có endpoint nhận file, và
 * nhận file là mở thêm cả một mặt trận (đường dẫn lưu, chống ghi đè, phục vụ lại đúng
 * Content-Type, chống truy cập chéo...). Lưu dạng data URL trong `localStorage` thì ảnh
 * không bao giờ rời khỏi máy người dùng — an toàn nhất có thể cho một đồ án.
 */
import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'moodbite.avatar';

/** 2 MB. Ảnh đại diện thật hiếm khi quá 1 MB; lớn hơn gần như chắc chắn là nhầm hoặc phá. */
export const KICH_THUOC_TOI_DA = 2 * 1024 * 1024;

/** Cạnh dài nhất sau khi vẽ lại. 256px là quá đủ cho khung avatar 96px ở màn hình 2x. */
const CANH_TOI_DA = 256;

/** Chỉ ba định dạng ẢNH ĐIỂM (raster). SVG bị loại có chủ đích — xem ghi chú đầu file. */
const KIEU_CHO_PHEP = ['image/png', 'image/jpeg', 'image/webp'];

/** Vài byte đầu của từng định dạng. Nguồn: đặc tả của chính các định dạng đó. */
const SO_MA_THUAT: Array<{ kieu: string; byte: number[] }> = [
  { kieu: 'image/png', byte: [0x89, 0x50, 0x4e, 0x47] },              // \x89PNG
  { kieu: 'image/jpeg', byte: [0xff, 0xd8, 0xff] },                   // JPEG SOI
  { kieu: 'image/webp', byte: [0x52, 0x49, 0x46, 0x46] },             // "RIFF"
];

export class AnhKhongHopLe extends Error {}

/**
 * Đọc 12 byte đầu của file.
 *
 * `Blob.arrayBuffer()` là cách gọn nhất nhưng KHÔNG có ở Safari < 14 và ở jsdom (môi
 * trường chạy test). Thiếu đường lui thì phép kiểm số ma thuật ném TypeError, và vì hàm
 * gọi nó bọc trong try/catch nên file độc hại có thể LỌT — lỗi bảo mật im lặng. Đường lui
 * bằng `FileReader` chạy được ở mọi nơi.
 */
function doc_byte_dau(file: File): Promise<Uint8Array> {
  const dau = file.slice(0, 12);

  if (typeof dau.arrayBuffer === 'function') {
    return dau.arrayBuffer().then((buf) => new Uint8Array(buf));
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer));
    reader.onerror = () => reject(new AnhKhongHopLe('Không đọc được file.'));
    reader.readAsArrayBuffer(dau);
  });
}

/** Đối chiếu 12 byte đầu với số ma thuật của từng định dạng. */
async function kieu_that(file: File): Promise<string | null> {
  const dau = await doc_byte_dau(file);
  for (const { kieu, byte } of SO_MA_THUAT) {
    if (byte.every((b, i) => dau[i] === b)) return kieu;
  }
  return null;
}

/**
 * Vẽ lại ảnh qua canvas và xuất ra PNG. Đây là lớp chặn mạnh nhất.
 *
 * Dùng `createObjectURL` chứ không phải `readAsDataURL`: file 2MB chuyển sang base64 sẽ
 * phình lên ~2,7MB chuỗi trong bộ nhớ, trong khi object URL chỉ là một cái tham chiếu.
 * Nhớ `revokeObjectURL` nếu không sẽ rò bộ nhớ.
 */
function ve_lai(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      URL.revokeObjectURL(url);
      try {
        const ty_le = Math.min(1, CANH_TOI_DA / Math.max(img.width, img.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(img.width * ty_le));
        canvas.height = Math.max(1, Math.round(img.height * ty_le));

        const ctx = canvas.getContext('2d');
        if (!ctx) throw new AnhKhongHopLe('Trình duyệt không vẽ lại được ảnh.');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        resolve(canvas.toDataURL('image/png'));
      } catch (err) {
        reject(err instanceof Error ? err : new AnhKhongHopLe('Không xử lý được ảnh.'));
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      // Tới đây nghĩa là file qua được hai lớp đầu nhưng trình duyệt không giải mã nổi ->
      // file hỏng, hoặc là thứ giả dạng ảnh.
      reject(new AnhKhongHopLe('File này không phải ảnh hợp lệ.'));
    };

    img.src = url;
  });
}

export interface UseAvatarResult {
  /** Data URL của ảnh người dùng đã tải lên, hoặc `null` nếu đang dùng ảnh mặc định. */
  avatar: string | null;
  /** Ném `AnhKhongHopLe` kèm câu giải thích nếu file không đạt. */
  doiAvatar: (file: File) => Promise<void>;
  xoaAvatar: () => void;
}

export function useAvatar(): UseAvatarResult {
  const [avatar, setAvatar] = useState<string | null>(null);

  useEffect(() => {
    try {
      const luu = localStorage.getItem(STORAGE_KEY);
      // Chỉ nhận data URL PNG do CHÍNH TA sinh ra ở `ve_lai`. localStorage người dùng sửa
      // được, nên đây là lớp chặn cuối: dữ liệu lạ thì bỏ qua, không đem đi hiển thị.
      if (luu && luu.startsWith('data:image/png;base64,')) setAvatar(luu);
    } catch {
      /* trình duyệt chặn storage -> dùng ảnh mặc định */
    }
  }, []);

  const doiAvatar = useCallback(async (file: File) => {
    if (file.size > KICH_THUOC_TOI_DA) {
      throw new AnhKhongHopLe(
        `Ảnh lớn quá (${Math.round(file.size / 1024 / 1024)} MB). Tối đa 2 MB.`,
      );
    }
    if (!KIEU_CHO_PHEP.includes(file.type)) {
      throw new AnhKhongHopLe('Chỉ nhận ảnh PNG, JPG hoặc WEBP.');
    }
    if ((await kieu_that(file)) === null) {
      // Đuôi file nói là ảnh nhưng ruột thì không.
      throw new AnhKhongHopLe('File này không phải ảnh thật. Hãy chọn ảnh khác.');
    }

    const png = await ve_lai(file);
    setAvatar(png);
    try {
      localStorage.setItem(STORAGE_KEY, png);
    } catch {
      // Hết dung lượng localStorage -> vẫn hiện trong phiên này, chỉ là không nhớ được.
    }
  }, []);

  const xoaAvatar = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* bỏ qua */
    }
    setAvatar(null);
  }, []);

  return { avatar, doiAvatar, xoaAvatar };
}
