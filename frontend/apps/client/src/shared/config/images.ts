/**
 * KHAI BÁO HÌNH ẢNH CỦA GIAO DIỆN — một chỗ duy nhất.
 *
 * ==========================================================================
 * CHỖ NÀY DÀNH CHO ẢNH NÀO
 *
 *   ✅ Ảnh của BỘ GIAO DIỆN: logo, ảnh bìa đầu trang, hình minh hoạ lúc không
 *      có kết quả, ảnh nền, biểu tượng riêng.
 *   ✅ Ảnh DỰ PHÒNG khi API không có ảnh thật (xem `ANH_DU_PHONG` bên dưới).
 *
 *   ❌ Ảnh của MỘT MÓN cụ thể  -> API trả về ở `dish.image_url` (87,1% món có).
 *   ❌ Ảnh của MỘT QUÁN cụ thể -> API trả về ở `restaurant.thumbnail_url` (28,2%).
 *
 * Vì sao gạch hai dòng cuối: khai ảnh món/quán ở đây là tạo NƠI THỨ HAI chứa
 * cùng một dữ liệu. Ảnh trong dataset đổi thì file này không đổi theo, và sẽ
 * có lúc màn hình hiện ảnh cũ mà không ai biết vì sao. Đây đúng là kiểu lỗi
 * "hai nguồn sự thật" mà dự án đã trả giá ở cả backend lẫn frontend.
 *
 * ==========================================================================
 * CÁCH THÊM MỘT TẤM ẢNH (chủ dự án)
 *
 *   Cách 1 — ảnh để trong máy (khuyên dùng):
 *     1. Chép file ảnh vào thư mục `frontend/apps/client/public/anh/`
 *        (chưa có thì tạo mới, tên thư mục viết đúng như trên).
 *     2. Khai ở dưới với `src: '/anh/ten-file.jpg'` — bắt đầu bằng dấu `/`.
 *
 *   Cách 2 — ảnh trên mạng:
 *     `src: 'https://.../anh.jpg'`, và BẮT BUỘC ghi `credit` cho biết ảnh của ai.
 *
 * ⚠️ ẢNH LẤY TRÊN MẠNG PHẢI GHI NGUỒN + GIẤY PHÉP ở trường `credit`.
 *    Đồ án tốt nghiệp không nên dùng ảnh không rõ bản quyền — đây là chỗ dễ bị
 *    hỏi nhất khi bảo vệ. Nguồn dùng được miễn phí: Wikimedia Commons,
 *    Unsplash, Pexels (đọc kỹ điều khoản từng ảnh).
 *
 * ⚠️ Sai tên file thì trình duyệt chỉ lặng lẽ hiện ô vỡ. Vì vậy MỌI chỗ dùng
 *    ảnh trong app đều phải có bản thay thế khi ảnh hỏng — xem `RestaurantThumb`
 *    và `DishThumb` đã làm sẵn.
 * ==========================================================================
 */

/** Thuộc tính đầy đủ của một tấm ảnh trong giao diện. */
export interface AnhUI {
  /** Đường dẫn. Ảnh trong máy: `/anh/ten.jpg`. Ảnh mạng: `https://...`. */
  src: string;
  /**
   * Chữ thay ảnh cho người dùng trình đọc màn hình.
   *
   * Chuỗi RỖNG là hợp lệ và có nghĩa riêng: "ảnh chỉ để trang trí, bỏ qua cũng
   * không mất thông tin gì". Đừng viết `alt="hình ảnh"` — nó ồn mà vô nghĩa.
   */
  alt: string;
  /**
   * Kích thước gốc tính bằng pixel. Khai vào thì trình duyệt chừa sẵn chỗ, trang
   * không bị NHẢY khi ảnh tải xong. Không biết thì bỏ trống.
   */
  width?: number;
  height?: number;
  /** `cover` = lấp đầy khung, có thể bị cắt · `contain` = thấy trọn ảnh, có viền thừa. */
  fit?: 'cover' | 'contain';
  /** Phần nào của ảnh được giữ lại khi bị cắt. VD `'center'`, `'50% 30%'`. */
  position?: string;
  /**
   * Bản dùng cho NỀN TỐI. App tự đổi màu theo cài đặt máy, nên logo nền trắng
   * sẽ biến mất trên nền tối. Không khai thì dùng chung `src`.
   */
  srcDark?: string;
  /** Nguồn + giấy phép. BẮT BUỘC với ảnh không phải tự chụp/tự vẽ. */
  credit?: string;
}

/**
 * Ảnh của bộ giao diện.
 *
 * `null` = CHƯA CÓ ẢNH, và phải để `null` chứ đừng trỏ tới file không tồn tại.
 * Component đọc thấy `null` sẽ vẽ bản thay thế; trỏ sai đường dẫn thì nó tưởng
 * có ảnh rồi hiện ô vỡ — tệ hơn hẳn.
 */
export const ANH_GIAO_DIEN: Record<string, AnhUI | null> = {
  /** Logo ở góc trái header. */
  logo: null,

  /** Ảnh bìa đầu trang chủ, phía trên lưới món. */
  bia_trang_chu: null,

  /** Hình minh hoạ khi tìm không ra quán nào. */
  khong_co_ket_qua: null,

  /** Hình minh hoạ khi mất mạng / backend không trả lời. */
  loi_ket_noi: null,

  /** Ảnh nền trang đăng nhập (nếu sau này làm giao diện tài khoản). */
  nen_dang_nhap: null,
};

/**
 * Ảnh DỰ PHÒNG theo loại hình quán — chỉ dùng khi API KHÔNG có ảnh thật.
 *
 * VÌ SAO CẦN: 71,8% quán không có ảnh. Hiện tại chỗ đó vẽ ô màu sinh từ tên quán
 * kèm một emoji (`RestaurantThumb`), trông ổn và KHÔNG tốn gì. Đây chỉ là lối mở
 * sẵn nếu chủ dự án muốn thay bằng ảnh thật.
 *
 * ⚠️ ĐỌC KỸ TRƯỚC KHI DÙNG: ảnh dự phòng đẹp rất dễ bị người dùng hiểu là ẢNH
 * CHỤP QUÁN ĐÓ. Một tấm ảnh phở lung linh gắn cho quán ta chưa từng thấy mặt
 * chính là "bịa dữ liệu" bằng hình ảnh. Nếu bật phần này thì giao diện PHẢI nói
 * rõ đây là ảnh minh hoạ, y như cách nhãn tin cậy của món đang làm.
 *
 * Khoá là từ khoá xuất hiện trong tên hoặc loại hình quán, viết thường không dấu.
 */
export const ANH_DU_PHONG: Record<string, AnhUI> = {
  // Ví dụ cách khai — bỏ dấu `//` và sửa lại là dùng được:
  //
  // pho: {
  //   src: '/anh/du-phong/pho.jpg',
  //   alt: '',                       // trang trí -> để rỗng
  //   fit: 'cover',
  //   credit: 'Wikimedia Commons, CC BY-SA 4.0',
  // },
};

/**
 * Chọn ảnh dự phòng theo tên + loại hình quán.
 *
 * Đây là quy tắc HIỂN THỊ, không phải nghiệp vụ: nó không đổi thứ tự kết quả,
 * không lọc bỏ quán nào. Cùng loại với bảng emoji đã có sẵn trong `RestaurantThumb`.
 *
 * Chưa khai ảnh nào thì trả `null` và mọi thứ chạy y như cũ.
 */
export function anhDuPhongCho(
  name: string,
  category?: string | null,
  /** Chỉ để TEST truyền bảng giả vào. Chạy thật luôn dùng `ANH_DU_PHONG`. */
  bang: Record<string, AnhUI> = ANH_DU_PHONG,
): AnhUI | null {
  const khoa = Object.keys(bang);
  if (khoa.length === 0) return null;

  // Bỏ dấu tiếng Việt trước khi so khớp: quán tên "Phở Bò" và "Pho Bo" phải ra
  // cùng một kết quả. Đây là bài học đã trả giá ở backend - xem CLAUDE.md mục 4.
  const canhTim = boDau(`${name} ${category ?? ''}`);
  const timDuoc = khoa.find((k) => canhTim.includes(boDau(k)));
  return timDuoc ? bang[timDuoc] : null;
}

/**
 * Bỏ dấu tiếng Việt và hạ về chữ thường.
 *
 * Khoảng dấu thanh viết bằng MÃ (`\u0300-\u036f`) chứ không gõ thẳng ký tự: dấu tổ hợp
 * là ký tự VÔ HÌNH, dán thẳng vào mã nguồn thì lần sau mở file ra chỉ thấy hai ngoặc
 * vuông trống rỗng và không ai dám sửa. `đ` phải xử lý riêng vì NFD không tách nó ra
 * thành chữ + dấu.
 */
function boDau(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd');
}
