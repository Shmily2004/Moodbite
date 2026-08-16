import React, { useState, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api'

export default function UploadFloorplan(){
  // Photo→3D feature is paused by architecture decision.
  // Do not call `/api/predict-floorplan` from the demo UI unless user re-enables it.
  const [file, setFile] = useState(null)
  const [imageSrc, setImageSrc] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(false)
  const imgRef = useRef(null)
  const canvasRef = useRef(null)

  const onSubmit = async (e)=>{
    e.preventDefault()
    if(!file) return
    setLoading(true)
    setPredictions([])

    // Show image locally
    const src = URL.createObjectURL(file)
    setImageSrc(src)

    const fd = new FormData()
    fd.append('file', file)

    try{
      const res = await fetch(`${API_BASE}/predict-floorplan`, { method:'POST', body: fd })
      if(!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      // Expect data.predictions: [{class, confidence, bbox: [x1,y1,x2,y2]}]
      setPredictions(data.predictions || [])
    }catch(err){
      setPredictions([{class:'error', confidence:0, bbox:[], message: err.message}])
    }finally{setLoading(false)}
  }

  const onImageLoad = ()=>{
    // draw predictions on canvas sized to the displayed image
    const img = imgRef.current
    const canvas = canvasRef.current
    if(!img || !canvas) return
    const scaleX = img.clientWidth / img.naturalWidth
    const scaleY = img.clientHeight / img.naturalHeight
    canvas.width = img.clientWidth
    canvas.height = img.clientHeight
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0,0,canvas.width,canvas.height)
    ctx.lineWidth = 2
    predictions.forEach(p=>{
      if(!p.bbox || p.bbox.length<4) return
      const [x1,y1,x2,y2] = p.bbox
      const rx = x1 * scaleX
      const ry = y1 * scaleY
      const rw = (x2 - x1) * scaleX
      const rh = (y2 - y1) * scaleY
      ctx.strokeStyle = 'rgba(255,0,0,0.9)'
      ctx.strokeRect(rx, ry, rw, rh)
      ctx.fillStyle = 'rgba(255,0,0,0.9)'
      ctx.font = '14px Arial'
      const label = `${p.class || 'obj'} ${p.confidence? (p.confidence.toFixed? (p.confidence*100).toFixed(0) + '%' : p.confidence) : ''}`
      ctx.fillText(label, rx+4, ry+14)
    })
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

      {imageSrc && (
        <div style={{position:'relative', display:'inline-block', marginTop:12}}>
          <img ref={imgRef} src={imageSrc} alt="floorplan" onLoad={onImageLoad} style={{maxWidth:'640px',height:'auto',display:'block'}} />
          <canvas ref={canvasRef} style={{position:'absolute', left:0, top:0, pointerEvents:'none'}} />
        </div>
      )}

      {predictions && predictions.length>0 && (
        <div style={{marginTop:12}}>
          <h4>Detections</h4>
          <ul>
            {predictions.map((p, i)=> (
              <li key={i}>{p.class} — {p.confidence ? `${(p.confidence*100).toFixed(0)}%` : ''}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
