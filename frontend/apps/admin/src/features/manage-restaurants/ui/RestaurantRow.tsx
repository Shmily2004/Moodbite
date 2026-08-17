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
  onToggleHidden: (restaurant: AdminRestaurantSummary) => void;
  onSave: (id: string, changes: AdminUpdateRestaurantRequest) => Promise<boolean>;
}

export function RestaurantRow({ restaurant, onToggleHidden, onSave }: RestaurantRowProps) {
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
        <td colSpan={5}>
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
        <b>{restaurant.name}</b>
        <br />
        <span className="muted small">{restaurant.address ?? 'chưa có địa chỉ'}</span>
      </td>
      <td>{restaurant.category ?? '—'}</td>
      {/* `null` = CHƯA CÓ DỮ LIỆU, không phải 0 sao. Không bao giờ hiện "0". */}
      <td>
        {restaurant.rating != null
          ? `${restaurant.rating}★`
          : <span className="muted">chưa có đánh giá</span>}
      </td>
      <td>
        {restaurant.is_active ? (
          <span className="pill pill--on">Đang hiện</span>
        ) : (
          <span className="pill pill--off">Đã ẩn</span>
        )}
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
