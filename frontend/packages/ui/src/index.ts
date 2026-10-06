/**
 * Component / tiện ích dùng chung giữa `apps/client` và `apps/admin`.
 *
 * File này CỐ Ý còn rỗng. Nó phải tồn tại vì `@moodbite/ui` đã được khai làm
 * dependency của `apps/client` và được alias trong `vite.config.ts` +
 * `tsconfig.json`; thiếu file thì lần đầu có ai đó `import ... from '@moodbite/ui'`
 * sẽ vỡ ngay lúc resolve, chứ không phải lỗi rõ ràng.
 *
 * Chỉ đưa component vào đây khi nó thực sự được DÙNG Ở HAI NƠI. Component chỉ
 * client dùng thì để trong `apps/client/src/shared/ui/`.
 *
 * App KHÔNG import thẳng package này từ feature/widget: đi qua `shared/lib` của app để
 * giữ đúng luật import FSD.
 */

export { safeHttpUrl, safeInternalPath } from './safeUrl';
