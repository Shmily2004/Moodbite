/**
 * DỮ LIỆU MẪU cho test hai màn "Chất lượng dữ liệu" và "Cần xử lý".
 *
 * VÌ SAO Ở `shared/test/` CHỨ KHÔNG Ở CẠNH MỘT TRONG HAI TRANG: luật FSD cấm import
 * chéo giữa hai slice cùng tầng, nên `pages/quality` không được với sang `pages/issues`
 * và ngược lại. Đặt ở `shared/` là chỗ DUY NHẤT cả hai cùng với tới được — và `steiger`
 * trong CI sẽ chặn ngay nếu ai đó thử đi tắt.
 *
 * Chỉ có DỮ LIỆU, không có `vi.mock`: mỗi file test tự dựng mock của mình, vì `vi.mock`
 * được nâng lên đầu FILE gọi nó và không dùng chung được.
 *
 * Các con số ở đây lấy từ lượt đo thật ngày 2026-09-08 (52.871 quán · 855 món) để test
 * đọc lên còn giống dữ liệu thật, không phải 1/2/3 vô nghĩa.
 */

export function mocChatLuong(ghiDe: Record<string, unknown> = {}) {
  return {
    restaurants_total: { current: 52871, baseline: null, baseline_date: null, delta: null },
    dishes_total: { current: 855, baseline: null, baseline_date: null, delta: null },
    restaurants_in_hanoi: 52871,
    restaurants_in_hanoi_percent: 100,
    completeness_percent: 88.1,
    critical: 16,
    important: 8920,
    to_review: 719,
    data_quality: [
      {
        key: 'co_ban',
        label: 'Quán có đủ thông tin cơ bản',
        description: 'Địa chỉ, khu vực, loại hình',
        covered: 46579,
        total: 52871,
        percent: 88.1,
        level: 'tot',
      },
    ],
    by_source: [{ source: 'overture', count: 48427, percent: 91.6 }],
    needs_attention: [
      {
        key: 'mon_thieu_anh',
        label: 'Món chưa có ảnh',
        description: 'Thiếu hình ảnh đại diện món',
        count: 102,
        severity: 'canh_bao',
        priority: 'can_kiem_tra',
        target_type: 'mon_an',
      },
    ],
    needs_attention_now: [
      {
        key: 'dong_tam',
        id: 'q1',
        name: 'Bún Chả Hàng Mành',
        description: 'Hoàn Kiếm',
        image_url: null,
        source_updated_at: null,
        resolved_at: null,
        resolved_by: null,
      },
    ],
    trend: [
      {
        date: '2026-09-08',
        restaurants_total: 52871,
        dishes_total: 855,
        completeness_percent: 88.1,
        critical: 16,
        important: 8920,
        to_review: 719,
      },
    ],
    resolved_today: 0,
    history_available: true,
    generated_at: '2026-09-08T02:00:00+00:00',
    ...ghiDe,
  };
}

export function mocVanDe(ghiDe: Record<string, unknown> = {}) {
  return {
    groups: [
      {
        key: 'dong_tam',
        label: 'Quán có khả năng đã đóng cửa',
        description: 'Nguồn đánh dấu đóng tạm thời',
        count: 16,
        severity: 'canh_bao',
        priority: 'nghiem_trong',
        target_type: 'quan_an',
      },
      {
        key: 'mon_thieu_anh',
        label: 'Món chưa có ảnh',
        description: 'Thiếu hình ảnh đại diện món',
        count: 102,
        severity: 'canh_bao',
        priority: 'can_kiem_tra',
        target_type: 'mon_an',
      },
    ],
    critical: 16,
    important: 8920,
    to_review: 719,
    total: 9655,
    resolved_today: 3,
    resolved_total: 12,
    can_resolve: true,
    ...ghiDe,
  };
}
