/**
 * Test tiện ích trình bày dùng chung: CSV, phân trang, ngày giờ, phần trăm.
 *
 * Canh đúng những chỗ "nhìn thì hợp lý" dễ sai: `null` thành chữ "null" trong CSV, dấu
 * phẩy làm lệch cột, chia cho 0 ra "NaN%", ngày không giờ bị bịa thêm "00:00".
 */
import { describe, expect, it } from 'vitest';
import { danhSachTrang, ngayGioVN, phanTramVN, taoCsv } from './index';

describe('taoCsv', () => {
  it('null/undefined thanh o RONG, khong phai chu "null" hay so 0', () => {
    expect(taoCsv(['a', 'b'], [[null, undefined]])).toBe('a,b\r\n,');
  });

  it('boc nhay khi co dau phay, nhay kep hoac xuong dong', () => {
    expect(taoCsv(['x'], [['Phở, bún'], ['nói "ngon"'], ['a\nb']])).toBe(
      'x\r\n"Phở, bún"\r\n"nói ""ngon"""\r\n"a\nb"',
    );
  });
});

describe('danhSachTrang', () => {
  it('it trang thi hien het', () => {
    expect(danhSachTrang(1, 3)).toEqual([1, 2, 3]);
  });

  it('nhieu trang thi giu dau, cuoi va quanh trang hien tai', () => {
    expect(danhSachTrang(5, 20)).toEqual([1, '…', 4, 5, 6, '…', 20]);
  });
});

describe('dinh dang', () => {
  it('tong 0 thi khong chia cho 0', () => {
    expect(phanTramVN(3, 0)).toBe('—');
  });

  it('thieu ngay thi "—", KHONG doan', () => {
    expect(ngayGioVN(null)).toBe('—');
    expect(ngayGioVN('khong-phai-ngay')).toBe('—');
  });

  it('chuoi chi co ngay thi KHONG bia them gio', () => {
    expect(ngayGioVN('2026-08-18')).not.toMatch(/:/);
  });
});
