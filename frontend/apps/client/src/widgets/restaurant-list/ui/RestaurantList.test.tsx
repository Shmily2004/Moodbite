/**
 * DWELL TIME (audit 2026-10-06): lượt xem chi tiết phải được ghi cả khi người dùng
 * CHUYỂN sang quán khác hoặc RỜI trang, không chỉ khi bấm "Đóng".
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import type { SearchResultItem } from '@moodbite/api-client';
import { LanguageProvider } from '@/shared/i18n';
import { RestaurantList } from './RestaurantList';

function quan(id: string, name: string, rank: number) {
  return {
    restaurant_id: id,
    name,
    category: 'Quán ăn',
    address: null,
    latitude: 21.02,
    longitude: 105.85,
    distance_m: 100,
    price_range: null,
    rating: null,
    user_ratings_total: null,
    is_famous: false,
    rank_position: rank,
    predicted_score: 0.6,
    match_source: 'name',
    thumbnail_url: null,
    district: null,
    dietary: [],
    amenities: [],
    source: 'osm',
    experience_cluster_id: null,
    experience_cluster_label: null,
    temporarily_closed: null,
    source_updated_at: null,
    source_datasets: [],
    surveyed_at: null,
    suggested_dish: null,
  } as unknown as SearchResultItem;
}

type GhiNhan = { restaurant_id: string; action_type: string; dwell_time_ms: number | null };

function giaLapFetch() {
  const ghi: GhiNhan[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (String(url).includes('/interactions')) ghi.push(JSON.parse(String(init?.body)));
      const data = String(url).includes('/restaurants/')
        ? { restaurant_id: 'x', has_details: false, reason: 'Chưa có chi tiết' }
        : { ok: true };
      return Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
    }),
  );
  return ghi;
}

afterEach(() => vi.unstubAllGlobals());

describe('RestaurantList - dwell time', () => {
  it('mo quan B khi dang xem quan A -> ghi luot xem cua A; roi trang -> ghi luot cua B', async () => {
    const ghi = giaLapFetch();
    const { unmount } = render(
      <LanguageProvider>
        <RestaurantList restaurants={[quan('A', 'Quán A', 1), quan('B', 'Quán B', 2)]} searchQueryId="s1" />
      </LanguageProvider>,
    );

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Quán A/ }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Quán B/ }));
    });

    const xem = () => ghi.filter((g) => g.action_type === 'view_detail');
    expect(xem().map((g) => g.restaurant_id)).toEqual(['A']);

    unmount();
    await act(async () => Promise.resolve());
    expect(xem().map((g) => g.restaurant_id)).toEqual(['A', 'B']);
    expect(xem().every((g) => typeof g.dwell_time_ms === 'number')).toBe(true);
  });
});

describe('RestaurantList - khối "Không khí" trong chi tiết quán', () => {
  it('backend trả MẢNG -> hiện từng nhãn (trước 2026-10-13 backend trả chuỗi repr nên không bao giờ hiện)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            data: {
              restaurant_id: 'A',
              has_details: true,
              reason: null,
              name: 'Quán A',
              price_range: null,
              // Đúng hình dạng mà `GET /restaurants/{id}` trả SAU khi sửa repository.
              atmosphere: [{ 'Thông thường': true }, { 'Ấm cúng': true }],
              opening_hours: [],
              images: [],
              reviews: [],
              menu_url: null,
              website: null,
              google_maps_url: null,
              review_summary: null,
            },
          }),
        }),
      ),
    );
    render(
      <LanguageProvider>
        <RestaurantList restaurants={[quan('A', 'Quán A', 1)]} searchQueryId="s1" />
      </LanguageProvider>,
    );

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Quán A/ }));
    });

    expect(await screen.findByText(/Thông thường, Ấm cúng/)).toBeInTheDocument();
  });
});
