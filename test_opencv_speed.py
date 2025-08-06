#!/usr/bin/env python3
"""
OpenCV Speed Test - 20 Second Evaluation
Tests if the dice roller fails to stop when numbers are matched due to slow OpenCV processing.
Measures frame capture rate and template matching speed.
"""

import time
import argparse
import sys
import signal
import threading
from collections import deque

# Library import
import numpy as np
import cv2
import pyautogui

# Disable PyAutoGUI fail-safe
pyautogui.FAILSAFE = False

# Local import
from src.utils.global_var import WINDOW_WORKING_SIZE
from src.utils.logger import logger
from src.utils.common import (
    find_pattern_sqdiff, load_image, is_mac, 
    override_cfg, load_yaml, click_in_game_window,
)

if is_mac():
    from src.input.GameWindowCapturorForMac import GameWindowCapturor
else:
    from src.input.GameWindowCapturor import GameWindowCapturor

from src.input.KeyBoardListener import KeyBoardListener

class OpenCVSpeedTester:
    """Test OpenCV processing speed for dice detection"""
    
    def __init__(self, cfg_name="custom"):
        self.start_time = time.time()
        self.test_duration = 20.0  # 20 seconds
        
        # Performance tracking
        self.frame_times = deque(maxlen=100)
        self.processing_times = deque(maxlen=100)
        self.template_match_times = deque(maxlen=100)
        self.total_frames = 0
        self.frames_with_detection = 0
        self.successful_matches = 0
        
        # Test target attributes - known good values to test stopping
        self.test_target = [4, 4, 13, 4]  # STR, DEX, INT, LUK
        self.current_attributes = [None, None, None, None]
        self.jackpot_detected = False
        self.jackpot_detection_time = None
        self.frames_after_jackpot = 0
        
        # Load configuration
        cfg = load_yaml("config/config_default.yaml")
        if is_mac():
            cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
        self.cfg = override_cfg(cfg, load_yaml(f"config/config_{cfg_name}.yaml"))
        
        # Get FPS limits from config
        self.capture_fps = self.cfg["system"]["fps_limit_window_capturor"]
        self.dice_fps = self.cfg["system"]["fps_limit_auto_dice_roller"]
        
        logger.info(f"Config FPS limits - Capture: {self.capture_fps}, Dice: {self.dice_fps}")
        
        # Load number templates
        self.img_numbers = [
            load_image(f"numbers/{i}.png", cv2.IMREAD_GRAYSCALE)
            for i in range(4, 14)
        ]
        
        # Coordinate constants (from AutoDiceRoller)
        self.attr_precise_coords = [(892, 354), (892, 376), (893, 400), (893, 422)]
        self.attr_box_size_work = (22, 37)  # (h, w) in working frame
        
        # Initialize keyboard listener and game capture
        self.kb = KeyBoardListener(self.cfg, is_autobot=False)
        logger.info("Initializing game window capture...")
        self.capture = GameWindowCapturor(self.cfg)
        
        self.running = True
        
    def detect_numbers(self, img_frame_gray):
        """Detect attribute numbers using template matching"""
        match_start = time.time()
        
        attributes = []
        for i, attribute in enumerate(["STR", "DEX", "INT", "LUK"]):
            center_x, center_y = self.attr_precise_coords[i]
            p0 = (center_x - self.attr_box_size_work[1]//2, center_y - self.attr_box_size_work[0]//2)
            p1 = (center_x + self.attr_box_size_work[1]//2, center_y + self.attr_box_size_work[0]//2)
            
            # Ensure coordinates are within bounds
            p0 = (max(0, p0[0]), max(0, p0[1]))
            p1 = (min(img_frame_gray.shape[1], p1[0]), min(img_frame_gray.shape[0], p1[1]))
            
            if p1[0] > p0[0] and p1[1] > p0[1]:
                img_roi = img_frame_gray[p0[1]:p1[1], p0[0]:p1[0]]
                
                # Match with each number template
                best_score = float('inf')
                best_digit = None
                for idx, img_number in enumerate(self.img_numbers, start=4):
                    _, score, _ = find_pattern_sqdiff(img_roi, img_number)
                    if score < best_score:
                        best_score = score
                        best_digit = idx
                        
                attributes.append((best_digit, best_score))
            else:
                attributes.append((None, float('inf')))
        
        match_time = time.time() - match_start
        self.template_match_times.append(match_time)
        
        return attributes
    
    def check_jackpot(self, attributes):
        """Check if current attributes match the target"""
        for i, (val, score) in enumerate(attributes):
            if val != self.test_target[i]:
                return False
        return True
    
    def run_test(self):
        """Run the 20-second test"""
        logger.info(f"🚀 Starting 20-second OpenCV speed test")
        logger.info(f"Target attributes: {self.test_target}")
        logger.info(f"Capture FPS limit: {self.capture_fps}")
        logger.info(f"Dice FPS limit: {self.dice_fps}")
        
        while self.running and (time.time() - self.start_time) < self.test_duration:
            frame_start = time.time()
            
            # Get frame
            frame = self.capture.get_frame()
            if frame is None:
                continue
                
            # Resize to working size
            img_frame = cv2.resize(frame, WINDOW_WORKING_SIZE, interpolation=cv2.INTER_NEAREST)
            img_frame_gray = cv2.cvtColor(img_frame, cv2.COLOR_BGR2GRAY)
            
            processing_start = time.time()
            
            # Detect numbers
            attributes = self.detect_numbers(img_frame_gray)
            self.current_attributes = [val for val, score in attributes]
            
            processing_time = time.time() - processing_start
            self.processing_times.append(processing_time)
            
            # Check for jackpot
            is_jackpot = self.check_jackpot(attributes)
            if is_jackpot and not self.jackpot_detected:
                self.jackpot_detected = True
                self.jackpot_detection_time = time.time()
                logger.info(f"🎯 JACKPOT DETECTED at {self.jackpot_detection_time - self.start_time:.2f}s!")
                logger.info(f"Detected attributes: {self.current_attributes}")
            
            if self.jackpot_detected:
                self.frames_after_jackpot += 1
                
            # Count successful detections
            if all(val is not None for val, score in attributes):
                self.frames_with_detection += 1
                if all(score < 0.2 for val, score in attributes):  # Good quality matches
                    self.successful_matches += 1
            
            frame_time = time.time() - frame_start
            self.frame_times.append(frame_time)
            self.total_frames += 1
            
            # Log progress every 5 seconds
            elapsed = time.time() - self.start_time
            if self.total_frames % (int(self.capture_fps) * 5) == 0:
                logger.info(f"⏱️  Progress: {elapsed:.1f}s - Processed {self.total_frames} frames")
                
            # Add small delay to match capture FPS
            target_frame_time = 1.0 / self.capture_fps
            if frame_time < target_frame_time:
                time.sleep(target_frame_time - frame_time)
                
        self.print_results()
    
    def print_results(self):
        """Print test results"""
        total_time = time.time() - self.start_time
        
        logger.info("=" * 60)
        logger.info("🧪 OpenCV Speed Test Results")
        logger.info("=" * 60)
        
        logger.info(f"⏱️  Total test duration: {total_time:.2f}s")
        logger.info(f"🎬 Total frames processed: {self.total_frames}")
        logger.info(f"🎯 Frames with valid detection: {self.frames_with_detection}")
        logger.info(f"✅ High quality matches: {self.successful_matches}")
        
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            actual_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            logger.info(f"📊 Average frame time: {avg_frame_time*1000:.2f}ms")
            logger.info(f"📊 Actual processing FPS: {actual_fps:.2f}")
            logger.info(f"📊 Config capture FPS limit: {self.capture_fps}")
        
        if self.processing_times:
            avg_processing = sum(self.processing_times) / len(self.processing_times)
            logger.info(f"🔬 Average OpenCV processing time: {avg_processing*1000:.2f}ms")
        
        if self.template_match_times:
            avg_template = sum(self.template_match_times) / len(self.template_match_times)
            logger.info(f"🎯 Average template matching time: {avg_template*1000:.2f}ms")
        
        # Jackpot detection analysis
        if self.jackpot_detected:
            detection_delay = self.jackpot_detection_time - self.start_time
            logger.info(f"🎯 Jackpot detected at: {detection_delay:.2f}s")
            logger.info(f"🎬 Frames processed after jackpot: {self.frames_after_jackpot}")
            
            if self.frames_after_jackpot > 2:
                logger.warning("⚠️  ISSUE DETECTED: Script continued processing after jackpot!")
                logger.warning("⚠️  This suggests OpenCV is too slow to stop dice rolling in time.")
                logger.info("💡 Recommended solutions:")
                logger.info("   1. Increase frame capture FPS to 30 if system allows")
                logger.info("   2. Optimize template matching algorithms")
                logger.info("   3. Reduce template matching precision requirements")
            else:
                logger.info("✅ Script stopped appropriately after jackpot detection")
        else:
            logger.info("🎯 No jackpot detected during test (target not reached)")
        
        # Performance recommendations
        if self.frame_times and self.processing_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            avg_processing = sum(self.processing_times) / len(self.processing_times)
            
            if avg_processing > (avg_frame_time * 0.8):
                logger.warning("⚠️  OpenCV processing takes >80% of frame time!")
                logger.info("💡 Consider:")
                logger.info("   - Reducing template matching precision")
                logger.info("   - Using smaller ROI areas")
                logger.info("   - Implementing frame skipping")
            
            target_frame_time = 1.0 / 30.0  # 30 FPS target
            if avg_frame_time > target_frame_time:
                logger.warning(f"⚠️  Frame processing too slow for 30 FPS target")
                logger.info(f"   Current: {1.0/avg_frame_time:.1f} FPS, Target: 30 FPS")
                logger.info("💡 Increase cv2.VideoCapture polling speed to 30 FPS if system allows")
    
    def stop(self):
        """Stop the test"""
        self.running = False

# Global tester instance for signal handling
tester = None

def signal_handler(signum, frame):
    """Handle Ctrl+C signal gracefully"""
    global tester
    logger.info("\n⏹️  Ctrl+C received! Stopping test...")
    if tester:
        tester.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--cfg',
        type=str,
        default='custom',
        help='Choose customized config yaml file in config/'
    )
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        args = parser.parse_args()
        tester = OpenCVSpeedTester(args.cfg)
        tester.run_test()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted!")
    finally:
        if tester:
            logger.info("🧹 Cleaning up...")
        cv2.destroyAllWindows()
        logger.info("✅ Test completed!")
