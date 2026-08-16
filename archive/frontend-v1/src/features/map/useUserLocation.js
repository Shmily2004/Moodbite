import { useCallback, useState } from 'react'

/**
 * Vị trí người dùng qua Geolocation API của trình duyệt.
 * MIỄN PHÍ, không cần API key, không liên quan tới Google.
 *
 * Đề án mục 5: vị trí lấy trực tiếp từ thiết bị, KHÔNG hỏi người dùng
 * "bán kính 1km/3km" như một câu khảo sát trừu tượng.
 */

// Hồ Hoàn Kiếm - phải khớp HANOI_CENTER trong src/domain/value_objects/location.py.
export const HANOI_CENTER = { lat: 21.0285, lng: 105.8542 }

const ERROR_MESSAGES = {
  1: 'Bạn đã từ chối chia sẻ vị trí. Đang dùng trung tâm Hà Nội.',
  2: 'Không xác định được vị trí. Đang dùng trung tâm Hà Nội.',
  3: 'Quá thời gian chờ định vị. Đang dùng trung tâm Hà Nội.',
}

export default function useUserLocation() {
  const [position, setPosition] = useState(HANOI_CENTER)
  const [isDefault, setIsDefault] = useState(true)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setError('Trình duyệt không hỗ trợ định vị.')
      return
    }
    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setPosition({ lat: coords.latitude, lng: coords.longitude })
        setIsDefault(false)
        setError(null)
        setLoading(false)
      },
      (err) => {
        // Bị từ chối KHÔNG phải lỗi chặn đường: vẫn còn vị trí mặc định để tìm kiếm.
        setError(ERROR_MESSAGES[err.code] || 'Không lấy được vị trí.')
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    )
  }, [])

  return { position, isDefault, error, loading, request }
}
