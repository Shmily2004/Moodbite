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

/**
 * Mức cay thành hình. `null`/`undefined` = CHƯA BIẾT, trả null để UI nói "chưa rõ" thay
 * vì hiện 0 quả ớt như thể món này chắc chắn không cay.
 */
export function describeSpice(level?: number | null): string | null {
  if (level === null || level === undefined) return null;
  if (level <= 0) return 'Không cay';
  return '🌶️'.repeat(Math.min(level, 3));
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
  return `${count} quán gần bạn`;
}

/**
 * Nhãn cho phần thành phần.
 *
 * Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không cần nguyên liệu" - đây là quy
 * tắc 1 ở CLAUDE.md mục 4, và là lý do backend trả kèm cờ `has_ingredients` riêng thay
 * vì để frontend tự đoán từ mảng rỗng.
 */
export function describeIngredientsState(hasIngredients: boolean): string | null {
  return hasIngredients ? null : 'Chưa có dữ liệu thành phần cho món này.';
}
