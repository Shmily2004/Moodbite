/**
 * TRANG CHI TIẾT MÓN - bước 2 và 3 của luồng.
 *
 *   GIỚI THIỆU NGẮN về món  ->  DANH SÁCH QUÁN gần bạn bán món đó  ->  bấm quán để xem
 *   review/ảnh (panel chi tiết nằm sẵn trong `RestaurantList`).
 *
 * Dùng lại NGUYÊN VẸN `RestaurantList` của luồng tìm kiếm cũ: backend trả về đúng kiểu
 * `SearchResponseData`, nên không cần component thẻ quán thứ hai. Hai bản thẻ quán gần
 * giống nhau là hai chỗ phải cùng sửa mỗi lần đổi cách hiển thị.
 *
 * ⚠️ MỌI HOOK PHẢI ĐỨNG TRƯỚC MỌI `return` SỚM (Rules of Hooks). Lỗi thật sửa 2026-09-16:
 * `useMemo` sắp xếp quán từng nằm SAU nhánh `if (detail.notFound) return …`, nên khi đi từ
 * một món có thật sang một món bị gỡ (cùng component, chỉ đổi `:dishId`) React thấy số
 * hook giảm và ném "Rendered fewer hooks than expected" — trang trắng. Có test khoá lại.
 */
import { useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { AssistantBubble } from '@/widgets/assistant-bubble';
import { RestaurantList } from '@/widgets/restaurant-list';
import { RestaurantMap } from '@/widgets/restaurant-map';
import { SiteHeader } from '@/widgets/site-header';
import { useDishDetail } from '@/features/view-dish-detail';
import { useUserLocation } from '@/features/pick-location';
import { describeRestaurantCount } from '@/entities/dish';
import { DEFAULT_RADIUS_KM, ROUTES } from '@/shared/config';
import { DishFilterPanel } from './DishFilterPanel';
import { DishIntro } from './DishIntro';

type KieuSapXep = 'gan' | 'hop';

/** Số quán hiện lúc đầu. "Xem thêm quán" mở hết phần còn lại. */
const SO_QUAN_BAN_DAU = 8;

export function DishPage() {
  const [sapXep, setSapXep] = useState<KieuSapXep>('gan');
  // Cắt bớt danh sách lúc đầu (bản thiết kế có nút "Xem thêm quán"): 20 thẻ quán đẩy
  // bản đồ và mọi thứ dưới nó ra khỏi màn hình ngay lần đầu vào trang.
  const [xemHet, setXemHet] = useState(false);
  // Ẩn bản đồ để danh sách rộng ra (nút "Xem danh sách" trên bản đồ trong thiết kế).
  const [anBanDo, setAnBanDo] = useState(false);
  const [moBoLoc, setMoBoLoc] = useState(false);
  const { dishId } = useParams<{ dishId: string }>();
  const [urlParams] = useSearchParams();
  const location = useUserLocation();
  // Công tắc giá THEO ĐƯỢC từ trang gợi ý sang: đi từ `/recommend?gia=1` mà tới đây rồi
  // thấy lại đủ quán không giá thì người dùng tưởng bộ lọc tự tắt. Cùng tham số `gia=1`
  // mà `ghiBoLocLenUrl` sinh ra, nên hai trang không thể nói lệch nhau.
  const chiQuanCoGia = urlParams.get('gia') === '1';
  const detail = useDishDetail(
    dishId,
    location.position,
    DEFAULT_RADIUS_KM,
    chiQuanCoGia,
  );

  /**
   * Thứ tự hiển thị danh sách quán.
   *   'hop' = giữ nguyên thứ tự backend trả (theo `predicted_score`) — mặc định của API.
   *   'gan' = gần nhất trước.
   * Mặc định 'gan' theo thiết kế chủ dự án gửi 2026-08-26.
   */
  const quanDaSap = useMemo(() => {
    if (sapXep !== 'gan') return detail.restaurants;
    // `distance_m` có thể thiếu (quán không rõ toạ độ) -> đẩy xuống cuối thay vì coi là 0,
    // nếu không quán không biết ở đâu lại đứng đầu danh sách "gần bạn nhất".
    return [...detail.restaurants].sort(
      (a, b) => (a.distance_m ?? Infinity) - (b.distance_m ?? Infinity),
    );
  }, [detail.restaurants, sapXep]);

  if (detail.notFound) {
    return (
      <div className="page">
        <SiteHeader />
        <main className="dish-page">
          <div className="state">
            <p className="state__title">Không tìm thấy món này</p>
            <p>Món có thể đã bị gỡ khỏi danh mục.</p>
            <Link className="btn btn--primary" to={ROUTES.home}>
              Chọn món khác
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const dish = detail.dish;
  const quanHien = xemHet ? quanDaSap : quanDaSap.slice(0, SO_QUAN_BAN_DAU);
  const conLai = quanDaSap.length - quanHien.length;

  return (
    <div className="page">
      <SiteHeader />

      <main className="dish-page">
        {/* Đường về + đường dẫn phân cấp nằm TRONG nội dung (thanh trên nay là
            `SiteHeader` dùng chung). Nút Back của trình duyệt không phải ai cũng dùng. */}
        <nav className="breadcrumb" aria-label="Đường dẫn">
          <Link to={ROUTES.home}>← Đổi món</Link>
          <span aria-hidden="true">·</span>
          <Link to={ROUTES.home}>Trang chủ</Link>
          <span aria-hidden="true">›</span>
          <span className="breadcrumb__hien-tai">{dish?.name ?? 'Đang tải…'}</span>
          {dish && (
            <>
              <span aria-hidden="true">›</span>
              <span className="breadcrumb__hien-tai">Quán ăn</span>
            </>
          )}
        </nav>

        {detail.error && <p className="notice notice--error">{detail.error}</p>}

        {dish && <DishIntro dish={dish} onEditFilters={() => setMoBoLoc(true)} />}

        <section className="dish-restaurants">
          <div className="dish-restaurants__head">
            <h2 className="dish-detail__heading">
              {dish ? describeRestaurantCount(dish.restaurant_count) : 'Quán gần bạn'}
            </h2>

            {/* SẮP XẾP Ở PHÍA CLIENT, có chủ đích.
                `/dishes/{id}/restaurants` CHƯA có tham số sort. Thêm vào API là đổi hợp
                đồng, nên tạm sắp ngay trên danh sách đã tải — mọi trường cần để sắp đều
                đã nằm trong kết quả. Hệ quả phải biết: chỉ sắp trong SỐ QUÁN ĐÃ TẢI. */}
            <label className="dish-restaurants__sort">
              <span className="sr-only">Sắp xếp danh sách quán</span>
              <select
                value={sapXep}
                onChange={(event) => setSapXep(event.target.value as KieuSapXep)}
              >
                <option value="gan">Gần bạn nhất</option>
                <option value="hop">Phù hợp nhất</option>
              </select>
            </label>
          </div>

          {detail.restaurantsError && (
            <p className="notice notice--error">{detail.restaurantsError}</p>
          )}

          {detail.warnings.map((warning, index) => (
            <p key={index} className="notice notice--warn">
              {warning}
            </p>
          ))}

          {detail.loading && <p className="muted">Đang tìm quán…</p>}

          {!detail.loading && detail.restaurants.length > 0 && (
            <div
              className={
                anBanDo
                  ? 'dish-restaurants__body dish-restaurants__body--rong'
                  : 'dish-restaurants__body'
              }
            >
              {/* Danh sách ĐỨNG TRƯỚC bản đồ trong DOM (đổi 2026-08-26 theo thiết kế):
                  nó là nội dung chính, và trình đọc màn hình nên gặp nó trước. */}
              <div className="dish-restaurants__ds">
                <RestaurantList
                  restaurants={quanHien}
                  searchQueryId={detail.searchQueryId}
                  queryText={dish?.name ?? null}
                  // Đánh số khớp ghim bản đồ — chỉ ở trang này, không ở trang tìm kiếm.
                  danhSo
                />

                {/* "XEM THÊM QUÁN" (bản thiết kế). Nói rõ CÒN BAO NHIÊU. */}
                {conLai > 0 && (
                  <button
                    type="button"
                    className="btn btn--rong"
                    onClick={() => setXemHet(true)}
                  >
                    Xem thêm {conLai} quán ▾
                  </button>
                )}
              </div>

              {!anBanDo && (
                <div className="map-pane">
                  {/* "XEM DANH SÁCH" (bản thiết kế): thu bản đồ để danh sách rộng ra. */}
                  <button
                    type="button"
                    className="map-pane__thu"
                    onClick={() => setAnBanDo(true)}
                  >
                    Xem danh sách
                  </button>
                  <RestaurantMap
                    restaurants={quanHien}
                    center={location.position}
                    userPosition={location.isDefault ? null : location.position}
                    activeId={null}
                    onSelect={() => undefined}
                    danhSo
                  />
                </div>
              )}

              {anBanDo && (
                <button
                  type="button"
                  className="btn btn--rong"
                  onClick={() => setAnBanDo(false)}
                >
                  Hiện lại bản đồ
                </button>
              )}
            </div>
          )}

          {!detail.loading && detail.restaurants.length === 0 && !detail.restaurantsError && (
            <div className="state">
              <p className="state__title">Chưa tìm thấy quán nào bán món này gần bạn</p>
              <p>
                Dữ liệu quán được đối chiếu theo TÊN QUÁN, nên quán có bán nhưng không ghi
                tên món thì chưa tìm ra được.
              </p>
              <Link className="chip" to={ROUTES.home}>
                Chọn món khác
              </Link>
            </div>
          )}
        </section>

        {/* Bong bóng trợ lý — trang này có danh sách quán nên bộ lọc có tác dụng thật. */}
        <AssistantBubble onOpen={() => setMoBoLoc(true)} />

        {/* Ngăn kéo bộ lọc: CHỈ mount khi mở, để bộ lọc ban đầu tính từ món đã tải xong.
            "Xem kết quả" sang `/recommend` KÈM bộ lọc — vì đổi tiêu chí thì MÓN gợi ý
            cũng đổi, mà trang này đã khoá vào đúng một món. */}
        {moBoLoc && (
          <DishFilterPanel
            dish={dish}
            onClose={() => setMoBoLoc(false)}
            locationIsDefault={location.isDefault}
            locationLabel={location.label}
            locationLoading={location.loading}
            onRequestLocation={location.request}
          />
        )}
      </main>
    </div>
  );
}
