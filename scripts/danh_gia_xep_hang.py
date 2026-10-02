"""Đánh giá xếp hạng OFFLINE trên phiên GIẢ LẬP.

    python scripts/danh_gia_xep_hang.py

Đọc `data_pipeline/data_synthetic/sessions.jsonl` (do `gia_lap_nguoi_dung.py` sinh), mỗi
phiên có TẬP ỨNG VIÊN ~50 quán MoodBite trả về kèm utility "sự thật mặt đất" của người giả
lập. Xếp lại cùng tập đó theo 3 cách rồi so:

    moodbite  thứ tự MoodBite trả về (công thức hiện tại)
    distance  chỉ theo khoảng cách, gần trước
    random    xáo ngẫu nhiên (có seed) — mức sàn

⚠️ ĐỌC KẾT QUẢ CHO ĐÚNG:
  * Đây là DỮ LIỆU GIẢ LẬP. Con số chỉ nói MoodBite hợp với người dùng giả định ra sao,
    KHÔNG nói gì về người dùng thật. Không được ghi vào báo cáo như kết quả thực nghiệm.
  * Hai baseline chỉ XẾP LẠI tập ứng viên MoodBite đã lọc (bán kính, món). Chúng không
    tự tìm ứng viên, nên đây là so sánh THỨ TỰ, không phải so sánh cả hệ thống.
  * Utility cố ý độc lập với công thức MoodBite (xem `scripts/synthetic/persona.py`), nhưng
    cả hai đều coi trọng khoảng cách nên baseline khoảng cách là đối thủ khó — đúng như đời.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.synthetic.an_toan import DEFAULT_OUT_DIR, synthetic_paths  # noqa: E402
from scripts.synthetic.metrics import (  # noqa: E402
    catalog_coverage, mean, ndcg_at_k, precision_at_k, reciprocal_rank,
)
from scripts.synthetic.persona import RELEVANT_GRADE  # noqa: E402

HEADER = "DỮ LIỆU GIẢ LẬP — không phải kết quả người dùng thật"
STRATEGIES = ("moodbite", "distance", "random")
# Cần ít nhất 2 ứng viên thì "thứ tự" mới có nghĩa.
MIN_CANDIDATES = 2
COVERAGE_K = 10


def rank_candidates(candidates: list[dict], strategy: str, seed: int, session_id: str) -> list[dict]:
    if strategy == "moodbite":
        return sorted(candidates, key=lambda c: c["moodbite_rank"])
    if strategy == "distance":
        # Hoà khoảng cách thì theo id để kết quả ổn định giữa các lần chạy.
        return sorted(candidates, key=lambda c: (c["distance_m"], c["restaurant_id"]))
    # crc32 thay vì hash(): hash() của chuỗi đổi theo mỗi tiến trình Python.
    shuffled = list(candidates)
    random.Random(seed + zlib.crc32(session_id.encode("utf-8"))).shuffle(shuffled)
    return shuffled


def evaluate(sessions: list[dict], seed: int) -> dict:
    usable = [s for s in sessions if len(s.get("candidates") or []) >= MIN_CANDIDATES]
    report = _evaluate_usable(sessions, usable, seed)
    # TÁCH THEO LUỒNG (thêm 2026-10-02). Phân tích ngày 2026-09-29: con số tổng che mất một
    # khác biệt lớn - luồng tìm kiếm gần hoà với baseline khoảng cách, còn luồng món thua xa
    # vì ở đó MỌI ứng viên cùng một món nên phần "khẩu vị" của nhãn gần như không đổi trong
    # phiên, nhãn chỉ còn lại khoảng cách. Báo cáo chỉ con số tổng là báo cáo sai bức tranh.
    report["by_entry_metrics"] = {
        e: _evaluate_usable(sessions, [s for s in usable if s["entry"] == e], seed)["metrics"]
        for e in ("dish", "search")
        if any(s["entry"] == e for s in usable)
    }
    return report


def _evaluate_usable(sessions: list[dict], usable: list[dict], seed: int) -> dict:
    universe = {c["restaurant_id"] for s in usable for c in s["candidates"]}
    results = {}
    for strategy in STRATEGIES:
        per = {"ndcg@5": [], "ndcg@10": [], "p@5": [], "p@10": [], "mrr": []}
        tops = []
        for s in usable:
            ranked = rank_candidates(s["candidates"], strategy, seed, s["session_id"])
            grades = [c["grade"] for c in ranked]
            relevant = [g >= RELEVANT_GRADE for g in grades]
            per["ndcg@5"].append(ndcg_at_k(grades, 5))
            per["ndcg@10"].append(ndcg_at_k(grades, 10))
            per["p@5"].append(precision_at_k(relevant, 5))
            per["p@10"].append(precision_at_k(relevant, 10))
            per["mrr"].append(reciprocal_rank(relevant))
            tops.append([c["restaurant_id"] for c in ranked[:COVERAGE_K]])
        results[strategy] = {name: mean(vals) for name, vals in per.items()}
        results[strategy]["coverage@10"] = catalog_coverage(tops, universe)
    no_relevant = sum(1 for s in usable if not any(c["grade"] for c in s["candidates"]))
    return {
        "synthetic": True,
        "warning": HEADER,
        "sessions_total": len(sessions),
        "sessions_evaluated": len(usable),
        "sessions_without_any_relevant_item": no_relevant,
        "candidate_universe": len(universe),
        "by_entry": {e: sum(1 for s in usable if s["entry"] == e) for e in ("dish", "search")},
        "metrics": results,
    }


def print_table(report: dict) -> None:
    bar = "!" * (len(HEADER) + 8)
    print(f"{bar}\n!!! {HEADER} !!!\n{bar}")
    print(f"Phiên: {report['sessions_total']} | đánh giá được: {report['sessions_evaluated']} "
          f"(món: {report['by_entry']['dish']}, tìm kiếm: {report['by_entry']['search']}) | "
          f"không có quán nào hợp (loại khỏi NDCG): {report['sessions_without_any_relevant_item']} | "
          f"tập ứng viên: {report['candidate_universe']} quán")
    cols = ("ndcg@5", "ndcg@10", "p@5", "p@10", "mrr", "coverage@10")
    print(f"{'chiến lược':<10} " + " ".join(f"{c:>11}" for c in cols))
    for strategy, m in report["metrics"].items():
        cells = " ".join(f"{'-' if m[c] is None else format(m[c], '.4f'):>11}" for c in cols)
        print(f"{strategy:<10} {cells}")
    for entry, metrics in report.get("by_entry_metrics", {}).items():
        nhan = "luồng MÓN" if entry == "dish" else "luồng TÌM KIẾM"
        print(f"-- {nhan}: " + " · ".join(
            f"{s} ndcg@10={'-' if m['ndcg@10'] is None else format(m['ndcg@10'], '.4f')}"
            for s, m in metrics.items()
        ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Đánh giá xếp hạng trên phiên giả lập.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    paths = synthetic_paths(args.out_dir)
    if not paths.sessions.exists():
        print(f"Chưa có {paths.sessions}. Chạy trước: python scripts/gia_lap_nguoi_dung.py --reset")
        return 1
    with paths.sessions.open(encoding="utf-8") as f:
        sessions = [json.loads(line) for line in f if line.strip()]
    report = evaluate(sessions, args.seed)
    print_table(report)
    paths.eval_results.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi: {paths.eval_results}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
