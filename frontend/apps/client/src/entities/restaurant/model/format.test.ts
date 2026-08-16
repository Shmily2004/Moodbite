/**
 * Khoá lại các QUY ƯỚC HIỂN THỊ. Đây là chỗ dễ vi phạm nhất và hậu quả là nói dối
 * người dùng ("0 sao", "miễn phí") cho quán vốn chỉ THIẾU dữ liệu.
 */
import { describe, expect, it } from 'vitest';
import {
  describeCluster,
  describeDishConfidence,
  describeMatchSource,
  formatDistance,
  formatPrice,
  formatRating,
} from './format';

describe('formatDistance', () => {
  it('hiện mét khi dưới 1km', () => {
    expect(formatDistance(320)).toBe('320 m');
  });

  it('đổi sang km khi từ 1km trở lên', () => {
    expect(formatDistance(4800)).toBe('4.8 km');
  });

  it('thiếu dữ liệu trả null, KHÔNG phải "0 m"', () => {
    expect(formatDistance(null)).toBeNull();
    expect(formatDistance(undefined)).toBeNull();
  });
});

describe('formatRating', () => {
  it('hiện sao kèm số lượt đánh giá', () => {
    expect(formatRating(4.5, 120)).toBe('4.5★ (120)');
  });

  it('có sao nhưng chưa có số lượt thì chỉ hiện sao', () => {
    expect(formatRating(4.5, null)).toBe('4.5★');
  });

  it('CHƯA CÓ đánh giá phải nói rõ, tuyệt đối không hiện "0 sao"', () => {
    expect(formatRating(null, null)).toBe('chưa có đánh giá');
    expect(formatRating(null, null)).not.toContain('0');
  });
});

describe('formatPrice', () => {
  it('giữ nguyên chuỗi khoảng giá của Google Maps', () => {
    expect(formatPrice('100-200 N ₫')).toBe('100-200 N ₫');
  });

  it('thiếu giá trả null, KHÔNG phải "miễn phí"', () => {
    expect(formatPrice(null)).toBeNull();
    expect(formatPrice('')).toBeNull();
  });
});

describe('describeMatchSource', () => {
  it('dịch mã nguồn khớp sang tiếng Việt', () => {
    expect(describeMatchSource('name')).toBe('tên quán');
    expect(describeMatchSource('semantic')).toBe('ngữ nghĩa');
  });

  it('ghép nhiều nguồn bằng dấu phẩy', () => {
    expect(describeMatchSource('name+review')).toBe('tên quán, đánh giá');
  });

  it('mã lạ vẫn hiện được thay vì vỡ giao diện', () => {
    expect(describeMatchSource('mã_mới')).toBe('mã_mới');
  });
});

describe('describeDishConfidence', () => {
  it('nói rõ mức tin cậy vì món ăn là SUY LUẬN, không phải thực đơn thật', () => {
    expect(describeDishConfidence('specific')).toContain('khớp loại hình');
    expect(describeDishConfidence('generic_fallback')).toContain('có thể không chính xác');
  });

  it('không rõ vẫn có nhãn, không để trống', () => {
    expect(describeDishConfidence(null)).toBe('chưa xác định');
  });
});

describe('describeCluster', () => {
  it('quán CHƯA phân cụm hiện "Đang cập nhật" theo đặc tả API mục 3.1', () => {
    expect(describeCluster(null)).toBe('Đang cập nhật');
  });

  it('có cụm thì hiện nhãn cụm', () => {
    expect(describeCluster('Cao cấp, không gian sang')).toBe('Cao cấp, không gian sang');
  });
});
