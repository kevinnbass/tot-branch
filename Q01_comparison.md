# Q01 Prompt Comparison: Enhanced Cue Detection vs JSON Parameterized

## Example Segment
```
The virus is extremely deadly, causing massive losses in poultry farms.
```

## 1. Enhanced Cue Detection Format (`cue_detection_enhanced`)

```markdown
---
meta_id: Q01
frame: Alarmist
summary: "Intensifier / comparative + risk-adjective"
---
### Segment (StatementID: S123)
The virus is extremely deadly, causing massive losses in poultry farms.

### Question Q01
Does the segment trigger any of the patterns listed below?  
If yes and no exclusions apply, answer "yes"; otherwise "no".

When you reply **first output a `cue_map` object** listing each pattern
in `row_map` with a boolean string value (`"yes"` or `"no"`).  Then
output `answer` and `rationale`.

### Q01 Rule Slice (checklist v2)
```json
{
  "row_map": {
    "Q1.1": "Intensifier + Risk-Adj",
    "Q1.2": "Comparative + Risk-Adj",
    "Q1.3": "Fixed Lethal-from-Outset Idiom"
  },
  "quick_check": "• Contains INTENSIFIER (**SO / VERY / EXTREMELY / HIGHLY / FRIGHTENINGLY / MORE / DEADLIER**) **AND** RISK‑ADJ (**DEADLY / DANGEROUS / SEVERE / CATASTROPHIC / LETHAL / CONTAGIOUS / VIRULENT / DESTRUCTIVE**) in the **same clause**?  \n• Skip if it's the taxonomic phrase **\"highly pathogenic (avian) influenza / HPAI\"**.  \n→ If yes → `\"yes\"`; else → `\"no\"`.",
  "inclusion_criteria": [
    "Authorial use of intensifiers (e.g., 'so,' 'very,' 'extremely,' 'incredibly,' 'particularly,' 'frighteningly') coupled with high-valence negative adjectives (e.g., 'destructive,' 'contagious') to describe the subject or its characteristics. The intensifier must clearly serve to heighten the emotional impact of the negative descriptor, pushing it beyond a factual statement of degree. Example: Author: 'Because the virus is *so deadly* to this species, culling is the only option.' → Alarmist. (Rationale: The intensifier 'so' amplifies 'deadly,' emphasizing the extreme nature and justifying the severe consequence, thereby framing the virus itself in alarming terms.)"
  ],
  "exclusion_criteria": [
    "When \"volatile\" modifies *prices/markets/rates* it is treated as an **economic metric** and never triggers Q1.",
    "> **Technical-term guard** – \"highly pathogenic\" used as part of the formal disease name (HPAI) is **Neutral** unless further alarmist cues appear."
  ],
  "examples": [
    "| **→ Alarmist** |",
    "| **Intensifier + Risk-Adj** | \"so deadly,\" \"very dangerous,\" \"extremely severe,\" \"highly lethal,\" \"frighteningly contagious\" | ✓ |",
    "| **Comparative + Risk-Adj** | \"more deadly,\" \"deadlier,\" \"more dangerous,\" \"less safe,\" \"increasingly severe\" | ✓ |",
    "| **Fixed Lethal-from-Outset Idiom** | \"deadly from the start,\" \"deadly from the outset\" | ✓ |",
    "| **Base Risk-Adj (alone)** | \"deadly,\" \"dangerous,\" \"severe\" (without intensifier) | → Neutral |"
  ],
  "special_rules": [
    "Adjacency requirement: elements must be in same clause or adjacent"
  ],
  "pattern_table": [
    {
      "id": "",
      "pattern_type": "Intensifier + Risk-Adj",
      "examples": "\"so deadly,\" \"very dangerous,\" \"extremely severe,\" \"highly lethal,\" \"frighteningly contagious\"",
      "outcome": "✓"
    }
  ],
  "guards": [
    "Technical Term Guard: 'highly pathogenic (avian) influenza' and 'HPAI' are neutral taxonomy",
    "Containment Override: 'culled' can neutralize certain patterns"
  ],
  "clarifications": [
    "** These terms when modified by an intensifier (e.g., 'so deadly,' 'extremely fatal,' 'particularly lethal,' 'frighteningly deadly') are Alarmist. Without such direct intensification, \"deadly\" (etc.) describing a factual characteristic (e.g., 'Avian flu can be deadly in domestic poultry') is typically Neutral unless other alarmist cues are present.",
    "TECHNICAL OR CLINICAL TERMS**  \nA term like *deadly, lethal, fatal* **by itself** can still be Neutral when used *clinically* (e.g. \"lethal dose 50\").  \n**BUT** if the same term is paired with *any intensifier or emotive verb* → **Alarmist (Precedence #1)**"
  ],
  "precedence_rules": [],
  "technical_notes": [],
  "raw_sections": []
}
```
### Your JSON reply
```json
{
  "cue_map": {
    "Q1.1": "yes|no",
    "Q1.2": "yes|no",
    "Q1.3": "yes|no"
  },
  "answer": "yes|no|uncertain",
  "rationale": "<max 80 tokens – quote the decisive cue(s) if yes>"
}
```
```

## 2. JSON Parameterized Format (`cue_detection_enhanced_json`)

```markdown
### Segment (StatementID: S123)
The virus is extremely deadly, causing massive losses in poultry farms.

### Question Q01
Apply the rules for Q01

### Rule Data (JSON)
```json
{
  "hop_id": "Q1",
  "frame": "Alarmist",
  "summary": "Intensifier / comparative + risk-adjective",
  "quick_check": "• Contains INTENSIFIER (**SO / VERY / EXTREMELY / HIGHLY / FRIGHTENINGLY / MORE / DEADLIER**) **AND** RISK‑ADJ (**DEADLY / DANGEROUS / SEVERE / CATASTROPHIC / LETHAL / CONTAGIOUS / VIRULENT / DESTRUCTIVE**) in the **same clause**?  \n• Skip if it's the taxonomic phrase **\"highly pathogenic (avian) influenza / HPAI\"**.  \n→ If yes → `\"yes\"`; else → `\"no\"`.",
  "patterns": {
    "Q1.1": {
      "id": "Q1.1",
      "label": "Intensifier + Risk-Adj",
      "active": true
    },
    "Q1.2": {
      "id": "Q1.2",
      "label": "Comparative + Risk-Adj",
      "active": true
    },
    "Q1.3": {
      "id": "Q1.3",
      "label": "Fixed Lethal-from-Outset Idiom",
      "active": true
    }
  },
  "pattern_table": [
    {
      "id": "",
      "pattern_type": "Intensifier + Risk-Adj",
      "examples": "\"so deadly,\" \"very dangerous,\" \"extremely severe,\" \"highly lethal,\" \"frighteningly contagious\"",
      "outcome": "✓"
    }
  ],
  "rules": {
    "inclusion": [
      {
        "text": "Authorial use of intensifiers (e.g., 'so,' 'very,' 'extremely,' 'incredibly,' 'particularly,' 'frighteningly') coupled with high-valence negative adjectives (e.g., 'destructive,' 'contagious') to describe the subject or its characteristics. The intensifier must clearly serve to heighten the emotional impact of the negative descriptor, pushing it beyond a factual statement of degree. Example: Author: 'Because the virus is *so deadly* to this species, culling is the only option.' → Alarmist. (Rationale: The intensifier 'so' amplifies 'deadly,' emphasizing the extreme nature and justifying the severe consequence, thereby framing the virus itself in alarming terms.)",
        "type": "general"
      }
    ],
    "exclusion": [
      {
        "text": "When \"volatile\" modifies *prices/markets/rates* it is treated as an **economic metric** and never triggers Q1.",
        "type": "general"
      },
      {
        "text": "> **Technical-term guard** – \"highly pathogenic\" used as part of the formal disease name (HPAI) is **Neutral** unless further alarmist cues appear.",
        "type": "general"
      }
    ],
    "special": [
      {
        "text": "Adjacency requirement: elements must be in same clause or adjacent",
        "type": "special"
      }
    ],
    "precedence": []
  },
  "examples": {
    "positive": [
      {
        "text": "| **→ Alarmist** |",
        "explanation": "",
        "patterns": []
      },
      {
        "text": "| **Intensifier + Risk-Adj** | \"so deadly,\" \"very dangerous,\" \"extremely severe,\" \"highly lethal,\" \"frighteningly contagious\" | ✓ |",
        "explanation": "",
        "patterns": []
      },
      {
        "text": "| **Comparative + Risk-Adj** | \"more deadly,\" \"deadlier,\" \"more dangerous,\" \"less safe,\" \"increasingly severe\" | ✓ |",
        "explanation": "",
        "patterns": []
      },
      {
        "text": "| **Fixed Lethal-from-Outset Idiom** | \"deadly from the start,\" \"deadly from the outset\" | ✓ |",
        "explanation": "",
        "patterns": []
      }
    ],
    "negative": [
      {
        "text": "| **Base Risk-Adj (alone)** | \"deadly,\" \"dangerous,\" \"severe\" (without intensifier) | → Neutral |",
        "explanation": "",
        "patterns": []
      }
    ]
  },
  "guards": [
    "Technical Term Guard: 'highly pathogenic (avian) influenza' and 'HPAI' are neutral taxonomy",
    "Containment Override: 'culled' can neutralize certain patterns"
  ],
  "clarifications": [
    "** These terms when modified by an intensifier (e.g., 'so deadly,' 'extremely fatal,' 'particularly lethal,' 'frighteningly deadly') are Alarmist. Without such direct intensification, \"deadly\" (etc.) describing a factual characteristic (e.g., 'Avian flu can be deadly in domestic poultry') is typically Neutral unless other alarmist cues are present.",
    "TECHNICAL OR CLINICAL TERMS**  \nA term like *deadly, lethal, fatal* **by itself** can still be Neutral when used *clinically* (e.g. \"lethal dose 50\").  \n**BUT** if the same term is paired with *any intensifier or emotive verb* → **Alarmist (Precedence #1)**"
  ]
}
```

### Response Format
Return a JSON object with the following structure:
```json
{
  "answer": "yes/no/uncertain",
  "rationale": "Your reasoning here",
  "cue_map": {
    "Q1.1": "Intensifier + Risk-Adj",
    "Q1.2": "Comparative + Risk-Adj", 
    "Q1.3": "Fixed Lethal-from-Outset Idiom"
  },
  "confidence": 85,
  "frame_likelihoods": {
    "Alarmist": 70,
    "Neutral": 20,
    "Reassuring": 10
  }
}
```
```

## Key Differences:

1. **Structure**:
   - **Enhanced**: Rules embedded in markdown with JSON code blocks
   - **JSON**: Everything is structured JSON data

2. **Flexibility**:
   - **Enhanced**: Fixed format, harder to modify programmatically
   - **JSON**: Fully parameterized, easy to modify/filter rules

3. **Response Format**:
   - **Enhanced**: Basic JSON with cue_map, answer, rationale
   - **JSON**: Extended with confidence scores and frame likelihoods

4. **Examples Policy**:
   - Both respect the `--examples` flag:
     - `full`: All examples included
     - `trim`: Only first 3 examples
     - `none`: Examples section empty

5. **Use Cases**:
   - **Enhanced**: Good for human readability, traditional approach
   - **JSON**: Better for A/B testing, programmatic rule modification, confidence scoring

## Running the A/B Test:

```bash
# Test both layouts
python scripts/layout_experiment.py \
  --layouts cue_detection_enhanced,cue_detection_enhanced_json \
  --gold-standard data/gold_standard.csv \
  --use-tot \
  --batch-size 1 \
  --examples full
``` 