/**
 * Component dùng chung giữa `apps/client` và `apps/admin` (admin chưa dựng).
 *
 * File này CỐ Ý còn rỗng. Nó phải tồn tại vì `@moodbite/ui` đã được khai làm
 * dependency của `apps/client` và được alias trong `vite.config.ts` +
 * `tsconfig.json`; thiếu file thì lần đầu có ai đó `import ... from '@moodbite/ui'`
 * sẽ vỡ ngay lúc resolve, chứ không phải lỗi rõ ràng.
 *
 * Chỉ đưa component vào đây khi nó thực sự được DÙNG Ở HAI NƠI. Component chỉ
 * client dùng thì để trong `apps/client/src/shared/ui/`.
 */

export {};
