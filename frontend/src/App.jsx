import React, { useState } from 'react'
import UploadFloorplan from './components/UploadFloorplan'
import Recommend from './components/Recommend'

export default function App(){
  const [route, setRoute] = useState('home')
  return (
    <div style={{fontFamily:'Arial, sans-serif', padding:20}}>
      <header>
        <h1>MoodBite — Demo UI</h1>
        <nav style={{marginBottom:20}}>
          <button onClick={()=>setRoute('home')}>Home</button>
          <button onClick={()=>setRoute('upload')}>Upload Floorplan</button>
          <button onClick={()=>setRoute('recommend')}>Recommend</button>
        </nav>
      </header>

      <main>
        {route === 'home' && (
          <div>
            <p>Quick demo UI to interact with the MoodBite API.</p>
            <p>Backend API base: <code>http://localhost:8001/api</code></p>
          </div>
        )}
        {route === 'upload' && <UploadFloorplan />}
        {route === 'recommend' && <Recommend />}
      </main>
    </div>
  )
}
