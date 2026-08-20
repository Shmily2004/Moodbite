/**
 * Test cho lớp "quán này còn đúng không?" — trạng thái đóng cửa và TUỔI THẬT của dữ liệu.
 *
 * Trọng tâm: BA trạng thái `true` / `false` / `null` phải cho ra ba cách hiển thị khác
 * nhau. Gộp `null` vào `false` là tự nhận đã xác minh 40.000 quán còn mở trong khi chưa
 * kiểm quán nào — đúng cái sai mà backend đã cẩn thận tránh.
 */
import { describe, expect, it } from 'vitest';
import {
  describeFreshness,
  describeSurvey,
  describeTemporaryClosure,
  describeVerification,
  tenNenTang,
} from './format';

// Ngày cố định để test không đổi kết quả theo ngày chạy.
const HOM_NAY = new Date('2026-08-20T00:00:00Z');

describe('describeTemporaryClosure', () => {
  it('CHỈ quán biết chắc đang nghỉ mới được gắn nhãn', () => {
    expect(describeTemporaryClosure(true)).toBe('Đang tạm đóng cửa');
  });

  it('biết chắc đang mở thì KHÔNG gắn nhãn gì', () => {
    expect(describeTemporaryClosure(false)).toBeNull();
  });

  it('null/undefined = nguồn KHÔNG cho biết -> im lặng, không được nói "đang mở"', () => {
    // 96,5% quán OSM + Overture rơi vào đây. Nếu hàm này nói bất cứ điều gì khẳng định
    // thì gần như toàn bộ dataset sẽ mang một lời hứa chưa ai kiểm chứng.
    expect(describeTemporaryClosure(null)).toBeNull();
    expect(describeTemporaryClosure(undefined)).toBeNull();
  });
});

describe('describeFreshness', () => {
  it('không có ngày nguồn thì im lặng, không đoán', () => {
    expect(describeFreshness(null, HOM_NAY)).toBeNull();
    expect(describeFreshness(undefined, HOM_NAY)).toBeNull();
  });

  it('ngày hỏng không được biến thành "NaN năm trước"', () => {
    expect(describeFreshness('không-phải-ngày', HOM_NAY)).toBeNull();
  });

  it('bản ghi vừa cập nhật', () => {
    expect(describeFreshness('2026-08-05T10:00:00Z', HOM_NAY)?.text).toBe(
      'nguồn vừa cập nhật',
    );
  });

  it('vài tháng trước thì nói theo THÁNG', () => {
    const f = describeFreshness('2026-02-20T00:00:00Z', HOM_NAY);
    expect(f?.text).toMatch(/^nguồn cập nhật \d+ tháng trước$/);
    expect(f?.stale).toBe(false);
  });

  it('bản ghi OSM từ 2019 phải bị đánh dấu là CŨ', () => {
    // Đây là trường hợp có thật và đông: 71,5% bản ghi OSM sửa lần cuối từ 2025 trở về
    // trước, cũ nhất là 2010.
    const f = describeFreshness('2019-05-06T11:19:02Z', HOM_NAY);
    expect(f?.text).toBe('nguồn cập nhật 7 năm trước');
    expect(f?.stale).toBe(true);
  });

  it('mới hơn 2 năm thì chưa coi là cũ', () => {
    expect(describeFreshness('2025-08-20T00:00:00Z', HOM_NAY)?.stale).toBe(false);
  });

  it('ngày ở TƯƠNG LAI (dữ liệu nguồn sai) thì im lặng thay vì nói ngược', () => {
    expect(describeFreshness('2030-01-01T00:00:00Z', HOM_NAY)).toBeNull();
  });
});

describe('describeVerification', () => {
  it('MỘT nguồn không phải bằng chứng gì - mọi quán đều có ít nhất một', () => {
    expect(describeVerification(['openstreetmap'])).toBeNull();
    expect(describeVerification([])).toBeNull();
    expect(describeVerification(null)).toBeNull();
  });

  it('từ hai nguồn độc lập trở lên mới nói, và nói rõ là nguồn nào', () => {
    expect(describeVerification(['meta', 'msft'])).toBe(
      '2 nguồn xác nhận: Meta, Microsoft',
    );
  });

  it('nền tảng lạ vẫn giữ NGUYÊN VĂN, không bị bỏ đi', () => {
    // Bỏ đi là giấu mất một bằng chứng có thật chỉ vì ta chưa kịp đặt tên tiếng Việt.
    expect(describeVerification(['meta', 'nen-tang-moi'])).toContain('nen-tang-moi');
  });
});

describe('tenNenTang', () => {
  it('khớp không phân biệt hoa thường vì nguồn ghi không nhất quán', () => {
    // Dữ liệu thật trong bộ mẫu: 'meta' viết thường, 'Foursquare' viết hoa.
    expect(tenNenTang('Foursquare')).toBe('Foursquare');
    expect(tenNenTang('OPENSTREETMAP')).toBe('OpenStreetMap');
    expect(tenNenTang('meta')).toBe('Meta');
  });
});

describe('describeSurvey', () => {
  it('có người đi xác minh tận nơi là bằng chứng MẠNH NHẤT -> nói rõ năm', () => {
    expect(describeSurvey('2024-11-30')).toBe('có người xác minh tận nơi (2024)');
  });

  it('thiếu hoặc hỏng thì im lặng', () => {
    expect(describeSurvey(null)).toBeNull();
    expect(describeSurvey('hôm nọ')).toBeNull();
  });
});
