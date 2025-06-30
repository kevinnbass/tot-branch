# Enhanced Cue Detection System

## Overview

The Enhanced Cue Detection system is a two-step approach to frame classification that ensures systematic cue identification before frame determination. This approach improves accuracy and debuggability by forcing the model to explicitly mark all cues before making decisions.

## Directory Structure

```
cue_detection/
├── README.md                           # This file
├── cue_detection_instructions.txt      # Step 1 instructions
├── cue_checklist.txt                  # Simple checklist (deprecated)
├── enhanced_checklist.txt             # First enhanced version
├── enhanced_checklist_v2.txt          # Complete loss-less checklist (RECOMMENDED)
├── enhanced_checklist_v2.json         # Structured data version
├── frame_decision_instructions.txt    # Step 2 instructions
├── hops/                              # Simplified hop prompts
│   └── hop_Q01-Q12.txt               
└── enhanced_hops/                     # Minimalist hop prompts for v2
    └── hop_Q01-Q12.txt
```

## Layout Options

### 1. `cue_detection` (Basic)
- Uses the simple checklist (`cue_checklist.txt`)
- Trimmed hop prompts that reference CUE_MAP
- Good for testing the two-step concept

### 2. `cue_detection_enhanced` (Recommended)
- Uses the complete checklist (`enhanced_checklist_v2.txt`)
- Contains 100% of rules from original hop prompts
- Truly loss-less migration
- Best accuracy while maintaining debuggability

## How It Works

### Step 1: Cue Detection
The model systematically checks for cues using the enhanced checklist:
- Alarmist cues (intensifiers, vivid verbs, loaded questions)
- Reassuring cues (safety assurances, minimizers, calming language)  
- Neutral indicators (bare facts, capability statements)

### Step 2: Frame Decision
Based on identified cues, apply framing logic:
- If alarmist cues present and no strong reassuring → Alarmist
- If reassuring cues present and no strong alarmist → Reassuring
- If both types present → Neutral (mixed signals)
- If only neutral indicators → Neutral

### Step 3: Hop-Specific Question
The minimalist hop prompt references the CUE_MAP to answer yes/no.

## Key Improvements in V2

1. **Complete Pattern Tables**: All pattern IDs and examples preserved
2. **Full Rule Preservation**: Every exclusion, guard, and special case
3. **Distance Requirements**: All "within X chars" rules maintained
4. **Precedence Rules**: Complete ordering when patterns conflict
5. **Technical Guards**: HPAI and containment overrides preserved
6. **Structured Access**: JSON format for programmatic use

## Usage

```python
# In run_multi_coder_tot.py
config = {
    "layout": "cue_detection_enhanced",  # Use enhanced v2
    # ... other config
}
```

## Migration Verification

Run the verification test to ensure no information was lost:
```bash
python tests/test_checklist_migration.py
```

## Benefits

1. **Systematic**: Forces complete cue evaluation before decisions
2. **Debuggable**: Clear trace of which cues were identified
3. **Accurate**: No loss of hard-won optimization from original prompts
4. **Maintainable**: Single source of truth for all patterns
5. **Flexible**: Can update checklist without changing hop prompts

## Future Enhancements

1. **Weighted Scoring**: Assign confidence scores to each cue
2. **Cue Interactions**: Model how cues amplify/cancel each other
3. **Dynamic Precedence**: Context-aware precedence rules
4. **Explanation Generation**: Auto-generate rationales from CUE_MAP 