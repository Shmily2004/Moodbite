/** Câu lỗi API phải theo NGÔN NGỮ đang chọn, không phải tiếng Việt cứng (audit 2026-10-06). */
import { describe, expect, it } from 'vitest';
import { ApiError } from '@moodbite/api-client';
import { taoHamDich } from '../i18n';
import { accountErrorText, apiErrorText } from './loiApi';

const en = taoHamDich('en');
const vi = taoHamDich('vi');

describe('apiErrorText', () => {
  it('NETWORK o ban tieng Anh la cau tieng Anh, khong phai "Failed to fetch"', () => {
    const err = new ApiError('NETWORK', 'Failed to fetch');
    expect(apiErrorText(err, en)).toMatch(/Could not reach the server/);
    expect(apiErrorText(err, vi)).toMatch(/Không kết nối được/);
  });

  it('DATA_NOT_READY dich theo ngon ngu', () => {
    expect(apiErrorText(new ApiError('DATA_NOT_READY', 'x', {}, 503), en)).toMatch(/restaurant data/);
  });

  it('ma khong co cau soan san -> dung cau backend', () => {
    expect(apiErrorText(new ApiError('INVALID_REQUEST', 'Bán kính phải > 0', {}, 400), en)).toBe(
      'Bán kính phải > 0',
    );
  });

  it('khong phai ApiError -> cau du phong', () => {
    expect(apiErrorText(new Error('boom'), en)).toBe('Something went wrong.');
  });
});

describe('accountErrorText', () => {
  it('401 sai mat khau -> cau backend, khong phai "phien het han"', () => {
    const err = new ApiError('UNAUTHORIZED', 'Mật khẩu hiện tại không đúng.', {}, 401);
    expect(accountErrorText(err, en)).toBe('Mật khẩu hiện tại không đúng.');
  });

  it('NETWORK -> cau dich', () => {
    expect(accountErrorText(new ApiError('NETWORK', 'Failed to fetch'), en)).toMatch(/Could not reach/);
  });
});
