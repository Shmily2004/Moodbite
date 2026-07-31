# Spatial JSON Schema v1.0

Tài liệu định nghĩa cấu trúc dữ liệu trao đổi giữa AI Backend và 3D Frontend.

## 1. Cấu trúc tổng quát (SpatialJSON)

```json
{
  "project_id": "string",
  "metadata": {
    "scale_ratio": 0.01,
    "unit": "mm",
    "origin": [0, 0, 0]
  },
  "levels": [
    {
      "level_id": "string",
      "elevation": 0,
      "height": 3000,
      "walls": [],
      "openings": [],
      "objects": [],
      "rooms": []
    }
  ]
}
```

## 2. Chi tiết thực thể

### 2.1. Wall (Tường)
- `id`: string
- `points`: list of [x, y] (tọa độ 2D của tim tường hoặc đa giác bao)
- `thickness`: number (mm)
- `type`: "inner" | "outer" | "partition"

### 2.2. Opening (Cửa)
- `id`: string
- `wall_id`: string (nếu gắn vào tường)
- `type`: "door" | "window"
- `position`: [x, y]
- `size`: [width, height]
- `orientation`: number (degrees)

### 2.3. Object (Đồ đạc)
- `id`: string
- `type`: "bed" | "sofa" | "table" | ... (theo nhãn YOLO)
- `position`: [x, y, z]
- `rotation`: [rx, ry, rz]
- `scale`: [sx, sy, sz]
- `confidence`: number (0-1)

### 2.4. Room (Không gian)
- `id`: string
- `name`: string
- `boundary`: list of [x, y]
- `area`: number (m2)
