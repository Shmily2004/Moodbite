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
import { HAM_DICH_VI } from '@/shared/i18n';
import type { HamDich, Khoa } from '@/shared/i18n';

/*
 * SONG NGỮ (2026-10-02): mọi hàm trả CHỮ nhận thêm `t` (hàm dịch) ở tham số cuối; bỏ
 * trống = tiếng Việt như trước. Luật trung thực không đổi theo ngôn ngữ: thiếu rating là
 * "chưa có đánh giá" / "No rating yet", không bao giờ là "0".
 */

export function formatDistance(metres: number | null | undefined): string | null {
  if (metres == null) return null;
  if (metres < 1000) return `${metres} m`;
  return `${(metres / 1000).toFixed(1)} km`;
}

export function formatRating(
  rating: number | null | undefined,
  total: number | null | undefined,
  t: HamDich = HAM_DICH_VI,
): string {
  if (rating == null) return t('rest.noRating');
  return total != null ? `${rating}★ (${total})` : `${rating}★`;
}

/** Giá là CHUỖI khoảng giá của Google Maps ("100-200 N ₫"), không phải số. */
export function formatPrice(priceRange: string | null | undefined): string | null {
  return priceRange || null;
}

/* ---------------------------------------------------------------------------
   MỨC PHÙ HỢP — cách trình bày `predicted_score`
   ---------------------------------------------------------------------------
   ⚠ ĐỌC KỸ TRƯỚC KHI ĐỔI. Đo thật trên 40 kết quả của 4 câu tìm kiếm:

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
  { min: 0.68, level: 'high', khoa: 'rest.fit.high' },
  { min: 0.6, level: 'mid', khoa: 'rest.fit.mid' },
  { min: 0, level: 'low', khoa: 'rest.fit.low' },
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

export function describeFit(score: number, t: HamDich = HAM_DICH_VI): FitLevel {
  const band = FIT_BANDS.find((b) => score >= b.min) ?? FIT_BANDS[FIT_BANDS.length - 1];
  const ratio = (score - BAR_MIN) / (BAR_MAX - BAR_MIN);
  return {
    level: band.level,
    label: t(band.khoa),
    // Tối thiểu 8% để thanh không biến mất hoàn toàn ở quán điểm thấp.
    barPercent: Math.round(Math.min(1, Math.max(0.08, ratio)) * 100),
  };
}

const MATCH_SOURCE_LABELS: Record<string, Khoa> = {
  name: 'rest.match.name',
  category: 'rest.match.category',
  atmosphere: 'rest.match.atmosphere',
  review: 'rest.match.review',
  semantic: 'rest.match.semantic',
  mood: 'rest.match.mood',
};

/** Mã lạ thì giữ nguyên mã — vẫn nói được gì đó thay vì im lặng. */
function nhanNguon(part: string, t: HamDich): string {
  const khoa = MATCH_SOURCE_LABELS[part];
  return khoa ? t(khoa) : part;
}

/** Vì sao quán này được gợi ý - để giao diện nói thật với người dùng. */
export function describeMatchSource(
  source: string | null | undefined,
  t: HamDich = HAM_DICH_VI,
): string | null {
  if (!source) return null;
  return source
    .split('+')
    .map((part) => nhanNguon(part, t))
    .join(', ');
}

/**
 * `kind` thay cho chuỗi emoji (đổi 2026-09-29, checklist A9): model chỉ nói LOẠI lý do,
 * còn vẽ hình gì là việc của VIEW (`RestaurantCard`) — file `.ts` này không kéo React vào.
 *   feel  = khớp không gian / cảm giác · match = khớp nội dung (tên, loại hình, đánh giá…)
 */
export type ReasonKind = 'feel' | 'match';

export interface Reason {
  kind: ReasonKind;
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
  t: HamDich = HAM_DICH_VI,
): Reason[] {
  if (!matchSource) return [];
  const parts = matchSource.split('+');
  const reasons: Reason[] = [];

  // 1. Khớp về KHÔNG GIAN / CẢM GIÁC - phần "mood" trong "Context + Mood".
  const feelParts = parts.filter((p) => p === 'atmosphere' || p === 'mood');
  if (feelParts.length > 0) {
    const query = queryText?.trim();
    reasons.push({
      kind: 'feel',
      text: query ? t('rest.reason.feelQuery', { query }) : t('rest.reason.feel'),
    });
  }

  // 2. Khớp về NỘI DUNG - tên, loại hình, đánh giá, ngữ nghĩa.
  const textParts = parts.filter(
    (p) => p === 'name' || p === 'category' || p === 'review' || p === 'semantic',
  );
  if (textParts.length > 0) {
    const labels = textParts.map((p) => nhanNguon(p, t));
    reasons.push({ kind: 'match', text: t('rest.reason.match', { labels: labels.join(', ') }) });
  }

  // Backend trả mã lạ -> vẫn nói được gì đó thay vì im lặng.
  if (reasons.length === 0) {
    const fallback = describeMatchSource(matchSource, t);
    if (fallback) reasons.push({ kind: 'match', text: t('rest.reason.match', { labels: fallback }) });
  }
  return reasons;
}

const DISH_CONFIDENCE_LABELS: Record<string, Khoa> = {
  specific: 'rest.conf.specific',
  generic_fallback: 'rest.conf.generic_fallback',
  ml: 'rest.conf.ml',
  unknown: 'rest.conf.unknown',
};

/** Món ăn là SUY LUẬN từ loại hình quán, KHÔNG phải thực đơn thật. */
export function describeDishConfidence(
  confidence: string | null | undefined,
  t: HamDich = HAM_DICH_VI,
): string {
  return t(DISH_CONFIDENCE_LABELS[confidence ?? 'unknown'] ?? 'rest.conf.unknown');
}

/**
 * Nhãn cụm trải nghiệm. `null` = CHƯA phân cụm (Cold Start), hiện "Đang cập nhật"
 * thay vì để trống - đúng quy ước ở đặc tả API mục 3.1.
 */
export function describeCluster(
  label: string | null | undefined,
  t: HamDich = HAM_DICH_VI,
): string {
  // `label` là TÊN CỤM backend đặt (dữ liệu, tiếng Việt) — chỉ chữ dự phòng mới dịch.
  return label || t('rest.cluster.pending');
}

// "Trạng thái & tuổi thật" nằm ở `freshness.ts` (tách 2026-10-06) — re-export để mọi
// nơi vẫn import từ `format` như trước.
export {
  describeFreshness,
  describeSurvey,
  describeTemporaryClosure,
  describeVerification,
  tenNenTang,
} from './freshness';
export type { Freshness } from './freshness';

export function hasCoordinates(
  item: SearchResultItem,
): item is SearchResultItem & { latitude: number; longitude: number } {
  return item.latitude != null && item.longitude != null;
}
