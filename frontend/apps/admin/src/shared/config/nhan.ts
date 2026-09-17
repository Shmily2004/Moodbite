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

export function nhanTheoMa(bang: Record<string, string>, ma: string | null | undefined): string {
  if (!ma) return '—';
  return bang[ma] ?? ma;
}
