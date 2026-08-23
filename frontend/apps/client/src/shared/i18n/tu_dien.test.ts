/**
 * Từ điển Việt–Anh: kiểm những thứ TypeScript KHÔNG bắt được.
 *
 * Kiểu `Record<Khoa, string>` đã bảo đảm bản tiếng Anh không thiếu khoá nào. Nhưng nó
 * KHÔNG bắt được ba lỗi dưới đây, và cả ba đều từng xảy ra ở các dự án i18n:
 *   - dán nhầm nguyên câu tiếng Việt vào ô tiếng Anh (chưa dịch mà tưởng đã dịch)
 *   - chuỗi rỗng (chữ biến mất trên giao diện, không ai biết vì sao)
 *   - placeholder `{name}` bị mất khi dịch (câu hiện thiếu tên người dùng)
 */
import { describe, expect, it } from 'vitest';
import { NGON_NGU, TU_DIEN, thay_the } from './tu_dien';

/** Dấu tiếng Việt: có ít nhất một ký tự này là gần như chắc chắn chưa dịch. */
const DAU_TIENG_VIET = /[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]/i;

describe('tu dien', () => {
  it('ban tieng Anh KHONG con chuoi tieng Viet nao', () => {
    const con_sot = Object.entries(TU_DIEN.en).filter(([, cau]) =>
      DAU_TIENG_VIET.test(cau),
    );
    expect(con_sot).toEqual([]);
  });

  it('khong co cau nao rong o bat ky ngon ngu nao', () => {
    for (const ma of NGON_NGU) {
      const rong = Object.entries(TU_DIEN[ma]).filter(([, cau]) => cau.trim() === '');
      expect(rong, `ngôn ngữ ${ma}`).toEqual([]);
    }
  });

  it('placeholder {…} phai giong nhau giua hai ban dich', () => {
    const cho_trong = (cau: string) => (cau.match(/\{\w+\}/g) ?? []).sort();

    for (const [khoa, cau_vi] of Object.entries(TU_DIEN.vi)) {
      const cau_en = TU_DIEN.en[khoa as keyof typeof TU_DIEN.en];
      expect(cho_trong(cau_en), `khoá ${khoa}`).toEqual(cho_trong(cau_vi));
    }
  });
});

describe('thay_the', () => {
  it('thay dung gia tri', () => {
    expect(thay_the('Xin chào {name}', { name: 'Mừng' })).toBe('Xin chào Mừng');
  });

  it('giu nguyen cho trong khong co gia tri - de nhin thay ma sua', () => {
    expect(thay_the('Xin chào {name}', {})).toBe('Xin chào {name}');
  });

  it('thay duoc nhieu cho trong trong mot cau', () => {
    expect(thay_the('{a} / {b}', { a: 1, b: 2 })).toBe('1 / 2');
  });
});
