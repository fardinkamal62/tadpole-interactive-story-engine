import base64
import json

from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from .models import Choice, PlayerState, Scene, Story, StoryAttribute


def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _normalize_attribute_key(raw_key):
    return (raw_key or "").strip().lower().replace(" ", "_")


def _parse_attribute_payload(raw_payload):
    if not raw_payload:
        return [
            {"key": "trust", "label": "Trust", "initial_value": 0},
            {"key": "courage", "label": "Courage", "initial_value": 0},
        ]

    try:
        parsed_defaults = json.loads(raw_payload)
    except json.JSONDecodeError:
        raise ValueError("attribute_defaults must be valid JSON")

    if not isinstance(parsed_defaults, list):
        raise ValueError("attribute_defaults must be a JSON list")

    attribute_defaults = []
    for index, item in enumerate(parsed_defaults):
        if not isinstance(item, dict):
            raise ValueError(f"attribute_defaults[{index}] must be an object")

        key = _normalize_attribute_key(item.get("key"))
        label = (item.get("label") or key.replace("_", " ").title()).strip()

        try:
            initial_value = int(item.get("initial_value", 0))
        except (TypeError, ValueError):
            raise ValueError(f"attribute_defaults[{index}].initial_value must be an integer")

        if not key:
            raise ValueError(f"attribute_defaults[{index}].key is required")

        attribute_defaults.append(
            {
                "key": key,
                "label": label,
                "initial_value": initial_value,
            }
        )

    deduplicated_attributes = []
    seen_keys = set()
    for item in attribute_defaults:
        if item["key"] in seen_keys:
            continue
        seen_keys.add(item["key"])
        deduplicated_attributes.append(item)

    return deduplicated_attributes


def _audio_payload(background_audio):
    if not background_audio:
        return None

    if not (background_audio.content_type or "").startswith("audio/"):
        raise ValueError("background_audio must be an audio file")
    if background_audio.size > 5 * 1024 * 1024:
        raise ValueError("background_audio must be smaller than 5 MB")

    encoded_audio = base64.b64encode(background_audio.read()).decode("ascii")
    return f"data:{background_audio.content_type};base64,{encoded_audio}"


def _story_payload_from_request(request, story=None):
    title = (request.data.get("title") or "").strip()
    description = (request.data.get("description") or "").strip()
    background_music_url = (request.data.get("background_music_url") or "").strip()
    background_audio = request.FILES.get("background_audio")

    if not title:
        raise ValueError("title is required")

    audio_url = _audio_payload(background_audio) if background_audio is not None else None
    if audio_url is not None:
        background_music_url = audio_url
    elif story is not None and not background_music_url:
        background_music_url = story.background_music_url

    attribute_defaults = _parse_attribute_payload(request.data.get("attribute_defaults"))

    return {
        "title": title,
        "description": description,
        "background_music_url": background_music_url,
        "attribute_defaults": attribute_defaults,
    }


def _store_story_attributes(story, attribute_defaults):
    StoryAttribute.objects.filter(story=story).delete()
    StoryAttribute.objects.bulk_create(
        [
            StoryAttribute(
                story=story,
                key=item["key"],
                label=item["label"],
                initial_value=item["initial_value"],
            )
            for item in attribute_defaults
        ]
    )


def _story_response(story, payload, message, status_code):
    return JsonResponse(
        {
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "background_music_url": story.background_music_url,
            "attribute_defaults": payload["attribute_defaults"],
            "message": message,
        },
        status=status_code,
    )


def _get_owned_story(user_id, story_id):
    try:
        story = Story.objects.prefetch_related("attributes").get(pk=story_id)
    except Story.DoesNotExist:
        return None, JsonResponse({"error": "Story not found"}, status=404)

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return None, JsonResponse({"error": "You can only edit your own stories"}, status=403)

    # Legacy stories can have no owner. First authenticated editor claims ownership.
    if story.owner_id is None:
        claimed_count = Story.objects.filter(pk=story.pk, owner__isnull=True).update(owner_id=user_id_int)
        if claimed_count:
            story.owner_id = user_id_int

    if story.owner_id != user_id_int:
        return None, JsonResponse({"error": "You can only edit your own stories"}, status=403)

    return story, None


def _parse_choice_payload(story, raw_choice, index):
    if not isinstance(raw_choice, dict):
        raise ValueError(f"choices[{index}] must be an object")

    text = (raw_choice.get("text") or "").strip()
    if not text:
        raise ValueError(f"choices[{index}].text is required")

    target_scene_id = raw_choice.get("target_scene_id")
    if target_scene_id in (None, ""):
        target_scene_id = None
    else:
        try:
            target_scene_id = int(str(target_scene_id))
        except (TypeError, ValueError):
            raise ValueError(f"choices[{index}].target_scene_id must be an integer")

        target_exists = story.scenes.filter(pk=target_scene_id).exists()
        if not target_exists:
            raise ValueError(f"choices[{index}].target_scene_id must belong to this story")

    conditions = {}
    if isinstance(raw_choice.get("conditions"), dict):
        for k, v in raw_choice["conditions"].items():
            key = _normalize_attribute_key(k)
            if key and v not in (None, ""):
                try:
                    conditions[key] = int(str(v))
                except (TypeError, ValueError):
                    raise ValueError(f"choices[{index}].conditions.{k} must be an integer")
    else:
        requirement = raw_choice.get("requirement") or {}
        requirement_key = _normalize_attribute_key(requirement.get("key"))
        requirement_value = requirement.get("value")
        if requirement_key and requirement_value not in (None, ""):
            try:
                conditions[requirement_key] = int(str(requirement_value))
            except (TypeError, ValueError):
                raise ValueError(f"choices[{index}].requirement.value must be an integer")

    effects = {}
    if isinstance(raw_choice.get("effects"), dict):
        for k, v in raw_choice["effects"].items():
            key = _normalize_attribute_key(k)
            if key and v not in (None, ""):
                try:
                    effects[key] = int(str(v))
                except (TypeError, ValueError):
                    raise ValueError(f"choices[{index}].effects.{k} must be an integer")
    else:
        effect = raw_choice.get("effect") or {}
        effect_key = _normalize_attribute_key(effect.get("key"))
        effect_delta = effect.get("delta")
        if effect_key and effect_delta not in (None, ""):
            try:
                effects[effect_key] = int(str(effect_delta))
            except (TypeError, ValueError):
                raise ValueError(f"choices[{index}].effect.delta must be an integer")

    return {
        "text": text,
        "target_scene_id": target_scene_id,
        "conditions": conditions,
        "effects": effects,
    }


def _attributes_payload(story, attributes):
    payload = []
    for story_attribute in story.attributes.all():
        payload.append(
            {
                "key": story_attribute.key,
                "label": story_attribute.label,
                "value": attributes.get(story_attribute.key, story_attribute.initial_value),
            }
        )
    return payload


def _check_conditions(conditions, attributes):
    for key, required_value in conditions.items():
        if attributes.get(key, 0) < required_value:
            return False
    return True


def _has_conditional_flow(choices):
    return len(choices) >= 2 and choices[0].conditions and not choices[-1].conditions


def _get_available_choices(scene, attributes):
    choices_payload = []
    choices = list(scene.choices.all())
    for choice in choices:
        if choice.target_scene_id is None:
            continue
        choices_payload.append(
            {
                "id": choice.id,
                "text": choice.text,
                "available": _check_conditions(choice.conditions, attributes),
            }
        )

    if len(choices_payload) > 1 and _has_conditional_flow(choices):
        for index, choice in enumerate(choices):
            if _check_conditions(choice.conditions, attributes):
                return [choices_payload[index]]
        return [choices_payload[-1]]

    return choices_payload


def _build_scene_response(request, story, scene, attributes):
    return JsonResponse(
        {
            "csrf_token": get_token(request),
            "story": {
                "id": story.id,
                "title": story.title,
                "description": story.description,
                "background_music_url": story.background_music_url,
            },
            "scene": {
                "id": scene.id,
                "title": scene.title,
                "content": scene.content,
                "background_image_url": scene.background_image_url,
                "background_image_mime": scene.background_image_mime,
                "choices": _get_available_choices(scene, attributes),
            },
            "attributes": _attributes_payload(story, attributes),
        }
    )


@ensure_csrf_cookie
@require_http_methods(["GET"])
def start_story(request):
    story_id = request.GET.get("story_id")
    if not story_id:
        return JsonResponse({"error": "story_id is required"}, status=400)

    try:
        story = Story.objects.prefetch_related("attributes").get(pk=story_id)
    except Story.DoesNotExist:
        return JsonResponse({"error": "Story not found"}, status=404)

    starting_scene = story.scenes.filter(is_starting=True).first()
    if not starting_scene:
        starting_scene = story.scenes.order_by("id").first()
    if not starting_scene:
        return JsonResponse({"error": "No scenes available"}, status=404)

    session_key = _get_session_key(request)
    PlayerState.objects.filter(story=story, session_key=session_key).delete()

    attributes = {
        story_attribute.key: story_attribute.initial_value
        for story_attribute in story.attributes.all()
    }

    PlayerState.objects.create(
        story=story,
        session_key=session_key,
        current_scene=starting_scene,
        attributes=attributes,
        visited_scenes=[],
    )

    return _build_scene_response(request, story, starting_scene, attributes)


@require_http_methods(["POST"])
def process_choice(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    choice_id = data.get("choice_id")
    story_id = data.get("story_id")

    if not choice_id or not story_id:
        return JsonResponse({"error": "choice_id and story_id are required"}, status=400)

    session_key = _get_session_key(request)

    try:
        player_state = PlayerState.objects.select_related("current_scene", "story").get(
            story_id=story_id,
            session_key=session_key,
        )
    except PlayerState.DoesNotExist:
        return JsonResponse({"error": "No active story session"}, status=400)

    try:
        choice = Choice.objects.select_related("scene", "target_scene").get(pk=choice_id)
    except Choice.DoesNotExist:
        return JsonResponse({"error": "Choice not found"}, status=404)

    if choice.scene_id != player_state.current_scene_id:
        return JsonResponse({"error": "Choice does not match current scene"}, status=400)

    if choice.target_scene_id is None:
        return JsonResponse({"error": "Choice is not linked to a scene yet"}, status=400)

    if not _check_conditions(choice.conditions, player_state.attributes or {}):
        return JsonResponse({"error": "Choice requirements not met"}, status=400)

    attributes = player_state.attributes or {}
    if not _check_conditions(choice.conditions or {}, attributes):
        return JsonResponse({"error": "Choice requirements not met"}, status=400)

    for key, delta in choice.effects.items():
        attributes[key] = attributes.get(key, 0) + delta

    visited_scenes = list(player_state.visited_scenes or [])
    visited_scenes.append(player_state.current_scene_id)

    player_state.attributes = attributes
    player_state.visited_scenes = visited_scenes
    player_state.current_scene = choice.target_scene
    player_state.save(update_fields=["attributes", "visited_scenes", "current_scene", "updated_at"])

    next_scene = choice.target_scene
    if next_scene.is_ending or not next_scene.choices.exists():
        return JsonResponse(
            {
                "ending": True,
                "message": "The story concludes here.",
                "story": {
                    "id": player_state.story.id,
                    "title": player_state.story.title,
                    "description": player_state.story.description,
                    "background_music_url": player_state.story.background_music_url,
                },
                "scene": {
                    "id": next_scene.id,
                    "title": next_scene.title,
                    "content": next_scene.content,
                    "background_image_url": next_scene.background_image_url,
                },
                "final_attributes": _attributes_payload(player_state.story, attributes),
                "path": visited_scenes,
            }
        )

    return _build_scene_response(request, player_state.story, next_scene, attributes)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_story(request):
    try:
        payload = _story_payload_from_request(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    with transaction.atomic():
        story = Story.objects.create(
            owner=request.user,
            title=payload["title"],
            description=payload["description"],
            background_music_url=payload["background_music_url"],
        )
        _store_story_attributes(story, payload["attribute_defaults"])

    return _story_response(story, payload, "Story draft created. Scene editor ready.", 201)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_story(request, story_id):
    story, error_response = _get_owned_story(request.user.id, story_id)
    if error_response:
        return error_response

    try:
        payload = _story_payload_from_request(request, story=story)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    with transaction.atomic():
        story.title = payload["title"]
        story.description = payload["description"]
        story.background_music_url = payload["background_music_url"]
        story.save(update_fields=["title", "description", "background_music_url"])
        _store_story_attributes(story, payload["attribute_defaults"])

    return _story_response(story, payload, "Story updated.", 200)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_story_scenes(request, story_id):
    story, error_response = _get_owned_story(request.user.id, story_id)
    if error_response:
        return error_response

    scenes = story.scenes.prefetch_related("choices").order_by("id")
    scene_payload = []
    for scene in scenes:
        scene_payload.append(
            {
                "id": scene.id,
                "title": scene.title,
                "content": scene.content,
                "background_image_url": scene.background_image_url,
                "is_starting": scene.is_starting,
                "is_ending": scene.is_ending,
                "choices": [
                    {
                        "id": choice.id,
                        "text": choice.text,
                        "target_scene_id": choice.target_scene_id,
                        "conditions": choice.conditions,
                        "effects": choice.effects,
                    }
                    for choice in scene.choices.all()
                ],
            }
        )

    return JsonResponse(
        {
            "story": {"id": story.id, "title": story.title},
            "attributes": [
                {
                    "key": attribute.key,
                    "label": attribute.label,
                    "initial_value": attribute.initial_value,
                }
                for attribute in story.attributes.all()
            ],
            "scenes": scene_payload,
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser])
def create_story_scene(request, story_id):
    story, error_response = _get_owned_story(request.user.id, story_id)
    if error_response:
        return error_response

    title = (request.data.get("title") or "").strip()
    content = (request.data.get("content") or "").strip()
    background_image_url = (request.data.get("background_image_url") or "").strip()
    is_ending = bool(request.data.get("is_ending"))
    is_starting = bool(request.data.get("is_starting"))

    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    raw_choices = request.data.get("choices") or []
    if isinstance(raw_choices, str):
        try:
            raw_choices = json.loads(raw_choices)
        except json.JSONDecodeError:
            return JsonResponse({"error": "choices must be valid JSON"}, status=400)

    if not isinstance(raw_choices, list):
        return JsonResponse({"error": "choices must be a list"}, status=400)

    try:
        parsed_choices = [_parse_choice_payload(story, item, index) for index, item in enumerate(raw_choices)]
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    with transaction.atomic():
        scene = Scene.objects.create(
            story=story,
            title=title,
            content=content,
            background_image_url=background_image_url,
            is_starting=is_starting,
            is_ending=is_ending,
        )

        Choice.objects.bulk_create(
            [
                Choice(
                    scene=scene,
                    text=item["text"],
                    target_scene_id=item["target_scene_id"],
                    conditions=item["conditions"],
                    effects=item["effects"],
                )
                for item in parsed_choices
            ]
        )

    return JsonResponse(
        {
            "id": scene.id,
            "title": scene.title,
            "content": scene.content,
            "background_image_url": scene.background_image_url,
            "is_starting": scene.is_starting,
            "is_ending": scene.is_ending,
            "choices_count": len(parsed_choices),
            "message": "Scene created.",
        },
        status=201,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser])
def update_story_scene(request, story_id, scene_id):
    story, error_response = _get_owned_story(request.user.id, story_id)
    if error_response:
        return error_response

    scene = story.scenes.filter(pk=scene_id).first()
    if not scene:
        return JsonResponse({"error": "Scene not found"}, status=404)

    title = request.data.get("title")
    if title is None:
        title = scene.title
    else:
        title = title.strip()

    content = request.data.get("content")
    if content is None:
        content = scene.content
    else:
        content = content.strip()

    background_image_url = request.data.get("background_image_url")
    if background_image_url is None:
        background_image_url = scene.background_image_url
    else:
        background_image_url = background_image_url.strip()


    is_ending = request.data.get("is_ending")
    if is_ending is None:
        is_ending = scene.is_ending
    else:
        is_ending = bool(is_ending)

    is_starting = request.data.get("is_starting")
    if is_starting is None:
        is_starting = scene.is_starting
    else:
        is_starting = bool(is_starting)

    parsed_choices = None
    raw_choices = request.data.get("choices")
    if raw_choices is not None:
        if isinstance(raw_choices, str):
            try:
                raw_choices = json.loads(raw_choices)
            except json.JSONDecodeError:
                return JsonResponse({"error": "choices must be valid JSON"}, status=400)

        if not isinstance(raw_choices, list):
            return JsonResponse({"error": "choices must be a list"}, status=400)

        try:
            parsed_choices = [_parse_choice_payload(story, item, index) for index, item in enumerate(raw_choices)]
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

    with transaction.atomic():
        scene.title = title
        scene.content = content
        scene.background_image_url = background_image_url
        scene.is_ending = is_ending
        scene.is_starting = is_starting
        scene.save(update_fields=["title", "content", "background_image_url", "is_ending", "is_starting"])

        if parsed_choices is not None:
            scene.choices.all().delete()
            Choice.objects.bulk_create(
                [
                    Choice(
                        scene=scene,
                        text=item["text"],
                        target_scene_id=item["target_scene_id"],
                        conditions=item["conditions"],
                        effects=item["effects"],
                    )
                    for item in parsed_choices
                ]
            )

    return JsonResponse(
        {
            "id": scene.id,
            "title": scene.title,
            "content": scene.content,
            "background_image_url": scene.background_image_url,
            "is_starting": scene.is_starting,
            "is_ending": scene.is_ending,
            "choices_count": scene.choices.count(),
            "message": "Scene updated.",
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_story_scene(request, story_id, scene_id):
    story, error_response = _get_owned_story(request.user.id, story_id)
    if error_response:
        return error_response

    scene = story.scenes.filter(pk=scene_id).first()
    if not scene:
        return JsonResponse({"error": "Scene not found"}, status=404)

    scene.delete()
    return JsonResponse({"message": "Scene deleted."})
