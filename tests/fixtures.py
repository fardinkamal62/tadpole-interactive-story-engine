"""
Test fixtures and sample data for tests
"""
from backend.story_logic import Scene, Choice


def create_test_story():
    """Create a simple test story for testing purposes"""
    return {
        "attributes": ["trust", "courage"],
        "scenes": {
            0: Scene(
                scene_id=0,
                background="/static/start.jpg",
                choices=[
                    Choice(1, "Go left", 1, effects={"trust": 5}),
                    Choice(2, "Go right", 2, effects={"courage": 5})
                ]
            ),
            1: Scene(
                scene_id=1,
                background="/static/left.jpg",
                choices=[
                    Choice(3, "Continue", 3, effects={"trust": 10})
                ]
            ),
            2: Scene(
                scene_id=2,
                background="/static/right.jpg",
                choices=[
                    Choice(4, "Continue", 3, effects={"courage": 10})
                ]
            ),
            3: Scene(
                scene_id=3,
                background="/static/end.jpg",
                choices=[]  # Ending scene
            )
        }
    }


def create_conditional_story():
    """Create a story with conditional choices for testing"""
    return {
        "attributes": ["trust"],
        "scenes": {
            0: Scene(
                scene_id=0,
                background="/static/start.jpg",
                choices=[
                    Choice(1, "Build trust", 1, effects={"trust": 30})
                ]
            ),
            1: Scene(
                scene_id=1,
                background="/static/choice.jpg",
                choices=[
                    Choice(2, "High trust path", 2, conditions={"trust": 30}),
                    Choice(3, "Low trust path", 3, conditions={})
                ]
            ),
            2: Scene(
                scene_id=2,
                background="/static/high_trust.jpg",
                choices=[]
            ),
            3: Scene(
                scene_id=3,
                background="/static/low_trust.jpg",
                choices=[]
            )
        }
    }


def create_empty_story():
    """Create an empty story for edge case testing"""
    return {
        "attributes": [],
        "scenes": {
            0: Scene(
                scene_id=0,
                background="/static/only.jpg",
                choices=[]
            )
        }
    }
