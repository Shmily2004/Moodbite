import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse } from "csv-parse/sync";
import type { Dish } from "../../domain/entities/Dish";
import type { IDishRepository } from "../../application/ports/IDishRepository";
import { dishesForCategory } from "./DishKnowledgeBase";

const DEFAULT_CSV_PATH = "data_pipeline/data_cleaned/dataset_moodbite_features.csv";

type CsvRow = {
  title: string;
  placeId: string;
  categoryName: string;
  [key: string]: string;
};

/**
 * QUAN TRỌNG - ĐỌC TRƯỚC KHI DÙNG:
 * Adapter này suy luận món ăn THẬT (VD "Phở bò", "Lẩu Thái") cho mỗi quán, dựa trên
 * categoryName khớp với data_pipeline/dish_knowledge_base.json (nguồn tri thức món ăn
 * DÙNG CHUNG với tầng Python - xem data_pipeline/dish_knowledge.py). Một quán có thể sinh
 * ra NHIỀU Dish (VD "Nhà hàng phở" -> cả "Phở bò" và "Phở gà").
 *
 * VẪN LÀ SUY LUẬN HEURISTIC, KHÔNG PHẢI MENU THẬT — vì nguồn dữ liệu cào được (Google
 * Maps/OSM) chỉ cung cấp thông tin CẤP QUÁN (tên, loại hình, địa chỉ, rating), không có
 * thực đơn chi tiết từng món. Trước đây (phiên bản cũ) món ăn = chính categoryName gốc
 * (VD dish "Nhà hàng gia đình") - không phải tên món thật, chỉ là loại hình quán được gán
 * nhãn lại. Bản này thay bằng tên món thật suy luận qua knowledge base, độ tin cậy khác
 * nhau tuỳ rule (xem confidence "specific" | "generic_fallback" | "unknown" trong knowledge
 * base) - CHƯA lộ field confidence này ra Dish entity (xem TODO bên dưới).
 *
 * TODO: khi dự án có dữ liệu menu thật cho từng quán cụ thể, nên ưu tiên món thật đó thay
 * vì suy luận ở đây. Cũng nên cân nhắc thêm field `confidence`/`source` vào Dish entity để
 * tầng UI phân biệt được "món suy luận cụ thể" vs "suy luận chung chung" vs "không suy luận
 * được" (hiện 3 loại confidence này bị bỏ qua sau khi rời khỏi adapter này).
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
      .flatMap((row): Dish[] => {
        if (!row.placeId) {
          return [];
        }

        // Một quán có thể sinh ra NHIỀU món (VD "Nhà hàng phở" -> "Phở bò" + "Phở gà"),
        // khác với bản cũ (1 quán = đúng 1 "dish" giả = categoryName).
        const { dishes } = dishesForCategory(row.categoryName);

        return dishes.map((dish, index) => ({
          id: `dish-${row.placeId}-${index}`,
          restaurant_id: row.placeId,
          name: dish.name,
          category: row.categoryName || null,
          spice_level: dish.spice_level ?? null,
          temperature: dish.temperature ?? null,
          portion_size: dish.portion_size ?? null,
          mood_keywords: dish.mood_keywords.length > 0 ? dish.mood_keywords : null,
          price: null,
          is_active: true,
          updated_by: "batch_pipeline",
          created_at: nowIso,
          updated_at: nowIso,
        }));
      });
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
