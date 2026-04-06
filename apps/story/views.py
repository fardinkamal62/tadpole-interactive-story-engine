import json

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import Choice, PlayerState, Story


def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


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

    attributes = player_state.attributes or {}
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
                "final_attributes": _attributes_payload(player_state.story, attributes),
                "path": visited_scenes,
            }
        )

    return _build_scene_response(request, player_state.story, next_scene, attributes)
