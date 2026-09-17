/**
 * Test KHUNG quản trị: banner dữ liệu giả lập, dòng phiên bản, breadcrumb trang con.
 *
 * Giả `fetch` theo đường dẫn thay vì giả `adminApi`: khung + trang con gọi nhiều endpoint
 * khác nhau, giả ở tầng HTTP thì test đi qua đúng lớp envelope `{data}` thật.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, useRoutes } from 'react-router-dom';
import { routes } from '../routes';
import { APP_VERSION } from '@/shared/config';

const TOKEN_KEY = 'moodbite.admin.token';

function heThong(ghiDe: Record<string, unknown> = {}) {
  return {
    storage_backend: 'sqlite',
    weather_enabled: false,
    admin_token_ttl_seconds: 3600,
    user_token_ttl_seconds: 3600,
    email_configured: false,
    app_base_url: '',
    services: [{ key: 'restaurants', label: 'Kho quán', ready: true, detail: null }],
    ...ghiDe,
  };
}

function giaFetch(system: Record<string, unknown>, rieng: Record<string, unknown> = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      const duong = new URL(url).pathname;
      if (duong.endsWith('/admin/system')) {
        return new Response(JSON.stringify({ data: system }), { status: 200 });
      }
      for (const [khoa, data] of Object.entries(rieng)) {
        if (duong.endsWith(khoa)) {
          return new Response(JSON.stringify({ data }), { status: 200 });
        }
      }
      throw new Error('backend tat');
    }),
  );
}

function Harness() {
  return useRoutes(routes);
}

function moTai(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Harness />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  sessionStorage.setItem(TOKEN_KEY, 'token-gia');
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe('Khung quan tri', () => {
  it('synthetic_data === true thi HIEN banner du lieu gia lap', async () => {
    giaFetch(heThong({ synthetic_data: true }));
    moTai('/nhat-ky');

    expect(await screen.findByRole('alert')).toHaveTextContent(/DỮ LIỆU GIẢ LẬP/);
  });

  it('thieu truong synthetic_data (backend cu) thi KHONG hien banner', async () => {
    giaFetch(heThong());
    moTai('/nhat-ky');

    // Đợi khung đọc xong /admin/system (dòng trạng thái kho xuất hiện) rồi mới khẳng định.
    expect(await screen.findByText(/Mọi kho dữ liệu sẵn sàng/)).toBeInTheDocument();
    expect(screen.queryByText(/DỮ LIỆU GIẢ LẬP/)).not.toBeInTheDocument();
  });

  it('hien phien ban doc tu package.json', () => {
    giaFetch(heThong());
    moTai('/nhat-ky');

    expect(screen.getByText(`Phiên bản ${APP_VERSION}`)).toBeInTheDocument();
  });

  it('trang chi tiet mon co breadcrumb ve danh sach mon + ten mon', async () => {
    giaFetch(heThong(), {
      '/admin/dishes/bun-cha': {
        dish_id: 'bun-cha',
        name: 'Bún chả',
        is_category: false,
        is_active: true,
        restaurant_count: 2,
      },
    });
    moTai('/mon-an/bun-cha');

    const duongDan = screen.getByRole('navigation', { name: 'Breadcrumb' });
    expect(duongDan).toHaveTextContent('Quản lý món ăn');
    expect(await screen.findByText('Bún chả', { selector: '.duong-dan li' })).toBeInTheDocument();
    // Mục menu của trang CHA vẫn sáng khi đang ở trang con.
    expect(
      screen.getAllByRole('link', { name: /Quản lý món ăn/ })[0].className,
    ).toMatch(/canh-trai__muc--dang/);
  });
});
