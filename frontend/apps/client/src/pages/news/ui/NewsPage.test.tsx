/**
 * TRANG DANH SÁCH TIN TỨC (UC14 trong `docs/bieu_do_uml`). Giả lập `fetch` ở mức thấp nhất
 * để đi qua đúng lớp `HttpClient` thật — đổi tên trường là test đỏ ngay.
 *
 * Khoá: chỉ hiện những gì backend trả về (không tự lọc nháp ở frontend), và lỗi không
 * bị đánh tráo thành "chưa có bài".
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { NewsPage } from '../index';

const BAI = {
  post_id: 'p1',
  slug: 'cam-nang-an-sang',
  title: 'Cẩm nang ăn sáng',
  summary: 'Phở và bún chả.',
  body: 'Nội dung',
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

function vaoTrangDanhSach() {
  return render(
    <MemoryRouter initialEntries={['/tin-tuc']}>
      <LanguageProvider>
        <UserSessionProvider>
          <Routes>
            <Route path="/tin-tuc" element={<NewsPage />} />
          </Routes>
        </UserSessionProvider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

describe('NewsPage (danh sách)', () => {
  it('hiện đúng các bài backend trả về, mỗi bài là một link tới trang đọc', async () => {
    giaLapApi(() => traLoi(200, { data: { posts: [BAI], total: 1 } }));
    vaoTrangDanhSach();

    // Tên truy cập của thẻ gồm cả ngày và tóm tắt, nên khớp theo tiêu đề thay vì chuỗi đầy đủ.
    const link = await screen.findByRole('link', { name: /Cẩm nang ăn sáng/ });
    expect(link.getAttribute('href')).toBe('/tin-tuc/cam-nang-an-sang');
  });

  it('không có bài thì nói rõ là chưa có, không để trang trống', async () => {
    giaLapApi(() => traLoi(200, { data: { posts: [], total: 0 } }));
    vaoTrangDanhSach();

    expect(await screen.findByText('Chưa có bài viết nào.')).toBeTruthy();
  });

  it('lỗi máy chủ thì báo lỗi, không báo "chưa có bài"', async () => {
    giaLapApi(() =>
      traLoi(500, { error: { code: 'INTERNAL_ERROR', message: 'hỏng', details: null } }),
    );
    vaoTrangDanhSach();

    expect(await screen.findByText('Không tải được bài viết. Thử lại sau.')).toBeTruthy();
    expect(screen.queryByText('Chưa có bài viết nào.')).toBeNull();
  });
  it('bài có ảnh thì hiện ảnh; bài không có ảnh thì hiện chữ cái đầu, không ô vỡ', async () => {
    giaLapApi(() =>
      traLoi(200, {
        data: {
          posts: [
            { ...BAI, image_url: '/anh/banner-trang-chu.png', image_credit: null },
            { ...BAI, post_id: 'p2', slug: 'bai-khac', title: 'Bài không ảnh', image_url: null, image_credit: null },
          ],
          total: 2,
        },
      }),
    );
    const { container } = vaoTrangDanhSach();

    await screen.findByRole('link', { name: /Cẩm nang ăn sáng/ });
    const anh = container.querySelectorAll('img.news-card__img');
    expect(anh.length).toBe(1);
    expect(anh[0].getAttribute('src')).toBe('/anh/banner-trang-chu.png');
    expect(container.querySelector('.news-card__initial')?.textContent).toBe('B');
  });
});
