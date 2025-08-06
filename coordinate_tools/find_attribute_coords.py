#!/usr/bin/env python3
"""
Interactive coordinate finder for the attribute boxes
Click on each attribute number to find the correct coordinates
"""

import cv2
import numpy as np
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.common import load_yaml, override_cfg, is_mac
from src.utils.global_var import WINDOW_WORKING_SIZE
if is_mac():
    from src.input.GameWindowCapturorForMac import GameWindowCapturor
else:
    from src.input.GameWindowCapturor import GameWindowCapturor

def find_attribute_coordinates():
    print("=== Attribute Coordinate Finder ===")
    print("This tool will help you find the correct attribute box coordinates.")
    print()
    
    # Load config
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    
    # Start capture
    capture = GameWindowCapturor(cfg)
    time.sleep(1)
    
    # Store coordinates for each attribute
    attribute_coords = {}
    attributes = ["STR", "DEX", "INT", "LUK"]
    current_attr_index = 0
    
    # Mouse callback function
    def mouse_callback(event, x, y, flags, param):
        nonlocal current_attr_index
        if event == cv2.EVENT_LBUTTONDOWN and current_attr_index < len(attributes):
            attr_name = attributes[current_attr_index]
            attribute_coords[attr_name] = (x, y)
            print(f"Clicked {attr_name} at working frame coordinates: ({x}, {y})")
            current_attr_index += 1
    
    print("Instructions:")
    print("1. A window showing your game will appear")
    print("2. Click on EACH attribute number in this order:")
    for i, attr in enumerate(attributes, 1):
        print(f"   {i}. {attr} (Strength)")
    print("3. Click exactly on the CENTER of each number")
    print("4. Press 'q' to quit when done")
    print()
    print("Starting attribute coordinate finder...")
    
    cv2.namedWindow("Click on Attributes - Find Coordinates", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Click on Attributes - Find Coordinates", mouse_callback)
    
    while True:
        frame = capture.get_frame()
        if frame is None:
            continue
            
        # Resize to working size like AutoDiceRoller does
        working_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
        
        # Draw crosshairs for clicked coordinates
        display_frame = working_frame.copy()
        for i, (attr_name, coords) in enumerate(attribute_coords.items()):
            x, y = coords
            # Draw crosshairs
            cv2.line(display_frame, (x-15, y), (x+15, y), (0, 255, 0), 2)
            cv2.line(display_frame, (x, y-15), (x, y+15), (0, 255, 0), 2)
            cv2.circle(display_frame, (x, y), 3, (0, 255, 0), -1)
            
            # Add text
            cv2.putText(display_frame, f"{attr_name}: ({x}, {y})", (x+20, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Show current instruction
        if current_attr_index < len(attributes):
            current_attr = attributes[current_attr_index]
            instruction_text = f"Click on {current_attr} number"
            cv2.putText(display_frame, instruction_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        else:
            cv2.putText(display_frame, "All done! Press 'q' to quit", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        cv2.putText(display_frame, "Press 'q' to quit", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Click on Attributes - Find Coordinates", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or current_attr_index >= len(attributes):
            break
    
    cv2.destroyAllWindows()
    capture.stop()
    
    if len(attribute_coords) == len(attributes):
        print(f"\\n✅ SUCCESS! All attribute coordinates found:")
        for attr_name, coords in attribute_coords.items():
            print(f"{attr_name}: {coords}")
        
        # Calculate intervals
        if len(attribute_coords) >= 2:
            str_y = attribute_coords["STR"][1]
            dex_y = attribute_coords["DEX"][1]
            y_interval = dex_y - str_y
            print(f"\\nY interval between attributes: {y_interval}")
        
        print(f"\\nTo use these coordinates, replace this section in AutoDiceRoller.py:")
        print(f"    base_first_box = (890, 371)")
        print(f"    box_y_interval = 25")
        print(f"With:")
        print(f"    base_first_box = {attribute_coords['STR']}")
        if len(attribute_coords) >= 2:
            print(f"    box_y_interval = {y_interval}")
    else:
        print(f"\\n❌ Only found {len(attribute_coords)}/{len(attributes)} coordinates.")
        print("Please make sure to click on all attribute numbers!")

if __name__ == "__main__":
    find_attribute_coordinates()
