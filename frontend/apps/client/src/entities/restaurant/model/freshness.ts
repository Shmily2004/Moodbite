/**
 * Quy tắc HIỂN THỊ "quán này còn đúng không?" — tách khỏi `format.ts` ngày 2026-10-06 khi
 * file đó vượt ~300 dòng (CLAUDE.md mục 6). `format.ts` RE-EXPORT mọi thứ ở đây nên nơi
 * khác vẫn import như cũ. Thuần TypeScript, không React, không nghiệp vụ.
 */
import { HAM_DICH_VI } from '@/shared/i18n';
import type { HamDich } from '@/shared/i18n';

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
  t: HamDich = HAM_DICH_VI,
): string | null {
  return temporarilyClosed === true ? t('rest.closedTemp') : null;
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
  t: HamDich = HAM_DICH_VI,
): Freshness | null {
  if (!sourceUpdatedAt) return null;
  const moc = new Date(sourceUpdatedAt);
  if (Number.isNaN(moc.getTime())) return null;

  const soNgay = Math.floor((now.getTime() - moc.getTime()) / MS_MOT_NGAY);
  // Ngày ở TƯƠNG LAI = dữ liệu nguồn sai. Nói "cập nhật -2 năm trước" còn tệ hơn im lặng.
  if (soNgay < 0) return null;

  if (soNgay < 45) return { text: t('rest.fresh.recent'), stale: false };

  const soThang = Math.floor(soNgay / 30);
  if (soThang < 12) {
    const text = soThang === 1 ? t('rest.fresh.month1') : t('rest.fresh.months', { n: soThang });
    return { text, stale: false };
  }

  const soNam = Math.floor(soNgay / 365);
  return {
    text: soNam === 1 ? t('rest.fresh.year1') : t('rest.fresh.years', { n: soNam }),
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
  t: HamDich = HAM_DICH_VI,
): string | null {
  const list = (sourceDatasets ?? []).filter(Boolean);
  if (list.length < 2) return null;
  return t('rest.verified', { n: list.length, list: list.map(tenNenTang).join(', ') });
}

/**
 * Ngày có NGƯỜI đi xác minh tận nơi (tag `check_date` của OSM).
 *
 * Hiếm (0,3% quán) nhưng là bằng chứng MẠNH NHẤT ta có, nên đáng một nhãn riêng thay vì
 * trộn chung vào dòng "nguồn cập nhật".
 */
export function describeSurvey(
  surveyedAt: string | null | undefined,
  t: HamDich = HAM_DICH_VI,
): string | null {
  if (!surveyedAt) return null;
  const nam = surveyedAt.slice(0, 4);
  return /^\d{4}$/.test(nam) ? t('rest.surveyed', { year: nam }) : null;
}
