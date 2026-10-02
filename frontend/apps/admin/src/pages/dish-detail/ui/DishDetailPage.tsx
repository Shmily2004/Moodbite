/**
 * TRANG CHI TIẾT MÓN của khu quản trị — `/mon-an/:dishId`.
 *
 * Dựng theo `frontend/design/dish details admin.png`:
 *
 *   ← Quay lại danh sách món ăn
 *   [ảnh] Bún chả  (Có quán)(danh mục)      Số quán bán 94       (khối Thao tác)
 *         Ẩm thực · Mô tả ngắn              Lần cập nhật gần nhất
 *   Tab: Tổng quan · Danh sách quán (94) · Thông tin chi tiết · Lịch sử cập nhật
 *
 * ⚠️ KHÔNG CÓ KHỐI "THAO TÁC" (Chỉnh sửa · Cập nhật mô tả · Cập nhật ảnh · Ngừng hoạt
 * động) dù bản thiết kế có. Backend CHƯA có endpoint nào sửa món: `dish_catalog.json` là
 * file do `build_dish_catalog.py` SINH RA, ghi thẳng vào đó sẽ bị lần chạy sau xoá sạch.
 * Chọn BỎ HẲN thay vì hiện nút mờ: bốn nút không bấm được chiếm cả một khối mà không giúp
 * gì; một dòng ghi chú nói rõ lý do là đủ.
 *
 * ⚠️ "Lịch sử cập nhật" đọc NHẬT KÝ HOẠT ĐỘNG lọc theo đúng món này. Vì món chưa sửa được
 * qua trang quản trị nên hiện tại tab này luôn trống — và trang nói thẳng như vậy.
 */
import type { ReactNode } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import {
  DishInfo,
  DishRestaurantList,
  useDishDetail,
} from '@/features/manage-dishes';
import { ROUTES } from '@/shared/config';
import { ngayGioVN, soVN, useDatNhanBreadcrumb } from '@/shared/lib';
import { AnhThuNho, Icon } from '@/shared/ui';

type Tab = 'tong-quan' | 'quan' | 'thong-tin' | 'lich-su';

const TAB_HOP_LE: Tab[] = ['tong-quan', 'quan', 'thong-tin', 'lich-su'];
/** Khối "Top quán" ở tab Tổng quan — đúng số dòng bản thiết kế vẽ. */
const SO_QUAN_TOP = 5;

export function DishDetailPage() {
  const { dishId = '' } = useParams();
  const { dish, restaurants, history } = useDishDetail(dishId);
  // Tab nằm trên URL: F5 hoặc gửi link vẫn mở đúng tab.
  const [thamSo, setThamSo] = useSearchParams();
  const tuUrl = thamSo.get('tab') as Tab | null;
  const tab: Tab = tuUrl && TAB_HOP_LE.includes(tuUrl) ? tuUrl : 'tong-quan';
  const chonTab = (t: Tab) => {
    const moi = new URLSearchParams(thamSo);
    if (t === 'tong-quan') moi.delete('tab');
    else moi.set('tab', t);
    setThamSo(moi, { replace: true });
  };

  useDatNhanBreadcrumb(dish.data?.name ?? null);

  const mon = dish.data;
  // Số quán: ưu tiên con số của chỉ mục (restaurant_count); danh sách quán chỉ là phần đầu.
  const soQuan = mon?.restaurant_count ?? restaurants.data?.total ?? null;

  return (
    <div className="chi-tiet-mon">
      {/* Link quay lại dùng lịch sử KHÔNG được: mở thẳng link chi tiết thì "Back" ra khỏi
          app. Dẫn về bảng món là đích chắc chắn đúng. */}
      <Link className="nut-quay-lai" to={ROUTES.dishes}>
        <Icon ten="mui-ten-trai" /> Quay lại danh sách món ăn
      </Link>

      {dish.loading && <p className="panel muted">Đang tải món…</p>}
      {dish.error && <p className="panel panel--error">{dish.error}</p>}

      {mon && (
        <>
          <section className="panel chi-tiet-mon__dau">
            <AnhThuNho
              src={mon.image_url}
              className="chi-tiet-mon__anh"
              classNameTrong="chi-tiet-mon__anh--trong"
              alt={mon.name}
            >
              Chưa có ảnh
            </AnhThuNho>
            <div className="chi-tiet-mon__chinh">
              <h2 className="tong-quan__chao">{mon.name}</h2>
              <p className="chi-tiet__nhan-hang">
                <span className={mon.is_active ? 'nhan nhan--ok' : 'nhan nhan--tat'}>
                  {mon.is_active ? 'Có quán' : 'Chưa có quán'}
                </span>
                {mon.is_category && <span className="nhan nhan--tin">danh mục</span>}
              </p>
              <dl className="chi-tiet-mon__tom-tat">
                <dt>Ẩm thực</dt>
                <dd>{mon.cuisine ?? '—'}</dd>
                <dt>Mô tả ngắn</dt>
                <dd className="cat-dong">{mon.description ?? 'Chưa có mô tả.'}</dd>
              </dl>
            </div>
            <dl className="chi-tiet-mon__so">
              <dt className="muted small">Số quán bán</dt>
              <dd className="the-so__gia-tri">{soQuan == null ? '—' : soVN(soQuan)}</dd>
              <dd className="muted small">quán tại Hà Nội (khớp theo tên quán)</dd>
              <dt className="muted small">Lần cập nhật gần nhất</dt>
              <dd>{ngayGioVN(mon.last_updated)}</dd>
            </dl>
          </section>

          <p className="muted small">
            Chưa có thao tác sửa: danh mục món là file do <code>build_dish_catalog.py</code>{' '}
            sinh ra, sửa qua trang quản trị sẽ bị lần chạy sau ghi đè.
          </p>

          <div className="tab-loc" role="tablist" aria-label="Nội dung chi tiết món">
            <NutTab dang={tab} khoa="tong-quan" onChon={chonTab}>
              Tổng quan
            </NutTab>
            <NutTab dang={tab} khoa="quan" onChon={chonTab}>
              Danh sách quán{soQuan != null && ` (${soVN(soQuan)})`}
            </NutTab>
            <NutTab dang={tab} khoa="thong-tin" onChon={chonTab}>
              Thông tin chi tiết
            </NutTab>
            <NutTab dang={tab} khoa="lich-su" onChon={chonTab}>
              Lịch sử cập nhật
            </NutTab>
          </div>

          {tab === 'tong-quan' && (
            <div className="chi-tiet-mon__luoi">
              <section className="panel">
                <h3 className="panel__tieu-de">Thông tin chi tiết</h3>
                <DishInfo data={mon} />
              </section>
              <section className="panel">
                <div className="bang__dau">
                  <h3 className="panel__tieu-de">
                    Top quán bán món này{soQuan != null && ` (${soVN(soQuan)})`}
                  </h3>
                  {(restaurants.data?.total ?? 0) > SO_QUAN_TOP && (
                    <button type="button" className="linkish" onClick={() => chonTab('quan')}>
                      Xem tất cả →
                    </button>
                  )}
                </div>
                <KhoiQuan
                  loading={restaurants.loading}
                  error={restaurants.error}
                  quan={restaurants.data?.results.slice(0, SO_QUAN_TOP) ?? null}
                />
                {/* "Xem thêm N quán" của bản thiết kế. N = tổng THẬT do server đếm trừ số
                    đang hiện — chỉ hiện khi thật sự còn quán, và dẫn sang tab danh sách. */}
                {restaurants.data && restaurants.data.total > SO_QUAN_TOP && (
                  <button
                    type="button"
                    className="nut-xem-them"
                    onClick={() => chonTab('quan')}
                  >
                    Xem thêm {soVN(restaurants.data.total - SO_QUAN_TOP)} quán
                  </button>
                )}
              </section>
            </div>
          )}

          {tab === 'quan' && (
            <section className="panel">
              {restaurants.data && (
                <p className="muted small">
                  Hiện {soVN(restaurants.data.results.length)} trong{' '}
                  {soVN(restaurants.data.total)} quán. Thứ tự: khớp chắc trước (tên quán ghi
                  đúng tên món), cùng mức thì quán có đánh giá trước.
                </p>
              )}
              <KhoiQuan
                loading={restaurants.loading}
                error={restaurants.error}
                quan={restaurants.data?.results ?? null}
              />
            </section>
          )}

          {tab === 'thong-tin' && (
            <section className="panel">
              <DishInfo data={mon} />
            </section>
          )}

          {tab === 'lich-su' && (
            <section className="panel">
              <h3 className="panel__tieu-de">Lịch sử cập nhật</h3>
              {history.loading && <p className="muted">Đang tải…</p>}
              {history.error && <p className="notice notice--warn">{history.error}</p>}
              {!history.loading && !history.error && !history.available && (
                <p className="notice notice--warn">
                  Không mở được kho nhật ký — đây <strong>không phải</strong> là "chưa có thay
                  đổi nào".
                </p>
              )}
              {history.available && history.data && history.data.length === 0 && (
                <p className="muted">
                  Chưa có thay đổi nào được ghi cho món này. Món hiện chỉ xem được, chưa sửa
                  qua trang quản trị, nên nhật ký chưa có dòng nào về món.
                </p>
              )}
              {history.data && history.data.length > 0 && (
                <ul className="nhat-ky">
                  {history.data.map((e, i) => (
                    <li key={`${e.created_at}-${i}`} className="nhat-ky__dong">
                      <div className="nhat-ky__chinh">
                        <p className="nhat-ky__hanh-dong">{e.action_label}</p>
                        <p className="muted nhat-ky__tom-tat">
                          {e.summary} · bởi {e.actor}
                        </p>
                      </div>
                      <span className="muted nhat-ky__gio">{ngayGioVN(e.created_at)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}

function NutTab({
  dang,
  khoa,
  onChon,
  children,
}: {
  dang: Tab;
  khoa: Tab;
  onChon: (t: Tab) => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={dang === khoa}
      className={dang === khoa ? 'tab-loc__nut tab-loc__nut--dang' : 'tab-loc__nut'}
      onClick={() => onChon(khoa)}
    >
      {children}
    </button>
  );
}

function KhoiQuan({
  loading,
  error,
  quan,
}: {
  loading: boolean;
  error: string | null;
  quan: Parameters<typeof DishRestaurantList>[0]['quan'] | null;
}) {
  if (loading) return <p className="muted">Đang tải danh sách quán…</p>;
  if (error) return <p className="notice notice--warn">{error}</p>;
  if (!quan) return null;
  return <DishRestaurantList quan={quan} />;
}
