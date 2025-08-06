#!/usr/bin/env python3
"""
Interactive coordinate finder for the dice button
Click on the game window to find the correct coordinates
"""

import cv2
import numpy as np
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.common import load_yaml, override_cfg, is_mac
if is_mac():
    from src.input.GameWindowCapturorForMac import GameWindowCapturor
else:
    from src.input.GameWindowCapturor import GameWindowCapturor

def find_coordinates():
    print("=== Dice Coordinate Finder ===")
    print("This tool will help you find the correct dice coordinates.")
    print()
    
    # Load config
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    
    # Start capture
    capture = GameWindowCapturor(cfg)
    time.sleep(1)
    
    # Mouse callback function
    dice_coords = None
    def mouse_callback(event, x, y, flags, param):
        nonlocal dice_coords
        if event == cv2.EVENT_LBUTTONDOWN:
            dice_coords = (x, y)
            print(f"Clicked at working frame coordinates: ({x}, {y})")
    
    print("Instructions:")
    print("1. A window showing your game will appear")
    print("2. Click EXACTLY on the dice button in the character creation screen")
    print("3. Press 'q' to quit when done")
    print("4. The coordinates will be shown in the terminal")
    print()
    print("Starting coordinate finder...")
    
    cv2.namedWindow("Click on Dice - Find Coordinates", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Click on Dice - Find Coordinates", mouse_callback)
    
    while True:
        frame = capture.get_frame()
        if frame is None:
            continue
            
        # Resize to working size like AutoDiceRoller does
        from src.utils.global_var import WINDOW_WORKING_SIZE
        working_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
        
        # Draw crosshairs if coordinates found
        display_frame = working_frame.copy()
        if dice_coords:
            x, y = dice_coords
            # Draw crosshairs
            cv2.line(display_frame, (x-20, y), (x+20, y), (0, 255, 0), 2)
            cv2.line(display_frame, (x, y-20), (x, y+20), (0, 255, 0), 2)
            cv2.circle(display_frame, (x, y), 5, (0, 255, 0), -1)
            
            # Add text
            cv2.putText(display_frame, f"Dice: ({x}, {y})", (x+10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Show instructions on image
        cv2.putText(display_frame, "Click on the dice button", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, "Press 'q' to quit", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Click on Dice - Find Coordinates", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()
    capture.stop()
    
    if dice_coords:
        print(f"\n✅ SUCCESS! Dice coordinates found:")
        print(f"Working frame coordinates: {dice_coords}")
        print(f"\nTo use these coordinates, replace this line in AutoDiceRoller.py:")
        print(f"    loc_dice = (981, 445)")
        print(f"With:")
        print(f"    loc_dice = {dice_coords}")
        print(f"\nThen run: python -m tools.AutoDiceRoller --attribute 4,4,13,4 --timeout 10")
    else:
        print("\n❌ No coordinates found. Make sure to click on the dice button!")

if __name__ == "__main__":
    find_coordinates()
