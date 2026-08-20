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
    // Markup mới tách ★ / số / số lượt thành nhiều thẻ, nên khớp theo NỘI DUNG gộp
    // của phần tử cha thay vì một chuỗi liền.
    expect(screen.getByText((_, el) => el?.className === 'card__rating' &&
      /4\.5/.test(el.textContent ?? '') && /120/.test(el.textContent ?? ''))).toBeInTheDocument();
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
    expect(screen.getByText(/Phở bò/)).toBeInTheDocument();
    // Mức tin cậy phải HIỆN RA CHỮ, không được giấu trong tooltip `title`.
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

    // Bố cục mới: BẤM CẢ THẺ để mở chi tiết, không còn nút "Xem giá" riêng —
    // vùng bấm to hơn, hợp với thao tác ngón tay trên điện thoại.
    screen.getByRole('button', { name: /Phở Thìn Bờ Hồ/ }).click();

    expect(onOpenDetail).toHaveBeenCalledOnce();
  });

  it('quán KHÔNG có ảnh vẫn hiện ô đại diện, không để trống', () => {
    // 78.5% quán không có ảnh -> đây là trường hợp PHỔ BIẾN, phải trông có chủ đích.
    const { container } = render(
      <RestaurantCard restaurant={makeRestaurant({ thumbnail_url: null })} />,
    );

    expect(container.querySelector('.thumb--generated')).not.toBeNull();
  });

  it('quán CÓ ảnh thì hiện ảnh thật', () => {
    const { container } = render(
      <RestaurantCard
        restaurant={makeRestaurant({ thumbnail_url: 'https://example.test/a.jpg' })}
      />,
    );

    const img = container.querySelector('.thumb img');
    expect(img).toHaveAttribute('src', 'https://example.test/a.jpg');
  });

  it('quán ĐANG TẠM ĐÓNG phải được gắn nhãn cảnh báo', () => {
    // Backend cào cờ này về từ 2026-08-19 nhưng giao diện chưa dùng, nên người dùng
    // vẫn được gợi ý quán đang nghỉ và chỉ biết khi đã đi tới nơi.
    render(<RestaurantCard restaurant={makeRestaurant({ temporarily_closed: true })} />);
    expect(screen.getByText(/đang tạm đóng cửa/i)).toBeInTheDocument();
  });

  it('quán KHÔNG BIẾT trạng thái thì tuyệt đối không nói gì về đóng/mở', () => {
    // 96,5% dataset rơi vào đây. Nói "đang mở" cho nhóm này là bịa.
    render(<RestaurantCard restaurant={makeRestaurant({ temporarily_closed: null })} />);
    expect(screen.queryByText(/đóng cửa/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/đang mở/i)).not.toBeInTheDocument();
  });

  it('hiện TUỔI THẬT của dữ liệu và các nguồn cùng xác nhận', () => {
    render(
      <RestaurantCard
        restaurant={makeRestaurant({
          source_updated_at: '2019-05-06T11:19:02Z',
          source_datasets: ['meta', 'msft'],
        })}
      />,
    );
    expect(screen.getByText(/nguồn cập nhật \d+ năm trước/)).toBeInTheDocument();
    expect(screen.getByText(/2 nguồn xác nhận: Meta, Microsoft/)).toBeInTheDocument();
  });

  it('không có dữ liệu tuổi thì im lặng, không hiện dòng trống', () => {
    const { container } = render(
      <RestaurantCard
        restaurant={makeRestaurant({
          source_updated_at: null,
          source_datasets: [],
          surveyed_at: null,
        })}
      />,
    );
    expect(container.querySelector('.card__origin')).toBeNull();
  });
});
