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
| **Wikidata** | ❌ rất ít quán ăn | ✅ chuẩn | ❌ | ✅ SPARQL mở | ✅ miễn phí | ✅ CC0 | Không đáng công **cho quán** — nhưng ĐANG DÙNG cho MÓN, xem mục 5 |
| **Foursquare OS Places** | ? chưa đo được | ? | 🟡 | ❌ bộ dữ liệu bị khoá | ✅ miễn phí | ✅ Apache-2.0 | **THỬ 2026-08-24, KHÔNG DÙNG ĐƯỢC** — xem mục 6 |

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

---

## Nguồn dữ liệu MÓN ĂN (bổ sung 2026-08-19)

Luồng "chọn món trước, tìm quán sau" cần một danh mục MÓN, không chỉ danh sách quán.
Ba nguồn dưới đây đều **miễn phí, hợp pháp, không cần thẻ thanh toán**.

| Nguồn | Cho ra cái gì | Lệnh |
|---|---|---|
| `dish_knowledge_base.json` | 38 rule cũ → 60 món, đã gắn với quán thật | có sẵn |
| Khai thác **TÊN QUÁN** trong dataset | món có quán bán CHẮC CHẮN (đo được) | `scripts/build_dish_catalog.py` |
| **Nội dung REVIEW** (đề án mục 7) | quán bán món nhưng không ghi lên biển hiệu | tự động trong `dish_matching.py` |
| **Wikipedia tiếng Việt** (CC BY-SA) | giới thiệu ngắn + ảnh + món mới (37 thể loại, quét 1959 trang) | `scripts/discover_dishes.py` |

### Vì sao khai thác tên quán là nguồn tốt nhất

Đo ngày 2026-08-18 trên 4938 quán: đếm cụm từ trong TÊN QUÁN lộ ra hàng loạt món phổ biến
chưa có rule nào phủ — `bún cá` 39 quán, `trà chanh` 35, `nem nướng` 26, `bún ốc` 25,
`chả cá` 11. Đây là nguồn **duy nhất** đảm bảo món thêm vào có quán thật bán, vì nó lấy
chính từ dữ liệu quán mình đang có. Không tốn một lần gọi mạng nào.

### Wikipedia: dùng cái gì và KHÔNG dùng cái gì

| Lấy | Không lấy |
|---|---|
| ✅ Đoạn mở đầu (REST summary) làm GIỚI THIỆU NGẮN | ❌ Trích thành phần bằng regex trên thân bài |
| ✅ `thumbnail` (~320px) làm ảnh minh hoạ | ❌ `originalimage` (có ảnh 8MB) |
| ✅ Thể loại (category) để tìm món mới | ❌ Wikidata SPARQL lọc theo nước |

**Hai thứ đã thử rồi BỎ, đừng làm lại:**

1. **Regex bắt câu "Thành phần chính là..."** — đo trên 18 món, sinh dữ liệu SAI mà trông
   hợp lệ: `Bánh mì` → *"chất độn để chèn vào răng sâu"*, `Cơm tấm` → *"nguyên liệu khác."*
2. **Wikidata SPARQL lọc `P495 = Việt Nam`** — chạy được nhưng trả về cả bài hát, phim,
   thơ ("Tiến quân ca", "Bước nhảy hoàn vũ"). Lọc theo nước KHÔNG phải lọc theo món ăn.
   Truy vấn có duyệt cây `P279*` thì timeout 504.

**Một lỗi kỹ thuật đáng nhớ:** MediaWiki `prop=extracts&exintro` chỉ trả đoạn mở đầu cho
ĐÚNG MỘT trang mỗi request. Gộp 50 title vào một lần gọi thì 49 món về tay không — đây là
lý do độ phủ mô tả từng đo được chỉ 51.9% dù mọi lần gọi mạng đều thành công. Chuyển sang
REST summary (mỗi món một lần gọi, có cache) thì lên 100%.

---

## Nguồn dữ liệu QUÁN — mở rộng ra ngoài Hà Nội

`OsmOverpassSource` đã nhận `bbox` làm tham số từ đầu, nên thêm thành phố = thêm một dòng
vào `CITY_BBOXES` (`data_pipeline/sources/osm_overpass.py`), KHÔNG sửa pipeline:

```powershell
python -m data_pipeline.harvest --source openstreetmap --city ha_noi
python -m data_pipeline.harvest --source overture      --city ha_noi
```

> ⚠️ **CHỈ HÀ NỘI** (chốt 2026-08-19). Bảng `CITY_BBOXES` từng có 8 thành phố, nay chỉ còn
> `ha_noi`; truyền `--city` khác sẽ bị từ chối kèm thông báo. Sản phẩm chỉ phục vụ Hà Nội —
> thêm quán tỉnh khác làm loãng dữ liệu và khiến bộ lọc bán kính vô nghĩa.

Vẫn giữ nguyên các quy tắc Overpass đã trả giá để học: **chia ô** (hỏi cả thành phố một
lần luôn 504), **nhiều mirror + thử lại nhiều vòng** (504 là lỗi TẠM THỜI), **cache theo ô**.

---

## Kiểm soát DUNG LƯỢNG (máy chủ là laptop cá nhân)

```powershell
python scripts/disk_report.py                # đo
python scripts/disk_report.py --clean-cache  # xoá cache tra cứu (lấy lại được)
```

Ba quyết định giữ cho dữ liệu không phình:

1. **Ảnh món chỉ lưu ĐƯỜNG DẪN, không tải file về.** Đo thật: cache 1149 món = **790 KB**.
   Nếu tải ảnh về (~200KB/ảnh) thì cùng số món đó tốn khoảng **230 MB**.
2. **Cache tra cứu xoá được** — mất thì chỉ tốn công gọi lại mạng, không mất dữ liệu gốc.
3. **Mỗi nguồn một file thô riêng** — xoá được từng nguồn thay vì phải xoá cả cụm.

> Đã đo 2026-08-19: `data_raw` chiếm 353 MB, trong đó **210 MB là `floorplans_yolo`** —
> ảnh huấn luyện của tính năng floorplan→3D **đã tạm dừng** (code ở `archive/spatial-3d/`).
> Đây là chỗ dọn được nhiều nhất, nhưng script KHÔNG tự xoá: xoá thứ đang tồn tại thì phải
> hỏi chủ dự án trước (CLAUDE.md mục 8).


---

## 5. Nguồn MÓN ĂN (khác nguồn quán — đừng lẫn)

Ba nguồn, mỗi nguồn trả lời một câu hỏi khác nhau. Thiếu bất kỳ nguồn nào là mất một
loại món.

| Nguồn | Trả lời câu | Cách chạy | Giấy phép |
|---|---|---|---|
| **Wikipedia tiếng Việt** | "món này có tồn tại không" | `python scripts/discover_dishes.py --source wikipedia` | CC BY-SA |
| **Wikidata** | "món này còn tên gọi nào khác" | `python scripts/discover_dishes.py --source wikidata --merge-aliases` | **CC0** |
| **Tên quán trong dataset** | "món này có ai bán ở Hà Nội không" | `python scripts/mine_dish_names.py` | dữ liệu của chính dự án |

**Vì sao cần nguồn thứ ba.** Đo ngày 2026-08-23: **565/747 món (75,6%)** trong danh mục
không khớp một quán nào. Chúng đến từ Wikipedia, đều là món có thật, nhưng ở Hà Nội thì
là ngõ cụt với người dùng. Đào ngược từ TÊN của 53.461 quán thì món tìm được **luôn có
quán bán**, vì chính tên quán sinh ra nó.

**Vì sao cần Wikidata dù đã có Wikipedia.** Wikipedia không bao giờ cho biết TÊN GỌI KHÁC
của một món. Đo 2026-08-24: gộp `aliases` của Wikidata vào 55 món đang có thì thêm được
90 từ khoá khớp (`Mì Quảng` → `Mỳ Quảng`, `Bibimbap` → `cơm trộn`, `Pa tê sô` → 6 cách
viết khác).

**KHÔNG dùng SPARQL của Wikidata.** Đo 2026-08-24: `query.wikidata.org` trả HTTP 504 rồi
502 cho hai cách viết query khác nhau. Dùng API tìm kiếm + `wbgetentities` — xem
`data_pipeline/sources/wikidata_dish.py`.

### Cửa kiểm duyệt BẮT BUỘC

Cả ba nguồn đều trả về ứng viên **lẫn rác**, và rác ở đây không vô hại:

| Nguồn | Rác đo được 2026-08-24 |
|---|---|
| Tên quán | "Coffee tea" 357 quán · "Trung Nguyên" 234 · "Long Biên" 201 — thương hiệu và địa danh |
| Wikidata | "kho" 310 quán (cách chế biến, không phải món) · "Kun" · "Gui" · "Bûş" · "Koki" |

Nên `--apply` của cả hai script CHỈ thêm món có `dish_id` trong
`data_pipeline/dish_approved.json` — danh sách do người đọc và duyệt. Muốn bỏ qua thì
phải gõ hẳn `--apply-all`, và không nên.

---

## 6. Foursquare OS Places — đã thử, KHÔNG dùng được

Nghe rất hợp: bộ POI mở của Foursquare, giấy phép **Apache-2.0**, có sẵn category,
số điện thoại, mạng xã hội — đúng là nguồn thứ ba độc lập với OSM và Overture.

Thử ngày 2026-08-24, hai đường vào đều tắc:

1. **HuggingFace** (`foursquare/fsq-os-places`, bản mới nhất `dt=2026-08-11`, 100 file
   parquet): tải file trả **HTTP 401 Unauthorized** — bộ dữ liệu bị khoá, phải có tài
   khoản và bấm đồng ý điều khoản mới tải được.
2. **S3 công khai** (`fsq-os-places-us-east-1`): liệt kê thư mục trả về rỗng, và cả ba
   cách đặt tên file hợp lý (`places-00000.parquet`, `.zstd.parquet`, `.snappy.parquet`)
   đều trả **404** ở hai bản phát hành khác nhau.

Kể cả có tải được thì vẫn còn vấn đề dung lượng: 100 file parquet toàn cầu, và lược đồ
KHÔNG có cột `bbox` như Overture nên không chắc lọc được ở tầng đọc file.

→ Xem lại nếu Foursquare bỏ khoá. Chưa bỏ khoá thì **đừng thử lại**, đã tốn một lượt rồi.


---

## 7. PHẠM VI ĐỊA LÝ — bbox từng SAI và cắt mất 1/3 Hà Nội

Sửa 2026-08-24. Ghi lại vì đây là loại lỗi làm **mất dữ liệu mà không ai thấy gì bất thường**:
số quán vẫn tăng đều qua mỗi lượt cào, chỉ là một phần ba thành phố chưa bao giờ được hỏi tới.

### Số đo

| | vĩ độ | kinh độ |
|---|---|---|
| Hà Nội **thật** (OSM relation 1903516, `ISO3166-2=VN-HN`) | 20.5645 – 21.3854 | 105.2890 – 106.0200 |
| bbox **cũ** trong code | 20.8500 – 21.4000 | 105.7000 – 106.0500 |

Bản cũ **cắt mất**: toàn bộ phía tây (Ba Vì, Sơn Tây, Phúc Thọ, Thạch Thất, Quốc Oai,
Chương Mỹ — từ kinh độ 105.289) và phía nam (Mỹ Đức, Ứng Hoà, Phú Xuyên — từ vĩ độ
20.5645). Đồng thời **lấn** sang Bắc Ninh ở phía đông.

### Hậu quả đo được

- File ranh giới cache có **136 đơn vị** trong khi Hà Nội chỉ có **126** → 10 đơn vị thừa
  của tỉnh khác (`Phường Ninh Xá`, `Phường Hạp Lĩnh`, `Huyện Yên Phong`…).
- Tải lại theo ranh giới đúng: **thêm 41** đơn vị Hà Nội trước đây không có, **bỏ 51**
  đơn vị không thuộc Hà Nội.
- **3.184 quán (6,0%)** trong dataset nằm ở tỉnh khác: Từ Sơn/Tiên Du/Yên Phong (Bắc Ninh),
  Ecopark – Xã Phụng Công/Văn Giang/Như Quỳnh (Hưng Yên), Phúc Yên/Xuân Hoà (Vĩnh Phúc),
  Việt Yên/Hiệp Hoà (Bắc Giang). Vi phạm đúng quy tắc "CHỈ HÀ NỘI" của `CLAUDE.md` mục 4b.
- **904 quán** có `district` sai hoặc bẩn — dataset từng có **185** giá trị `district` khác
  nhau: `"Hoan Kiem"` (không dấu), `"Hà đông"` (khác hoa thường), `"quận Long Biên"` (lẫn
  tiền tố), `"Phố Phan Huy Chú"` (là TÊN PHỐ), `"Hà Nội"` (là thành phố).
- Overture cào lại với bbox đúng: **268.304 → 309.566 POI**, tức **+6.698 quán ăn uống**.

### Ba thứ đã sửa ở gốc

1. `HANOI_BBOX` lấy theo ranh giới thật, khai ở **một chỗ** (`sources/districts.py`) và
   `osm_overpass.py` import lại — trước đó hai file khai riêng, chắc chắn sẽ có ngày lệch.
2. `fetch_district_boundaries()` hỏi theo **AREA của Hà Nội** (`rel(1903516);map_to_area`)
   thay vì theo bbox. Cách này không phụ thuộc bbox có đúng hay không, nên lỗi cũ không
   lặp lại được. Comment cũ ghi "hỏi theo area luôn trả 504" là **sai**: đo lại chỉ mất
   ~20 giây. Nó hỏng vì tra theo TÊN `"Hà Nội"`, mà tên OSM là **"Thành phố Hà Nội"**.
3. `merge_and_prepare_raw` nay **gán lại** khu vực cho MỌI bản ghi từ toạ độ (không chỉ
   bản ghi trống) và **bỏ** quán không rơi vào đơn vị nào của Hà Nội. Có chốt an toàn:
   tải hụt ranh giới (<100 đơn vị) thì vẫn gán nhưng **KHÔNG lọc** — thà để lẫn thêm một
   hôm còn hơn xoá dữ liệu vì một lỗi mạng.

### Bài học chung với hai lỗi cache trước đó

Đây là **lần thứ ba** cùng một loại lỗi: *tên cache không phản ánh nội dung câu hỏi*.

| Ngày | Cache | Quên đưa vào tên | Hậu quả |
|---|---|---|---|
| 2026-08-23 | Overture parquet | bản phát hành | cào lại bao nhiêu lần cũng ra dữ liệu tháng đầu |
| 2026-08-24 | ô OSM Overpass | nội dung query | thêm loại quán mới nhưng đọc trúng kết quả cũ |
| 2026-08-24 | Overture parquet | **bbox** | sửa bbox nhưng vẫn đọc file của bbox cũ |

**Luật rút ra: tên file cache phải chứa MỌI thứ làm kết quả thay đổi.** Thiếu một yếu tố
là cache trả về câu trả lời của một câu hỏi khác, và không có dòng log nào báo.
