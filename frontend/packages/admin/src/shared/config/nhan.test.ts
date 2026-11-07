/**
 * Test nhãn hiển thị cho mã do backend trả về.
 *
 * Canh: mã thô ("hot", "nuoc", "sang") không lọt ra màn quản trị · mã LẠ thì hiện nguyên
 * mã chứ không đoán · thiếu giá trị thì "—" (chưa có dữ liệu), không phải chuỗi rỗng.
 */
import { describe, expect, it } from 'vitest';
import {
  NHAN_BUA_AN,
  NHAN_CACH_CHE_BIEN,
  NHAN_NGUON_QUAN,
  NHAN_NHIET_DO_MON,
  NHAN_UU_TIEN_VAN_DE,
  nhanTheoMa,
} from './nhan';

describe('nhanTheoMa', () => {
  it('doi ma thuoc tinh mon sang chu nguoi doc', () => {
    expect(nhanTheoMa(NHAN_NHIET_DO_MON, 'hot')).toBe('Nóng');
    expect(nhanTheoMa(NHAN_CACH_CHE_BIEN, 'nuoc')).toBe('Món nước');
    expect(nhanTheoMa(NHAN_CACH_CHE_BIEN, 'nuong_lo')).toBe('Nướng lò');
    expect(['sang', 'trua', 'toi'].map((b) => nhanTheoMa(NHAN_BUA_AN, b))).toEqual([
      'Sáng',
      'Trưa',
      'Tối',
    ]);
  });

  it('nguon quan va muc uu tien', () => {
    expect(nhanTheoMa(NHAN_NGUON_QUAN, 'google_maps_apify')).toBe('Google Maps');
    expect(nhanTheoMa(NHAN_UU_TIEN_VAN_DE, 'nghiem_trong')).toBe('Nghiêm trọng');
  });

  it('ma la thi hien NGUYEN MA, khong doan; thieu thi "—"', () => {
    expect(nhanTheoMa(NHAN_CACH_CHE_BIEN, 'kho_to')).toBe('kho_to');
    expect(nhanTheoMa(NHAN_NHIET_DO_MON, null)).toBe('—');
    expect(nhanTheoMa(NHAN_NHIET_DO_MON, undefined)).toBe('—');
  });
});
