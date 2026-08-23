/**
 * Ngôn ngữ hiển thị — context + hook dịch.
 *
 * File nằm THẲNG trong `shared/i18n/`, không có thư mục `model/` con: ở tầng `shared`,
 * chính các thư mục con (`ui`, `lib`, `api`, `config`, `i18n`) mới là SEGMENT — tạo thêm
 * `model/` bên trong là đặt tên trùng khái niệm segment và `steiger` chặn.
 *
 * ĐẶT Ở `shared/` chứ không phải `app/`: luật import của FSD chỉ cho đi XUỐNG
 * (`app → pages → widgets → features → entities → shared`). Mọi tầng đều cần dịch chữ,
 * nên nó phải nằm ở tầng thấp nhất — để ở `app/` thì `features/` sẽ phải import ngược lên
 * và `steiger` chặn ngay.
 *
 * MẶC ĐỊNH LUÔN LÀ TIẾNG VIỆT, và CỐ Ý KHÔNG đoán theo `navigator.language`.
 *
 * Đoán theo trình duyệt nghe thì hay nhưng ở đây là sai: rất nhiều máy ở Việt Nam cài
 * Windows bản tiếng Anh, nên buổi bảo vệ đồ án có thể mở ra thành giao diện tiếng Anh mà
 * không ai kịp hiểu vì sao. Tệ hơn nữa, DỮ LIỆU vẫn là tiếng Việt (tên món, tên quán,
 * câu ngữ cảnh) — giao diện Anh + nội dung Việt là trạng thái nửa vời, xấu hơn cả hai.
 * Người dùng muốn tiếng Anh thì bấm một cái ở thanh trên, và lựa chọn đó được nhớ.
 */
import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { NGON_NGU, TU_DIEN, thay_the } from './tu_dien';
import type { Khoa, NgonNgu } from './tu_dien';

const STORAGE_KEY = 'moodbite.lang';
const MAC_DINH: NgonNgu = 'vi';

export type HamDich = (khoa: Khoa, gia_tri?: Record<string, string | number>) => string;

export interface NgonNguContext {
  ngonNgu: NgonNgu;
  doiNgonNgu: (moi: NgonNgu) => void;
  t: HamDich;
}

const Context = createContext<NgonNguContext | null>(null);

function la_ngon_ngu(gia_tri: unknown): gia_tri is NgonNgu {
  return typeof gia_tri === 'string' && (NGON_NGU as readonly string[]).includes(gia_tri);
}

/** Ngôn ngữ ban đầu. Không đọc trong render để tránh lệch giữa server và client. */
function ngon_ngu_dau(): NgonNgu {
  try {
    const luu = localStorage.getItem(STORAGE_KEY);
    if (la_ngon_ngu(luu)) return luu;
  } catch {
    /* trình duyệt chặn storage -> dùng mặc định */
  }
  return MAC_DINH;
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [ngonNgu, setNgonNgu] = useState<NgonNgu>(ngon_ngu_dau);

  useEffect(() => {
    // `<html lang>` KHÔNG phải trang trí: trình đọc màn hình dựa vào nó để chọn giọng
    // đọc, và trình duyệt dựa vào nó để đề nghị dịch trang. Sai thuộc tính này thì người
    // dùng trình đọc màn hình nghe tiếng Việt bằng giọng Anh.
    document.documentElement.lang = ngonNgu;
  }, [ngonNgu]);

  const doiNgonNgu = useCallback((moi: NgonNgu) => {
    setNgonNgu(moi);
    try {
      localStorage.setItem(STORAGE_KEY, moi);
    } catch {
      /* vẫn đổi trong phiên này, chỉ là không nhớ được */
    }
  }, []);

  const t = useCallback<HamDich>(
    (khoa, gia_tri) => {
      // `?? khoa`: thiếu bản dịch thì hiện CHÍNH KHOÁ chứ không hiện chuỗi rỗng. Chuỗi
      // rỗng làm chữ biến mất và không ai biết vì sao; khoá lộ ra thì thấy ngay.
      const mau = TU_DIEN[ngonNgu][khoa] ?? TU_DIEN[MAC_DINH][khoa] ?? khoa;
      return thay_the(mau, gia_tri);
    },
    [ngonNgu],
  );

  return (
    <Context.Provider value={{ ngonNgu, doiNgonNgu, t }}>{children}</Context.Provider>
  );
}

/**
 * Dùng ở mọi component. KHÔNG ném lỗi khi thiếu provider — trả về bản tiếng Việt.
 *
 * Khác `useUserSessionContext` (ném lỗi) có chủ đích: thiếu phiên đăng nhập là lỗi lập
 * trình thật sự, còn thiếu provider ngôn ngữ chỉ khiến chữ hiện bằng tiếng Việt. Làm nổ
 * cả trang vì một câu chữ là phản ứng quá tay, và nó khiến mọi test component phải bọc
 * thêm một provider chẳng liên quan gì tới thứ đang test.
 */
export function useNgonNgu(): NgonNguContext {
  const ctx = useContext(Context);
  if (ctx !== null) return ctx;
  return {
    ngonNgu: MAC_DINH,
    doiNgonNgu: () => undefined,
    t: (khoa, gia_tri) => thay_the(TU_DIEN[MAC_DINH][khoa] ?? khoa, gia_tri),
  };
}

/** Đường tắt cho trường hợp phổ biến nhất: chỉ cần hàm dịch. */
export function useT(): HamDich {
  return useNgonNgu().t;
}
