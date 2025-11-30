"""
Example usage script for the Occupancy Meter System
Demonstrates how to use the system programmatically
"""

from occupancy_detector import OccupancyMeter
import time


def main():
    """Example usage of the Occupancy Meter System"""
    
    print("="*60)
    print("Occupancy Meter System - Example Usage")
    print("="*60)
    print()
    
    # Initialize the system with configuration file
    print("Initializing Occupancy Meter System...")
    meter = OccupancyMeter(config_path="config.yaml")
    
    print("\nConfiguration loaded:")
    print(f"  Room: {meter.config['room']['identifier']}")
    print(f"  MQTT Broker: {meter.config['mqtt']['broker_host']}:{meter.config['mqtt']['broker_port']}")
    print(f"  Topic Prefix: {meter.config['mqtt']['topic_prefix']}")
    print(f"  Model: {meter.config['detection']['model_path']}")
    print(f"  Device: {meter.config['detection']['device']}")
    print(f"  Time Window: {meter.config['averaging']['time_window_seconds']} seconds")
    print()
    
    # Run the system
    print("Starting occupancy detection...")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        meter.run()
    except KeyboardInterrupt:
        print("\nStopped by user")


if __name__ == "__main__":
    main()

