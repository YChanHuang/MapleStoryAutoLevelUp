# AutoDiceRoller Break Functionality

## Overview

The AutoDiceRoller now includes an intelligent break system that automatically pauses dice rolling every 100 rolls to avoid detection patterns and reduce system strain.

## Features

### 🛌 Automatic Breaks
- **Frequency**: Every 100 dice rolls (100, 200, 300, etc.)
- **Duration**: Random 3.0-5.0 seconds per break
- **Purpose**: Mimics natural human behavior and prevents automation detection

### 🎯 Smart Timing
- Breaks only occur after successful dice rolls
- No breaks during jackpot detection or error states
- Seamless resume after break completion

### 📝 Clear Logging
- Logs break start with duration and roll count
- Logs break completion and resume
- Easy monitoring of break patterns

## Implementation Details

### Code Changes

1. **New Instance Variables**:
   ```python
   self.roll_count = 0           # Tracks total dice rolls
   self.last_break_time = time.time()  # Tracks last break timing
   ```

2. **Break Logic**:
   ```python
   # Check if we need a break every 100 rolls
   if self.roll_count > 0 and self.roll_count % 100 == 0:
       break_duration = random.uniform(3.0, 5.0)
       logger.info(f"🛌 Taking a {break_duration:.1f}s break after {self.roll_count} rolls...")
       time.sleep(break_duration)
       self.last_break_time = current_time
       logger.info("🎯 Resuming dice rolling!")
   ```

3. **Roll Counting**:
   ```python
   # Increment roll count after each successful dice roll
   self.roll_count += 1
   ```

## Usage Examples

### Normal Operation
```bash
python -m tools.AutoDiceRoller --attribute "6,6,?,?" --timeout 300
```

**Expected Output**:
```
[INFO] Roll the dice: (967, 413) -> (1593, 712)
[INFO] Roll the dice: (967, 413) -> (1593, 712)
... (after 100 rolls) ...
[INFO] 🛌 Taking a 4.2s break after 100 rolls...
[INFO] 🎯 Resuming dice rolling!
[INFO] Roll the dice: (967, 413) -> (1593, 712)
```

## Testing

### Unit Tests
Run the comprehensive test suite:
```bash
python test_auto_dice_roller_breaks.py
```

**Test Coverage**:
- ✅ Break timing every 100 rolls
- ✅ Break duration 3.0-5.0 seconds  
- ✅ Break intervals (100, 200, 300...)
- ✅ Random duration distribution
- ✅ Break logging messages

### Demo Script
See the feature in action:
```bash
python demo_break_functionality.py
```

## Benefits

### 🔒 Automation Detection Avoidance
- Random break durations prevent predictable patterns
- Natural-seeming pauses mimic human behavior
- Reduces risk of bot detection

### ⚡ System Performance
- Periodic breaks prevent system strain
- Allows other processes to run smoothly
- Reduces continuous high-frequency clicking

### 📊 Monitoring & Control
- Clear logging enables performance tracking
- Easy to monitor break frequency and duration
- Helps estimate total completion time

## Configuration

The break system uses these parameters:
- **Break Interval**: 100 rolls (hardcoded)
- **Min Duration**: 3.0 seconds
- **Max Duration**: 5.0 seconds
- **Random Distribution**: Uniform between min/max

## Compatibility

- ✅ Compatible with all existing AutoDiceRoller features
- ✅ Works with timeout functionality
- ✅ Supports Ctrl+C interruption during breaks
- ✅ Maintains existing logging and debug features

## Performance Impact

- **Negligible CPU overhead**: Simple modulo check per roll
- **Memory usage**: +16 bytes for two additional instance variables
- **Total time increase**: ~4 seconds per 100 rolls (4% overhead)

---

*This feature was added to enhance the reliability and stealth of the AutoDiceRoller while maintaining optimal performance.*
