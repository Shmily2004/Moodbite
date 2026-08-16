/**
 * Quy tắc HIỂN THỊ của thực thể nhà hàng. Thuần TypeScript - không import React.
 *
 * ⚠️ Đây KHÔNG phải business logic. Nghiệp vụ (xếp hạng, chấm điểm mood, suy luận món)
 * nằm hoàn toàn ở backend - xem CLAUDE.md mục 1b. Ở đây chỉ có quy tắc TRÌNH BÀY.
 *
 * QUY ƯỚC XUYÊN SUỐT: `null` nghĩa là CHƯA CÓ DỮ LIỆU, không phải 0.
 * Không bao giờ hiện "0 sao" hay "miễn phí" cho quán thiếu dữ liệu.
 */
import type { SearchResultItem } from '@moodbite/api-client';

export function formatDistance(metres: number | null | undefined): string | null {
  if (metres == null) return null;
  if (metres < 1000) return `${metres} m`;
  return `${(metres / 1000).toFixed(1)} km`;
}

export function formatRating(
  rating: number | null | undefined,
  total: number | null | undefined,
): string {
  if (rating == null) return 'chưa có đánh giá';
  return total != null ? `${rating}★ (${total})` : `${rating}★`;
}

/** Giá là CHUỖI khoảng giá của Google Maps ("100-200 N ₫"), không phải số. */
export function formatPrice(priceRange: string | null | undefined): string | null {
  return priceRange || null;
}

const MATCH_SOURCE_LABELS: Record<string, string> = {
  name: 'tên quán',
  category: 'loại hình',
  atmosphere: 'không gian',
  review: 'đánh giá',
  semantic: 'ngữ nghĩa',
  mood: 'mức phù hợp chung',
};

/** Vì sao quán này được gợi ý - để giao diện nói thật với người dùng. */
export function describeMatchSource(source: string | null | undefined): string | null {
  if (!source) return null;
  return source
    .split('+')
    .map((part) => MATCH_SOURCE_LABELS[part] ?? part)
    .join(', ');
}

const DISH_CONFIDENCE_LABELS: Record<string, string> = {
  specific: 'khớp loại hình cụ thể của quán',
  generic_fallback: 'suy luận rộng, có thể không chính xác',
  ml: 'do mô hình dự đoán',
  unknown: 'chưa xác định',
};

/** Món ăn là SUY LUẬN từ loại hình quán, KHÔNG phải thực đơn thật. */
export function describeDishConfidence(confidence: string | null | undefined): string {
  return DISH_CONFIDENCE_LABELS[confidence ?? 'unknown'] ?? 'chưa xác định';
}

/**
 * Nhãn cụm trải nghiệm. `null` = CHƯA phân cụm (Cold Start), hiện "Đang cập nhật"
 * thay vì để trống - đúng quy ước ở đặc tả API mục 3.1.
 */
export function describeCluster(label: string | null | undefined): string {
  return label || 'Đang cập nhật';
}

export function hasCoordinates(
  item: SearchResultItem,
): item is SearchResultItem & { latitude: number; longitude: number } {
  return item.latitude != null && item.longitude != null;
}
