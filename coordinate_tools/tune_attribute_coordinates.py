#!/usr/bin/env python3
"""
Interactive Attribute Coordinate Tuner for AutoDiceRoller

This tool helps you visually adjust the attribute box coordinates 
until they accurately capture the attribute numbers.

Usage:
    python tune_attribute_coordinates.py

Controls:
    Arrow keys: Move the first attribute box
    Shift + Arrow keys: Adjust box size
    Space: Save current coordinates and update AutoDiceRoller.py
    ESC/Q: Quit without saving
    R: Reset to original coordinates
"""

import cv2
import numpy as np
import time
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tools.AutoDiceRoller import AutoDiceRoller

class AttributeCoordinateTuner:
    def __init__(self):
        # Initialize AutoDiceRoller to get current coordinates
        args = argparse.Namespace()
        args.attribute = [4,4,13,4]
        args.cfg = 'custom'
        args.timeout = 0
        
        self.roller = AutoDiceRoller(args)
        
        # Current coordinates (working frame) - using precise coordinates
        self.attr_precise_coords = [list(coord) for coord in self.roller.attr_precise_coords]  # Make it mutable
        self.attr_box_size_work = list(self.roller.attr_box_size_work)  # Make it mutable
        
        # Original coordinates for reset
        self.original_coords = {
            'precise_coords': [tuple(coord) for coord in self.roller.attr_precise_coords],
            'box_size': tuple(self.roller.attr_box_size_work)
        }
        
        # Step sizes for adjustment
        self.move_step = 1
        self.size_step = 1
        
        print("=== Attribute Coordinate Tuner ===")
        print("Current coordinates:")
        print(f"  First box: {self.attr_first_box_work}")
        print(f"  Y interval: {self.attr_box_y_interval_work}")
        print(f"  Box size: {self.attr_box_size_work}")
        print("\nControls:")
        print("  Arrow keys: Move first box position")
        print("  Shift + Arrow keys: Adjust box size")
        print("  +/- keys: Adjust Y interval between boxes")
        print("  Space: Save coordinates and update AutoDiceRoller.py")
        print("  R: Reset to original coordinates")  
        print("  ESC/Q: Quit without saving")
        print("\nStarting tuner... Click on the game window first!")
        
    def get_current_frame(self):
        """Get current game frame"""
        self.roller.run_once()
        return self.roller.img_frame.copy() if self.roller.img_frame is not None else None
        
    def draw_attribute_boxes(self, img):
        """Draw the current attribute box positions on the image"""
        for i, attr_name in enumerate(["STR", "DEX", "INT", "LUK"]):
            # Calculate box position
            p0 = (self.attr_first_box_work[0], 
                  self.attr_first_box_work[1] + i * self.attr_box_y_interval_work)
            p1 = (p0[0] + self.attr_box_size_work[1], 
                  p0[1] + self.attr_box_size_work[0])
            
            # Ensure coordinates are within bounds
            p0 = (max(0, p0[0]), max(0, p0[1]))
            p1 = (min(img.shape[1], p1[0]), min(img.shape[0], p1[1]))
            
            # Draw rectangle
            color = (0, 255, 0) if i == 0 else (0, 0, 255)  # Green for first, red for others
            thickness = 2 if i == 0 else 1
            cv2.rectangle(img, p0, p1, color, thickness)
            
            # Draw label
            label_pos = (p0[0] - 40, p0[1] + 15)
            cv2.putText(img, attr_name, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, color, 1, cv2.LINE_AA)
            
            # Show coordinates for first box
            if i == 0:
                coord_text = f"({p0[0]},{p0[1]}) {self.attr_box_size_work[1]}x{self.attr_box_size_work[0]}"
                cv2.putText(img, coord_text, (p0[0], p0[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1, cv2.LINE_AA)
        
        return img
        
    def save_coordinates(self):
        """Save the current coordinates to AutoDiceRoller.py"""
        # Read the current file
        file_path = "/Users/jamesh/my_dev/MapleStoryAutoLevelUp/tools/AutoDiceRoller.py"
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find and replace the coordinate lines
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'self.attr_first_box_work =' in line:
                lines[i] = f"        self.attr_first_box_work = {tuple(self.attr_first_box_work)}"
            elif 'self.attr_box_y_interval_work =' in line:
                lines[i] = f"        self.attr_box_y_interval_work = {self.attr_box_y_interval_work}"
            elif 'self.attr_box_size_work =' in line:
                lines[i] = f"        self.attr_box_size_work = {tuple(self.attr_box_size_work)}  # (h, w) in working frame"
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✅ Coordinates saved to {file_path}:")
        print(f"   attr_first_box_work = {tuple(self.attr_first_box_work)}")
        print(f"   attr_box_y_interval_work = {self.attr_box_y_interval_work}")
        print(f"   attr_box_size_work = {tuple(self.attr_box_size_work)}")
        
    def reset_coordinates(self):
        """Reset coordinates to original values"""
        self.attr_first_box_work = list(self.original_coords['first_box'])
        self.attr_box_y_interval_work = self.original_coords['y_interval']
        self.attr_box_size_work = list(self.original_coords['box_size'])
        print("🔄 Coordinates reset to original values")
        
    def run(self):
        """Main tuning loop"""
        cv2.namedWindow("Attribute Coordinate Tuner", cv2.WINDOW_NORMAL)
        
        while True:
            # Get current frame
            frame = self.get_current_frame()
            if frame is None:
                print("Could not capture frame. Make sure game window is active.")
                time.sleep(0.1)
                continue
            
            # Draw attribute boxes
            display_frame = self.draw_attribute_boxes(frame.copy())
            
            # Add instruction text
            instructions = [
                "Arrow keys: Move position | Shift+Arrow: Size | +/-: Y interval",
                "SPACE: Save | R: Reset | ESC/Q: Quit",
                f"Pos: {self.attr_first_box_work} | Size: {self.attr_box_size_work} | Y-gap: {self.attr_box_y_interval_work}"
            ]
            
            for i, instruction in enumerate(instructions):
                y_pos = 30 + i * 20
                cv2.putText(display_frame, instruction, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.imshow("Attribute Coordinate Tuner", display_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(30) & 0xFF
            shift_pressed = key >= 65 and key <= 90  # Capital letters indicate shift
            
            if key == 27 or key == ord('q') or key == ord('Q'):  # ESC or Q
                print("Exiting without saving...")
                break
            elif key == ord(' '):  # Space - Save
                self.save_coordinates()
                print("Coordinates saved! You can now test the AutoDiceRoller.")
                break
            elif key == ord('r') or key == ord('R'):  # Reset
                self.reset_coordinates()
            elif key == ord('+') or key == ord('='):  # Increase Y interval
                self.attr_box_y_interval_work += 1
                print(f"Y interval: {self.attr_box_y_interval_work}")
            elif key == ord('-') or key == ord('_'):  # Decrease Y interval
                self.attr_box_y_interval_work = max(1, self.attr_box_y_interval_work - 1)
                print(f"Y interval: {self.attr_box_y_interval_work}")
            # Arrow keys - move or resize
            elif key == 82 or key == 0:  # Up arrow
                if shift_pressed:
                    self.attr_box_size_work[0] += self.size_step  # Height
                else:
                    self.attr_first_box_work[1] -= self.move_step  # Y position
            elif key == 84 or key == 1:  # Down arrow  
                if shift_pressed:
                    self.attr_box_size_work[0] = max(1, self.attr_box_size_work[0] - self.size_step)
                else:
                    self.attr_first_box_work[1] += self.move_step
            elif key == 81 or key == 2:  # Left arrow
                if shift_pressed:
                    self.attr_box_size_work[1] = max(1, self.attr_box_size_work[1] - self.size_step)  # Width
                else:
                    self.attr_first_box_work[0] -= self.move_step  # X position
            elif key == 83 or key == 3:  # Right arrow
                if shift_pressed:
                    self.attr_box_size_work[1] += self.size_step
                else:
                    self.attr_first_box_work[0] += self.move_step
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    tuner = AttributeCoordinateTuner()
    tuner.run()
