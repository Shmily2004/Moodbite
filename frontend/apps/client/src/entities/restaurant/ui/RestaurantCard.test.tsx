/**
 * Test component "ngu" — chỉ cần props, không cần mock mạng.
 * Đây chính là lợi ích của việc tách View khỏi ViewModel.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { SearchResultItem } from '@moodbite/api-client';
import { RestaurantCard } from './RestaurantCard';

function makeRestaurant(overrides: Partial<SearchResultItem> = {}): SearchResultItem {
  return {
    restaurant_id: 'ChIJtest',
    name: 'Phở Thìn Bờ Hồ',
    category: 'Nhà hàng phở',
    address: '13 Lò Đúc',
    latitude: 21.03,
    longitude: 105.85,
    distance_m: 320,
    price_range: '100-200 N ₫',
    rating: 4.5,
    user_ratings_total: 120,
    rank_position: 1,
    predicted_score: 0.87,
    match_source: 'name+review',
    district: 'Phường Hoàn Kiếm',
    dietary: [],
    amenities: [],
    source: 'google_maps_apify',
    experience_cluster_id: 2,
    experience_cluster_label: 'Tầm trung, đánh giá cao',
    suggested_dish: {
      dish_id: 'pho:pho-bo',
      name: 'Phở bò',
      cuisine: 'Việt Nam',
      spice_level: 1,
      temperature: 'hot',
      confidence: 'specific',
      reason: null,
    },
    ...overrides,
  } as SearchResultItem;
}

describe('RestaurantCard', () => {
  it('hiện tên, khoảng cách, đánh giá và giá', () => {
    render(<RestaurantCard restaurant={makeRestaurant()} />);
    expect(screen.getByText('Phở Thìn Bờ Hồ')).toBeInTheDocument();
    expect(screen.getByText('320 m')).toBeInTheDocument();
    expect(screen.getByText('4.5★ (120)')).toBeInTheDocument();
    expect(screen.getByText('100-200 N ₫')).toBeInTheDocument();
  });

  it('quán THIẾU đánh giá/giá không được hiện "0 sao" hay "miễn phí"', () => {
    render(
      <RestaurantCard
        restaurant={makeRestaurant({ rating: null, user_ratings_total: null, price_range: null })}
      />,
    );
    expect(screen.getByText('chưa có đánh giá')).toBeInTheDocument();
    expect(screen.queryByText(/0★/)).not.toBeInTheDocument();
    expect(screen.queryByText(/miễn phí/i)).not.toBeInTheDocument();
  });

  it('luôn hiện mức tin cậy của món gợi ý — món là suy luận, không phải thực đơn thật', () => {
    render(<RestaurantCard restaurant={makeRestaurant()} />);
    expect(screen.getByText('Phở bò')).toBeInTheDocument();
    expect(screen.getByText(/khớp loại hình/)).toBeInTheDocument();
  });

  it('giải thích VÌ SAO quán được gợi ý', () => {
    render(<RestaurantCard restaurant={makeRestaurant()} />);
    expect(screen.getByText(/tên quán, đánh giá/)).toBeInTheDocument();
  });

  it('quán chưa phân cụm hiện "Đang cập nhật" thay vì để trống', () => {
    render(
      <RestaurantCard
        restaurant={makeRestaurant({ experience_cluster_id: null, experience_cluster_label: null })}
      />,
    );
    expect(screen.getByText(/Đang cập nhật/)).toBeInTheDocument();
  });

  it('báo sự kiện lên trên thay vì tự gọi API', async () => {
    const onOpenDetail = vi.fn();
    render(<RestaurantCard restaurant={makeRestaurant()} onOpenDetail={onOpenDetail} />);
    screen.getByRole('button', { name: /Xem giá/ }).click();
    expect(onOpenDetail).toHaveBeenCalledOnce();
  });
});
