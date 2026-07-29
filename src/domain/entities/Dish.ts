export interface Dish {
  id: string;
  restaurant_id: string;
  name: string;
  category?: string | null;
  spice_level?: number | null;
  temperature?: 'hot' | 'cold' | 'neutral' | null;
  portion_size?: 'light' | 'regular' | 'heavy' | null;
  mood_keywords?: string[] | null;
  price?: number | null;
  is_active: boolean;
  deleted_at?: string | null;
  updated_by: 'crawler' | 'batch_pipeline' | 'manual';
  created_at: string;
  updated_at: string;
}
