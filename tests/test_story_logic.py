"""
Unit tests for story_logic models (StoryState, Scene, Choice)
"""
import unittest
from backend.story_logic import StoryState, Scene, Choice


class TestStoryState(unittest.TestCase):
    """Test cases for StoryState class"""
    
    def test_initialization_defaults(self):
        """Test StoryState initializes with default values"""
        state = StoryState(story_id=1, current_scene_id=0)
        
        self.assertEqual(state.story_id, 1)
        self.assertEqual(state.current_scene_id, 0)
        self.assertEqual(state.variables, {})
        self.assertEqual(state.visited_scenes, [])
    
    def test_initialization_with_custom_values(self):
        """Test StoryState initializes with custom values"""
        variables = {"trust": 10, "security": 5}
        visited = [0, 1, 2]
        
        state = StoryState(
            story_id=2,
            current_scene_id=3,
            variables=variables,
            visited_scenes=visited
        )
        
        self.assertEqual(state.story_id, 2)
        self.assertEqual(state.current_scene_id, 3)
        self.assertEqual(state.variables, variables)
        self.assertEqual(state.visited_scenes, visited)
    
    def test_variables_mutable(self):
        """Test that variables can be modified"""
        state = StoryState(story_id=1, current_scene_id=0)
        state.variables["trust"] = 10
        
        self.assertEqual(state.variables["trust"], 10)
    
    def test_visited_scenes_mutable(self):
        """Test that visited_scenes can be appended"""
        state = StoryState(story_id=1, current_scene_id=0)
        state.visited_scenes.append(0)
        state.visited_scenes.append(1)
        
        self.assertEqual(len(state.visited_scenes), 2)
        self.assertIn(0, state.visited_scenes)
        self.assertIn(1, state.visited_scenes)


class TestScene(unittest.TestCase):
    """Test cases for Scene class"""
    
    def test_initialization_minimal(self):
        """Test Scene initializes with minimal parameters"""
        scene = Scene(scene_id=1, background="/static/bg.jpg", choices=[])
        
        self.assertEqual(scene.id, 1)
        self.assertEqual(scene.background, "/static/bg.jpg")
        self.assertEqual(scene.choices, [])
        self.assertEqual(scene.conditions, {})
    
    def test_initialization_with_choices(self):
        """Test Scene initializes with choices"""
        choice = Choice(1, "Test choice", 2)
        scene = Scene(scene_id=1, background="/static/bg.jpg", choices=[choice])
        
        self.assertEqual(len(scene.choices), 1)
        self.assertEqual(scene.choices[0].text, "Test choice")
    
    def test_initialization_with_conditions(self):
        """Test Scene initializes with conditions"""
        conditions = {"trust": 10}
        scene = Scene(
            scene_id=1,
            background="/static/bg.jpg",
            choices=[],
            conditions=conditions
        )
        
        self.assertEqual(scene.conditions, conditions)
    
    def test_empty_choices_default(self):
        """Test that choices defaults to empty list"""
        scene = Scene(scene_id=1, background="/static/bg.jpg", choices=None)
        
        self.assertEqual(scene.choices, [])


class TestChoice(unittest.TestCase):
    """Test cases for Choice class"""
    
    def test_initialization_minimal(self):
        """Test Choice initializes with minimal parameters"""
        choice = Choice(1, "Go forward", 2)
        
        self.assertEqual(choice.id, 1)
        self.assertEqual(choice.text, "Go forward")
        self.assertEqual(choice.target_scene_id, 2)
        self.assertEqual(choice.conditions, {})
        self.assertEqual(choice.effects, {})
    
    def test_initialization_with_conditions(self):
        """Test Choice initializes with conditions"""
        conditions = {"trust": 10, "security": 5}
        choice = Choice(1, "Trust them", 2, conditions=conditions)
        
        self.assertEqual(choice.conditions, conditions)
    
    def test_initialization_with_effects(self):
        """Test Choice initializes with effects"""
        effects = {"trust": 10, "security": -5}
        choice = Choice(1, "Help friend", 2, effects=effects)
        
        self.assertEqual(choice.effects, effects)
    
    def test_initialization_with_conditions_and_effects(self):
        """Test Choice initializes with both conditions and effects"""
        conditions = {"trust": 5}
        effects = {"trust": 10}
        choice = Choice(
            1,
            "Deep trust",
            2,
            conditions=conditions,
            effects=effects
        )
        
        self.assertEqual(choice.conditions, conditions)
        self.assertEqual(choice.effects, effects)
    
    def test_conditions_default_empty_dict(self):
        """Test that conditions defaults to empty dict"""
        choice = Choice(1, "Test", 2, conditions=None)
        
        self.assertEqual(choice.conditions, {})
    
    def test_effects_default_empty_dict(self):
        """Test that effects defaults to empty dict"""
        choice = Choice(1, "Test", 2, effects=None)
        
        self.assertEqual(choice.effects, {})


if __name__ == '__main__':
    unittest.main()
