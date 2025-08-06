'''
Execute this script:
python AutoDiceRoller.py --attribute 4,4,13,4 --cfg XXX
'''
# Standard import
import time
import argparse
import sys
import signal
import random

# Library import
import numpy as np
import cv2
import pyautogui

# Disable PyAutoGUI fail-safe to prevent crash when mouse goes to corner
pyautogui.FAILSAFE = False

# Local import
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
# macOS window info
if is_mac():
    import Quartz

class AutoDiceRoller:
    '''
    AutoDiceRoller
    '''
    def __init__(self, args):
        '''
        Init AutoDiceRoller
        '''
        # self.cfg = Config # Configuration
        self.args = args # User arguments
        self.fps = 0 # Frame per second
        self.is_first_frame = True # first frame flag
        self.is_enable = True
        # Scale factors (logical pt → raw px)
        # raw/device-pixel scale
        self.scale_x = 1.0
        self.scale_y = 1.0
        # working-frame (resized) scale
        self.wscale_x = 1.0
        self.wscale_y = 1.0
        self.scale_ready = False  # set after first frame is captured
        # Working frame coordinates (already in working frame space) - Updated based on discovery
        self.loc_dice_work = (967, 413)
        # Use precise coordinates from discovery: STR(892,354), DEX(892,376), INT(893,400), LUK(893,422)
        self.attr_precise_coords = [(892, 354), (892, 376), (893, 400), (893, 422)]
        self.attr_box_size_work = (22, 37)  # (h, w) in working frame
        # Cached positions to avoid erratic jumping
        self.cached_dice_pos = None
        self.cached_attr_positions = None
        # Images
        self.frame = None # raw image
        self.img_frame = None # game window frame
        self.img_frame_gray = None # game window frame graysale
        self.img_frame_debug = None # game window frame for visualization
        self.img_route = None # route map
        self.img_route_debug = None # route map for visualization
        self.img_minimap = np.zeros((10, 10, 3), dtype=np.uint8) # minimap on game screen
        # Timers
        self.t_last_frame = time.time() # Last frame timer, for fps calculation
        
        # Roll counting for periodic breaks
        self.roll_count = 0
        self.last_break_time = time.time()

        # Load defautl yaml config
        cfg = load_yaml("config/config_default.yaml")
        # Override with platform config
        if is_mac():
            cfg = override_cfg(cfg, load_yaml("config/config_macOS.yaml"))
        # Override with user customized config
        self.cfg = override_cfg(cfg, load_yaml(f"config/config_{args.cfg}.yaml"))

        # Set up fps limits
        self.fps_limit = self.cfg["system"]["fps_limit_auto_dice_roller"]  # For dice rolling actions
        self.visual_fps_limit = 15.0  # For visual updates (15 FPS for smooth display)
        self.last_dice_roll_time = 0  # Track when we last rolled dice

        # Load number image
        self.img_numbers = [
            load_image(f"numbers/{i}.png", cv2.IMREAD_GRAYSCALE)
            for i in range(4, 14)
        ]

        # Start keyboard listener thread
        self.kb = KeyBoardListener(self.cfg, is_autobot=False)

        # Start game window capturing thread
        logger.info("Waiting for game window to activate, please click on game window")
        self.capture = GameWindowCapturor(self.cfg)

    def find_dice_automatically(self):
        '''
        Find dice button using template matching with number templates
        Returns (x, y) coordinates if found, None otherwise
        '''
        try:
            # Use the "4" template to find dice button (it often shows "4" initially)
            template = self.img_numbers[0]  # "4" template
            
            # Try template matching on grayscale
            result = cv2.matchTemplate(self.img_frame_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            # If we found a good match
            if max_val > 0.7:  # High confidence threshold
                template_h, template_w = template.shape
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                
                # Check if it's in the expected dice area (right side of screen)
                img_height, img_width = self.img_frame.shape[:2]
                if center_x > img_width * 0.6:  # Right side of screen
                    logger.info(f"[DICE] Auto-detected dice at work coords ({center_x}, {center_y}) confidence: {max_val:.3f}")
                    return (center_x, center_y)
            
            return None
        except Exception as e:
            logger.warning(f"[find_dice_automatically] Error: {e}")
            return None
    
    def find_attribute_numbers(self):
        '''
        Use template matching to find all attribute numbers automatically
        Returns list of [(x,y), (x,y), (x,y), (x,y)] for STR,DEX,INT,LUK or None if not found
        '''
        try:
            attribute_positions = []
            
            # Search for each number template in the left portion of the screen
            for template in self.img_numbers:  # Templates for numbers 4-13
                result = cv2.matchTemplate(self.img_frame_gray, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= 0.6)  # Lower threshold for attribute detection
                
                template_h, template_w = template.shape
                
                for pt in zip(*locations[::-1]):  # Switch x,y
                    x, y = pt[0] + template_w//2, pt[1] + template_h//2
                    
                    # Only consider left side of screen (attributes are on the left)
                    if x < self.img_frame.shape[1] * 0.8:  # Left 80% of screen
                        attribute_positions.append((x, y, result[pt[1], pt[0]]))
            
            if not attribute_positions:
                return None
                
            # Sort by Y coordinate (top to bottom) to get STR, DEX, INT, LUK order
            attribute_positions.sort(key=lambda pos: pos[1])
            
            # Take the 4 topmost positions (assuming STR, DEX, INT, LUK)
            if len(attribute_positions) >= 4:
                final_positions = [(pos[0], pos[1]) for pos in attribute_positions[:4]]
                logger.info(f"[ATTRS] Auto-detected attribute positions: {final_positions}")
                return final_positions
            
            return None
            
        except Exception as e:
            logger.warning(f"[find_attribute_numbers] Error: {e}")
            return None

    def update_img_frame_debug(self):
        '''
        update_img_frame_debug
        '''
        cv2.imshow("Game Window Debug",
            self.img_frame_debug[:self.cfg["ui_coords"]["ui_y_start"], :])
        # Update FPS timer
        self.t_last_frame = time.time()

    # ----------------------------
    # Utilities for scaling
    # ----------------------------
    def _update_scale_factor(self, raw_w, raw_h):
        """Compute pt→px scale using Quartz logical window size"""
        if not is_mac() or self.scale_ready:
            return
        # get logical bounds
        try:
            opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
            wins = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID)
            title = self.cfg["game_window"]["title"]
            for w in wins:
                if w.get(Quartz.kCGWindowName, '') == title:
                    bounds = w[Quartz.kCGWindowBounds]
                    log_w = int(bounds['Width'])
                    log_h = int(bounds['Height'])
                    self.scale_x = raw_w / log_w
                    self.scale_y = raw_h / log_h
                    logger.info(f"[SCALE] logical=({log_w},{log_h}) raw=({raw_w},{raw_h}) → scale=({self.scale_x:.2f},{self.scale_y:.2f})")
                    # compute working-frame scale as well (after we know WINDOW_WORKING_SIZE)
                    self.wscale_x = WINDOW_WORKING_SIZE[0] / log_w  # [0] = width = 1296
                    self.wscale_y = WINDOW_WORKING_SIZE[1] / log_h  # [1] = height = 700
                    self.scale_ready = True
                    return
        except Exception as e:
            logger.warning(f"[SCALE] Cannot compute scale factor: {e}")
            self.scale_ready = True  # prevent retry endless

    def _pt2raw(self, pt):
        return int(pt[0]*self.scale_x), int(pt[1]*self.scale_y)
    def _pt2work(self, pt):
        return int(pt[0]*self.wscale_x), int(pt[1]*self.wscale_y)
    
    def save_debug_screenshots(self):
        """Save debug screenshots with dice and attribute regions marked"""
        if self.img_frame is None or self.img_frame_gray is None:
            logger.warning("No frame to save")
            return
            
        # Create debug_images directory if it doesn't exist
        import os
        debug_dir = "debug_images"
        os.makedirs(debug_dir, exist_ok=True)
            
        # Use working frame coordinates directly
        loc_dice_work = self.loc_dice_work
        
        # Create annotated debug image
        debug_img = self.img_frame.copy()
        
        # Mark dice location with a circle
        cv2.circle(debug_img, loc_dice_work, 20, (0, 255, 0), 2)  # Green circle
        cv2.putText(debug_img, "DICE", (loc_dice_work[0]-20, loc_dice_work[1]-25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Mark attribute boxes using precise coordinates
        for i, attr_name in enumerate(["STR", "DEX", "INT", "LUK"]):
            center_x, center_y = self.attr_precise_coords[i]
            # Create box around the center point
            p0 = (center_x - self.attr_box_size_work[1]//2, center_y - self.attr_box_size_work[0]//2)
            p1 = (center_x + self.attr_box_size_work[1]//2, center_y + self.attr_box_size_work[0]//2)
            
            # Ensure coordinates are within bounds
            p0 = (max(0, p0[0]), max(0, p0[1]))
            p1 = (min(debug_img.shape[1], p1[0]), min(debug_img.shape[0], p1[1]))
            
            cv2.rectangle(debug_img, p0, p1, (255, 0, 0), 2)  # Blue rectangles
            cv2.putText(debug_img, attr_name, (p0[0]-30, p0[1]+10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Save full annotated screenshot
        timestamp = int(time.time())
        cv2.imwrite(os.path.join(debug_dir, f'debug_dice_full_{timestamp}.png'), debug_img)
        
        # Save crop around dice area (50x50 pixels)
        dice_crop_size = 50
        dice_x, dice_y = loc_dice_work
        x1 = max(0, dice_x - dice_crop_size//2)
        y1 = max(0, dice_y - dice_crop_size//2)
        x2 = min(debug_img.shape[1], dice_x + dice_crop_size//2)
        y2 = min(debug_img.shape[0], dice_y + dice_crop_size//2)
        dice_crop = debug_img[y1:y2, x1:x2]
        cv2.imwrite(os.path.join(debug_dir, f'debug_dice_crop_{timestamp}.png'), dice_crop)
        
        # Save crops of each attribute area using precise coordinates
        for i, attr_name in enumerate(["STR", "DEX", "INT", "LUK"]):
            center_x, center_y = self.attr_precise_coords[i]
            p0 = (center_x - self.attr_box_size_work[1]//2, center_y - self.attr_box_size_work[0]//2)
            p1 = (center_x + self.attr_box_size_work[1]//2, center_y + self.attr_box_size_work[0]//2)
            
            p0 = (max(0, p0[0]), max(0, p0[1]))
            p1 = (min(debug_img.shape[1], p1[0]), min(debug_img.shape[0], p1[1]))
            
            if p1[0] > p0[0] and p1[1] > p0[1]:
                attr_crop = debug_img[p0[1]:p1[1], p0[0]:p1[0]]
                cv2.imwrite(os.path.join(debug_dir, f'debug_attr_{attr_name}_{timestamp}.png'), attr_crop)
        
        logger.info(f"Debug screenshots saved to {debug_dir}/ with timestamp {timestamp}")

    def run_once(self):
        '''
        Process one game window frame
        '''
        # Get window game raw frame
        self.frame = self.capture.get_frame()
        if self.frame is None:
            logger.warning("Failed to capture game frame.")
            return

        # Make sure resolution is as expected
        if self.cfg["game_window"]["size"] != self.frame.shape[:2]:
            text = (
                f"Unexpeted window size: {self.frame.shape[:2]} "
                f"(expect {self.cfg['game_window']['size']})"
            )
            logger.error(text)
            return

        # Resize raw frame to working size
        self.img_frame = cv2.resize(self.frame, WINDOW_WORKING_SIZE,
                                    interpolation=cv2.INTER_NEAREST)

        # Grayscale game window
        self.img_frame_gray = cv2.cvtColor(self.img_frame, cv2.COLOR_BGR2GRAY)

        # Image for debug use
        self.img_frame_debug = self.img_frame.copy()

        # Enable cached location since second frame
        self.is_first_frame = False

        # Check if user want to disable dice rolling (use 'q' key in terminal instead of F1)
        # Press 'q' in the debug window to quit the program entirely
        
        # Check if need to save screenshot (use 's' key instead of F2)
        if 's' in self.kb.key_pressing:
            screenshot(self.img_frame)
            self.kb.key_pressing.remove('s')
            logger.info("Screenshot saved!")

        if self.is_enable and self.kb.is_game_window_active():
            # Debug: Log frame info
            logger.info(f"[DEBUG] Raw frame shape: {self.frame.shape}, Working frame shape: {self.img_frame.shape}")
            
            # Auto-detect coordinates based on frame size and display scaling
            raw_height, raw_width = self.frame.shape[:2]
            # make sure scale factor is ready
            self._update_scale_factor(raw_width, raw_height)
            work_height, work_width = self.img_frame.shape[:2]
            
            # Calculate scaling factor from expected to actual
            # Expected macOS size from config: [1208, 2136] 
            # optional debug
            logger.info(f"[DEBUG] Raw size: ({raw_width}, {raw_height})  scale (raw): ({self.scale_x:.2f},{self.scale_y:.2f})")
            
            window_title = self.cfg["game_window"]["title"]
            
            # Debug: Log coordinates being used
            logger.info(f"[DEBUG] Dice location work: {self.loc_dice_work}")
            logger.info(f"[DEBUG] Using precise attribute coordinates: {self.attr_precise_coords}")

            # Parse the attribute number using precise coordinates from discovery
            attibutes_info = []
            for i, attibute in enumerate(["STR", "DEX", "INT", "LUK"]):
                # Use precise coordinates directly
                center_x, center_y = self.attr_precise_coords[i]
                # Create box around the center point
                p0 = (center_x - self.attr_box_size_work[1]//2, center_y - self.attr_box_size_work[0]//2)
                p1 = (center_x + self.attr_box_size_work[1]//2, center_y + self.attr_box_size_work[0]//2)

                # Ensure coordinates are within bounds
                p0 = (max(0, p0[0]), max(0, p0[1]))
                p1 = (min(self.img_frame_gray.shape[1], p1[0]), 
                      min(self.img_frame_gray.shape[0], p1[1]))

                # Crop the box region from the image
                if p1[0] > p0[0] and p1[1] > p0[1]:  # Valid box
                    img_roi = self.img_frame_gray[p0[1]:p1[1], p0[0]:p1[0]]
                else:
                    img_roi = np.zeros((10, 10), dtype=np.uint8)  # Dummy image

                # Match with each number template (from 4 to 11)
                best_score = float('inf')
                best_digit = None
                for idx, img_number in enumerate(self.img_numbers, start=4):
                    _, score, _ = find_pattern_sqdiff(img_roi, img_number)
                    if score < best_score:
                        best_score = score
                        best_digit = idx
                logger.info(f"[{attibute}]: {best_digit} (score: {round(best_score, 2)})")
                attibutes_info.append((best_digit, best_score))

                # Draw box and put text on debug image
                cv2.rectangle(self.img_frame_debug, p0, p1, (0, 0, 255), 1)
                cv2.putText(
                    self.img_frame_debug,
                    f"{best_digit}",
                    (p0[0], p0[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA
                )

            # for val, score in attibutes_info:
            #     if score > 0.11:
            #         logger.warning(f"Stop! Unable to recognize number: {(val, score)})")
            #         self.is_enable = False

            # Check if is equal to target
            is_jackpot = True
            for i, (val, score) in enumerate(attibutes_info):
                target = self.args.attribute[i]
                if target is not None and target != val:
                    is_jackpot = False

            # Stop rolling dice if reach target
            if is_jackpot:
                self.is_enable = False
                logger.info("Hit Jackpot! Stop!")
                return  # Exit early if jackpot hit

            # Click to roll the dice or not (controlled by slower fps_limit)
            if self.is_enable:
                current_time = time.time()
                dice_roll_interval = 1.0 / self.fps_limit  # Time between dice rolls
                
                # Only roll dice if enough time has passed since last roll
                if current_time - self.last_dice_roll_time >= dice_roll_interval:
                    # Check if we need a break every 100 rolls
                    if self.roll_count > 0 and self.roll_count % 100 == 0:
                        break_duration = random.uniform(3.0, 5.0)
                        logger.info(f"🛌 Taking a {break_duration:.1f}s break after {self.roll_count} rolls...")
                        time.sleep(break_duration)
                        self.last_break_time = current_time
                        logger.info("🎯 Resuming dice rolling!")
                    
                    # Use the exact same scaling approach as debug_auto_dice_roller.py
                    scale_x_work_to_raw = raw_width / work_width
                    scale_y_work_to_raw = raw_height / work_height
                    # Use dice coordinates in working frame space directly (967, 413)
                    loc_dice_work = (967, 413)
                    dice_raw_coords = (int(loc_dice_work[0] * scale_x_work_to_raw), 
                                      int(loc_dice_work[1] * scale_y_work_to_raw))
                    
                    click_in_game_window(window_title, dice_raw_coords)
                    logger.info(f"Roll the dice: {loc_dice_work} -> {dice_raw_coords}")
                    self.last_dice_roll_time = current_time
                    self.roll_count += 1

        # Save debug screenshot with annotations if 'd' is pressed
        if 'd' in self.kb.key_pressing:
            self.kb.key_pressing.remove('d')
            self.save_debug_screenshots()
            logger.info("Debug screenshots saved!")
        
        # Show debug image on window
        self.update_img_frame_debug()

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

# Global flag for signal handling
stop_requested = False

def signal_handler(signum, frame):
    """Handle Ctrl+C signal gracefully"""
    global stop_requested
    logger.info("\n⏹️  Ctrl+C received! Stopping dice roller...")
    stop_requested = True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--attribute',
        type=parse_and_validate_attributes,
        default=[4, 4, 13, 4],
        help='Assign the attributes in order: STR,DEX,INT,LUK.'
             'Each must be between 4-13 and total must sum to 25.'
    )

    parser.add_argument(
        '--cfg',
        type=str,
        default='custom',
        help='Choose customized config yaml file in config/'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=15,
        help='Auto-stop after X seconds (default: 15, set to 0 for no timeout)'
    )

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        autoDiceRoller = AutoDiceRoller(parser.parse_args())
    except Exception as e:
        logger.error(f"AutoDiceRoller Init failed: {e}")
        sys.exit(1)
    else:
        start_time = time.time()
        timeout = autoDiceRoller.args.timeout
        
        logger.info(f"🎲 AutoDiceRoller started! Will auto-stop after {timeout}s or press Ctrl+C to stop immediately.")
        
        try:
            while not stop_requested:
                t_start = time.time()

                # Process one game window frame
                autoDiceRoller.run_once()

                # Exit if 'q' is pressed
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("'q' key pressed, stopping...")
                    break
                    
                # Auto-stop after timeout
                if timeout > 0 and (time.time() - start_time) > timeout:
                    logger.info(f"⏰ Auto-stopping after {timeout} seconds")
                    break

                # Cap FPS for visual updates (15 FPS for smooth display)
                frame_duration = time.time() - t_start
                target_duration = 1.0 / autoDiceRoller.visual_fps_limit
                if frame_duration < target_duration:
                    time.sleep(target_duration - frame_duration)
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Keyboard interrupt received!")
        
        finally:
            logger.info("🧹 Cleaning up...")
            cv2.destroyAllWindows()
            logger.info("✅ AutoDiceRoller stopped successfully!")
