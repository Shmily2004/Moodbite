// Tách từ QualityPage.tsx ngày 2026-10-06 (file vượt ~300 dòng, CLAUDE.md mục 6).
// Giữ riêng trong slice trang này — không gộp với bản ở trang khác (FSD cấm import chéo giữa các page).

export function soVN(n: number): string {
  return n.toLocaleString('vi-VN');
}
