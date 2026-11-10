# ⚠️ File này đã được thay thế

Trạng thái dự án nay nằm ở **[`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md)**.

## Vì sao chuyển

Có hai file cùng mô tả trạng thái dự án thì chắc chắn sẽ có lúc chúng mâu thuẫn nhau, và
khi đó không ai biết tin file nào. Chỉ giữ **một** nguồn sự thật.

## Những gì file cũ ghi sai (rút kinh nghiệm)

File này từng ghi backend "hoạt động tốt" và "14/14 test pass". Kiểm chứng lại ngày
2026-08-16 cho thấy:

- **App không khởi động được** — `main.py` dùng `@app.exception_handler` trước khi biến
  `app` tồn tại (`NameError`).
- Test vẫn xanh **vì không có test nào import app**.
- `/api/recommend` và `/api/suggest-dish` cũng hỏng riêng (đọc `request.mood` trên object
  `Request` thay vì trên body).

→ Bài học đã đưa vào [`CLAUDE.md`](CLAUDE.md): **chỉ đánh dấu hoàn thành sau khi chạy thật**,
không dựa vào tài liệu. Nay đã có test bắt buộc app phải dựng được, chạy trong CI.

Nội dung cũ vẫn xem lại được trong lịch sử git:

```bash
git log --follow -p project_state.md
```

---

## Cập nhật 2026-08-19 — luồng chính là CHỌN MÓN TRƯỚC

Trang chủ nay là **lưới MÓN**, không phải ô tìm quán:

```
bộ lọc (trời mưa · đồ nướng · đồ nóng) → DANH SÁCH MÓN → giới thiệu món → QUÁN bán món đó
```

- Đề án gốc đã được sửa cho khớp — xem phần **SỬA ĐỔI PHẠM VI** ở đầu
  `docs/original/MoodBite_De_An_Y_Tuong.md`.
- Lối vào cũ (gõ câu tự nhiên) vẫn còn ở `/tim-kiem`, không bị xoá.
- Các mục `/api/recommend`, `/api/suggest-dish` nhắc ở trên là **lịch sử bug đã sửa** của
  backend TypeScript cũ, không phải endpoint hiện tại.
