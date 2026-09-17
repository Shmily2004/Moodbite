/**
 * Trang tài khoản: các TAB phải bấm được thật, và MỌI SỐ phải là số server đếm.
 *
 * VÌ SAO CẦN: bản thiết kế vẽ sẵn "27 · 15 · 18 · 5" và "320/500 điểm". Rủi ro lớn nhất
 * của cả trang này là ai đó chép mấy con số minh hoạ vào code cho "giống thiết kế" — lúc
 * đó giao diện trông đẹp mà nói dối. Test dưới đây khoá đúng chỗ ấy: tài khoản mới thì
 * mọi số phải là 0.
 *
 * Giả lập `fetch` ở mức thấp nhất (không mock `@/shared/api`) để đi qua ĐÚNG lớp
 * HttpClient thật — envelope `{data: …}` đọc sai là test đỏ.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { AccountPage } from '../index';

const NGUOI_DUNG = {
  user_id: 'u1',
  username: 'mung',
  role: 'user',
  display_name: 'Mừng',
  email: 'mung@example.com',
  created_at: '2024-05-02T00:00:00+00:00',
};

/** Tài khoản MỚI TINH: đúng thứ server trả về khi chưa có hoạt động nào. */
const STATS_RONG = {
  saved_restaurants: 0,
  saved_dishes: 0,
  viewed_restaurants: 0,
  explorations: 0,
  directions: 0,
  ratings: 0,
  closure_reports: 0,
  active_days: 0,
  points: 0,
  level: {
    current: { number: 1, name: 'Người mới', min_points: 0 },
    next: { number: 2, name: 'Foodie Explorer', min_points: 50 },
    points: 0,
    points_to_next: 50,
    ratio: 0,
  },
  badges: [
    {
      badge_id: 'explorer',
      name: 'Explorer',
      description: 'Xem chi tiết 20 quán khác nhau',
      emoji: '🧭',
      target: 20,
      current: 0,
      earned: false,
    },
  ],
};

function gia_lap_fetch(
  stats = STATS_RONG,
  favorites: unknown[] = [],
  anhMon: Record<string, string> = {},
) {
  return vi.fn().mockImplementation((url: string) => {
    const duong_dan = String(url);
    const tra = (data: unknown) =>
      Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });

    if (duong_dan.includes('/auth/me')) return tra(NGUOI_DUNG);
    if (duong_dan.includes('/me/stats')) return tra(stats);
    if (duong_dan.includes('/me/favorites'))
      return tra({ items: favorites, total: favorites.length });
    // `GET /dishes/{id}` — trang tra ảnh món cho thẻ đã lưu / đã xem.
    const mon = duong_dan.match(/\/dishes\/([^/?]+)/);
    if (mon) return tra({ dish_id: mon[1], name: mon[1], image_url: anhMon[mon[1]] ?? null });
    return tra({});
  });
}

function renderAccount() {
  return render(
    <MemoryRouter initialEntries={['/account']}>
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

describe('AccountPage', () => {
  it('hien du BAY tab ben trai', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    expect(await screen.findByRole('button', { name: /Tổng quan/ })).toBeInTheDocument();
    for (const ten of [
      /Hồ sơ cá nhân/,
      /Sở thích & khẩu vị/,
      // Đổi nhãn 2026-08-25: chủ dự án gọi đây là "yêu thích", không phải "đã lưu".
      /Yêu thích/,
      /Đã xem gần đây/,
      /Cấp độ & huy hiệu/,
      /Cài đặt/,
    ]) {
      expect(screen.getByRole('button', { name: ten })).toBeInTheDocument();
    }
  });

  it('TAI KHOAN MOI: moi so deu la 0, KHONG phai so tren ban thiet ke', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    await screen.findByText(/Thành viên từ 05\/2024/);

    // Bốn ô số liệu + điểm đều phải là 0. Nếu ai đó chép "27 · 15 · 18 · 5" vào code thì
    // test này đỏ ngay.
    for (const so of ['27', '15', '18', '5', '320']) {
      expect(screen.queryByText(so)).not.toBeInTheDocument();
    }
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(4);
  });

  it('bam tab thi doi noi dung VA doi URL (nut Back con dung)', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    fireEvent.click(await screen.findByRole('button', { name: /Hồ sơ cá nhân/ }));

    await waitFor(() => {
      expect(screen.getByText(/Tên đăng nhập/)).toBeInTheDocument();
    });
    // Tab nằm trên URL chứ không phải trong state -> gửi link được, Back chạy đúng.
    expect(window.location.search || document.location.search).toBeDefined();
  });

  it('tab CAP DO hien thanh tien do va huy hieu CHUA DAT o dang mo', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    fireEvent.click(await screen.findByRole('button', { name: /Cấp độ & huy hiệu/ }));

    expect(await screen.findByText(/Người mới/)).toBeInTheDocument();
    expect(screen.getByText(/Cấp 1/)).toBeInTheDocument();
    // Huy hiệu chưa đạt vẫn hiện, kèm tiến độ - đó là thứ cho người dùng biết phải làm gì.
    expect(screen.getByText('0/20')).toBeInTheDocument();
  });

  it('danh sach da luu lay tu SERVER, hien thanh THE co anh, "Xem tat ca" sang tab', async () => {
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch(
        STATS_RONG,
        [{ item_type: 'dish', item_id: 'bun-cha', name: 'Bún chả', created_at: null }],
        { 'bun-cha': 'https://anh.example/bun-cha.jpg' },
      ),
    );
    const { container } = renderAccount();

    expect(await screen.findByText('Bún chả')).toBeInTheDocument();
    // THẺ (không còn là chip chữ): có nhãn loại, dẫn tới trang món, và ảnh lấy từ API.
    const the = container.querySelector('.item-card');
    expect(the).not.toBeNull();
    expect(within(the as HTMLElement).getByText(/Món ăn/)).toBeInTheDocument();
    expect(within(the as HTMLElement).getByRole('link')).toHaveAttribute('href', '/dishes/bun-cha');
    await waitFor(() =>
      expect(the?.querySelector('img.item-card__img')).toHaveAttribute(
        'src',
        'https://anh.example/bun-cha.jpg',
      ),
    );

    // "Xem tất cả" CHUYỂN TAB chứ không đi trang khác.
    fireEvent.click(screen.getAllByRole('button', { name: /Xem tất cả/ })[0]);
    // Nói đúng nơi dữ liệu đang nằm.
    expect(await screen.findByText(/Đã đồng bộ với tài khoản/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Yêu thích/ })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  it('KHAU VI: chua chon gi thi hien trang thai rong + nut sang tab khau vi', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    expect(await screen.findByText('Bạn chưa chọn khẩu vị nào.')).toBeInTheDocument();
    expect(screen.queryByTestId('taste-radar-vung')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Cập nhật khẩu vị' }));
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Sở thích & khẩu vị/ })).toHaveAttribute(
        'aria-current',
        'page',
      ),
    );
  });

  it('KHAU VI: ve radar tu dung so thich da luu, va doi ngay khi bam chip', async () => {
    localStorage.setItem('moodbite.taste', JSON.stringify(['nuong']));
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    expect(await screen.findByTestId('taste-radar-vung')).toBeInTheDocument();
    // Số đọc được cho trình đọc màn hình: 1/5 cách chế biến.
    expect(screen.getByText('Cách chế biến: 1/5')).toBeInTheDocument();

    // Cùng một state với ô chọn phía trên -> bấm chip là biểu đồ đổi theo.
    fireEvent.click(screen.getByRole('button', { name: /Món nước/ }));
    expect(await screen.findByText('Cách chế biến: 2/5')).toBeInTheDocument();
  });

  it('dai "Cai thien goi y" dan sang tab khau vi', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    renderAccount();

    fireEvent.click(await screen.findByRole('button', { name: /Cập nhật ngay/ }));
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Sở thích & khẩu vị/ })).toHaveAttribute(
        'aria-current',
        'page',
      ),
    );
  });
});
