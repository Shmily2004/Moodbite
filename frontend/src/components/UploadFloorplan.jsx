import React, { useState } from 'react'

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8001/api'

export default function UploadFloorplan(){
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e)=>{
    e.preventDefault()
    if(!file) return
    setLoading(true)
    const fd = new FormData()
    fd.append('file', file)
    try{
      const res = await fetch(`${API_BASE}/predict-floorplan`, { method:'POST', body: fd })
      const data = await res.json()
      setResult(data)
    }catch(err){
      setResult({error:err.message})
    }finally{setLoading(false)}
  }

  return (
    <div className="card">
      <h3>Upload Floorplan</h3>
      <form onSubmit={onSubmit}>
        <input type="file" accept="image/*" onChange={e=>setFile(e.target.files[0])} />
        <div style={{marginTop:8}}>
          <button type="submit">Upload & Predict</button>
        </div>
      </form>

      {loading && <p>Processing...</p>}
      {result && (
        <pre style={{whiteSpace:'pre-wrap',wordBreak:'break-word'}}>{JSON.stringify(result,null,2)}</pre>
      )}
    </div>
  )
}
