# Ma trận truy vết — MoodBite

**Cập nhật:** 2026-10-13.
**Nguyên tắc:** mỗi dòng chỉ được ghi file **THẬT SỰ TỒN TẠI** và test **THẬT SỰ CHẠY**.
**Máy kiểm:** `python scripts/verify.py` mục 10 (gọi `scripts/check_traceability.py`):
mọi đường dẫn, ký hiệu, tên test trong file này phải tồn tại, và **mọi** file trong
`src/application/use_cases/` lẫn `src/presentation/api/routers/` phải có mặt ở đây.

> ⚠️ **Lịch sử — vì sao có máy kiểm.**
> Bản đầu tiên ghi 10 đường dẫn thì 9 cái không tồn tại (có cả một file `.ts` của backend
> cũ đã gỡ, kèm trạng thái "ACTIVE").
> Bản viết lại 2026-08-19 thì mọi đường dẫn đều đúng, nhưng ghi "kiểm lại bằng verify.py"
> trong khi verify.py **không hề đọc file này**. Đến 2026-10-10 bảng thiếu 15/20 use case,
> 10/12 router (toàn bộ tài khoản + trang quản trị), và còn ghi Lớp 4 "chưa làm" dù đã xong.
> Bài học: tài liệu chỉ đúng khi có MÁY kiểm nó.

---

## Luồng chính — chọn món trước, tìm quán sau

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| D1.1 | Bộ lọc trang chủ → danh sách MÓN | `src/presentation/api/routers/dishes.py` · `src/application/use_cases/suggest_dishes.py` | `test_suggest_returns_dishes_not_restaurants` |
| D1.2 | Quy tắc lọc & xếp hạng món | `src/domain/services/dish_ranking.py` | `tests/test_dish_ranking.py` |
| D1.3 | Tổng trọng số xếp hạng = 1.0 | `dish_ranking.W_*` | `test_weights_sum_to_one` |
| D1.4 | Món thiếu dữ liệu KHÔNG bị loại | `dish_ranking._passes_hard_filter` | `test_hard_filter_keeps_dish_with_missing_data` |
| D1.5 | Lọc rỗng thì TRẢ RỖNG + cảnh báo (không trả lại cả danh sách khi bữa sáng không khớp) | `dish_ranking.filter_dishes` · `suggest_dishes.py` | `test_filter_that_matches_nothing_returns_empty_NOT_the_whole_list` · `test_bua_sang_KHONG_lot_lau_toi_khi_khong_mon_sang_nao_khop` |
| D1.5 | Ẩn món 0 quán **và nói rõ đã ẩn** | `suggest_dishes._drop_dead_ends` | `test_dish_without_nearby_restaurant_is_hidden_and_announced` |
| D1.6 | Lọc "chỉ quán có ghi giá" phải nói ra món bị ẩn | `src/application/use_cases/suggest_dishes.py` | `test_suggest_an_mon_khong_quan_nao_ghi_gia_va_noi_ra` |
| D2.1 | Giới thiệu ngắn về món | `src/domain/entities/dish.py` (`description`, `has_description`) | `test_dish_detail_returns_short_intro` |
| D2.2 | Phân biệt "chưa tra được" với "không có gì" | `Dish.has_description` | `test_blank_description_counts_as_missing` |
| D3.1 | Món → quán bán món đó | `src/application/use_cases/find_restaurants_for_dish.py` | `test_restaurants_for_dish_returns_matching_restaurants` |
| D3.2 | Đối chiếu món ↔ quán (tên, loại hình) | `src/domain/services/dish_matching.py` | `test_phrase_does_not_span_name_and_category_boundary` |
| D3.3 | Trích món từ **nội dung review** (đề án mục 7) | `dish_matching._matching_dish_ids_in_review` | `test_review_mention_links_dish_to_restaurant` |
| D3.4 | Nới bán kính thì phải **nói ra** | `find_restaurants_for_dish._warn_if_radius_was_widened` | `test_far_restaurant_is_shown_but_the_widened_radius_is_announced` |
| D3.5 | Chỉ mục món ↔ quán dựng lại khi dữ liệu đổi | `src/infrastructure/adapters/live_dish_restaurant_index.py` | `tests/test_dish_index_freshness.py` |
| D3.6 | Trang món đếm theo ĐÚNG bán kính đã chọn ở lưới món (kể cả "Không giới hạn") | `src/presentation/api/routers/dishes.py` (`no_distance_limit`) · `frontend/apps/client/src/pages/dish/ui/DishPage.tsx` | `test_no_distance_limit_matches_suggest_null_radius` · `frontend/apps/client/src/pages/dish/ui/DishBanKinh.test.tsx` |
| D3.7 | Mở món từ trang chủ mang theo bộ lọc | `frontend/apps/client/src/pages/home/ui/HomePage.tsx` | `frontend/apps/client/src/pages/home/ui/HomeLocGia.test.tsx` |
| D4.1 | Mã lỗi riêng cho món | `src/presentation/api/envelope.py` (`DISH_NOT_FOUND`) | `test_unknown_dish_returns_404_with_its_own_code` |
| D4.2 | Thiếu dataset quán → 503 ở **cả** luồng món | `src/application/use_cases/restaurant_data_guard.py` | `test_thieu_du_lieu_quan_thi_goi_y_mon_tra_503` · `test_thieu_du_lieu_quan_thi_trang_quan_cua_mon_tra_503` |

## Lối vào thứ hai — tìm quán bằng câu tự nhiên

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| R2.1 | Tìm kiếm + xếp hạng quán | `src/presentation/api/routers/search.py` · `src/application/use_cases/search_restaurants.py` | `tests/test_use_cases.py`, `tests/test_api.py` |
| R2.2 | Công thức xếp hạng quán (tổng trọng số = 1.0) | `src/domain/services/search_ranking.py` | `tests/test_domain_ranking.py` |
| R2.3 | Gợi ý món nằm TRONG từng kết quả | `search_restaurants._suggest_dish` | `test_search_nests_suggested_dish` |
| R2.4 | Chi tiết quán (review, ảnh, giá, tóm tắt) | `src/presentation/api/routers/restaurants.py` · `src/application/use_cases/get_restaurant_details.py` | `tests/test_api.py` |
| R2.4b | Không khí / giờ mở cửa trả MẢNG, không phải chuỗi repr Python | `src/infrastructure/repositories/json_restaurant_details_repository.py` | `test_details_repo_decodes_python_repr_columns` |
| R2.5 | Thiếu dữ liệu → 503 kèm lệnh cần chạy | `src/application/use_cases/restaurant_data_guard.py` | `test_search_returns_503_when_data_missing` |
| R2.6 | So khớp tiếng Việt: bỏ dấu + từ nguyên vẹn + dấu là bằng chứng | `src/domain/value_objects/text.py` | `test_khong_khop_chuoi_con` · `tests/test_text_matching.py` |
| R2.7 | Suy mood từ câu gõ theo TỪ NGUYÊN VẸN | `src/domain/value_objects/mood.py` | `test_tu_khoa_that_van_khop` · `tests/test_mood_inference_whole_word.py` |
| R2.8 | Tách địa danh khỏi câu tìm kiếm ("gần Hồ Gươm") | `src/domain/services/query_location.py` | `test_cac_gioi_tu_dia_diem_co_dau` |
| R2.9 | Thời tiết lỗi KHÔNG làm hỏng lượt tìm | `src/infrastructure/adapters/open_meteo_context_provider.py` | `test_loi_mang_thi_tra_ngu_canh_trung_lap` |
| R2.10 | Giờ mở cửa · quán đóng cửa hẳn | `src/domain/value_objects/opening_hours.py` | `test_closed_day_is_not_open` · `tests/test_closed_restaurants.py` |
| R2.11 | Nhãn "nổi tiếng" (đủ cả rating lẫn số review) | `src/domain/services/restaurant_badges.py` | `test_du_ca_hai_dieu_kien_thi_noi_tieng` |
| R2.12 | Hợp đồng kết quả giống nhau ở hai lối vào | `src/presentation/api/schemas.py` | `test_search_tra_du_tuoi_that_va_co_dong_tam` |
| R2.13 | Thông tin chung: sức khoẻ hệ thống, danh sách mood | `src/presentation/api/routers/meta.py` | `tests/test_api.py` |

## Tài khoản người dùng

Đổi phạm vi CÓ CHỦ ĐÍCH so với SRS mục 8 (xem ghi chú trong `PROJECT_CHECKLIST.md`).

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| A1.1 | Đăng ký · đăng nhập · đăng xuất | `src/presentation/api/routers/auth.py` · `src/application/use_cases/manage_account.py` · `src/domain/entities/user.py` | `tests/test_auth_api.py`, `tests/test_user_auth.py` |
| A1.2 | Không tự đăng ký thành admin | `src/domain/entities/user.py` | `test_khong_the_tu_dang_ky_thanh_admin_qua_tham_so` |
| A1.3 | Băm mật khẩu, ký token | `src/infrastructure/auth/crypto.py` · `src/infrastructure/auth/user_auth.py` | `tests/test_audit_tai_khoan.py` |
| A1.4 | Quên / đặt lại mật khẩu qua thư | `src/infrastructure/auth/password_reset.py` · `src/infrastructure/notifications/smtp_email_sender.py` | `test_quen_mat_khau_gui_thu_va_doi_duoc_mat_khau` |
| A1.5 | Xác minh email | `src/infrastructure/auth/email_verification.py` | `test_xac_minh_thanh_cong_thi_email_verified_thanh_true` |
| A2.1 | Quán & món yêu thích (đồng bộ từ máy khách) | `src/presentation/api/routers/me.py` · `src/application/use_cases/manage_favorites.py` · `src/domain/entities/saved_item.py` | `test_luu_va_doc_lai_duoc` · `test_chua_dang_nhap_thi_401_chu_khong_phai_danh_sach_rong` |
| A2.2 | Hai danh sách lưu (yêu thích / muốn thử) | `src/infrastructure/repositories/sqlite_saved_item_repository.py` | `test_bo_trong_list_type_thi_mac_dinh_la_trai_tim` |
| A2.3 | Điểm · cấp độ · huy hiệu | `src/application/use_cases/get_user_stats.py` · `src/domain/services/gamification.py` | `test_tai_khoan_moi_co_dung_0_diem_va_cap_1` · `tests/test_gamification.py` |
| A2.4 | Bộ sưu tập | `src/presentation/api/routers/me_collections.py` · `src/application/use_cases/manage_collections.py` · `src/domain/entities/collection.py` | `test_ten_rong_bi_tu_choi` · `test_gioi_han_so_bo_suu_tap` |
| A2.5 | Địa chỉ của tôi (chỉ trong Hà Nội) | `src/presentation/api/routers/me_addresses.py` · `src/application/use_cases/manage_addresses.py` · `src/domain/entities/user_address.py` | `test_toa_do_ngoai_ha_noi_bi_tu_choi_kem_ly_do` |
| A3.1 | Ghi tương tác (`user_id` lấy từ token) | `src/presentation/api/routers/interactions.py` · `src/application/use_cases/log_interaction.py` · `src/domain/entities/interaction.py` | `tests/test_use_cases.py`, `tests/test_api.py` |
| A3.2 | Báo quán đóng cửa — đủ ngưỡng mới ẩn | `src/domain/services/closure_reports.py` | `test_du_nguong_thi_an` · `tests/test_closure_reports.py` |

## Trang quản trị

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| Q1.1 | Phân quyền: chỉ `role='admin'` | `src/presentation/api/routers/admin.py` (`require_admin`) · `src/infrastructure/auth/admin_auth.py` | `test_khong_co_token_thi_401` · `test_dang_nhap_dung_thi_tra_token` |
| Q1.2 | Tạo tài khoản admin không trùng | `scripts/make_admin_user.py` | `test_tu_env_chay_hai_lan_khong_tao_trung` |
| Q2.1 | Tổng quan | `src/application/use_cases/get_admin_overview.py` · `src/domain/services/data_quality.py` | `test_do_phu_khong_mau_thi_la_0_phan_tram_chu_khong_phai_100` |
| Q2.2 | Chất lượng dữ liệu | `src/application/use_cases/get_data_quality.py` · `src/domain/services/data_quality_history.py` | `test_quan_o_tinh_khac_bi_cham_la_ngoai_ha_noi` · `tests/test_admin_chat_luong.py` |
| Q2.3 | Thống kê hệ thống gợi ý | `src/application/use_cases/get_interaction_stats.py` · `src/domain/services/interaction_stats.py` | `test_thong_ke_dem_dung_phien_tai_khoan_va_theo_ngay` |
| Q3.1 | Xem · sửa · ẩn quán | `src/application/use_cases/manage_restaurants.py` · `src/domain/value_objects/restaurant_edit.py` | `test_an_quan_thi_nguoi_dung_cuoi_khong_thay_nua` · `test_sua_quan_khong_ton_tai_tra_404` |
| Q3.2 | Danh mục món cho admin | `src/application/use_cases/list_dishes_admin.py` | `test_bang_mon_tra_phan_trang_va_so_tren_nut_loc` · `test_chi_tiet_mon_co_so_quan_va_danh_sach_quan` |
| Q3.3 | Inbox "Cần xử lý" | `src/application/use_cases/manage_issues.py` · `src/domain/services/data_issues.py` · `src/domain/entities/issue_resolution.py` | `test_tab_da_xu_ly_KHONG_bi_route_issues_key_nuot` · `test_can_xu_ly_giu_lai_ca_dong_bang_0` |
| Q3.4 | Xem và gỡ lượt báo đóng cửa | `src/presentation/api/routers/admin_closures.py` · `src/application/use_cases/manage_closure_reports.py` | `test_xoa_luot_bao_thi_quan_hien_lai_va_dem_lai_tu_dau` |
| Q3.5 | Nhật ký hoạt động quản trị | `src/application/use_cases/manage_audit_log.py` · `src/domain/entities/audit_log.py` | `test_sua_quan_thi_nhat_ky_noi_ro_CU_ROI_MOI` · `test_GHI_NHAT_KY_HONG_KHONG_LAM_HONG_THAO_TAC` |
| Q3.6 | Sửa mô tả món (bản sửa tay, đọc chồng lên danh mục gốc, có nhật ký) | `src/application/use_cases/edit_dish_description.py` · `src/domain/value_objects/dish_description.py` · `src/infrastructure/repositories/overlay_dish_catalog_repository.py` · `src/infrastructure/repositories/sqlite_dish_override_repository.py` | `test_sua_xong_chi_tiet_hien_ban_moi_va_danh_dau_da_sua` · `test_overlay_doc_chong_ban_sua_nhung_goc_van_nguyen` · `test_moi_lan_sua_deu_vao_nhat_ky` |
| Q3.7 | Tìm quán (admin) không phân biệt dấu và hoa/thường | `src/infrastructure/repositories/sqlite_restaurant_repository.py` · `src/domain/value_objects/text.py` | `test_tim_khong_phan_biet_hoa_thuong_va_dau` · `test_tim_khong_dau_khop_quan_co_dau` |
| Q3.8 | Ô tìm kiếm admin: không ghi URL mỗi phím, không phá bộ gõ tiếng Việt | `frontend/packages/admin/src/shared/ui/OTimKiem.tsx` | `OTimKiem.test.tsx` (ca composition) |
| Q3.9 | Sửa mô tả món ngay trên trang chi tiết (nút Sửa / Gỡ bản sửa) | `frontend/packages/admin/src/features/manage-dishes/ui/DishInfo.tsx` · `frontend/packages/admin/src/features/manage-dishes/model/useDishDetail.ts` | `DishInfo.test.tsx` |
| Q4.1 | Giao diện admin | `frontend/packages/admin/src/` | steiger (verify.py mục 7) · Vitest (verify.py mục 6) |

## Bảo mật

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| S1.1 | Giới hạn tần suất API công khai (429) | `src/infrastructure/auth/rate_limit.py` | `test_interactions_qua_gioi_han_chung_tra_429` · `tests/test_rate_limits_public.py` |
| S1.2 | Chặn đoán mật khẩu | `src/presentation/api/login_throttle.py` | `test_doan_mat_khau_admin_bi_chan_sau_vai_lan` |
| S1.3 | CORS mặc định không mở cho mọi trang | `src/presentation/api/main.py` | `test_cors_mac_dinh_khong_mo_cho_moi_trang_web` |
| S1.4 | Lỗi ánh xạ tập trung, 500 không lộ traceback | `src/presentation/api/error_handlers.py` | `tests/test_api.py` |

## Bài viết (cẩm nang và tin cập nhật)

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| B1.1 | Bài web tổng hợp BẮT BUỘC có nguồn (tên + đường dẫn) | `src/domain/entities/post.py` (`validate_post_fields`) | `test_bai_web_thieu_nguon_bi_tu_choi` |
| B1.2 | Tiêu đề quá dài thì báo lỗi, không cắt im lặng | `src/domain/entities/post.py` | `test_tieu_de_qua_dai_bi_bao_loi_khong_tu_cat` |
| B1.3 | Đường dẫn nguồn phải là http(s) | `src/domain/entities/post.py` | `test_nguon_khong_phai_http_bi_tu_choi` |
| B2.1 | Bài mới luôn là NHÁP khi admin không chọn công khai | `src/application/use_cases/manage_posts.py` (`CreatePostUseCase`) | `test_tao_bai_moi_luon_la_nhap_khi_admin_khong_chon` |
| B2.2 | Nháp KHÔNG lọt ra trang công khai (danh sách và chi tiết) | `src/application/use_cases/manage_posts.py` · `src/presentation/api/routers/posts.py` | `test_nhap_khong_lot_ra_trang_cong_khai` · `test_cong_khai_khong_thay_nhap_qua_http` · `test_mot_bai_nhap_tra_404_qua_http_nhu_khong_ton_tai` |
| B2.3 | Giờ công khai đóng dấu một lần; về nháp rồi công khai lại không đổi | `src/application/use_cases/manage_posts.py` (`UpdatePostUseCase`) | `test_cong_bo_roi_moi_hien_va_dong_dau_gio_mot_lan` |
| B2.4 | Trùng tiêu đề vẫn tạo được, đường dẫn tự thêm hậu tố | `src/application/use_cases/manage_posts.py` (`_slug_khong_trung`) | `test_trung_tieu_de_van_tao_duoc_va_co_duong_dan_khac` |
| B2.5 | Sửa tiêu đề không làm gãy đường dẫn đã gửi đi | `src/application/use_cases/manage_posts.py` | `test_sua_tieu_de_khong_doi_duong_dan` |
| B2.6 | Kho không mở được thì 503 kèm cách khắc phục, không sập app | `src/application/use_cases/manage_posts.py` (`PostsNotAvailable`) | `test_kho_khong_mo_duoc_thi_bao_503_khong_lam_sap` |
| B3.1 | Router quản trị bài viết gắn chốt `require_admin` ở cấp router | `src/presentation/api/routers/admin_posts.py` | `test_router_quan_tri_gan_chot_admin` |
| B3.2 | Sửa / xoá bài không tồn tại trả 404 | `src/application/use_cases/manage_posts.py` | `test_sua_bai_khong_ton_tai_bao_404` · `test_xoa_roi_khong_con_thay` |
| B4.1 | Kho SQLite bài viết (chống trùng đường dẫn trong giao dịch) | `src/infrastructure/repositories/sqlite_post_repository.py` | `test_kho_thiet_lap_dung_trang_thai_cua_bai` |
| B4.2 | Router công khai `/posts` | `src/presentation/api/routers/posts.py` | `test_cong_bo_roi_cong_khai_qua_http` |

## Dữ liệu

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| R1.1 | Làm sạch dữ liệu | `data_pipeline/data_cleaning.py` | `tests/test_data_pipeline.py` |
| R1.2 | Sinh đặc trưng | `data_pipeline/feature_engineering.py` | `tests/test_data_pipeline.py` |
| R1.3 | Hợp đồng chung cho mọi nguồn | `data_pipeline/sources/base.py` | `tests/test_data_sources.py` |
| R1.4 | Thu thập quán OSM — **chỉ Hà Nội** | `data_pipeline/sources/osm_overpass.py` (`CITY_BBOXES` chỉ có `ha_noi`) | `tests/test_data_sources.py` |
| R1.5 | Nguồn quán thứ hai: Overture Maps | `data_pipeline/sources/overture_places.py` | `tests/test_data_sources.py` |
| R1.6 | Lọc bỏ nơi không phải quán ăn | `data_pipeline/filter_restaurants.py` | `test_filters_only_food_related_places` |
| R1.7 | Dựng danh mục món | `scripts/build_dish_catalog.py` | `tests/test_dish_catalog_build.py` |
| R1.8 | Tìm món mới (Wikipedia, Wikidata, tên quán) | `scripts/discover_dishes.py` · `scripts/mine_dish_names.py` · `data_pipeline/sources/wikidata_dish.py` | chạy tay; mọi `--apply` đi qua `data_pipeline/dish_approved.json` |
| R1.9 | Giới thiệu + ảnh món | `data_pipeline/sources/wikipedia_dish.py` | chạy tay |
| R1.10 | Kho SQLite | `scripts/build_sqlite.py` · `src/infrastructure/repositories/sqlite_restaurant_repository.py` | `test_quan_bi_an_khong_bao_gio_tra_ve` · `tests/test_sqlite_repository.py` |
| R1.11 | Bộ mẫu frontend không giàu hơn dữ liệu thật | `scripts/make_fixture.py` · `scripts/verify_ui_data.py` | verify.py mục 9 |
| R1.12 | Đo dữ liệu · dung lượng | `scripts/data_report.py` · `scripts/disk_report.py` | chạy tay |

## Năm lớp mô hình của đề án

Số đo 2026-10-10.

| Lớp | Trạng thái | Ở đâu | Kiểm chứng |
|---|---|---|---|
| 1. Phân cụm trải nghiệm | ✅ KMeans k=7 (chọn bằng silhouette) · **1.230/52.872 quán (2,3%)** đủ tín hiệu để phân cụm; còn lại dùng điểm trung lập 0.5 | `data_pipeline/clustering.py` | `tests/test_ml_layers.py` |
| 2. Tìm kiếm ngữ nghĩa | ✅ TF-IDF cosine | `src/infrastructure/adapters/tfidf_semantic_search.py` | `tests/test_ml_layers.py` |
| 3. Xếp hạng ngữ cảnh | 🟡 công thức trọng số cố định (chưa đủ tương tác để học) | `src/domain/services/search_ranking.py` | `tests/test_domain_ranking.py` |
| 4. Tóm tắt review | ✅ trích rút TF-IDF centroid, câu nguyên văn · **884 quán** có tóm tắt, 358 có cả điểm yếu | `data_pipeline/review_summary.py` | `test_giu_cau_du_dai` · `tests/test_review_summary.py` |
| 5. Gợi ý món | ✅ **là cửa vào chính** | `src/domain/services/dish_ranking.py` | `tests/test_dish_ranking.py` |

## Nền tảng

| ID | Yêu cầu | Hiện thực | Kiểm chứng |
|---|---|---|---|
| R0.1 | Hướng phụ thuộc Clean Architecture | `src/` (4 tầng) | `scripts/check_architecture.py` |
| R0.2 | Cấu hình tập trung | `src/infrastructure/config/settings.py` | `tests/test_repositories.py` · `tests/test_dotenv.py` |
| R0.3 | Chuẩn viết code | `CODING_STANDARDS.md`, `CLAUDE.md` | đọc tay |
| R0.4 | Kiến trúc frontend FSD | `frontend/apps/client/src/` · `frontend/packages/admin/src/` | steiger cho cả hai (verify.py mục 7) |
| R0.5 | Một backend duy nhất | `src/` | `scripts/verify.py` mục 4 |
| R0.6 | Ma trận truy vết này không trỏ vào thứ không có | `scripts/check_traceability.py` | `scripts/verify.py` mục 10 |

## Đã DỪNG — không còn trong luồng chạy

| ID | Việc | Trạng thái |
|---|---|---|
| X1 | Floorplan → Spatial JSON → 3D (SegFormer + YOLO) | **BỎ** — train trên bản vẽ kiến trúc không chuyển được sang ảnh chụp thật. Code ở `archive/spatial-3d/`; ảnh còn ở `data_pipeline/data_raw/floorplans_yolo` (xoá được) |
| X2 | Photo → 3D bằng Depth Anything V2 | **TẠM DỪNG** |
| X3 | Backend TypeScript song song | **BỎ** — ở `archive/typescript-backend/` |
