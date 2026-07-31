# Hướng dẫn gán nhãn dữ liệu (Annotation Guidelines) - Project Floorplan to 3D

Tài liệu này hướng dẫn cách gán nhãn bản vẽ mặt bằng trên công cụ CVAT.

## 1. Các lớp đối tượng (Labels)

| Label | Kiểu gán nhãn | Mô tả |
|---|---|---|
| **wall** | Polygon | Gán nhãn toàn bộ vùng bao của tường. Cần độ chính xác cao ở các góc. |
| **door** | Bounding Box | Gán nhãn vùng cửa đi. |
| **window** | Bounding Box | Gán nhãn vùng cửa sổ. |
| **bed** | Bounding Box | Giường ngủ. |
| **sofa** | Bounding Box | Ghế sofa. |
| **toilet** | Bounding Box | Bồn cầu / Thiết bị vệ sinh. |
| **dimension_line** | Polyline | Đường kích thước (phục vụ OCR). |

## 2. Quy tắc quan trọng
- **Độ chính xác:** Polygon của tường phải khít với nét vẽ trên bản vẽ. Không gán nhãn chồng lấn quá nhiều lên cửa.
- **Cửa:** Gán nhãn bao gồm cả phần cánh cửa mở (nếu có ký hiệu hình quạt).
- **Multi-level:** Nếu bản vẽ có nhiều tầng, gán nhãn từng tầng vào các Job riêng biệt trong CVAT.

## 3. Quy trình xuất dữ liệu
- Xuất định dạng **COCO 1.1** cho bài toán Segmentation (SegFormer).
- Xuất định dạng **YOLO 1.1** cho bài toán Detection (YOLOv11).
