/**
 * Lớp gọi HTTP dùng chung. Đây là NƠI DUY NHẤT biết về envelope của API.
 *
 * Backend bọc mọi response trong {data} hoặc {error} (đặc tả API mục 1.5). Bóc lớp đó ở
 * đây để phần còn lại của giao diện chỉ làm việc với dữ liệu thuần, và khi backend đổi
 * quy ước envelope thì chỉ phải sửa đúng một file.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api/v1'

/** Lỗi có mã, để giao diện phản ứng khác nhau theo từng loại. */
export class ApiError extends Error {
  constructor(code, message, details, status) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
    this.status = status
  }

  /** Người dùng cần biết phải làm gì, không phải mã lỗi kỹ thuật. */
  get userMessage() {
    switch (this.code) {
      case 'DATA_NOT_READY':
        return 'Server chưa nạp xong dữ liệu quán ăn. Hãy thử lại sau.'
      case 'RESTAURANT_NOT_FOUND':
        return 'Không tìm thấy quán này.'
      case 'EXTERNAL_SERVICE_UNAVAILABLE':
        return 'Dịch vụ bên ngoài đang lỗi. Kết quả có thể thiếu thông tin.'
      case 'NETWORK':
        return 'Không kết nối được tới server. Kiểm tra backend đã chạy chưa.'
      default:
        return this.message || 'Có lỗi xảy ra.'
    }
  }
}

/**
 * @param {string} path   đường dẫn tương đối, VD '/search'
 * @param {object} options  { method, body, signal }
 */
export async function request(path, { method = 'GET', body, signal } = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    })
  } catch (err) {
    // AbortError là do CHÍNH TA huỷ request cũ, không phải lỗi -> ném lại nguyên trạng
    // để tầng gọi bỏ qua, tránh hiện thông báo lỗi giả cho người dùng.
    if (err.name === 'AbortError') throw err
    throw new ApiError('NETWORK', err.message, {}, 0)
  }

  let payload = null
  try {
    payload = await response.json()
  } catch {
    throw new ApiError('INTERNAL_ERROR', 'Response không phải JSON hợp lệ.', {}, response.status)
  }

  if (payload && payload.error) {
    const { code, message, details } = payload.error
    throw new ApiError(code, message, details, response.status)
  }
  if (!response.ok) {
    throw new ApiError('INTERNAL_ERROR', `HTTP ${response.status}`, {}, response.status)
  }
  return payload?.data ?? null
}
