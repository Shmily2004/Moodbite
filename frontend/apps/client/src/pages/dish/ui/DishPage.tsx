/**
 * TRANG CHI TIẾT MÓN - bước 2 và 3 của luồng.
 *
 *   GIỚI THIỆU NGẮN về món  ->  DANH SÁCH QUÁN gần bạn bán món đó  ->  bấm quán để xem
 *   review/ảnh (panel chi tiết nằm sẵn trong `RestaurantList`).
 *
 * Dùng lại NGUYÊN VẸN `RestaurantList` của luồng tìm kiếm cũ: backend trả về đúng kiểu
 * `SearchResponseData`, nên không cần component thẻ quán thứ hai. Hai bản thẻ quán gần
 * giống nhau là hai chỗ phải cùng sửa mỗi lần đổi cách hiển thị.
 */
import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AssistantBubble } from '@/widgets/assistant-bubble';
import { RestaurantList } from '@/widgets/restaurant-list';
import { RestaurantMap } from '@/widgets/restaurant-map';
import { useDishDetail } from '@/features/view-dish-detail';
import { useUserLocation } from '@/features/pick-location';
import {
  describeCookingMethod,
  describeIntroState,
  describeMealTimes,
  describeRestaurantCount,
  describeSource,
  describeSpice,
  describeTemperature,
} from '@/entities/dish';
import { DEFAULT_RADIUS_KM, ROUTES } from '@/shared/config';

type KieuSapXep = 'gan' | 'hop';

export function DishPage() {
  const [sapXep, setSapXep] = useState<KieuSapXep>('gan');
  const navigate = useNavigate();
  const { dishId } = useParams<{ dishId: string }>();
  const location = useUserLocation();
  const detail = useDishDetail(dishId, location.position, DEFAULT_RADIUS_KM);

  if (detail.notFound) {
    return (
      <div className="shell">
        <div className="state">
          <p className="state__title">Không tìm thấy món này</p>
          <p>Món có thể đã bị gỡ khỏi danh mục.</p>
          <Link className="btn btn--primary" to={ROUTES.home}>
            Chọn món khác
          </Link>
        </div>
      </div>
    );
  }

  const dish = detail.dish;

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

  return (
    <div className="shell">
      <header className="topbar topbar--dish">
        <Link className="btn btn--link" to={ROUTES.home}>
          ← Đổi món
        </Link>
        <span className="brand__name">{dish?.name ?? 'Đang tải…'}</span>
      </header>

      {detail.error && <p className="notice notice--error">{detail.error}</p>}

      {dish && (
        <>
        {/* Đường dẫn phân cấp: cho biết đang ở đâu, và cho một đường VỀ rõ ràng —
            nút Back của trình duyệt không phải ai cũng dùng. */}
        <nav className="breadcrumb" aria-label="Đường dẫn">
          <Link to={ROUTES.home}>Trang chủ</Link>
          <span aria-hidden="true">›</span>
          <span className="breadcrumb__hien-tai">{dish.name}</span>
          <span aria-hidden="true">›</span>
          <span className="breadcrumb__hien-tai">Quán ăn</span>
        </nav>

        <section className="dish-detail">
          {dish.image_url && (
            <img className="dish-detail__image" src={dish.image_url} alt="" />
          )}

          <div className="dish-detail__info">
            <h1 className="dish-detail__name">{dish.name}</h1>

            <ul className="dish__tags">
              {describeTemperature(dish.temperature) && (
                <li className="tag">{describeTemperature(dish.temperature)}</li>
              )}
              {describeCookingMethod(dish.cooking_method) && (
                <li className="tag">{describeCookingMethod(dish.cooking_method)}</li>
              )}
              {describeSpice(dish.spice_level) && (
                <li className="tag">{describeSpice(dish.spice_level)}</li>
              )}
              {describeMealTimes(dish.meal_times) && (
                <li className="tag tag--muted">{describeMealTimes(dish.meal_times)}</li>
              )}
            </ul>

            {/* GIỚI THIỆU NGẮN - nội dung chính của bước 2 trong luồng.
                Chốt 2026-08-19: thay cho danh sách nguyên liệu. Một đoạn văn nói món đó
                là gì và ăn thế nào thì dễ đọc hơn, và phủ được 100% danh mục (đo được),
                trong khi danh sách nguyên liệu chỉ phủ 87%. */}
            <h2 className="dish-detail__heading">Món này là gì?</h2>
            {dish.has_description ? (
              <p className="dish-detail__intro">{dish.description}</p>
            ) : (
              /* Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không có gì để nói".
                 Nói thẳng ra thay vì để một vùng trắng (CLAUDE.md mục 4 quy tắc 1). */
              <p className="muted">{describeIntroState(false)}</p>
            )}

            {/* Nguồn dữ liệu: người đọc phải biết đoạn giới thiệu này ở đâu ra. */}
            {describeSource(dish.source) && (
              <p className="dish-detail__source small muted">
                Nguồn: {describeSource(dish.source)}
                {dish.source_url && (
                  <>
                    {' · '}
                    <a href={dish.source_url} target="_blank" rel="noreferrer">
                      xem nguồn
                    </a>
                  </>
                )}
              </p>
            )}
          </div>
        </section>
        </>
      )}

      <section className="dish-restaurants">
        <div className="dish-restaurants__head">
          <h2 className="dish-detail__heading">
            {dish ? describeRestaurantCount(dish.restaurant_count) : 'Quán gần bạn'}
          </h2>

          {/* SẮP XẾP Ở PHÍA CLIENT, có chủ đích.
              `/dishes/{id}/restaurants` CHƯA có tham số sort. Thêm vào API là đổi hợp
              đồng, nên tạm sắp ngay trên danh sách đã tải — mọi trường cần để sắp đều
              đã nằm trong kết quả. Hệ quả phải biết: chỉ sắp trong SỐ QUÁN ĐÃ TẢI, nên
              nhãn nói "trong danh sách này" chứ không hứa là toàn thành phố. */}
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
          <div className="dish-restaurants__body">
            {/* Danh sách ĐỨNG TRƯỚC bản đồ trong DOM (đổi 2026-08-26 theo thiết kế):
                nó là nội dung chính, và trình đọc màn hình nên gặp nó trước. Bố cục
                trái/phải do CSS lo. */}
            <RestaurantList
              restaurants={quanDaSap}
              searchQueryId={detail.searchQueryId}
              queryText={dish?.name ?? null}
            />
            <div className="map-pane">
              <RestaurantMap
                restaurants={quanDaSap}
                center={location.position}
                userPosition={location.isDefault ? null : location.position}
                activeId={null}
                onSelect={() => undefined}
              />
            </div>
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

      {/* Bong bóng trợ lý — trang này có danh sách quán nên bộ lọc có tác dụng thật.
          Bấm vào thì về trang kết quả gợi ý, nơi giữ bộ lọc. */}
      <AssistantBubble onOpen={() => navigate(ROUTES.recommend)} />
    </div>
  );
}
