/**
 * THẺ NHỎ cho món/quán đã lưu hoặc đã xem — dựng theo `design/profile.png`: ảnh · tên ·
 * nhãn loại. Thay cho chip chữ (2026-09-16).
 *
 * Component "ngu": KHÔNG gọi API. Ảnh do trang tra sẵn và truyền vào (`useDishImages`).
 *
 * ⚠️ KHÔNG có ⭐ và km như bản thiết kế: mục đã lưu chỉ có `id` + `name`; bịa khoảng cách
 * hay điểm sao là nói dối người dùng (CLAUDE.md mục 4).
 *
 * ẢNH: luôn vẽ ô màu sinh từ tên (`RestaurantThumb`) làm NỀN, ảnh thật (nếu có) phủ lên.
 * Link ảnh ngoài chết thì ẩn `<img>` đi và ô màu lộ ra — không bao giờ hiện ảnh vỡ.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { RestaurantThumb } from '@/entities/restaurant';
import { IconClose } from '@/shared/ui';

export interface ItemCardProps {
  name: string;
  /** "Món ăn" / "Quán ăn" — đã dịch sẵn. */
  typeLabel: string;
  typeIcon?: ReactNode;
  imageUrl?: string | null;
  /** Không truyền = không có trang để dẫn tới (quán chưa có trang riêng) -> không phải link. */
  to?: string | null;
  onRemove?: () => void;
  removeLabel?: string;
  /**
   * Khối gắn thêm dưới thẻ (ô "Thêm vào bộ sưu tập" ở tab Yêu thích). Là một KHE chứ không
   * phải prop riêng cho bộ sưu tập: widget không được biết feature nào (FSD), trang tự
   * quyết đặt gì vào.
   */
  footer?: ReactNode;
}

export function ItemCard({
  name,
  typeLabel,
  typeIcon,
  imageUrl,
  to,
  onRemove,
  removeLabel,
  footer,
}: ItemCardProps) {
  const noiDung = (
    <>
      <div className="item-card__media">
        <RestaurantThumb name={name} />
        {imageUrl && (
          <img
            className="item-card__img"
            src={imageUrl}
            alt=""
            loading="lazy"
            onError={(event) => {
              event.currentTarget.style.display = 'none';
            }}
          />
        )}
      </div>
      <span className="item-card__name">{name}</span>
      <span className="item-card__type">
        {typeIcon} {typeLabel}
      </span>
    </>
  );

  return (
    <li className="item-card">
      {to ? (
        <Link className="item-card__body" to={to}>
          {noiDung}
        </Link>
      ) : (
        <div className="item-card__body">{noiDung}</div>
      )}
      {onRemove && (
        <button
          type="button"
          className="item-card__remove"
          aria-label={removeLabel}
          onClick={onRemove}
        >
          <IconClose />
        </button>
      )}
      {footer && <div className="item-card__footer">{footer}</div>}
    </li>
  );
}
