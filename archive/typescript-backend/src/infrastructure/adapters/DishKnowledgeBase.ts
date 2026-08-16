import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Đọc và match data_pipeline/dish_knowledge_base.json — nguồn tri thức món ăn DÙNG CHUNG
 * với tầng Python (data_pipeline/dish_knowledge.py). Sửa nội dung món ăn thì sửa ở file
 * JSON đó, KHÔNG hardcode lại danh sách món ở đây hay bên Python, để 2 tầng không lệch nhau.
 */

export type KnowledgeDish = {
  name: string;
  cuisine?: string | null;
  spice_level?: number | null;
  temperature?: "hot" | "cold" | "neutral" | null;
  portion_size?: "light" | "regular" | "heavy" | null;
  mood_keywords: string[];
};

export type KnowledgeRule = {
  id: string;
  match_category: string[];
  match_cuisine: string[];
  confidence: "specific" | "generic_fallback";
  dishes: KnowledgeDish[];
};

type KnowledgeBase = {
  rules: KnowledgeRule[];
  unmatched_fallback: { confidence: "unknown"; note: string };
};

const DEFAULT_KB_PATH = "data_pipeline/dish_knowledge_base.json";

let cachedKb: KnowledgeBase | null = null;

export function loadKnowledgeBase(path: string = DEFAULT_KB_PATH): KnowledgeBase {
  if (cachedKb) return cachedKb;
  const absolutePath = resolve(process.cwd(), path);
  const content = readFileSync(absolutePath, "utf-8");
  cachedKb = JSON.parse(content) as KnowledgeBase;
  return cachedKb;
}

/**
 * Trả về rule đầu tiên khớp categoryName. Thứ tự rule trong JSON quyết định độ ưu tiên -
 * rule cụ thể (VD "phở") phải đứng trước rule chung chung (VD "nhà hàng") trong file JSON,
 * nếu không rule chung sẽ nuốt mất trước khi rule cụ thể có cơ hội khớp.
 */
export function matchRuleForCategory(
  categoryName: string | null | undefined,
  kb: KnowledgeBase = loadKnowledgeBase()
): KnowledgeRule | null {
  if (!categoryName) return null;
  const normalized = categoryName.trim().toLowerCase();
  for (const rule of kb.rules) {
    for (const keyword of rule.match_category) {
      if (normalized.includes(keyword.toLowerCase())) {
        return rule;
      }
    }
  }
  return null;
}

/**
 * Trả về (danh sách món, confidence) cho 1 categoryName. Khi không khớp rule nào, trả về
 * 1 món giả tên = categoryName gốc với confidence "unknown" - giữ hành vi cũ (không loại
 * quán khỏi kết quả) nhưng tầng gọi có thể tự hiển thị khác đi khi thấy confidence này.
 */
export function dishesForCategory(
  categoryName: string | null | undefined,
  kb: KnowledgeBase = loadKnowledgeBase()
): { dishes: KnowledgeDish[]; confidence: "specific" | "generic_fallback" | "unknown" } {
  const rule = matchRuleForCategory(categoryName, kb);
  if (rule) {
    return { dishes: rule.dishes, confidence: rule.confidence };
  }
  const fallbackName = categoryName && categoryName.trim() ? categoryName : "Món ăn";
  return {
    dishes: [{ name: fallbackName, cuisine: null, spice_level: null, temperature: null, portion_size: null, mood_keywords: [] }],
    confidence: kb.unmatched_fallback.confidence,
  };
}
