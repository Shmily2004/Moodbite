import { useCallback, useEffect, useRef, useState } from 'react'
import { search as searchApi } from '../../services/moodbiteApi'

/**
 * State + điều phối cho luồng tìm kiếm.
 *
 * Hai lỗi của bản cũ được sửa ở đây:
 *  1. Gọi 2 API tuần tự (/recommend rồi /suggest-dish) -> nay backend gộp thành 1 lượt
 *     /search, món đã nằm sẵn trong từng kết quả.
 *  2. Không huỷ request cũ -> bấm nhanh 2 lần thì kết quả cũ về sau ghi đè kết quả mới.
 *     Nay dùng AbortController.
 */
export default function useSearch({ position }) {
  const [queryText, setQueryText] = useState('')
  const [maxDistanceKm, setMaxDistanceKm] = useState(10)
  const [results, setResults] = useState(null)
  const [context, setContext] = useState([])
  const [warnings, setWarnings] = useState([])
  const [searchQueryId, setSearchQueryId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const abortRef = useRef(null)

  // Huỷ request đang bay khi component bị gỡ, tránh setState trên component đã chết.
  useEffect(() => () => abortRef.current?.abort(), [])

  const run = useCallback(
    async ({ mood } = {}) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      setLoading(true)
      setError(null)
      try {
        const data = await searchApi(
          {
            queryText,
            mood,
            latitude: position.lat,
            longitude: position.lng,
            maxDistanceKm,
            limit: 10,
          },
          controller.signal,
        )
        setResults(data.results)
        setContext(data.context)
        setWarnings(data.warnings)
        setSearchQueryId(data.searchQueryId)
      } catch (err) {
        // Request bị chính ta huỷ -> không phải lỗi, bỏ qua im lặng.
        if (err.name === 'AbortError') return
        setError(err.userMessage || err.message)
      } finally {
        if (abortRef.current === controller) setLoading(false)
      }
    },
    [queryText, maxDistanceKm, position.lat, position.lng],
  )

  return {
    queryText, setQueryText,
    maxDistanceKm, setMaxDistanceKm,
    results, context, warnings, searchQueryId,
    loading, error,
    run,
  }
}
