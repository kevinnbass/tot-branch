
# Layout-Specific Optimizations

## 1. Instruction Placement Standardization
- Move instruction to consistent position relative to segments
- For recency layouts: segments → instruction → hop
- For primacy layouts: instruction → hop → segments
- For structured layouts: instruction → segments (with clear format indicators)

## 2. Segment Count Indication
- Always include total count: "Segment N/M"
- Helps model allocate response space
- Critical for 200+ segment batches

## 3. Clean Hop Content for Batch Mode
- Remove all {{segment_text}} placeholders
- Replace with clear batch indicators
- Add "For each segment below:" prefix

## 4. Response Length Hints
- For large batches: "Keep each rationale under 50 words"
- Prevents token exhaustion
- Maintains consistency across segments

## 5. Layout-Specific System Prompts
- standard: "You are an expert claim-framing coder..."
- structured_json: "You process JSON-formatted analysis tasks..."
- evidence_based: "You systematically extract evidence before decisions..."
- Tailored to layout philosophy

## 6. Progressive Complexity
- Simple layouts for small batches
- Structured layouts for large batches
- JSON/XML for 100+ segments

## 7. Error Recovery Instructions
- Add: "If a segment is unclear, mark as uncertain"
- Add: "Process all segments even if some are difficult"
- Prevents partial responses
