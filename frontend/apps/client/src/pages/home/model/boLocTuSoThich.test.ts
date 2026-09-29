/**
 * Ánh xạ SỞ THÍCH ĐÃ LƯU -> BỘ LỌC bật sẵn.
 *
 * Khoá đúng một lời hứa đang in trên trang tài khoản: "MoodBite sẽ bật sẵn các bộ lọc
 * này". Trước 2026-09-23 câu đó không có gì phía sau — sở thích nằm im trong localStorage.
 */
import { describe, expect, it } from 'vitest';
import { SO_THICH } from '@/features/taste-preferences';
import type { SoThich } from '@/features/taste-preferences';
import { boLocTuSoThich, coBoLocTuSoThich } from './boLocTuSoThich';

function lay(...ids: string[]): SoThich[] {
  return ids.map((id) => {
    const x = SO_THICH.find((s) => s.id === id);
    if (!x) throw new Error(`Không có sở thích id=${id} trong SO_THICH`);
    return x;
  });
}

describe('boLocTuSoThich', () => {
  it('chưa chọn gì thì KHÔNG áp bộ lọc nào', () => {
    // Rỗng phải nghĩa là "không lọc", tuyệt đối không phải "lọc ra 0 món".
    expect(boLocTuSoThich([])).toEqual({});
    expect(coBoLocTuSoThich({})).toBe(false);
  });

  it('gom nhiều sở thích CÙNG NHÓM vào một mảng', () => {
    expect(boLocTuSoThich(lay('nuong', 'chien')).cookingMethods).toEqual(['nuong', 'chien']);
  });

  it('tách đúng nhóm: cách chế biến và nhiệt độ không lẫn vào nhau', () => {
    const preset = boLocTuSoThich(lay('nuong', 'nong'));

    expect(preset.cookingMethods).toEqual(['nuong']);
    expect(preset.temperatures).toEqual(['hot']);
  });

  it('mood chỉ lấy MỘT - hợp đồng API khai `mood` là chuỗi, không phải mảng', () => {
    expect(boLocTuSoThich(lay('cay')).mood).toBe('excited');
  });

  it('mọi mã sinh ra đều là mã BACKEND (không dấu), không phải nhãn tiếng Việt', () => {
    // Đưa nhãn ("Đồ nướng") lên API là 400 INVALID_REQUEST. Khoá lại để đổi nhãn hiển thị
    // không vô tình làm hỏng lượt gọi.
    const preset = boLocTuSoThich(SO_THICH);
    const moi_ma = [
      ...(preset.cookingMethods ?? []),
      ...(preset.temperatures ?? []),
      ...(preset.cuisines ?? []),
      ...(preset.mood ? [preset.mood] : []),
    ];

    expect(moi_ma.length).toBeGreaterThan(0);
    for (const ma of moi_ma) expect(ma).toMatch(/^[a-z_]+$/);
  });

  it('không sinh khoá trùng khi cùng một giá trị được chọn hai lần', () => {
    const [nuong] = lay('nuong');

    expect(boLocTuSoThich([nuong, nuong]).cookingMethods).toEqual(['nuong']);
  });
});
