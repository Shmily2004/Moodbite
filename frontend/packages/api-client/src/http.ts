/**
 * Lớp gọi HTTP dùng chung cho MỌI app (client và admin).
 *
 * Đây là NƠI DUY NHẤT trong frontend biết:
 *   - envelope `{data}` / `{error}` của backend (đặc tả API mục 1.5)
 *   - cách xử lý huỷ request
 *   - cách dịch mã lỗi sang câu người dùng đọc được
 *
 * Backend đổi quy ước envelope -> chỉ sửa file này.
 */

/** Mã lỗi backend trả về (đặc tả API mục 1.6). */
export type ApiErrorCode =
  | 'INVALID_REQUEST'
  | 'RESTAURANT_NOT_FOUND'
  | 'SEARCH_RESULT_ITEM_NOT_FOUND'
  | 'RATE_LIMITED'
  | 'EXTERNAL_SERVICE_UNAVAILABLE'
  | 'DATA_NOT_READY'
  | 'INTERNAL_ERROR'
  | 'NETWORK';

export class ApiError extends Error {
  constructor(
    readonly code: ApiErrorCode,
    message: string,
    readonly details: Record<string, unknown> = {},
    readonly status = 0,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  /** Câu hiển thị cho người dùng - họ cần biết PHẢI LÀM GÌ, không phải mã lỗi kỹ thuật. */
  get userMessage(): string {
    switch (this.code) {
      case 'DATA_NOT_READY':
        return 'Server chưa nạp xong dữ liệu quán ăn. Hãy thử lại sau.';
      case 'RESTAURANT_NOT_FOUND':
        return 'Không tìm thấy quán này.';
      case 'EXTERNAL_SERVICE_UNAVAILABLE':
        return 'Dịch vụ bên ngoài đang lỗi. Kết quả có thể thiếu thông tin.';
      case 'RATE_LIMITED':
        return 'Bạn thao tác hơi nhanh. Chờ một chút rồi thử lại.';
      case 'NETWORK':
        return 'Không kết nối được tới server. Kiểm tra backend đã chạy chưa.';
      default:
        return this.message || 'Có lỗi xảy ra.';
    }
  }
}

/** Response thành công của backend luôn bọc trong `data`. */
interface SuccessEnvelope<T> {
  data: T;
}

interface ErrorEnvelope {
  error: { code: string; message: string; details?: Record<string, unknown> };
}

export interface HttpClientOptions {
  baseUrl: string;
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  signal?: AbortSignal;
}

export class HttpClient {
  constructor(private readonly options: HttpClientOptions) {}

  /**
   * Gọi API và trả về phần `data` đã bóc vỏ.
   *
   * Ném `ApiError` khi backend trả lỗi. Riêng `AbortError` được ném lại NGUYÊN TRẠNG
   * để tầng gọi phân biệt được "ta chủ động huỷ" với "lỗi thật" - nếu không, mỗi lần
   * người dùng gõ thêm một chữ sẽ hiện một thông báo lỗi giả.
   */
  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, signal } = options;

    let response: Response;
    try {
      response = await fetch(`${this.options.baseUrl}${path}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
        signal,
      });
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') throw err;
      throw new ApiError('NETWORK', (err as Error).message);
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      throw new ApiError(
        'INTERNAL_ERROR',
        'Response không phải JSON hợp lệ.',
        {},
        response.status,
      );
    }

    if (payload && typeof payload === 'object' && 'error' in payload) {
      const { error } = payload as ErrorEnvelope;
      throw new ApiError(
        error.code as ApiErrorCode,
        error.message,
        error.details ?? {},
        response.status,
      );
    }

    if (!response.ok) {
      throw new ApiError('INTERNAL_ERROR', `HTTP ${response.status}`, {}, response.status);
    }

    return (payload as SuccessEnvelope<T>).data;
  }
}
