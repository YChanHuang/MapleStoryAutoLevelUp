#!/usr/bin/env python3
"""
FPS Configuration Optimizer
Updates configuration files to improve OpenCV processing speed based on test results.
"""

import os
import sys
import argparse
import yaml
from src.utils.logger import logger

class FPSOptimizer:
    """Optimize FPS configuration settings for better OpenCV performance"""
    
    def __init__(self, cfg_name="custom"):
        self.cfg_name = cfg_name
        self.config_path = f"config/config_{cfg_name}.yaml"
        self.backup_path = f"config/config_{cfg_name}_backup.yaml"
        
    def backup_config(self):
        """Create a backup of the current configuration"""
        try:
            if os.path.exists(self.config_path):
                import shutil
                shutil.copy2(self.config_path, self.backup_path)
                logger.info(f"✅ Backup created: {self.backup_path}")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
        return True
    
    def load_config(self):
        """Load current configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    content = f.read().strip()
                    if not content:  # Empty file
                        return {}
                    config = yaml.safe_load(content)
                    return config if config is not None else {}
            else:
                # Start with empty config (will override defaults)
                return {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def save_config(self, config):
        """Save optimized configuration"""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Ensure config is not None or empty
            if not config:
                config = {}
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
            logger.info(f"✅ Configuration saved: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            logger.error(f"Config content: {config}")
            return False
    
    def optimize_for_speed(self, target_fps=30):
        """Optimize configuration for speed"""
        logger.info(f"🚀 Optimizing configuration for {target_fps} FPS target")
        
        # Backup current config
        if not self.backup_config():
            return False
        
        # Load current config
        config = self.load_config()
        if config is None:
            return False
        
        # Initialize system section if it doesn't exist
        if 'system' not in config:
            config['system'] = {}
        
        # Apply speed optimizations
        old_values = {}
        
        # Increase window capturor FPS to 30 if system allows
        old_values['fps_limit_window_capturor'] = config['system'].get('fps_limit_window_capturor', 15)
        config['system']['fps_limit_window_capturor'] = target_fps
        
        # Keep dice roller FPS relatively low for human-like behavior, but not too slow
        old_values['fps_limit_auto_dice_roller'] = config['system'].get('fps_limit_auto_dice_roller', 0.5)
        config['system']['fps_limit_auto_dice_roller'] = max(1.0, config['system'].get('fps_limit_auto_dice_roller', 0.5))
        
        # Increase main loop FPS for better responsiveness  
        old_values['fps_limit_main'] = config['system'].get('fps_limit_main', 10)
        config['system']['fps_limit_main'] = min(30, target_fps)
        
        # Optimize health monitor FPS
        old_values['fps_limit_health_monitor'] = config.get('health_monitor', {}).get('fps_limit', 20)
        if 'health_monitor' not in config:
            config['health_monitor'] = {}
        config['health_monitor']['fps_limit'] = min(30, target_fps)
        
        # Save optimized config
        if self.save_config(config):
            logger.info("📊 Configuration optimized with the following changes:")
            logger.info(f"   Window Capturor FPS: {old_values['fps_limit_window_capturor']} → {config['system']['fps_limit_window_capturor']}")
            logger.info(f"   Auto Dice Roller FPS: {old_values['fps_limit_auto_dice_roller']} → {config['system']['fps_limit_auto_dice_roller']}")
            logger.info(f"   Main Loop FPS: {old_values['fps_limit_main']} → {config['system']['fps_limit_main']}")
            logger.info(f"   Health Monitor FPS: {old_values['fps_limit_health_monitor']} → {config['health_monitor']['fps_limit']}")
            logger.info(f"💾 Backup saved to: {self.backup_path}")
            return True
        
        return False
    
    def optimize_for_accuracy(self):
        """Optimize configuration for accuracy over speed"""
        logger.info("🎯 Optimizing configuration for accuracy")
        
        # Backup current config
        if not self.backup_config():
            return False
        
        # Load current config
        config = self.load_config()
        if config is None:
            return False
        
        # Initialize system section if it doesn't exist
        if 'system' not in config:
            config['system'] = {}
        
        # Apply accuracy optimizations
        old_values = {}
        
        # Moderate window capturor FPS for stable detection
        old_values['fps_limit_window_capturor'] = config['system'].get('fps_limit_window_capturor', 15)
        config['system']['fps_limit_window_capturor'] = 20
        
        # Slow dice roller FPS for human-like behavior and accurate detection
        old_values['fps_limit_auto_dice_roller'] = config['system'].get('fps_limit_auto_dice_roller', 0.5)
        config['system']['fps_limit_auto_dice_roller'] = 0.3
        
        # Moderate main loop FPS
        old_values['fps_limit_main'] = config['system'].get('fps_limit_main', 10)
        config['system']['fps_limit_main'] = 15
        
        # Save optimized config
        if self.save_config(config):
            logger.info("📊 Configuration optimized for accuracy:")
            logger.info(f"   Window Capturor FPS: {old_values['fps_limit_window_capturor']} → {config['system']['fps_limit_window_capturor']}")
            logger.info(f"   Auto Dice Roller FPS: {old_values['fps_limit_auto_dice_roller']} → {config['system']['fps_limit_auto_dice_roller']}")
            logger.info(f"   Main Loop FPS: {old_values['fps_limit_main']} → {config['system']['fps_limit_main']}")
            logger.info(f"💾 Backup saved to: {self.backup_path}")
            return True
        
        return False
    
    def restore_backup(self):
        """Restore from backup"""
        try:
            if os.path.exists(self.backup_path):
                import shutil
                shutil.copy2(self.backup_path, self.config_path)
                logger.info(f"✅ Configuration restored from backup")
                return True
            else:
                logger.error(f"Backup file not found: {self.backup_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Optimize FPS configuration for OpenCV performance")
    parser.add_argument(
        '--cfg',
        type=str,
        default='custom',
        help='Configuration file name (without extension)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['speed', 'accuracy', 'restore'],
        default='speed',
        help='Optimization mode: speed (30fps), accuracy (stable), or restore (from backup)'
    )
    parser.add_argument(
        '--target-fps',
        type=int,
        default=30,
        help='Target FPS for speed optimization (default: 30)'
    )
    
    args = parser.parse_args()
    
    optimizer = FPSOptimizer(args.cfg)
    
    if args.mode == 'speed':
        if optimizer.optimize_for_speed(args.target_fps):
            logger.info("🚀 Speed optimization completed!")
            logger.info("💡 Run the test again to verify improvements")
        else:
            logger.error("❌ Speed optimization failed!")
            return 1
            
    elif args.mode == 'accuracy':
        if optimizer.optimize_for_accuracy():
            logger.info("🎯 Accuracy optimization completed!")
        else:
            logger.error("❌ Accuracy optimization failed!")
            return 1
            
    elif args.mode == 'restore':
        if optimizer.restore_backup():
            logger.info("🔄 Configuration restored from backup!")
        else:
            logger.error("❌ Failed to restore from backup!")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
