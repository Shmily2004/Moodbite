import { useState } from 'react'
import {
  describeDishConfidence,
  describeMatchSource,
  formatDistance,
  formatPrice,
  formatRating,
} from '../../domain/formatters'
import { getRestaurantDetail, logInteraction } from '../../services/moodbiteApi'

/**
 * Thẻ hiển thị 1 quán. Component "ngu": nhận props, hiển thị, báo tương tác lên trên.
 *
 * Nguyên tắc hiển thị: null = CHƯA CÓ dữ liệu. Không bao giờ hiện "0 sao"/"miễn phí".
 */
export default function RestaurantCard({ restaurant, searchQueryId }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [openedAt, setOpenedAt] = useState(null)

  const loadDetail = async () => {
    setLoading(true)
    setOpenedAt(Date.now())
    try {
      setDetail(await getRestaurantDetail(restaurant.id))
    } catch (err) {
      setDetail({ error: err.userMessage || err.message })
    } finally {
      setLoading(false)
    }
  }

  const close = () => {
    // dwell_time thật = thời gian người dùng thực sự xem, để phân biệt với bấm nhầm.
    if (openedAt) {
      logInteraction({
        restaurantId: restaurant.id,
        actionType: 'view_detail',
        searchQueryId,
        dwellTimeMs: Date.now() - openedAt,
        rankPosition: restaurant.rankPosition,
      })
    }
    setDetail(null)
    setOpenedAt(null)
  }

  const dish = restaurant.suggestedDish

  return (
    <li className="card">
      <div className="card__head">
        <span className="card__rank">#{restaurant.rankPosition}</span>
        <strong>{restaurant.name}</strong>
      </div>

      <div className="card__meta">
        {restaurant.category && <span>{restaurant.category}</span>}
        <span>{formatDistance(restaurant.distanceM)}</span>
        <span>{formatRating(restaurant.rating, restaurant.ratingsTotal)}</span>
        {formatPrice(restaurant.priceRange) && <span>{formatPrice(restaurant.priceRange)}</span>}
      </div>

      {restaurant.address && <div className="card__address">{restaurant.address}</div>}

      {/* Nói thật vì sao quán này được gợi ý, thay vì để người dùng tự đoán. */}
      <div className="card__why">
        Khớp theo: {describeMatchSource(restaurant.matchSource)}
        <span className="card__score"> · điểm {restaurant.score.toFixed(2)}</span>
      </div>

      {dish && (
        <div className="dish">
          <strong>Gợi ý món:</strong> {dish.name}
          {/* Món là SUY LUẬN từ loại hình quán, không phải thực đơn thật -
              luôn hiện mức tin cậy để không nói dối người dùng. */}
          <span className={`dish__confidence dish__confidence--${dish.confidence}`}>
            {describeDishConfidence(dish.confidence)}
          </span>
        </div>
      )}

      {!detail && (
        <button className="btn btn--link" onClick={loadDetail} disabled={loading}>
          {loading ? 'Đang tải…' : 'Xem giá, đánh giá & ảnh'}
        </button>
      )}

      {detail && <Detail detail={detail} onClose={close} restaurant={restaurant}
                         searchQueryId={searchQueryId} />}
    </li>
  )
}

function Detail({ detail, onClose, restaurant, searchQueryId }) {
  if (detail.error) return <div className="error">{detail.error}</div>

  if (!detail.hasDetails) {
    return (
      <div className="detail">
        <p className="muted">{detail.reason}</p>
        <button className="btn btn--link" onClick={onClose}>Đóng</button>
      </div>
    )
  }

  const atmosphere = Array.isArray(detail.atmosphere)
    ? detail.atmosphere.flatMap((o) => (o && typeof o === 'object' ? Object.keys(o) : []))
    : null

  return (
    <div className="detail">
      {detail.priceRange && <div><strong>Giá:</strong> {detail.priceRange}</div>}
      {atmosphere?.length > 0 && <div><strong>Không gian:</strong> {atmosphere.join(', ')}</div>}

      {detail.images.length > 0 && (
        <div className="detail__images">
          {detail.images.slice(0, 6).map((src, i) => (
            <img key={i} src={src} alt="" loading="lazy" />
          ))}
        </div>
      )}

      {detail.reviews.length > 0 && (
        <div className="detail__reviews">
          <strong>Đánh giá ({detail.reviews.length}):</strong>
          {detail.reviews.filter((r) => r.text).slice(0, 4).map((r, i) => (
            <blockquote key={i}>
              <span className="stars">{'★'.repeat(r.stars || 0)}</span> {r.name}
              <p>{r.text}</p>
            </blockquote>
          ))}
        </div>
      )}

      <div className="detail__links">
        {detail.menuUrl && <a href={detail.menuUrl} target="_blank" rel="noreferrer">Xem menu</a>}
        {detail.website && <a href={detail.website} target="_blank" rel="noreferrer">Website</a>}
        {detail.googleMapsUrl && (
          <a
            href={detail.googleMapsUrl}
            target="_blank"
            rel="noreferrer"
            onClick={() =>
              logInteraction({
                restaurantId: restaurant.id,
                actionType: 'get_directions',
                searchQueryId,
                rankPosition: restaurant.rankPosition,
              })
            }
          >
            Chỉ đường
          </a>
        )}
        {!detail.menuUrl && <span className="muted">(quán này chưa có menu trên Google Maps)</span>}
      </div>

      <button className="btn btn--link" onClick={onClose}>Đóng</button>
    </div>
  )
}
