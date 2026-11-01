/**
 * Bản đồ MỘT quán - Leaflet + OpenStreetMap, miễn phí, không cần key (CLAUDE.md 1b).
 *
 * Không dùng lại `widgets/restaurant-map`: widget đó nhận DANH SÁCH kết quả tìm kiếm
 * (`SearchResultItem[]`, có `distance_m`, `rank_position`...) - ép một quán vào kiểu đó
 * nghĩa là bịa các trường còn thiếu. Bản đồ một ghim chỉ cần toạ độ.
 */
import { MapContainer, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { NenBanDo } from '@/shared/map';

/** Đủ gần để thấy tên phố quanh quán, đủ xa để còn nhận ra khu vực. */
const ZOOM_MOT_QUAN = 16;

// Cùng kiểu ghim vẽ bằng CSS với bản đồ danh sách (`.map-pin--active`) - không phụ
// thuộc file ảnh marker của Leaflet, vốn vỡ đường dẫn khi build bằng Vite.
const ghim = L.divIcon({
  className: 'map-pin map-pin--active',
  html: '<span class="map-pin__dot"></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

interface Props {
  lat: number;
  lng: number;
  name: string;
}

export function RestaurantLocationMap({ lat, lng, name }: Props) {
  return (
    <MapContainer
      className="map rest-map"
      center={[lat, lng]}
      zoom={ZOOM_MOT_QUAN}
      // Tắt cuộn chuột để phóng to: bản đồ nằm giữa trang, lăn chuột đọc tiếp mà bị bản
      // đồ "nuốt" mất thì rất khó chịu. Nút +/- vẫn dùng được.
      scrollWheelZoom={false}
      style={{ height: '100%', width: '100%' }}
    >
      <NenBanDo />
      <Marker position={[lat, lng]} icon={ghim} title={name} alt={name} />
    </MapContainer>
  );
}
