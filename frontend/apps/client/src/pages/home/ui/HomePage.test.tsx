/**
 * Trang chủ phải RENDER ĐƯỢC DỮ LIỆU THẬT từ API, không chỉ dựng được khung.
 *
 * VÌ SAO CẦN: `App.test.tsx` render trang chủ với `fetch` luôn lỗi, nên nó chỉ chứng minh
 * "backend chết vẫn không trắng màn hình". Nó KHÔNG chứng minh được đường dữ liệu
 * API -> hook -> widget -> thẻ món có thông suốt hay không. Một lỗi đọc sai tên trường
 * (VD `has_description` viết nhầm) sẽ lọt qua toàn bộ bộ test cũ.
 *
 * Giả lập `fetch` ở mức thấp nhất thay vì mock module `@/shared/api`: như vậy test đi qua
 * ĐÚNG lớp HttpClient thật, nên nếu envelope `{data: ...}` bị đọc sai thì test đỏ.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { HomePage } from '../index';

/** Một món đúng hình dạng backend trả về (envelope `data`, tên trường snake_case). */
const BUN_CHA = {
  dish_id: 'bun-cha',
  name: 'Bún chả',
  cuisine: 'Việt Nam',
  spice_level: 1,
  temperature: 'hot',
  cooking_method: 'nuong',
  meal_times: ['trua'],
  has_description: true,
  description: 'Bún chả là món Hà Nội gồm chả thịt lợn nướng than, ăn kèm bún và rau sống.',
  image_url: null,
  restaurant_count: 86,
  rank_position: 1,
  score: 0.81,
  reasons: ['đúng cách chế biến bạn chọn', 'trời mưa, món nóng ấm bụng'],
  source: 'manual',
  source_url: null,
  data_confidence: 'manual',
};

function mockSuggestResponse(results: unknown[], warnings: string[] = []) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      data: {
        search_query_id: 'q1',
        results,
        context: ['trời mưa'],
        warnings,
      },
    }),
  });
}

/**
 * Render THẲNG `HomePage`, không đi qua `app/routes`.
 *
 * Luật FSD chỉ cho import đi XUỐNG, mà `pages` thì KHÔNG được import từ `app` - steiger
 * bắt đúng lỗi này ở bản đầu của file. `MemoryRouter` là đủ để `useNavigate` chạy được.
 */
function renderHome() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      {/* Trang chủ đọc phiên tài khoản (lời chào có tên, dải mời đăng nhập) nên phải có
          provider. Lúc chạy thật `RootLayout` lo việc này. */}
      <UserSessionProvider>
        <HomePage />
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

describe('HomePage - KHACH vs DA DANG NHAP', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('KHACH: goi la "Mon pho bien", KHONG noi "danh cho ban"', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));
    renderHome();

    expect(await screen.findByText(/Món phổ biến hôm nay/i)).toBeInTheDocument();
    // Chốt chặn quan trọng: chưa đăng nhập thì hệ thống KHÔNG biết người này là ai, nên
    // mọi câu "dành cho bạn / phù hợp với bạn" đều là nói dối.
    expect(screen.queryByText(/dành cho bạn/i)).not.toBeInTheDocument();
  });

  it('KHACH: co hang "Kham pha theo nhu cau" - dung duoc khi chua co tai khoan', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));
    renderHome();

    expect(await screen.findByText(/Khám phá theo nhu cầu/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ăn gần đây/i })).toBeInTheDocument();
  });

  it('DA DANG NHAP: chao ten that va doi tieu de sang "danh cho <ten>"', async () => {
    // Có token -> `useUserSession` sẽ hỏi `/auth/me`. Giả lập theo TỪNG đường dẫn thay vì
    // một response chung, để test đi đúng hai lời gọi khác nhau.
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (String(url).includes('/auth/me')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              data: { user_id: 'u1', username: 'mung', role: 'user', display_name: 'Mừng' },
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            data: { search_query_id: 'q1', results: [BUN_CHA], context: [], warnings: [] },
          }),
        });
      }),
    );

    renderHome();

    expect(await screen.findByText(/Gợi ý hôm nay dành cho Mừng/i)).toBeInTheDocument();
    expect(screen.getByText(/Mood của bạn hôm nay/i)).toBeInTheDocument();
    // Hàng "Khám phá theo nhu cầu" là lối vào cho khách, người đã đăng nhập không cần.
    expect(screen.queryByText(/Khám phá theo nhu cầu/i)).not.toBeInTheDocument();
  });
});

describe('HomePage - nut tim luu mon', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('bam tim thi luu lai o may, bam lai thi bo luu', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));
    renderHome();

    const tim = await screen.findByRole('button', { name: /^Lưu Bún chả$/ });
    fireEvent.click(tim);

    // KHÁCH lưu ở localStorage; người đã đăng nhập thì đồng bộ lên `/me/favorites`
    // (xem `features/save-favorite`). Test này chạy ở trạng thái CHƯA đăng nhập.
    // Lưu kèm TÊN chứ không chỉ id: trang tài khoản hiện danh sách đã lưu mà không phải
    // gọi API lấy tên từng món.
    expect(JSON.parse(localStorage.getItem('moodbite.favorites') ?? '[]')).toEqual([
      { itemType: 'dish', itemId: 'bun-cha', name: 'Bún chả' },
    ]);

    fireEvent.click(screen.getByRole('button', { name: /^Bỏ lưu Bún chả$/ }));
    expect(JSON.parse(localStorage.getItem('moodbite.favorites') ?? '[]')).toHaveLength(0);
  });

  it('bam tim KHONG mo trang chi tiet mon', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));
    renderHome();

    fireEvent.click(await screen.findByRole('button', { name: /^Lưu Bún chả$/ }));

    // Vẫn ở trang chủ: tiêu đề khối kết quả còn đó.
    expect(screen.getByText(/Món phổ biến hôm nay/i)).toBeInTheDocument();
  });
});

describe('HomePage - duong du lieu API -> the mon', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('hien TEN MON tra ve tu API', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));

    renderHome();

    expect(await screen.findByText('Bún chả')).toBeInTheDocument();
  });

  it('hien SO QUAN - thu quyet dinh nguoi dung co bam hay khong', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));

    renderHome();

    expect(await screen.findByText(/86 quán gần bạn/i)).toBeInTheDocument();
  });

  it('the mon KHONG con doan gioi thieu - no da chuyen sang trang chi tiet', async () => {
    // ĐỔI Ý CÓ CHỦ ĐÍCH (2026-08-22): bản đầu cho cả đoạn giới thiệu lên thẻ vì thẻ hồi
    // đó không có ảnh. Bản thiết kế của chủ dự án dùng thẻ gọn: ẢNH + tên + số quán, và
    // ảnh nói "món này là gì" tốt hơn hai dòng chữ bị cắt cụt.
    //
    // Thông tin KHÔNG mất: đoạn giới thiệu đầy đủ nằm ở `pages/dish` (DishPage) — có
    // `dish-detail__intro`. Test này khoá đúng điều đó: đừng nhét lại vào thẻ.
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));
    renderHome();

    expect(await screen.findByText('Bún chả')).toBeInTheDocument();
    expect(screen.queryByText(/chả thịt lợn nướng than/i)).not.toBeInTheDocument();
  });

  it('hien LY DO duoc goi y', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));

    renderHome();

    expect(await screen.findByText(/trời mưa, món nóng ấm bụng/i)).toBeInTheDocument();
  });

  it('hien CANH BAO cua server thay vi nuot di', async () => {
    // Backend ẩn món ngõ cụt và nói rõ đã ẩn bao nhiêu. UI phải hiện câu đó ra -
    // im lặng bỏ bớt kết quả là lỗi `/suggest-dish` cũ từng mắc.
    vi.stubGlobal(
      'fetch',
      mockSuggestResponse([BUN_CHA], ['Đã ẩn 12 món không có quán nào trong bán kính 5 km.']),
    );

    renderHome();

    expect(await screen.findByText(/Đã ẩn 12 món/i)).toBeInTheDocument();
  });

  it('khong co mon nao -> moi nguoi dung noi bo loc, khong de man hinh trong', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([]));

    renderHome();

    expect(await screen.findByText(/Không có món nào khớp/i)).toBeInTheDocument();
  });

  it('mon CHUA co gioi thieu thi khong render doan trong', async () => {
    // `has_description: false` -> thẻ không được hiện đoạn giới thiệu rỗng.
    vi.stubGlobal(
      'fetch',
      mockSuggestResponse([{ ...BUN_CHA, has_description: false, description: null }]),
    );

    renderHome();

    await screen.findByText('Bún chả');
    expect(screen.queryByText(/chả thịt lợn nướng than/i)).not.toBeInTheDocument();
  });
});

describe('HomePage - nhac xac minh email', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  /** Giả lập một phiên đăng nhập với trạng thái email cho trước. */
  function dangNhapVoi(email: string | null, daXacMinh: boolean) {
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    return vi.fn().mockImplementation((url: string) => {
      if (String(url).includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            data: {
              user_id: 'u1',
              username: 'mung',
              role: 'user',
              display_name: 'Mừng',
              email,
              email_verified: daXacMinh,
            },
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({
          data: { search_query_id: 'q1', results: [BUN_CHA], context: [], warnings: [] },
        }),
      });
    });
  }

  it('CHUA xac minh thi nhac ngay o trang chu, co nut gui lai thu', async () => {
    vi.stubGlobal('fetch', dangNhapVoi('ai.do@vi.du.com', false));
    renderHome();

    expect(await screen.findByText(/Email chưa xác minh/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Gửi lại thư xác minh/i })).toBeInTheDocument();
  });

  it('DA xac minh thi KHONG nhac nua', async () => {
    vi.stubGlobal('fetch', dangNhapVoi('ai.do@vi.du.com', true));
    renderHome();

    // Đợi phiên nạp xong rồi mới khẳng định là không có — không thì test xanh giả vì
    // lúc kiểm trang còn chưa biết người dùng là ai.
    await screen.findByText(/Gợi ý hôm nay dành cho Mừng/i);
    expect(screen.queryByText(/Email chưa xác minh/i)).not.toBeInTheDocument();
  });

  it('KHACH thi khong bao gio thay dai nay', async () => {
    // Khách chưa có email nào để mà xác minh.
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));
    renderHome();

    await screen.findByText(/Món phổ biến hôm nay/i);
    expect(screen.queryByText(/Email chưa xác minh/i)).not.toBeInTheDocument();
  });
});
