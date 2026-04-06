# Tadpole Interactive Story Engine - Current Codebase Documentation

This document describes what is currently implemented in the repository as of now (code-first snapshot), including modules, features, data model, API endpoints, request parameters, and response formats.

## 1) Project Snapshot

- Framework: Django 6 + Django REST Framework
- Database: SQLite (`db.sqlite3`)
- Main app modules:
  - `backend/` - project configuration and a session-based interactive story API
  - `game/` - persistent DB-backed story/domain models and REST endpoints
- Entry URLs are configured in `backend/urls.py`

## 2) Implemented Features

### A. Session-based interactive story runtime (in-memory story graph)
Implemented in `backend/views.py` using classes from `backend/story_logic.py`.

- Starts a story session and stores state in Django session (`game_state`)
- Processes player choices by:
  - validating current scene + selected choice
  - applying choice effects to state variables
  - moving to next scene
  - detecting ending scenes
- Supports conditional flow where a scene can expose only the first matching conditional choice (with fallback)
- Returns CSRF token in API responses and sets CSRF cookie

### B. Database-backed story API (DRF)
Implemented in `game/models.py`, `game/serializers.py`, `game/views.py`, and `game/urls.py`.

- List stories
- List scenes / fetch single scene
- List choices for a scene
- Submit a choice selection to compute next scene by trust-level logic
- Retrieve player state records (currently hardcoded to user `id=1` in view logic)

### C. Admin support
Implemented in `game/admin.py`.

- Registers `Story`, `Scene`, `Choice`, and `PlayerState` models in Django admin.

### D. Automated tests
Implemented mainly under `tests/`.

- `tests/test_story_logic.py`: unit tests for `StoryState`, `Scene`, `Choice`
- `tests/test_views.py`: integration tests for story API endpoints (`/story/api/start/`, `/story/api/choice/`) and helper logic

## 3) Module Map

### `backend/`

- `backend/settings.py`
  - Django settings, `rest_framework` + `game` installed apps, SQLite config, static file settings, `.env` loading via `django-environ`
- `backend/urls.py`
  - Root router:
    - `/admin/`
    - `/story/` (story list)
    - `/story/<id>/` (story play)
    - `/story/api/` (includes `apps.story.urls`)
- `backend/story_logic.py`
  - Plain Python domain classes used by the session API:
    - `StoryState(story_id, current_scene_id, variables={}, visited_scenes=[])`
    - `Scene(scene_id, background, choices, conditions={})`
    - `Choice(scene_id, text, target_scene_id, conditions={}, effects={})`
- `backend/views.py`
  - Contains in-memory `STORY_DATA`
  - Endpoint handlers: `start_story`, `process_choice`
  - Helpers: `build_scene_response`, `get_available_choices`, `check_conditions`, `has_conditional_flow`
- `backend/asgi.py`, `backend/wsgi.py`
  - Standard ASGI/WSGI application setup

### `game/`

- `game/models.py`
  - Persistent entities: `Story`, `Scene`, `Choice`, `PlayerState`
- `game/serializers.py`
  - DRF model serializers for each model (`fields = '__all__'`)
- `game/views.py`
  - API views:
    - `StoryView`
    - `SceneListView`
    - `SceneView`
    - `ChoiceView` (GET choices by scene, POST choice selection)
    - `PlayerStateView`
- `game/urls.py`
  - URL routes mounted at `/game/`
- `game/migrations/`
  - Schema creation and additions for `Scene.is_ending` and `Scene.is_starting`
- `game/admin.py`
  - Admin model registration

### `tests/`

- `tests/conftest.py` - pytest + Django setup
- `tests/fixtures.py` - reusable in-memory story fixtures
- `tests/test_story_logic.py` - unit tests for story logic classes
- `tests/test_views.py` - integration tests for session API and helper functions

## 4) Data Model (Database)

Defined in `game/models.py`.

### `Story`
- `id` (auto)
- `title: CharField(200)`
- `theme: CharField(100)`
- `description: TextField`

### `Scene`
- `id` (auto)
- `story: ForeignKey(Story, related_name='scenes')`
- `scene_content: TextField`
- `background_image: URLField(null=True, blank=True)`
- `trust_level: IntegerField(default=0)`
- `is_ending: BooleanField(default=False)`
- `is_starting: BooleanField(default=False)`

### `Choice`
- `id` (auto)
- `label: CharField(200)`
- `trust_level_change: IntegerField(default=0)`
- `scene: ForeignKey(Scene, related_name='choices')`

### `PlayerState`
- `id` (auto)
- `user: ForeignKey(auth.User)`
- `story: ForeignKey(Story)`
- `current_scene: ForeignKey(Scene, null=True, on_delete=SET_NULL)`

## 5) API Reference

Base URL examples below assume local server at `http://localhost:8000`.

---

### 5.1 Story API (`apps/story/views.py`)

#### `GET /story/api/start/`
Starts a new in-session game state.

- Method: `GET`
- Query params: `story_id` (required)
- Side effects:
  - creates/overwrites `request.session['game_state']`
  - sets CSRF cookie (`csrftoken`)
- Success response: `200 OK`

Example response shape:

```json
{
  "csrf_token": "<token>",
  "story": {
    "id": 1,
    "title": "The Lantern Trail",
    "description": "A rainy night reveals a quiet house and a choice to trust the light.",
    "background_music_url": "https://example.com/music.mp3"
  },
  "scene": {
    "id": 10,
    "title": "At the Gate",
    "content": "Rain taps the iron gate. A warm lantern glows inside the house.",
    "background_image_url": "https://example.com/image.png",
    "choices": [
      {"id": 1, "text": "Enter the house", "available": true},
      {"id": 2, "text": "Don't enter, go to the barn", "available": true}
    ]
  },
  "attributes": [
    {"key": "trust", "label": "Trust", "value": 0},
    {"key": "security", "label": "Security", "value": 0}
  ]
}
```

#### `POST /story/api/choice/`
Processes a player choice and transitions to next scene.

- Method: `POST` only
- Content type: `application/json`
- Required JSON body:

```json
{
  "choice_id": 1,
  "story_id": 1
}
```

- Validation behavior:
  - returns `405` if method is not POST
  - returns `400` if no active story session
  - returns `400` for invalid JSON
  - returns `400` if the choice does not match the current scene
  - returns `404` for invalid choice

- Success response when next scene is non-ending: `200 OK`

```json
{
  "csrf_token": "<token>",
  "scene": {
    "id": 11,
    "title": "Inside the House",
    "content": "You step into the foyer. A friend offers tea and a story.",
    "background_image_url": "https://example.com/image.png",
    "choices": [
      {"id": 3, "text": "Trust the friend", "available": true}
    ]
  },
  "attributes": [
    {"key": "trust", "label": "Trust", "value": 10},
    {"key": "security", "label": "Security", "value": 10}
  ]
}
```

- Success response when next scene has no choices (ending): `200 OK`

```json
{
  "ending": true,
  "message": "The story concludes here.",
  "final_attributes": [
    {"key": "trust", "label": "Trust", "value": -5},
    {"key": "security", "label": "Security", "value": -10}
  ],
  "path": [0, 3]
}
```

---

### 5.2 Game API (`game/views.py`, mounted under `/game/`)

#### `GET /game/stories/`
Returns all stories.

- Method: `GET`
- Query params: none
- Response: `200 OK`, array of serialized `Story` records

Example:

```json
[
  {
    "id": 1,
    "title": "Story Title",
    "theme": "Mystery",
    "description": "..."
  }
]
```

#### `GET /game/scenes/`
Returns all scenes.

- Method: `GET`
- Query params: none
- Response: `200 OK`, array of serialized `Scene` records

#### `GET /game/scenes/<scene_id>/`
Returns a single scene.

- Path param: `scene_id` (integer)
- Success: `200 OK`, serialized `Scene`
- Not found: `404 Not Found`

Error example:

```json
{"error": "Scene not found"}
```

#### `GET /game/scenes/<scene_id>/choices/`
Returns all choices for a scene.

- Path param: `scene_id` (integer)
- Success: `200 OK`, array of serialized `Choice`
- Not found: `404 Not Found` with `{"error": "Scene not found"}`

#### `POST /game/choices/<choice_id>/select/`
Processes a selected choice and computes the next scene by trust-level lookup.

- Path param: `choice_id` (integer)
- Request body: none currently required/used
- Internal behavior:
  - fetches `Choice` by `choice_id`
  - derives current scene as `choice.scene`
  - creates `PlayerState` using hardcoded `user = 1`, `story = scene.story.id`, `current_scene = scene.id`
  - computes `new_trust_level = scene.trust_level + choice.trust_level_change`
  - special case: if `new_trust_level < 0` and current scene `is_starting=True`, adjusts baseline
  - selects next scene via `Scene.objects.filter(trust_level=new_trust_level).first()`

- Success (`200 OK`):
  - if next scene is ending (`is_ending=True`):

```json
{
  "message": "You've reached an ending!",
  "scene": {
    "id": 10,
    "story": 1,
    "scene_content": "...",
    "background_image": null,
    "trust_level": 20,
    "is_ending": true,
    "is_starting": false
  }
}
```

  - if not ending: returns serialized `Scene` object directly

- Error cases:
  - `404 Not Found` if choice does not exist: `{"error": "Choice not found"}`
  - `400 Bad Request` if `PlayerStateSerializer` validation fails
  - `404 Not Found` if no scene exists for computed trust level: `{"error": "No scene found for this trust level"}`

#### `GET /game/player-state/`
Returns player state records for hardcoded `user = 1`.

- Method: `GET`
- Response: `200 OK`, array of serialized `PlayerState`

---

### 5.3 Admin Endpoint

#### `GET /admin/`
Django admin panel (authentication required).

## 6) Session Story Data and Flow

The session API uses an in-code story graph (`STORY_DATA` in `backend/views.py`) with scene IDs `0..8`.

- Variables used: `trust`, `security`
- Endings occur when scene has `choices=[]` (e.g., scenes `4`, `6`, `7`, `8`)
- Conditional flow implemented at scene `5`:
  - first choice requires `trust >= 30` and `security >= 10`
  - second choice acts as fallback
  - helper `has_conditional_flow` enforces "first matching choice only" behavior for this pattern

## 7) Configuration and Runtime Notes

- Environment handling: `django-environ` in `backend/settings.py`
  - required: `SECRET_KEY`
  - optional: `DEBUG`, `ALLOWED_HOSTS`
- Static files:
  - `STATIC_URL = '/static/'`
  - additional dir: `static/`
- Containerization:
  - `Dockerfile` and `compose.yml` included
  - container command runs migrations then `runserver`

## 8) Testing Coverage Summary

Based on existing tests in `tests/`:

- Covered well:
  - Session API happy paths and most error paths
  - Ending behavior
  - Conditional-choice helpers
  - Domain classes in `story_logic.py`
- Not clearly covered in this repository:
  - DRF endpoints in `game/views.py`
  - Authentication/permissions behavior around hardcoded user usage in `game` API

## 9) Known Implementation Characteristics (Current State)

These are factual characteristics of the current implementation that may influence API consumers:

- The repository has two parallel story systems:
  1. in-memory/session-driven API under `/api/*`
  2. DB-backed API under `/game/*`
- `/game/*` endpoints currently do not use authenticated request user; several views are hardcoded to `user = 1`
- `ChoiceView.post` in `game/views.py` does not consume request payload today; it relies only on path `choice_id`
- Session API relies on client-provided `current_scene_id` in `/api/choice/`; server validates that scene and choice exist

## 10) Quick Endpoint Index

- `GET /admin/`
- `GET /api/start/`
- `POST /api/choice/`
- `GET /game/stories/`
- `GET /game/scenes/`
- `GET /game/scenes/<scene_id>/`
- `GET /game/scenes/<scene_id>/choices/`
- `POST /game/choices/<choice_id>/select/`
- `GET /game/player-state/`

