#!/usr/bin/env python3
"""
Demonstration of the AutoDiceRoller break functionality.
This script simulates the break behavior without requiring the actual game.
"""

import time
import random

class DiceRollerBreakDemo:
    """Demo class to showcase the break functionality"""
    
    def __init__(self):
        self.roll_count = 0
        self.last_break_time = time.time()
        
    def simulate_dice_roll(self):
        """Simulate a dice roll with break logic"""
        
        # Check if we need a break every 100 rolls
        if self.roll_count > 0 and self.roll_count % 100 == 0:
            break_duration = random.uniform(3.0, 5.0)
            print(f"🛌 Taking a {break_duration:.1f}s break after {self.roll_count} rolls...")
            
            # Simulate the break (in real demo, we'd actually sleep)
            # time.sleep(break_duration)
            print(f"   [Simulated {break_duration:.1f}s sleep]")
            
            self.last_break_time = time.time()
            print("🎯 Resuming dice rolling!")
            print()
        
        # Simulate dice roll
        print(f"Roll #{self.roll_count + 1}: STR={random.randint(4,13)}, DEX={random.randint(4,13)}, INT={random.randint(4,13)}, LUK={random.randint(4,13)}")
        
        self.roll_count += 1
        
        # Small delay to make it visible
        time.sleep(0.1)

def main():
    """Demonstrate the break functionality"""
    print("=" * 60)
    print("AutoDiceRoller Break Functionality Demonstration")
    print("=" * 60)
    print("This demo shows breaks occurring every 100 rolls")
    print("(Break durations are simulated for speed)")
    print()
    
    demo = DiceRollerBreakDemo()
    
    # Simulate rolling dice, with breaks at 100, 200, 300
    target_rolls = 250
    
    print(f"Simulating {target_rolls} dice rolls...")
    print()
    
    for i in range(target_rolls):
        demo.simulate_dice_roll()
        
        # Show progress for large batches
        if (i + 1) % 50 == 0:
            print(f"--- Progress: {i + 1}/{target_rolls} rolls ---")
            print()
    
    print("=" * 60)
    print("Demo completed!")
    print(f"Total rolls: {demo.roll_count}")
    print(f"Breaks taken: {demo.roll_count // 100}")
    print("=" * 60)
    print()
    print("Key Features Demonstrated:")
    print("✅ Automatic breaks every 100 rolls")
    print("✅ Random break duration (3.0-5.0 seconds)")
    print("✅ Clear logging of break events")  
    print("✅ Seamless resume after breaks")

if __name__ == "__main__":
    main()
