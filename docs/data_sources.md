# Đánh giá nguồn dữ liệu quán ăn

Tài liệu này giải thích **vì sao MoodBite dùng nguồn nào**, và vì sao KHÔNG dùng nguồn khác.
Đọc trước khi định thêm một nguồn mới.

---

## 1. Bảng đánh giá

Đánh giá theo 11 tiêu chí đã đặt ra. Thang: ✅ tốt · 🟡 hạn chế · ❌ không dùng được.

| Nguồn | Độ phủ HN | Chất lượng | Rating/Review | Tự động hoá | Chi phí | Pháp lý / ToS | Kết luận |
|---|---|---|---|---|---|---|---|
| **OpenStreetMap (Overpass)** | ✅ ~4.400 POI | 🟡 tên/toạ độ tốt, thiếu rating | ❌ không có | ✅ API mở, không key | ✅ miễn phí | ✅ ODbL, chỉ cần ghi công | **ĐANG DÙNG - nguồn chính** |
| **Google Places API** | ✅ tốt nhất | ✅ tốt nhất | ✅ đầy đủ | ✅ API chính thức | ❌ trả tiền/request, cần thẻ | 🟡 cấm lưu trữ lâu dài phần lớn field | **Đã cắm sẵn chỗ, chờ key** |
| **Apify Google Maps Scraper** | ✅ tốt | ✅ tốt | ✅ có | 🟡 cần tài khoản trả phí | ❌ trả phí | 🟡 vùng xám ToS Google | **Đã dùng trước đó (546 quán), không chạy lại được** |
| **ShopeeFood** | ✅ rất tốt cho quán giao đồ | ✅ có menu + giá THẬT | ✅ có | ❌ không có API công khai | — | ❌ ToS cấm thu thập tự động | **KHÔNG DÙNG** |
| **GrabFood** | ✅ tốt | ✅ có menu + giá | ✅ có | ❌ không có API công khai | — | ❌ ToS cấm | **KHÔNG DÙNG** |
| **Facebook / Fanpage** | 🟡 phân mảnh | ❌ không có cấu trúc | 🟡 | ❌ | — | ❌ ToS cấm scraping | **KHÔNG DÙNG** |
| **Foody / TripAdvisor** | ✅ tốt | ✅ có review | ✅ có | ❌ chặn bot | — | ❌ ToS cấm | **KHÔNG DÙNG** |
| **Nominatim (OSM)** | — | — | ❌ | 🟡 1 req/giây | ✅ miễn phí | ✅ ODbL | **Chỉ dùng khi cần geocode lẻ** |
| **Wikidata** | ❌ rất ít quán ăn | ✅ chuẩn | ❌ | ✅ SPARQL mở | ✅ miễn phí | ✅ CC0 | Không đáng công |

---

## 2. Vì sao chọn OpenStreetMap làm nguồn chính

**Ưu điểm quyết định:**
- Không cần API key, không cần thẻ tín dụng → đồ án chạy được trên máy bất kỳ ai.
- Giấy phép ODbL cho phép dùng lại và phân phối (chỉ cần ghi công).
- Phủ **100%** hai trường sống còn: tên + toạ độ.
- Nhiều tag hữu ích mà bản cào cũ **bỏ phí**: `opening_hours`, `phone`, `website`,
  `cuisine`, `outdoor_seating`, `air_conditioning`, `diet:vegetarian`, `takeaway`, `delivery`.

**Nhược điểm phải nói thẳng:**
- **KHÔNG có rating, KHÔNG có review, KHÔNG có ảnh.** Đây là dữ liệu bản đồ, không phải
  nền tảng đánh giá. Không có cách nào lấy được từ OSM.
- Giá gần như không có.
- Dữ liệu cộng đồng đóng góp → có thể cũ hoặc thiếu.

→ Vì vậy `data_confidence` của mọi bản ghi OSM là `community`, thấp hơn `verified`.

---

## 3. Vì sao KHÔNG scrape ShopeeFood / GrabFood / Foody / Facebook

Đây là câu hỏi hợp lý vì các nền tảng này có **đúng thứ MoodBite đang thiếu**: menu thật,
giá thật, review thật.

Lý do không làm:

1. **Điều khoản sử dụng cấm rõ ràng.** ToS của cả 4 nền tảng đều cấm truy cập tự động và
   sao chép nội dung có hệ thống. Một đồ án tốt nghiệp không nên xây trên nền vi phạm ToS —
   đây là điểm rất dễ bị hỏi khi bảo vệ.
2. **Không có API công khai.** Muốn lấy phải giả lập trình duyệt, vượt chống bot — vừa
   mong manh vừa rõ ràng là cố tình lách.
3. **Không bền vững.** Các nền tảng đổi giao diện liên tục; scraper hỏng là dataset chết.
4. **Rủi ro pháp lý về dữ liệu cá nhân.** Review có tên người dùng → là dữ liệu cá nhân.

**Thay thế hợp pháp cho cùng nhu cầu:**

| Muốn có | Cách hợp pháp |
|---|---|
| Menu / món ăn | Suy luận từ tên quán + `cuisine` của OSM (đang làm) hoặc nhập tay có kiểm duyệt |
| Giá | Google Places API (có `price_level`) khi có key |
| Review | Google Places API, có giới hạn lưu trữ theo ToS |
| Đường link giao đồ ăn | Lưu **link** tới trang quán thay vì sao chép nội dung |

---

## 4. Kiến trúc cho phép thêm nguồn sau này

Mọi nguồn tuân theo **cùng một hợp đồng** ở `data_pipeline/sources/base.py`:

```
SourceAdapter.fetch()  ->  list[RawPlace]  ->  data_raw/NN_<source>.json
                                                       |
                                        merge_and_prepare_raw.py  (gộp + khử trùng lặp)
                                                       |
                                       data_cleaning.py -> feature_engineering.py
```

**Thêm nguồn mới = 3 bước, KHÔNG sửa pipeline:**

1. Tạo `data_pipeline/sources/<ten>.py` với class thoả `SourceAdapter`
2. Đăng ký vào `AVAILABLE_SOURCES` trong `data_pipeline/sources/__init__.py`
3. Chạy `python -m data_pipeline.harvest --source <ten>`

Nguồn chưa cấu hình (VD thiếu API key) tự báo qua `is_available()` và bị **bỏ qua**, không
làm hỏng cả lượt chạy.

### Khi nào bật Google Places

Khi có API key, viết `sources/google_places.py`. Nó sẽ lấp đúng những gì OSM thiếu:
`rating`, `user_ratings_total`, `price_level`, `photos`, `reviews`. Đặt
`data_confidence = "verified"` để tầng xếp hạng ưu tiên hơn dữ liệu `community`.

⚠️ Lưu ý ToS: Google cấm lưu trữ lâu dài phần lớn nội dung Places (trừ `place_id`).
Thiết kế đúng là **cache ngắn hạn + gọi lại khi cần**, không đổ hết vào CSV vĩnh viễn.

---

## 5. Khử trùng lặp giữa các nguồn

Cùng một quán xuất hiện ở nhiều nguồn với `placeId` khác nhau
(`ChIJ...` của Google vs `osm-node-...` của OSM).

Chiến lược hiện tại (`merge_and_prepare_raw.py`):
1. Trùng theo `placeId` → giữ bản đầu tiên.
2. Không có `placeId` → so cặp `(title, address)` đã chuẩn hoá.

**Hạn chế đã biết:** hai nguồn khác nhau mô tả cùng một quán bằng tên hơi khác
("Phở Thìn" vs "Pho Thin Bo Ho") sẽ **không** bị coi là trùng. Cách xử lý đúng khi có
nhiều nguồn hơn là so khớp theo **khoảng cách địa lý + độ tương đồng tên**
(VD: cùng bán kính 50m và tên giống ≥ 80%). Chưa làm vì hiện chỉ có 2 nguồn và
`placeId` đã tách bạch rõ.

---

## 6. Trường dữ liệu: cái gì có, cái gì không

| Trường yêu cầu | Trạng thái | Nguồn |
|---|---|---|
| restaurant_id / place_id | ✅ 100% | OSM + Google |
| tên quán | ✅ 100% | OSM + Google |
| aliases | ✅ có khi OSM ghi `name:en`/`alt_name` | OSM |
| category | ✅ 100% | OSM + Google |
| cuisine | 🟡 một phần | OSM `cuisine` |
| dishes | 🟡 suy luận, không phải menu thật | tên quán + `cuisine` |
| address / street | ✅ | OSM `addr:*` |
| district | ✅ suy từ toạ độ | ranh giới hành chính OSM |
| latitude / longitude | ✅ 100% | OSM + Google |
| phone | 🟡 thưa | OSM `phone` |
| website | 🟡 thưa | OSM + Google |
| opening hours | 🟡 một phần | OSM + Google |
| price range | 🟡 rất thưa | chỉ Google |
| rating / review count | 🟡 rất thưa | **chỉ Google** - OSM không có |
| review text | 🟡 rất thưa | chỉ Google |
| photos | 🟡 rất thưa | chỉ Google |
| amenities | ✅ mới bổ sung | OSM tag |
| atmosphere | 🟡 thưa | Google `additionalInfo` |
| dietary | ✅ mới bổ sung | OSM `diet:*` |
| delivery / takeaway | ✅ mới bổ sung | OSM tag |
| delivery platform | ❌ **không lấy được hợp pháp** | — |
| menu | ❌ hầu như không có | — |
| source / source_url / last_updated / data_confidence | ✅ 100% (bản ghi mới) | pipeline tự gắn |

**Kết luận trung thực:** dataset ĐỦ để làm bản đồ, tìm kiếm, lọc theo khu vực/tiện nghi/
chế độ ăn/giờ mở cửa. CHƯA đủ để làm tính năng dựa trên **giá** hoặc **đánh giá**, và sẽ
không đủ chừng nào chưa có Google Places API key.
