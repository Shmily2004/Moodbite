/**
 * Khoá lại QUY TẮC HIỂN THỊ của món ăn.
 *
 * Trọng tâm: phân biệt "CHƯA CÓ DỮ LIỆU" với "giá trị bằng 0". Đây là quy tắc 1 ở
 * CLAUDE.md mục 4 và là loại lỗi đã xảy ra thật ở phần rating quán ("chưa có đánh giá"
 * từng bị hiện thành "0 sao").
 */
import { describe, expect, it } from 'vitest';
import {
  describeCookingMethod,
  describeIntroState,
  describeMealTimes,
  describeRestaurantCount,
  describeSource,
  describeSpice,
  describeTemperature,
} from './format';

describe('describeSpice - phan biet CHUA BIET voi KHONG CAY', () => {
  it('null la CHUA BIET -> tra null de UI noi "chua ro"', () => {
    expect(describeSpice(null)).toBeNull();
    expect(describeSpice(undefined)).toBeNull();
  });

  it('0 la KHONG CAY - mot khang dinh that su, khac han chua biet', () => {
    expect(describeSpice(0)).toBe('Không cay');
  });

  it('muc cay thanh so qua ot, chan tren 3 de khong tran ra ca dong', () => {
    expect(describeSpice(2)).toBe('🌶️🌶️');
    expect(describeSpice(9)).toBe('🌶️🌶️🌶️');
  });
});

describe('describeIntroState', () => {
  it('khong co gioi thieu -> NOI RA, khong de vung trang', () => {
    expect(describeIntroState(false)).toMatch(/Chưa có giới thiệu/i);
  });

  it('co gioi thieu -> khong can cau giai thich nao', () => {
    expect(describeIntroState(true)).toBeNull();
  });
});

describe('describeRestaurantCount', () => {
  it('0 quan KHONG duoc hien nhu mot lua chon hap dan', () => {
    expect(describeRestaurantCount(0)).toMatch(/Chưa tìm thấy/i);
  });

  it('dem duoc thi noi so that', () => {
    expect(describeRestaurantCount(1)).toBe('1 quán gần bạn');
    expect(describeRestaurantCount(86)).toBe('86 quán gần bạn');
  });
});

describe('doi ma khong dau cua backend sang chu tieng Viet', () => {
  it('cach che bien', () => {
    expect(describeCookingMethod('nuong')).toBe('Nướng');
    expect(describeCookingMethod('nuoc')).toBe('Món nước');
  });

  it('nhiet do', () => {
    expect(describeTemperature('hot')).toBe('Nóng');
    expect(describeTemperature('cold')).toBe('Mát/lạnh');
  });

  it('bua trong ngay noi lai bang dau cham giua', () => {
    expect(describeMealTimes(['sang', 'trua'])).toBe('Sáng · Trưa');
  });

  it('thieu du lieu -> null, KHONG phai chuoi rong hay "undefined"', () => {
    expect(describeCookingMethod(null)).toBeNull();
    expect(describeTemperature(undefined)).toBeNull();
    expect(describeMealTimes([])).toBeNull();
  });

  it('ma la khong lam vo giao dien - hien nguyen ma con hon hien trong', () => {
    // Backend thêm mã mới mà frontend chưa kịp cập nhật là chuyện sẽ xảy ra.
    expect(describeCookingMethod('ma-moi-chua-biet')).toBe('ma-moi-chua-biet');
  });
});

describe('describeSource - nguoi doc phai biet du lieu o dau ra', () => {
  it('noi ro nguon, vi thanh phan mon co the la tu soan', () => {
    expect(describeSource('manual')).toMatch(/nhóm dự án/i);
    expect(describeSource('wikipedia_vi')).toMatch(/Wikipedia/i);
  });

  it('khong co nguon -> null', () => {
    expect(describeSource(null)).toBeNull();
  });
});
