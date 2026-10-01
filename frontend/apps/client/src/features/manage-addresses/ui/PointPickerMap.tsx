/**
 * Bản đồ CHỌN ĐIỂM — Leaflet + tile OpenStreetMap (miễn phí, không key, không Google).
 *
 * Không dùng lại `widgets/restaurant-map`: feature không được import widget (FSD chỉ cho
 * đi xuống), và bản đồ đó vẽ danh sách quán, còn ở đây chỉ cần bắt MỘT cú bấm.
 *
 * Không chặn cú bấm ngoài Hà Nội ở đây: phạm vi Hà Nội là luật nghiệp vụ và nằm ở backend
 * (`trong_ha_noi`). Bấm ra ngoài thì server trả 400 kèm câu giải thích, và giao diện hiện
 * nguyên văn câu đó.
 */
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { HANOI_CENTER } from '@/shared/config';
import type { DiemChon } from '../model/useAddressForm';

// Icon vẽ bằng CSS (cùng lý do với RestaurantMap): icon ảnh mặc định của Leaflet vỡ khi
// build bằng Vite.
const ghim = L.divIcon({
  className: 'map-pin map-pin--user',
  html: '<span class="map-pin__dot"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

function BatCuBam({ onPick }: { onPick: (p: DiemChon) => void }) {
  useMapEvents({
    click: (e) => onPick({ lat: e.latlng.lat, lng: e.latlng.lng }),
  });
  return null;
}

export interface PointPickerMapProps {
  point: DiemChon | null;
  onPick: (p: DiemChon) => void;
}

export function PointPickerMap({ point, onPick }: PointPickerMapProps) {
  const tam = point ?? HANOI_CENTER;
  return (
    <MapContainer
      className="dc-map"
      center={[tam.lat, tam.lng]}
      zoom={13}
      scrollWheelZoom={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <BatCuBam onPick={onPick} />
      {point && <Marker position={[point.lat, point.lng]} icon={ghim} />}
    </MapContainer>
  );
}
