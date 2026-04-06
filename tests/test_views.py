"""Integration tests for story API views."""
import json

from django.test import TestCase, Client
from django.urls import reverse

from apps.story.models import Story, StoryAttribute, Scene, Choice, PlayerState
from apps.story.views import _check_conditions, _get_available_choices, _has_conditional_flow


def _attributes_to_dict(attributes):
    return {item["key"]: item["value"] for item in attributes}


class StoryApiBase(TestCase):
    def setUp(self):
        self.client = Client()
        self.story = Story.objects.create(
            title="Test Story",
            description="A test story for API routes.",
        )
        StoryAttribute.objects.create(story=self.story, key="trust", label="Trust", initial_value=0)
        StoryAttribute.objects.create(story=self.story, key="security", label="Security", initial_value=0)

        self.scene_start = Scene.objects.create(
            story=self.story,
            title="Start",
            content="Start scene",
            background_image_url="",
            is_starting=True,
        )
        self.scene_house = Scene.objects.create(
            story=self.story,
            title="House",
            content="House scene",
            background_image_url="",
        )
        self.scene_conditional = Scene.objects.create(
            story=self.story,
            title="Crossroads",
            content="Conditional scene",
            background_image_url="",
        )
        self.scene_end = Scene.objects.create(
            story=self.story,
            title="Ending",
            content="End scene",
            background_image_url="",
            is_ending=True,
        )

        self.choice_to_house = Choice.objects.create(
            scene=self.scene_start,
            text="Enter the house",
            target_scene=self.scene_house,
            effects={"trust": 10},
        )
        self.choice_to_end = Choice.objects.create(
            scene=self.scene_start,
            text="Walk away",
            target_scene=self.scene_end,
            effects={"security": 5},
        )
        self.choice_to_conditional_low = Choice.objects.create(
            scene=self.scene_start,
            text="Take the shortcut",
            target_scene=self.scene_conditional,
            effects={},
        )
        self.choice_to_conditional = Choice.objects.create(
            scene=self.scene_house,
            text="Earn trust",
            target_scene=self.scene_conditional,
            effects={"trust": 20, "security": 10},
        )
        self.choice_negative = Choice.objects.create(
            scene=self.scene_house,
            text="Make a mistake",
            target_scene=self.scene_end,
            effects={"trust": -5, "security": -10},
        )

        self.choice_conditional_good = Choice.objects.create(
            scene=self.scene_conditional,
            text="High trust path",
            target_scene=self.scene_end,
            conditions={"trust": 30},
        )
        self.choice_conditional_fallback = Choice.objects.create(
            scene=self.scene_conditional,
            text="Fallback path",
            target_scene=self.scene_end,
            conditions={},
        )

        self.start_url = reverse("start_story")
        self.choice_url = reverse("process_choice")

    def start_story(self):
        return self.client.get(self.start_url, {"story_id": self.story.id})


class TestStartStoryView(StoryApiBase):
    def test_start_story_success(self):
        response = self.start_story()

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("scene", data)
        self.assertIn("attributes", data)
        self.assertIn("csrf_token", data)
        self.assertIn("story", data)

        scene = data["scene"]
        self.assertIn("id", scene)
        self.assertIn("background_image_url", scene)
        self.assertIn("choices", scene)
        self.assertEqual(scene["id"], self.scene_start.id)

        attributes = _attributes_to_dict(data["attributes"])
        self.assertEqual(attributes.get("trust"), 0)
        self.assertEqual(attributes.get("security"), 0)

    def test_start_story_creates_session(self):
        response = self.start_story()

        self.assertEqual(response.status_code, 200)
        session_key = self.client.session.session_key
        self.assertTrue(session_key)
        state = PlayerState.objects.get(story=self.story, session_key=session_key)
        self.assertEqual(state.current_scene_id, self.scene_start.id)

    def test_start_story_returns_choices(self):
        response = self.start_story()

        self.assertEqual(response.status_code, 200)
        data = response.json()

        choices = data["scene"]["choices"]
        self.assertIsInstance(choices, list)
        self.assertGreater(len(choices), 0)

        choice = choices[0]
        self.assertIn("id", choice)
        self.assertIn("text", choice)
        self.assertIn("available", choice)

    def test_start_story_sets_csrf_cookie(self):
        response = self.start_story()

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)


class TestProcessChoiceView(StoryApiBase):
    def setUp(self):
        super().setUp()
        self.start_story()

    def test_process_choice_requires_post(self):
        response = self.client.get(self.choice_url)

        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn("error", data)

    def test_process_choice_success(self):
        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_house.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scene", data)
        self.assertIn("attributes", data)
        self.assertIn("csrf_token", data)
        self.assertEqual(data["scene"]["id"], self.scene_house.id)

    def test_process_choice_applies_effects(self):
        self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_house.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_conditional.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        attributes = _attributes_to_dict(data["attributes"])
        self.assertEqual(attributes.get("trust"), 30)
        self.assertEqual(attributes.get("security"), 10)

    def test_process_choice_updates_session(self):
        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_house.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        session_key = self.client.session.session_key
        state = PlayerState.objects.get(story=self.story, session_key=session_key)
        self.assertEqual(state.current_scene_id, self.scene_house.id)
        self.assertIn(self.scene_start.id, state.visited_scenes)

    def test_process_choice_wrong_scene(self):
        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_conditional.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_process_choice_invalid_choice(self):
        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": 999999, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

    def test_process_choice_no_session(self):
        new_client = Client()
        response = new_client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_house.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_process_choice_invalid_json(self):
        response = self.client.post(
            self.choice_url,
            data="invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_process_choice_ending_scene(self):
        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_end.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("ending"))
        self.assertIn("message", data)
        self.assertIn("final_attributes", data)
        self.assertIn("path", data)

    def test_process_choice_negative_effects(self):
        self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_house.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_negative.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        attributes = _attributes_to_dict(data["final_attributes"])
        self.assertEqual(attributes.get("trust"), 5)
        self.assertEqual(attributes.get("security"), -10)


class TestConditionalChoices(StoryApiBase):
    def test_conditional_choice_available_when_conditions_met(self):
        self.start_story()
        self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_house.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_conditional.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        choices = data["scene"]["choices"]
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["id"], self.choice_conditional_good.id)
        self.assertTrue(choices[0]["available"])

    def test_conditional_choice_shows_fallback_when_not_met(self):
        self.start_story()
        response = self.client.post(
            self.choice_url,
            data=json.dumps({"choice_id": self.choice_to_conditional_low.id, "story_id": self.story.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        choices = data["scene"]["choices"]
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["id"], self.choice_conditional_fallback.id)
        self.assertTrue(choices[0]["available"])


class TestHelperFunctions(TestCase):
    def test_check_conditions_empty_conditions(self):
        result = _check_conditions({}, {"trust": 10})
        self.assertTrue(result)

    def test_check_conditions_met(self):
        conditions = {"trust": 10, "security": 5}
        variables = {"trust": 15, "security": 10}

        result = _check_conditions(conditions, variables)
        self.assertTrue(result)

    def test_check_conditions_not_met(self):
        conditions = {"trust": 20}
        variables = {"trust": 10}

        result = _check_conditions(conditions, variables)
        self.assertFalse(result)

    def test_check_conditions_missing_variable(self):
        conditions = {"trust": 10}
        variables = {}

        result = _check_conditions(conditions, variables)
        self.assertFalse(result)

    def test_has_conditional_flow_true(self):
        choices = [
            Choice(text="High trust", scene=Scene(story=Story(title="S")), target_scene=Scene(story=Story(title="T")), conditions={"trust": 30}),
            Choice(text="Low trust", scene=Scene(story=Story(title="S")), target_scene=Scene(story=Story(title="T")), conditions={}),
        ]

        result = _has_conditional_flow(choices)
        self.assertTrue(result)

    def test_has_conditional_flow_false_no_pattern(self):
        choices = [
            Choice(text="Option 1", scene=Scene(story=Story(title="S")), target_scene=Scene(story=Story(title="T")), conditions={}),
            Choice(text="Option 2", scene=Scene(story=Story(title="S")), target_scene=Scene(story=Story(title="T")), conditions={}),
        ]

        result = _has_conditional_flow(choices)
        self.assertFalse(result)

    def test_has_conditional_flow_false_single_choice(self):
        choices = [
            Choice(text="Only option", scene=Scene(story=Story(title="S")), target_scene=Scene(story=Story(title="T")), conditions={}),
        ]

        result = _has_conditional_flow(choices)
        self.assertFalse(result)

    def test_get_available_choices_filters_correctly(self):
        story = Story.objects.create(title="Logic Story")
        scene = Scene.objects.create(story=story)
        target = Scene.objects.create(story=story)
        Choice.objects.create(scene=scene, target_scene=target, text="Option 1", conditions={})
        Choice.objects.create(scene=scene, target_scene=target, text="Option 2", conditions={"trust": 10})

        result = _get_available_choices(scene, {"trust": 5})

        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]["available"])
        self.assertFalse(result[1]["available"])
