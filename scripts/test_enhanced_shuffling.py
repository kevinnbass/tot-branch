#!/usr/bin/env python3
"""
Test script to demonstrate enhanced shuffling capabilities for increased stochasticity.

This script shows the difference between:
1. No shuffling (deterministic batching)
2. Batch-level shuffling (--shuffle-batches)
3. Segment-level shuffling (--shuffle-segments)
4. Combined shuffling (both flags)
"""

import random
from typing import List

def simulate_batching(segments: List[str], batch_size: int, shuffle_batches: bool = False, shuffle_segments: bool = False) -> List[List[str]]:
    """Simulate the batching process with different shuffle strategies."""
    
    # Step 1: Create batches
    batches = [segments[i:i + batch_size] for i in range(0, len(segments), batch_size)]
    
    # Step 2: Apply shuffling strategies
    if shuffle_segments:
        # Shuffle segments within each batch
        for batch in batches:
            random.shuffle(batch)
    
    if shuffle_batches and len(batches) > 1:
        # Shuffle batch order
        random.shuffle(batches)
    
    return batches

def demonstrate_shuffling():
    """Demonstrate different shuffling strategies."""
    
    # Sample segments (simulating StatementIDs)
    segments = [f"seg_{i:03d}" for i in range(1, 21)]  # 20 segments
    batch_size = 5  # 4 batches of 5 each
    
    print("🔀 Enhanced Shuffling Demonstration")
    print("=" * 50)
    print(f"Original segments: {segments}")
    print(f"Batch size: {batch_size}")
    print()
    
    # Set seed for reproducible demonstration
    random.seed(42)
    
    # 1. No shuffling (baseline)
    print("1️⃣  NO SHUFFLING (baseline)")
    batches_none = simulate_batching(segments, batch_size)
    for i, batch in enumerate(batches_none):
        print(f"   Batch {i+1}: {batch}")
    print()
    
    # 2. Batch-level shuffling only
    print("2️⃣  BATCH SHUFFLING ONLY (--shuffle-batches)")
    random.seed(42)
    batches_batch = simulate_batching(segments, batch_size, shuffle_batches=True)
    for i, batch in enumerate(batches_batch):
        print(f"   Batch {i+1}: {batch}")
    print()
    
    # 3. Segment-level shuffling only
    print("3️⃣  SEGMENT SHUFFLING ONLY (--shuffle-segments)")
    random.seed(42)
    batches_segment = simulate_batching(segments, batch_size, shuffle_segments=True)
    for i, batch in enumerate(batches_segment):
        print(f"   Batch {i+1}: {batch}")
    print()
    
    # 4. Combined shuffling (maximum stochasticity)
    print("4️⃣  COMBINED SHUFFLING (--shuffle-batches --shuffle-segments)")
    random.seed(42)
    batches_combined = simulate_batching(segments, batch_size, shuffle_batches=True, shuffle_segments=True)
    for i, batch in enumerate(batches_combined):
        print(f"   Batch {i+1}: {batch}")
    print()
    
    print("🎯 STOCHASTICITY ANALYSIS")
    print("=" * 30)
    print("• No shuffling: Completely deterministic")
    print("• Batch shuffling: Changes batch processing order")
    print("• Segment shuffling: Randomizes within-batch segment order")
    print("• Combined: Maximum randomization at both levels")
    print()
    
    print("💡 RECOMMENDATIONS FOR YOUR USE CASE")
    print("=" * 40)
    print("For maximum stochasticity while batching:")
    print("  python -m multi_coder_analysis.main \\")
    print("    --batch-size 10 \\")
    print("    --shuffle-batches \\")
    print("    --shuffle-segments \\")
    print("    --concurrency 4")
    print()
    print("This provides:")
    print("  ✓ Randomized batch order (load balancing)")
    print("  ✓ Randomized segment order within batches")
    print("  ✓ Different segment combinations across runs")
    print("  ✓ Reduced bias from consistent ordering")

if __name__ == "__main__":
    demonstrate_shuffling() 