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
import { useEffect, useId, useState } from 'react';
import { MapContainer, Marker, useMap, useMapEvents } from 'react-leaflet';
import type { Map as LeafletMap } from 'leaflet';
import { NenBanDo } from '@/shared/map';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { HANOI_CENTER } from '@/shared/config';
import { useT } from '@/shared/i18n';
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

/**
 * Điểm đổi từ BÊN NGOÀI bản đồ (nút "Vị trí của tôi") mà nằm ngoài khung đang nhìn →
 * đưa bản đồ tới đó. `MapContainer.center` chỉ đọc lúc dựng, nên thiếu bước này thì ghim
 * mới nằm khuất ngoài khung và người dùng tưởng chưa chọn được (audit 2026-10-06).
 * Điểm vẫn trong khung (vd. vừa bấm lên bản đồ) thì KHÔNG kéo bản đồ đi — giật mắt.
 */
function TheoDiem({ point }: { point: DiemChon | null }) {
  const map = useMap();
  const lat = point?.lat;
  const lng = point?.lng;
  useEffect(() => {
    if (lat === undefined || lng === undefined) return;
    if (!map.getBounds().contains([lat, lng])) map.setView([lat, lng]);
  }, [map, lat, lng]);
  return null;
}

export interface PointPickerMapProps {
  point: DiemChon | null;
  onPick: (p: DiemChon) => void;
}

export function PointPickerMap({ point, onPick }: PointPickerMapProps) {
  const t = useT();
  const tam = point ?? HANOI_CENTER;
  // Giữ instance bản đồ để nút bên dưới đọc được TÂM hiện tại.
  const [map, setMap] = useState<LeafletMap | null>(null);
  const idGoiY = useId();

  return (
    <div className="dc-picker">
      <MapContainer
        ref={setMap}
        className="dc-map"
        center={[tam.lat, tam.lng]}
        zoom={13}
        scrollWheelZoom={false}
      >
        <NenBanDo />
        <BatCuBam onPick={onPick} />
        <TheoDiem point={point} />
        {point && <Marker position={[point.lat, point.lng]} icon={ghim} />}
      </MapContainer>
      {/* LỐI KHÔNG CẦN CHUỘT (audit 2026-10-06): bị chặn định vị thì cách duy nhất để chọn
          điểm từng là bấm chuột lên bản đồ. Leaflet cho di chuyển bản đồ bằng phím mũi
          tên khi bản đồ có focus; nút này đặt ghim ở TÂM khung đang nhìn. */}
      <button
        type="button"
        className="btn btn--link dc-picker__center"
        disabled={!map}
        aria-describedby={idGoiY}
        onClick={() => {
          if (!map) return;
          const c = map.getCenter();
          onPick({ lat: c.lat, lng: c.lng });
        }}
      >
        {t('addresses.pinCenter')}
      </button>
      <p id={idGoiY} className="muted small">
        {t('addresses.pinCenterHint')}
      </p>
    </div>
  );
}
