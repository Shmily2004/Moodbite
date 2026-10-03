/**
 * Hàm định dạng thẻ quán ở bản TIẾNG ANH (thêm 2026-10-02). Luật trung thực không đổi theo
 * ngôn ngữ: thiếu rating là "No rating yet" chứ không phải "0", mức tin cậy món vẫn nói rõ.
 */
import { describe, expect, it } from 'vitest';
import { taoHamDich } from '@/shared/i18n';
import {
  describeDishConfidence,
  describeFit,
  describeFreshness,
  describeReasons,
  formatRating,
} from './format';

const en = taoHamDich('en');
const NOW = new Date('2026-10-02T00:00:00Z');

describe('format - tieng Anh', () => {
  it('thieu rating la "No rating yet", khong bao gio la 0', () => {
    expect(formatRating(null, null, en)).toBe('No rating yet');
    expect(formatRating(4.5, 120, en)).toBe('4.5★ (120)');
  });

  it('muc tin cay mon van noi ro bang chu', () => {
    expect(describeDishConfidence('generic_fallback', en)).toBe('broad guess, may be inaccurate');
    expect(describeDishConfidence(null, en)).toBe('not determined');
  });

  it('nhan phu hop va ly do khop deu dich', () => {
    expect(describeFit(0.7, en).label).toBe('Great match');
    expect(describeReasons('name+review', null, en)).toEqual([
      { kind: 'match', text: 'Matches restaurant name, reviews' },
    ]);
  });

  it('so it / so nhieu dung tieng Anh (khong in "1 months ago")', () => {
    expect(describeFreshness('2026-08-10', NOW, en)?.text).toBe('source updated 1 month ago');
    expect(describeFreshness('2026-05-01', NOW, en)?.text).toBe('source updated 5 months ago');
    expect(describeFreshness('2025-09-01', NOW, en)?.text).toBe('source updated 1 year ago');
    // Bản tiếng Việt giữ nguyên câu cũ.
    expect(describeFreshness('2026-08-10', NOW)?.text).toBe('nguồn cập nhật 1 tháng trước');
  });
});
