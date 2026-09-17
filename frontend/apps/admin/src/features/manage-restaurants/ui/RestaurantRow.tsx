/**
 * VIEW: một dòng quán trong bảng quản trị, có chế độ xem và chế độ sửa.
 *
 * Chỉ giữ state của RIÊNG form đang sửa (state giao diện). Việc gọi API là của
 * ViewModel ở tầng trên.
 */
import { useState } from 'react';
import type {
  AdminRestaurantSummary,
  AdminUpdateRestaurantRequest,
} from '@moodbite/api-client';
import { NHAN_NGUON_QUAN, nhanTheoMa } from '@/shared/config';
import { ngayGioVN, soVN } from '@/shared/lib';

/** Số cột của bảng — dòng đang sửa phải trải hết chiều ngang. */
const SO_COT = 10;

/** Trường admin sửa được — khớp với EDITABLE_FIELDS ở backend. */
const EDITABLE: Array<{ key: keyof AdminUpdateRestaurantRequest; label: string }> = [
  { key: 'name', label: 'Tên quán' },
  { key: 'category', label: 'Loại hình' },
  { key: 'cuisine', label: 'Ẩm thực' },
  { key: 'address', label: 'Địa chỉ' },
  { key: 'district', label: 'Khu vực' },
  { key: 'price', label: 'Khoảng giá' },
  { key: 'phone', label: 'Điện thoại' },
  { key: 'website', label: 'Website' },
];

export interface RestaurantRowProps {
  restaurant: AdminRestaurantSummary;
  /** Có ô chọn hàng loạt hay không (quán thiếu mã thì không chọn được). */
  selected?: boolean;
  onToggleSelected?: (id: string) => void;
  onToggleHidden: (restaurant: AdminRestaurantSummary) => void;
  onSave: (id: string, changes: AdminUpdateRestaurantRequest) => Promise<boolean>;
}

export function RestaurantRow({
  restaurant,
  selected = false,
  onToggleSelected,
  onToggleHidden,
  onSave,
}: RestaurantRowProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<AdminUpdateRestaurantRequest>({});
  const [saving, setSaving] = useState(false);

  const startEdit = () => {
    setDraft(
      Object.fromEntries(
        EDITABLE.map(({ key }) => [key, (restaurant[key] as string | null) ?? '']),
      ),
    );
    setEditing(true);
  };

  const save = async () => {
    setSaving(true);
    // Chuỗi rỗng -> null: đó là ý muốn XOÁ giá trị. Backend cũng hiểu như vậy.
    const changes = Object.fromEntries(
      Object.entries(draft).map(([k, v]) => [k, v === '' ? null : v]),
    ) as AdminUpdateRestaurantRequest;
    const ok = await onSave(restaurant.restaurant_id ?? '', changes);
    setSaving(false);
    if (ok) setEditing(false);
  };

  if (editing) {
    return (
      <tr className="row row--editing">
        <td colSpan={SO_COT}>
          <div className="edit-grid">
            {EDITABLE.map(({ key, label }) => (
              <label key={key}>
                <span>{label}</span>
                <input
                  value={(draft[key] as string | null) ?? ''}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, [key]: event.target.value }))
                  }
                />
              </label>
            ))}
          </div>
          <p className="muted small">
            Để trống một ô nghĩa là XOÁ giá trị đó. Đánh giá, số lượt đánh giá và cụm
            trải nghiệm không sửa được ở đây — chúng do pipeline dữ liệu sinh ra.
          </p>
          <div className="actions">
            <button onClick={() => void save()} disabled={saving}>
              {saving ? 'Đang lưu…' : 'Lưu'}
            </button>
            <button className="ghost" onClick={() => setEditing(false)} disabled={saving}>
              Huỷ
            </button>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr className={restaurant.is_active ? 'row' : 'row row--hidden'}>
      <td>
        {restaurant.restaurant_id && onToggleSelected && (
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onToggleSelected(restaurant.restaurant_id ?? '')}
            aria-label={`Chọn ${restaurant.name}`}
          />
        )}
      </td>
      <td>
        <div className="o-mon">
          {restaurant.thumbnail_url ? (
            <img className="o-anh" src={restaurant.thumbnail_url} alt="" loading="lazy" />
          ) : (
            <span className="o-anh o-anh--trong" aria-hidden="true" />
          )}
          <div>
            <span className="bang__ten">{restaurant.name}</span>
            <span className="bang__phu muted small">
              {restaurant.category ?? 'chưa rõ loại hình'}
            </span>
          </div>
        </div>
      </td>
      <td className="small">{restaurant.address ?? <span className="muted">chưa có địa chỉ</span>}</td>
      <td className="small">{restaurant.district ?? <span className="muted">—</span>}</td>
      {/* `null` = CHƯA CÓ DỮ LIỆU, không phải 0 sao. Không bao giờ hiện "0". */}
      <td className="tnum">
        {restaurant.rating != null ? (
          <span className="bang__ten">{restaurant.rating.toLocaleString('vi-VN')} ★</span>
        ) : (
          <span className="muted small">chưa có</span>
        )}
      </td>
      <td className="tnum small muted">
        {restaurant.reviews_count != null ? `(${soVN(restaurant.reviews_count)})` : '—'}
      </td>
      <td>
        {/* NGUỒN ngay trên dòng: quán `manual:` do người gõ tay, sửa thoải mái; quán từ
            Overture/OSM thì lần chạy pipeline sau có thể ghi đè. */}
        <span className={restaurant.source === 'manual' ? 'nhan nhan--tin' : 'nhan nhan--tat'}>
          {nhanTheoMa(NHAN_NGUON_QUAN, restaurant.source)}
        </span>
      </td>
      <td>
        {restaurant.is_active ? (
          <span className="nhan nhan--ok">Đang hiện</span>
        ) : (
          <span className="nhan nhan--loi">Đã ẩn</span>
        )}
      </td>
      {/* Ngày NGUỒN cập nhật bản ghi (quán nhập tay: ngày nhập). Không có thì "—" —
          KHÔNG thay bằng ngày dựng CSDL, vì đó là nói sai tuổi dữ liệu. */}
      <td className="small muted" title="Ngày nguồn dữ liệu cập nhật bản ghi">
        {ngayGioVN(restaurant.source_updated_at)}
      </td>
      <td className="actions">
        <button className="ghost" onClick={startEdit}>
          Sửa
        </button>
        <button className="ghost" onClick={() => onToggleHidden(restaurant)}>
          {restaurant.is_active ? 'Ẩn' : 'Bỏ ẩn'}
        </button>
      </td>
    </tr>
  );
}
