/**
 * Khoá lại các QUY ƯỚC HIỂN THỊ. Đây là chỗ dễ vi phạm nhất và hậu quả là nói dối
 * người dùng ("0 sao", "miễn phí") cho quán vốn chỉ THIẾU dữ liệu.
 */
import { describe, expect, it } from 'vitest';
import { describeCluster, describeDishConfidence, describeFit, describeMatchSource, describeReasons, formatDistance, formatPrice, formatRating } from './format';

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

describe('describeFit — mức phù hợp', () => {
  it('KHÔNG hiện phần trăm thô của predicted_score', () => {
    // Điểm thật dồn quanh 0.6; hiện "61%" khiến người dùng tưởng gợi ý kém
    // trong khi đó lại là quán khớp nhất. Nhãn phải là CHỮ.
    expect(describeFit(0.61).label).toBe('Phù hợp');
    expect(describeFit(0.61).label).not.toMatch(/%/);
  });

  it('chia đúng 3 mức theo phân bố điểm đo được', () => {
    expect(describeFit(0.721).label).toBe('Rất phù hợp');  // cao nhất đo được
    expect(describeFit(0.68).label).toBe('Rất phù hợp');
    expect(describeFit(0.613).label).toBe('Phù hợp');       // trung vị đo được
    expect(describeFit(0.576).label).toBe('Có thể hợp');    // thấp nhất đo được
  });

  it('thanh luôn nhìn thấy được, không bao giờ tràn', () => {
    for (const score of [0, 0.3, 0.576, 0.613, 0.721, 0.95, 1]) {
      const { barPercent } = describeFit(score);
      expect(barPercent).toBeGreaterThanOrEqual(8);
      expect(barPercent).toBeLessThanOrEqual(100);
    }
  });

  it('điểm cao hơn thì thanh dài hơn', () => {
    expect(describeFit(0.72).barPercent).toBeGreaterThan(describeFit(0.60).barPercent);
  });
});

describe('describeReasons — vì sao quán được đề xuất', () => {
  it('dịch mã match_source sang câu người đọc hiểu', () => {
    const reasons = describeReasons('name+review');
    expect(reasons).toHaveLength(1);
    expect(reasons[0].text).toBe('Khớp tên quán, đánh giá');
  });

  it('nhắc lại CHÍNH CÂU người dùng gõ khi khớp về không gian', () => {
    const reasons = describeReasons('atmosphere+name', 'quán lẩu ấm cúng');
    expect(reasons[0].text).toBe('Hợp với "quán lẩu ấm cúng"');
    expect(reasons[1].text).toBe('Khớp tên quán');
  });

  it('không có câu tìm thì vẫn nói được lý do', () => {
    expect(describeReasons('atmosphere')[0].text).toBe('Hợp về không gian và cảm giác');
  });

  it('tối đa 2 dòng — thẻ dài quá thì không ai đọc', () => {
    expect(describeReasons('name+category+review+semantic+atmosphere+mood')).toHaveLength(2);
  });

  it('mã lạ từ backend vẫn nói được gì đó, không im lặng', () => {
    expect(describeReasons('mã_lạ')).toHaveLength(1);
  });

  it('không có match_source thì trả rỗng, KHÔNG bịa lý do', () => {
    expect(describeReasons(null)).toEqual([]);
    expect(describeReasons('')).toEqual([]);
  });
});
