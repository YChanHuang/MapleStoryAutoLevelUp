#!/usr/bin/env python3
"""
Debug version of AutoDiceRoller with detailed logging
"""

import time
import argparse
import sys
import numpy as np
import cv2

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.global_var import WINDOW_WORKING_SIZE
from src.utils.logger import logger
from src.utils.common import (
    find_pattern_sqdiff, screenshot, load_image,
    is_mac, override_cfg, load_yaml, click_in_game_window,
)
if is_mac():
    from src.input.GameWindowCapturorForMac import GameWindowCapturor
else:
    from src.input.GameWindowCapturor import GameWindowCapturor
from src.input.KeyBoardListener import KeyBoardListener

def parse_and_validate_attributes(attr_str):
    raw_values = attr_str.split(',')
    if len(raw_values) != 4:
        raise argparse.ArgumentTypeError("You must provide exactly 4 attributes: STR,DEX,INT,LUK")

    parsed = []
    total_known = 0
    unknown_count = 0

    for v in raw_values:
        if v.strip() == '?':
            parsed.append(None)
            unknown_count += 1
        else:
            try:
                val = int(v)
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid attribute value: {v}")
            if not (4 <= val <= 13):
                raise argparse.ArgumentTypeError("Each attribute must be between 4 and 13.")
            parsed.append(val)
            total_known += val

    if unknown_count > 0 and (total_known > 25 or total_known + 4 * unknown_count > 25):
        raise argparse.ArgumentTypeError("Impossible to satisfy sum of 25 with current values.")

    return parsed

def debug_auto_dice_roller():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attribute', type=parse_and_validate_attributes, default=[4, 4, 13, 4])
    parser.add_argument('--cfg', type=str, default='custom')
    parser.add_argument('--timeout', type=int, default=10)
    args = parser.parse_args()
    
    print("=== DEBUG AUTO DICE ROLLER ===")
    print(f"Target attributes: {args.attribute}")
    print(f"Timeout: {args.timeout} seconds")
    
    # Load config
    cfg = load_yaml("config/config_default.yaml")
    if is_mac():
        cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
    cfg = override_cfg(cfg, load_yaml("config/config_custom.yaml"))
    
    # Load number templates
    img_numbers = [
        load_image(f"numbers/{i}.png", cv2.IMREAD_GRAYSCALE)
        for i in range(4, 14)
    ]
    
    # Start keyboard listener and capture
    kb = KeyBoardListener(cfg, is_autobot=False)
    capture = GameWindowCapturor(cfg)
    
    # Dice coordinates (corrected from coordinate finder)
    loc_dice = (967, 413)
    
    # Attribute box coordinates
    loc_first_box = (890, 371)
    box_size = (22, 37)
    box_y_interval = 25
    
    window_title = cfg["game_window"]["title"]
    start_time = time.time()
    frame_count = 0
    click_count = 0
    last_attributes = [None, None, None, None]
    
    print("\\nStarting debug dice rolling...")
    print("Press 'q' to quit manually")
    
    cv2.namedWindow("Debug Dice Rolling", cv2.WINDOW_NORMAL)
    
    try:
        while True:
            frame_count += 1
            
            # Get frame
            frame = capture.get_frame()
            if frame is None:
                logger.warning("Failed to capture frame")
                continue
            
            # Resize to working frame
            img_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
            img_frame_gray = cv2.cvtColor(img_frame, cv2.COLOR_BGR2GRAY)
            img_frame_debug = img_frame.copy()
            
            # Check if game window is active
            is_window_active = kb.is_game_window_active()
            
            # Read current attributes
            current_attributes = []
            for i, attribute_name in enumerate(["STR", "DEX", "INT", "LUK"]):
                p0 = (loc_first_box[0], loc_first_box[1] + i * box_y_interval)
                p1 = (p0[0] + box_size[1], p0[1] + box_size[0])
                
                img_roi = img_frame_gray[p0[1]:p1[1], p0[0]:p1[0]]
                
                best_score = float('inf')
                best_digit = None
                for idx, img_number in enumerate(img_numbers, start=4):
                    _, score, _ = find_pattern_sqdiff(img_roi, img_number)
                    if score < best_score:
                        best_score = score
                        best_digit = idx
                        
                current_attributes.append(best_digit)
                
                # Draw box on debug image
                cv2.rectangle(img_frame_debug, p0, p1, (0, 255, 0), 2)
                cv2.putText(img_frame_debug, f"{attribute_name}:{best_digit}", 
                           (p0[0], p0[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw dice location on debug image
            cv2.circle(img_frame_debug, loc_dice, 10, (0, 0, 255), 3)
            cv2.putText(img_frame_debug, "DICE", (loc_dice[0] + 15, loc_dice[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Check if attributes changed from last time
            if current_attributes != last_attributes:
                print(f"\\n[Frame {frame_count}] ATTRIBUTES CHANGED!")
                print(f"  Previous: {last_attributes}")
                print(f"  Current:  {current_attributes}")
                last_attributes = current_attributes.copy()
            
            # Add debug info to image
            debug_text = [
                f"Frame: {frame_count}, Clicks: {click_count}",
                f"Window Active: {is_window_active}",
                f"Target: {args.attribute}",
                f"Current: {current_attributes}",
                f"Time: {time.time() - start_time:.1f}s"
            ]
            
            for i, text in enumerate(debug_text):
                y_pos = 30 + i * 25
                cv2.putText(img_frame_debug, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Check if we hit the target
            is_jackpot = True
            for i, (current, target) in enumerate(zip(current_attributes, args.attribute)):
                if target is not None and target != current:
                    is_jackpot = False
                    break
            
            if is_jackpot:
                print(f"\\n🎉 JACKPOT! Target reached: {current_attributes}")
                break
            
            # Click dice if window is active and we haven't reached target
            if is_window_active:
                # Calculate scaled coordinates
                raw_height, raw_width = frame.shape[:2]
                work_height, work_width = img_frame.shape[:2]
                scale_x = raw_width / work_width
                scale_y = raw_height / work_height
                loc_dice_scaled = (int(loc_dice[0] * scale_x), int(loc_dice[1] * scale_y))
                
                print(f"[Frame {frame_count}] Clicking dice: {loc_dice} -> {loc_dice_scaled}")
                click_in_game_window(window_title, loc_dice_scaled)
                click_count += 1
                
                # Wait a bit after click
                time.sleep(0.5)
            else:
                print(f"[Frame {frame_count}] Window not active, skipping click")
            
            # Show debug image
            cv2.imshow("Debug Dice Rolling", img_frame_debug)
            
            # Check for exit conditions
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\\nManual quit (q pressed)")
                break
                
            if args.timeout > 0 and (time.time() - start_time) > args.timeout:
                print(f"\\nTimeout reached ({args.timeout}s)")
                break
                
            # Limit FPS
            time.sleep(0.2)  # ~5 FPS for debugging
            
    except KeyboardInterrupt:
        print("\\nInterrupted by user")
    finally:
        cv2.destroyAllWindows()
        capture.stop()
        kb.stop()
        
    print(f"\\nDebug session complete:")
    print(f"  Total frames: {frame_count}")
    print(f"  Total clicks: {click_count}")
    print(f"  Final attributes: {current_attributes}")
    print(f"  Target attributes: {args.attribute}")

if __name__ == "__main__":
    debug_auto_dice_roller()
