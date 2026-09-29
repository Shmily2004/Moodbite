/**
 * Công tắc "Chỉ hiện quán có ghi giá" ở phía bộ lọc.
 *
 * Bộ lọc này cắt kết quả mạnh hơn mọi chip khác (backend đo được chỉ 1,3% quán có giá đọc
 * được), nên hai thứ phải được khoá lại: nó được ĐẾM vào huy hiệu bộ lọc, và nó ĐI ĐƯỢC
 * qua đường dẫn chia sẻ. Một bộ lọc nặng mà vô hình là cách nhanh nhất để người dùng kết
 * luận sai về dữ liệu.
 */
import { describe, expect, it } from 'vitest';
import { docBoLocTuUrl, ghiBoLocLenUrl, urlCoBoLoc } from './boLocTuUrl';
import { EMPTY_FILTERS } from './useDishFilterState';

describe('công tắc giá trên URL', () => {
  it('mặc định TẮT, và khi tắt thì không ghi gì lên URL', () => {
    expect(EMPTY_FILTERS.onlyWithPrice).toBe(false);
    expect(ghiBoLocLenUrl(EMPTY_FILTERS).get('gia')).toBeNull();
  });

  it('bật thì ghi `gia=1` và đọc lại đúng - đường dẫn chia sẻ giữ nguyên lựa chọn', () => {
    const params = ghiBoLocLenUrl({ ...EMPTY_FILTERS, onlyWithPrice: true });

    expect(params.get('gia')).toBe('1');
    expect(docBoLocTuUrl(params).onlyWithPrice).toBe(true);
  });

  it('`gia=0` KHÔNG bật bộ lọc', () => {
    // Chỉ nhận đúng '1'. Một đường dẫn cũ lỡ mang `gia=0` mà lại bật bộ lọc nặng nhất của
    // sản phẩm thì người dùng không có cách nào đoán ra vì sao kết quả ít đi.
    expect(docBoLocTuUrl(new URLSearchParams('gia=0')).onlyWithPrice).toBeUndefined();
  });

  it('được tính là MỘT điều kiện lọc, khác với bán kính', () => {
    // `urlCoBoLoc` quyết định trang chi tiết món có suy bộ lọc từ món hay tôn trọng URL.
    expect(urlCoBoLoc(new URLSearchParams('km=10'))).toBe(false);
    expect(urlCoBoLoc(new URLSearchParams('gia=1'))).toBe(true);
  });
});
