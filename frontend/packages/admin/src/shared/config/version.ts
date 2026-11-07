/**
 * Phiên bản khu quản trị, đọc từ `packages/admin/package.json` lúc build.
 *
 * Đọc từ package.json thay vì gõ tay chuỗi "1.0.0" vào khung: gõ tay là nói sai ngay từ
 * đầu, và sẽ sai tiếp mỗi lần tăng phiên bản mà quên sửa khung.
 */
import pkg from '../../../package.json';

export const APP_VERSION: string = pkg.version;
