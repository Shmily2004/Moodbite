/**
 * Component / tiện ích dùng chung giữa `apps/client` và `apps/admin`.
 *
 * Chỉ đưa component vào đây khi nó thực sự được DÙNG Ở HAI NƠI. Component chỉ client dùng
 * thì để trong `apps/client/src/shared/ui/`.
 *
 * App KHÔNG import thẳng package này từ feature/widget: đi qua `shared/ui` của app để
 * giữ đúng luật import FSD.
 */

export { safeHttpUrl, safeInternalPath } from './safeUrl';
export { ConfirmDialog } from './ConfirmDialog';
export type { ConfirmDialogProps } from './ConfirmDialog';
