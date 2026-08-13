import React, { useState } from 'react'
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8001/api'

export default function Recommend(){
  const [mood, setMood] = useState('happy')
  const [recs, setRecs] = useState(null)
  const [dishes, setDishes] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchRecommend = async ()=>{
    setLoading(true)
    try{
      const r = await fetch(`${API_BASE}/recommend`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({mood})
      })
      setRecs(await r.json())

      const s = await fetch(`${API_BASE}/suggest-dish`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({mood})
      })
      setDishes(await s.json())
    }catch(err){
      setRecs({error: err.message})
    }finally{setLoading(false)}
  }

  return (
    <div className="card">
      <h3>Mood-based Recommendation</h3>
      <div>
        <label>Mood: </label>
        <select value={mood} onChange={e=>setMood(e.target.value)}>
          <option value="happy">happy</option>
          <option value="sad">sad</option>
          <option value="excited">excited</option>
          <option value="relaxed">relaxed</option>
        </select>
        <button style={{marginLeft:8}} onClick={fetchRecommend}>Get Recommendations</button>
      </div>

      {loading && <p>Loading...</p>}

      {recs && (
        <div>
          <h4>Restaurants</h4>
          <ul>
            {(recs.recommendations || []).map((r, i)=> (
              <li key={i}>
                <strong>{r.title || r.name || r.placeId}</strong>
                {r.dish_confidence && (<em> — {r.dish_confidence}</em>)}
                <div style={{fontSize:12,color:'#444'}}>{r.address || r.location?.lat + ',' + r.location?.lng}</div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {dishes && (
        <div>
          <h4>Suggested Dishes</h4>
          <ol>
            {(dishes.suggested_dishes || []).map((d, i)=> (
              <li key={i} style={{marginBottom:8}}>
                <strong>{d.dish}</strong> <span style={{fontSize:12,color:'#666'}}>{d.dish_confidence || ''}</span>
                <div style={{marginTop:6}}>
                  <em>Top restaurants for this dish:</em>
                  <ul>
                    {(d.restaurants || []).slice(0,5).map((r,j)=> (
                      <li key={j}>{r.title || r.name || r.placeId} — {r.address || ''}</li>
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
