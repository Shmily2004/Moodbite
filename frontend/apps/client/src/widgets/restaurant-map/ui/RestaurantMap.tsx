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

interface RestaurantMapProps {
  restaurants: SearchResultItem[];
  center: Coordinates;
  userPosition?: Coordinates | null;
  onSelect?: (restaurant: SearchResultItem) => void;
}

export function RestaurantMap({
  restaurants,
  center,
  userPosition,
  onSelect,
}: RestaurantMapProps) {
  const withCoordinates = restaurants.filter(hasCoordinates);

  return (
    <div className="map">
      <MapContainer
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

        {withCoordinates.map((restaurant) => (
          <Marker
            key={restaurant.restaurant_id ?? `${restaurant.latitude},${restaurant.longitude}`}
            position={[restaurant.latitude, restaurant.longitude]}
            icon={restaurantIcon}
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
    </div>
  );
}
