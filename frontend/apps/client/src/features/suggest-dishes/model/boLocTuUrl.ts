/**
 * Đổi qua lại giữa BỘ LỌC và QUERY STRING.
 *
 * VÌ SAO ĐỂ BỘ LỌC TRÊN URL thay vì giữ trong bộ nhớ:
 *   1. Chia sẻ được — gửi bạn bè đúng danh sách mình đang xem.
 *   2. F5 không mất lựa chọn.
 *   3. Nút Back của trình duyệt hoạt động đúng thay vì nhảy thẳng về trang chủ.
 *   4. Bộ lọc THEO ĐƯỢC từ trang chủ sang đây — trang chủ chỉ cần dựng đường dẫn.
 * Cùng lý do đã chọn cho tab ở trang tài khoản (`?tab=saved`).
 *
 * ⚠️ ĐẶT Ở `features`, KHÔNG PHẢI `pages`. Bản đầu để trong `pages/recommend/`, nhưng
 * trang chủ cũng cần nó để dựng đường dẫn "Xem tất cả" — mà luật FSD CẤM page import
 * page. Nó thuộc về bộ lọc món, nên chỗ đúng là ở đây.
 *
 * ⚠️ MÃ TRÊN URL LÀ MÃ BACKEND ('nuong', 'toi', 'rain'), không phải nhãn tiếng Việt.
 * Nhãn chỉ nằm ở `DishFilters`. Nếu đưa nhãn lên URL thì đổi chữ hiển thị sẽ làm chết
 * mọi đường dẫn đã chia sẻ.
 */
import type { DishFilterState } from './useDishSuggestions';

/** Tên tham số trên URL -> nhóm lọc. Ngắn gọn vì nó hiện trên thanh địa chỉ. */
const NHOM_NHIEU = {
  cach: 'cookingMethods',
  nhiet: 'temperatures',
  bua: 'mealTimes',
  am_thuc: 'cuisines',
} as const;

export function docBoLocTuUrl(params: URLSearchParams): Partial<DishFilterState> {
  const ket_qua: Partial<DishFilterState> = {};

  for (const [khoa, nhom] of Object.entries(NHOM_NHIEU)) {
    const gia_tri = params.get(khoa);
    if (gia_tri) {
      // `filter(Boolean)` để "a,,b" không sinh ra một giá trị rỗng — backend sẽ coi
      // chuỗi rỗng là một mã lọc không tồn tại rồi trả 400.
      (ket_qua as Record<string, unknown>)[nhom] = gia_tri.split(',').filter(Boolean);
    }
  }

  const mood = params.get('mood');
  if (mood) ket_qua.mood = mood;
  const thoi_tiet = params.get('thoi_tiet');
  if (thoi_tiet) ket_qua.weather = thoi_tiet;

  const km = params.get('km');
  if (km !== null) {
    // `km=` (rỗng) nghĩa là NGƯỜI DÙNG CHỌN "không giới hạn" — khác hẳn với không có
    // tham số `km` (chưa chọn gì, dùng mặc định).
    ket_qua.maxDistanceKm = km === '' ? null : Number(km);
  }

  return ket_qua;
}

export function ghiBoLocLenUrl(filters: DishFilterState): URLSearchParams {
  const params = new URLSearchParams();

  for (const [khoa, nhom] of Object.entries(NHOM_NHIEU)) {
    const gia_tri = filters[nhom];
    if (gia_tri.length) params.set(khoa, gia_tri.join(','));
  }
  if (filters.mood) params.set('mood', filters.mood);
  if (filters.weather) params.set('thoi_tiet', filters.weather);
  if (filters.maxDistanceKm === null) params.set('km', '');
  else if (filters.maxDistanceKm !== undefined) params.set('km', String(filters.maxDistanceKm));

  return params;
}
