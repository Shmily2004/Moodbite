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

/* ---------------------------------------------------------------------------
   MỨC PHÙ HỢP — cách trình bày `predicted_score`
   ---------------------------------------------------------------------------
   ⚠️ ĐỌC KỸ TRƯỚC KHI ĐỔI. Đo thật trên 40 kết quả của 4 câu tìm kiếm:

     câu tìm                  cao nhất   thấp nhất
     quán lẩu ấm cúng gần đây   0.659      0.598
     phở bò                     0.641      0.576
     chỗ yên tĩnh để làm việc   0.658      0.594
     cà phê                     0.721      0.674

   Nghĩa là: KẾT QUẢ TỐT NHẤT cũng chỉ khoảng 0.72, trung vị 0.61.
   `predicted_score` là tổng có trọng số của 6 tín hiệu; phần lớn quán thiếu dữ liệu nên
   nhận điểm trung lập, khiến mọi điểm dồn quanh 0.6. Nó là điểm XẾP HẠNG (so quán này
   với quán kia), KHÔNG phải xác suất phù hợp.

   ⇒ Nhân 100 rồi hiện "61% phù hợp" là PHẢN TÁC DỤNG: người dùng tưởng máy gợi ý kém
   trong khi đó đúng là quán khớp nhất. Vì vậy hiện NHÃN ĐỊNH TÍNH (phương án A, chủ dự
   án chốt 2026-08-17), kèm một thanh chỉ để so sánh tương đối giữa các quán.
--------------------------------------------------------------------------- */

/** Ngưỡng chia nhãn, đặt theo phân bố đo được ở trên. */
const FIT_BANDS = [
  { min: 0.68, level: 'high', label: 'Rất phù hợp' },
  { min: 0.6, level: 'mid', label: 'Phù hợp' },
  { min: 0, level: 'low', label: 'Có thể hợp' },
] as const;

// Neo của THANH hiển thị. Điểm thực tế nằm gọn trong ~[0.55, 0.75], nên nếu vẽ thanh
// theo đúng `score` thì mọi quán đều dài xấp xỉ nhau và thanh trở nên vô nghĩa.
// Trải khoảng này ra toàn bộ chiều dài thanh để MẮT phân biệt được hơn kém.
// Đây thuần là phép co giãn HIỂN THỊ - nhãn chữ mới là phần nói thật.
const BAR_MIN = 0.5;
const BAR_MAX = 0.78;

export interface FitLevel {
  level: 'high' | 'mid' | 'low';
  label: string;
  /** 0..100 - chiều dài thanh, chỉ để so sánh tương đối. */
  barPercent: number;
}

export function describeFit(score: number): FitLevel {
  const band = FIT_BANDS.find((b) => score >= b.min) ?? FIT_BANDS[FIT_BANDS.length - 1];
  const ratio = (score - BAR_MIN) / (BAR_MAX - BAR_MIN);
  return {
    level: band.level,
    label: band.label,
    // Tối thiểu 8% để thanh không biến mất hoàn toàn ở quán điểm thấp.
    barPercent: Math.round(Math.min(1, Math.max(0.08, ratio)) * 100),
  };
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

export interface Reason {
  icon: string;
  text: string;
}

/**
 * Dịch `match_source` sang câu NGƯỜI ĐỌC HIỂU — đây là USP của MoodBite hiện ra màn hình.
 *
 * Backend đã trả sẵn lý do dưới dạng mã (`name+review`, `atmosphere+semantic`…). Nếu chỉ
 * in nguyên mã đó thì người dùng không hiểu gì. Hàm này chỉ ĐỔI CHỮ, tuyệt đối không tự
 * suy luận thêm lý do nào backend không nói - làm thế là bịa.
 *
 * Tối đa 2 dòng: nhiều hơn thì thẻ dài ra và không ai đọc.
 */
export function describeReasons(
  matchSource: string | null | undefined,
  queryText?: string | null,
): Reason[] {
  if (!matchSource) return [];
  const parts = matchSource.split('+');
  const reasons: Reason[] = [];

  // 1. Khớp về KHÔNG GIAN / CẢM GIÁC - phần "mood" trong "Context + Mood".
  const feelParts = parts.filter((p) => p === 'atmosphere' || p === 'mood');
  if (feelParts.length > 0) {
    const query = queryText?.trim();
    reasons.push({
      icon: '😌',
      text: query
        ? `Hợp với "${query}"`
        : 'Hợp về không gian và cảm giác',
    });
  }

  // 2. Khớp về NỘI DUNG - tên, loại hình, đánh giá, ngữ nghĩa.
  const textParts = parts.filter(
    (p) => p === 'name' || p === 'category' || p === 'review' || p === 'semantic',
  );
  if (textParts.length > 0) {
    const labels = textParts.map((p) => MATCH_SOURCE_LABELS[p] ?? p);
    reasons.push({ icon: '🔎', text: `Khớp ${labels.join(', ')}` });
  }

  // Backend trả mã lạ -> vẫn nói được gì đó thay vì im lặng.
  if (reasons.length === 0) {
    const fallback = describeMatchSource(matchSource);
    if (fallback) reasons.push({ icon: '🔎', text: `Khớp ${fallback}` });
  }
  return reasons;
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
