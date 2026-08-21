/**
 * Ô chọn ngôn ngữ ở góc phải thanh trên.
 *
 * ⚠️ HIỆN CHỈ CÓ ĐÚNG MỘT NGÔN NGỮ — và ô này nói thật điều đó thay vì giả vờ có nhiều.
 * Toàn bộ chữ trong app đang viết thẳng bằng tiếng Việt trong JSX; làm đa ngôn ngữ thật
 * là một việc RIÊNG (tách chuỗi ra file dịch, thêm thư viện i18n, dịch lại toàn bộ) —
 * phải chốt với chủ dự án trước, không tự làm kèm.
 *
 * Khi nào làm: thêm option ở đây + nối vào thư viện i18n. Chỗ đặt ô này không đổi.
 */
export function LanguageSelect({ className }: { className?: string }) {
  return (
    <select
      className={['lang-select', className].filter(Boolean).join(' ')}
      value="vi"
      // Chỉ một lựa chọn nên không có gì để đổi. Vẫn phải khai `onChange` vì React coi
      // `value` không kèm `onChange` là ô chỉ-đọc và sẽ cảnh báo trong console.
      onChange={() => undefined}
      aria-label="Ngôn ngữ hiển thị"
      title="Hiện chỉ có tiếng Việt"
    >
      <option value="vi">VI</option>
    </select>
  );
}
