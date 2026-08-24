# Lớp 3 — Xếp hạng theo ngữ cảnh: chỗ ghi NGUỒN NGHIÊN CỨU

> **Trả lời câu hỏi của chủ dự án (2026-08-24): CÓ, và nên làm.**
> Đây là phần duy nhất của đề án đang chọn hằng số bằng **lập luận thường thức**, trong khi
> `CLAUDE.md` mục 4c yêu cầu *"Chọn siêu tham số bằng SỐ ĐO, không bằng cảm tính. Mọi hằng
> số đều phải có comment ghi rõ đã thử gì và vì sao chọn."*
> Không có dữ liệu người dùng thật để đo, nên **trích dẫn nghiên cứu đã công bố là cách
> hợp lệ và rẻ nhất để lấp đúng chỗ trống đó**.

---

## 1. Vì sao Lớp 3 cần nguồn, còn Lớp 1/2/5 thì không

| Lớp | Hằng số quan trọng | Hiện đang biện minh bằng |
|---|---|---|
| 1. Phân cụm | `k = 7` | ✅ **Số đo**: Silhouette 0.318 cao nhất trong dải k=3..8 |
| 2. Tìm kiếm ngữ nghĩa | ngưỡng cosine `0.15` | ✅ Số đo trên dataset thật |
| 3. **Xếp hạng ngữ cảnh** | `+0.3` món nóng khi mưa · `-0.25` món lạnh khi mưa · `+0.2` món nước · ngưỡng `32°C` | ❌ **Chỉ có lập luận thường thức** |
| 5. Gợi ý món | trọng số `W_FILTER`… | 🟡 Tổng = 1.0, có test khoá, nhưng tỷ lệ giữa các thành phần cũng là chọn tay |

Hằng số Lớp 3 nằm ở:
- `src/domain/services/dish_ranking.py` — hàm `_score_context()`
- `src/domain/services/search_ranking.py` — `W_TEXT`, `W_MOOD`, `W_DISTANCE`…
- `src/domain/value_objects/context_signal.py` — `mood_bias()`, ngưỡng nhiệt độ

**Câu hỏi hội đồng gần như chắc chắn sẽ hỏi:** *"Tại sao trời mưa lại cộng 0.3 mà không
phải 0.5?"* Hiện tại chưa có câu trả lời nào ngoài "thấy hợp lý".

---

## 2. Loại nguồn DÙNG ĐƯỢC

Ưu tiên từ trên xuống. Nguồn càng gần đầu bảng thì càng khó bị bắt bẻ.

| Hạng | Loại nguồn | Ví dụ cụ thể nên tìm |
|---|---|---|
| A | Bài báo bình duyệt (peer-reviewed) | Nghiên cứu tâm lý học về *weather and mood*, *seasonal affective disorder*, *ambient temperature and food choice* |
| A | Tổng quan hệ thống / phân tích gộp (meta-analysis) | Mạnh hơn một nghiên cứu lẻ vì đã gộp nhiều mẫu |
| B | Báo cáo của cơ quan nhà nước / tổ chức quốc tế | Tổng cục Thống kê, WHO, FAO, Bộ Y tế |
| B | Khảo sát thị trường công bố công khai | Nielsen, Kantar, Q&Me, Decision Lab (nhiều báo cáo về ăn uống Việt Nam là **miễn phí**) |
| C | Luận văn / luận án đã bảo vệ | Có phần phương pháp rõ ràng, trích dẫn được |
| C | Bài báo chí dẫn lại nghiên cứu | **Chỉ dùng để lần ra nghiên cứu gốc**, không trích dẫn thẳng |

### KHÔNG dùng được

- Blog cá nhân, bài SEO, nội dung do AI sinh, không nói rõ cỡ mẫu.
- **Bất cứ thứ gì không xem được nguồn gốc số liệu.** Đây cùng một luật với dữ liệu quán:
  *không có nguồn rõ ràng thì không đưa vào* (`CLAUDE.md` mục 4b).
- Số liệu nhớ mang máng rồi ghi lại. Không có link thì coi như không có.

### Điểm cộng riêng cho đề án này

Nghiên cứu về **Việt Nam / Đông Nam Á / khí hậu nhiệt đới ẩm** đáng giá hơn hẳn nghiên
cứu ở Bắc Âu — mùa đông Hà Nội và mùa đông Phần Lan không so được, mà phần lớn nghiên cứu
*weather and mood* lại làm ở vùng ôn đới. Nếu chỉ tìm được nguồn ôn đới thì **vẫn dùng
được, nhưng phải tự ghi rõ hạn chế đó** — hội đồng đánh giá cao người tự nêu điểm yếu hơn
là người giấu.

---

## 3. Bảng đăng ký nguồn — ĐIỀN VÀO ĐÂY

Mỗi hằng số một dòng. Cột "Nguồn" để trống nghĩa là **chưa có gì bảo vệ nó**.

| # | Hằng số | Giá trị | Ở đâu | Nguồn (điền) | Nguồn nói gì (1 câu) |
|---|---|---|---|---|---|
| 1 | món nóng khi trời mưa | `+0.3` | `dish_ranking._score_context` | | |
| 2 | món lạnh khi trời mưa | `-0.25` | `dish_ranking._score_context` | | |
| 3 | món nước khi trời mưa | `+0.2` | `dish_ranking._score_context` | | |
| 4 | ngưỡng "nắng nóng" | `32°C` | `dish_ranking` + `context_signal` | | |
| 5 | món mát khi nắng nóng | `+0.3` | `dish_ranking._score_context` | | |
| 6 | món nướng khi nắng nóng | `-0.1` | `dish_ranking._score_context` | | |
| 7 | hợp giờ ăn hiện tại | `+0.2` | `dish_ranking._score_context` | | |
| 8 | trọng số mood khi xếp hạng quán | `W_MOOD = 0.26` | `search_ranking` | | |
| 9 | trọng số khoảng cách | `W_DISTANCE = 0.17` | `search_ranking` | | |
| 10 | bán kính mặc định | `10 km` | `search_ranking` | | |

### Cách điền một dòng cho ĐÚNG

```
| 1 | món nóng khi trời mưa | +0.3 | dish_ranking._score_context |
  Tên tác giả (năm). "Tên bài". Tạp chí, tập(số), trang. DOI/URL |
  Cỡ mẫu N=…, đo được … |
```

Ba thứ **bắt buộc** có, thiếu một là dòng đó chưa dùng được:
1. **Đường dẫn ổn định** — DOI tốt hơn URL, URL tốt hơn không có gì.
2. **Cỡ mẫu và nơi khảo sát** — "N=1.200 người tại Hà Nội" mạnh hơn hẳn "nhiều nghiên cứu cho thấy".
3. **Con số thật trong nguồn** — nguồn nói *bao nhiêu*, không phải nguồn nói *có ảnh hưởng*.

---

## 4. Điều PHẢI trung thực — đọc trước khi viết báo cáo

Nghiên cứu tâm lý học **không bao giờ** nói thẳng "trời mưa thì cộng 0.3 điểm cho món
nóng". Nó nói những chuyện kiểu "nhiệt độ thấp làm tăng xu hướng tìm đồ ăn ấm, d = 0.4".

Từ đó ra con số `0.3` là **một bước diễn giải do nhóm làm đề án tự đặt ra**. Vậy nên:

- ✅ Được viết: *"Chiều tác động (mưa → ưu tiên món nóng) dựa trên [nguồn]. Độ lớn 0.3 do
  nhóm chọn để tín hiệu ngữ cảnh không lấn át lựa chọn chủ động của người dùng."*
- ❌ Không được viết: *"Theo [nguồn], trọng số món nóng khi trời mưa là 0.3."* — nguồn
  không hề nói vậy, và đây đúng là kiểu bịa mà `CLAUDE.md` mục 0 cấm.

Nói cách khác: **nguồn biện minh cho CHIỀU và SỰ TỒN TẠI của quy tắc, còn ĐỘ LỚN là lựa
chọn thiết kế của nhóm.** Ghi rõ ranh giới đó là điểm cộng, không phải điểm trừ.

---

## 5. Sau khi có nguồn thì làm gì

1. Điền vào bảng mục 3.
2. Thêm comment ngay cạnh hằng số trong code, trỏ về file này:
   ```python
   # +0.3: chiều tác động (mưa -> ưu tiên món nóng) theo [Nguon #1], xem
   # docs/nghien_cuu_lop3.md. Độ lớn do nhóm chọn - xem mục 4 của tài liệu đó.
   ```
3. Chạy `python scripts/run_suggest_demo.py` trước và sau nếu có đổi số, để thấy thứ tự
   gợi ý đổi thế nào. **Không đổi số mà không xem kết quả đổi ra sao.**
4. Cập nhật `PROJECT_CHECKLIST.md` dòng Lớp 3.

---

## 6. Khoảng trống lớn hơn: chưa có người dùng thật

Nguồn nghiên cứu lấp được chỗ "vì sao có quy tắc này". Nó **không** lấp được chỗ "quy tắc
này có làm người dùng hài lòng hơn không" — muốn biết thì phải có lượt tương tác thật.

Hạ tầng cho việc đó **đã có sẵn**: `POST /interactions` ghi lại `view_detail`,
`get_directions`, `save`… kèm `search_query_id`. Khi frontend chạy được và có vài chục
người dùng thử, có thể đối chiếu *thứ hạng do hệ thống chấm* với *quán người ta thật sự
bấm vào* — đó mới là số đo mạnh nhất, và cũng là hướng phát triển tiếp đáng viết vào
phần "Hướng phát triển" của báo cáo.
