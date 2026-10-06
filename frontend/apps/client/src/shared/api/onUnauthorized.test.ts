/**
 * `onUnauthorized` của HttpClient (packages/api-client) — opt-in, chỉ cho request ĐÃ GỬI
 * token, và KHÔNG cho request kiểu "kiểm tra thông tin" (sai mật khẩu cũng là 401).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, HttpClient } from '@moodbite/api-client';

function tra401() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ error: { code: 'UNAUTHORIZED', message: 'Hết hạn', details: {} } }),
    }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('HttpClient.onUnauthorized', () => {
  it('goi callback kem token da gui, roi van nem ApiError', async () => {
    tra401();
    const cb = vi.fn();
    const http = new HttpClient({ baseUrl: '', getAuthToken: () => 'tok', onUnauthorized: cb });
    await expect(http.request('/me/stats')).rejects.toBeInstanceOf(ApiError);
    expect(cb).toHaveBeenCalledWith(expect.objectContaining({ token: 'tok', path: '/me/stats' }));
  });

  it('khong co token -> khong goi', async () => {
    tra401();
    const cb = vi.fn();
    const http = new HttpClient({ baseUrl: '', getAuthToken: () => null, onUnauthorized: cb });
    await expect(http.request('/auth/me')).rejects.toBeInstanceOf(ApiError);
    expect(cb).not.toHaveBeenCalled();
  });

  it('credentialCheck (vd. sai mat khau hien tai) -> khong goi', async () => {
    tra401();
    const cb = vi.fn();
    const http = new HttpClient({ baseUrl: '', getAuthToken: () => 'tok', onUnauthorized: cb });
    await expect(
      http.request('/auth/change-password', { method: 'POST', body: {}, credentialCheck: true }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(cb).not.toHaveBeenCalled();
  });
});
