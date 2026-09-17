import { describe, expect, it } from 'vitest';
import type { DishItem } from '@/shared/api';
import { sapXepMon } from './sapXepMon';

function mon(name: string, restaurant_count: number, rank_position: number): DishItem {
  return {
    dish_id: name,
    name,
    restaurant_count,
    rank_position,
    score: 0.5,
    reasons: [],
    meal_times: [],
    has_description: false,
    is_category: false,
  } as DishItem;
}

const DS = [mon('Phở bò', 10, 1), mon('Bánh cuốn', 40, 2), mon('Ốc luộc', 40, 3)];

describe('sapXepMon', () => {
  it('"Phù hợp nhất" giữ NGUYÊN thứ tự backend — frontend không xếp hạng lại', () => {
    expect(sapXepMon(DS, 'phu-hop')).toBe(DS);
  });

  it('theo tên dùng thứ tự chữ tiếng Việt', () => {
    expect(sapXepMon(DS, 'ten').map((m) => m.name)).toEqual(['Bánh cuốn', 'Ốc luộc', 'Phở bò']);
  });

  it('theo số quán: nhiều trước, bằng nhau giữ thứ tự backend', () => {
    expect(sapXepMon(DS, 'so-quan').map((m) => m.name)).toEqual([
      'Bánh cuốn',
      'Ốc luộc',
      'Phở bò',
    ]);
  });

  it('KHÔNG sửa mảng gốc', () => {
    sapXepMon(DS, 'ten');
    expect(DS[0].name).toBe('Phở bò');
  });
});
