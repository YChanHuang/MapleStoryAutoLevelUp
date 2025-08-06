#!/usr/bin/env python3
"""
Debug script to check if window activity detection is working correctly
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.common import load_yaml, override_cfg, is_mac
from src.input.KeyBoardListener import KeyBoardListener

def debug_window_active():
    """Debug window activity detection"""
    print("=== Window Activity Debug ===")
    
    # Load configuration
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    
    # Create keyboard listener
    kb = KeyBoardListener(cfg, is_autobot=False)
    
    window_title = cfg["game_window"]["title"]
    print(f"Looking for window title: '{window_title}'")
    
    print("Testing window activity detection...")
    print("Make sure MapleStory Worlds is open and click on it to make it active")
    print("Press Ctrl+C to exit")
    
    try:
        for i in range(20):  # Test for 20 seconds
            is_active = kb.is_game_window_active()
            print(f"Window active: {is_active}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    
    kb.stop()

if __name__ == "__main__":
    debug_window_active()
