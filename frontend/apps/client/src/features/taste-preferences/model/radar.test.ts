import { describe, expect, it } from 'vitest';
import { SO_THICH } from './danh_sach';
import { trucRadar } from './radar';

describe('trucRadar', () => {
  it('mỗi trục là một nhóm CÓ ô chọn — không vẽ trục luôn bằng 0', () => {
    const nhomCoThat = new Set(SO_THICH.map((x) => x.nhom));
    expect(trucRadar([]).map((t) => t.nhom).sort()).toEqual([...nhomCoThat].sort());
  });

  it('đếm đúng số ô đã chọn trong từng nhóm', () => {
    const truc = trucRadar(['nuong', 'nuoc', 'nong']);
    expect(truc.find((t) => t.nhom === 'cookingMethods')?.daChon).toBe(2);
    expect(truc.find((t) => t.nhom === 'temperatures')?.daChon).toBe(1);
    expect(truc.find((t) => t.nhom === 'mood')?.daChon).toBe(0);
  });

  it('chưa chọn gì thì mọi trục bằng 0 (trang hiện trạng thái rỗng)', () => {
    expect(trucRadar([]).every((t) => t.daChon === 0)).toBe(true);
  });
});
