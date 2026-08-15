import React, { useState } from 'react'

// Vite (không phải CRA): biến môi trường đọc qua import.meta.env và PHẢI có tiền tố VITE_.
// Dùng process.env ở đây là vô nghĩa - Vite thay process.env bằng {} lúc build nên giá trị
// luôn rơi về fallback, không thể trỏ UI sang API trên Railway.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api'

const MOODS = ['happy', 'sad', 'excited', 'relaxed']

// Google gắn nhãn không gian quán dạng [{'Ấm cúng': true}, ...] -> đổi thành "Ấm cúng, ...".
function formatAtmosphere(raw) {
  if (!Array.isArray(raw)) return null
  const tags = raw.flatMap(o => (o && typeof o === 'object' ? Object.keys(o) : []))
  return tags.length ? tags.join(', ') : null
}

function RestaurantDetails({ placeId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API_BASE}/restaurant/${encodeURIComponent(placeId)}`)
      setData(await r.json())
    } catch (err) {
      setData({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  if (!data) {
    return (
      <button onClick={load} disabled={loading} style={{ marginTop: 6, fontSize: 12 }}>
        {loading ? 'Đang tải...' : 'Xem giá, review & ảnh'}
      </button>
    )
  }

  if (data.error) return <div style={{ color: 'crimson', fontSize: 12 }}>{data.error}</div>

  // 3623/4170 quán lấy từ OpenStreetMap nên không có giá/review - nói thẳng là chưa có
  // dữ liệu, không hiện ô trống khiến người dùng tưởng quán dở hoặc app lỗi.
  if (!data.has_details) {
    return <div style={{ fontSize: 12, color: '#888', marginTop: 6 }}>{data.reason}</div>
  }

  const atmosphere = formatAtmosphere(data.atmosphere)

  return (
    <div style={{ marginTop: 8, padding: 10, background: '#fafafa', borderRadius: 6 }}>
      {data.price && <div style={{ fontSize: 13 }}><strong>Giá:</strong> {data.price}</div>}
      {atmosphere && <div style={{ fontSize: 13 }}><strong>Không gian:</strong> {atmosphere}</div>}

      {data.images?.length > 0 && (
        <div style={{ display: 'flex', gap: 6, overflowX: 'auto', margin: '8px 0' }}>
          {data.images.slice(0, 6).map((src, i) => (
            <img key={i} src={src} alt="" width={110} height={80}
                 style={{ objectFit: 'cover', borderRadius: 4, flexShrink: 0 }} />
          ))}
        </div>
      )}

      {data.reviews?.length > 0 && (
        <div style={{ marginTop: 6 }}>
          <strong style={{ fontSize: 13 }}>Review ({data.reviews.length}):</strong>
          {data.reviews.filter(rv => rv.text).slice(0, 4).map((rv, i) => (
            <div key={i} style={{ fontSize: 12, marginTop: 6, borderLeft: '3px solid #ddd', paddingLeft: 8 }}>
              <div style={{ color: '#b8860b' }}>{'★'.repeat(rv.stars || 0)} <span style={{ color: '#666' }}>{rv.name}</span></div>
              <div style={{ whiteSpace: 'pre-wrap' }}>{rv.text}</div>
            </div>
          ))}
        </div>
      )}

      {/* Google Maps hầu như không có menu có cấu trúc (~2% quán ở Hà Nội), nên chỉ
          dẫn link ra nguồn thay vì bịa dữ liệu menu. */}
      <div style={{ marginTop: 8, fontSize: 12 }}>
        {data.menu_url && <a href={data.menu_url} target="_blank" rel="noreferrer">Xem menu</a>}
        {data.website && <a href={data.website} target="_blank" rel="noreferrer" style={{ marginLeft: 10 }}>Website</a>}
        {data.google_maps_url && <a href={data.google_maps_url} target="_blank" rel="noreferrer" style={{ marginLeft: 10 }}>Google Maps</a>}
        {!data.menu_url && <span style={{ color: '#888', marginLeft: 10 }}>(quán này chưa có menu trên Google Maps)</span>}
      </div>
    </div>
  )
}

export default function Recommend() {
  const [mood, setMood] = useState('happy')
  const [maxDistance, setMaxDistance] = useState(10)
  const [recs, setRecs] = useState(null)
  const [dishes, setDishes] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchRecommend = async () => {
    setLoading(true)
    try {
      const body = JSON.stringify({ mood, max_distance_km: maxDistance })
      const headers = { 'Content-Type': 'application/json' }

      const r = await fetch(`${API_BASE}/recommend`, { method: 'POST', headers, body })
      setRecs(await r.json())

      const s = await fetch(`${API_BASE}/suggest-dish`, { method: 'POST', headers, body })
      setDishes(await s.json())
    } catch (err) {
      setRecs({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3>Mood-based Recommendation</h3>
      <div>
        <label>Mood: </label>
        <select value={mood} onChange={e => setMood(e.target.value)}>
          {MOODS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>

        <label style={{ marginLeft: 12 }}>Bán kính: </label>
        <select value={maxDistance} onChange={e => setMaxDistance(Number(e.target.value))}>
          {[2, 5, 10, 20].map(km => <option key={km} value={km}>{km} km</option>)}
        </select>

        <button style={{ marginLeft: 8 }} onClick={fetchRecommend} disabled={loading}>
          Get Recommendations
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {recs?.error && <p style={{ color: 'crimson' }}>{recs.error}</p>}

      {recs?.recommendations && (
        <div>
          <h4>Restaurants</h4>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {recs.recommendations.map((r, i) => (
              <li key={r.placeId || i} style={{ marginBottom: 14, paddingBottom: 10, borderBottom: '1px solid #eee' }}>
                <strong>{r.name}</strong>
                <span style={{ fontSize: 12, color: '#666' }}> · {r.category}</span>
                <div style={{ fontSize: 12, color: '#444' }}>{r.address}</div>
                <div style={{ fontSize: 12, color: '#444', marginTop: 2 }}>
                  {r.distance_km != null && <span>{r.distance_km} km</span>}
                  {/* null = CHƯA CÓ dữ liệu, khác hẳn với 0 - không hiện "0đ" hay "0 sao". */}
                  {r.price && <span> · {r.price}</span>}
                  {r.rating != null && <span> · {r.rating}★{r.reviews_count != null && ` (${r.reviews_count})`}</span>}
                </div>
                {r.placeId && <RestaurantDetails placeId={r.placeId} />}
              </li>
            ))}
          </ul>
        </div>
      )}

      {dishes?.suggested_dishes && (
        <div>
          <h4>Suggested Dishes</h4>
          <ol>
            {dishes.suggested_dishes.map((d, i) => (
              <li key={i} style={{ marginBottom: 8 }}>
                {/* API trả về dish_name; trước đây UI đọc d.dish nên tên món luôn trống. */}
                <strong>{d.dish_name}</strong>
                <span style={{ fontSize: 12, color: '#666' }}> {d.cuisine} · {d.dish_confidence}</span>
                <div style={{ marginTop: 6 }}>
                  <em style={{ fontSize: 12 }}>Quán bán món này:</em>
                  <ul>
                    {(d.restaurants || []).slice(0, 5).map((r, j) => (
                      <li key={j} style={{ fontSize: 13 }}>
                        {r.name} <span style={{ color: '#666', fontSize: 12 }}>— {r.address || ''}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
