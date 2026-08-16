/**
 * VIEWMODEL của tính năng tìm kiếm (vai trò "Controller" trong MVC cổ điển).
 *
 * Giữ state, gọi API, xử lý lỗi. KHÔNG chứa JSX. KHÔNG chứa quy tắc nghiệp vụ -
 * xếp hạng/chấm điểm nằm ở backend (CLAUDE.md mục 1b).
 *
 * Hai lỗi của bản JavaScript cũ được sửa ở đây:
 *   1. Gọi 2 API tuần tự -> nay backend gộp còn 1 lượt /search, món nằm sẵn trong kết quả.
 *   2. Không huỷ request cũ -> bấm nhanh 2 lần thì kết quả cũ về sau ghi đè kết quả mới.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { SearchResponseData, SearchResultItem } from '@moodbite/api-client';
import { ApiError, api } from '@/shared/api';
import { DEFAULT_RADIUS_KM, DEFAULT_SEARCH_LIMIT } from '@/shared/config';
import { getSessionId } from '@/shared/lib';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface UseSearchOptions {
  position: Coordinates;
}

export interface SearchRunOptions {
  mood?: string;
  district?: string;
  openNow?: boolean;
}

export interface UseSearchResult {
  queryText: string;
  setQueryText: (value: string) => void;
  maxDistanceKm: number | null;
  setMaxDistanceKm: (value: number | null) => void;
  results: SearchResultItem[] | null;
  context: string[];
  warnings: string[];
  searchQueryId: string | null;
  loading: boolean;
  error: string | null;
  run: (options?: SearchRunOptions) => Promise<void>;
}

export function useSearch({ position }: UseSearchOptions): UseSearchResult {
  const [queryText, setQueryText] = useState('');
  const [maxDistanceKm, setMaxDistanceKm] = useState<number | null>(DEFAULT_RADIUS_KM);
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [context, setContext] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [searchQueryId, setSearchQueryId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  // Huỷ request đang bay khi component bị gỡ, tránh setState trên component đã chết.
  useEffect(() => () => abortRef.current?.abort(), []);

  const run = useCallback(
    async (options: SearchRunOptions = {}) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);

      try {
        const data: SearchResponseData = await api.search(
          {
            session_id: getSessionId(),
            query_text: queryText || null,
            mood: options.mood ?? null,
            district: options.district ?? null,
            opening_hours_constraint: options.openNow ? 'now' : null,
            latitude: position.lat,
            longitude: position.lng,
            max_distance_km: maxDistanceKm,
            dietary_restrictions: [],
            limit: DEFAULT_SEARCH_LIMIT,
          },
          { signal: controller.signal },
        );

        setResults(data.results);
        setContext(data.context ?? []);
        setWarnings(data.warnings ?? []);
        setSearchQueryId(data.search_query_id);
      } catch (err) {
        // Request bị CHÍNH TA huỷ -> không phải lỗi, bỏ qua im lặng.
        if (err instanceof Error && err.name === 'AbortError') return;
        setError(err instanceof ApiError ? err.userMessage : (err as Error).message);
      } finally {
        if (abortRef.current === controller) setLoading(false);
      }
    },
    [queryText, maxDistanceKm, position.lat, position.lng],
  );

  return {
    queryText,
    setQueryText,
    maxDistanceKm,
    setMaxDistanceKm,
    results,
    context,
    warnings,
    searchQueryId,
    loading,
    error,
    run,
  };
}
