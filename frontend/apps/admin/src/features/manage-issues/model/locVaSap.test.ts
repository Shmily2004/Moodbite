import { describe, expect, it } from 'vitest';
import type { VanDeNhom } from '@/shared/api';
import { locVaSapNhom } from './locVaSap';

const nhom = (key: string, ghiDe: Partial<VanDeNhom>): VanDeNhom => ({
  key,
  label: key,
  description: '',
  count: 0,
  severity: 'canh_bao',
  priority: 'can_kiem_tra',
  target_type: 'quan_an',
  ...ghiDe,
});

const DATA = [
  nhom('a', { count: 5, target_type: 'quan_an', last_resolved_at: null }),
  nhom('b', { count: 50, target_type: 'mon_an', last_resolved_at: '2026-09-10T00:00:00Z' }),
  nhom('c', { count: 9, target_type: 'mon_an', last_resolved_at: '2026-09-15T00:00:00Z' }),
];

describe('locVaSapNhom', () => {
  it('mac dinh GIU NGUYEN thu tu uu tien backend da xep', () => {
    expect(locVaSapNhom(DATA, null, 'uu_tien').map((v) => v.key)).toEqual(['a', 'b', 'c']);
  });

  it('loc theo loai', () => {
    expect(locVaSapNhom(DATA, 'mon_an', 'uu_tien').map((v) => v.key)).toEqual(['b', 'c']);
  });

  it('sap theo so luong giam dan', () => {
    expect(locVaSapNhom(DATA, null, 'so_luong').map((v) => v.key)).toEqual(['b', 'c', 'a']);
  });

  it('xu ly gan nhat: nhom CHUA ai danh dau xuong cuoi', () => {
    expect(locVaSapNhom(DATA, null, 'xu_ly_gan_nhat').map((v) => v.key)).toEqual([
      'c',
      'b',
      'a',
    ]);
  });

  it('khong sua mang goc', () => {
    locVaSapNhom(DATA, null, 'so_luong');
    expect(DATA.map((v) => v.key)).toEqual(['a', 'b', 'c']);
  });
});
