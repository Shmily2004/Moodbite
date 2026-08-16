# Tích hợp bản đồ + vị trí người dùng

**Mục tiêu đã chọn:** (1) hiện kết quả trên bản đồ, (2) lấy vị trí thật của người dùng.
**Không làm:** Routes API (thời gian đi thật) và Places API (bổ sung rating/ảnh) — cả hai
đều tính tiền theo từng request và chưa cần cho mục tiêu hiện tại.

---

## ⭐ PHƯƠNG ÁN MIỄN PHÍ — Leaflet + OpenStreetMap (KHUYẾN NGHỊ)

**Google Maps JavaScript API bắt buộc bật thanh toán (cần thẻ tín dụng/ghi nợ) dù có hạn
mức miễn phí hàng tháng.** Không có thẻ thì không dùng được, kể cả khi chỉ dùng rất ít.

**Leaflet + tile OpenStreetMap: miễn phí hoàn toàn, KHÔNG cần key, KHÔNG cần thẻ.**

```bash
cd frontend
npm install leaflet react-leaflet
```

```jsx
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { HANOI_CENTER } from './useUserLocation'

export default function RestaurantMap({ restaurants = [], userPosition }) {
  const center = userPosition || HANOI_CENTER

  return (
    <MapContainer center={[center.lat, center.lng]} zoom={14}
                  style={{ height: 420, width: '100%' }}>
      {/* Ghi công là BẮT BUỘC theo giấy phép ODbL của OpenStreetMap */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {restaurants
        .filter(r => r.lat != null && r.lng != null)
        .map(r => (
          <Marker key={r.id ?? `${r.lat},${r.lng}`} position={[r.lat, r.lng]}>
            <Popup>
              <strong>{r.name}</strong>
              <div>{r.address}</div>
              <div>{r.distanceM} m</div>
              {/* null = CHƯA CÓ dữ liệu, không phải 0 sao */}
              {r.rating != null && <div>{r.rating} ★</div>}
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  )
}
```

### So sánh hai phương án

| | Leaflet + OSM | Google Maps |
|---|---|---|
| Chi phí | ✅ **Miễn phí hoàn toàn** | 🟡 Có hạn mức miễn phí nhưng **cần thẻ** |
| API key | ✅ Không cần | ❌ Bắt buộc |
| Chất lượng bản đồ VN | 🟡 Tốt, ít chi tiết hơn | ✅ Chi tiết nhất |
| Nhất quán giấy phép | ✅ Dữ liệu quán cũng từ OSM | 🟡 Trộn hai nguồn |
| Đổi sang cái kia sau này | ✅ Chỉ thay 1 component | ✅ |

**Với đồ án tốt nghiệp, Leaflet là lựa chọn đúng** — chứng minh được năng lực kỹ thuật y
hệt, không phát sinh chi phí, và nhất quán với việc dữ liệu quán vốn đã lấy từ OSM.

⚠️ Lưu ý về tile OSM công cộng: có [chính sách sử dụng](https://operations.osmfoundation.org/policies/tiles/)
giới hạn lưu lượng, đủ cho đồ án và demo nhưng không dành cho sản phẩm lưu lượng lớn.
Khi cần mở rộng, chuyển sang nhà cung cấp tile khác (MapTiler, Stadia…) — chỉ đổi 1 dòng `url`.

**Phần định vị người dùng ở mục 2 dưới đây dùng chung cho cả hai phương án.**

---

## Phương án Google Maps (chỉ khi đã có thẻ thanh toán)

---

## 1. Tin tốt: backend KHÔNG cần sửa gì

`POST /api/recommend` đã trả sẵn toạ độ. Response thật (đã kiểm chứng):

```json
{
  "placeId": "ChIJa8RmJwmrNTERuzIIN1YJYtk",
  "name": "Ốc Hằng Mập - Ốc Ngon, Hải Sản Tươi...",
  "address": "82 P. Dương Khuê, Từ Liêm, Hà Nội, Việt Nam",
  "lat": 21.0336942,
  "lng": 105.7723742,
  "distance_km": 8.51,
  "rating": 4.9,
  "price": "100-200 N ₫"
}
```

**Cả 4170/4170 quán đều có `lat`/`lng`** → vẽ bản đồ được ngay, không cần cào thêm dữ liệu,
không cần gọi Geocoding API.

API cũng đã nhận `user_lat` / `user_lng`, nên chỉ cần truyền vị trí thật vào là xong.

---

## 2. Phần MIỄN PHÍ: lấy vị trí người dùng

Geolocation API là tính năng sẵn có của trình duyệt — **không cần key, không tốn tiền,
không liên quan gì tới Google**.

`frontend/src/features/map/useUserLocation.js`:

```js
import { useState, useCallback } from 'react'

// Mặc định: Hồ Hoàn Kiếm — dùng khi người dùng từ chối chia sẻ vị trí.
// Phải khớp với HANOI_CENTER trong src/domain/value_objects/location.py.
export const HANOI_CENTER = { lat: 21.0285, lng: 105.8542 }

export default function useUserLocation() {
  const [position, setPosition] = useState(HANOI_CENTER)
  const [isDefault, setIsDefault] = useState(true)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setError('Trình duyệt không hỗ trợ định vị.')
      return
    }
    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setPosition({ lat: coords.latitude, lng: coords.longitude })
        setIsDefault(false)
        setError(null)
        setLoading(false)
      },
      (err) => {
        // Từ chối chia sẻ vị trí KHÔNG phải lỗi — vẫn dùng được với vị trí mặc định.
        const messages = {
          1: 'Bạn đã từ chối chia sẻ vị trí. Đang dùng trung tâm Hà Nội.',
          2: 'Không xác định được vị trí. Đang dùng trung tâm Hà Nội.',
          3: 'Quá thời gian chờ định vị. Đang dùng trung tâm Hà Nội.',
        }
        setError(messages[err.code] || 'Không lấy được vị trí.')
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    )
  }, [])

  return { position, isDefault, error, loading, request }
}
```

**Ba điều bắt buộc nhớ:**

1. **Chỉ chạy trên HTTPS** (hoặc `localhost`). Trên `http://` thật, trình duyệt chặn thẳng.
2. **Đừng gọi tự động khi vừa mở trang.** Trình duyệt hiện hộp thoại xin quyền — hỏi khi
   chưa có ngữ cảnh thì đa số người dùng bấm "Từ chối", và sau đó rất khó hỏi lại.
   Nên gắn vào một nút: *"Dùng vị trí của tôi"*.
3. **Bị từ chối không phải lỗi.** Luôn còn vị trí mặc định để chạy tiếp.

Truyền vào API:

```js
const { position } = useUserLocation()
fetchRecommend({ mood, userLat: position.lat, userLng: position.lng, maxDistance })
```

---

## 3. Phần CẦN KEY: bản đồ Google Maps

### 3.1 Lấy API key

1. Vào [console.cloud.google.com](https://console.cloud.google.com) → tạo project (VD `moodbite`)
2. **Bật thanh toán** — bắt buộc, kể cả khi dùng trong hạn mức miễn phí
3. *APIs & Services → Library* → bật **Maps JavaScript API**
   (chỉ cần API này; **không** bật Places/Routes nếu chưa dùng)
4. *Credentials → Create credentials → API key*

### 3.2 ⚠️ Giới hạn key NGAY — bước quan trọng nhất

Key dùng cho Maps JavaScript API **bắt buộc nằm trong mã nguồn phía trình duyệt**, nên ai
cũng xem được. Cách bảo vệ duy nhất là giới hạn theo tên miền:

*Credentials → bấm vào key →*

- **Application restrictions** → *Websites*, thêm:
  - `http://localhost:5173/*` (Vite khi dev)
  - `https://ten-mien-that-cua-ban.com/*`
- **API restrictions** → *Restrict key* → chỉ chọn **Maps JavaScript API**

> Không giới hạn key = người khác dùng key của bạn và **bạn trả tiền**.
> Nên đặt thêm hạn mức cảnh báo ở *Billing → Budgets & alerts*.

### 3.3 Chi phí

Google có hạn mức miễn phí hàng tháng cho Maps JavaScript API, thường thừa sức cho một đồ
án. Chính sách giá của Google **có thay đổi theo thời gian**, nên hãy tự kiểm tra hạn mức
hiện hành tại [Google Maps Platform Pricing](https://mapsplatform.google.com/pricing/)
thay vì tin một con số chép sẵn ở đây.

Cách giữ chi phí gần như bằng 0:
- Chỉ bật **Maps JavaScript API** (không bật Places/Routes/Geocoding)
- Không tạo lại bản đồ mỗi lần đổi mood — chỉ cập nhật marker
- Đặt ngân sách cảnh báo trong Cloud Console

### 3.4 Cấu hình key trong dự án

`frontend/.env.local` (**không commit file này**):

```
VITE_GOOGLE_MAPS_API_KEY=AIza...
VITE_API_BASE=http://localhost:8001/api
```

`frontend/.env.example` (**có commit**, để người khác biết cần biến gì):

```
VITE_GOOGLE_MAPS_API_KEY=
VITE_API_BASE=http://localhost:8001/api
```

Kiểm tra `.gitignore` đã có `.env.local`.

> Biến `VITE_*` được nhúng thẳng vào file build — **coi như công khai**. Đây là lý do
> bước giới hạn key ở 3.2 là bắt buộc, không phải tuỳ chọn.

### 3.5 Cài thư viện

```bash
cd frontend
npm install @vis.gl/react-google-maps
```

Đây là thư viện React chính thức do Google duy trì — tự lo việc nạp script, tránh nạp
trùng khi component re-render.

### 3.6 Component bản đồ

`frontend/src/features/map/RestaurantMap.jsx`:

```jsx
import { APIProvider, Map, AdvancedMarker, Pin, InfoWindow }
  from '@vis.gl/react-google-maps'
import { useState } from 'react'
import { HANOI_CENTER } from './useUserLocation'

const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

export default function RestaurantMap({ restaurants = [], userPosition }) {
  const [selected, setSelected] = useState(null)

  // Thiếu key thì báo rõ, không để bản đồ xám trắng không ai hiểu vì sao.
  if (!API_KEY) {
    return (
      <div className="map-fallback">
        Chưa cấu hình <code>VITE_GOOGLE_MAPS_API_KEY</code> trong{' '}
        <code>frontend/.env.local</code>. Xem docs/google_maps_integration.md
      </div>
    )
  }

  const center = userPosition || HANOI_CENTER

  return (
    <APIProvider apiKey={API_KEY}>
      <div style={{ height: 420, width: '100%' }}>
        <Map
          defaultCenter={center}
          defaultZoom={13}
          mapId="moodbite-map"
          gestureHandling="greedy"
          disableDefaultUI={false}
        >
          {userPosition && (
            <AdvancedMarker position={userPosition} title="Vị trí của bạn">
              <Pin background="#1a73e8" borderColor="#fff" glyphColor="#fff" />
            </AdvancedMarker>
          )}

          {restaurants
            .filter(r => r.lat != null && r.lng != null)
            .map(r => (
              <AdvancedMarker
                key={r.placeId ?? `${r.lat},${r.lng}`}
                position={{ lat: r.lat, lng: r.lng }}
                title={r.name}
                onClick={() => setSelected(r)}
              >
                <Pin background="#ea4335" borderColor="#fff" glyphColor="#fff" />
              </AdvancedMarker>
            ))}

          {selected && (
            <InfoWindow
              position={{ lat: selected.lat, lng: selected.lng }}
              onCloseClick={() => setSelected(null)}
            >
              <div style={{ maxWidth: 220 }}>
                <strong>{selected.name}</strong>
                <div>{selected.address}</div>
                <div>{selected.distance_km} km</div>
                {/* null = CHƯA CÓ dữ liệu, không phải 0 sao / miễn phí */}
                {selected.rating != null && <div>{selected.rating} ★</div>}
                {selected.price && <div>{selected.price}</div>}
              </div>
            </InfoWindow>
          )}
        </Map>
      </div>
    </APIProvider>
  )
}
```

### 3.7 Ghép vào trang

```jsx
const { position, isDefault, error, request } = useUserLocation()
const { recs, load } = useRecommend()

<button onClick={request}>Dùng vị trí của tôi</button>
{isDefault && <p className="hint">Đang dùng trung tâm Hà Nội làm vị trí mặc định.</p>}
{error && <p className="warn">{error}</p>}

<RestaurantMap
  restaurants={recs?.recommendations ?? []}
  userPosition={isDefault ? null : position}
/>
```

---

## 4. Thứ tự làm

1. [ ] `useUserLocation.js` + nút "Dùng vị trí của tôi" — **miễn phí, làm trước, kiểm chứng ngay**
2. [ ] Truyền `user_lat`/`user_lng` thật vào `/api/recommend`
3. [ ] Lấy API key, **giới hạn key**, đặt ngân sách cảnh báo
4. [ ] `.env.local` + `.env.example`
5. [ ] `npm install @vis.gl/react-google-maps`
6. [ ] `RestaurantMap.jsx`
7. [ ] Ghép vào trang gợi ý

Bước 1-2 làm được ngay mà chưa cần key — và đã cải thiện sản phẩm rõ rệt.

---

## 5. Không cần Google Maps API cho những việc sau

| Việc | Cách làm không tốn tiền |
|---|---|
| Khoảng cách tới quán | Backend đã tính bằng haversine |
| Mở quán trên Google Maps | Dùng field `google_maps_url` trong `/api/restaurant/{id}` |
| Địa chỉ quán | Đã có sẵn trong dataset (100% quán) |
| Toạ độ quán | Đã có sẵn (100% quán) |

Nhắc lại: `distance_km` là **đường chim bay**, không phải quãng đường đi thật. Muốn số thật
phải dùng Routes API (tính tiền mỗi request). Nếu chưa dùng, nên ghi trên giao diện là
"khoảng cách theo đường chim bay" để không gây hiểu nhầm.
