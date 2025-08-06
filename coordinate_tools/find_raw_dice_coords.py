#!/usr/bin/env python3
"""
Find dice coordinates on the RAW frame (not working frame)
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

def find_raw_coordinates():
    print("=== Raw Frame Dice Coordinate Finder ===")
    print("This tool will help you find dice coordinates on the RAW frame.")
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
            print(f"Clicked at RAW frame coordinates: ({x}, {y})")
    
    print("Instructions:")
    print("1. A window showing your game at FULL RESOLUTION will appear")
    print("2. Click EXACTLY on the dice button in the character creation screen")
    print("3. Press 'q' to quit when done")
    print("4. The RAW coordinates will be shown in the terminal")
    print()
    print("Starting raw coordinate finder...")
    
    cv2.namedWindow("Click on Dice - Raw Frame", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Click on Dice - Raw Frame", mouse_callback)
    
    while True:
        frame = capture.get_frame()
        if frame is None:
            continue
            
        # Use the RAW frame directly (no resizing)
        display_frame = frame.copy()
        
        # Draw crosshairs if coordinates found
        if dice_coords:
            x, y = dice_coords
            # Draw crosshairs
            cv2.line(display_frame, (x-30, y), (x+30, y), (0, 255, 0), 3)
            cv2.line(display_frame, (x, y-30), (x, y+30), (0, 255, 0), 3)
            cv2.circle(display_frame, (x, y), 8, (0, 255, 0), -1)
            
            # Add text
            cv2.putText(display_frame, f"RAW: ({x}, {y})", (x+20, y-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Show instructions on image
        cv2.putText(display_frame, "Click on the dice button (RAW FRAME)", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
        cv2.putText(display_frame, "Press 'q' to quit", (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
        cv2.putText(display_frame, f"Frame size: {frame.shape[:2]}", (20, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
        
        cv2.imshow("Click on Dice - Raw Frame", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()
    capture.stop()
    
    if dice_coords:
        print(f"\\n✅ SUCCESS! Raw dice coordinates found:")
        print(f"Raw frame coordinates: {dice_coords}")
        
        # Show what the macOS transformation would do
        mac_coords = (dice_coords[0] // 2, dice_coords[1] // 2 + 10)
        print(f"After macOS transformation: {mac_coords}")
        
        print(f"\\nTo test these coordinates, run:")
        print(f"python test_raw_dice_click.py {dice_coords[0]} {dice_coords[1]}")
    else:
        print("\\n❌ No coordinates found. Make sure to click on the dice button!")

if __name__ == "__main__":
    find_raw_coordinates()
