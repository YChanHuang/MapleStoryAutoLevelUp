#!/usr/bin/env python3
"""
Automatic attribute coordinate discovery
Scans the screen to find attribute numbers and suggests correct coordinates
"""

import cv2
import numpy as np
import time
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.common import load_yaml, override_cfg, is_mac, load_image
from src.utils.global_var import WINDOW_WORKING_SIZE
from src.utils.logger import logger

if is_mac():
    from src.input.GameWindowCapturorForMac import GameWindowCapturor
else:
    from src.input.GameWindowCapturor import GameWindowCapturor

def discover_attribute_coordinates():
    print("=== Automatic Attribute Coordinate Discovery ===")
    print("This will scan your game window to find attribute numbers")
    
    # Load config
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    try:
        cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    except:
        print("Using default config")
    
    # Load number templates
    print("Loading number templates...")
    img_numbers = []
    for i in range(4, 14):
        try:
            img = load_image(f"numbers/{i}.png", cv2.IMREAD_GRAYSCALE)
            img_numbers.append((i, img))
            print(f"✅ Loaded template for number {i}")
        except:
            print(f"❌ Failed to load template for number {i}")
    
    if not img_numbers:
        print("❌ No number templates found! Make sure numbers/ directory exists.")
        return
    
    # Start capture
    print("Starting game window capture...")
    capture = GameWindowCapturor(cfg)
    time.sleep(2)
    
    # Capture frame
    print("Capturing frame...")
    frame = None
    for i in range(10):  # Try multiple times
        frame = capture.get_frame()
        if frame is not None:
            break
        time.sleep(0.5)
    
    if frame is None:
        print("❌ Could not capture game frame. Make sure game window is active.")
        return
    
    # Resize to working size
    working_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
    gray_frame = cv2.cvtColor(working_frame, cv2.COLOR_BGR2GRAY)
    
    print(f"📏 Frame size: {working_frame.shape}")
    print(f"📏 Gray frame size: {gray_frame.shape}")
    
    # Save the frame for reference
    cv2.imwrite('debug_discovery_frame.png', working_frame)
    cv2.imwrite('debug_discovery_gray.png', gray_frame)
    print("💾 Saved debug frames: debug_discovery_frame.png, debug_discovery_gray.png")
    
    # Find all number matches
    print("\\n🔍 Scanning for numbers...")
    all_matches = []
    
    for number, template in img_numbers:
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.6)  # Lower threshold
        
        template_h, template_w = template.shape
        
        for pt in zip(*locations[::-1]):  # Switch x,y
            x, y = pt[0] + template_w//2, pt[1] + template_h//2
            confidence = result[pt[1], pt[0]]
            
            # Only consider left side of screen (attributes should be on left)
            if x < gray_frame.shape[1] * 0.7:  # Left 70% of screen
                all_matches.append((number, x, y, confidence))
                print(f"  Found {number} at ({x}, {y}) confidence: {confidence:.3f}")
    
    if not all_matches:
        print("❌ No numbers found! Try adjusting the matching threshold.")
        return
    
    # Sort matches by Y coordinate to identify STR, DEX, INT, LUK order
    all_matches.sort(key=lambda m: m[2])  # Sort by y coordinate
    
    print(f"\\n📊 Found {len(all_matches)} total matches:")
    for number, x, y, conf in all_matches:
        print(f"  {number} at ({x:3d}, {y:3d}) conf: {conf:.3f}")
    
    # Group by Y coordinate to find rows (attributes should be in vertical line)
    y_groups = {}
    y_tolerance = 10  # pixels
    
    for number, x, y, conf in all_matches:
        # Find existing group with similar Y
        found_group = False
        for group_y in y_groups.keys():
            if abs(y - group_y) <= y_tolerance:
                y_groups[group_y].append((number, x, y, conf))
                found_group = True
                break
        
        if not found_group:
            y_groups[y] = [(number, x, y, conf)]
    
    print(f"\\n🗂️  Found {len(y_groups)} Y-groups (potential attribute rows):")
    
    # Find the 4 most likely attribute positions
    attribute_candidates = []
    
    for group_y in sorted(y_groups.keys()):
        group = y_groups[group_y]
        # Take the best match from each group
        best_match = max(group, key=lambda m: m[3])  # Best confidence
        attribute_candidates.append(best_match)
        print(f"  Y={group_y:3d}: {len(group)} numbers, best = {best_match[0]} at ({best_match[1]}, {best_match[2]}) conf: {best_match[3]:.3f}")
    
    # Take top 4 candidates (should be STR, DEX, INT, LUK)
    if len(attribute_candidates) >= 4:
        top_4 = attribute_candidates[:4]
        print(f"\\n🎯 Top 4 attribute candidates:")
        
        attr_names = ["STR", "DEX", "INT", "LUK"]
        suggested_coords = []
        
        for i, (number, x, y, conf) in enumerate(top_4):
            attr_name = attr_names[i] if i < len(attr_names) else f"ATTR{i+1}"
            print(f"  {attr_name}: {number} at ({x:3d}, {y:3d}) conf: {conf:.3f}")
            suggested_coords.append((x, y))
        
        # Calculate intervals
        if len(suggested_coords) >= 2:
            y_intervals = []
            for i in range(1, len(suggested_coords)):
                interval = suggested_coords[i][1] - suggested_coords[i-1][1]
                y_intervals.append(interval)
            
            avg_interval = sum(y_intervals) / len(y_intervals)
            print(f"\\n📐 Y intervals: {y_intervals}")
            print(f"📐 Average Y interval: {avg_interval:.1f}")
            
            # Generate AutoDiceRoller coordinates
            first_coord = suggested_coords[0]
            print(f"\\n🔧 Suggested AutoDiceRoller coordinates:")
            print(f"   attr_first_box_work = {first_coord}")
            print(f"   attr_box_y_interval_work = {int(round(avg_interval))}")
            print(f"   attr_box_size_work = (22, 37)  # Keep existing box size")
            
            # Create annotated debug image
            debug_img = working_frame.copy()
            for i, (x, y) in enumerate(suggested_coords):
                attr_name = attr_names[i] if i < len(attr_names) else f"ATTR{i+1}"
                # Draw crosshairs
                cv2.line(debug_img, (x-15, y), (x+15, y), (0, 255, 0), 2)
                cv2.line(debug_img, (x, y-15), (x, y+15), (0, 255, 0), 2)
                cv2.circle(debug_img, (x, y), 3, (0, 255, 0), -1)
                # Draw rectangle (estimated box)
                box_w, box_h = 37, 22  # width, height
                p1 = (x - box_w//2, y - box_h//2)
                p2 = (x + box_w//2, y + box_h//2)
                cv2.rectangle(debug_img, p1, p2, (0, 0, 255), 1)
                # Add label
                cv2.putText(debug_img, f"{attr_name}: {suggested_coords[i]}", 
                           (x + 20, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            cv2.imwrite('debug_discovered_coordinates.png', debug_img)
            print(f"\\n💾 Saved annotated image: debug_discovered_coordinates.png")
            
    else:
        print(f"❌ Only found {len(attribute_candidates)} attribute candidates (need at least 4)")
        print("Try adjusting the game window or number templates")
    
    print("\\n✅ Discovery complete!")
    
if __name__ == "__main__":
    discover_attribute_coordinates()
