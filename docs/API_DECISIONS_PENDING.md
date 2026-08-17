# Quyết định API đang chờ duyệt

**Cập nhật:** 2026-08-17

File này giữ các **thay đổi API/data model đã bàn nhưng CHƯA được duyệt để code**.

Tách riêng khỏi `UI_REQUIREMENTS.md` có chủ đích, theo đúng ranh giới đã thống nhất:

| File | Trả lời câu hỏi |
|---|---|
| `UI_REQUIREMENTS.md` | Giao diện **phải làm gì** |
| **`API_DECISIONS_PENDING.md`** *(file này)* | Backend **sẽ được phép thêm gì**, khi nào |
| `PROJECT_CHECKLIST.md` | Cái gì **đã chạy thật** |

> ⛔ **Không được code bất kỳ mục nào dưới đây khi chưa có duyệt.**
> Đây đều là thay đổi hợp đồng API hoặc data model.

---

## 1. `GET /api/v1/admin/stats` — phục vụ Dashboard + Chất lượng dữ liệu

**Trạng thái:** đã chốt hình dạng, **chưa code**.

```json
{
  "total_restaurants": 4938,
  "sources": { "openstreetmap": 3528, "google_maps_apify": 1410 },
  "coverage": {
    "coordinates":   1.000,
    "name":          1.000,
    "district":      0.969,
    "opening_hours": 0.326,
    "rating":        0.232,
    "thumbnail":     0.215,
    "price":         0.130
  },
  "clustering": { "clustered": 1197, "total": 4938 },
  "hidden_count": 0,
  "generated_at": "<ISO-8601 do SERVER sinh lúc gọi>"
}
```

**Bằng chứng cho từng con số** — đếm trực tiếp ngày 2026-08-17:

```
4938 dòng CSV = 4938 dòng SQLite
openstreetmap 3528 + google_maps_apify 1410 = 4938 ✓
experience_cluster_id khác NULL = 1197
```

Kiểm lại: `python scripts/data_report.py`

### ⛔ Ba trường BỊ CẤM trong response này

| Trường | Vì sao cấm |
|---|---|
| `users` | Không có hệ thống tài khoản (`rules/api.md`: *"Không áp dụng hệ thống tài khoản cá nhân đăng nhập ở Giai đoạn MVP"*) |
| `reviews_count` | Review nhúng trong dữ liệu quán, không đếm riêng được |
| `match_quality` | Chỉ số này **không tồn tại** |

**Kể cả trả về `0` cũng không được** — trả 0 vẫn khiến người đọc tưởng hệ thống có đo,
chỉ là chưa ai dùng.

---

## 2. `POST /api/v1/admin/restaurants` — thêm quán thủ công

**Trạng thái:** 🔴 **BLOCKING DECISION** — đây là thay đổi data model, chưa được duyệt.

### Vấn đề chặn: quán thêm tay sẽ BỊ XOÁ

`scripts/build_sqlite.py` chạy `DELETE FROM restaurants` rồi ghi lại toàn bộ từ CSV,
hiện chỉ giữ được cột `is_active` qua `--keep-hidden`.

Nghĩa là **CSV vẫn là source of truth**, và quán admin nhập tay sẽ biến mất ở lần chạy
pipeline tiếp theo — mất công nhập 50–100 quán Hoàn Kiếm.

### Bảng đề xuất (CHƯA phải quyết định)

| Câu hỏi | Đề xuất | Vì sao |
|---|---|---|
| Source of truth? | CSV cho quán pipeline · SQLite cho quán thủ công | thêm cột `origin`; `build_sqlite` chỉ xoá dòng `origin='pipeline'` |
| Trường bắt buộc | `name` · `latitude` · `longitude` | thiếu toạ độ thì không xếp hạng và không lên bản đồ được |
| ID sinh thế nào | `manual-<uuid4>` | nhìn là biết không phải placeId của Google |
| `source` | `"admin_manual"` | CLAUDE.md mục 4b: mọi bản ghi phải có nguồn rõ ràng |
| `data_confidence` | `"manual"` | phân biệt với dữ liệu cào |
| `is_active` mặc định | `true` | nhập xong dùng được ngay |
| `rating` / `price` | **bắt buộc `null`** | admin không được tự chấm sao — đó là bịa số liệu |
| `mood_scores` / cụm | `null` | do pipeline tính; Cold Start dùng 0.5 trung lập |

---

## 3. Trường `reason` cho `explicit_negative`

**Trạng thái:** 🔴 **BLOCKING DECISION** — chưa duyệt.

Ý tưởng: khi người dùng bấm "không phù hợp", cho chọn lý do (quá xa / sai món / sai mood /
giá không hợp / khác).

**Hiện KHÔNG gửi được.** `InteractionRequest` chỉ có:

```
session_id · restaurant_id · action_type · search_query_id · dwell_time_ms · rank_position
```

Không có `reason`. Làm giao diện chọn lý do bây giờ thì lý do **rơi vào hư không**.

---

## 4. `GET /api/v1/admin/interactions` — thống kê tương tác

**Trạng thái:** 🔴 chưa duyệt, và **chưa có dữ liệu để hiển thị**.

Hiện chỉ có `POST /interactions`, không có endpoint đọc. Ngoài ra
`data_pipeline/data_cleaned/interactions.jsonl` **chưa tồn tại (0 bản ghi)** — nên kể cả
làm xong endpoint thì trang thống kê vẫn trống.

> ⚠️ Mọi con số kiểu *"1.284 tương tác · 842 xem chi tiết · 217 lưu"* từng xuất hiện trong
> các bản đề xuất đều là **bịa**. Thực tế là 0.

**Thứ tự đúng:** thêm nút phản hồi vào giao diện → có người dùng thật → có dữ liệu →
lúc đó mới làm trang thống kê.
