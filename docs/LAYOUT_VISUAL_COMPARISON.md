# Visual Comparison of All 13 Prompt Layouts

## Quick Reference Table

| # | Layout Name | System Prompt | User Prompt Structure | Key Purpose |
|---|-------------|---------------|----------------------|-------------|
| 1 | **STANDARD** | Header + Full Hop | Full Hop [with Segment] + Footer | Baseline approach |
| 2 | **RECENCY** | Header only | Segment → Hop → Footer | Leverage recency bias |
| 3 | **SANDWICH** | Header only | Quick Check → Segment → Detailed → Footer | Segment between checks |
| 4 | **MINIMAL_SYSTEM** | One-liner | Header + Full Hop [with Segment] + Footer | Minimal system prompt |
| 5 | **QUESTION_FIRST** | Header only | Question → Segment → Rules → Footer | Question prominence |
| 6 | **HOP_LAST** | Header only | Segment → Full Hop → Footer | Maximum hop recency |
| 7 | **STRUCTURED_JSON** | Header + JSON notice | {segment: JSON} → Hop → Footer | Structured data format |
| 8 | **SEGMENT_FOCUS** | Header only | ═══SEGMENT═══ → Hop → Footer | Visual segment emphasis |
| 9 | **INSTRUCTION_FIRST** | Brief instruction | INSTRUCTION → Question → Segment → Guidelines → Footer | Clear task framing |
| 10 | **PARALLEL_ANALYSIS** | Header only | Segment → YES/NO/UNCERTAIN → Hop → Footer | Parallel consideration |
| 11 | **EVIDENCE_BASED** | Header + Evidence notice | Step 1: Segment → Step 2: Extract → Step 3: Apply → Footer | Force evidence extraction |
| 12 | **XML_STRUCTURED** | Header + XML notice | `<segment>` → `<question>` → Footer | XML structure clarity |
| 13 | **PRIMACY_RECENCY** | Header only | Question → Segment → Hop → REMEMBER: Question → Footer | Question at start AND end |

## Detailed Visual Breakdown

### Original 5 Layouts

```
1. STANDARD
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • Question + Rules               │
│ • Question      │    │ • [SEGMENT EMBEDDED HERE]        │
│ • Rules         │    │ • Examples                       │
│ • Examples      │    │ • Footer                         │
└─────────────────┘    └──────────────────────────────────┘

2. RECENCY  
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • [SEGMENT FIRST]                │
│                 │    │ • Question                       │
│                 │    │ • Rules + Examples               │
│                 │    │ • Footer                         │
└─────────────────┘    └──────────────────────────────────┘

3. SANDWICH
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • Quick Decision Check           │
│                 │    │ • [SEGMENT IN MIDDLE]            │
│                 │    │ • Detailed Analysis Rules        │
│                 │    │ • Footer                         │
└─────────────────┘    └──────────────────────────────────┘

4. MINIMAL_SYSTEM
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ "You are an     │    │ • Header                         │
│  expert..."     │    │ • Question + Rules               │
│                 │    │ • [SEGMENT]                      │
│                 │    │ • Examples + Footer              │
└─────────────────┘    └──────────────────────────────────┘

5. QUESTION_FIRST
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • Question (extracted)           │
│                 │    │ • [SEGMENT]                      │
│                 │    │ • Rules + Examples               │
│                 │    │ • Footer                         │
└─────────────────┘    └──────────────────────────────────┘
```

### New 8 Layouts

```
6. HOP_LAST
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • [SEGMENT FIRST]                │
│                 │    │ • Question                       │
│                 │    │ • Rules                          │
│                 │    │ • Examples + Footer              │
└─────────────────┘    └──────────────────────────────────┘

7. STRUCTURED_JSON
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • ```json                        │
│ • "JSON format" │    │   {                              │
│                 │    │     "segment_id": "XXX",         │
│                 │    │     "content": "[SEGMENT]",      │
│                 │    │     "task": "Answer QX"          │
│                 │    │   }                              │
│                 │    │   ```                            │
│                 │    │ • Hop Content + Footer           │
└─────────────────┘    └──────────────────────────────────┘

8. SEGMENT_FOCUS
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ ═══════════════════════          │
│                 │    │ SEGMENT TO ANALYZE               │
│                 │    │ ═══════════════════════          │
│                 │    │ [SEGMENT WITH VISUAL BOX]        │
│                 │    │ ═══════════════════════          │
│                 │    │ • Hop Content + Footer           │
└─────────────────┘    └──────────────────────────────────┘

9. INSTRUCTION_FIRST
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ "Follow         │    │ • Header                         │
│  instructions   │    │ • INSTRUCTION: You must...       │
│  exactly..."    │    │ • Question                       │
│                 │    │ • SEGMENT (ID: XXX): [TEXT]      │
│                 │    │ • ANALYSIS GUIDELINES:           │
│                 │    │ • Rules + Footer                 │
└─────────────────┘    └──────────────────────────────────┘

10. PARALLEL_ANALYSIS
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • SEGMENT: [TEXT]                │
│                 │    │ • Analyze by considering:        │
│                 │    │   • Would be YES if...           │
│                 │    │   • Would be NO if...            │
│                 │    │   • Would be UNCERTAIN if...     │
│                 │    │ • Hop Content + Footer           │
└─────────────────┘    └──────────────────────────────────┘

11. EVIDENCE_BASED
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • Step 1: Read segment           │
│ • "ALWAYS       │    │   [SEGMENT]                      │
│   extract       │    │ • Step 2: Extract evidence       │
│   evidence"     │    │   [You will identify...]         │
│                 │    │ • Step 3: Apply question         │
│                 │    │   Hop Content + Footer           │
└─────────────────┘    └──────────────────────────────────┘

12. XML_STRUCTURED
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ <analysis_task>                  │
│ • "XML format"  │    │   <segment id="XXX">             │
│                 │    │     <content>[SEGMENT]</content> │
│                 │    │   </segment>                     │
│                 │    │   <question number="X">          │
│                 │    │     [Hop Content]                │
│                 │    │   </question>                    │
│                 │    │ </analysis_task>                 │
│                 │    │ • Footer                         │
└─────────────────┘    └──────────────────────────────────┘

13. PRIMACY_RECENCY
┌─────────────────┐    ┌──────────────────────────────────┐
│ SYSTEM          │    │ USER                             │
│ • Header        │    │ • [QUESTION AT START]            │
│                 │    │ • "Now analyze this segment:"    │
│                 │    │ • [SEGMENT]                      │
│                 │    │ • Rules + Examples               │
│                 │    │ • REMEMBER: [QUESTION AGAIN]     │
│                 │    │ • Footer                         │
└─────────────────┘    └──────────────────────────────────┘
```

## Key Insights

1. **System Prompt Variations**:
   - Most layouts use header-only in system prompt
   - Only 4 layouts modify system prompt significantly:
     - STANDARD (full content)
     - MINIMAL_SYSTEM (one-liner)
     - INSTRUCTION_FIRST (brief instruction)
     - STRUCTURED_JSON, EVIDENCE_BASED, XML_STRUCTURED (add format notices)

2. **Segment Positioning**:
   - **Before hop content**: RECENCY, HOP_LAST, SEGMENT_FOCUS, PARALLEL_ANALYSIS
   - **After question**: QUESTION_FIRST, PRIMACY_RECENCY
   - **In structured format**: STRUCTURED_JSON, XML_STRUCTURED, EVIDENCE_BASED
   - **Sandwiched**: SANDWICH (between quick and detailed)
   - **Embedded in hop**: STANDARD, MINIMAL_SYSTEM

3. **Special Features**:
   - **Visual emphasis**: SEGMENT_FOCUS (box drawing)
   - **Structured data**: STRUCTURED_JSON (JSON), XML_STRUCTURED (XML)
   - **Process enforcement**: EVIDENCE_BASED (3-step process)
   - **Dual placement**: PRIMACY_RECENCY (question twice)
   - **Parallel thinking**: PARALLEL_ANALYSIS (YES/NO/UNCERTAIN) 