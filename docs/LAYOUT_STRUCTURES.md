# Prompt Layout Structures - All 13 Layouts

## Overview
Each layout controls how the prompt components are arranged for the LLM. The key components are:
- **Header**: System instructions about the task
- **Question**: The specific question (Q1-Q12) being asked
- **Segment**: The text being analyzed
- **Rules/Examples**: Decision criteria and examples
- **Footer**: Output format instructions

## Layout Structures

### 1. STANDARD (Baseline)
```
SYSTEM: Header + Full Hop Content (Question + Rules + Examples)
USER:   Full Hop Content with [Segment] embedded + Footer
```
- Traditional approach where hop content appears in both system and user prompts
- Segment is embedded within the hop content

### 2. RECENCY
```
SYSTEM: Header only
USER:   [Segment] → Question + Rules + Examples → Footer
```
- Segment appears first to leverage recency bias
- All hop content moved to user prompt after segment

### 3. SANDWICH
```
SYSTEM: Header only
USER:   Quick Decision Check → [Segment] → Detailed Rules → Footer
```
- Segment is "sandwiched" between quick check and detailed analysis
- Extracts "QUICK DECISION CHECK" section from hop content

### 4. MINIMAL_SYSTEM
```
SYSTEM: "You are an expert claim-framing coder following a mandatory 12-step decision tree."
USER:   Header + Full Hop Content with [Segment] + Footer
```
- Minimal system prompt (one line)
- Everything else in user prompt

### 5. QUESTION_FIRST
```
SYSTEM: Header only
USER:   Question Only → [Segment] → Rules + Examples → Footer
```
- Question extracted and placed prominently before segment
- Rules and examples follow after segment

### 6. HOP_LAST
```
SYSTEM: Header only
USER:   [Segment] → Full Hop Content → Footer
```
- Segment first, then entire hop content
- Maximizes recency effect for hop instructions

### 7. STRUCTURED_JSON
```
SYSTEM: Header + "You will analyze segments presented in JSON format."
USER:   ```json
        {
          "segment_id": "XXX",
          "content": "[Segment Text]",
          "task": "Answer Question QX"
        }
        ```
        → Hop Content → Footer
```
- Segment presented as structured JSON
- Clear data format for better parsing

### 8. SEGMENT_FOCUS
```
SYSTEM: Header only
USER:   ═══════════════════════════════════
        SEGMENT TO ANALYZE (ID: XXX)
        ═══════════════════════════════════
        [Segment Text]
        ═══════════════════════════════════
        → Hop Content → Footer
```
- Visual emphasis on segment with box drawing
- Segment prominently displayed before hop content

### 9. INSTRUCTION_FIRST
```
SYSTEM: "Follow the instructions exactly. Analyze each segment systematically."
USER:   Header + 
        INSTRUCTION: You must answer the following question...
        Question
        SEGMENT (ID: XXX): [Segment Text]
        ANALYSIS GUIDELINES:
        → Rules + Examples → Footer
```
- Clear instruction framing before content
- Structured sections for clarity

### 10. PARALLEL_ANALYSIS
```
SYSTEM: Header only
USER:   SEGMENT (ID: XXX): [Segment Text]
        
        Analyze the segment above by considering:
        • Would indicate YES if: [Apply positive criteria]
        • Would indicate NO if: [Apply negative criteria]  
        • Would be UNCERTAIN if: [Neither clearly applies]
        
        → Hop Content → Footer
```
- Encourages parallel consideration of all options
- Explicit YES/NO/UNCERTAIN criteria

### 11. EVIDENCE_BASED
```
SYSTEM: Header + "ALWAYS extract evidence before making decisions."
USER:   Step 1: Read this segment (ID: XXX):
        [Segment Text]
        
        Step 2: Extract relevant evidence:
        [You will identify specific quotes and facts]
        
        Step 3: Apply the following question based on evidence:
        → Hop Content → Footer
```
- Forces evidence extraction before decision
- Step-by-step process

### 12. XML_STRUCTURED
```
SYSTEM: Header + "Segments and questions are presented in XML format."
USER:   <analysis_task>
            <segment id="XXX">
                <content>[Segment Text]</content>
            </segment>
            
            <question number="X">
                [Hop Content]
            </question>
        </analysis_task>
        → Footer
```
- XML structure for clarity
- Clear separation of components

### 13. PRIMACY_RECENCY
```
SYSTEM: Header only
USER:   [Question]
        
        Now analyze this segment (ID: XXX):
        [Segment Text]
        
        → Rules + Examples →
        
        REMEMBER: [Question]
        → Footer
```
- Question appears at both beginning AND end
- Maximizes salience through primacy and recency effects

## Key Differences Summary

| Layout | System Prompt | Segment Position | Special Features |
|--------|--------------|------------------|------------------|
| Standard | Full content | Embedded in hop | Baseline approach |
| Recency | Header only | First | Leverages recency bias |
| Sandwich | Header only | Middle | Between quick/detailed |
| Minimal_System | One line | Embedded | Everything in user |
| Question_First | Header only | After question | Question prominence |
| Hop_Last | Header only | First | Maximum hop recency |
| Structured_JSON | Header + notice | As JSON | Structured data |
| Segment_Focus | Header only | First with box | Visual emphasis |
| Instruction_First | Brief | After instruction | Clear task framing |
| Parallel_Analysis | Header only | First | YES/NO/UNCERTAIN |
| Evidence_Based | Header + notice | Step 1 | Forced evidence |
| XML_Structured | Header + notice | In XML | XML clarity |
| Primacy_Recency | Header only | Middle | Question twice | 