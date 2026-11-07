/**
 * NHÃN HIỂN THỊ cho các mã do backend trả về. Chỉ là quy tắc TRÌNH BÀY (CLAUDE.md mục
 * 1b) — không có quy tắc nghiệp vụ nào ở đây. Mã lạ thì hiện nguyên mã, KHÔNG đoán.
 */

/** Nguồn dữ liệu QUÁN (`restaurants.source`). */
export const NHAN_NGUON_QUAN: Record<string, string> = {
  overture: 'Overture Maps',
  openstreetmap: 'OpenStreetMap',
  google_maps_apify: 'Google Maps',
  manual: 'Nhập tay',
  admin: 'Nhập tay',
};

/** Nguồn GIỚI THIỆU MÓN (`dish.source`). */
export const NHAN_NGUON_MON: Record<string, string> = {
  wikipedia_vi: 'Wikipedia',
  wikidata: 'Wikidata',
  manual: 'Nhập tay',
  admin: 'Admin',
  seed_kb: 'Bộ luật gốc',
  dataset_ten_quan: 'Suy từ tên quán',
};

/** Cách một quán được khớp với món (`matched_by`). */
export const NHAN_CACH_KHOP: Record<string, string> = {
  dish_name: 'Tên quán ghi đúng tên món',
  name: 'Tên quán khớp từ khoá món',
  review: 'Chỉ review nhắc tới',
};

/** Loại hành động trong nhật ký tương tác (`action_type`). */
export const NHAN_HANH_DONG_TUONG_TAC: Record<string, string> = {
  view_detail: 'Xem chi tiết',
  get_directions: 'Chỉ đường',
  save: 'Lưu quán',
  explicit_positive: 'Thích',
  explicit_negative: 'Không thích',
  report_closed: 'Báo đã đóng cửa',
};

/**
 * Thuộc tính món — mã do backend đặt ở `src/domain/entities/dish.py` (danh sách đóng).
 * Admin đọc "nuoc", "sang, trua" thì phải tự dịch trong đầu; bảng này chỉ đổi CÁCH HIỆN.
 */
export const NHAN_NHIET_DO_MON: Record<string, string> = {
  hot: 'Nóng',
  cold: 'Lạnh',
  room: 'Nhiệt độ phòng',
  neutral: 'Không rõ nóng/lạnh',
};

export const NHAN_CACH_CHE_BIEN: Record<string, string> = {
  nuong: 'Nướng',
  chien: 'Chiên / rán',
  luoc: 'Luộc',
  hap: 'Hấp',
  xao: 'Xào',
  nuoc: 'Món nước',
  song: 'Gỏi / sống',
  tron: 'Trộn / nộm',
  nuong_lo: 'Nướng lò',
};

export const NHAN_BUA_AN: Record<string, string> = {
  sang: 'Sáng',
  trua: 'Trưa',
  toi: 'Tối',
  khuya: 'Khuya',
  an_vat: 'Ăn vặt',
};

/** Mức ưu tiên của nhóm vấn đề. Khoá do backend đặt (`domain/services/data_issues.py`). */
export const NHAN_UU_TIEN_VAN_DE: Record<string, string> = {
  nghiem_trong: 'Nghiêm trọng',
  quan_trong: 'Quan trọng',
  can_kiem_tra: 'Cần kiểm tra',
};

export function nhanTheoMa(bang: Record<string, string>, ma: string | null | undefined): string {
  if (!ma) return '—';
  return bang[ma] ?? ma;
}
