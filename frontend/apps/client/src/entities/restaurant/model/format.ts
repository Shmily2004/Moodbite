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

/* ---------------------------------------------------------------------------
   TRẠNG THÁI & TUỔI THẬT — "quán này còn đúng không?"

   Backend trả bốn tín hiệu để trả lời câu đó: `temporarily_closed`,
   `source_updated_at`, `source_datasets`, `surveyed_at`. Ở đây CHỈ đổi chúng thành
   chữ người đọc hiểu — không lọc, không chấm điểm, không quyết định quán nào hiện.
   Việc đó nằm ở backend (`domain/entities/restaurant.py: is_visible`).
--------------------------------------------------------------------------- */

/**
 * Nhãn "đang đóng tạm".
 *
 * BA trạng thái, đừng rút xuống hai: `true` = biết chắc đang nghỉ · `false` = biết chắc
 * đang mở · `null`/`undefined` = NGUỒN KHÔNG CHO BIẾT (96,5% quán OSM + Overture).
 * Chỉ `true` mới được gắn nhãn. Nói "đang mở" cho quán chưa ai kiểm là bịa.
 */
export function describeTemporaryClosure(
  temporarilyClosed: boolean | null | undefined,
): string | null {
  return temporarilyClosed === true ? 'Đang tạm đóng cửa' : null;
}

export interface Freshness {
  /** Câu hiện ra màn hình, VD "nguồn cập nhật 3 năm trước". */
  text: string;
  /** Chỉ để CHỌN MÀU. Nhãn chữ mới là phần nói thật. */
  stale: boolean;
}

// Mốc "cũ" tính theo NĂM. Đo 2026-08-19 trên dữ liệu thật: 71,5% bản ghi OSM được sửa
// lần cuối từ 2025 trở về trước, cũ nhất là 2010; Overture thì 100% trong 2026.
// Lấy 2 năm vì dưới mốc đó phần lớn là bản ghi Overture còn tươi, trên mốc đó gần như
// chỉ còn OSM lâu không ai đụng tới - tức là ngưỡng này TÁCH ĐƯỢC hai nhóm có thật.
// Đây thuần là quy tắc TÔ MÀU, không lọc bỏ quán nào.
const NAM_COI_LA_CU = 2;

const MS_MOT_NGAY = 24 * 60 * 60 * 1000;

/**
 * Tuổi THẬT của bản ghi — ngày NGUỒN cập nhật, KHÁC HẲN ngày ta cào về.
 *
 * VÌ SAO PHẢI HIỆN: trường `last_updated` cũ ghi 97,4% dữ liệu "cập nhật 3 ngày trước"
 * vì đó là ngày ta chạy pipeline. Im lặng ở đây bị người dùng đọc thành "mọi quán đều
 * vừa được kiểm hôm qua" - tệ hơn hẳn so với nói thẳng "nguồn cập nhật 7 năm trước".
 *
 * `now` truyền vào được để test không phụ thuộc ngày chạy.
 */
export function describeFreshness(
  sourceUpdatedAt: string | null | undefined,
  now: Date = new Date(),
): Freshness | null {
  if (!sourceUpdatedAt) return null;
  const moc = new Date(sourceUpdatedAt);
  if (Number.isNaN(moc.getTime())) return null;

  const soNgay = Math.floor((now.getTime() - moc.getTime()) / MS_MOT_NGAY);
  // Ngày ở TƯƠNG LAI = dữ liệu nguồn sai. Nói "cập nhật -2 năm trước" còn tệ hơn im lặng.
  if (soNgay < 0) return null;

  if (soNgay < 45) return { text: 'nguồn vừa cập nhật', stale: false };

  const soThang = Math.floor(soNgay / 30);
  if (soThang < 12) return { text: `nguồn cập nhật ${soThang} tháng trước`, stale: false };

  const soNam = Math.floor(soNgay / 365);
  return {
    text: `nguồn cập nhật ${soNam} năm trước`,
    stale: soNam >= NAM_COI_LA_CU,
  };
}

// Tên nền tảng như nguồn ghi (chữ hoa/thường không nhất quán: 'meta', 'Foursquare').
// So khớp bằng chữ thường; nền tảng lạ thì giữ NGUYÊN VĂN thay vì bỏ đi - bỏ đi là
// giấu mất một bằng chứng có thật.
const TEN_NEN_TANG: Record<string, string> = {
  meta: 'Meta',
  msft: 'Microsoft',
  microsoft: 'Microsoft',
  foursquare: 'Foursquare',
  openstreetmap: 'OpenStreetMap',
  osm: 'OpenStreetMap',
  pinmeto: 'PinMeTo',
  alltheplaces: 'AllThePlaces',
};

export function tenNenTang(dataset: string): string {
  return TEN_NEN_TANG[dataset.trim().toLowerCase()] ?? dataset;
}

/**
 * Bằng chứng ĐỐI CHIẾU: bao nhiêu nền tảng độc lập cùng ghi nhận quán này.
 *
 * MỘT nguồn không phải bằng chứng gì cả (mọi quán đều có ít nhất một), nên chỉ nói khi
 * có từ HAI trở lên - đúng lúc đó con số mới mang thêm thông tin.
 */
export function describeVerification(
  sourceDatasets: string[] | null | undefined,
): string | null {
  const list = (sourceDatasets ?? []).filter(Boolean);
  if (list.length < 2) return null;
  return `${list.length} nguồn xác nhận: ${list.map(tenNenTang).join(', ')}`;
}

/**
 * Ngày có NGƯỜI đi xác minh tận nơi (tag `check_date` của OSM).
 *
 * Hiếm (0,3% quán) nhưng là bằng chứng MẠNH NHẤT ta có, nên đáng một nhãn riêng thay vì
 * trộn chung vào dòng "nguồn cập nhật".
 */
export function describeSurvey(surveyedAt: string | null | undefined): string | null {
  if (!surveyedAt) return null;
  const nam = surveyedAt.slice(0, 4);
  return /^\d{4}$/.test(nam) ? `có người xác minh tận nơi (${nam})` : null;
}

export function hasCoordinates(
  item: SearchResultItem,
): item is SearchResultItem & { latitude: number; longitude: number } {
  return item.latitude != null && item.longitude != null;
}
