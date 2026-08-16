/**
 * Định danh phiên - đặc tả API mục 1.3.
 *
 * Client tự sinh UUID v4 và lưu ở localStorage. KHÔNG có tài khoản người dùng
 * (SRS mục 8, Won't-have). session_id chỉ dùng để nhóm các tương tác của cùng một
 * phiên duyệt, phục vụ huấn luyện mô hình xếp hạng sau này.
 */
const STORAGE_KEY = 'moodbite.session_id'

function uuidV4() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  // Dự phòng cho trình duyệt cũ / ngữ cảnh không bảo mật (http).
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export function getSessionId() {
  try {
    let id = localStorage.getItem(STORAGE_KEY)
    if (!id) {
      id = uuidV4()
      localStorage.setItem(STORAGE_KEY, id)
    }
    return id
  } catch {
    // localStorage bị chặn (chế độ riêng tư) -> vẫn phải tìm kiếm được,
    // chỉ là tương tác không nhóm được theo phiên.
    return uuidV4()
  }
}
