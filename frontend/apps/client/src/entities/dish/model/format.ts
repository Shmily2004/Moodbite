/**
 * Quy tắc HIỂN THỊ của món ăn. Không có quy tắc nghiệp vụ nào ở đây.
 *
 * Backend trả về mã không dấu ("nuong", "sang") vì đó là khoá ổn định, không phụ thuộc
 * ngôn ngữ. Việc đổi mã thành chữ tiếng Việt có dấu là việc TRÌNH BÀY, nên nó nằm ở
 * frontend - đúng ranh giới ở CLAUDE.md mục 1b.
 *
 * CẨN THẬN: đây KHÔNG phải chỗ để tính điểm, xếp hạng hay lọc món. Nếu thấy mình sắp
 * viết công thức ở file này thì việc đó thuộc về `domain/services/dish_ranking.py`.
 *
 * SONG NGỮ (2026-10-02): các bảng dưới đây ánh xạ mã -> KHOÁ TỪ ĐIỂN, không phải chữ.
 * Mỗi hàm nhận thêm `t` (hàm dịch); bỏ trống = tiếng Việt, đúng như hành vi cũ, nên
 * test cũ không phải đổi. Component lấy `t` từ `useT()` rồi truyền vào.
 */
import { HAM_DICH_VI } from '@/shared/i18n';
import type { HamDich, Khoa } from '@/shared/i18n';

/** Mã cách chế biến -> khoá nhãn. Phải khớp `COOKING_METHODS` ở backend. */
const COOKING_METHOD_LABELS: Record<string, Khoa> = {
  nuong: 'dish.cook.nuong',
  chien: 'dish.cook.chien',
  luoc: 'dish.cook.luoc',
  hap: 'dish.cook.hap',
  xao: 'dish.cook.xao',
  nuoc: 'dish.cook.nuoc',
  song: 'dish.cook.song',
  tron: 'dish.cook.tron',
  nuong_lo: 'dish.cook.nuong_lo',
};

const MEAL_TIME_LABELS: Record<string, Khoa> = {
  sang: 'dish.meal.sang',
  trua: 'dish.meal.trua',
  toi: 'dish.meal.toi',
  khuya: 'dish.meal.khuya',
  an_vat: 'dish.meal.an_vat',
};

const TEMPERATURE_LABELS: Record<string, Khoa> = {
  hot: 'dish.temp.hot',
  cold: 'dish.temp.cold',
  room: 'dish.temp.room',
};

/** Nguồn dữ liệu -> câu nói cho người đọc hiểu con số/nguyên liệu này ở đâu ra. */
const SOURCE_LABELS: Record<string, Khoa> = {
  wikipedia_vi: 'dish.src.wikipedia_vi',
  wikidata: 'dish.src.wikidata',
  manual: 'dish.src.manual',
  seed_kb: 'dish.src.seed_kb',
  admin: 'dish.src.admin',
};

/** Mã lạ (backend thêm giá trị mới) thì hiện nguyên mã, đừng nuốt mất. */
function dichMa(bang: Record<string, Khoa>, ma: string, t: HamDich): string {
  const khoa = bang[ma];
  return khoa ? t(khoa) : ma;
}

export function describeCookingMethod(
  method?: string | null,
  t: HamDich = HAM_DICH_VI,
): string | null {
  if (!method) return null;
  return dichMa(COOKING_METHOD_LABELS, method, t);
}

export function describeTemperature(
  temperature?: string | null,
  t: HamDich = HAM_DICH_VI,
): string | null {
  if (!temperature) return null;
  return dichMa(TEMPERATURE_LABELS, temperature, t);
}

export function describeMealTimes(
  mealTimes?: string[] | null,
  t: HamDich = HAM_DICH_VI,
): string | null {
  if (!mealTimes || mealTimes.length === 0) return null;
  return mealTimes.map((m) => dichMa(MEAL_TIME_LABELS, m, t)).join(' · ');
}

export function describeSource(source?: string | null, t: HamDich = HAM_DICH_VI): string | null {
  if (!source) return null;
  return dichMa(SOURCE_LABELS, source, t);
}

/** Chặn trên số quả ớt: nhiều hơn thì tràn ra cả dòng thuộc tính. */
const MAX_CHILIES = 3;

export interface SpiceDisplay {
  /** Số quả ớt cần vẽ (0..3). 0 = khẳng định KHÔNG CAY, khác hẳn "chưa biết". */
  chilies: number;
  /** Câu cho trình đọc màn hình / chữ hiện ra khi không vẽ ớt. */
  label: string;
}

/**
 * Mức cay thành hình. `null`/`undefined` = CHƯA BIẾT, trả null để UI nói "chưa rõ" thay
 * vì hiện 0 quả ớt như thể món này chắc chắn không cay.
 *
 * Trả SỐ quả ớt chứ không trả chuỗi emoji nữa (đổi 2026-09-29, checklist A9): hình quả ớt
 * là icon SVG do VIEW vẽ, file `.ts` này không kéo React vào.
 */
export function describeSpice(
  level?: number | null,
  t: HamDich = HAM_DICH_VI,
): SpiceDisplay | null {
  if (level === null || level === undefined) return null;
  if (level <= 0) return { chilies: 0, label: t('dish.spice.none') };
  const chilies = Math.min(level, MAX_CHILIES);
  return { chilies, label: t('dish.spice.level', { n: chilies, max: MAX_CHILIES }) };
}

/**
 * Nhãn THUỘC TÍNH ngắn cho thẻ món ở lưới `/recommend` (thêm 2026-10-02, theo
 * `design/Filler.png`: "Món nước · Việt Nam").
 *
 * Thứ tự: cách chế biến -> ẩm thực -> nhiệt độ. Hai nhãn đầu phân biệt món tốt nhất
 * ("Món nước"/"Việt Nam"); nhiệt độ đứng cuối vì đa số món là "Nóng", ít thông tin nhất.
 * Thiếu trường nào thì BỎ nhãn đó — không bao giờ in "Chưa rõ" lên một thẻ nhỏ.
 * Chặn tối đa `MAX_DISH_TAGS` để thẻ không xuống ba dòng nhãn.
 */
const MAX_DISH_TAGS = 3;

export function describeDishTags(
  dish: {
    cooking_method?: string | null;
    cuisine?: string | null;
    temperature?: string | null;
  },
  t: HamDich = HAM_DICH_VI,
): string[] {
  const nhan = [
    describeCookingMethod(dish.cooking_method, t),
    // `cuisine` backend trả sẵn chữ có dấu ("Việt Nam", "Thái Lan") nên hiện nguyên văn.
    dish.cuisine?.trim() || null,
    describeTemperature(dish.temperature, t),
  ].filter((x): x is string => Boolean(x));
  // Bỏ trùng (VD "Nướng" vừa là cách chế biến vừa có thể là ẩm thực tự đặt).
  return [...new Set(nhan)].slice(0, MAX_DISH_TAGS);
}

/**
 * Định dạng số theo ngôn ngữ đang dùng: 12877 -> "12.877" (vi) / "12,877" (en).
 * Locale lấy từ khoá `common.numberLocale` để chỉ cần truyền đúng MỘT thứ là `t`.
 */
const DINH_DANG_SO = new Map<string, Intl.NumberFormat>();

export function formatCount(n: number, t: HamDich = HAM_DICH_VI): string {
  const locale = t('common.numberLocale');
  let dinhDang = DINH_DANG_SO.get(locale);
  if (!dinhDang) {
    dinhDang = new Intl.NumberFormat(locale);
    DINH_DANG_SO.set(locale, dinhDang);
  }
  return dinhDang.format(n);
}

/**
 * Tiêu đề danh sách quán ở trang chi tiết món: "Hiện 8 / 1.233 quán phù hợp với Phở bò".
 *
 * ⚠️ BẮT BUỘC NÓI "ĐANG HIỆN BAO NHIÊU / TỔNG BAO NHIÊU" (sửa 2026-10-02). Bản trước ghi
 * "1233 quán gần bạn" ngay trên một danh sách chỉ có 20 dòng (API giới hạn số quán trả
 * về) — người đọc hiểu là 1.233 quán đều nằm bên dưới. Chỉ khi đã hiện ĐỦ mới được bỏ
 * vế "Hiện x /".
 */
export function describeRestaurantListHeading(
  shown: number,
  total: number,
  dishName?: string | null,
  t: HamDich = HAM_DICH_VI,
): string {
  if (total <= 0 && shown <= 0) return t('dish.list.none');
  // `total` là số đếm của MÓN (tính lúc gợi ý), có thể lệch nhẹ với số quán tải về.
  // Lấy số lớn hơn làm tổng để không bao giờ in ra "Hiện 20 / 12".
  const tong = Math.max(total, shown);
  const gia_tri = {
    shown: formatCount(shown, t),
    total: formatCount(tong, t),
    dish: dishName ?? '',
  };
  if (shown >= tong) return t(dishName ? 'dish.list.allFor' : 'dish.list.all', gia_tri);
  return t(dishName ? 'dish.list.someFor' : 'dish.list.some', gia_tri);
}

/**
 * Câu mô tả số quán bán món này.
 *
 * KHÔNG BAO GIỜ hiện "0 quán" như một lựa chọn bấm được: backend đã ẩn món ngõ cụt khỏi
 * trang chủ, nhưng trang chi tiết mở từ liên kết chia sẻ thì vẫn có thể gặp.
 */
export function describeRestaurantCount(count: number, t: HamDich = HAM_DICH_VI): string {
  if (count <= 0) return t('dish.list.none');
  if (count === 1) return t('dish.count.one');
  // Có dấu ngăn hàng nghìn (2026-10-02): "12877 quán" đọc nhầm thành mã số.
  return t('dish.count.many', { n: formatCount(count, t) });
}

/**
 * Nhãn cho phần giới thiệu món.
 *
 * Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không có gì để nói" - đây là quy tắc 1
 * ở CLAUDE.md mục 4, và là lý do backend trả kèm cờ `has_description` riêng thay vì để
 * frontend tự đoán từ chuỗi rỗng.
 */
export function describeIntroState(
  hasDescription: boolean,
  t: HamDich = HAM_DICH_VI,
): string | null {
  return hasDescription ? null : t('dish.intro.none');
}
