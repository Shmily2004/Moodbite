/**
 * TRANG ĐỌC MỘT BÀI (UC14 trong `docs/bieu_do_uml`). Giả lập `fetch` ở mức thấp nhất.
 *
 * Khoá:
 *   - nội dung bài là CHỮ, không render HTML từ dữ liệu
 *   - bài nháp và bài không tồn tại (cùng 404) hiện CÙNG một câu — khách không dò được
 *     bài nháp
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { NewsArticlePage } from '../index';

const BAI = {
  post_id: 'p1',
  slug: 'cam-nang-an-sang',
  title: 'Cẩm nang ăn sáng',
  summary: 'Phở và bún chả.',
  body: 'Dòng một\n<b>không-in-đậm</b>',
  status: 'published',
  origin: 'admin',
  source_name: null,
  source_url: null,
  last_updated: null,
  published_at: '2026-11-12T08:00:00+00:00',
  updated_at: '2026-11-12T08:00:00+00:00',
};

function traLoi(status: number, body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
}

function giaLapApi(handler: (url: string) => Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn((url: string) => handler(String(url))));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function vaoTrangBai(slug: string) {
  return render(
    <MemoryRouter initialEntries={[`/tin-tuc/${slug}`]}>
      <LanguageProvider>
        <UserSessionProvider>
          <Routes>
            <Route path="/tin-tuc/:slug" element={<NewsArticlePage />} />
          </Routes>
        </UserSessionProvider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

describe('NewsArticlePage (đọc một bài)', () => {
  it('bài công khai: hiện tiêu đề và nội dung dưới dạng chữ, không dựng HTML', async () => {
    giaLapApi(() => traLoi(200, { data: { post: BAI } }));
    vaoTrangBai('cam-nang-an-sang');

    expect(await screen.findByRole('heading', { name: 'Cẩm nang ăn sáng' })).toBeTruthy();
    // Thẻ <b> trong nội dung phải hiện nguyên văn, không thành chữ đậm.
    expect(screen.getByText(/<b>không-in-đậm<\/b>/)).toBeTruthy();
    expect(document.querySelector('.news-article__body b')).toBeNull();
  });

  it('bài nháp hoặc không tồn tại (404) đều hiện CÙNG một câu', async () => {
    giaLapApi(() =>
      traLoi(404, { error: { code: 'POST_NOT_FOUND', message: 'không có', details: null } }),
    );
    vaoTrangBai('bai-nhap');

    await waitFor(() =>
      expect(screen.getByText('Bài viết này không còn hoặc chưa được công bố.')).toBeTruthy(),
    );
  });
});
