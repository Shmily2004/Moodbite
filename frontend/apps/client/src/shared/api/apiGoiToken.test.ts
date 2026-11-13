/**
 * Khoá lỗi "Món phù hợp với bạn hôm nay báo lỗi" (phát hiện 2026-11-13).
 *
 * Backend chặn `/dishes/suggest`, `/search`, ... bằng token người dùng. Client `api` từng
 * được tạo KHÔNG có `getAuthToken`, nên mọi gợi ý trên trang chủ đi không kèm header và
 * nhận 401. Test này đi qua đúng client thật và kiểm header trên request.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './index';
import { TOKEN_KEY } from '../lib/tokenStorage';

function fetchTraLoiRong() {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      data: { search_query_id: 'q', results: [], context: [], warnings: [] },
    }),
  });
}

describe('client api gửi token người dùng', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
    localStorage.clear();
  });

  it('gợi ý món gửi kèm Authorization khi đã đăng nhập', async () => {
    sessionStorage.setItem(TOKEN_KEY, 'token-kiem-thu');
    const fetchMock = fetchTraLoiRong();
    vi.stubGlobal('fetch', fetchMock);

    await api.suggestDishes({
      session_id: 's',
      latitude: 21,
      longitude: 105,
      cooking_methods: [],
      temperatures: [],
      meal_times: [],
      cuisines: [],
      mood: null,
      weather: null,
      max_distance_km: null,
      only_categories: false,
      only_with_price: false,
      limit: 30,
    });

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer token-kiem-thu');
  });

  it('tìm quán cũng gửi kèm Authorization', async () => {
    sessionStorage.setItem(TOKEN_KEY, 'token-kiem-thu');
    const fetchMock = fetchTraLoiRong();
    vi.stubGlobal('fetch', fetchMock);

    await api.search({ session_id: 's', latitude: 21, longitude: 105, query_text: 'phở', max_distance_km: null, limit: 10 });

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer token-kiem-thu');
  });
});
