# Bản đồ dự án MoodBite — file nào ở đâu, làm việc gì

**Viết cho:** chủ dự án, để mở đúng file mà không phải đi mò.
**Cập nhật:** 2026-08-23.

Nếu chỉ đọc được một mục, hãy đọc **mục 2** ("Tôi muốn sửa X thì mở file nào").

---

## 1. Mở xem giao diện — một lệnh duy nhất

```powershell
python scripts/run_dev.py
```

Lệnh này bật **cả hai** thứ cùng lúc (backend + frontend) và tự tìm cổng trống nếu cổng
đang bận. Mở trình duyệt vào **<http://localhost:5173>**.

Thêm trang quản trị:

```powershell
python scripts/run_dev.py --admin
```

Dừng: bấm `Ctrl + C` trong cửa sổ đó.

> Không có lệnh nào "mở riêng một layout". Đây là ứng dụng một trang (SPA) — mọi màn hình
> là một **đường dẫn** trên cùng một server. Muốn xem trang nào thì gõ đường dẫn của trang
> đó, xem bảng dưới đây.

---

## 2. Tôi muốn sửa X thì mở file nào

### 2.1. Các màn hình người dùng (app `client`)

Mọi đường dẫn dưới đây gốc là `frontend/apps/client/src/`.

| Màn hình | Mở ở trình duyệt | File GIAO DIỆN (View) | File XỬ LÝ (ViewModel/hook) |
|---|---|---|---|
| **Trang chủ** | `/` | `pages/home/ui/HomePage.tsx` | `features/suggest-dishes/model/useDishSuggestions.ts` |
| ↳ khối đầu trang + ô tìm | | `widgets/home-hero/ui/HomeHero.tsx` | — |
| ↳ hàng thẻ mood | | `widgets/mood-quick-pick/ui/MoodQuickPick.tsx` | — |
| ↳ hàng "khám phá theo nhu cầu" | | `widgets/explore-needs/ui/ExploreNeeds.tsx` | — |
| ↳ lưới/hàng thẻ món | | `widgets/dish-list/ui/DishList.tsx` + `entities/dish/ui/DishCard.tsx` | — |
| ↳ bảng lọc chi tiết | | `features/suggest-dishes/ui/DishFilters.tsx` | như trên |
| **Chi tiết món** | `/dishes/pho-bo` | `pages/dish/ui/DishPage.tsx` | `features/view-dish-detail/model/useDishDetail.ts` |
| **Tìm bằng câu tự nhiên** | `/search` | `pages/search/ui/SearchPage.tsx` | `features/search-restaurants/model/useSearch.ts` |
| ↳ bản đồ | | `widgets/restaurant-map/ui/RestaurantMap.tsx` | — |
| ↳ thẻ quán | | `entities/restaurant/ui/RestaurantCard.tsx` | — |
| **Đăng nhập** | `/login` | `pages/login/ui/LoginPage.tsx` + `features/auth-login/ui/LoginForm.tsx` | `entities/user/model/useUserSession.ts` |
| **Đăng ký** | `/register` | `pages/register/ui/RegisterPage.tsx` + `features/auth-register/ui/RegisterForm.tsx` | như trên |
| **Quên mật khẩu** | `/forgot-password` | `features/auth-recover-password/ui/ForgotPasswordForm.tsx` | `features/auth-recover-password/model/usePasswordRecovery.ts` |
| **Đặt mật khẩu mới** | `/reset-password?token=…` | `features/auth-recover-password/ui/ResetPasswordForm.tsx` | như trên |
| **Trang tài khoản** | `/account` | `pages/account/ui/AccountPage.tsx` (khung) + `pages/account/ui/tabs.tsx` (nội dung từng tab) | `entities/user/model/useUserStats.ts` · `features/save-favorite/model/useFavorites.ts` |
| ↳ tab Hồ sơ | `/account?tab=profile` | `pages/account/ui/tabs.tsx` → `ProfileTab` | — |
| ↳ tab Sở thích | `/account?tab=taste` | `features/taste-preferences/ui/TastePicker.tsx` | `features/taste-preferences/model/useTastePreferences.ts` |
| ↳ tab Đã lưu | `/account?tab=saved` | `pages/account/ui/tabs.tsx` → `SavedTab` | `features/save-favorite/model/useFavorites.ts` |
| ↳ tab Cấp độ & huy hiệu | `/account?tab=badges` | `widgets/user-progress/ui/LevelCard.tsx` · `BadgeGrid.tsx` | `entities/user/model/useUserStats.ts` |
| ↳ tab Cài đặt | `/account?tab=settings` | `pages/account/ui/AccountPage.tsx` (cuối file) | — |
| **404** | đường dẫn sai bất kỳ | `pages/not-found/ui/NotFoundPage.tsx` | — |

**Thanh trên (logo · điều hướng · ngôn ngữ · nền tối · tài khoản)** dùng chung ở nhiều
trang: `widgets/site-header/ui/SiteHeader.tsx`.

### 2.2. Sửa CHỮ trên giao diện (và bản dịch tiếng Anh)

Toàn bộ chữ nằm ở **một file duy nhất**: `shared/i18n/tu_dien.ts`.

- Sửa câu tiếng Việt → sửa trong khối `vi`
- TypeScript sẽ **báo lỗi** nếu bạn thêm câu mới mà quên dịch sang `en` — cố ý như vậy
- Chữ **không** dịch được: tên món, tên quán, câu ngữ cảnh, thông báo lỗi từ máy chủ.
  Chúng do backend sinh bằng tiếng Việt; dịch nốt nghĩa là phải làm i18n ở backend.

### 2.3. Sửa MÀU SẮC / BỐ CỤC

| Muốn sửa | File |
|---|---|
| Màu thương hiệu, nền, chữ, nền tối | `app/styles/brand.css` |
| Bố cục chung + 404 | `app/styles.css` |
| Trang đăng nhập / đăng ký / quên mật khẩu | `app/styles/auth.css` |
| Trang chủ (hero, mood, thẻ món, CTA) | `app/styles/home.css` |
| Trang tài khoản (thanh bên, cấp độ, huy hiệu) | `app/styles/account.css` |

### 2.4. Sửa ẢNH / LOGO

- Ảnh gốc do bạn cung cấp: `frontend/design/attribute/`
- Chạy `python scripts/prepare_design_assets.py` để tạo bản đã tối ưu vào
  `frontend/apps/client/public/anh/`
- Khai báo kích thước ảnh: `shared/config/images.ts`

### 2.5. Trang quản trị (app `admin`, chạy riêng)

Gốc `frontend/apps/admin/src/`. Bật bằng `python scripts/run_dev.py --admin`,
mở <http://localhost:5174>.

| Màn hình | Đường dẫn | File |
|---|---|---|
| Đăng nhập quản trị | `/login` | `pages/login/ui/LoginPage.tsx` |
| Danh sách quán (sửa/ẩn) | `/` | `pages/restaurants/ui/RestaurantsPage.tsx` |

---

## 3. Backend — file nào lo việc gì

Gốc `src/`. Kiến trúc **Clean Architecture**: phụ thuộc chỉ đi một chiều
`presentation → application → domain ← infrastructure`.

### 3.1. Bốn tầng, nói bằng tiếng Việt

| Tầng | Trả lời câu hỏi | Ví dụ |
|---|---|---|
| `domain/` | "**Luật** là gì?" | chấm điểm mood, xếp hạng, tính khoảng cách, tính điểm/cấp độ |
| `application/` | "**Trình tự** làm việc thế nào?" | gọi kho lấy quán → gọi domain chấm điểm → trả kết quả |
| `infrastructure/` | "Dữ liệu **nằm ở đâu**?" | đọc CSV, đọc SQLite, gọi API thời tiết, gửi email |
| `presentation/` | "Nói chuyện với **bên ngoài** thế nào?" | đường dẫn HTTP, hình dạng JSON, mã lỗi |

### 3.2. Bảng tra nhanh

| Muốn sửa | File |
|---|---|
| Công thức **xếp hạng quán** | `domain/services/search_ranking.py` |
| Công thức **xếp hạng món** | `domain/services/dish_ranking.py` |
| Quy tắc **so khớp tên tiếng Việt** (bỏ dấu, khớp nguyên từ) | `domain/value_objects/text.py` |
| Quy tắc **suy ra món từ tên quán** | `domain/services/dish_matching.py` |
| **Điểm · cấp độ · huy hiệu** | `domain/services/gamification.py` |
| Đếm "lượt khám phá" theo người | `domain/services/activity_tally.py` |
| Ngưỡng **báo quán đóng cửa** | `domain/services/closure_reports.py` |
| Quy tắc **tên đăng nhập / mật khẩu / email** | `domain/entities/user.py` |
| Luồng **tìm quán** | `application/use_cases/search_restaurants.py` |
| Luồng **gợi ý món** | `application/use_cases/suggest_dishes.py` |
| Luồng **tìm quán bán món X** | `application/use_cases/find_restaurants_for_dish.py` |
| Luồng **đăng ký/đăng nhập/quên mật khẩu** | `application/use_cases/manage_account.py` |
| Luồng **lưu quán & món yêu thích** | `application/use_cases/manage_favorites.py` |
| Luồng **số liệu tài khoản** | `application/use_cases/get_user_stats.py` |
| **Đường dẫn file dữ liệu, biến môi trường** | `infrastructure/config/settings.py` |
| Đọc dữ liệu quán (CSV) | `infrastructure/repositories/csv_restaurant_repository.py` |
| Đọc dữ liệu quán (SQLite) | `infrastructure/repositories/sqlite_restaurant_repository.py` |
| Kho **tài khoản** | `infrastructure/repositories/sqlite_user_repository.py` |
| Kho **đã lưu** | `infrastructure/repositories/sqlite_saved_item_repository.py` |
| **Gửi email** | `infrastructure/notifications/smtp_email_sender.py` |
| **Tìm kiếm ngữ nghĩa TF-IDF** | `infrastructure/adapters/tfidf_semantic_search.py` |
| **Thời tiết** | `infrastructure/adapters/open_meteo_context_provider.py` |
| Đường dẫn HTTP `/search` | `presentation/api/routers/search.py` |
| Đường dẫn HTTP `/dishes/*` | `presentation/api/routers/dishes.py` |
| Đường dẫn HTTP `/auth/*` | `presentation/api/routers/auth.py` |
| Đường dẫn HTTP `/me/*` (đã lưu, cấp độ) | `presentation/api/routers/me.py` |
| **Hình dạng JSON** của mọi request/response | `presentation/api/schemas.py` |
| **Mã lỗi → HTTP status** | `presentation/api/error_handlers.py` |
| **Nối dây toàn hệ thống** (cái gì dùng cái gì) | `presentation/api/dependencies.py` ⬅ *quan trọng nhất khi muốn hiểu hệ thống* |

### 3.3. Xem danh sách API đang có

Chạy backend rồi mở: **<http://localhost:8001/docs>** — trang này tự sinh, luôn đúng với
code, và bấm thử được từng endpoint ngay trên trình duyệt.

---

## 4. Dữ liệu — file nào là gì

| File / thư mục | Là gì |
|---|---|
| `data_pipeline/data_raw/` | **Dữ liệu thô** vừa cào về, chưa xử lý. Không đọc trực tiếp |
| `data_pipeline/data_cleaned/dataset_moodbite_features.csv` | **Dataset chính** — app đọc file này |
| `data_pipeline/data_cleaned/restaurant_details.json` | Review · ảnh · giá (10,4% quán) |
| `data_pipeline/data_cleaned/dish_catalog.json` | **Danh mục 855 món** + ảnh + giới thiệu |
| `data_pipeline/dish_seed_manual.json` | Từ khoá nhận diện món — **soạn tay**, nguồn sự thật |
| `data_pipeline/dish_approved.json` | **Cửa kiểm duyệt**: chỉ món có tên ở đây mới được `--apply` vào danh mục |
| `data_pipeline/sources/wikidata_dish.py` | Nguồn món thứ hai (Wikidata, CC0) — lấy **tên gọi khác** |
| `scripts/mine_dish_names.py` | Nguồn món thứ ba: đào cụm từ trong TÊN quán thật |
| `data_pipeline/dish_knowledge_base.json` | Luật gợi ý món theo mood |
| `data_pipeline/sources/` | Mỗi file = một **nguồn dữ liệu** (OSM, Overture, Wikipedia) |

### Thứ tự chạy pipeline — BẮT BUỘC

```
merge_and_prepare_raw  →  data_cleaning  →  feature_engineering  →  clustering
```

⚠️ `clustering` phải **cuối cùng**. Chạy `feature_engineering` sau nó sẽ xoá mất hai cột
phân cụm.

---

## 5. Script — chạy cái gì để làm gì

| Lệnh | Làm gì |
|---|---|
| `python scripts/verify.py` | **Kiểm tra toàn bộ dự án** (9 mục). Chạy sau mọi thay đổi |
| `python scripts/run_dev.py` | Bật app để xem giao diện |
| `python scripts/data_report.py` | Đo độ phủ dữ liệu — chạy trước/sau mỗi lần bổ sung |
| `python scripts/audit_dish_images.py` | Soát ảnh món gắn nhầm (`--clear` để gỡ) |
| `python scripts/find_dish_images.py --apply` | Tìm ảnh cho món chưa có |
| `python scripts/set_dish_image.py --list-missing` | Liệt kê món thiếu ảnh, và nhập ảnh tay |
| `python scripts/prepare_design_assets.py` | Xử lý logo/ảnh từ `design/attribute/` |
| `python scripts/check_architecture.py` | Kiểm hướng phụ thuộc backend |
| `python scripts/check_email.py` | Thử kết nối máy chủ thư |
| `python scripts/refresh_check.py` | So dữ liệu mới/cũ: quán nào mới, mất, đổi tên |
| `python scripts/build_sqlite.py` | Dựng CSDL SQLite từ CSV |
| `python scripts/export_openapi.py` | Xuất đặc tả API cho frontend |

---

## 6. Muốn hiểu hệ thống trong 15 phút thì đọc theo thứ tự này

1. `PROJECT_CHECKLIST.md` — đang có gì, còn thiếu gì
2. `src/presentation/api/dependencies.py` — sơ đồ nối dây của cả backend
3. `src/application/use_cases/suggest_dishes.py` — một luồng nghiệp vụ đầy đủ
4. `frontend/apps/client/src/pages/home/ui/HomePage.tsx` — một màn hình đầy đủ
5. `CLAUDE.md` — luật của dự án và **lý do** của từng luật

---

## 7. Ba câu hỏi hay gặp

**"Sao sửa file rồi mà trình duyệt không đổi?"**
Vite tự nạp lại. Nếu không đổi: dừng `run_dev.py` (Ctrl+C) rồi chạy lại. Sau khi **xoá
hoặc đổi tên file**, gần như luôn phải khởi động lại — đây là lỗi đã gặp thật (trang trắng
tinh kèm lỗi `does not provide an export named …`).

**"Sao trang tài khoản đá tôi về trang đăng nhập?"**
Token hết hạn (sống 24 giờ) hoặc chưa đăng nhập. Đăng nhập lại.

**"Sao gọi API bị lỗi 503 `DATA_NOT_READY`?"**
Chưa chạy pipeline dữ liệu. Thông báo lỗi luôn kèm đúng lệnh cần chạy — đọc phần
`error.message`.
