/**
 * Quy tắc HIỂN THỊ của món ăn. Không có quy tắc nghiệp vụ nào ở đây.
 *
 * Backend trả về mã không dấu ("nuong", "sang") vì đó là khoá ổn định, không phụ thuộc
 * ngôn ngữ. Việc đổi mã thành chữ tiếng Việt có dấu là việc TRÌNH BÀY, nên nó nằm ở
 * frontend - đúng ranh giới ở CLAUDE.md mục 1b.
 *
 * CẨN THẬN: đây KHÔNG phải chỗ để tính điểm, xếp hạng hay lọc món. Nếu thấy mình sắp
 * viết công thức ở file này thì việc đó thuộc về `domain/services/dish_ranking.py`.
 */

/** Mã cách chế biến -> nhãn tiếng Việt. Phải khớp `COOKING_METHODS` ở backend. */
const COOKING_METHOD_LABELS: Record<string, string> = {
  nuong: 'Nướng',
  chien: 'Chiên/rán',
  luoc: 'Luộc',
  hap: 'Hấp',
  xao: 'Xào',
  nuoc: 'Món nước',
  song: 'Tươi sống',
  tron: 'Trộn',
  nuong_lo: 'Nướng lò',
};

const MEAL_TIME_LABELS: Record<string, string> = {
  sang: 'Sáng',
  trua: 'Trưa',
  toi: 'Tối',
  khuya: 'Khuya',
  an_vat: 'Ăn vặt',
};

const TEMPERATURE_LABELS: Record<string, string> = {
  hot: 'Nóng',
  cold: 'Mát/lạnh',
  room: 'Nguội',
};

/** Nguồn dữ liệu -> câu nói cho người đọc hiểu con số/nguyên liệu này ở đâu ra. */
const SOURCE_LABELS: Record<string, string> = {
  wikipedia_vi: 'theo Wikipedia tiếng Việt',
  wikidata: 'theo Wikidata',
  manual: 'do nhóm dự án tổng hợp',
  seed_kb: 'từ bộ quy tắc món ăn',
  admin: 'do quản trị viên nhập',
};

export function describeCookingMethod(method?: string | null): string | null {
  if (!method) return null;
  return COOKING_METHOD_LABELS[method] ?? method;
}

export function describeTemperature(temperature?: string | null): string | null {
  if (!temperature) return null;
  return TEMPERATURE_LABELS[temperature] ?? temperature;
}

export function describeMealTimes(mealTimes?: string[] | null): string | null {
  if (!mealTimes || mealTimes.length === 0) return null;
  return mealTimes.map((m) => MEAL_TIME_LABELS[m] ?? m).join(' · ');
}

export function describeSource(source?: string | null): string | null {
  if (!source) return null;
  return SOURCE_LABELS[source] ?? source;
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
export function describeSpice(level?: number | null): SpiceDisplay | null {
  if (level === null || level === undefined) return null;
  if (level <= 0) return { chilies: 0, label: 'Không cay' };
  const chilies = Math.min(level, MAX_CHILIES);
  return { chilies, label: `Độ cay ${chilies}/${MAX_CHILIES}` };
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

export function describeDishTags(dish: {
  cooking_method?: string | null;
  cuisine?: string | null;
  temperature?: string | null;
}): string[] {
  const nhan = [
    describeCookingMethod(dish.cooking_method),
    // `cuisine` backend trả sẵn chữ có dấu ("Việt Nam", "Thái Lan") nên hiện nguyên văn.
    dish.cuisine?.trim() || null,
    describeTemperature(dish.temperature),
  ].filter((x): x is string => Boolean(x));
  // Bỏ trùng (VD "Nướng" vừa là cách chế biến vừa có thể là ẩm thực tự đặt).
  return [...new Set(nhan)].slice(0, MAX_DISH_TAGS);
}

/** Định dạng số kiểu Việt Nam: 12877 -> "12.877". */
const DINH_DANG_SO = new Intl.NumberFormat('vi-VN');

export function formatCount(n: number): string {
  return DINH_DANG_SO.format(n);
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
): string {
  if (total <= 0 && shown <= 0) return 'Chưa tìm thấy quán nào gần bạn';
  const duoi = dishName ? ` quán phù hợp với ${dishName}` : ' quán phù hợp';
  // `total` là số đếm của MÓN (tính lúc gợi ý), có thể lệch nhẹ với số quán tải về.
  // Lấy số lớn hơn làm tổng để không bao giờ in ra "Hiện 20 / 12".
  const tong = Math.max(total, shown);
  if (shown >= tong) return `${formatCount(tong)}${duoi}`;
  return `Hiện ${formatCount(shown)} / ${formatCount(tong)}${duoi}`;
}

/**
 * Câu mô tả số quán bán món này.
 *
 * KHÔNG BAO GIỜ hiện "0 quán" như một lựa chọn bấm được: backend đã ẩn món ngõ cụt khỏi
 * trang chủ, nhưng trang chi tiết mở từ liên kết chia sẻ thì vẫn có thể gặp.
 */
export function describeRestaurantCount(count: number): string {
  if (count <= 0) return 'Chưa tìm thấy quán nào gần bạn';
  if (count === 1) return '1 quán gần bạn';
  // Có dấu chấm ngăn hàng nghìn (2026-10-02): "12877 quán" đọc nhầm thành mã số.
  return `${DINH_DANG_SO.format(count)} quán gần bạn`;
}

/**
 * Nhãn cho phần giới thiệu món.
 *
 * Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không có gì để nói" - đây là quy tắc 1
 * ở CLAUDE.md mục 4, và là lý do backend trả kèm cờ `has_description` riêng thay vì để
 * frontend tự đoán từ chuỗi rỗng.
 */
export function describeIntroState(hasDescription: boolean): string | null {
  return hasDescription ? null : 'Chưa có giới thiệu cho món này.';
}
