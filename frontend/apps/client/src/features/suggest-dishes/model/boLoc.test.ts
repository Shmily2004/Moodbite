/**
 * Các hàm thuần của bộ lọc món thêm ngày 2026-09-16: thanh trượt bán kính, suy bộ lọc từ
 * món đang xem, và chip bán kính ở dòng "Đang lọc theo".
 */
import { describe, expect, it } from 'vitest';
import { DEFAULT_RADIUS_KM } from '@/shared/config';
import { boLocTuMon } from './boLocTuMon';
import { urlCoBoLoc } from './boLocTuUrl';
import { chipDangBat } from './chipDangBat';
import { NAC_KHOANG_CACH, giaTriNac, viTriNac } from './khoangCach';
import { EMPTY_FILTERS } from './useDishFilterState';

describe('thanh trượt bán kính', () => {
  it('có đủ các nấc của bản thiết kế 1 · 3 · 5 · 10 km', () => {
    for (const km of [1, 3, 5, 10]) expect(NAC_KHOANG_CACH).toContain(km);
  });

  it('mọi nấc đều nằm trong khoảng backend nhận: (0, 100] hoặc null', () => {
    // `DishSuggestRequest.max_distance_km`: gt=0, le=100, cho phép null.
    for (const km of NAC_KHOANG_CACH) {
      if (km !== null) {
        expect(km).toBeGreaterThan(0);
        expect(km).toBeLessThanOrEqual(100);
      }
    }
  });

  it('vị trí <-> giá trị khép kín với mọi nấc', () => {
    NAC_KHOANG_CACH.forEach((km, i) => {
      expect(viTriNac(km)).toBe(i);
      expect(giaTriNac(i)).toBe(km);
    });
  });

  it('giá trị không trùng nấc (2 km của "Ăn gần đây") đặt ở nấc gần nhất', () => {
    expect(NAC_KHOANG_CACH[viTriNac(2)]).toBe(1);
    expect(NAC_KHOANG_CACH[viTriNac(8)]).toBe(10);
  });

  it('"Không giới hạn" là nấc cuối, KHÔNG bị lẫn với số 0', () => {
    expect(giaTriNac(NAC_KHOANG_CACH.length - 1)).toBeNull();
    expect(viTriNac(null)).toBe(NAC_KHOANG_CACH.length - 1);
  });
});

describe('boLocTuMon', () => {
  it('chép nhiệt độ + cách chế biến của món sang đúng ô lọc', () => {
    expect(boLocTuMon({ temperature: 'hot', cooking_method: 'nuong' })).toEqual({
      temperatures: ['hot'],
      cookingMethods: ['nuong'],
    });
  });

  it('bỏ mã KHÔNG có ô bấm (người dùng không thấy thì không tắt được)', () => {
    expect(boLocTuMon({ temperature: null, cooking_method: 'nuong_lo' })).toEqual({});
  });

  it('chưa tải xong món thì không suy gì', () => {
    expect(boLocTuMon(null)).toEqual({});
  });
});

describe('urlCoBoLoc', () => {
  it('chỉ có bán kính thì KHÔNG tính là có bộ lọc', () => {
    // Trang chủ luôn ghi `km=10` lên URL — tính nó thì nhánh suy từ món không bao giờ chạy.
    expect(urlCoBoLoc(new URLSearchParams('km=10'))).toBe(false);
    expect(urlCoBoLoc(new URLSearchParams('km=10&thoi_tiet=rain'))).toBe(true);
  });
});

describe('chipDangBat — bán kính', () => {
  it('bán kính mặc định thì KHÔNG thành chip', () => {
    expect(chipDangBat(EMPTY_FILTERS).some((c) => c.khoangCach)).toBe(false);
    expect(EMPTY_FILTERS.maxDistanceKm).toBe(DEFAULT_RADIUS_KM);
  });

  it('bán kính khác mặc định / không giới hạn thì thành chip gỡ được', () => {
    expect(chipDangBat({ ...EMPTY_FILTERS, maxDistanceKm: 3 }).at(-1)?.nhan).toBe(
      'Trong vòng 3 km',
    );
    expect(chipDangBat({ ...EMPTY_FILTERS, maxDistanceKm: null }).at(-1)?.khoangCach).toBe(true);
  });
});
