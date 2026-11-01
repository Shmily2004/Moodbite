/**
 * Quy tắc HIỂN THỊ cho trang chi tiết quán - thuần TypeScript, không React, không nghiệp vụ.
 */
import type { RestaurantDetailData } from '@moodbite/api-client';
import { safeHttpUrl } from '@/shared/lib';

/**
 * Link CHỈ ĐƯỜNG - luôn có, kể cả 97% quán không có `google_maps_url`.
 *
 * Dùng URL công khai `google.com/maps/dir/?api=1` - đây chỉ là MỘT ĐƯỜNG LINK mở app bản
 * đồ của người dùng, không gọi API nào nên không cần key hay thẻ thanh toán (CLAUDE.md 1b).
 * Có link trang quán trên Google (quán từ Apify) thì dùng nó: mở đúng quán, kèm ảnh/review.
 */
export function linkChiDuong(
  detail: Pick<RestaurantDetailData, 'google_maps_url'>,
  toaDo: { latitude: number; longitude: number } | null,
): string | null {
  const trangQuan = safeHttpUrl(detail.google_maps_url);
  if (trangQuan) return trangQuan;
  if (!toaDo) return null;
  return `https://www.google.com/maps/dir/?api=1&destination=${toaDo.latitude},${toaDo.longitude}`;
}

export interface DongGio {
  day: string;
  hours: string;
}

/**
 * Giờ mở cửa dạng bảng (quán từ Apify: `[{day, hours}]`). Dạng khác -> `[]`.
 * Backend đã giải mã chuỗi repr Python, nhưng `opening_hours` vẫn là `unknown` trong hợp
 * đồng nên phải kiểm kiểu trước khi dùng - một bản ghi lệch không được làm sập trang.
 */
export function bangGioMoCua(raw: unknown): DongGio[] {
  if (!Array.isArray(raw)) return [];
  return raw.flatMap((dong) => {
    if (!dong || typeof dong !== 'object') return [];
    const { day, hours } = dong as Record<string, unknown>;
    return typeof day === 'string' && typeof hours === 'string' ? [{ day, hours }] : [];
  });
}

/** Tag không gian từ Apify: `[{"Thông thường": true}]` -> `["Thông thường"]`. */
export function tagKhongGian(raw: unknown, duPhong: string[]): string[] {
  const tuChiTiet = Array.isArray(raw)
    ? raw.flatMap((x) =>
        x && typeof x === 'object'
          ? Object.entries(x as Record<string, unknown>)
              .filter(([, co]) => co === true)
              .map(([ten]) => ten)
          : [],
      )
    : [];
  return tuChiTiet.length > 0 ? tuChiTiet : duPhong;
}

export interface Review {
  name: string | null;
  text: string;
  stars: number | null;
  publishedAt: string | null;
}

/**
 * Review CÓ CHỮ. Đo 2026-10-28: nhiều review Apify chỉ có số sao, `text: null` - hiện
 * chúng thành thẻ rỗng thì người đọc tưởng trang lỗi.
 */
export function reviewCoChu(raw: Array<Record<string, unknown>>): Review[] {
  return raw.flatMap((r) => {
    const text = typeof r.text === 'string' ? r.text.trim() : '';
    if (!text) return [];
    return [
      {
        name: typeof r.name === 'string' ? r.name : null,
        text,
        // `null` = không rõ số sao, KHÔNG vẽ thành 0 sao.
        stars: typeof r.stars === 'number' ? r.stars : null,
        publishedAt: typeof r.publishedAtDate === 'string' ? r.publishedAtDate : null,
      },
    ];
  });
}
