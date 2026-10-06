/**
 * TRANG TÌM QUÁN — khoá hai lỗi thật (audit 2026-10-06):
 *   1. Ô tìm ở trang chủ chuyển sang `/search?q=…` nhưng trang này không đọc `q` →
 *      chữ người dùng gõ biến mất, không lượt tìm nào chạy.
 *   2. Closure cũ: `setQueryText(q); run()` gửi câu CŨ; "mở rộng bán kính" tìm lại với
 *      bán kính CŨ.
 *
 * Giả lập `fetch` để đọc đúng body mà HttpClient thật gửi lên `/search`.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { SearchPage } from '../index';

vi.mock('@/widgets/restaurant-map', () => ({
  RestaurantMap: () => <div data-testid="ban-do" />,
}));

type BodyTim = { query_text: string | null; max_distance_km: number | null };

function giaLapFetch(results: unknown[] = []) {
  const bodies: BodyTim[] = [];
  const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    if (String(url).includes('/search')) bodies.push(JSON.parse(String(init?.body)));
    const data = String(url).includes('/search')
      ? { search_query_id: 's1', results, context: [], warnings: [] }
      : {};
    return Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
  });
  vi.stubGlobal('fetch', fetchMock);
  return bodies;
}

let urlHienTai = '';
function GhiUrl() {
  const loc = useLocation();
  urlHienTai = loc.pathname + loc.search;
  return null;
}

function renderAt(path: string) {
  return render(
    <LanguageProvider>
      <UserSessionProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route
              path="/search"
              element={
                <>
                  <SearchPage />
                  <GhiUrl />
                </>
              }
            />
          </Routes>
        </MemoryRouter>
      </UserSessionProvider>
    </LanguageProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  sessionStorage.clear();
});

describe('SearchPage', () => {
  it('doc ?q= tu URL: dien san o nhap va tim ngay mot lan', async () => {
    const bodies = giaLapFetch();
    renderAt('/search?q=b%C3%BAn%20ch%E1%BA%A3');

    expect(screen.getByRole('textbox')).toHaveValue('bún chả');
    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0].query_text).toBe('bún chả');
  });

  it('khong co q -> khong tu tim', async () => {
    const bodies = giaLapFetch();
    renderAt('/search');
    await new Promise((r) => setTimeout(r, 20));
    expect(bodies).toHaveLength(0);
  });

  it('bam cau mau gui DUNG cau vua bam (khong phai cau cu) va cap nhat URL', async () => {
    const bodies = giaLapFetch();
    renderAt('/search');

    fireEvent.click(screen.getByRole('button', { name: /quán lẩu ấm cúng/ }));

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0].query_text).toBe('quán lẩu ấm cúng');
    expect(new URLSearchParams(urlHienTai.split('?')[1]).get('q')).toBe('quán lẩu ấm cúng');
  });

  it('mo rong ban kinh tim lai voi ban kinh MOI', async () => {
    const bodies = giaLapFetch([]);
    renderAt('/search?q=xyz');
    await waitFor(() => expect(bodies).toHaveLength(1));
    const banDau = bodies[0].max_distance_km;

    const nut = await screen.findByRole('button', { name: /Mở rộng 20 km/ });
    fireEvent.click(nut);

    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(banDau).not.toBe(20);
    expect(bodies[1].max_distance_km).toBe(20);
    expect(bodies[1].query_text).toBe('xyz');
  });
});
