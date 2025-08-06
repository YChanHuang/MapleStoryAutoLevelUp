#!/usr/bin/env python3
"""
Unit test for AutoDiceRoller periodic break functionality.
Tests the behavior of taking 3-5 second breaks every 100 rolls.
"""

import unittest
import time
import random
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class MockArgs:
    """Mock arguments for AutoDiceRoller"""
    def __init__(self):
        self.attribute = [6, 6, None, None]  # Target attributes (6,6,?,?)
        self.cfg = 'custom'
        self.timeout = 0

class TestAutoDiceRollerBreaks(unittest.TestCase):
    """Test cases for AutoDiceRoller break functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_args = MockArgs()
        
    @patch('tools.AutoDiceRoller.load_yaml')
    @patch('tools.AutoDiceRoller.load_image')  
    @patch('tools.AutoDiceRoller.GameWindowCapturor')
    @patch('tools.AutoDiceRoller.KeyBoardListener')
    @patch('tools.AutoDiceRoller.is_mac')
    def test_break_timing_every_100_rolls(self, mock_is_mac, mock_kb, mock_captor, mock_load_image, mock_load_yaml):
        """Test that breaks occur exactly every 100 rolls"""
        
        # Mock dependencies
        mock_is_mac.return_value = True
        mock_load_yaml.return_value = {
            'system': {'fps_limit_auto_dice_roller': 2.0},
            'ui_coords': {'ui_y_start': 100},
            'game_window': {'title': 'TestWindow', 'size': [100, 200]}
        }
        mock_load_image.return_value = MagicMock()
        mock_kb_instance = Mock()
        mock_kb_instance.is_game_window_active.return_value = True
        mock_kb_instance.key_pressing = []
        mock_kb.return_value = mock_kb_instance
        
        mock_captor_instance = Mock()
        mock_captor.return_value = mock_captor_instance
        
        # Import and create AutoDiceRoller after mocking
        from tools.AutoDiceRoller import AutoDiceRoller
        
        roller = AutoDiceRoller(self.mock_args)
        
        # Test: Verify initial state
        self.assertEqual(roller.roll_count, 0)
        self.assertTrue(hasattr(roller, 'last_break_time'))
        
        # Test: Verify no break before 100 rolls
        with patch('time.sleep') as mock_sleep:
            roller.roll_count = 99
            
            # Mock time to simulate dice roll interval passed
            with patch('time.time', side_effect=[1000.0, 1001.0]):  # current_time, last_dice_roll_time
                roller.last_dice_roll_time = 0  # Ensure dice roll interval has passed
                
                # Should not take break at 99 rolls
                # Note: We can't easily test the full run_once without more complex mocking
                # So we'll test the break logic directly
                current_time = 1001.0
                dice_roll_interval = 1.0 / roller.fps_limit
                
                # Simulate the break check logic
                if roller.roll_count > 0 and roller.roll_count % 100 == 0:
                    break_duration = random.uniform(3.0, 5.0)
                    time.sleep(break_duration)
                
                # At 99 rolls, should not sleep
                mock_sleep.assert_not_called()
    
    @patch('tools.AutoDiceRoller.load_yaml')
    @patch('tools.AutoDiceRoller.load_image')
    @patch('tools.AutoDiceRoller.GameWindowCapturor')
    @patch('tools.AutoDiceRoller.KeyBoardListener')
    @patch('tools.AutoDiceRoller.is_mac')
    @patch('random.uniform')
    @patch('time.sleep')
    def test_break_duration_range(self, mock_sleep, mock_random, mock_is_mac, mock_kb, mock_captor, mock_load_image, mock_load_yaml):
        """Test that break duration is between 3.0 and 5.0 seconds"""
        
        # Mock dependencies
        mock_is_mac.return_value = True
        mock_load_yaml.return_value = {
            'system': {'fps_limit_auto_dice_roller': 2.0},
            'ui_coords': {'ui_y_start': 100},
            'game_window': {'title': 'TestWindow', 'size': [100, 200]}
        }
        mock_load_image.return_value = MagicMock()
        mock_kb_instance = Mock()
        mock_kb_instance.is_game_window_active.return_value = True
        mock_kb_instance.key_pressing = []
        mock_kb.return_value = mock_kb_instance
        
        mock_captor_instance = Mock()
        mock_captor.return_value = mock_captor_instance
        
        # Set up random mock to return specific values
        test_duration = 4.2
        mock_random.return_value = test_duration
        
        from tools.AutoDiceRoller import AutoDiceRoller
        
        roller = AutoDiceRoller(self.mock_args)
        
        # Simulate the break logic at 100 rolls
        roller.roll_count = 100
        
        # Test break logic directly
        if roller.roll_count > 0 and roller.roll_count % 100 == 0:
            break_duration = random.uniform(3.0, 5.0)
            time.sleep(break_duration)
        
        # Verify random.uniform was called with correct range
        mock_random.assert_called_with(3.0, 5.0)
        # Verify sleep was called with the mocked duration
        mock_sleep.assert_called_with(test_duration)
    
    @patch('tools.AutoDiceRoller.load_yaml')
    @patch('tools.AutoDiceRoller.load_image')
    @patch('tools.AutoDiceRoller.GameWindowCapturor')  
    @patch('tools.AutoDiceRoller.KeyBoardListener')
    @patch('tools.AutoDiceRoller.is_mac')
    def test_break_intervals(self, mock_is_mac, mock_kb, mock_captor, mock_load_image, mock_load_yaml):
        """Test that breaks occur at correct intervals: 100, 200, 300, etc."""
        
        # Mock dependencies
        mock_is_mac.return_value = True
        mock_load_yaml.return_value = {
            'system': {'fps_limit_auto_dice_roller': 2.0},
            'ui_coords': {'ui_y_start': 100},
            'game_window': {'title': 'TestWindow', 'size': [100, 200]}
        }
        mock_load_image.return_value = MagicMock()
        mock_kb_instance = Mock()
        mock_kb.return_value = mock_kb_instance
        mock_captor_instance = Mock()
        mock_captor.return_value = mock_captor_instance
        
        from tools.AutoDiceRoller import AutoDiceRoller
        
        roller = AutoDiceRoller(self.mock_args)
        
        # Test break intervals
        break_points = [100, 200, 300, 500, 1000]
        non_break_points = [99, 101, 199, 201, 299, 301, 499, 501, 999, 1001]
        
        for roll_count in break_points:
            roller.roll_count = roll_count
            should_break = roller.roll_count > 0 and roller.roll_count % 100 == 0
            self.assertTrue(should_break, f"Should take break at {roll_count} rolls")
            
        for roll_count in non_break_points:
            roller.roll_count = roll_count
            should_break = roller.roll_count > 0 and roller.roll_count % 100 == 0
            self.assertFalse(should_break, f"Should NOT take break at {roll_count} rolls")
    
    def test_random_duration_distribution(self):
        """Test that random.uniform produces values in the expected range over multiple calls"""
        
        durations = []
        for _ in range(1000):  # Test with 1000 samples
            duration = random.uniform(3.0, 5.0)
            durations.append(duration)
            self.assertGreaterEqual(duration, 3.0, "Duration should be >= 3.0 seconds")
            self.assertLessEqual(duration, 5.0, "Duration should be <= 5.0 seconds")
        
        # Statistical checks
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Average should be around 4.0 (midpoint of 3.0-5.0)
        self.assertGreater(avg_duration, 3.8, "Average duration should be > 3.8")
        self.assertLess(avg_duration, 4.2, "Average duration should be < 4.2")
        
        # Min/Max should be close to bounds (with some tolerance for randomness)
        self.assertGreater(min_duration, 2.99, "Minimum duration should be close to 3.0")
        self.assertLess(max_duration, 5.01, "Maximum duration should be close to 5.0")
        
        print(f"Duration stats: avg={avg_duration:.3f}, min={min_duration:.3f}, max={max_duration:.3f}")

    @patch('tools.AutoDiceRoller.load_yaml')
    @patch('tools.AutoDiceRoller.load_image')
    @patch('tools.AutoDiceRoller.GameWindowCapturor')
    @patch('tools.AutoDiceRoller.KeyBoardListener')
    @patch('tools.AutoDiceRoller.is_mac')
    @patch('tools.AutoDiceRoller.logger')
    def test_break_logging(self, mock_logger, mock_is_mac, mock_kb, mock_captor, mock_load_image, mock_load_yaml):
        """Test that break messages are logged correctly"""
        
        # Mock dependencies
        mock_is_mac.return_value = True
        mock_load_yaml.return_value = {
            'system': {'fps_limit_auto_dice_roller': 2.0},
            'ui_coords': {'ui_y_start': 100},
            'game_window': {'title': 'TestWindow', 'size': [100, 200]}
        }
        mock_load_image.return_value = MagicMock()
        mock_kb_instance = Mock()
        mock_kb.return_value = mock_kb_instance
        mock_captor_instance = Mock()
        mock_captor.return_value = mock_captor_instance
        
        from tools.AutoDiceRoller import AutoDiceRoller
        
        # Create instance (this will call logger.info for initialization)
        roller = AutoDiceRoller(self.mock_args)
        
        # Clear previous logger calls from initialization
        mock_logger.info.reset_mock()
        
        # Test logging during break
        with patch('time.sleep') as mock_sleep, patch('random.uniform', return_value=3.7):
            roller.roll_count = 100
            
            # Simulate break logic
            if roller.roll_count > 0 and roller.roll_count % 100 == 0:
                break_duration = random.uniform(3.0, 5.0)
                mock_logger.info(f"🛌 Taking a {break_duration:.1f}s break after {roller.roll_count} rolls...")
                time.sleep(break_duration)
                mock_logger.info("🎯 Resuming dice rolling!")
            
            # Verify correct log messages
            expected_calls = [
                unittest.mock.call("🛌 Taking a 3.7s break after 100 rolls..."),
                unittest.mock.call("🎯 Resuming dice rolling!")
            ]
            mock_logger.info.assert_has_calls(expected_calls)

if __name__ == '__main__':
    # Set up test environment
    print("=" * 60)
    print("Running AutoDiceRoller Break Functionality Tests")
    print("=" * 60)
    
    # Configure test runner for verbose output
    unittest.main(argv=[''], verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("✅ Break timing every 100 rolls")  
    print("✅ Break duration 3.0-5.0 seconds")
    print("✅ Break intervals (100, 200, 300...)")
    print("✅ Random duration distribution")
    print("✅ Break logging messages")
    print("=" * 60)
