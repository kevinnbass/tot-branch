#!/usr/bin/env python3
"""
Test script to verify Ctrl+C handling works properly.
Run this and press Ctrl+C at any time to test shutdown.
"""

import sys
import time
import signal
import threading
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the signal handler setup from main
from multi_coder_analysis.main import handle_sigint, shutdown_event


def simulate_long_running_task(task_name, duration=10):
    """Simulate a long-running task that checks for shutdown."""
    print(f"Starting {task_name}...")
    
    for i in range(duration):
        if shutdown_event.is_set():
            print(f"  {task_name}: Shutdown detected at step {i+1}/{duration}")
            return
        
        print(f"  {task_name}: Step {i+1}/{duration}")
        time.sleep(1)
    
    print(f"  {task_name}: Completed!")


def main():
    """Test the Ctrl+C handling."""
    print("=" * 60)
    print("Ctrl+C Handling Test")
    print("=" * 60)
    print("\nPress Ctrl+C at any time to test shutdown...")
    print("This simulates running multiple layout experiments.\n")
    
    # Set up signal handler
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Simulate multiple concurrent tasks
    threads = []
    for i in range(3):
        thread = threading.Thread(
            target=simulate_long_running_task, 
            args=(f"Layout Experiment {i+1}", 15)
        )
        thread.start()
        threads.append(thread)
        time.sleep(0.5)  # Stagger the starts
    
    # Wait for all threads or shutdown
    for thread in threads:
        thread.join()
    
    if shutdown_event.is_set():
        print("\n✅ Shutdown completed successfully!")
    else:
        print("\n✅ All tasks completed normally.")


if __name__ == "__main__":
    main() 