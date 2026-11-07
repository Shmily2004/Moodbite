/**
 * Public API của `shared/test` — dữ liệu mẫu dùng chung cho test.
 *
 * Có barrel này vì luật FSD (steiger) cấm import thẳng vào file bên trong một slice:
 * mọi thứ phải đi qua cửa trước. Nhờ vậy đổi cấu trúc bên trong `shared/test/` không
 * làm gãy file test nào.
 *
 * `setup.ts` CỐ Ý không xuất ở đây: nó do vitest nạp qua `setupFiles`, không phải thứ
 * code khác import.
 */
export { mocChatLuong, mocVanDe } from './moc-chat-luong';
