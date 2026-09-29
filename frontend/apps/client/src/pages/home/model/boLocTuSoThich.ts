/**
 * SỞ THÍCH đã lưu  ->  BỘ LỌC MÓN bật sẵn.
 *
 * VÌ SAO NẰM Ở `pages/home/model` CHỨ KHÔNG Ở TRONG MỘT FEATURE:
 * nó ghép HAI feature lại (`taste-preferences` đọc ra sở thích, `suggest-dishes` nhận bộ
 * lọc). Luật FSD cấm feature import ngang sang feature khác, nên chỗ duy nhất được phép
 * biết cả hai là trang — đó đúng là việc của trang.
 *
 * ⚠️ ĐÂY KHÔNG PHẢI QUY TẮC NGHIỆP VỤ. Nó chỉ dịch "ô người dùng đã tick" thành "tham số
 * gửi lên API", không chấm điểm và không quyết định món nào hợp. Việc lọc và xếp hạng
 * nằm trọn ở backend (`domain/services/dish_ranking.py`) — CLAUDE.md mục 1b.
 */
import type { FilterPreset } from '@/features/suggest-dishes';
import type { SoThich } from '@/features/taste-preferences';

/**
 * @param daChon Các sở thích đang bật, lấy từ `useTastePreferences().daChon`.
 * @returns Bộ lọc để đưa vào `useDishSuggestions` làm giá trị BAN ĐẦU. Rỗng khi người
 *   dùng chưa chọn gì — và rỗng phải nghĩa là "không áp gì cả", không phải "lọc ra 0 món".
 */
export function boLocTuSoThich(daChon: SoThich[]): FilterPreset {
  const preset: FilterPreset = {};

  for (const so_thich of daChon) {
    if (so_thich.nhom === 'mood') {
      // `mood` chỉ chọn được MỘT (hợp đồng API: `mood` là chuỗi, không phải mảng). Người
      // dùng tick nhiều ô mood thì lấy ô ĐẦU TIÊN thay vì để ô sau ghi đè ô trước — thứ
      // tự trong `SO_THICH` là cố định nên kết quả đoán trước được, không đổi theo thứ tự
      // người dùng bấm.
      preset.mood ??= so_thich.gia_tri;
      continue;
    }
    const hien = preset[so_thich.nhom] ?? [];
    if (!hien.includes(so_thich.gia_tri)) {
      preset[so_thich.nhom] = [...hien, so_thich.gia_tri];
    }
  }

  return preset;
}

/** Sở thích có sinh ra bộ lọc nào không — để trang biết có cần nói gì với người dùng. */
export function coBoLocTuSoThich(preset: FilterPreset): boolean {
  return Object.keys(preset).length > 0;
}
