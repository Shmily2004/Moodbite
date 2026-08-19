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
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
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
      <HomePage />
    </MemoryRouter>,
  );
}

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

  it('hien GIOI THIEU NGAN ngay tren the mon', async () => {
    vi.stubGlobal('fetch', mockSuggestResponse([BUN_CHA]));

    renderHome();

    expect(await screen.findByText(/chả thịt lợn nướng than/i)).toBeInTheDocument();
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
