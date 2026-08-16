/**
 * Quy tắc HIỂN THỊ thuần tuý. Không import React, không gọi API.
 *
 * Quy ước xuyên suốt: null nghĩa là CHƯA CÓ DỮ LIỆU, không phải 0. Hiển thị "—" hoặc
 * "chưa có đánh giá", tuyệt đối không hiện "0 sao" hay "miễn phí".
 */

export function formatDistance(metres) {
  if (metres == null) return null
  if (metres < 1000) return `${metres} m`
  return `${(metres / 1000).toFixed(1)} km`
}

export function formatRating(rating, total) {
  if (rating == null) return 'chưa có đánh giá'
  return total != null ? `${rating}★ (${total})` : `${rating}★`
}

export function formatPrice(priceRange) {
  // price là CHUỖI khoảng giá của Google Maps ("100-200 N ₫"), không phải số.
  return priceRange || null
}

/** Giải thích vì sao quán này được gợi ý - để giao diện nói thật với người dùng. */
export function describeMatchSource(source) {
  if (!source) return null
  const labels = {
    name: 'tên quán',
    category: 'loại hình',
    atmosphere: 'không gian',
    review: 'đánh giá',
    mood: 'mức phù hợp chung',
  }
  return source
    .split('+')
    .map((s) => labels[s] || s)
    .join(', ')
}

/** Nhãn cho mức tin cậy của MÓN gợi ý. Món là suy luận, không phải thực đơn thật. */
export function describeDishConfidence(confidence) {
  switch (confidence) {
    case 'specific':
      return 'khớp loại hình cụ thể của quán'
    case 'generic_fallback':
      return 'suy luận rộng, có thể không chính xác'
    case 'ml':
      return 'do mô hình dự đoán'
    default:
      return 'chưa xác định'
  }
}
