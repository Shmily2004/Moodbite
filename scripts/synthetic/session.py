"""Một PHIÊN dùng app của người dùng giả lập — gọi API THẬT qua FastAPI TestClient.

Gọi qua HTTP (TestClient) thay vì gọi thẳng use case: có vậy dữ liệu sinh ra mới đi qua
đúng router, kiểm tra hợp lệ, xác thực token và luật `is_positive_signal` như người thật.
Endpoint lỗi thì phiên giả lập cũng lỗi — đó là điều ta MUỐN thấy.
"""
from __future__ import annotations

import logging
import random
import uuid
from collections import Counter
from typing import Optional

from scripts.synthetic.an_toan import SESSION_PREFIX
from scripts.synthetic.click_model import (
    SHOWN_TOP_K,
    choose_one,
    reactions_after_click,
    simulate_clicks,
)
from scripts.synthetic.persona import (
    Persona,
    dish_utility,
    natural_query,
    relevance_grade,
    restaurant_utility,
)

logger = logging.getLogger("moodbite.synthetic")
API = "/api/v1"

# Bữa trong ngày và tỷ lệ phiên rơi vào mỗi bữa. GIẢ ĐỊNH (trưa/tối đông nhất), không đo.
# Mã bữa đúng từ vựng `src/domain/entities/dish.py::MEAL_TIMES`.
MEAL_SLOTS = ("sang", "trua", "an_vat", "toi", "khuya")
MEAL_WEIGHTS = (0.18, 0.34, 0.12, 0.30, 0.06)
# Tỷ lệ phiên đi theo luồng CHÍNH (chọn món trước) so với gõ câu tìm kiếm.
DISH_FLOW_SHARE = 0.65
# Lấy 50 quán làm TẬP ỨNG VIÊN để đánh giá xếp hạng lại; người dùng chỉ thấy 10 quán đầu.
CANDIDATE_POOL = 50
# Xác suất mở trang giới thiệu món trước khi xem quán, và lưu món/quán vào danh sách.
OPEN_DISH_DETAIL_PROB = 0.3
SAVE_DISH_PROB = 0.1
SAVE_RESTAURANT_TO_LIST_PROB = 0.5


def _check(resp, what: str) -> Optional[dict]:
    if resp.status_code >= 400:
        logger.warning("%s -> HTTP %s: %s", what, resp.status_code, resp.text[:200])
        return None
    return resp.json()["data"]


def run_session(
    client, token: str, persona: Persona, rng: random.Random, day: int,
    moods: tuple[str, ...], counters: Counter,
) -> dict:
    """Chạy một phiên, ghi tương tác qua API, trả bản ghi sidecar cho đánh giá."""
    headers = {"Authorization": f"Bearer {token}"}
    session_id = f"{SESSION_PREFIX}{uuid.UUID(int=rng.getrandbits(128))}"
    meal = rng.choices(MEAL_SLOTS, weights=MEAL_WEIGHTS)[0]
    # 80% theo mood quen thuộc của người đó, 20% tâm trạng bất chợt.
    mood = rng.choice(persona.preferred_moods) if rng.random() < 0.8 else rng.choice(moods)
    record = {
        "session_id": session_id, "username": persona.username, "day": day,
        "meal_time": meal, "mood": mood, "entry": None, "query": None,
        "search_query_id": None, "candidates": [], "clicked_ranks": [],
    }
    location = {"latitude": persona.home_lat, "longitude": persona.home_lng}

    results = None
    if rng.random() < DISH_FLOW_SHARE:
        record["entry"] = "dish"
        results = _dish_flow(client, headers, persona, rng, session_id, meal, mood,
                             location, record, counters)
    else:
        record["entry"] = "search"
        query_text = natural_query(rng, persona)
        record["query"] = query_text
        data = _check(client.post(f"{API}/search", json={
            "session_id": session_id, "query_text": query_text, **location,
            "max_distance_km": persona.max_travel_km, "limit": CANDIDATE_POOL,
        }), "POST /search")
        counters["api_search"] += 1
        if data:
            record["search_query_id"] = data["search_query_id"]
            results = data["results"]

    if not results:
        counters["sessions_abandoned"] += 1
        return record

    utilities = [restaurant_utility(persona, item) for item in results]
    record["candidates"] = [
        {"restaurant_id": item["restaurant_id"], "moodbite_rank": item["rank_position"],
         "distance_m": item["distance_m"], "utility": u, "grade": relevance_grade(u)}
        for item, u in zip(results, utilities)
    ]
    for index in simulate_clicks(rng, utilities):
        item = results[index]
        record["clicked_ranks"].append(item["rank_position"])
        for reaction in reactions_after_click(rng, utilities[index]):
            _log_interaction(client, headers, session_id, record["search_query_id"],
                             item, reaction, counters)
            if reaction.action_type == "save" and rng.random() < SAVE_RESTAURANT_TO_LIST_PROB:
                _save_favorite(client, headers, rng, "restaurant",
                               item["restaurant_id"], item["name"], counters)
    return record


def _dish_flow(client, headers, persona, rng, session_id, meal, mood, location,
               record, counters) -> Optional[list]:
    data = _check(client.post(f"{API}/dishes/suggest", json={
        "session_id": session_id, **location, "mood": mood, "meal_times": [meal],
        "max_distance_km": persona.max_travel_km, "limit": 12,
    }), "POST /dishes/suggest")
    counters["api_dish_suggest"] += 1
    if not data or not data["results"]:
        return None
    dishes = data["results"]
    picked = choose_one(rng, [dish_utility(persona, d) for d in dishes])
    if picked is None:
        return None
    dish = dishes[picked]
    record["query"] = dish["dish_id"]
    if rng.random() < OPEN_DISH_DETAIL_PROB:
        _check(client.get(f"{API}/dishes/{dish['dish_id']}", params={
            **location, "max_distance_km": persona.max_travel_km}), "GET /dishes/{id}")
        counters["api_dish_detail"] += 1
    if rng.random() < SAVE_DISH_PROB:
        _save_favorite(client, headers, rng, "dish", dish["dish_id"], dish["name"], counters)
    data = _check(client.get(f"{API}/dishes/{dish['dish_id']}/restaurants", params={
        "session_id": session_id, **location, "mood": mood,
        "max_distance_km": persona.max_travel_km, "limit": CANDIDATE_POOL,
    }), "GET /dishes/{id}/restaurants")
    counters["api_dish_restaurants"] += 1
    if not data:
        return None
    record["search_query_id"] = data["search_query_id"]
    return data["results"]


def _log_interaction(client, headers, session_id, search_query_id, item, reaction,
                     counters) -> None:
    body = {
        "session_id": session_id, "restaurant_id": item["restaurant_id"],
        "action_type": reaction.action_type, "search_query_id": search_query_id,
        "rank_position": item["rank_position"],
    }
    if reaction.dwell_time_ms is not None:
        body["dwell_time_ms"] = reaction.dwell_time_ms
    data = _check(client.post(f"{API}/interactions", json=body, headers=headers),
                  "POST /interactions")
    if data is None:
        counters["interaction_errors"] += 1
        return
    counters[f"event_{reaction.action_type}"] += 1
    counters["events_total"] += 1
    counters["events_positive"] += int(data["is_positive_signal"])


def _save_favorite(client, headers, rng, item_type, item_id, name, counters) -> None:
    list_type = rng.choice(("favorite", "bookmark"))
    if _check(client.post(f"{API}/me/favorites", headers=headers, json={
        "item_type": item_type, "item_id": item_id, "name": name, "list_type": list_type,
    }), "POST /me/favorites") is not None:
        counters[f"saved_{item_type}_{list_type}"] += 1
