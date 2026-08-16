MoodBite - Code Organization and Clean Architecture Notes

Overview
--------
This document explains the current layout and recommended navigation for maintainability.

Top-level Python package: `src/`

Recommended structure inside `src/`:
- `domain/` - core entities and value objects (pure logic/data classes)
- `application/` - use-cases and service classes (business rules)
  - `services/` - classes like `RecommendationService`, `DishRecommendationService`
  - `use_cases/` - thin orchestration functions for controller use
- `infrastructure/` - adapters, repositories, AI integrations
  - `repositories/` - data access layer (CSV, DB, external APIs)
  - `ai/` - model integration, lazy loaders
  - `adapters/` - third-party integrations
- `presentation/` - API layer (FastAPI routes, schemas, startup)
  - `api/` - `routes.py`, `schemas.py`, `startup.py`, `main.py`

Why this helps
----------------
- Single-responsibility files make debugging faster: to find data-loading bugs, check `infrastructure/repositories` first.
- DI via `startup.py` centralizes lifecycle management; routes only orchestrate use-cases and call services from `app.state`.
- Pydantic schemas are the single source of truth for API contracts.

Migration notes
---------------
- Prefer small incremental PRs: first extract repositories, then wire services via `startup.py`, then add schemas and exception handlers.
- Tests should mock repositories (not CSV files) to make unit tests fast and deterministic.
