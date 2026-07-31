# CODING_STANDARDS.md

## 1. Ngôn ngữ & Định dạng
- **Backend:** Python 3.10+ (FastAPI). Sử dụng Type Hints đầy đủ.
- **Frontend:** TypeScript (React/Three.js).
- **Định dạng:** Tuân thủ PEP 8 cho Python. Sử dụng `ruff` hoặc `black` để format.
- **Tuyệt đối không sử dụng Jupyter Notebook (.ipynb) trong thư mục `src/` hoặc `data_pipeline/` phục vụ production.** Mọi thử nghiệm phải được chuyển đổi sang `.py` trước khi commit.

## 2. Kiến trúc (Clean Architecture)
- **Domain:** Chứa các Business Entities và Logic cốt lõi. Không phụ thuộc framework.
- **Application:** Chứa Use Cases và Ports (Interfaces).
- **Infrastructure:** Chứa Adapters (DB, AI Model, API bên thứ ba).
- **Presentation:** Chứa Controllers (API) và UI.

## 3. Quản lý cấu hình
- Không hard-code các tham số kỹ thuật (thresholds, magic numbers).
- Mọi cấu hình phải đặt trong `config/thresholds.yaml` và truy cập qua `ConfigService`.
- Bí mật (API Keys) đặt trong `.env` hoặc `config/secrets.yaml` (đã bị .gitignore).

## 4. Kiểm thử (Testing)
- Mỗi tính năng mới phải đi kèm Unit Test.
- Đảm bảo CI/CD xanh trước khi merge PR.

## 5. Dữ liệu & Artifacts
- Không commit các file dữ liệu lớn (>10MB), model weights (.pth, .onnx), hoặc file 3D (.glb) lên Git. Sử dụng Cloud Storage hoặc Git LFS nếu cần thiết.
