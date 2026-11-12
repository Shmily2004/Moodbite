/**
 * Kiểu dữ liệu BÀI VIẾT (cẩm nang + tin cập nhật) — dùng chung cho app khách và app quản trị.
 *
 * VÌ SAO KHAI TAY, KHÔNG LẤY TỪ `schema.d.ts`: `PostListData` / `PostDetailData` phía
 * backend khai `posts: list` và `post: dict` (không có kiểu từng trường), nên sinh ra chỉ
 * còn `unknown[]`. Trường ở đây phải khớp `PostOrigin`/`PostStatus` + `Post.to_public()`
 * trong `src/domain/entities/post.py`. Đổi một trường bên đó thì sửa tại đây.
 */
export type PostStatus = 'draft' | 'published';
export type PostOrigin = 'admin' | 'web_sample';

export interface PostPublic {
  post_id: string;
  slug: string;
  title: string;
  summary: string;
  body: string;
  status: PostStatus;
  origin: PostOrigin;
  source_name: string | null;
  source_url: string | null;
  /** `YYYY-MM-DD` hoặc null. */
  last_updated: string | null;
  /** `/anh/...` (ảnh trong dự án) hoặc `https://...` (ảnh từ mạng). Null = không có ảnh. */
  image_url: string | null;
  image_credit: string | null;
  published_at: string | null;
  updated_at: string | null;
}

export interface PostListData {
  posts: PostPublic[];
  total: number;
}

export interface PostDetailData {
  post: PostPublic;
}

/** Thân khi tạo/sửa bài (admin). Khớp `PostWriteRequest` ở `schemas_posts.py`. */
export interface PostWriteRequest {
  title: string;
  summary: string;
  body: string;
  status: PostStatus;
  source_name?: string | null;
  source_url?: string | null;
  last_updated?: string | null;
  image_url?: string | null;
  image_credit?: string | null;
}
