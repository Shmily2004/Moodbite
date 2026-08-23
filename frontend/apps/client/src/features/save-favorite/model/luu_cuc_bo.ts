/**
 * Danh sách yêu thích lưu TRÊN MÁY — dùng cho KHÁCH chưa đăng nhập.
 *
 * Người đã đăng nhập dùng bảng `saved_items` ở server (xem `useFavorites`). Khách thì
 * không có tài khoản để gắn dữ liệu vào, nên vẫn phải có bản cục bộ — bỏ hẳn thì nút tim
 * trên trang chủ sẽ không bấm được cho tới khi đăng ký, và đó là bắt người dùng trả tiền
 * trước khi thấy món hàng.
 *
 * Tách thành file riêng (không nằm trong hook) để phần ĐỌC/GHI STORAGE test được mà không
 * cần dựng React, và để hook chỉ còn lo việc điều phối.
 */

const STORAGE_KEY = 'moodbite.favorites';

/** Khoá CŨ, từ thời chỉ lưu được món. Đọc để không làm mất dữ liệu của người đang dùng. */
const STORAGE_KEY_CU = 'moodbite.saved_dishes';

export type LoaiMuc = 'restaurant' | 'dish';

export interface MucYeuThich {
  itemType: LoaiMuc;
  itemId: string;
  name: string;
}

export function khoa(muc: { itemType: LoaiMuc; itemId: string }): string {
  return `${muc.itemType}:${muc.itemId}`;
}

function hop_le(x: unknown): x is MucYeuThich {
  if (!x || typeof x !== 'object') return false;
  const m = x as Record<string, unknown>;
  return (
    (m.itemType === 'restaurant' || m.itemType === 'dish') &&
    typeof m.itemId === 'string' &&
    typeof m.name === 'string'
  );
}

/**
 * Đọc danh sách cục bộ, kèm NÂNG CẤP từ khoá cũ.
 *
 * Bản trước chỉ lưu món và dùng khoá `moodbite.saved_dishes` với hình dạng
 * `{dishId, name}`. Người dùng đã lưu vài món bằng bản đó không đáng bị mất dữ liệu chỉ
 * vì ta đổi cấu trúc — đọc nốt khoá cũ và quy về hình dạng mới.
 */
export function doc_cuc_bo(): MucYeuThich[] {
  const ket_qua: MucYeuThich[] = [];
  const da_co = new Set<string>();

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const data = JSON.parse(raw);
      // localStorage do NGƯỜI DÙNG sở hữu và sửa được — không tin cấu trúc.
      if (Array.isArray(data)) {
        for (const x of data) {
          if (hop_le(x) && !da_co.has(khoa(x))) {
            da_co.add(khoa(x));
            ket_qua.push({ itemType: x.itemType, itemId: x.itemId, name: x.name });
          }
        }
      }
    }
  } catch {
    /* JSON hỏng hoặc storage bị chặn -> coi như chưa lưu gì */
  }

  try {
    const raw_cu = localStorage.getItem(STORAGE_KEY_CU);
    if (raw_cu) {
      const data = JSON.parse(raw_cu);
      if (Array.isArray(data)) {
        for (const x of data) {
          const m = x as Record<string, unknown>;
          if (typeof m?.dishId !== 'string' || typeof m?.name !== 'string') continue;
          const muc: MucYeuThich = {
            itemType: 'dish',
            itemId: m.dishId,
            name: m.name,
          };
          if (!da_co.has(khoa(muc))) {
            da_co.add(khoa(muc));
            ket_qua.push(muc);
          }
        }
      }
    }
  } catch {
    /* bỏ qua */
  }

  return ket_qua;
}

export function ghi_cuc_bo(danh_sach: MucYeuThich[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(danh_sach));
  } catch {
    // Hết dung lượng hoặc chế độ riêng tư -> vẫn đúng trong phiên này, chỉ là không nhớ.
  }
}

/** Xoá bản cục bộ sau khi đã đẩy lên server thành công. */
export function xoa_cuc_bo(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY_CU);
  } catch {
    /* bỏ qua */
  }
}
