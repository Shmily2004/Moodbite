import { describe, expect, it } from 'vitest';
import { ROUTES } from '@/shared/config';
import { MUC_TAB, tabDangMo } from './mucTab';

describe('thanh tab dưới đáy', () => {
  it('mọi mục dẫn tới route CÓ THẬT — không có link chết', () => {
    // Đối chiếu với bảng đường dẫn dùng chung (không import `app/routes`: widget không được
    // import ngược lên tầng `app`). Việc đăng ký route thật đã có `App.test.tsx` khoá.
    const duongDanCo = new Set<string>(Object.values(ROUTES));
    for (const muc of MUC_TAB) {
      expect(duongDanCo, muc.to).toContain(muc.to.split('?')[0]);
    }
  });

  it('tô sáng đúng tab, phân biệt Yêu thích với Cá nhân bằng ?tab=saved', () => {
    expect(tabDangMo('/', '')).toBe('home');
    expect(tabDangMo('/recommend', '?km=3')).toBe('suggest');
    expect(tabDangMo('/account', '?tab=saved')).toBe('favorites');
    expect(tabDangMo('/account', '?tab=profile')).toBe('me');
    expect(tabDangMo('/search', '')).toBeNull();
  });
});
