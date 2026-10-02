/**
 * VIEW: danh sách quán khớp một món (tab "Danh sách quán" + khối "Top quán" ở tab Tổng quan).
 *
 * ⚠️ Món là SUY LUẬN theo TÊN QUÁN, không phải thực đơn thật (CLAUDE.md mục 4 quy tắc 4),
 * nên mỗi dòng nói rõ CÁCH khớp. Đánh giá `null` hiện "chưa có", KHÔNG BAO GIỜ hiện 0.
 */
import { Link } from 'react-router-dom';
import type { AdminDishRestaurant } from '@/shared/api';
import {
  NHAN_CACH_KHOP,
  NHAN_NGUON_QUAN,
  ROUTES,
  nhanTheoMa,
} from '@/shared/config';
import { soVN } from '@/shared/lib';
import { AnhThuNho } from '@/shared/ui';

export function DishRestaurantList({ quan }: { quan: AdminDishRestaurant[] }) {
  if (quan.length === 0) {
    return (
      <p className="muted">
        Chưa có quán nào trong dữ liệu khớp món này. Dữ liệu được đối chiếu theo TÊN QUÁN,
        nên quán có bán nhưng không ghi tên món thì không tìm ra được.
      </p>
    );
  }

  return (
    <ol className="quan-cua-mon">
      {quan.map((q, i) => (
        <li key={q.restaurant_id ?? `${q.name}-${i}`} className="quan-cua-mon__dong">
          <span className="quan-cua-mon__hang">{i + 1}</span>
          {/* Ảnh quán là link Google ngoài, chết dần theo thời gian -> ô giữ chỗ. */}
          <AnhThuNho src={q.thumbnail_url} className="o-anh" classNameTrong="o-anh--trong" />
          <div className="quan-cua-mon__chu">
            <p className="bang__ten">{q.name}</p>
            <p className="muted small">
              {[q.address, q.district].filter(Boolean).join(', ') || 'chưa có địa chỉ'}
            </p>
            <p className="small">
              <span className="nhan nhan--tat">
                Nguồn: {nhanTheoMa(NHAN_NGUON_QUAN, q.source)}
              </span>
              <span
                className={q.matched_by === 'review' ? 'nhan nhan--canh-bao' : 'nhan nhan--tin'}
              >
                {nhanTheoMa(NHAN_CACH_KHOP, q.matched_by)}
              </span>
            </p>
          </div>
          <div className="quan-cua-mon__diem">
            {q.rating != null ? (
              <>
                <span className="bang__ten">{q.rating.toLocaleString('vi-VN')} ★</span>
                {q.reviews_count != null && (
                  <span className="muted small">{soVN(q.reviews_count)} đánh giá</span>
                )}
              </>
            ) : (
              <span className="muted small">chưa có đánh giá</span>
            )}
          </div>
          {/* Không có trang chi tiết quán trong khu quản trị — dẫn sang bảng quán đã lọc
              sẵn theo mã, nơi sửa/ẩn được quán đó. */}
          {q.restaurant_id && (
            <Link
              className="linkish"
              to={`${ROUTES.restaurants}?q=${encodeURIComponent(q.restaurant_id)}`}
            >
              Xem trong Quản lý quán →
            </Link>
          )}
        </li>
      ))}
    </ol>
  );
}
