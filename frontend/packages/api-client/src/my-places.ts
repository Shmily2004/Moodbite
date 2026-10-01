/**
 * "Bộ sưu tập của tôi" + "Địa chỉ của tôi" — `/api/v1/me/collections/*`, `/me/addresses/*`.
 * Chủ dự án duyệt 2026-09-29.
 *
 * VÌ SAO LỚP RIÊNG, KHÔNG THÊM VÀO `MoodbiteAuthApi`: lớp đó đã lo đăng nhập, mật khẩu,
 * email, yêu thích, số liệu. Hai tính năng này tự đứng được; nhét thêm 10 method vào đó
 * thì một file phải biết mọi thứ về tài khoản. Vẫn dùng chung `HttpClient`, nên envelope
 * `{data}`/`{error}` và cách gắn token chỉ có MỘT nơi định nghĩa.
 *
 * Không method nào nhận `user_id`: server lấy từ token. Mã của người khác -> 404.
 */
import type { components } from './schema';
import type { HttpClient, RequestOptions } from './http';
import type { MessageData } from './auth';

export type CollectionData = components['schemas']['CollectionSchema'];
export type CollectionItemData = components['schemas']['CollectionItemSchema'];
export type CollectionsData = components['schemas']['CollectionsData'];
export type AddCollectionItemRequest = components['schemas']['AddCollectionItemRequest'];
export type UserAddressData = components['schemas']['UserAddressSchema'];
export type AddressesData = components['schemas']['AddressesData'];
export type CreateAddressRequest = components['schemas']['CreateAddressRequest'];
export type UpdateAddressRequest = components['schemas']['UpdateAddressRequest'];

export class MoodbiteMyPlacesApi {
  constructor(private readonly http: HttpClient) {}

  // --- Bộ sưu tập -----------------------------------------------------------

  /** Mọi bộ của chính chủ, KÈM mục bên trong. Bộ mới nhất đứng đầu. */
  collections(options?: RequestOptions): Promise<CollectionsData> {
    return this.http.request<CollectionsData>('/me/collections', options);
  }

  /** Tên sai (rỗng / > 60 ký tự) -> 400 kèm câu tiếng Việt; hiện nguyên văn cho người dùng. */
  createCollection(name: string, options?: RequestOptions): Promise<CollectionData> {
    return this.http.request<CollectionData>('/me/collections', {
      ...options,
      method: 'POST',
      body: { name },
    });
  }

  renameCollection(
    collectionId: string,
    name: string,
    options?: RequestOptions,
  ): Promise<CollectionData> {
    return this.http.request<CollectionData>(
      `/me/collections/${encodeURIComponent(collectionId)}`,
      { ...options, method: 'PATCH', body: { name } },
    );
  }

  /** Xoá bộ và mọi mục trong bộ. Mục vẫn còn ở "Yêu thích"/"Đã lưu" nếu có. */
  deleteCollection(collectionId: string, options?: RequestOptions): Promise<MessageData> {
    return this.http.request<MessageData>(
      `/me/collections/${encodeURIComponent(collectionId)}`,
      { ...options, method: 'DELETE' },
    );
  }

  /** Idempotent: thêm lại thứ đã có chỉ cập nhật tên. Trả CẢ BỘ sau khi thêm. */
  addCollectionItem(
    collectionId: string,
    body: AddCollectionItemRequest,
    options?: RequestOptions,
  ): Promise<CollectionData> {
    return this.http.request<CollectionData>(
      `/me/collections/${encodeURIComponent(collectionId)}/items`,
      { ...options, method: 'POST', body },
    );
  }

  removeCollectionItem(
    collectionId: string,
    itemType: 'restaurant' | 'dish',
    itemId: string,
    options?: RequestOptions,
  ): Promise<MessageData> {
    return this.http.request<MessageData>(
      `/me/collections/${encodeURIComponent(collectionId)}/items/${itemType}/${encodeURIComponent(itemId)}`,
      { ...options, method: 'DELETE' },
    );
  }

  // --- Địa chỉ --------------------------------------------------------------

  /** Địa chỉ MẶC ĐỊNH (nếu có) đứng đầu. */
  addresses(options?: RequestOptions): Promise<AddressesData> {
    return this.http.request<AddressesData>('/me/addresses', options);
  }

  /** Toạ độ ngoài Hà Nội -> 400 kèm lý do. Không có geocoding: toạ độ do client gửi. */
  createAddress(body: CreateAddressRequest, options?: RequestOptions): Promise<UserAddressData> {
    return this.http.request<UserAddressData>('/me/addresses', {
      ...options,
      method: 'POST',
      body,
    });
  }

  /** Chỉ gửi trường muốn đổi. `address_text: null` = XOÁ mô tả; không gửi = giữ nguyên. */
  updateAddress(
    addressId: string,
    body: UpdateAddressRequest,
    options?: RequestOptions,
  ): Promise<UserAddressData> {
    return this.http.request<UserAddressData>(
      `/me/addresses/${encodeURIComponent(addressId)}`,
      { ...options, method: 'PATCH', body },
    );
  }

  deleteAddress(addressId: string, options?: RequestOptions): Promise<MessageData> {
    return this.http.request<MessageData>(
      `/me/addresses/${encodeURIComponent(addressId)}`,
      { ...options, method: 'DELETE' },
    );
  }
}
