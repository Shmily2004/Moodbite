export interface Restaurant {
  id: string;
  name: string;
  address?: string | null;
  latitude: number;
  longitude: number;
  opening_hours?: Record<string, unknown> | null;
  price_range?: number | null;
  rating?: number | null;
  user_ratings_total?: number | null;
  description_embedding?: number[] | null;
  is_active: boolean;
  deleted_at?: string | null;
  experience_cluster_id?: number | null;
  source: string;
  external_place_id?: string | null;
  updated_by: 'crawler' | 'batch_pipeline' | 'manual';
  created_at: string;
  updated_at: string;
}
