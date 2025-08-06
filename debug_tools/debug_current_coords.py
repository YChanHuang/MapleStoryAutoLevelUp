#!/usr/bin/env python3
"""
Quick debug to save screenshot with current coordinates
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

def debug_current_coords():
    print("=== Debug Current Coordinates ===")
    
    # Current coordinates from AutoDiceRoller
    attr_first_box_work = (892, 354)
    attr_box_y_interval_work = 23
    attr_box_size_work = (22, 37)  # (h, w)
    
    # Load config and capture
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    try:
        cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    except:
        pass
    
    capture = GameWindowCapturor(cfg)
    time.sleep(1)
    
    frame = capture.get_frame()
    if frame is None:
        print("❌ Could not capture frame")
        return
        
    working_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
    
    print(f"📏 Working frame size: {working_frame.shape}")
    print(f"📍 Current coordinates being used:")
    print(f"   First box: {attr_first_box_work}")
    print(f"   Y interval: {attr_box_y_interval_work}")
    print(f"   Box size: {attr_box_size_work}")
    
    # Draw the current boxes
    debug_img = working_frame.copy()
    
    for i, attr_name in enumerate(["STR", "DEX", "INT", "LUK"]):
        # Calculate box position (same logic as AutoDiceRoller)
        p0 = (attr_first_box_work[0], attr_first_box_work[1] + i * attr_box_y_interval_work)
        p1 = (p0[0] + attr_box_size_work[1], p0[1] + attr_box_size_work[0])
        
        print(f"   {attr_name}: p0={p0}, p1={p1}")
        
        # Draw rectangle
        color = (0, 255, 0) if i == 0 else (0, 0, 255)  # Green for STR, red for others
        cv2.rectangle(debug_img, p0, p1, color, 2)
        
        # Draw center point
        center = (p0[0] + attr_box_size_work[1]//2, p0[1] + attr_box_size_work[0]//2)
        cv2.circle(debug_img, center, 3, color, -1)
        
        # Add label
        cv2.putText(debug_img, f"{attr_name}: {p0}", (p0[0] - 80, p0[1] + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # Create debug_images directory if it doesn't exist
    import os
    debug_dir = "debug_images"
    os.makedirs(debug_dir, exist_ok=True)
    
    # Save the debug image
    cv2.imwrite(os.path.join(debug_dir, 'debug_current_coordinate_boxes.png'), debug_img)
    print(f"\\n💾 Saved debug image: {debug_dir}/debug_current_coordinate_boxes.png")
    print("Please check this image to see if the boxes are positioned correctly over the attribute numbers")

if __name__ == "__main__":
    debug_current_coords()
