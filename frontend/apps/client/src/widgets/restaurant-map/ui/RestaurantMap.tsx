/**
 * Bản đồ kết quả — Leaflet + tile OpenStreetMap.
 *
 * VÌ SAO KHÔNG DÙNG GOOGLE MAPS: Google bắt buộc bật thanh toán (cần thẻ) dù có hạn mức
 * miễn phí. Leaflet + OSM miễn phí hoàn toàn, không cần key. Dữ liệu quán vốn ~72% từ
 * OpenStreetMap nên dùng bản đồ OSM cũng nhất quán về giấy phép.
 *
 * Muốn đổi sang Google Maps sau này: thay DUY NHẤT component này, phần còn lại không đụng.
 */
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import type { SearchResultItem } from '@moodbite/api-client';
import { useEffect } from 'react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  formatDistance,
  formatPrice,
  formatRating,
  hasCoordinates,
} from '@/entities/restaurant';

// Leaflet mặc định trỏ icon marker tới đường dẫn tương đối, vỡ khi build bằng Vite.
// Dùng icon vẽ bằng CSS để không phụ thuộc file ảnh.
const restaurantIcon = L.divIcon({
  className: 'map-pin',
  html: '<span class="map-pin__dot"></span>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// Ghim của quán ĐANG ĐƯỢC CHỌN: to hơn + có quầng sáng, để mắt bắt được ngay khi
// người dùng bấm vào một thẻ trong danh sách.
const activeIcon = L.divIcon({
  className: 'map-pin map-pin--active',
  html: '<span class="map-pin__dot"></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

const userIcon = L.divIcon({
  className: 'map-pin map-pin--user',
  html: '<span class="map-pin__dot"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

interface Coordinates {
  lat: number;
  lng: number;
}

/** Bản đồ không tự đi theo khi tâm đổi -> phải ra lệnh tường minh. */
function RecenterOnChange({ center }: { center: Coordinates }) {
  const map = useMap();
  useEffect(() => {
    map.setView([center.lat, center.lng]);
  }, [map, center.lat, center.lng]);
  return null;
}

/**
 * GHIM MANG SỐ, khớp với số thứ tự trên thẻ quán bên danh sách.
 *
 * Chủ dự án chốt 2026-08-27 theo `design/restaurance recommend.png`. Trước đó ghim là
 * chấm tròn trơn, nên nhìn 20 chấm giống hệt nhau trên bản đồ mà không biết chấm nào
 * ứng với quán nào trong danh sách — bản đồ và danh sách là hai thứ rời rạc.
 *
 * Dựng bằng `divIcon` (HTML thuần) thay vì file ảnh: số thay đổi theo từng quán nên
 * không thể là ảnh tĩnh, và cách này không thêm phụ thuộc nào.
 */
function ghimSo(so: number, dangChon: boolean) {
  return L.divIcon({
    className: dangChon ? 'map-pin-so map-pin-so--dang' : 'map-pin-so',
    html: `<span class="map-pin-so__so">${so}</span>`,
    iconSize: dangChon ? [30, 30] : [26, 26],
    iconAnchor: dangChon ? [15, 15] : [13, 13],
  });
}

interface RestaurantMapProps {
  restaurants: SearchResultItem[];
  center: Coordinates;
  userPosition?: Coordinates | null;
  /** placeId của quán đang chọn - ghim tương ứng sẽ được làm nổi. */
  activeId?: string | null;
  onSelect?: (restaurant: SearchResultItem) => void;
  /**
   * Đánh số ghim 1, 2, 3… theo ĐÚNG thứ tự danh sách bên cạnh.
   *
   * Mặc định `false` để trang tìm kiếm giữ nguyên ghim chấm — ở đó danh sách cuộn độc
   * lập với bản đồ nên số thứ tự không nối được hai bên với nhau.
   */
  danhSo?: boolean;
}

export function RestaurantMap({
  restaurants,
  center,
  userPosition,
  activeId,
  onSelect,
  danhSo = false,
}: RestaurantMapProps) {
  // ⚠️ Đánh số TRƯỚC khi lọc toạ độ, để số trên ghim khớp số trên thẻ.
  // Lọc trước rồi mới đánh số thì một quán thiếu toạ độ sẽ làm lệch toàn bộ số phía sau:
  // thẻ số 5 ứng với ghim số 4, và không ai hiểu vì sao.
  const daDanhSo = restaurants.map((r, i) => ({ quan: r, so: i + 1 }));
  const withCoordinates = daDanhSo.filter((x) => hasCoordinates(x.quan));

  return (
    <MapContainer
      className="map"
      center={[center.lat, center.lng]}
      zoom={14}
      scrollWheelZoom
      style={{ height: '100%', width: '100%' }}
    >
        {/* Ghi công là BẮT BUỘC theo giấy phép ODbL của OpenStreetMap. */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <RecenterOnChange center={center} />

        {userPosition && (
          <Marker position={[userPosition.lat, userPosition.lng]} icon={userIcon}>
            <Popup>Vị trí của bạn</Popup>
          </Marker>
        )}

        {withCoordinates.map(({ quan: restaurant, so }) => (
          <Marker
            key={restaurant.restaurant_id ?? `${restaurant.latitude},${restaurant.longitude}`}
            position={[restaurant.latitude, restaurant.longitude]}
            icon={
              danhSo
                ? ghimSo(so, restaurant.restaurant_id === activeId)
                : activeId && restaurant.restaurant_id === activeId
                  ? activeIcon
                  : restaurantIcon
            }
            eventHandlers={onSelect ? { click: () => onSelect(restaurant) } : undefined}
          >
            <Popup>
              <strong>{restaurant.name}</strong>
              {restaurant.address && <div>{restaurant.address}</div>}
              <div>{formatDistance(restaurant.distance_m)}</div>
              {/* null = CHƯA CÓ dữ liệu, không phải "0 sao". */}
              <div>{formatRating(restaurant.rating, restaurant.user_ratings_total)}</div>
              {formatPrice(restaurant.price_range) && (
                <div>{formatPrice(restaurant.price_range)}</div>
              )}
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );
}
