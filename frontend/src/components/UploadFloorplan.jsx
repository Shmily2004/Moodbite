import React, { useState } from 'react'

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8001/api'

export default function UploadFloorplan(){
  // Photo→3D feature is paused by architecture decision.
  // Do not call `/api/predict-floorplan` from the demo UI unless user re-enables it.
  return (
    <div className="card">
      <h3>Upload Floorplan (Temporarily Paused)</h3>
      <p>
        The Photo→3D / floorplan detection UI is currently paused per project
        architecture decisions. This demo intentionally does not upload images
        or call the backend endpoint. If you need to re-enable this feature,
        update the frontend after confirming with the project owner.
      </p>
    </div>
  )
}
