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
          <pre>{JSON.stringify(recs, null, 2)}</pre>
        </div>
      )}

      {dishes && (
        <div>
          <h4>Suggested Dishes</h4>
          <pre>{JSON.stringify(dishes, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
