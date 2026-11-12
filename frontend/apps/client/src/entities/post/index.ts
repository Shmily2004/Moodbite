/**
 * Thực thể BÀI VIẾT (cẩm nang + tin cập nhật) ở phía khách — UC14 trong `docs/bieu_do_uml`.
 * Chỉ đọc: khách không tạo/sửa bài. Quản lý bài nằm ở khu quản trị.
 */
export { useNewsList } from './model/useNewsList';
export { useNewsArticle } from './model/useNewsArticle';
export { NewsList, dinhDangNgay } from './ui/NewsList';
export { NewsArticleView } from './ui/NewsArticleView';
