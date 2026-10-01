/**
 * Hai tab mới của trang tài khoản (2026-09-29): "Bộ sưu tập của tôi", "Địa chỉ của tôi",
 * và ô "Thêm vào bộ sưu tập" trên thẻ ở tab Yêu thích.
 *
 * Khoá những thứ chỉ hỏng ở tầng giao diện: tab có trên thanh bên và mở được bằng URL,
 * câu "chưa có gì" nói THẬT (không vẽ dữ liệu mẫu như bản thiết kế), xoá phải qua bước
 * xác nhận, và lưu địa chỉ bị khoá cho tới khi đã chọn điểm.
 *
 * Giả lập `fetch` ở mức thấp nhất để đi qua đúng HttpClient thật.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { AccountPage } from '../index';

// Leaflet cần kích thước thật của DOM — jsdom không có. Thay bằng một nút "bấm lên bản đồ".
vi.mock('@/features/manage-addresses/ui/PointPickerMap', () => ({
  PointPickerMap: ({ onPick }: { onPick: (p: { lat: number; lng: number }) => void }) => (
    <button type="button" onClick={() => onPick({ lat: 21.0285, lng: 105.8542 })}>
      ban-do-gia
    </button>
  ),
}));

const NGUOI_DUNG = {
  user_id: 'u1',
  username: 'mung',
  role: 'user',
  display_name: 'Mừng',
  email: 'mung@example.com',
  created_at: '2024-05-02T00:00:00+00:00',
};

type Goi = { url: string; method: string; body: unknown };

function gia_lap_fetch(opts: {
  collections?: unknown[];
  addresses?: unknown[];
  favorites?: unknown[];
  goi?: Goi[];
}) {
  return vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    const u = String(url);
    const method = init?.method ?? 'GET';
    opts.goi?.push({ url: u, method, body: init?.body ? JSON.parse(String(init.body)) : null });
    const tra = (data: unknown) =>
      Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
    if (u.includes('/auth/me')) return tra(NGUOI_DUNG);
    if (u.includes('/me/stats')) return tra(null);
    if (u.includes('/me/favorites'))
      return tra({ items: opts.favorites ?? [], total: (opts.favorites ?? []).length });
    if (u.endsWith('/me/collections') && method === 'GET')
      return tra({ collections: opts.collections ?? [], total: 0 });
    if (u.endsWith('/me/addresses') && method === 'GET')
      return tra({ addresses: opts.addresses ?? [], total: 0 });
    if (u.includes('/me/collections') && method === 'DELETE') return tra({ message: 'ok' });
    if (u.includes('/me/addresses') && method === 'POST')
      return tra({ address_id: 'a1', label: 'Nhà', address_text: null, lat: 21.0285, lng: 105.8542, is_default: true, created_at: null });
    const mon = u.match(/\/dishes\/([^/?]+)/);
    if (mon) return tra({ dish_id: mon[1], name: mon[1], image_url: null });
    return tra({});
  });
}

function renderAccount(tab: string) {
  return render(
    <MemoryRouter initialEntries={[`/account?tab=${tab}`]}>
      <LanguageProvider>
        <UserSessionProvider>
          <AccountPage />
        </UserSessionProvider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Tab "Bộ sưu tập của tôi"', () => {
  it('co tren thanh ben va trang thai rong noi that', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch({}));
    renderAccount('collections');
    expect(await screen.findByRole('button', { name: /Bộ sưu tập của tôi/ })).toBeInTheDocument();
    expect(await screen.findByText(/Bạn chưa có bộ sưu tập nào/)).toBeInTheDocument();
  });

  it('mo bo de xem muc; mon co link toi trang mon, quan thi khong', async () => {
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch({
        collections: [
          {
            collection_id: 'c1',
            name: 'Hẹn hò',
            created_at: null,
            item_count: 2,
            items: [
              { item_type: 'dish', item_id: 'pho-bo', name: 'Phở bò', added_at: null },
              { item_type: 'restaurant', item_id: 'q1', name: 'Quán Nhà Mình', added_at: null },
            ],
          },
        ],
      }),
    );
    renderAccount('collections');
    fireEvent.click(await screen.findByRole('button', { name: /Hẹn hò/ }));
    expect(screen.getByRole('link', { name: 'Phở bò' })).toHaveAttribute('href', '/dishes/pho-bo');
    expect(screen.getByText('Quán Nhà Mình').closest('a')).toBeNull();
  });

  it('xoa phai qua buoc xac nhan', async () => {
    const goi: Goi[] = [];
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch({
        goi,
        collections: [
          { collection_id: 'c1', name: 'Hẹn hò', created_at: null, item_count: 0, items: [] },
        ],
      }),
    );
    renderAccount('collections');
    await screen.findByRole('button', { name: /Hẹn hò/ });
    fireEvent.click(screen.getByRole('button', { name: 'Xoá' }));
    expect(goi.some((g) => g.method === 'DELETE')).toBe(false);
    fireEvent.click(screen.getByRole('button', { name: 'Xoá hẳn' }));
    await waitFor(() => expect(goi.some((g) => g.method === 'DELETE')).toBe(true));
    await waitFor(() => expect(screen.queryByRole('button', { name: /Hẹn hò/ })).toBeNull());
  });
});

describe('Tab "Yêu thích" có ô thêm vào bộ sưu tập', () => {
  it('moi the co nut "Them vao bo suu tap"', async () => {
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch({
        favorites: [
          { list_type: 'favorite', item_type: 'dish', item_id: 'bun-cha', name: 'Bún chả', created_at: null },
        ],
      }),
    );
    renderAccount('saved');
    expect(
      await screen.findByRole('button', { name: /Thêm vào bộ sưu tập/ }),
    ).toBeInTheDocument();
  });
});

describe('Tab "Địa chỉ của tôi"', () => {
  it('co tren thanh ben va trang thai rong noi that', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch({}));
    renderAccount('addresses');
    expect(await screen.findByRole('button', { name: /Địa chỉ của tôi/ })).toBeInTheDocument();
    expect(await screen.findByText(/Chưa lưu địa chỉ nào/)).toBeInTheDocument();
  });

  it('nut luu bi khoa cho toi khi chon diem; bam ban do roi luu gui dung toa do', async () => {
    const goi: Goi[] = [];
    vi.stubGlobal('fetch', gia_lap_fetch({ goi }));
    renderAccount('addresses');
    fireEvent.click(await screen.findByRole('button', { name: 'Thêm địa chỉ' }));
    fireEvent.change(screen.getByPlaceholderText('Nhà, Công ty…'), { target: { value: 'Nhà' } });

    const luu = screen.getByRole('button', { name: 'Lưu địa chỉ' });
    expect(luu).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'ban-do-gia' }));
    expect(screen.getByText(/Đã chọn điểm: 21.02850, 105.85420/)).toBeInTheDocument();
    expect(luu).not.toBeDisabled();

    fireEvent.click(luu);
    await waitFor(() => expect(goi.some((g) => g.method === 'POST')).toBe(true));
    expect(goi.find((g) => g.method === 'POST')?.body).toEqual({
      label: 'Nhà',
      lat: 21.0285,
      lng: 105.8542,
      address_text: null,
    });
  });
});
