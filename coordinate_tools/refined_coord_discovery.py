#!/usr/bin/env python3
"""
Refined attribute coordinate discovery - Focus on main cluster
"""

import cv2
import numpy as np
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.common import load_yaml, override_cfg, is_mac, load_image
from src.utils.global_var import WINDOW_WORKING_SIZE

if is_mac():
    from src.input.GameWindowCapturorForMac import GameWindowCapturor
else:
    from src.input.GameWindowCapturor import GameWindowCapturor

def refined_discovery():
    print("=== Refined Attribute Coordinate Discovery ===")
    
    # Load config
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    try:
        cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    except:
        pass
    
    # Load number templates
    img_numbers = []
    for i in range(4, 14):
        try:
            img = load_image(f"numbers/{i}.png", cv2.IMREAD_GRAYSCALE)
            img_numbers.append((i, img))
        except:
            pass
    
    # Capture frame
    capture = GameWindowCapturor(cfg)
    time.sleep(1)
    
    frame = capture.get_frame()
    if frame is None:
        print("❌ Could not capture frame")
        return
        
    working_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
    gray_frame = cv2.cvtColor(working_frame, cv2.COLOR_BGR2GRAY)
    
    print(f"🔍 Scanning for attribute numbers in focused region...")
    
    # Find all matches
    all_matches = []
    for number, template in img_numbers:
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.7)  # Higher threshold for better accuracy
        
        template_h, template_w = template.shape
        
        for pt in zip(*locations[::-1]):
            x, y = pt[0] + template_w//2, pt[1] + template_h//2
            confidence = result[pt[1], pt[0]]
            
            # Focus on the main cluster area (around x=890-895)
            if 880 <= x <= 910 and 300 <= y <= 500:  # Focus region
                all_matches.append((number, x, y, confidence))
    
    # Sort by Y coordinate
    all_matches.sort(key=lambda m: m[2])
    
    print(f"\\n📍 Found {len(all_matches)} matches in focused region:")
    for number, x, y, conf in all_matches:
        print(f"  {number} at ({x:3d}, {y:3d}) conf: {conf:.3f}")
    
    # Group nearby Y coordinates (within 5 pixels)
    groups = []
    used = set()
    
    for i, (number, x, y, conf) in enumerate(all_matches):
        if i in used:
            continue
        
        # Start new group
        group = [(number, x, y, conf)]
        used.add(i)
        
        # Find nearby matches
        for j, (n2, x2, y2, c2) in enumerate(all_matches[i+1:], i+1):
            if j in used:
                continue
            if abs(y - y2) <= 5:  # Within 5 pixels vertically
                group.append((n2, x2, y2, c2))
                used.add(j)
        
        groups.append(group)
    
    print(f"\\n🗂️  Grouped into {len(groups)} rows:")
    
    # Take the best match from each group
    attribute_coords = []
    for i, group in enumerate(groups):
        best = max(group, key=lambda m: m[3])  # Best confidence
        attribute_coords.append(best)
        print(f"  Row {i+1}: {len(group)} matches, best = {best[0]} at ({best[1]}, {best[2]}) conf: {best[3]:.3f}")
    
    if len(attribute_coords) >= 4:
        print(f"\\n🎯 Top 4 attributes (STR, DEX, INT, LUK):")
        top_4 = attribute_coords[:4]
        
        coords_list = []
        for i, (number, x, y, conf) in enumerate(top_4):
            attr_name = ["STR", "DEX", "INT", "LUK"][i]
            print(f"  {attr_name}: {number} at ({x}, {y}) conf: {conf:.3f}")
            coords_list.append((x, y))
        
        # Calculate intervals
        y_intervals = []
        for i in range(1, len(coords_list)):
            interval = coords_list[i][1] - coords_list[i-1][1]
            y_intervals.append(interval)
        
        avg_interval = sum(y_intervals) / len(y_intervals) if y_intervals else 23
        
        print(f"\\n📐 Y intervals: {y_intervals}")
        print(f"📐 Average Y interval: {avg_interval:.1f}")
        
        # Suggest coordinates
        first_x, first_y = coords_list[0]
        print(f"\\n🔧 CORRECTED AutoDiceRoller coordinates:")
        print(f"   attr_first_box_work = ({first_x}, {first_y})")
        print(f"   attr_box_y_interval_work = {int(round(avg_interval))}")
        print(f"   attr_box_size_work = (22, 37)")
        
        # Create debug image
        debug_img = working_frame.copy()
        for i, (x, y) in enumerate(coords_list):
            attr_name = ["STR", "DEX", "INT", "LUK"][i]
            # Draw crosshairs
            cv2.line(debug_img, (x-20, y), (x+20, y), (0, 255, 0), 2)
            cv2.line(debug_img, (x, y-20), (x, y+20), (0, 255, 0), 2)
            cv2.circle(debug_img, (x, y), 5, (0, 255, 0), -1)
            
            # Draw suggested box
            box_w, box_h = 37, 22  # width, height of detection box
            p1 = (x - box_w//2, y - box_h//2)
            p2 = (x + box_w//2, y + box_h//2)
            cv2.rectangle(debug_img, p1, p2, (255, 0, 0), 2)
            
            # Add label
            cv2.putText(debug_img, f"{attr_name}: ({x}, {y})", 
                       (x + 25, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imwrite('debug_refined_coordinates.png', debug_img)
        print(f"\\n💾 Saved annotated image: debug_refined_coordinates.png")
        
        return first_x, first_y, int(round(avg_interval))
    
    else:
        print(f"❌ Only found {len(attribute_coords)} attributes (need 4)")
        return None

if __name__ == "__main__":
    result = refined_discovery()
    if result:
        x, y, interval = result
        print(f"\\n✅ Success! Use these coordinates:")
        print(f"   attr_first_box_work = ({x}, {y})")  
        print(f"   attr_box_y_interval_work = {interval}")
