# Lấy thêm dữ liệu quán bằng Apify — thông số cần dùng

**Cập nhật:** 2026-08-23. Viết cho tình huống: có **một tài khoản Apify mượn được**, muốn
lấy được nhiều dữ liệu có ích nhất trong hạn mức miễn phí.

Mọi thứ ở đây đã có sẵn trong `data_pipeline/scrape_apify_hanoi.py` — bạn **không phải
viết code**, chỉ cần chạy lệnh và đưa file kết quả vào pipeline.

---

## 0. Điều quan trọng nhất: nên lấy CÁI GÌ

Đây là độ phủ THẬT của dataset hiện tại (đo bằng `python scripts/data_report.py`,
2026-08-23, 40.720 quán):

| Trường | Độ phủ | Ai đang cung cấp | Ghi chú |
|---|---:|---|---|
| tên · toạ độ · loại hình | 100% | Overture + OSM | **đã đủ, đừng tốn tiền vào đây** |
| địa chỉ | 100% | Overture + OSM | đã đủ |
| điện thoại | 80,9% | Overture | đã đủ |
| **giờ mở cửa** | **3,9%** | Apify (đợt cũ) | ⬅ thiếu nặng |
| **đánh giá sao** | **2,8%** | Apify (đợt cũ) | ⬅ thiếu nặng |
| **review có chữ** | **3,1%** | Apify (đợt cũ) | ⬅ thiếu nặng |
| **giá** | **1,6%** | Apify (đợt cũ) | ⬅ thiếu nặng |
| ảnh quán | ~3% | Apify (đợt cũ) | thiếu |

**Kết luận:** đừng dùng Apify để tìm quán MỚI — Overture đã cho 36.176 quán miễn phí và
OSM thêm ~3.900 nữa. Hãy dùng Apify để **làm giàu**: giờ mở cửa, sao, review, giá, ảnh.
Đó chính là bốn thứ không nguồn miễn phí nào có (OSM: 0% sao, 0% giá, 0% review — đã đo).

---

## 1. Thông số cần đặt

Actor: **`compass/crawler-google-places`** (Google Maps Scraper).
Script đã ghim đúng actor này, bạn không phải chọn.

| Tham số | Giá trị | Vì sao
|---|---|---|
| `searchStringsArray` | 20 từ khoá **tiếng Việt** | Google Maps ở Hà Nội gắn nhãn tiếng Việt; tìm bằng "restaurant" bỏ sót phần lớn quán bình dân. Danh sách đã có sẵn trong script |
| `customGeolocation` | polygon bbox Hà Nội `20.85–21.40 N, 105.70–106.05 E` | Đã sửa đúng sau khi phát hiện bbox cũ quá hẹp. **Đừng thu hẹp lại** |
| `language` / `countryCode` | `vi` / `vn` | |
| `scrapePlaceDetailPage` | **`true`** | ⚠️ TẮT cái này là **KHÔNG có giá, giờ mở cửa, tiện nghi**. Đây là công tắc quan trọng nhất |
| `skipClosedPlaces` | `true` | quán đã đóng thì không cần |
| `reviewsSort` | `newest` | review mới phản ánh đúng tình trạng hiện tại hơn |
| `maxReviews` | **5** (xem mục 2) | mỗi review là tiền |
| `maxImages` | **3** (xem mục 2) | mỗi ảnh là tiền |
| `maxCrawledPlacesPerSearch` | `--max-places / 20` | script tự chia đều cho 20 từ khoá |

Hai trường **bắt buộc phải có** trong kết quả: `categoryName` và `placeId`.
Script tự kiểm và báo lỗi nếu thiếu — lỗi này đã lặp lại nhiều lần ở các đợt cào trước.

---

## 2. Chọn `--max-places`, `--max-reviews`, `--max-images` theo hạn mức

Apify tính tiền **theo số place** và **tính thêm** cho review/ảnh. Đơn giá thay đổi theo
thời gian nên **file này cố ý KHÔNG ghi con số tiền** — hãy tự xem tại
<https://apify.com/compass/crawler-google-places> ngay trước khi chạy.

Chạy lệnh này trước, **không tốn tiền và không cần token**, để xem đúng cấu hình sẽ gửi đi:

```
python -m data_pipeline.scrape_apify_hanoi --dry-run
```

Ba mức khuyến nghị, theo thứ tự ưu tiên:

| Mức | Lệnh | Được gì |
|---|---|---|
| **A — nên chạy trước** | `--max-places 1000 --max-reviews 5 --max-images 3` | +1.000 quán có sao/giá/giờ. Rẻ nhất trên mỗi quán, và **giá trị cao nhất**: tăng độ phủ sao từ 2,8% lên ~5,3% |
| B — nếu còn hạn mức | `--max-places 2000 --max-reviews 5 --max-images 3` | gấp đôi mức A |
| C — chỉ khi dư | `--max-places 1000 --max-reviews 20 --max-images 10` | ít quán hơn nhưng review dày, phục vụ Lớp 4 (tóm tắt review) |

**Vì sao `maxReviews = 5` chứ không phải 20:** review trung bình chỉ dài **106 ký tự** (đã
đo) — lấy 20 cái không làm phần tóm tắt tốt hơn bao nhiêu, trong khi tiền thì nhân lên.
Độ **PHỦ** (nhiều quán có ít review) có ích hơn độ **SÂU** (ít quán có nhiều review), vì
xếp hạng cần so được nhiều quán với nhau.

---

## 3. Các bước chạy (PowerShell — máy của chủ dự án)

Mỗi lệnh một dòng. **Không dùng `&&`** — PowerShell 5.1 báo lỗi cú pháp.

```powershell
# 1. Xem trước, không tốn gì
python -m data_pipeline.scrape_apify_hanoi --dry-run

# 2. Đặt token của tài khoản mượn được (lấy ở Apify Console > Settings > Integrations)
$env:APIFY_TOKEN = "apify_api_xxxxxxxxxxxxxxxx"

# 3. Chạy thật. Vài nghìn quán kèm review có thể mất HÀNG CHỤC PHÚT — bình thường, không treo
python -m data_pipeline.scrape_apify_hanoi --max-places 1000 --max-reviews 5 --max-images 3

# 4. Đo TRƯỚC khi gộp, để còn so sánh
python scripts/data_report.py

# 5. Gộp vào dataset — ĐÚNG THỨ TỰ NÀY, không được đảo
python -m data_pipeline.merge_and_prepare_raw
python -m data_pipeline.data_cleaning
python -m data_pipeline.feature_engineering
python -m data_pipeline.clustering

# 6. Đo lại và so với bước 4
python scripts/data_report.py

# 7. Kiểm tra toàn bộ dự án vẫn chạy
python scripts/verify.py
```

⚠️ **`clustering` phải chạy CUỐI.** Chạy `feature_engineering` sau nó sẽ **xoá mất** hai
cột `experience_cluster_id` / `experience_cluster_label` và phải phân cụm lại từ đầu.

⚠️ **Đừng đóng cửa sổ ở bước 3.** Script chờ run xong rồi mới tải kết quả về; đóng giữa
chừng thì tiền đã tiêu mà file không về máy. (Nếu lỡ đóng: run vẫn nằm trên Apify
Console, tải dataset về dạng JSON rồi đặt vào `data_pipeline/data_raw/`.)

---

## 4. Bảo mật — token là dữ liệu nhạy cảm

- **KHÔNG** dán token vào file nào trong repo. `$env:APIFY_TOKEN` chỉ sống trong cửa sổ
  PowerShell đang mở, đóng là mất — đúng như mong muốn.
- Nếu muốn giữ lại: cho vào `.env.local` (đã nằm trong `.gitignore`), **không phải**
  `.env.example` (file này được commit).
- Token là của **tài khoản người khác cho mượn**. Lộ ra ngoài thì người đó chịu hoá đơn.
- Sau khi lấy xong dữ liệu, nên vào Apify Console **thu hồi token** đó.

---

## 5. Nếu muốn tự đặt cấu hình khác

Sửa `data_pipeline/scrape_apify_hanoi.py`:

- Thêm/bớt từ khoá → `SEARCH_TERMS` (dòng ~62)
- Đổi phạm vi → `HANOI_BBOX` (dòng ~55) — nhưng **phạm vi dự án đã chốt CHỈ HÀ NỘI**
  (CLAUDE.md mục 4b), mở rộng phải hỏi trước
- Đổi cấu hình actor → `build_actor_input()`

**Không viết script cào riêng.** Kiến trúc thu thập đi qua `SourceAdapter`
(`data_pipeline/sources/base.py`); thêm nguồn mới = 1 adapter + 1 dòng đăng ký.

---

## 6. Những gì KHÔNG được làm

| Nguồn | Vì sao cấm |
|---|---|
| ShopeeFood · GrabFood · Foody · TripAdvisor · Facebook | ToS cấm truy cập tự động. Đồ án tốt nghiệp không được xây trên nền vi phạm ToS |
| Google Places API / Routes API trực tiếp | bắt buộc bật thanh toán bằng thẻ |
| Tự viết bot cào google.com/maps | vi phạm ToS của Google, và rất dễ vỡ |

Xem `docs/data_sources.md` để biết phương án thay thế hợp pháp cho từng nhu cầu.
