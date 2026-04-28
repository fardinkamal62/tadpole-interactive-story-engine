from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.shortcuts import render, get_object_or_404
import json
import time

from .story_logic import StoryState, Scene, Choice
from apps.story.models import Story as StoryModel

# A simple sample story
SCENES_DATA: dict[int, Scene] = {
    0: Scene(
        scene_id=0,
        background="/static/house_entrance.jpg",
        choices=[
            Choice(1, "Enter the house", 1,
                  effects={}),
            Choice(2, "Don't enter, go to the barn", 3,
                  effects={})
        ]
    ),
    1: Scene(
        scene_id=1,
        background="/static/inside_house.jpg",
        choices=[
            Choice(3, "Trust the friend", 2,
                  effects={"trust": 10, "security": 10}),
            Choice(4, "Don't trust them, go outside", 3,
                  effects={})
        ]
    ),
    2: Scene(
        scene_id=2,
        background="/static/with_friend.jpg",
        choices=[
            Choice(5, "Gift him my watch", 5,
                  effects={"trust": 20}),
            Choice(6, "Don't gift the watch", 5,
                  effects={})
        ]
    ),
    3: Scene(
        scene_id=3,
        background="/static/barn.jpg",
        choices=[
            Choice(7, "Sleep in the barn", 6,
                  effects={"trust": -5, "security": -10})
        ]
    ),
    4: Scene(
        scene_id=4,
        background="/static/outside.jpg",
        choices=[]
    ),
    5: Scene(
        scene_id=5,
        background="/static/friend_room.jpg",
        choices=[
            Choice(8, "Continue...", 7,
                  conditions={"trust": 30, "security": 10}),
            Choice(9, "Continue...", 8,
                  conditions={})
        ]
    ),
    6: Scene(
        scene_id=6,
        background="/static/barn_ending.jpg",
        choices=[]
    ),
    7: Scene(
        scene_id=7,
        background="/static/separate_bed.jpg",
        choices=[]
    ),
    8: Scene(
        scene_id=8,
        background="/static/couch.jpg",
        choices=[]
    )
}

STORY_DATA = {
    "attributes": ["trust", "security"],
    "scenes": SCENES_DATA
}

@ensure_csrf_cookie
def start_story(request):
    """Initialize a new story session and return the first scene"""
    initial_state = StoryState(story_id=0, current_scene_id=0)
    request.session['game_state'] = initial_state.__dict__

    current_scene = SCENES_DATA[int(initial_state.current_scene_id)]
    return build_scene_response(request, current_scene, initial_state.variables)

@ensure_csrf_cookie
def process_choice(request):
    """POST endpoint - processes player choice and returns next scene"""
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)

    # Get current state from session
    state_dict = request.session.get('game_state')
    if not isinstance(state_dict, dict):
        return JsonResponse({"error": "No active game session"}, status=400)

    assert isinstance(state_dict, dict)
    state = StoryState(**state_dict)

    # Get choice data from request
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        choice_id = int(data.get('choice_id'))
        current_scene_id = int(data.get('current_scene_id'))
    except (TypeError, ValueError):
        return JsonResponse({"error": "choice_id and current_scene_id must be integers"}, status=400)

    # Validate choice exists in current scene
    current_scene = SCENES_DATA.get(current_scene_id)
    if not current_scene:
        return JsonResponse({"error": "Invalid scene"}, status=400)

    selected_choice = next((c for c in current_scene.choices if c.id == choice_id), None)
    if not selected_choice:
        return JsonResponse({"error": "Invalid choice"}, status=400)

    # Apply effects to variables
    if len(selected_choice.effects) > 0:
        for var_name, value in selected_choice.effects.items():
            state.variables[var_name] = state.variables.get(var_name, 0) + value

    # Update state and move to next scene
    state.visited_scenes.append(current_scene_id)
    state.current_scene_id = selected_choice.target_scene_id
    request.session['game_state'] = state.__dict__

    # Check if story ends
    next_scene = SCENES_DATA.get(state.current_scene_id)
    if not next_scene:
        return JsonResponse({"error": "Invalid next scene"}, status=400)
    assert next_scene is not None
    if len(next_scene.choices) == 0:
        return JsonResponse({
            "ending": True,
            "message": "The story concludes here.",
            "final_variables": state.variables,
            "path": state.visited_scenes
        })

    return build_scene_response(request, next_scene, state.variables)

# Helper functions
def build_scene_response(request, scene: Scene, variables: dict[str, int]):
    """Build a JSON response for a scene with filtered choices"""
    available_choices = get_available_choices(scene, variables)

    return JsonResponse({
        "csrf_token": get_token(request),
        "scene": {
            "id": scene.id,
            "background": scene.background,
            "choices": available_choices
        },
        "variables": variables
    })

def get_available_choices(scene: Scene, variables: dict[str, int]):
    """Get filtered list of available choices based on conditions"""
    available_choices = []
    for choice in scene.choices:
        is_available = check_conditions(choice.conditions, variables)
        available_choices.append({
            "id": choice.id,
            "text": choice.text,
            "available": is_available
        })

    # For conditional flow scenes, show only the first matching choice
    if len(available_choices) > 1 and has_conditional_flow(scene.choices):
        for i, choice in enumerate(scene.choices):
            if check_conditions(choice.conditions, variables):
                return [available_choices[i]]
        # No conditional choices matched, return the fallback (last choice)
        return [available_choices[-1]]

    return available_choices

def check_conditions(conditions, variables):
    """Evaluate if all conditions are met with current variables"""
    for var_name, required_value in conditions.items():
        if variables.get(var_name, 0) < required_value:
            return False
    return True

def has_conditional_flow(choices):
    """Check if scene has conditional flow pattern (conditional choice followed by fallback)"""
    return len(choices) >= 2 and choices[0].conditions and not choices[-1].conditions

def home_page(request):
    """Simple home page view"""
    context = {'timestamp': int(time.time())}
    response = render(request, 'home_page.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def login_page(request):
    """Render the login page"""
    context = {'timestamp': int(time.time())}
    response = render(request, 'login_page.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def story_list_page(request):
    """Render the list of available stories."""
    is_mine = request.GET.get('mine') == 'true'
    if is_mine and request.user.is_authenticated:
        stories = StoryModel.objects.filter(owner=request.user).order_by("title")
    else:
        stories = StoryModel.objects.all().order_by("title")
    context = {
        "timestamp": int(time.time()),
        "stories": stories,
        "is_mine": is_mine,
    }
    response = render(request, "story_list.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def create_story_page(request):
    """Render the creator page for starting story creation."""
    context = {
        "timestamp": int(time.time()),
        "page_mode": "create",
        "story_form_data": None,
    }
    response = render(request, "create_story_page.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def story_edit_page(request, story_id):
    """Render the creator page in edit mode for an existing story."""
    story = get_object_or_404(StoryModel.objects.prefetch_related("attributes"), pk=story_id)
    context = {
        "timestamp": int(time.time()),
        "page_mode": "edit",
        "story_form_data": {
            "story_id": story.id,
            "title": story.title,
            "description": story.description,
            "background_music_url": story.background_music_url,
            "attributes": [
                {
                    "key": attribute.key,
                    "label": attribute.label,
                    "initial_value": attribute.initial_value,
                }
                for attribute in story.attributes.all()
            ],
        },
    }
    response = render(request, "create_story_page.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def story_scene_editor_page(request, story_id):
    """Render scene editor page for a story."""
    story = get_object_or_404(StoryModel, pk=story_id)
    context = {
        "timestamp": int(time.time()),
        "story_editor_data": {
            "story_id": story.id,
            "title": story.title,
        },
    }
    response = render(request, "scene_editor_page.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def story_play_page(request, story_id):
    """Render the story play page for a specific story."""
    try:
        story = StoryModel.objects.get(pk=story_id)
    except StoryModel.DoesNotExist:
        context = {"timestamp": int(time.time()), "story_id": story_id}
        response = render(request, "story_not_found.html", context, status=404)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response

    context = {"timestamp": int(time.time())}
    response = render(request, "story_page.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

