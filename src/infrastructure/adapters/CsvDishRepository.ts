import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse } from "csv-parse/sync";
import type { Dish } from "../../domain/entities/Dish";
import type { IDishRepository } from "../../application/ports/IDishRepository";

const DEFAULT_CSV_PATH = "data_pipeline/data_cleaned/dataset_moodbite_features.csv";

const MOOD_SCORE_COLUMNS: Array<{ column: string; keyword: string }> = [
  { column: "comfort_cozy_score", keyword: "comfort" },
  { column: "spicy_hot_score", keyword: "spicy" },
  { column: "fresh_healthy_score", keyword: "fresh" },
  { column: "cheap_budget_score", keyword: "cheap" },
  { column: "quick_fast_score", keyword: "quick" },
];

type CsvRow = {
  title: string;
  placeId: string;
  categoryName: string;
  [key: string]: string;
};

/**
 * QUAN TRỌNG - ĐỌC TRƯỚC KHI DÙNG:
 * Adapter này tạo ra "món ăn đại diện" (synthetic dish) cho mỗi quán, suy luận từ
 * categoryName (VD: "Nhà hàng phở" -> món "Phở") + mood score đã tính sẵn.
 * ĐÂY KHÔNG PHẢI DỮ LIỆU MÓN ĂN THẬT — vì nguồn dữ liệu cào được (Google Maps/OSM)
 * chỉ cung cấp thông tin CẤP QUÁN (tên, loại hình, địa chỉ, rating), không có thực đơn/menu
 * chi tiết từng món. Đây là giải pháp tạm cho MVP để luồng "đề xuất món -> quán" có dữ liệu
 * thật để chạy, KHÔNG nên coi là nguồn dữ liệu món ăn chính thức lâu dài.
 *
 * Khi dự án có dữ liệu menu thật (vd cào thêm ảnh/text menu, hoặc nhập tay các món phổ biến
 * theo từng quán), nên thay adapter này bằng 1 nguồn dữ liệu dish-level thật sự.
 */
export class CsvDishRepository implements IDishRepository {
  private readonly dishes: Dish[];

  constructor(csvPath: string = DEFAULT_CSV_PATH) {
    const absolutePath = resolve(process.cwd(), csvPath);
    let content: string;
    try {
      content = readFileSync(absolutePath, "utf-8");
    } catch (error) {
      throw new Error(
        `Không đọc được file dữ liệu tại ${absolutePath}. ` +
          `Hãy chạy pipeline Python trước: python -m data_pipeline.merge_and_prepare_raw && ` +
          `python -m data_pipeline.data_cleaning && python -m data_pipeline.feature_engineering. ` +
          `Lỗi gốc: ${error instanceof Error ? error.message : String(error)}`
      );
    }

    const rows: CsvRow[] = parse(content, {
      columns: true,
      skip_empty_lines: true,
      bom: true,
    });

    const nowIso = new Date().toISOString();

    this.dishes = rows
      .map((row): Dish | null => {
        if (!row.placeId) {
          return null;
        }

        const moodKeywords = MOOD_SCORE_COLUMNS.filter(({ column }) => {
          const value = Number(row[column]);
          return !Number.isNaN(value) && value > 0;
        })
          .sort((a, b) => Number(row[b.column]) - Number(row[a.column]))
          .slice(0, 2)
          .map(({ keyword }) => keyword);

        return {
          id: `dish-${row.placeId}`,
          restaurant_id: row.placeId,
          name: row.categoryName || row.title,
          category: row.categoryName || null,
          spice_level: null,
          temperature: null,
          portion_size: null,
          mood_keywords: moodKeywords.length > 0 ? moodKeywords : null,
          price: null,
          is_active: true,
          updated_by: "batch_pipeline",
          created_at: nowIso,
          updated_at: nowIso,
        };
      })
      .filter((d): d is Dish => d !== null);
  }

  async save(dish: Dish): Promise<Dish> {
    const existingIndex = this.dishes.findIndex((item) => item.id === dish.id);
    if (existingIndex >= 0) {
      this.dishes[existingIndex] = dish;
      return dish;
    }
    this.dishes.push(dish);
    return dish;
  }

  async findById(id: string): Promise<Dish | null> {
    return this.dishes.find((dish) => dish.id === id) ?? null;
  }

  async findAll(): Promise<Dish[]> {
    return this.dishes.filter((dish) => dish.is_active);
  }

  async findActive(): Promise<Dish[]> {
    return this.findAll();
  }

  async findByRestaurantId(restaurantId: string): Promise<Dish[]> {
    return this.dishes.filter((dish) => dish.restaurant_id === restaurantId && dish.is_active);
  }

  async findByCategory(category: string): Promise<Dish[]> {
    return this.dishes.filter(
      (dish) => dish.category?.toLowerCase() === category.toLowerCase() && dish.is_active
    );
  }

  async findByMoodKeywords(keywords: string[]): Promise<Dish[]> {
    const normalizedKeywords = keywords.map((keyword) => keyword.toLowerCase());
    return this.dishes.filter((dish) => {
      const dishKeywords = (dish.mood_keywords ?? []).map((keyword) => keyword.toLowerCase());
      return normalizedKeywords.some((keyword) => dishKeywords.includes(keyword)) && dish.is_active;
    });
  }

  async findByPriceRange(minPrice: number, maxPrice: number): Promise<Dish[]> {
    return this.dishes.filter((dish) => {
      const price = dish.price ?? Number.POSITIVE_INFINITY;
      return dish.is_active && price >= minPrice && price <= maxPrice;
    });
  }

  async findBySpiceAndTemperature(spiceLevel: number, temperature: Dish["temperature"]): Promise<Dish[]> {
    return this.dishes.filter(
      (dish) => dish.is_active && dish.spice_level === spiceLevel && dish.temperature === temperature
    );
  }

  async searchByNameOrCategory(query: string): Promise<Dish[]> {
    const normalizedQuery = query.toLowerCase();
    return this.dishes.filter((dish) => {
      const haystack = `${dish.name} ${dish.category ?? ""}`.toLowerCase();
      return dish.is_active && haystack.includes(normalizedQuery);
    });
  }

  async delete(id: string): Promise<void> {
    const index = this.dishes.findIndex((dish) => dish.id === id);
    if (index >= 0) {
      this.dishes.splice(index, 1);
    }
  }

  async softDelete(id: string): Promise<void> {
    const dish = this.dishes.find((item) => item.id === id);
    if (dish) {
      dish.is_active = false;
    }
  }
}
