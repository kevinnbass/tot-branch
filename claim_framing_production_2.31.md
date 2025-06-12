<!-- ───────────────────────────────────────────────────────────── -->
<!-- ROUTER LAYER – automatically routes a segment to its dimension -->
<!-- (added by patch)                                              -->
<!-- ───────────────────────────────────────────────────────────── -->

<!-- CHUNK_START:ROUTER_Q0_INTRO -->
---
chunk_type: router
rule_id: ROUTER_Q0_INTRO
dimension: Q0_INTRO
precedence_rank: 0
retrieve: true
text: "Router Q0 – Introductory / context-setting statements."
---
Router Q0 sentences give background or scene-setting without explicit risk framing.
***
Minimal diagnostic body for Q0 router (≤ 60 tokens).
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q1_INTENSIFIER_RISKADJ -->
---
chunk_type: router
rule_id: ROUTER_Q1_INTENSIFIER_RISKADJ
dimension: Q1_INTENSIFIER_RISKADJ
precedence_rank: 0
retrieve: true
text: "Router Q1 – Risk-adjusted intensifiers (e.g. 'highly deadly', 'extremely severe')."
---
Router Q1 catches intensifier + risk-adjective constructions that heighten danger.
***
Diagnostic body for Q1 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q2_HIGH_POTENCY_VERB -->
---
chunk_type: router
rule_id: ROUTER_Q2_HIGH_POTENCY_VERB
dimension: Q2_HIGH_POTENCY_VERB
precedence_rank: 0
retrieve: true
text: "Router Q2 – High-potency verbs (ravaged, devastated, crippled…)."
---
Router Q2 routes segments that use vivid verbs or metaphors to dramatise impact.
***
Diagnostic body for Q2 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q3_MODERATE_VERB_SCALE -->
---
chunk_type: router
rule_id: ROUTER_Q3_MODERATE_VERB_SCALE
dimension: Q3_MODERATE_VERB_SCALE
precedence_rank: 0
retrieve: true
text: "Router Q3 – Moderate verbs describing change in cases or risk."
---
Router Q3 covers moderate verbs explicitly paired with scale or impact numbers.
***
Diagnostic body for Q3 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q4_LOADED_RHETORICAL_QUESTION -->
---
chunk_type: router
rule_id: ROUTER_Q4_LOADED_RHETORICAL_QUESTION
dimension: Q4_LOADED_RHETORICAL_QUESTION
precedence_rank: 0
retrieve: true
text: "Router Q4 – Loaded rhetorical or leading questions."
---
Router Q4 activates on rhetorical questions implying fear, danger or urgency.
***
Diagnostic body for Q4 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q5_EXPLICIT_CALMING -->
---
chunk_type: router
rule_id: ROUTER_Q5_EXPLICIT_CALMING
dimension: Q5_EXPLICIT_CALMING
precedence_rank: 0
retrieve: true
text: "Router Q5 – Explicit calming / reassurance cues ('under control', 'nothing to fear')."
---
Router Q5 targets language that overtly reassures the reader about present safety.
***
Diagnostic body for Q5 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q6_MINIMISER_SCALE_CONTRAST -->
---
chunk_type: router
rule_id: ROUTER_Q6_MINIMISER_SCALE_CONTRAST
dimension: Q6_MINIMISER_SCALE_CONTRAST
precedence_rank: 0
retrieve: true
text: "Router Q6 – Minimising language or scale contrast ('only', 'just a few cases')."
---
Router Q6 detects minimisers plus scale contrast that downplay scope or risk.
***
Diagnostic body for Q6 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q8_CAPABILITY_PREPAREDNESS -->
---
chunk_type: router
rule_id: ROUTER_Q8_CAPABILITY_PREPAREDNESS
dimension: Q8_CAPABILITY_PREPAREDNESS
precedence_rank: 0
retrieve: true
text: "Router Q8 – Capability / preparedness framing (resources, readiness, containment)."
---
Router Q8 handles capability / preparedness statements without explicit calming.
***
Diagnostic body for Q8 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q10_SPECULATION_RELIEF -->
---
chunk_type: router
rule_id: ROUTER_Q10_SPECULATION_RELIEF
dimension: Q10_SPECULATION_RELIEF
precedence_rank: 0
retrieve: true
text: "Router Q10 – Speculation or tentative relief ('may be less deadly', 'early signs promising')."
---
Router Q10 is for future-oriented relief speculation lacking present-risk wording.
***
Diagnostic body for Q10 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q11_FRAMED_QUOTATIONS -->
---
chunk_type: router
rule_id: ROUTER_Q11_FRAMED_QUOTATIONS
dimension: Q11_FRAMED_QUOTATIONS
precedence_rank: 0
retrieve: true
text: "Router Q11 – Quoted statements framed or disputed by the author."
---
Router Q11 routes segments whose dominant framing comes from a quoted source.
***
Diagnostic body for Q11 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:ROUTER_Q12_DEFAULT_NEUTRAL -->
---
chunk_type: router
rule_id: ROUTER_Q12_DEFAULT_NEUTRAL
dimension: Q12_DEFAULT_NEUTRAL
precedence_rank: 0
retrieve: true
text: "Router Q12 – Default neutral / unmarked segments."
---
Router Q12 catches segments with no explicit alarmist or reassuring cues.
***
Diagnostic body for Q12 router.
<!-- CHUNK_END -->

<!-- CHUNK_START:META_SYSTEM_INSTRUCTIONS -->
---
chunk_type: rule
rule_id: META_SYSTEM_INSTRUCTIONS
dimension: META
parent_group: SYSTEM_INSTRUCTIONS
precedence_rank: 0
outcome: SystemGuidance
tags:
- core
---
**SYSTEM_INSTRUCTION_BLOCK_START**
IMPORTANT: You MUST output valid JSONL.
This means EACH line of your output MUST be a single, complete, and independently valid JSON object corresponding to one segment.
DO NOT output partial JSON objects or run-on JSON across lines.
Each JSON object per line MUST contain EXACTLY these fields: "StatementID", "Dim1_Frame", "Dim4_AmbiguityNote", and "ContextUseNote".
Follow all other formatting rules from the main prompt precisely, especially for ENUM values and field presence.
**SYSTEM_INSTRUCTION_BLOCK_END**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_INTRODUCTION -->
---
chunk_type: rule
rule_id: META_INTRODUCTION
pattern_summary: Introduction to Claim Framing Decision Tree and version info.
dimension: META
parent_group: INTRODUCTION
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: INTRODUCTION
---
> **Version 2.27 – Full cue-lexicon tables restored**  
> *Adds collapsed META_LEXICON_FULL chunk (high/mod/low potency & Neutral verbs)*

### Claim Framing Decision Tree

This document provides a step-by-step decision tree for claim framing analysis. Please follow the questions in order. Expand the `<details>` sections for full rules, examples, and clarifications corresponding to each step. The order of these questions reflects a specific precedence, similar to the "Precedence Ladder" from the original codebook, ensuring that higher-priority rules are checked first.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_CUE_LEXICON_WARNING -->
---
chunk_type: rule
rule_id: META_CUE_LEXICON_WARNING
pattern_summary: Illustrative cue lexicon warning and conceptual potency scale.
dimension: META
parent_group: CUE_LEXICON_WARNING
precedence_rank: 99
outcome: Meta
tags:
- lexicon
references_rule_group: CUE_LEXICON_WARNING
related: [META_LEXICON_FULL]
---
### CRITICAL WARNING – Illustrative Cue Lexicon

*This lexicon is illustrative and heuristic only. It is **not** a definitive checklist. The presence of a word from this list **does not** automatically assign a frame. Always apply the core definitions, inclusion/exclusion criteria, and the Principle of Cue Sufficiency; context and speaker intent govern the final call.*

#### Cue Potency Scale (Conceptual Guide)
**High-potency cues** (often sufficient alone):  
• *Alarmist*: catastrophe, existential threat, nightmare scenario, unmitigated disaster, ticking time-bomb; urgent calls to action tied to severe named outcomes.  
• *Reassuring*: completely safe, no danger whatsoever, fully under control, absolutely no cause for alarm, public can be fully at ease.

**Moderate-potency cues** (may be sufficient if central or in combination):  
*Alarmist*: crisis, devastating, severe impact, soaring/plummeting, grave concern, urgent need.  
*Reassuring*: manageable, low risk, situation contained, good progress, optimistic outlook.

**Low-potency / context-dependent cues** (rarely sufficient alone):  
*Alarmist*: concerning, worrying, potential threat, problematic.  
*Reassuring*: hopeful signs, positive development, efforts underway, plan in place.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_GLOSSARY_CUE_TERMS -->
---
chunk_type: rule
rule_id: META_GLOSSARY_CUE_TERMS
pattern_summary: Glossary definitions for key cue terminology.
dimension: META
parent_group: GLOSSARY_CUE_TERMS
precedence_rank: 99
outcome: Meta
tags:
- lexicon
references_rule_group: GLOSSARY_CUE_TERMS
---
### Glossary – Cue Terminology

**Active Reassurance** – Explicit linguistic effort to calm concerns, minimise perceived risk, or highlight present safety/control.  
**Passive Good News** – Factual reporting of positive information without additional calming language.  
**Explicit Linguistic Cue** – Specific words, phrases, or rhetorical figures that directly establish a frame.  
**Salience** – Prominence given through explicit emphasis, shaping audience perception.  
**Potent Cue** – Language with strong capacity to influence perceived risk or safety owing to intensity or authority.  
**Vivid Cue** – Particularly graphic or emotionally engaging wording that stands out.  
**Loaded Language** – Words with strong connotations used to sway perception beyond literal meaning.  
**Explicit Framing** – Direct statements guiding the audience's interpretation or emotional response.  
**Rhetorical Devices** – Persuasive techniques such as metaphors, hyperbole, or rhetorical questions.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:COMMENT_PROVENANCE_AUTO -->
---
chunk_type: rule
rule_id: COMMENT_PROVENANCE_AUTO
tags:
- comment
dimension: META
parent_group: PROVENANCE
precedence_rank: 99
outcome: Meta
---
    <!-- Source inspiration: Dudo et al., 2007; Burgers & de Graaf, 2013.  (kept for documentation; excluded from RAG index) -->
***
    <!-- CHUNK_END -->

<!-- CHUNK_START:Q0_INTRO -->
---
chunk_type: rule
rule_id: Q0_INTRO
pattern_summary: Meta-Guidance Review - mandatory review step before framing questions.
dimension: Q0_INTRO
parent_group: INTRO
precedence_rank: 99
outcome: Meta
tags:
- core
---
**Q0: Meta-Guidance Review**
Before answering specific framing questions, have you reviewed the 'Global Guidance & Core Principles' in `step-0-meta-details` below? (This is a mandatory review step. All principles apply throughout the decision process.)
***
<!-- CHUNK_END -->

<!-- CHUNK_START:PRECEDENCE_TABLE_INTRO -->
---
chunk_type: rule
rule_id: PRECEDENCE_TABLE_INTRO
pattern_summary: Introduction to Explicit Precedence & Tie-Breaker Rules table.
dimension: P
parent_group: TABLE_INTRO
precedence_rank: 99
outcome: Meta
tags:
- core
---
**NEW: Explicit Precedence & Tie-Breaker Rules**
If more than one cue type from the questions below appears in a segment, use the following ladder to decide which rule takes precedence. Evaluate conditions from top to bottom; the first one that is TRUE determines the approach or frame.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:P1_PRECEDENCE_INTENSIFIER_RISKADJ -->
---
chunk_type: rule
rule_id: P1_PRECEDENCE_INTENSIFIER_RISKADJ
precedence_rank: 1
outcome: Alarmist
references_rule_group: INTENSIFIER + risk-adjective
pattern_summary: 'Precedence 1: Intensifier + risk-adjective leads to Alarmist (Q1).'
dimension: P
parent_group: PRECEDENCE_INTENSIFIER_RISKADJ
tags:
- core
---
1. **INTENSIFIER + risk-adjective** *(e.g., highly/very/more/deadlier … deadly/lethal/dangerous/severe)* → **Alarmist**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:P2_PRECEDENCE_MODERATE_VERB_SCALE -->
---
chunk_type: rule
rule_id: P2_PRECEDENCE_MODERATE_VERB_SCALE
precedence_rank: 2
outcome: Alarmist
references_rule_group: MODERATE-VERB + scale/metric
pattern_summary: 'Precedence 2: Moderate verb + scale/metric leads to Alarmist (Q4).'
dimension: P
parent_group: PRECEDENCE_MODERATE_VERB_SCALE
tags:
- core
---
2. **MODERATE-VERB + scale/metric** *(e.g., swept/hit/soared/prompted AND millions/record/largest/X%)* → **Alarmist**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:P3_PRECEDENCE_VIVID_VERB -->
---
chunk_type: rule
rule_id: P3_PRECEDENCE_VIVID_VERB
precedence_rank: 3
outcome: Alarmist
references_rule_group: VIVID-VERB alone
pattern_summary: 'Precedence 3: Vivid verb alone leads to Alarmist (Q2).'
dimension: P
parent_group: PRECEDENCE_VIVID_VERB
tags:
- core
---
3. **VIVID-VERB alone** *(e.g., ravaged/devastated/skyrocketed)* → **Alarmist**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:P4_PRECEDENCE_EXPLICIT_CALMING -->
---
chunk_type: rule
rule_id: P4_PRECEDENCE_EXPLICIT_CALMING
precedence_rank: 4
outcome: Reassuring
references_rule_group: Explicit calming or safety claim
pattern_summary: 'Precedence 4: Explicit calming or safety claim leads to Reassuring
  (Q6).'
dimension: P
parent_group: PRECEDENCE_EXPLICIT_CALMING
tags:
- core
---
4. **Explicit calming or safety claim** *(e.g., public can rest easy, situation is fully contained)* → **Reassuring**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:P5_PRECEDENCE_BARE_NEGATION_CAPABILITY -->
---
chunk_type: rule
rule_id: P5_PRECEDENCE_BARE_NEGATION_CAPABILITY
precedence_rank: 5
outcome: Neutral
references_rule_group: Bare negation OR capability statement
pattern_summary: 'Precedence 5: Bare negation or capability statement without explicit
  calming leads to Neutral (Q3, Q8).'
dimension: P
parent_group: PRECEDENCE_BARE_NEGATION_CAPABILITY
tags:
- core
---
5. **Bare negation OR capability statement** *(e.g., no cases, vaccine can be made)* → **Neutral**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:P6_PRECEDENCE_DEFAULT_NEUTRAL -->
---
chunk_type: rule
rule_id: P6_PRECEDENCE_DEFAULT_NEUTRAL
precedence_rank: 6
outcome: Neutral
references_rule_group: Default to Neutral
pattern_summary: 'Precedence 6: Default to Neutral if none of the above conditions
  are met.'
dimension: P
parent_group: PRECEDENCE_DEFAULT_NEUTRAL
tags:
- core
---
6. **Default to Neutral** *(e.g., if none of the above conditions are met)* → **Neutral**
***
<!-- CHUNK_END -->

*(Note: This table provides a general hierarchy. The detailed logic within each specific Question (Q1-Q12) governs the final determination for that cue type.)*

<!-- CHUNK_START:GLOBAL_GUIDANCE_CORE_PRINCIPLES -->
---
chunk_type: rule
rule_id: GLOBAL_GUIDANCE_CORE_PRINCIPLES
pattern_summary: 'Foundational principles: code presentation, pitfalls, precedence,
  technical terms, symmetry, LLM issues, content vs. presentation.'
dimension: META
parent_group: GUIDANCE_CORE_PRINCIPLES
precedence_rank: 5
outcome: Meta
tags:
- core
child_ids: [GLOBAL_GUIDANCE_CORE_PRINCIPLES_A,
            GLOBAL_GUIDANCE_CORE_PRINCIPLES_B,
            GLOBAL_GUIDANCE_CORE_PRINCIPLES_C]
child_of: [GUIDANCE_CORE_PRINCIPLES]
---
*This chunk has been split into three sub-chunks (A–C) for retrieval efficiency.*  
No content removed.  
<!-- pointer only; see child chunks below -->
***
<!-- CHUNK_END -->

<!-- CHUNK_START:GLOBAL_GUIDANCE_CORE_PRINCIPLES_A -->
---
chunk_type: rule
rule_id: GLOBAL_GUIDANCE_CORE_PRINCIPLES_A           # new
dimension: META
parent_group: GLOBAL_GUIDANCE_CORE_PRINCIPLES
precedence_rank: 5
outcome: Meta
tags:
- core
references_rule_group: GLOBAL_GUIDANCE_CORE_PRINCIPLES
related: [GLOBAL_GUIDANCE_CORE_PRINCIPLES_B,
          GLOBAL_GUIDANCE_CORE_PRINCIPLES_C]
---
<details id="ggcp-a"><summary>Core Principles (§1-§2)</summary>

##### §1 Mission
**Global Guidance & Core Principles**
*This section contains foundational principles that apply throughout the entire decision tree process. All principles must be considered when making framing determinations.*
***
**!! CORE PRINCIPLES & COMMON PITFALLS (READ THIS FIRST!) !!**

**1. Bedrock Principle: CODE THE PRESENTATION, NOT THE FACTS**
The frame (Alarmist, Reassuring, Neutral) is determined solely by the explicit linguistic and rhetorical choices demonstrably made by the author or quoted source within the segment to make certain aspects salient. It is NEVER determined by the objective severity or positivity of the facts themselves, nor by the coder's inferred implications of those facts, nor by the coder's own emotional reaction to the facts. Your primary task is to identify how the information is explicitly presented by the author/source.

**Distinguishing Information Severity from Presentational Salience**
A core challenge is separating the raw information (which might be inherently concerning or positive) from the author's/source's deliberate presentational choices. The same severe fact can be presented neutrally or alarmingly. The same positive fact can be presented neutrally or reassuringly. Codebook demands you code only the latter – the deliberate presentational act.

**Examples:**
* **Severe Fact, Neutral Presentation:**
  * Segment: "The report documented 500,000 job losses in the last quarter."
  * Reasoning: "Neutral. The author reports a severe statistic factually. No loaded language, intensifiers, or explicit alarmist rhetoric (e.g., 'a catastrophic wave of job losses,' 'an economic disaster unfolding') is used by the author to frame this fact."

* **Severe Fact, Alarmist Presentation:**
  * Segment: "The report detailed a catastrophic wave of 500,000 job losses in the last quarter, signaling an economic disaster unfolding."
  * Reasoning: "Alarmist (Author-driven). The author uses 'catastrophic wave' and 'economic disaster unfolding' to explicitly frame the severe statistic. Decisive cues: 'catastrophic wave,' 'economic disaster unfolding'."

* **Positive Fact, Neutral Presentation:**
  * Segment: "Vaccination rates reached 80% in the target population."
  * Reasoning: "Neutral. The author reports a positive statistic factually. No explicit reassuring language (e.g., 'a wonderfully high rate providing excellent protection,' 'this achievement means the community is now safe') is used by the author."

* **Positive Fact, Reassuring Presentation:**
  * Segment: "Vaccination rates have thankfully reached 80% in the target population, a wonderfully high figure that provides excellent protection and means the community is now much safer."
  * Reasoning: "Reassuring (Author-driven). The author uses 'thankfully,' 'wonderfully high figure,' 'excellent protection,' and 'community is now much safer' to actively frame the positive statistic reassuringly. Decisive cues: 'thankfully,' 'wonderfully high,' 'much safer'."

**Red Flag Phrases for Coder Self-Correction**
Before assigning a frame, ask yourself:
* 'Am I coding this Alarmist because the number is big/event is bad, or because of specific alarmist words/rhetoric used by the author/source that I can quote?'
* 'Am I coding this Reassuring because the news is good, or because of specific calming/risk-minimizing words/rhetoric used by the author/source that I can quote?'
* 'If I removed the explicit framing words I've identified, would the remaining factual statement still inherently imply the frame, or would it become Neutral?' (If it becomes Neutral, your identified framing words are likely the correct basis for the code).

**🔥 CRITICAL REMINDER: Focus on *How* It's Said, Not *What* Is Said 🔥**
**Large Numbers ≠ Alarmist:** "50 million birds were culled" → Neutral (factual report)
**Large Numbers + Alarmist Framing = Alarmist:** "A catastrophic 50 million birds were slaughtered" → Alarmist (loaded language)
**Positive Facts ≠ Reassuring:** "No human cases detected" → Neutral (factual report)  
**Positive Facts + Reassuring Framing = Reassuring:** "Fortunately, no human cases detected, meaning the risk is very low" → Reassuring (active calming)
***

##### §2 Hierarchy of Authority
*(This section refers to guidance that was planned for GGCP_A but the specific text for "§2 Hierarchy of Authority" isn't explicitly detailed under GLOBAL_GUIDANCE_CORE_PRINCIPLES in the provided text. The user's instructions for GGCP_A §2 were "continue until token ~380-400". The above text for §1 is already substantial. For now, I will end GGCP_A here as per "ending cleanly at a paragraph break" after the "Bedrock Principle" and its examples, which forms a coherent unit. If specific text for a "§2 Hierarchy of Authority" was intended here from the original, it would need to be pasted from the original document content which I am approximating based on structure.)*

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:GLOBAL_GUIDANCE_CORE_PRINCIPLES_B -->
---
chunk_type: rule
rule_id: GLOBAL_GUIDANCE_CORE_PRINCIPLES_B
dimension: META
parent_group: GLOBAL_GUIDANCE_CORE_PRINCIPLES
precedence_rank: 5
outcome: Meta
tags:
- core
references_rule_group: GLOBAL_GUIDANCE_CORE_PRINCIPLES
related: [Q1_INTENSIFIER_RISKADJ,
          Q6_MINIMISER_SCALE_CONTRAST]
---
<details id="ggcp-b"><summary>Common Pitfalls</summary>

**2. Common Pitfalls & Guiding Micro-Rules:**

**(A) Positive Facts / Absence of Negative Events ≠ Active Reassurance**
* Micro-Rule: Statements merely reporting positive factual outcomes (e.g., "no further cases were reported," "tests were negative," "patient recovered") or the simple absence of negative events are categorically Neutral unless explicitly framed otherwise by the author/source.
* To be Reassuring, the author or quoted source MUST actively and explicitly employ calming, optimistic, or risk-minimizing language designed to reduce audience concern or highlight safety/control regarding the broader situation, beyond simply stating the positive fact.
* Canonical NON-EXAMPLE for Reassuring (Code: Neutral):
    * Text: "Despite the health department conducting contact tracing, no further cases of bird flu connected to the case have been reported at the time of writing."
    * Incorrect Reasoning (to avoid): "This is good news and implies containment, so it's Reassuring."
    * Correct Codebook Reasoning: "Neutral. The author reports a positive fact (absence of new cases) using descriptive, neutral language. No explicit reassuring language (e.g., 'providing significant relief,' 'which is very encouraging news,' 'fortunately') is used by the author to actively frame these facts reassuringly."

**(B) Severe Characteristics / Negative Facts ≠ Active Alarm**
* Micro-Rule: Listing objectively severe characteristics, properties, or statistics (e.g., "high mutation rate," "high mortality rates," "significant number of outbreaks," "virus spread to new areas") is categorically Neutral if presented by the author/source factually, without additional explicit alarmist framing language, tone, or rhetorical emphasis (e.g., "a terrifyingly high rate," "these characteristics paint a catastrophic picture," "this grave list signals imminent danger," "an explosive spread").
* Canonical NON-EXAMPLE for Alarmist (Code: Neutral):
    * Text: "These [characteristics] include a wide host range, high mutation rate, genetic reassortment, high mortality rates, and genetic reassortment."
    * Incorrect Reasoning (to avoid): "High mortality and mutation rates are inherently alarming, so it's Alarmist."
    * Correct Codebook Reasoning: "Neutral. The author lists factual characteristics using neutral, descriptive language. No loaded adjectives (e.g., 'terrifying,' 'devastating') or explicit alarmist rhetoric are used by the author to actively frame these characteristics beyond their factual statement."

**(C) Capability / Preparedness Statements ≠ Active Reassurance (Rule C)**
* Micro-Rule: Statements describing capabilities, preparedness measures (future or existing), implemented safeguards, capacities, or potential positive future actions (e.g., "a vaccine can be made in X weeks," "systems are in place to detect X," "we have the resources to respond," "new safeguards have been enacted") are categorically Neutral unless explicitly and actively framed by the author/source as a reason for current calm, safety, or substantially minimized present risk.
* To be Reassuring, the author or quoted source MUST go beyond stating the capability and actively use explicit language to connect that capability to a state of present calm, safety, or significantly reduced current risk for the audience.

**🔧 NEW Clarification – Rule C.1: "Vigilance ≠ Reassurance"**
Statements that an actor "remains vigilant," "follows all bio-security protocols," "is focused on safety every day," "regular testing is in place," etc. describe diligence, not audience safety.
These are Neutral unless explicitly linked to a present state of low risk or calm (e.g., "so the public can rest easy").

**Mini-pair**
* **Neutral:** "Producers remain vigilant and follow all bio-security protocols."
* **Reassuring:** "Producers remain vigilant and follow all bio-security protocols, meaning the current risk to consumers is negligible."

**KEY QUESTION FOR SELF-CORRECTION:** 
Am I coding based on explicit framing language I can highlight in the text (the *how* it is said by the author/source), OR am I coding based on the inferred positive/negative implications of the facts themselves (the *what* is being said)? The frame lies in the *how*.
***

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:GLOBAL_GUIDANCE_CORE_PRINCIPLES_C -->
---
chunk_type: rule
rule_id: GLOBAL_GUIDANCE_CORE_PRINCIPLES_C
dimension: META
parent_group: GLOBAL_GUIDANCE_CORE_PRINCIPLES
precedence_rank: 5
outcome: Meta
tags:
- core
references_rule_group: GLOBAL_GUIDANCE_CORE_PRINCIPLES
related: [Q1_INTENSIFIER_RISKADJ,
          Q5_EXPLICIT_CALMING,
          Q6_MINIMISER_SCALE_CONTRAST]
---
<details id="ggcp-c"><summary>Coder Self-Audit Checklist</summary>

**3. Precedence Rules**

**🟢 PRECEDENCE & CORE PRINCIPLES**
The explicit tie-breaker table presented directly under "Q0: Meta-Guidance Review" now governs the order of operations if multiple framing cues are present. Please refer to that table first.

Key principles that remain paramount:
1.  **Guidance Note: Primacy of Framed Quotations:** If a direct quote carries a distinct frame, it usually dictates the segment's frame. (Detailed in original notes below).
2.  **Dimension 1 - Guidance Note: Principle of Cue Sufficiency:** A single potent cue can be enough. (Detailed in original notes below).
3.  **Default-to-Neutral Rule (Strictly Presentation-Focused):** Absent explicit framing, default to Neutral. (Detailed in original notes below).

*(The original detailed text for "Primacy of Framed Quotations", "Principle of Cue Sufficiency", and "Default-to-Neutral Rule" should be preserved below this new summary within step-0-meta-details, but the old "PRECEDENCE LADDER" list itself is superseded by the new table above the details block).*
***
**4. Core Foundational Principles**

**Guidance Note: Primacy of Framed Quotations**
Core Principle: If a direct quotation (or a clearly attributed statement from a specific source) within the segment carries a distinct Alarmist or Reassuring frame, the segment's Dim1_Frame MUST reflect the frame of that quotation/attributed statement. This principle applies even if the author's narrative surrounding the quote is Neutral. The frame is determined by the language and tone used by the quoted source itself.

* **Author's Neutrality:** When the author neutrally reports a framed quote, the quote's frame dictates the segment's frame.
* **Author Reinforces Quote's Frame:** If the author's narrative also adopts or amplifies the same frame as the quote, this further strengthens the coding of the quote's frame.
* **Author Challenges Quote's Frame (Advanced):** If the author explicitly challenges, refutes, or heavily recontextualizes the quote's frame using their own explicit framing language, the coder must determine the overall dominant frame of the segment.
* **Multiple Framed Quotes & Mixed Messages:** If a segment contains multiple quotes with different frames, determine the dominant frame. If one quote is significantly more potent or central to the segment's point, its frame may prevail.

**Default-to-Neutral Rule (Strictly Presentation-Focused)**
Heuristic: In the absence of explicit emotional language, specific framing cues (e.g., loaded adjectives, urgent tone, calming words), or a distinct rhetorical tone from EITHER the segment's author OR any directly quoted source within the segment, Neutral is the appropriate code for Dim1_Frame. This rule applies if both the author's presentation and the presentation by any quoted sources are neutral.

* If a segment reports objectively severe facts, and both the author and any quoted source commenting on these facts use neutral, factual language without added alarmist rhetoric, the Dim1_Frame is Neutral.
* Similarly, if a segment reports objectively positive facts, and both the author and any quoted source use neutral, factual language without added reassuring rhetoric, the Dim1_Frame is Neutral.
* The focus remains on the presentation by the author and by any quoted sources.

**Guidance Note: Principle of Cue Sufficiency**
Consistent with established framing theory, a single, highly vivid, potent, or strategically emphasized framing cue in the presentation by either a quoted source or the author can be sufficient to categorize a segment as Alarmist or Reassuring. This includes powerful metaphors, stark worst-case scenarios phrased alarmingly, unequivocal statements of extreme danger or safety, brief but intensely emotional language, or strategically employed verbs (e.g., imperatives, deontic modals like 'must,' 'have to'), adverbs (e.g., 'immediately,' 'as soon as possible'), loaded rhetorical questions, or specific rhetorical constructions (e.g., negated reassurance) that convey a strong sense of urgency, risk, or (conversely) control and safety.

**+++ IMPORTANT BOXED NOTE +++**
**A single high-potency cue (e.g., a vivid verb describing impactful action + scale, a loaded rhetorical question implying danger, or an intensifier + high-valence/loaded adjective) is often sufficient to assign Alarmist, per the Principle of Cue Sufficiency.**
***
**5. Technical Terms and Clinical Language**

**Guidance Note: Handling Technical Terms, Official Classifications, and Procedural Language**
Technical terms, official classifications, and procedural language are generally considered Neutral when reported as factual designations or procedural descriptions, especially if attributed to official sources. They only shift the frame if the *author or quoted source adds their own separate layer of explicit emotional framing or alarmist/reassuring rhetoric* to these terms.

* **Technical Classifications:** Terms like "highly pathogenic," "Category 5," or specific case numbers are Neutral when used as formal identifiers.
    * Neutral: "A highly pathogenic form of bird flu was detected, according to the USDA."
    * Alarmist: "A terrifyingly dangerous, highly pathogenic strain was unleashed."
* **Procedural Language:** Clinical terms like "depopulated," "euthanized," "quarantined" are Neutral when describing standard procedures.
    * Neutral: "Birds will be depopulated to prevent spread."
    * Alarmist: "Birds will be horrifically slaughtered in a desperate attempt to prevent catastrophic spread."
* **Official Numbers/Statistics:** Large numbers or severe statistics are Neutral when reported factually.
    * Neutral: "50 million birds were culled in 2015."
    * Alarmist: "A catastrophic 50 million birds were slaughtered in the devastating 2015 outbreak."

> ⚠ **TECHNICAL OR CLINICAL TERMS**  
> A term like *deadly, lethal, fatal* **by itself** can still be Neutral when used *clinically* (e.g. "lethal dose 50").  
> **BUT** if the same term is paired with *any intensifier or emotive verb* → **Alarmist (Precedence #1)**.
***
**6. The Symmetry Rule**

**SIDEBAR: The Symmetry Rule**
The codebook now enforces symmetric standards between Alarmist and Reassuring frames:

**For Alarmist:** Severe facts require explicit intensification
- "50 million birds culled" → Neutral (factual)
- "A catastrophic 50 million birds slaughtered" → Alarmist (intensified)

**For Reassuring:** Positive facts require explicit calming cues
- "Not expected to lower production" → Neutral (bare negation)
- "Not expected to lower production, so the risk remains very low" → Reassuring (calming cue added)

Both frames now require active linguistic effort beyond stating facts.
***
**7. Common LLM Misinterpretations & How to Avoid Them**

1. **Mistaking Large Numbers/Severe Outcomes for Alarmist Framing:** Large casualty counts, high costs, or severe statistics are Neutral if reported factually without explicit alarmist language from the author/source. Focus on *how* the numbers are presented, not their magnitude.

2. **Assuming Positive Facts (e.g., 'no human cases') are Always Reassuring:** The absence of negative events is Neutral unless the author/source adds explicit reassuring language to actively calm broader concerns.

3. **Treating Technical Terms as Inherently Alarmist:** Terms like "highly pathogenic," "depopulated," or "high mortality rate" are often Neutral when used as standard descriptors or official classifications.

4. **Confusing Capability/Preparedness Statements with Active Reassurance:** Describing safeguards, capabilities, or control measures is Neutral unless explicitly framed as a reason for current calm or minimized risk.

5. **Overweighting Single Negative Adjectives:** Mild terms like "concerning" or standard descriptors like "deadly" (when describing disease characteristics) are often Neutral unless part of broader alarmist rhetoric.

6. **NEW (v2.10) - Treating Bare Negations as Reassuring:** Statements like "not expected to cause problems" or "unlikely to affect production" are Neutral unless paired with explicit calming/safety cues (e.g., "so the risk remains low," "meaning consumers can be confident"). The negation alone is insufficient for Reassuring framing.
***
**8. Critical Distinction: Information Severity vs. Framing Style**

A core principle of this codebook is the absolute and non-negotiable separation between the objective severity or positivity of an event/fact and the framing style used by the author/source to present it. Segments are NEVER coded Alarmist simply because they report bad news (e.g., deaths, outbreaks, high costs, risks) NOR Reassuring simply because they report good news (e.g., recovery, low numbers, successful prevention). The code MUST ALWAYS be based on the presence of explicit Alarmist or Reassuring framing cues in the language deliberately chosen by the author or quoted source. In the complete absence of such explicit framing cues from both author and quote, the segment is unquestionably Neutral, regardless of how concerning or encouraging the underlying facts may be to the coder or a general reader.
***
**Mini-Glossary: Content vs. Presentation**
* **Content/Fact:** The underlying event, statistic, or piece of information being reported (e.g., '100 birds died,' 'a vaccine was approved').
* **Presentational Cue:** The specific word choice, phrasing, tone, rhetorical strategy, or explicit evaluative language intentionally employed by the source or author to frame or make salient that content/fact, aiming to influence the audience's perception or emotional response.

**Example (Content):** "The company's stock fell 50%."
**Example (Presentational Cue - Alarmist):** "The company's stock suffered a catastrophic collapse, plummeting by a disastrous 50%." (Cue: 'catastrophic collapse,' 'plummeting,' 'disastrous').
**Example (Presentational Cue - Neutral):** "The company's stock decreased by 50%." (Cue: Neutral, factual verbs).
***
**9. Additional Important Call-Outs**

**+++ IMPORTANT CALL-OUT: LOADED RHETORICAL QUESTIONS AS ALARMIST CUES +++**
**Direct questions from the author or a quoted source that use explicitly loaded or emotionally charged language designed to imply an Alarmist frame, instill fear/urgency, or suggest a worrisome threat are often strong Alarmist cues.**
*   **Example (Author-driven, implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if context suggests framing a worrisome threat).
*   **Example (Quote-driven, implying disaster):** 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist.
*   **Critical Distinction:** Carefully distinguish these from neutral, purely information-seeking questions (which are Neutral).

**⚠ Verbs and Intensified Adjectives Can Also Frame (Examples for Alarmist):**
*   **Potent Verbs (Author/Source Driven):** `ravaged`, `soared` (e.g., prices soared), `swept across` (e.g., outbreak swept across), `plummeted` (when used to describe impact dramatically).
*   **Intensified Adjectives (Author/Source Driven):** `so deadly`, `particularly brutal`, `frighteningly contagious`, `catastrophic` (when used as part of author/source framing, not just a reported fact).
*   **(Note: These often become Alarmist when the author/source uses them to actively frame the situation, rather than as a purely technical or factual description. Context and the 'Principle of Cue Sufficiency' are key.)**

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:GUIDANCE_COMMON_MISINTERPRETATIONS -->
---
chunk_type: rule
rule_id: GUIDANCE_COMMON_MISINTERPRETATIONS
pattern_summary: Common LLM misinterpretations & how to avoid them.
dimension: META
parent_group: COMMON_MISINTERPRETATIONS
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: COMMON_MISINTERPRETATIONS
related: [Q7_BARE_NEGATION, Q8_CAPABILITY_PREPAREDNESS,
          Q9_FACTUAL_REPORTING]
---
**7\. Common LLM Misinterpretations & How to Avoid Them**

1. **Mistaking Large Numbers/Severe Outcomes for Alarmist Framing:** Large casualty counts, high costs, or severe statistics are Neutral if reported factually without explicit alarmist language from the author/source. Focus on *how* the numbers are presented, not their magnitude.

2. **Assuming Positive Facts (e.g., 'no human cases') are Always Reassuring:** The absence of negative events is Neutral unless the author/source adds explicit reassuring language to actively calm broader concerns.

3. **Treating Technical Terms as Inherently Alarmist:** Terms like "highly pathogenic," "depopulated," or "high mortality rate" are often Neutral when used as standard descriptors or official classifications.

4. **Confusing Capability/Preparedness Statements with Active Reassurance:** Describing safeguards, capabilities, or control measures is Neutral unless explicitly framed as a reason for current calm or minimized risk.

5. **Overweighting Single Negative Adjectives:** Mild terms like "concerning" or standard descriptors like "deadly" (when describing disease characteristics) are often Neutral unless part of broader alarmist rhetoric.

6. **NEW (v2.10) - Treating Bare Negations as Reassuring:** Statements like "not expected to cause problems" or "unlikely to affect production" are Neutral unless paired with explicit calming/safety cues (e.g., "so the risk remains low," "meaning consumers can be confident"). The negation alone is insufficient for Reassuring framing.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:GUIDANCE_CRITICAL_DISTINCTION -->
---
chunk_type: rule
rule_id: GUIDANCE_CRITICAL_DISTINCTION
pattern_summary: Critical distinction between information severity and framing style.
dimension: META
parent_group: CRITICAL_DISTINCTION
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: CRITICAL_DISTINCTION
related: [P6_PRECEDENCE_DEFAULT_NEUTRAL,
          Q12_DEFAULT_NEUTRAL]
---
**8\. Critical Distinction: Information Severity vs\. Framing Style**

A core principle of this codebook is the absolute and non-negotiable separation between the objective severity or positivity of an event/fact and the framing style used by the author/source to present it. Segments are NEVER coded Alarmist simply because they report bad news (e.g., deaths, outbreaks, high costs, risks) NOR Reassuring simply because they report good news (e.g., recovery, low numbers, successful prevention). The code MUST ALWAYS be based on the presence of explicit Alarmist or Reassuring framing cues in the language deliberately chosen by the author or quoted source. In the complete absence of such explicit framing cues from both author and quote, the segment is unquestionably Neutral, regardless of how concerning or encouraging the underlying facts may be to the coder or a general reader.
***
**Mini-Glossary: Content vs. Presentation**
* **Content/Fact:** The underlying event, statistic, or piece of information being reported (e.g., '100 birds died,' 'a vaccine was approved').
* **Presentational Cue:** The specific word choice, phrasing, tone, rhetorical strategy, or explicit evaluative language intentionally employed by the source or author to frame or make salient that content/fact, aiming to influence the audience's perception or emotional response.

**Example (Content):** "The company's stock fell 50%."
**Example (Presentational Cue - Alarmist):** "The company's stock suffered a catastrophic collapse, plummeting by a disastrous 50%." (Cue: 'catastrophic collapse,' 'plummeting,' 'disastrous').
**Example (Presentational Cue - Neutral):** "The company's stock decreased by 50%." (Cue: Neutral, factual verbs).
***
**9. Additional Important Call-Outs**

**+++ IMPORTANT CALL-OUT: LOADED RHETORICAL QUESTIONS AS ALARMIST CUES +++**
**Direct questions from the author or a quoted source that use explicitly loaded or emotionally charged language designed to imply an Alarmist frame, instill fear/urgency, or suggest a worrisome threat are often strong Alarmist cues.**
*   **Example (Author-driven, implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if context suggests framing a worrisome threat).
*   **Example (Quote-driven, implying disaster):** 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist.
*   **Critical Distinction:** Carefully distinguish these from neutral, purely information-seeking questions (which are Neutral).

**⚠ Verbs and Intensified Adjectives Can Also Frame (Examples for Alarmist):**
*   **Potent Verbs (Author/Source Driven):** `ravaged`, `soared` (e.g., prices soared), `swept across` (e.g., outbreak swept across), `plummeted` (when used to describe impact dramatically).
*   **Intensified Adjectives (Author/Source Driven):** `so deadly`, `particularly brutal`, `frighteningly contagious`, `catastrophic` (when used as part of author/source framing, not just a reported fact).
*   **(Note: These often become Alarmist when the author/source uses them to actively frame the situation, rather than as a purely technical or factual description. Context and the 'Principle of Cue Sufficiency' are key.)**
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q1_INTENSIFIER_RISKADJ -->
---
chunk_type: rule
rule_id: Q1_INTENSIFIER_RISKADJ
outcome: Alarmist
precedence_rank: 20
pattern_summary: Intensifier or comparative + risk-adjective (e.g., \'so deadly\').
regex_trigger: \'\\b(highly|very|deadlier|more|extremely|severely|so|particularly|frighteningly)\\s+(deadly|lethal|dangerous|severe|catastrophic|brutal|contagious|virulent|destructive)\\b \'
dimension: Q1_INTENSIFIER_RISKADJ
parent_group: INTENSIFIER_RISKADJ
tags:
- core
---
**Q1: Intensifier/Comparative + Risk-Adjective**
Does the segment feature an intensifier (e.g., 'so,' 'very,' 'extremely') or a comparative adjective (e.g., 'more,' 'deadlier') directly modifying a risk-adjective (e.g., 'deadly,' 'dangerous,' 'severe,' 'catastrophic') as defined in the detailed rules?

**🔍 Q1 Pattern Recognition Table:**
| **Pattern Type** | **Examples** | **→ Alarmist** |
|------------------|--------------|----------------|
| **Intensifier + Risk-Adj** | "so deadly," "very dangerous," "extremely severe," "highly lethal," "frighteningly contagious" | ✓ |
| **Comparative + Risk-Adj** | "more deadly," "deadlier," "more dangerous," "less safe," "increasingly severe" | ✓ |
| **Base Risk-Adj (alone)** | "deadly," "dangerous," "severe" (without intensifier) | → Neutral |

**🔗 See also:** Q2 for high-potency verbs; Q4 for loaded questions that may contain intensified language

*   Yes → Label: Alarmist. Justification: Refer to `step-1-details`.
*   No → Proceed to Q2.
<details id="step-1-details">
**Source Content from 2.25.md:**

From "⏩ 60-Second Cue Cheat-Sheet":

**‼ RULE 1 QUICK MEMORY HOOK**
• "Highly/very/so/more + deadly/lethal/dangerous" ⇒ Alarmist every time

| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **Intensifier/Comparative + Risk-Adjective** | Alarmist | **Any single match is sufficient (Precedence #1)** |
| - so/very/extremely/highly/frighteningly/particularly + deadly/lethal/dangerous/brutal/severe/contagious/virulent/destructive | | |
| - more/less/deadlier/safer/higher/lower + same risk adjectives | | |
| *(Risk-adjective list is illustrative, not exhaustive)* | | |

From "Alarmist - Inclusion Criteria":
*   Authorial use of intensifiers (e.g., 'so,' 'very,' 'extremely,' 'incredibly,' 'particularly,' 'frighteningly') coupled with high-valence negative adjectives (e.g., 'destructive,' 'contagious') to describe the subject or its characteristics. The intensifier must clearly serve to heighten the emotional impact of the negative descriptor, pushing it beyond a factual statement of degree. Example: Author: 'Because the virus is *so deadly* to this species, culling is the only option.' → Alarmist. (Rationale: The intensifier 'so' amplifies 'deadly,' emphasizing the extreme nature and justifying the severe consequence, thereby framing the virus itself in alarming terms.)
    *   **Clarification on "deadly," "fatal," "lethal":** These terms when modified by an intensifier (e.g., 'so deadly,' 'extremely fatal,' 'particularly lethal,' 'frighteningly deadly') are Alarmist. Without such direct intensification, "deadly" (etc.) describing a factual characteristic (e.g., 'Avian flu can be deadly in domestic poultry') is typically Neutral unless other alarmist cues are present.
    *   **Minimal Pair Example:**
        *   **Neutral:** "The virus is contagious."
        *   **Alarmist (Author):** "The virus is frighteningly contagious, spreading like wildfire." (Cue: 'frighteningly,' 'spreading like wildfire').
    *   **New Comparative Minimal Pair Example:**
        *   **Alarmist:** "Scientists warn the virus is becoming deadlier each season."
        *   **Neutral:** "Scientists track how the virus becomes more common each season."

From "Alarmist - Key Differentiators / Technical Terms":
> ⚠ **TECHNICAL OR CLINICAL TERMS**  
> A term like *deadly, lethal, fatal* **by itself** can still be Neutral when used *clinically* (e.g. "lethal dose 50").  
> **BUT** if the same term is paired with *any intensifier or emotive verb* (see Cue-Intensity Table) → **Alarmist (Precedence #1)**

From "Few-Shot Exemplars":
| **Category** | **Example Sentence** | **Correct Label** | **Key Cue** |
|--------------|---------------------|-------------------|--------------|
| **Alarmist – Intensifier + adjective** | "The flu is so deadly that entire flocks are culled." | **Alarmist** | "so deadly" (intensifier + risk adjective) |
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q2_HIGH_POTENCY_VERB -->
---
chunk_type: rule
rule_id: Q2_HIGH_POTENCY_VERB
outcome: Alarmist
precedence_rank: 21
pattern_summary: High-potency verb or metaphor (e.g., \'ravaged\', \'ticking time-bomb\').
regex_trigger: "\\b(ravaged|devastated|skyrocketed|crippling|unleashed|slaughtered|exploding|raging|tearing through|overwhelmed|crashed|nosedived|tanked)\\b"
dimension: Q2_HIGH_POTENCY_VERB
parent_group: HIGH_POTENCY_VERB
tags:
- core
---
**Q2: High-Potency Verb/Metaphor**
Does the author or a quoted source employ a high-potency verb (e.g., 'ravaged,' 'skyrocketed,' 'crippling') or a potent metaphor (e.g., 'ticking time-bomb,' 'nightmare scenario') to describe the event or its impacts, where such language actively frames the situation alarmingly, as detailed in the rules?

**🔍 Q2 Pattern Recognition Table:**
| **Pattern Type** | **Examples** | **→ Alarmist** |
|------------------|--------------|----------------|
| **High-Potency Verbs** | "ravaged," "devastated," "skyrocketed," "plummeted," "crashed," "nosedived," "tanked," "crippling," "unleashed," "slaughtered" | ✓ |
| **Potent Metaphors** | "ticking time-bomb," "nightmare scenario," "raging inferno," "powder keg," "house of cards" | ✓ |
| **Moderate Verbs (alone)** | "hit," "swept," "surged" (without scale/impact details) | → Neutral |

**🔗 See also:** Q3 for moderate verbs paired with scale/impact; Q1 for intensified adjectives

*   Yes → Label: Alarmist. Justification: Refer to `step-2-details`.
*   No → Proceed to Q3.
<details id="step-2-details">
**Source Content from 2.25.md:**

From "⏩ 60-Second Cue Cheat-Sheet":
| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **High-potency verb/metaphor** ("ravaged", "skyrocketed", "crippling") | Alarmist | Check *Potent Verb* list in Appendix A |

From "⚠ Verbs and Intensified Adjectives Can Also Frame (Examples for Alarmist)":
*   **Potent Verbs (Author/Source Driven):** `ravaged`, `soared` (e.g., prices soared), `swept across` (e.g., outbreak swept across), `plummeted` (when used to describe impact dramatically).
*   **(Note: These often become Alarmist when the author/source uses them to actively frame the situation, rather than as a purely technical or factual description. Context and the 'Principle of Cue Sufficiency' are key.)**

From "Alarmist - Inclusion Criteria":
*   Authorial use of vivid, active verbs or metaphors to describe the spread or impact of a threat, especially when combined with its scale or severity, thereby emphasizing its uncontrolled, rapid, or overwhelming nature. Example: Author: 'The wildfire swept across the valley, devouring homes and forcing thousands to flee.' → Alarmist. (Rationale: 'Swept across' and 'devouring' are vivid, active verbs creating a sense of uncontrolled destructive power.)

From "Alarmist - Examples":
*   "The economic impact of the subject on the agricultural sector is a ticking time-bomb for food security," said the analyst. (Alarmist → The analyst's quote uses a potent metaphor "ticking time-bomb," framing the economic impact with fear/urgency.)
*   Author: "Political inaction is steering us towards a catastrophic crisis related to the subject." (Alarmist → Author's framing of political aspect through loaded language like "catastrophic crisis," assuming no overriding framed quote.)
*   **Example (Author-driven, vivid metaphor & intensifier):**
    *   Author: "The virus is a raging inferno, tearing through populations with terrifying speed, leaving devastation in its wake."
    *   Reasoning: "Alarmist (Author-driven). Author uses vivid metaphor 'raging inferno,' 'tearing through,' 'terrifying speed,' and 'devastation in its wake.' Decisive cues: 'raging inferno,' 'terrifying speed'."
*   **Example (Vivid verb + scale from Author):** Author: "The disease ravaged poultry flocks across three states, leading to immense economic losses." (Alarmist → 'Ravaged' + 'across three states' + 'immense economic losses' create a strong alarmist frame).
*   **Example (Vivid verb + scale from Author):** Author: "Confirmed cases soared past one million, overwhelming healthcare systems." (Alarmist → 'Soared past one million' + 'overwhelming healthcare systems' creates a strong alarmist frame).

From "Few-Shot Exemplars":
| **Category** | **Example Sentence** | **Correct Label** | **Key Cue** |
|--------------|---------------------|-------------------|--------------|
| **Alarmist – High-potency verb** | "An outbreak ravaged farms across three states." | **Alarmist** | "ravaged" (vivid, destructive verb) |

**Boundary guard:** If the verb is "hit / hitting / swept / surged" but the segment gives no numbers, adjectives or metaphors that convey magnitude, treat it as Neutral. Alarmist fires only when a concrete scale/impact phrase is coupled.

(See also Appendix A for more illustrative verbs and metaphors. The 'Principle of Cue Sufficiency' is paramount.)
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q3_MODERATE_VERB_SCALE -->
---
chunk_type: rule
rule_id: Q3_MODERATE_VERB_SCALE
outcome: Alarmist
precedence_rank: 22
pattern_summary: Moderate verb + scale/metric (e.g., \'swept across + millions culled\').
regex_trigger: \'\\b(hit|swept|surged|soared|plunged|plummeted|prompted|culled)\\b[^.?!]{0,70}(million|thousand|record|largest|%|percent|cost|losses|wave|number of|significant number of) \'
dimension: Q3_MODERATE_VERB_SCALE
parent_group: MODERATE_VERB_SCALE
tags:
- core
---
**Q3: Moderate Verbs + Scale/Impact**
Does the author or a quoted source use a 'moderate verb' (e.g., 'swept across,' 'hard hit,' 'soared,' 'plummeted') AND is this verb explicitly paired with information detailing significant scale or impact (e.g., 'millions culled,' 'record losses,' 'overwhelming systems'), as detailed in the rules?
*   Yes → Label: Alarmist. Justification: Refer to `step-3-details`.
*   No → Proceed to Q4.
<details id="step-3-details">
**Source Content from 2.25.md:**

From "⏩ 60-Second Cue Cheat-Sheet":
| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **Moderate verbs** ("swept across", "hard hit", "soared", "plummeted") | Alarmist | **Only when** paired with scale/impact ("millions culled", "record losses") |

From "Alarmist - Examples":
*   Author: "The region was severely hit by the virus, resulting in record losses." (Alarmist → Author's use of "severely hit" and "record losses" to describe large-scale harm, assuming no overriding framed quote.)
*   Author: 'From Wyoming to Maine, the highly contagious bird flu swept across farms and backyard flocks, prompting millions of chickens and turkeys to be culled.' (Alarmist → The author's use of 'swept across' combined with 'highly contagious' and the large-scale consequence 'millions...culled' creates an alarmist depiction of an overwhelming, uncontrolled event, assuming no overriding framed quote.)
*   **Example (Evaluative adjective + scale from Author):** Author: "The agricultural sector was hard hit by the drought, with crop yields plummeting by over 50%." (Alarmist → 'Hard hit' coupled with the specific, severe scale of 'plummeting by over 50%' framed by the author).

Note: "swept across," "hard hit," "soared," "plummeted" can be potent verbs on their own (see Q2) if used dramatically. This rule specifically addresses their use when their alarmist nature is confirmed by accompanying details of scale/impact.
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q4_LOADED_RHETORICAL_QUESTION -->
---
chunk_type: rule
rule_id: Q4_LOADED_RHETORICAL_QUESTION
outcome: Alarmist
precedence_rank: 23
pattern_summary: Loaded rhetorical question implying worry/alarm.
dimension: Q4_LOADED_RHETORICAL_QUESTION
parent_group: LOADED_RHETORICAL_QUESTION
tags:
- core
regex_trigger: "\\b(?:should|can|could|will)\\s+\\w+\\s+(?:be\\s+)?(?:worried|concerned)\\b"
---
**Q4: Loaded Rhetorical Question for Alarm**
Does the author or a quoted source pose a loaded rhetorical question that is clearly designed to imply an Alarmist frame, instill fear/urgency, or suggest a worrisome threat (e.g., 'Should consumers worry...?', 'Are we simply going to stand by while this disaster unfolds?') AND is it distinguishable from a neutral, purely information-seeking question, as detailed in the rules?

**🔍 Q4 Pattern Recognition Table:**
| **Pattern Type** | **Examples** | **→ Alarmist** |
|------------------|--------------|----------------|
| **Loaded Questions (Worry/Fear)** | "Should consumers worry...?" "Are we facing a crisis?" "Is it safe to...?" | ✓ |
| **Loaded Questions (Inaction)** | "Are we going to stand by while this unfolds?" "How long can we ignore this?" | ✓ |
| **Neutral Information-Seeking** | "What are the safety protocols?" "When will results be available?" | → Neutral |

*   Yes → Label: Alarmist. Justification: Refer to `step-4-details`.
*   No → Proceed to Q5.
<details id="step-4-details">
**Source Content from 2.25.md:**

From "⏩ 60-Second Cue Cheat-Sheet":
| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **Loaded rhetorical question** ("Should consumers worry…?") | Alarmist | Q implies heightened danger |

From "+++ IMPORTANT CALL-OUT: LOADED RHETORICAL QUESTIONS AS ALARMIST CUES +++" (first instance):
**Direct questions from the author or a quoted source that use explicitly loaded or emotionally charged language designed to imply an Alarmist frame, instill fear/urgency, or suggest a worrisome threat are often strong Alarmist cues.**
*   **Example (Author-driven, implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if context suggests framing a worrisome threat).
*   **Example (Quote-driven, implying disaster):** 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist.
*   **Critical Distinction:** Carefully distinguish these from neutral, purely information-seeking questions (which are Neutral).

From "Alarmist - Inclusion Criteria":
*   Direct questions from the author that use explicitly loaded or emotionally charged language clearly designed to imply an Alarmist frame or instill fear/urgency in the reader.
    *   **Example:**
        *   **Author:** "With the system collapsing, can anyone truly feel safe anymore?" (Alarmist. Cues: 'system collapsing,' 'truly feel safe anymore?' - rhetorical question implying no).
        *   **Non-Example (Neutral):** Author: "What are the safety protocols in place?" (Information-seeking).
*   Use of loaded rhetorical questions by the quoted source or author that are designed to evoke fear, urgency, or strong concern by implying a severe problem or a dire lack of action.
    *   Example (Author-driven): 'How many more animals have to die before we finally act decisively?' → Alarmist. (Rationale: The rhetorical question uses emotive language 'have to die' and implies criticism of inaction, framing the situation as urgent and severe.)
    *   Example (Quote-driven): 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist. (Rationale: The quoted rhetorical question uses 'disaster unfolds' to frame the situation alarmingly.)
    *   **Example (Rhetorical question from author implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if the context suggests this is not a simple information request but a way to frame emerging variants as a worrisome threat).

From "Few-Shot Exemplars":
| **Category** | **Example Sentence** | **Correct Label** | **Key Cue** |
|--------------|---------------------|-------------------|--------------|
| **Alarmist – Loaded Q** | "Should consumers be worried about buying eggs?" | **Alarmist** | Loaded rhetorical question implying worry |
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q5_EXPLICIT_CALMING -->
---
chunk_type: rule
rule_id: Q5_EXPLICIT_CALMING
outcome: Reassuring
precedence_rank: 24
pattern_summary: Explicit calming cue communicating current safety/control.
dimension: Q5_EXPLICIT_CALMING
parent_group: EXPLICIT_CALMING
tags:
- core
regex_trigger: "\\b(?:no\\s+cause\\s+for\\s+alarm|public\\s+can\\s+rest\\s+easy|fully\\s+under\\s+control|completely\\s+safe)\\b"
---
**Q5: Explicit Calming Cue for Reassurance**
Does the author or a quoted source provide an explicit calming cue (e.g., 'no cause for alarm,' 'public can rest easy,' 'situation is fully contained,' 'excellent news and means citizens are very well protected') that directly communicates current safety, control, or significantly minimized present risk, as detailed in the Reassuring frame criteria?
*   Yes → Label: Reassuring. Justification: Refer to `step-5-details`.
*   No → Proceed to Q6.
<details id="step-5-details">
**Source Content from 2.25.md (Defining Reassuring Frame):**

From "⏩ 60-Second Cue Cheat-Sheet":
| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **Explicit calming cue** ("no cause for alarm", "public can rest easy") | Reassuring | Direct statement of *current* safety |

**Definition: Reassuring** (Synthesized from principles, common pitfalls, and examples in 2.25)
Statement, either through a directly quoted source or the author's own presentation, demonstrably employs explicit language, tone, or rhetorical devices specifically chosen by the author or quoted source to actively calm audience concerns, minimize perceived current risk, emphasize safety/control, or highlight positive aspects in a way designed to reduce worry regarding the subject or its impacts. The intent to reassure must be evident in the presentation, not inferred from the facts being merely positive. If a quoted source is Reassuring, the segment is Reassuring even if the author's narration is neutral.

**Key Differentiators from Neutral (Crucial for Borderline Cases for Reassuring):**
*   Neutral reports positive facts; Reassuring adds explicit calming/optimistic amplification.
*   Neutral uses standard descriptive terms for positive outcomes; Reassuring frames them with active confidence or relief.
*   Neutral states low risk factually; Reassuring actively frames this as a reason for calm or safety.
*   Neutral reports solutions/capabilities; Reassuring links them directly to present safety or significantly reduced current risk.

**Inclusion Criteria (Reassuring):**
*   A directly quoted source uses language fitting the Reassuring criteria.
*   Authorial or quoted source's use of explicit calming language or risk-minimizing evaluations designed to reduce audience concern or signal that the situation is under control, safe, or significantly less threatening than might be perceived. (e.g., "no cause for alarm," "public can rest easy," "situation is fully contained," "this is excellent news," "fortunately, the risk is very low," "we are confident," "this means consumers are safe").
*   Statements that not only report positive facts but also explicitly frame these facts as reasons for reduced concern or increased confidence about safety or control.
    *   **Example:** "Vaccination rates have thankfully reached 80% in the target population, a wonderfully high figure that provides excellent protection and means the community is now much safer." (Reassuring. Cues: 'thankfully,' 'wonderfully high,' 'excellent protection,' 'much safer').
*   Direct assurances of safety, control, or manageability from the author or a quoted source.
    *   **Example:** "Quote: 'We have stockpiled 30 million doses of the antiviral, which is excellent news and means our citizens are very well protected against any immediate threat from this virus.'" (Reassuring. Cues: 'excellent news,' 'very well protected').
*   Use of 'Minimiser + scale contrast' (see Q6 for full details) where both elements are present and clearly work together to reassure.
*   Capability/Preparedness statements ONLY IF explicitly and actively framed by the author/source as a reason for *current* calm, *present* safety, or *substantially minimized present risk*.
    *   **Example:** "The agency's new rapid deployment plan is a game-changer, meaning that in the event of an emergency, the public can rest assured that help will arrive swiftly and effectively, significantly reducing any potential danger." (Reassuring. Cues: 'rest assured,' 'significantly reducing potential danger').

**Exclusion Criteria (What is NOT Reassuring, often Neutral):**
*   Statements merely reporting positive factual outcomes (e.g., "no further cases were reported," "tests were negative," "patient recovered") or the simple absence of negative events, if NOT explicitly framed with additional calming/reassuring language by the author/source.
    *   **Canonical NON-EXAMPLE for Reassuring (Code: Neutral):** Text: "Despite the health department conducting contact tracing, no further cases of bird flu connected to the case have been reported at the time of writing." Reasoning: "Neutral. The author reports a positive fact (absence of new cases) using descriptive, neutral language. No explicit reassuring language (e.g., 'providing significant relief,' 'which is very encouraging news,' 'fortunately') is used by the author to actively frame these facts reassuringly."
*   Simple factual statements of capability, preparedness, or hopeful future possibilities if not explicitly linked to *present* safety or calm (see Rule C / Q8).
*   Bare negations (e.g., "not expected to cause problems," "unlikely to affect production") unless paired with explicit calming/safety cues (see Q7).
*   Vague positive language without specific commitment to current safety or substantial risk reduction.

**Minimal Pair Examples for Reassuring vs. Neutral:**
*   **Neutral:** "The company announced profits increased by 10%."
    *   Reasoning: "Neutral. Factual report of a positive outcome. No active reassuring framing from the author/source."
*   **Reassuring:** "The company was pleased to announce profits soared by 10%, a reassuring sign that our strategy is working and the future looks secure."
    *   Reasoning: "Reassuring (Author/Source-driven). Uses 'pleased to announce,' 'soared,' 'reassuring sign,' and 'future looks secure' to actively frame the positive outcome. Decisive cues: 'reassuring sign,' 'future looks secure'."
*   **Neutral:** "Segment: 'The latest tests on the water supply showed no contaminants.'"
    *   Reasoning: "Neutral. Reports absence of negative. No explicit reassuring language from the author/source about broader safety."
*   **Reassuring:** "Segment: 'Officials confirmed the latest tests on the water supply showed no contaminants, declaring, "This is excellent news, and residents can be fully confident in the safety of their drinking water."'"
    *   Reasoning: "Reassuring (Quote-driven). The official's quote explicitly frames the negative test as 'excellent news' and a reason for 'full confidence' and 'safety.' Decisive cues: 'excellent news,' 'fully confident in the safety'."

From "SIDEBAR: The Symmetry Rule":
**For Reassuring:** Positive facts require explicit calming cues
- "Not expected to lower production" → Neutral (bare negation)
- "Not expected to lower production, so the risk remains very low" → Reassuring (calming cue added)
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q6_MINIMISER_SCALE_CONTRAST -->
---
chunk_type: rule
rule_id: Q6_MINIMISER_SCALE_CONTRAST
outcome: Reassuring
precedence_rank: 25
pattern_summary: Minimiser + scale contrast for reassurance (e.g., \'only one barn
  out of thousands\').
dimension: Q6_MINIMISER_SCALE_CONTRAST
parent_group: MINIMISER_SCALE_CONTRAST
tags:
- core
regex_trigger: "\\b(?:only|just|merely)\\b.{0,40}\\b(?:out\\s+of|among|outnumber)\\b"
---
**Q6: \'Minimiser + Scale Contrast\' for Reassurance**
Does the author or a quoted source use a 'minimiser' (e.g., 'only,' 'just,' 'merely') in conjunction with a 'scale contrast' (e.g., 'one barn out of thousands,' 'a few cases among millions') to actively downplay an event or its significance, thereby framing it reassuringly, as detailed in the rules? (Both elements must be present and work together).
*   Yes → Label: Reassuring. Justification: Refer to `step-6-details`.
*   No → Proceed to Q7.
<details id="step-6-details">
**Source Content from 2.25.md:**

From "⏩ 60-Second Cue Cheat-Sheet":
| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **'Minimiser + scale contrast'** ("*only* one barn out of thousands") | Reassuring | Both elements required |

From "Few-Shot Exemplars":
| **Category** | **Example Sentence** | **Correct Label** | **Key Cue** |
|--------------|---------------------|-------------------|--------------|
| **Reassuring – Minimiser + contrast** | "Only one barn was infected out of thousands nationwide." | **Reassuring** | "Only...out of thousands" (minimizer + scale contrast) |

**Elaboration:** For this rule to apply, the statement must contain both a minimizing word (like 'only,' 'just,' 'merely,' 'a single,' 'few') and an explicit or clearly implied contrasting larger scale or context that makes the minimized number seem insignificant. The combination should create an overall reassuring effect about the limited scope or impact of an issue.
*   Example: "While there were concerns, only 3 out of 5,000 tested samples showed any irregularity, indicating the problem is not widespread." → Reassuring.
*   Non-Example (Missing Contrast): "Only 3 samples showed irregularity." → Could be Neutral if the "out of X" contrast is missing and no other reassuring cues are present.
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q7_BARE_NEGATION -->
---
chunk_type: rule
rule_id: Q7_BARE_NEGATION
outcome: Neutral
precedence_rank: 26
pattern_summary: Bare negation without explicit calming cue.
regex_trigger: \'\\b(no|not|doesn\\\'t|do not|never|isn\\\'t|are not|was not|were not|lack of|absence of|unlikely to)\\b[^.?!]{0,50}(cases|impact|risk|concern|infected|enter|affect|cause|problem|reported|detected|expected) \'
dimension: Q7_BARE_NEGATION
parent_group: BARE_NEGATION
tags:
- core
---
**Q7: Bare Negation without Explicit Calming Cue**
Does the segment merely state a 'bare negation' (e.g., 'not expected to cause problems,' 'unlikely to affect X,' 'no human cases detected,' 'tests were negative') WITHOUT any accompanying explicit calming cue from the author/source that actively frames this as reassuring about the broader situation, as detailed in the rules?

**🔍 Q7 Pattern Recognition Table:**
| **Pattern Type** | **Examples** | **→ Neutral** |
|------------------|--------------|---------------|
| **Expectation Negations** | "not expected to cause problems," "unlikely to affect consumers," "not anticipated to impact" | ✓ |
| **Evidence Negations** | "no evidence of transmission," "no human cases detected," "tests were negative" | ✓ |
| **Risk Negations** | "doesn't pose a risk," "will not impact food supply," "not expected to enter" | ✓ |
| **Capability Negations** | "viruses do not transmit easily," "cannot survive in," "does not spread through" | ✓ |
| **Bare Negation + Calming Cue** | "no cases detected, so consumers can be confident," "unlikely to affect supply, keeping risk very low" | → Reassuring |

**🔗 See also:** Q8 for capability statements; Q5-Q6 for explicit reassuring patterns

*   Yes → Label: Neutral. Justification: Refer to `step-7-details`.
*   No → Proceed to Q8.

**🚫 RED-FLAG REMINDER – Do not reward bare negatives**
"does not expect impact," "no Americans infected," "birds will not enter the food system" are Neutral unless a distinct calming phrase follows (e.g., "so consumers can be confident").

⚠️ **Additional problematic phrasings that remain NEUTRAL:**
- "unlikely to affect consumers"
- "no evidence of transmission"  
- "doesn't pose a risk to humans"
- "not expected to cause problems"
- "will not impact food supply"

Reassurance requires a second clause that explicitly spells out calm/safety.
<details id="step-7-details">
**Source Content from 2.25.md:**

From "⏩ 60-Second Cue Cheat-Sheet":
| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **Bare negation** ("not expected", "unlikely to affect") | Neutral | Stays Neutral unless paired with explicit calming cue |

From "Common LLM Misinterpretations & How to Avoid Them":
6. **NEW (v2.10) - Treating Bare Negations as Reassuring:** Statements like "not expected to cause problems" or "unlikely to affect production" are Neutral unless paired with explicit calming/safety cues (e.g., "so the risk remains low," "meaning consumers can be confident"). The negation alone is insufficient for Reassuring framing.

From "SIDEBAR: The Symmetry Rule":
**For Reassuring:** Positive facts require explicit calming cues
- "Not expected to lower production" → Neutral (bare negation)
- "Not expected to lower production, so the risk remains very low" → Reassuring (calming cue added)

**Elaboration:** A bare negation simply denies or downplays a risk/problem factually. To become Reassuring, it needs an additional linguistic layer that explicitly interprets this negation as a reason for calm or safety.
*   **Neutral (Bare Negation):** "Officials stated the new variant is not expected to be more severe."
*   **Reassuring (Bare Negation + Calming Cue):** "Officials stated the new variant is not expected to be more severe, meaning current health measures remain effective and there's no need for additional public concern."
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q8_CAPABILITY_PREPAREDNESS -->
---
chunk_type: rule
rule_id: Q8_CAPABILITY_PREPAREDNESS
outcome: Neutral
precedence_rank: 27
pattern_summary: Capability/preparedness statement without active reassurance.
dimension: Q8_CAPABILITY_PREPAREDNESS
parent_group: CAPABILITY_PREPAREDNESS
tags:
- core
regex_trigger: ""
---
**Q8: Capability/Preparedness Statement without Active Reassurance (Rule C Test)**
Does the segment describe capabilities, preparedness measures, hopeful future possibilities, or implemented safeguards (e.g., 'officials are working to contain,' 'vaccine can be made in X weeks,' 'systems are in place') WITHOUT the author or quoted source explicitly and actively linking these to a state of *current* calm, *present* safety, or *substantially minimized present risk* for the audience, as detailed in Rule C and related guidance?

**🔍 Q8 Pattern Recognition Table:**
| **Pattern Type** | **Examples** | **→ Neutral** |
|------------------|--------------|---------------|
| **Development Capabilities** | "vaccine can be made in X weeks," "researchers are developing treatments," "antiviral stockpiled" | ✓ |
| **Response Measures** | "officials are working to contain," "systems are in place," "protocols are being followed" | ✓ |
| **Preparedness Statements** | "we have the resources," "plans are ready," "surveillance is ongoing" | ✓ |
| **Future Possibilities** | "restrictions may be short-lived," "situation could improve," "recovery expected" | ✓ |
| **Capability + Active Reassurance** | "stockpiled 30M doses, which is excellent news and means citizens are very well protected," "systems in place, so public can rest easy" | → Reassuring |

**🔗 See also:** Q7 for bare negations; Q5-Q6 for active reassuring patterns; Q10 for future speculation

*   Yes → Label: Neutral. Justification: Refer to `step-8-details`.
*   No → Proceed to Q9.
<details id="step-8-details">
**Source Content from 2.25.md:**

> **Rule C — Capability ≠ Reassurance.**  
> A statement of capability, preparedness, or hopeful possibility ("officials are working to contain…", "restrictions may be short-lived") remains **Neutral** unless it *explicitly* links to present safety ("so the public can relax").

From "Common Pitfalls & Guiding Micro-Rules":
**(C) Capability / Preparedness Statements ≠ Active Reassurance**
*   Micro-Rule: Statements describing capabilities, preparedness measures (future or existing), implemented safeguards, capacities, or potential positive future actions (e.g., "a vaccine can be made in X weeks," "systems are in place to detect X," "we have the resources to respond," "new safeguards have been enacted") are categorically Neutral unless explicitly and actively framed by the author/source as a reason for current calm, safety, or substantially minimized present risk.
*   To be Reassuring, the author or quoted source MUST go beyond stating the capability and actively use explicit language to connect that capability to a state of present calm, safety, or significantly reduced current risk for the audience.
*   Canonical NON-EXAMPLE for Reassuring (Code: Neutral):
    *   Text: "'If a pandemic arises, once the genome sequence is known, an exact matched vaccine can be made in 6 weeks with mRNA technology and 4 months using the old egg-base methods,' she said."
    *   Incorrect Reasoning (to avoid): "Fast vaccine development is reassuring about capability, so it's Reassuring."
    *   Correct Codebook Reasoning: "Neutral. The quoted expert states a technical capability and timeline for a hypothetical future event. This statement lacks explicit calming or risk-minimizing language from the source (e.g., no 'fortunately,' 'this makes us very safe,' 'this is excellent news for our current preparedness,' 'the public can be reassured by this speed') to actively frame this capability as a reason for reassurance about existing or imminent risks."
*   **Minimal Pair Examples:**
    *   **Neutral:** "The agency has developed a rapid deployment plan for emergencies."
        *   Reasoning: "Neutral. States a capability. No explicit framing linking it to current reassurance."
    *   **Reassuring:** "The agency's new rapid deployment plan is a game-changer, meaning that in the event of an emergency, the public can rest assured that help will arrive swiftly and effectively, significantly reducing any potential danger."
        *   Reasoning: "Reassuring (Author-driven). Author explicitly links the plan to 'rest assured,' 'swiftly and effectively,' and 'significantly reducing potential danger.' Decisive cues: 'rest assured,' 'significantly reducing potential danger'."
    *   **Neutral:** "Quote: 'We have stockpiled 30 million doses of the antiviral.'"
        *   Reasoning: "Neutral. Quoted source states a fact about preparedness. Lacks explicit language from the source framing this as a reason for current public calm or safety."
    *   **Reassuring:** "Quote: 'We have stockpiled 30 million doses of the antiviral, which is excellent news and means our citizens are very well protected against any immediate threat from this virus.'"
        *   Reasoning: "Reassuring (Quote-driven). Quoted source explicitly frames the stockpile as 'excellent news' and a reason for being 'very well protected against any immediate threat.' Decisive cues: 'excellent news,' 'very well protected'."

From "Common LLM Misinterpretations & How to Avoid Them":
4. **Confusing Capability/Preparedness Statements with Active Reassurance:** Describing safeguards, capabilities, or control measures is Neutral unless explicitly framed as a reason for current calm or minimized risk. (See Common Pitfalls (C) and Reassuring - Exclusion Criteria.)
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q9_FACTUAL_REPORTING -->
---
chunk_type: rule
rule_id: Q9_FACTUAL_REPORTING
outcome: Neutral
precedence_rank: 28
pattern_summary: Factual reporting of prices/metrics without alarmist/reassuring framing.
dimension: Q9_FACTUAL_REPORTING
parent_group: FACTUAL_REPORTING
tags:
- core
regex_trigger: ""
---
**Q9: Factual Reporting of Prices/Metrics**
Is the segment primarily reporting prices, economic data, or other numerical metrics using standard descriptive verbs (e.g., 'rose,' 'declined,' 'increased,' 'fell') and potentially neutral adverbs (e.g., 'sharply,' 'significantly') BUT WITHOUT employing vivid/potent verbs (e.g., 'skyrocketed,' 'plummeted'), risk adjectives (e.g., 'catastrophic losses'), or other explicit alarmist/reassuring framing language from the author/source, as detailed in the rules for economic language?
*   Yes → Label: Neutral. Justification: Refer to `step-9-details`.
*   No → Proceed to Q10.
<details id="step-9-details">
**Source Content from 2.25.md:**

From "Quick Decision Tree ▼" (in main document):
3. **Is it reporting prices or other metrics?** 
   • If verbs like "rose/declined" or adverbs like "sharply" appear **without** a vivid verb or risk adjective → Neutral. 

From "##### Economic & Price Language Quick-Reference" (at the end of 2.25.md):
| Phrase (example) | Frame | Rationale |
|------------------|-------|-----------|
| "Prices **soared / skyrocketed**" | Alarmist | vivid verb |
| "Prices **trended sharply higher**" | Neutral | descriptive verb + adverb only |
| "Experts warn prices **could become volatile**" | Neutral | modal + mild adjective |

Adverbs such as **sharply, significantly, notably** do **not** raise potency *unless* paired with a vivid verb or risk adjective ("sharply worsening crisis").

From "Additional Nuanced Examples" (under Bedrock Principle):
* **Slightly Negative Fact + Neutral Framing:**
  * Segment: "Market prices for wheat decreased by 2% this month."
  * Reasoning: "Neutral. Factual report of a minor negative change. No explicit alarmist framing from the author."
* **Slightly Negative Fact + Alarmist Framing (Exaggeration):**
  * Segment: "Market prices for wheat took a devastating 2% dive this month, spelling trouble for farmers."
  * Reasoning: "Alarmist (Author-driven). Author uses 'devastating dive' and 'spelling trouble' to frame a minor decrease alarmingly. Decisive cues: 'devastating dive,' 'spelling trouble'."

**Elaboration:** This rule applies when the language is purely descriptive of economic or numerical trends without the author/source adding their own layer of alarmist or reassuring interpretation through word choice. Standard financial reporting language often falls here.
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q10_SPECULATION_RELIEF -->
---
chunk_type: rule
rule_id: Q10_SPECULATION_RELIEF
outcome: Neutral
precedence_rank: 29
pattern_summary: Speculation about future relief without explicit calming cue.
dimension: Q10_SPECULATION_RELIEF
parent_group: SPECULATION_RELIEF
tags:
- core
regex_trigger: ""
---
**Q10: Speculation about Relief without Explicit Calming**
Does the segment speculate about potential future relief or improvement (e.g., 'restrictions may be short-lived,' 'pressure could ease soon') WITHOUT an explicit calming cue from the author/source about the *current* state of risk or safety, as detailed in the rules?
*   Yes → Label: Neutral. Justification: Refer to `step-10-details`.
*   No → Proceed to Q11.
<details id="step-10-details">
**Source Content from 2.25.md:**

From "Quick Decision Tree ▼" (in main document):
4. **Does it speculate about relief ("may be short-lived", "could ease soon")?** 
   • Without an explicit calming cue → Neutral. 

**Elaboration:** Hopeful possibilities or predictions of future improvement are Neutral if the author/source does not use this speculation to make an explicit statement about current safety or reduced risk. The focus is on the *future possibility*, not a *present reassurance*.
*   **Neutral:** "Experts predict that the supply chain issues could ease in the next quarter."
*   **Neutral:** "There is hope that a new treatment may be available next year."
*   **Contrast with Reassuring:** If the statement was "Because these measures are working, restrictions may be short-lived, bringing welcome relief soon," the "because these measures are working" part, if framed as active present control, might shift it towards Reassuring, depending on potency.
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q11_FRAMED_QUOTATIONS -->
---
chunk_type: rule
rule_id: Q11_FRAMED_QUOTATIONS
outcome: Variable
precedence_rank: 30
pattern_summary: Primacy of framed quotations - label according to dominant quote\'s
  frame.
dimension: Q11_FRAMED_QUOTATIONS
parent_group: FRAMED_QUOTATIONS
tags:
- core
regex_trigger: ""
---
**Q11: Primacy of Framed Quotations - Dominant Quote Check**
Does a directly quoted source within the segment provide a clear, dominant Alarmist or Reassuring frame (per detailed definitions in `step-0-meta-details` and specific frame definitions) that is not overridden or equally balanced by other quotes or strong authorial counter-framing, as per the "Guidance Note: Primacy of Framed Quotations"?
*   Yes → Label according to the dominant quote's frame. Justification: Refer to `step-11-details`.
*   No (or quotes are Neutral/balanced/absent, or authorial frame is dominant) → Proceed to Q12.
<details id="step-11-details">
**Source Content from 2.25.md:**

From "Dimension 1 - General Rules & Guidance Notes":
**Guidance Note: Primacy of Framed Quotations (SUPERSEDES PREVIOUS QUOTE RULES)**
Core Principle: If a direct quotation (or a clearly attributed statement from a specific source) within the segment carries a distinct Alarmist or Reassuring frame, the segment's Dim1_Frame MUST reflect the frame of that quotation/attributed statement. This principle applies even if the author's narrative surrounding the quote is Neutral. The frame is determined by the language and tone used by the quoted source itself.

*   **Author's Neutrality:** When the author neutrally reports a framed quote, the quote's frame dictates the segment's frame.
*   **Author Reinforces Quote's Frame:** If the author's narrative also adopts or amplifies the same frame as the quote, this further strengthens the coding of the quote's frame.
*   **Author Challenges Quote's Frame (Advanced):** If the author explicitly challenges, refutes, or heavily recontextualizes the quote's frame using their own explicit framing language, the coder must determine the overall dominant frame of the segment. If the author merely presents a factual counterpoint after a framed quote, without adding their own framing to that counterpoint, the original quote's frame is more likely to prevail or be balanced to Neutral (see Mixed Messages). This scenario requires careful judgment of which frame is more salient. (For most cases, assume the author is not overtly challenging if they present the quote straightforwardly).
*   **Multiple Framed Quotes & Mixed Messages within a Single Quote:**
    *   If a segment contains multiple quotes with different frames, determine the dominant frame. If one quote is significantly more potent or central to the segment's point, its frame may prevail.
    *   **Handling Mixed Messages with Contrastive Conjunctions (e.g., 'but,' 'however'):**
        *   When a single quoted statement contains potentially mixed framing elements, particularly when linked by contrasting conjunctions (e.g., 'but,' 'however'):
            *   Evaluate Each Clause for Explicit Framing: Independently assess the clause before the conjunction and the clause after the conjunction for the presence of explicit framing cues that meet the definitions for Alarmist or Reassuring in this codebook. This means applying the full Alarmist/Reassuring/Neutral definitions to each part of the source's statement.
            *   Framing Strength of the Concluding Clause: For the clause after the conjunction to override or neutralize an explicitly framed initial clause, it MUST ITSELF contain clear and explicit framing language that meets the criteria for Reassuring or Alarmist. A neutrally worded factual statement, even if it factually counters or mitigates the initial clause, does not typically establish a new frame nor neutralize a potent initial frame on its own.
            *   Resolution Scenarios:
                *   Explicit Frame in Second Clause: If the second clause contains explicit framing cues (Reassuring or Alarmist) that are at least as potent as, or more potent than, the first clause (per 'Principle of Cue Sufficiency'), it will generally determine or significantly influence the segment's frame.
                *   No Explicit Framing in Second Clause (Canonical Example):
                    Text: "Meanwhile, Kirby Institute head of biosecurity Professor Raina MacIntyre described the bird flu news as 'concerning.' She [Professor Raina MacIntyre] said, however, that Avian flu viruses do not transmit easily in humans because they [Avian flu viruses] are adapted for birds."
                    Correct Code: Neutral.
                    Reasoning: "The source provides an initial mild-to-moderate alarm cue ('concerning'). The subsequent clause, introduced by 'however,' states a fact ('do not transmit easily') that has reassuring implications but is itself presented by the source without any explicit reassuring language from the source (e.g., no 'thankfully,' 'which is excellent news,' 'so the public can rest easy,' 'this low transmissibility means the risk is negligible'). The neutrally-presented factual counter-statement balances the initial mild concern without the second part actively meeting the criteria for a Reassuring frame on its own. Thus, the overall segment is Neutral."
                *   Additional Contrastive Example 1:
                    Text: "Quote: 'The outbreak is troubling, but no human infections have been detected,' stated the health commissioner."
                    Correct Code: Neutral.
                    Reasoning: "The source provides a mild alarm cue ('troubling'). The subsequent clause states a positive fact ('no human infections detected') without explicit reassuring framing from the source. The factual counter-statement balances the initial concern, resulting in Neutral rather than Reassuring."
                *   Additional Contrastive Example 2:
                    Text: "Quote: 'While cases have increased by 15%, testing capabilities remain adequate,' the director confirmed."
                    Correct Code: Neutral.
                    Reasoning: "Neither clause contains explicit framing. The negative fact (case increase) and positive capability statement are both presented factually by the source without alarm or reassuring amplification. Both parts are neutrally stated, resulting in Neutral overall."
</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:Q12_DEFAULT_NEUTRAL -->
---
chunk_type: rule
rule_id: Q12_DEFAULT_NEUTRAL
outcome: Neutral
precedence_rank: 31
pattern_summary: Default to Neutral if no explicit alarmist/reassuring cues found.
dimension: Q12_DEFAULT_NEUTRAL
parent_group: DEFAULT_NEUTRAL
tags:
- core
regex_trigger: ""
---
**Q12: Default to Neutral / Final Comprehensive Check**
After applying all preceding checks, are there NO remaining explicit and sufficient Alarmist or Reassuring framing cues (as defined in their respective detailed sections, considering cue potency and sufficiency from `step-0-meta-details`) from either the author or any quoted source? Is the presentation of any severe/positive facts purely factual and descriptive, leading to a Neutral frame by default as per the "Default-to-Neutral Rule"?
*   Yes → Label: Neutral. Justification: Refer to `step-12-details`.
*   No → *(This path suggests a cue type potentially missed or a nuanced case. Re-evaluate based on comprehensive Alarmist/Reassuring inclusion criteria not fitting simple top-level questions. The primary guidance for this should be within `step-0-meta-details` and the full definitions for Alarmist/Reassuring which will be populated in Pass 2 & 3).* Label: Re-evaluate.
<details id="step-12-details">
**Source Content from 2.25.md (Defining Neutral Frame by absence of other frames or by specific Neutral criteria):**

From "Quick Decision Tree ▼" (in main document):
5. **Default-to-Neutral Rule**

From "Dimension 1 - General Rules & Guidance Notes":
**Default-to-Neutral Rule (Strictly Presentation-Focused)**
Heuristic: In the absence of explicit emotional language, specific framing cues (e.g., loaded adjectives, urgent tone, calming words), or a distinct rhetorical tone from EITHER the segment's author OR any directly quoted source within the segment, Neutral is the appropriate code for Dim1_Frame.Crucial Clarification: This rule applies if both the author's presentation and the presentation by any quoted sources are neutral.

*   If a segment reports objectively severe facts, and both the author and any quoted source commenting on these facts use neutral, factual language without added alarmist rhetoric, the Dim1_Frame is Neutral.
*   Similarly, if a segment reports objectively positive facts, and both the author and any quoted source use neutral, factual language without added reassuring rhetoric, the Dim1_Frame is Neutral.
*   The focus remains on the presentation by the author and by any quoted sources.

**Definition: Neutral** (Synthesized from principles, common pitfalls, and examples in 2.25)
A segment is Neutral if it presents information factually without significant, explicit linguistic or rhetorical cues from the author or quoted sources that are designed to evoke strong fear, urgency (Alarmist), or to actively calm, reassure, or minimize risk (Reassuring). Neutral framing reports events, facts, or statements, even if objectively severe or positive, in a straightforward, descriptive manner.

**Examples of Neutral Framing (from "Bedrock Principle" and "Common Pitfalls")**
*   **Severe Fact, Neutral Presentation:**
    *   Segment: "The report documented 500,000 job losses in the last quarter."
    *   Reasoning: "Neutral. The author reports a severe statistic factually. No loaded language, intensifiers, or explicit alarmist rhetoric (e.g., 'a catastrophic wave of job losses,' 'an economic disaster unfolding') is used by the author to frame this fact."
*   **Positive Fact, Neutral Presentation:**
    *   Segment: "Vaccination rates reached 80% in the target population."
    *   Reasoning: "Neutral. The author reports a positive statistic factually. No explicit reassuring language (e.g., 'a wonderfully high rate providing excellent protection,' 'this achievement means the community is now safe') is used by the author."
*   **Canonical NON-EXAMPLE for Reassuring (Code: Neutral from Common Pitfalls A):**
    *   Text: "Despite the health department conducting contact tracing, no further cases of bird flu connected to the case have been reported at the time of writing."
    *   Correct Codebook Reasoning: "Neutral. The author reports a positive fact (absence of new cases) using descriptive, neutral language. No explicit reassuring language...is used by the author to actively frame these facts reassuringly."
*   **Canonical NON-EXAMPLE for Alarmist (Code: Neutral from Common Pitfalls B):**
    *   Text: "These [characteristics] include a wide host range, high mutation rate, genetic reassortment, high mortality rates, and genetic reassortment."
    *   Correct Codebook Reasoning: "Neutral. The author lists factual characteristics using neutral, descriptive language. No loaded adjectives...or explicit alarmist rhetoric are used by the author to actively frame these characteristics beyond their factual statement."
*   **Neutral (Capability/Preparedness - Rule C, Q8):** "The agency has developed a rapid deployment plan for emergencies."
*   **Neutral (Bare Negation - Q7):** "Not expected to lower production."
*   **Neutral (Factual Reporting of Prices/Metrics - Q9):** "Market prices for wheat decreased by 2% this month."
*   **Neutral (Speculation about Relief - Q10):** "Experts predict that the supply chain issues could ease in the next quarter."

**Further characteristics of Neutral framing include:**
*   Factual descriptions of phenomena that inherently possess negative-sounding descriptors (e.g., 'a high fever,' 'a high mortality rate,' 'a rapidly spreading virus') if the author/source does not add further explicit alarmist framing.
*   Listing a fatality/damage rate, case/incident count, or R-value/metric without evaluative language or alarming tone from either the quoted source or the author.
*   Reporting standard descriptive terms for negative events (e.g., 'outbreak,' 'death,' 'illness,' 'culling,' 'risk,' 'concern,' 'epidemic,' 'potential for X,' 'active outbreaks') without additional explicit alarmist cues.
*   Epistemic modals (e.g., 'could,' 'might,' 'may') expressing possibility alone, unless the potential outcome is itself framed with strong alarmist intensifiers or paired with other alarmist cues.
*   Technical terms, official classifications, and procedural language reported as factual designations.

See also Alarmist - Exclusion Criteria and Reassuring - Exclusion Criteria for what defaults to Neutral.
The "Neutral Verbs Reference" in Appendix provides examples of verbs that typically signal Neutral framing unless paired with other alarm cues.
</details>
***
<!-- CHUNK_END -->


<!-- CHUNK_START:META_MANDATORY_DECISION_PROCESS -->
---
chunk_type: rule
rule_id: META_MANDATORY_DECISION_PROCESS
pattern_summary: Instructions for the step-by-step decision process for coders.
dimension: META
parent_group: MANDATORY_DECISION_PROCESS
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: MANDATORY_DECISION_PROCESS
related: [Q0_INTRO, Q1_INTENSIFIER_RISKADJ, Q12_DEFAULT_NEUTRAL]
---
## MANDATORY: Step-by-Step Decision Process

**🚨 DELIBERATE: Work through the tree aloud one question at a time before outputting the JSON.**

Do NOT attempt one-shot pattern matching. You MUST:
1. Start with Q0 (Meta-Guidance Review) 
2. Proceed through Q1, Q2, Q3... in order
3. For each question, explicitly state "yes" or "no" and your reasoning
4. Only proceed to the next question if the current answer is "no"
5. Stop when you reach a "yes" answer and apply that label
6. If you reach Q12 and answer "yes," apply Neutral

This deliberate process prevents premature conclusions and ensures all high-priority rules are checked before lower-priority ones.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_OUTPUT_INSTRUCTIONS_SCHEMA -->
---
chunk_type: rule
rule_id: META_OUTPUT_INSTRUCTIONS_SCHEMA
pattern_summary: Mandatory output instructions, schema definition, and JSON formatting
  rules.
dimension: META
parent_group: OUTPUT_INSTRUCTIONS_SCHEMA
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: OUTPUT_INSTRUCTIONS_SCHEMA
---
## MANDATORY OUTPUT INSTRUCTIONS & SCHEMA FOR CLAIM FRAMING (Dimension 1)

**!! MANDATORY OUTPUT INSTRUCTIONS & SCHEMA FOR CLAIM FRAMING (Dimension 1) — CRITICAL: READ FIRST !!**

**§5 Final Schema Check & Self-Audit (MUST-FOLLOW)**
Before replying, silently verify your answer passes ALL rules in the "MANDATORY OUTPUT & SCHEMA DEFINITION" banner and this checklist. If not, you MUST correct it until it passes or output the exact string RETRY_AUDIT_FAILURE if perfect correction is impossible after attempting.

* **Output Format:** Is the output EITHER the exact string "NA/Not Applicable" OR a JSON object?
* **JSON SYNTAX CRITICAL:** If JSON, does it use ONLY double quotes (") for ALL keys and ALL string values? (If single quotes were generated, I must correct this or output RETRY_SYNTAX_ERROR).
* **CRITICAL RULE D (Content Trigger):** If the segment contained monetary figures or numerals > 0 explicitly linked to economic terms (cost, price, loss, compensation, culling counts), is the output a VALID JSON object (per rules 2-5) and NOT "NA/Not Applicable"? (This rule takes precedence).

**A. YOUR TASK & ABSOLUTE OUTPUT RULE:**
You are an information-extraction model. For EACH segment, your output MUST BE a PERFECTLY VALID JSON OBJECT adhering to all rules below.

‼️ **JSON SYNTAX CRITICAL FAILURE CONDITION:** Using single quotes (''') anywhere (for keys or string values) instead of double quotes (") is a CRITICAL FAILURE. You MUST use double quotes exclusively for all JSON keys and string values. If you realize you have produced single quotes, you MUST regenerate your response with correct double quotes or, if unable to self-correct perfectly, output an error indicator if the system allows, or a minimally valid JSON like {"error": "RETRY_SYNTAX_ERROR"}.

**B. REQUIRED FIELDS, VALID VALUES, AND FIELD EXCLUSIVITY (ALL MUST BE PRESENT AND CORRECT):**
Your JSON response for this Claim Framing task MUST ONLY contain the fields listed below (1-4).

**CRITICAL FIELD EXCLUSIVITY RULE:** DO NOT include any fields related to other dimensions or tasks, such as Dim22_EconomicFraming or ANY OTHER DimXX_... fields not specified here. The presence of ANY unspecified fields will result in a validation ERROR and rejection of your response.

1.  **"StatementID":** (This will be provided in the input, ensure it's copied to the output).
2.  **"Dim1_Frame":** MUST be one of the following exact string values: "Reassuring", "Neutral", "Alarmist".
3.  **"Dim4_AmbiguityNote":** A MANDATORY string. This note MUST provide the reasoning for the Dimension 1 coding decision for every segment. It cannot be "N/A" or an empty string.
4.  **"ContextUseNote":** A MANDATORY string. This note MUST state whether the broader article context (provided as {{FULL_TEXT}} in the input to this overall system) was consulted and meaningfully contributed to determining the "Dim1_Frame".
    * If the segment text alone provided sufficient cues and the {{FULL_TEXT}} was not consulted or did not meaningfully contribute to determining "Dim1_Frame", use the exact string: "Context was not consulted or did not meaningfully contribute to Dim1_Frame determination; segment text provided sufficient cues."
    * If you did consult the {{FULL_TEXT}} and it was helpful, confirmatory, added nuance, or was otherwise used to resolve ambiguity for determining "Dim1_Frame", briefly explain its role. Examples:
        * "Context from FULL_TEXT was consulted and confirmed the Dim1_Frame derived from segment cues."
        * "Context from FULL_TEXT was consulted to clarify the referent of 'this development', which helped confirm the Dim1_Frame."
        * "Context from FULL_TEXT was consulted and added nuance, supporting a more confident Dim1_Frame assessment."
        * "Context from FULL_TEXT was consulted and provided critical information (e.g., antecedent for 'this issue') necessary for Dim1_Frame determination."
    * If missing context (that might have previously been flagged by a now-removed ambiguity type) could not be resolved for "Dim1_Frame" even by looking at {{FULL_TEXT}} (or if {{FULL_TEXT}} wasn't helpful), you can state: "Context from FULL_TEXT was consulted but did not resolve the Dim1_Frame ambiguity."
    * This note should be concise and directly address the use of {{FULL_TEXT}} for "Dim1_Frame".

All fields from 1 to 4 are REQUIRED.

**C. JSON OUTPUT TEMPLATE:**json
{
"StatementID": "<statement_id_from_input>",
"Dim1_Frame": "<Value from §B.2>",
"Dim4_AmbiguityNote": "<MANDATORY free text note explaining the reasoning for the Dim1 coding decision. Cannot be N/A or empty.>",
"ContextUseNote": "<String based on guidance in §B.4>"
}

**(Implementation Note: For training/calibration, coders/LLMs should first process a standard calibration set (e.g., 3-5 pre-coded segments covering key distinctions) and compare results to a gold standard key. If significant discrepancies (e.g., ≥2/5 mismatches on Dim1 Frame) occur, halt and review codebook examples and guidance, paying special attention to the 'Dimension 1 - Guidance Note: Primacy of Framed Quotations,' 'Dimension 1 - Guidance Note: Principle of Cue Sufficiency,' and the 'Default-to-Neutral Rule,' before proceeding with live coding. A separate "Coder Implementation Guide & Checklist" document provides further practical advice and quality control procedures.)**
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FRAME_DEFINITIONS -->
---
chunk_type: rule
rule_id: META_FRAME_DEFINITIONS
pattern_summary: Detailed definitions and criteria for Alarmist, Reassuring, and Neutral
  frames.
dimension: META
parent_group: FRAME_DEFINITIONS
precedence_rank: 10
outcome: Meta
tags:
- core
child_ids: [META_FRAME_DEFINITIONS_D1,
            META_FRAME_DEFINITIONS_D2,
            META_FRAME_DEFINITIONS_D3,
            META_FRAME_DEFINITIONS_D4]
child_of: [FRAME_DEFINITIONS]
---
*Definitions moved to four child chunks (`_D1`…`_D4`) for RAG efficiency.*  
Original wording preserved verbatim in child chunks.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FRAME_DEFINITIONS_D1 -->
---
chunk_type: rule
rule_id: META_FRAME_DEFINITIONS_D1
dimension: META
parent_group: META_FRAME_DEFINITIONS
precedence_rank: 10
outcome: Meta
tags:
- core
references_rule_group: META_FRAME_DEFINITIONS
related: [Q1_INTENSIFIER_RISKADJ,
          Q2_HIGH_POTENCY_VERB,
          Q5_EXPLICIT_CALMING,
          Q6_MINIMISER_SCALE_CONTRAST]
---
<details id="mfd-d1"><summary>Dimension 1 – Frame definitions & examples</summary>

**DETERMINE THE CATEGORICAL FRAME!**
You MUST determine the primary Dim1_Frame ("Reassuring", "Neutral", or "Alarmist") based on the comprehensive definitions, inclusion/exclusion criteria, and general guidance notes for Dimension 1, paying special attention to the Guidance Note: Primacy of Framed Quotations and the Quick Decision Tree.

**+++ IMPORTANT BOXED NOTE START +++**
**A single high-potency cue (e.g., a vivid verb describing impactful action + scale, a loaded rhetorical question implying danger, or an intensifier + high-valence/loaded adjective) is often sufficient to assign Alarmist, per the Principle of Cue Sufficiency.**
**+++ IMPORTANT BOXED NOTE END +++**

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FRAME_DEFINITIONS_D2 -->
---
chunk_type: rule
rule_id: META_FRAME_DEFINITIONS_D2
dimension: META
parent_group: META_FRAME_DEFINITIONS
precedence_rank: 10
outcome: Meta
tags:
- core
references_rule_group: META_FRAME_DEFINITIONS
related: [Q3_BARE_NEGATION,
          Q4_LOADED_RHETORICAL_QUESTION]
---
<details id="mfd-d2"><summary>Dimension 2 – Alarmist Frame</summary>

### Code: Alarmist (Value for Dim1_Frame)

**(Reminder: One vivid cue from a quoted source or the author may qualify this frame—see Dimension 1 - Guidance Note: Principle of Cue Sufficiency under Core Foundational Principles.)**

**Definition:** Statement, either through a directly quoted source or the author's own presentation, demonstrably employs explicit language, tone, or rhetorical devices specifically chosen by the author or quoted source to evoke fear, a sense of urgency, extreme concern, or a strong sense of danger regarding the subject or its impacts. The intent to alarm must be evident in the presentation, not inferred from the facts. If a quoted source is Alarmist, the segment is Alarmist even if the author's narration is neutral.

**Key Differentiators from Neutral (Crucial for Borderline Cases)**
* Neutral reports severe facts; Alarmist adds explicit emotional amplification
* Neutral uses standard descriptive terms; Alarmist intensifies them dramatically
* Neutral states risks/threats factually; Alarmist frames them as imminent dangers
* Neutral reports problems; Alarmist characterizes them as crises or disasters

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FRAME_DEFINITIONS_D3 -->
---
chunk_type: rule
rule_id: META_FRAME_DEFINITIONS_D3
dimension: META
parent_group: META_FRAME_DEFINITIONS
precedence_rank: 10
outcome: Meta
tags:
- core
references_rule_group: META_FRAME_DEFINITIONS
related: [Q7_DATA_MAGNITUDE,
          Q8_VISUAL_DRAMATISATION]
---
<details id="mfd-d3"><summary>Dimension 3 – Reassuring Frame</summary>

### Code: Reassuring (Value for Dim1_Frame)

**Definition:** Statement, either through a directly quoted source or the author's own presentation, demonstrably employs explicit language, tone, or rhetorical devices specifically chosen by the author or quoted source to actively calm audience concerns, minimize perceived current risk, emphasize safety/control, or highlight positive aspects in a way designed to reduce worry regarding the subject or its impacts. The intent to reassure must be evident in the presentation, not inferred from the facts being merely positive. If a quoted source is Reassuring, the segment is Reassuring even if the author's narration is neutral.

**Key Differentiators from Neutral (Crucial for Borderline Cases for Reassuring):**
*   Neutral reports positive facts; Reassuring adds explicit calming/optimistic amplification.
*   Neutral uses standard descriptive terms for positive outcomes; Reassuring frames them with active confidence or relief.
*   Neutral states low risk factually; Reassuring actively frames this as a reason for calm or safety.
*   Neutral reports solutions/capabilities; Reassuring links them directly to present safety or significantly reduced current risk.

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FRAME_DEFINITIONS_D4 -->
---
chunk_type: rule
rule_id: META_FRAME_DEFINITIONS_D4
dimension: META
parent_group: META_FRAME_DEFINITIONS
precedence_rank: 10
outcome: Meta
tags:
- core
references_rule_group: META_FRAME_DEFINITIONS
related: [Q9_ECONOMIC_LANGUAGE,
          Q10_POLICY_IMPLICATION]
---
<details id="mfd-d4"><summary>Dimension 4 – Neutral Frame</summary>

### Code: Neutral (Value for Dim1_Frame)

**Definition:** A segment is Neutral if it presents information factually without significant, explicit linguistic or rhetorical cues from the author or quoted sources that are designed to evoke strong fear, urgency (Alarmist), or to actively calm, reassure, or minimize risk (Reassuring). Neutral framing reports events, facts, or statements, even if objectively severe or positive, in a straightforward, descriptive manner.

</details>
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_JUSTIFICATION_NOTE_DIM4 -->
---
chunk_type: rule
rule_id: META_JUSTIFICATION_NOTE_DIM4
pattern_summary: Guidelines for the mandatory Dim4_AmbiguityNote (justification note).
dimension: META
parent_group: JUSTIFICATION_NOTE_DIM4
precedence_rank: 99
outcome: Meta
tags:
- core
---
## Dimension 4: Justification Note (Mandatory)

**Purpose:** Provide a comprehensive free-text explanation for the Dimension 1 coding decision (Frame) for EVERY segment. This note is crucial for understanding the coder's rationale, ensuring consistency, and aiding in review or adjudication. It should specify whether the frame is driven by a quoted source or the author.

**Code: [MANDATORY Free Text Note]** This field must not be empty or "N/A".

**Definition:** A MANDATORY string. This note MUST provide the reasoning for the Dimension 1 coding decision. It cannot be "N/A" or an empty string. The note must briefly explain why the chosen frame applies, indicating if it's quote-driven or author-driven. Critically, the note MUST include a direct quotation of the primary word(s) or short phrase (ideally ≤12 words, but longer if necessary to capture a complex rhetorical device) from the segment text that served as the most decisive linguistic cue(s) for the Dim1_Frame determination. If the frame choice was difficult due to suspected sarcasm/irony (from author or quote) or because it relied on an accumulation of subtle cues rather than one single potent cue (especially for Neutral when potential weak cues were dismissed), the note MUST identify the specific phrase(s) or describe the situation, briefly explain the difficulty, and state why the chosen frame was selected.

**Inclusion Criteria:** MUST be provided for EVERY segment.
**Exclusion Criteria:** This field must NEVER be left blank or contain "N/A".

**Examples:**
* "Reasoning for Alarmist (Quote-driven): Quoted official uses multiple alarm cues. Decisive cue: 'catastrophic' and 'urgent crisis.' Author's narration is neutral."
* "Reasoning for Reassuring (Author-driven): The author actively uses reassuring language to describe economic effects. Decisive cue: 'manageable' and 'unlikely to cause widespread disruption.' Quotes are neutral."
* "Reasoning for Neutral (Author-driven): Both the author and quoted sources report factual data without emotional language or persuasive intent. No specific framing cues identified."
* "Reasoning for Neutral (Difficult Case - Sarcasm in Quote): Coded Neutral. Quoted person states 'This is just great.' Suspected sarcasm from quote. Framing intent unclear, author neutral, so defaulted to Neutral. Decisive cue (for ambiguity): 'This is just great.'"
* "Reasoning for Neutral (Mixed Quote - Balanced): Initial 'concerning' from quote (decisive cue: 'concerning') balanced by factual counter 'do not transmit easily' which lacked its own reassuring framing. No single dominant framing cue."
* **New Example for Dim4_AmbiguityNote (Dismissed Weak Cues for Neutral):**
  * "Reasoning for Neutral (Author-driven): Author uses mildly negative terms like 'challenges' and 'difficulties' but lacks potent alarmist cues. Quoted sources are factual. Potential weak cues 'pressure mounting' and 'concerns raised' were deemed insufficient on their own to shift from Neutral without stronger explicit framing. No single decisive alarmist or reassuring cue."
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FEW_SHOT_EXEMPLARS -->
---
chunk_type: rule
rule_id: META_FEW_SHOT_EXEMPLARS
pattern_summary: Crystal-clear few-shot examples demonstrating core framing patterns.
dimension: META
parent_group: FEW_SHOT_EXEMPLARS
precedence_rank: 99
outcome: Examples
tags:
- core
references_rule_group: META_FEW_SHOT_EXEMPLARS
related: [Q1_INTENSIFIER_RISKADJ,
          Q5_EXPLICIT_CALMING,
          Q6_MINIMISER_SCALE_CONTRAST]
---
## Few-Shot Exemplars (Crystal-Clear Demonstrations)

**These four examples demonstrate the core framing patterns. Learn from these precise distinctions:**

| **Category** | **Example Sentence** | **Correct Label** | **Key Cue** |
|--------------|---------------------|-------------------|--------------|
| **Alarmist – Intensifier + adjective** | "The flu is so deadly that entire flocks are culled." | **Alarmist** | "so deadly" (intensifier + risk adjective) |
| **Alarmist – High-potency verb** | "An outbreak ravaged farms across three states." | **Alarmist** | "ravaged" (vivid, destructive verb) |
| **Alarmist – Loaded Q** | "Should consumers be worried about buying eggs?" | **Alarmist** | Loaded rhetorical question implying worry |
| **Reassuring – Minimiser + contrast** | "Only one barn was infected out of thousands nationwide." | **Reassuring** | "Only...out of thousands" (minimizer + scale contrast) |
| **Reassuring – Explicit Calming (Q5)** | "Health officials say the outbreak is **fully under control** and poses **no danger to the public**." | **Reassuring** | "**fully under control**, **no danger to the public**" |
| **Reassuring – Explicit Calming (Q5)** | "Experts stress the situation is **completely safe** — there's **absolutely no cause for alarm**." | **Reassuring** | "**completely safe**, **absolutely no cause for alarm**" |

**Key Learning Points:**
- **Alarmist requires explicit intensification** beyond factual reporting
- **High-potency verbs** like "ravaged" create vivid, alarming imagery
- **Loaded questions** that imply worry/danger are strong Alarmist cues
- **Reassuring requires both minimization AND contrast** to show scale
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_SELF_AUDIT_CHECKLIST -->
---
chunk_type: rule
rule_id: META_SELF_AUDIT_CHECKLIST
pattern_summary: LLM self-audit checklist to be used before generating JSON output.
dimension: META
parent_group: SELF_AUDIT_CHECKLIST
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: SELF_AUDIT_CHECKLIST
related: [META_OUTPUT_INSTRUCTIONS_SCHEMA,
          META_FINAL_OUTPUT_INSTRUCTIONS]
---
## LLM SELF-AUDIT CHECKLIST (BEFORE GENERATING JSON)

**CRITICAL:** Silently verify your answer passes ALL rules below. If not, you MUST correct it. Failure to adhere, especially to field exclusivity, will invalidate your response.

1.  **CRITICAL - FIELD EXCLUSIVITY:** Does the JSON object contain ONLY the fields defined for Claim Framing (StatementID, Dim1_Frame, Dim4_AmbiguityNote, ContextUseNote) and ABSOLUTELY NO OTHERS (e.g., no Dim1_Score, Dim2_Certainty, Dim3_AmbiguityType, Dim5_SeverityFlag, Dim22_EconomicFraming or any other unspecified DimXX_... fields)? Have I re-read and fully complied with the CRITICAL FIELD EXCLUSIVITY RULE in Banner Section B?
2.  **JSON Syntax:** Are ALL keys and ALL string values enclosed in double quotes (")? (No single quotes!).
3.  **All Required Fields Present?** Are StatementID, Dim1_Frame, Dim4_AmbiguityNote, and ContextUseNote present? (All are mandatory).
4.  **Dim1_Frame Valid?** Is the value for Dim1_Frame one of: "Reassuring", "Neutral", "Alarmist"?
5.  **Dim4_AmbiguityNote Format:** Is Dim4_AmbiguityNote a non-empty string that provides justification (including the decisive cue) and is NOT "N/A"?
6.  **ContextUseNote Format:** Is ContextUseNote a non-empty string that provides justification and is NOT "N/A"?
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FINAL_OUTPUT_INSTRUCTIONS -->
---
chunk_type: rule
rule_id: META_FINAL_OUTPUT_INSTRUCTIONS
pattern_summary: Final instructions for JSON output format and example.
dimension: META
parent_group: FINAL_OUTPUT_INSTRUCTIONS
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: FINAL_OUTPUT_INSTRUCTIONS
related: [META_OUTPUT_INSTRUCTIONS_SCHEMA,
          META_SELF_AUDIT_CHECKLIST]
---
## Final Output Instructions

**Text Segment to Analyze:**text
{statement_text}

**Coder Sanity Check (for Dimension 1):**
*(Note: Detailed coder checklists and heuristics are available in the separate "Coder Implementation Guide & Checklist" document.)*
✔ Did I pick one label for Dimension 1?
✔ Would a different coder likely agree after reading only the segment and my Dimension 1 frame name, especially considering the Primacy of Framed Quotations rule and the Core Principles & Common Pitfalls?
✔ Highlight Trigger: Have I identified the specific word(s) or phrase(s) from the quoted source or the author that most strongly drove my frame decision and included it in my justification?
✔ Justification Note: Have I provided a clear and concise justification in Dim4_AmbiguityNote for my Dim1_Frame decision, indicating if it's quote- or author-driven, and included the decisive cue?

*Note: For Dimension 1, this scheme is single-label. Choose the one primary frame.*

**Automatic Validity Check for Output:**
* Dim1_Frame must be one of the allowed ENUM values.
* Dim4_AmbiguityNote must be a non-empty string.
* ContextUseNote must be a non-empty string.

**FINAL REMINDER:** Your response MUST strictly adhere to the Claim Framing schema defined above. Inclusion of any unspecified fields will invalidate the output and lead to rejection.

**Output Instructions:**
Return exactly this JSON object (keys in order):json
{
"StatementID": "Primary Framing Label (e.g., Alarmist, Neutral, Reassuring)",
"Dim1_Frame": "Primary Framing Label (e.g., Alarmist, Neutral, Reassuring)",
"Dim4_AmbiguityNote": "MANDATORY Free text note explaining reasoning for Dim1 coding decision, including the decisive textual cue. Cannot be N/A or empty.",
"ContextUseNote": "MANDATORY String based on guidance in §B.4"
}

**Example JSON Output:**

json
{
"StatementID": "cf-example-123",
"Dim1_Frame": "Reassuring",
"Dim4_AmbiguityNote": "Reasoning for Reassuring (Quote-driven): Quoted official uses very strong and unequivocal reassuring language. Decisive cue: 'absolutely no cause for alarm' and 'entirely safe.' Author is neutral.",
"ContextUseNote": "Context was not consulted or did not meaningfully contribute to Dim1_Frame determination; segment text provided sufficient cues."
}
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_ADDITIONAL_IMPLEMENTATION_NOTES -->
---
chunk_type: rule
rule_id: META_ADDITIONAL_IMPLEMENTATION_NOTES
pattern_summary: Additional implementation notes including the Symmetry Rule.
dimension: META
parent_group: ADDITIONAL_IMPLEMENTATION_NOTES
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: ADDITIONAL_IMPLEMENTATION_NOTES
related: [Q1_INTENSIFIER_RISKADJ,
          Q5_EXPLICIT_CALMING]
---
## Additional Implementation Notes

**The Symmetry Rule** (Core Principle)
The codebook enforces symmetric standards between Alarmist and Reassuring frames:

**For Alarmist:** Severe facts require explicit intensification
- "50 million birds culled" → Neutral (factual)
- "A catastrophic 50 million birds slaughtered" → Alarmist (intensified)

**For Reassuring:** Positive facts require explicit calming cues
- "Not expected to lower production" → Neutral (bare negation)
- "Not expected to lower production, so the risk remains very low" → Reassuring (calming cue added)

Both frames now require active linguistic effort beyond stating facts.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_FINAL_ASSERTION_EARLY_EXIT -->
---
chunk_type: rule
rule_id: META_FINAL_ASSERTION_EARLY_EXIT
pattern_summary: Instructions for final assertion and early exit guard for uncertain
  cases.
dimension: META
parent_group: FINAL_ASSERTION_EARLY_EXIT
precedence_rank: 99
outcome: Meta
tags:
- core
references_rule_group: FINAL_ASSERTION_EARLY_EXIT
related: [META_OUTPUT_INSTRUCTIONS_SCHEMA]
---
## FINAL ASSERTION - EARLY EXIT GUARD

**🚨 IF NO BRANCH FIRES:**
If you have worked through all 12 questions (Q0-Q12) and none have yielded a definitive "yes" answer, or if you are uncertain about your classification after following the complete decision tree process, you MUST:

Return:json
{
"StatementID": "<statement_id_from_input>",
"Dim1_Frame": "LABEL_UNCERTAIN",
"Dim4_AmbiguityNote": "Uncertain classification after complete decision tree analysis. Human review required. [Describe specific ambiguity or conflicting cues encountered]",
"ContextUseNote": "Context was consulted but could not resolve the classification uncertainty.",
"needs_human_review": true
}

This prevents silent fall-through errors and ensures problematic cases are flagged for human adjudication rather than producing potentially incorrect automatic classifications.
***
<!-- CHUNK_END -->

<!-- CHUNK_START:META_LEXICON_FULL -->
---
chunk_type: rule
rule_id: META_LEXICON_FULL
dimension: META
parent_group: LEXICON_FULL
precedence_rank: 0            # never outranks Q-rules
outcome: Meta
tags: [lexicon]
---

<details id="lexicon-full-details"><summary>Open COMPLETE cue lexicon (Alarmist · Reassuring · Neutral)</summary>

### ⚠️ CRITICAL WARNING – Read First
*This lexicon is illustrative and heuristic only. A cue's mere presence **does not** decide the frame.*  
Always apply the **Dimension 1 definitions** and the **Principle of Cue Sufficiency**.

---

## 1 Potency Cue Tables (Alarmist & Reassuring)

| Potency | Alarmist cues (examples) | Reassuring cues (examples) |
|---------|-------------------------|---------------------------|
| **High** | catastrophe, catastrophic, apocalypse, doomsday, existential threat, nightmare scenario, ticking time-bomb, unmitigated disaster, meltdown, irreversible damage, calamity, dire, terrified/terrifying | completely safe, 100 % safe, no danger whatsoever, fully under control, guaranteed safety, fool-proof, situation contained, nothing to worry about |
| **Moderate** | crisis, severe, grave, devastating, lethal, deadly, soaring, plummeting, urgent need, grave concern, critical threat, skyrocketing, spiralling, uncontrolled, rampant, mounting fears | manageable, contained, low risk, unlikely, optimistic outlook, good progress, situation stabilised, reassuring, improving, steady decline, significant mitigation |
| **Low / Context-Dependent** | concerning, worrying, threat, risk, problematic, difficult, potential for negative outcome, urging caution, volatility, uncertain | hopeful signs, positive development, plan in place, efforts underway, under investigation, rare, only, slight, mild, limited impact, preliminary success |

---

## 2 Intensifiers + Comparative Risk-Adjective Constructions  
*(Any single match usually sufficient for Alarmist)*

**Intensifiers:** so, very, extremely, highly, frighteningly, particularly, alarmingly, dangerously, record-high, record-low  
**Comparatives/superlatives:** more, less, deadlier, safer, higher, lower, worst, best, most, least  
**Risk adjectives (illustrative):** deadly, lethal, disastrous, catastrophic, brutal, severe, contagious, virulent, destructive, rampant

---

## 3 High-Potency Verbs • Modals • Idioms

### 3.1 High-Potency Verbs / Modals / Adverbs (Alarmist)
must (act), have to, need to, avert disaster, race to stop, scramble to contain, teetering, collapsing, spiralling, crippled, decimated, ravaged, engulfing, exploding, skyrocketed, plummeted, overwhelmed, paralyzed, **immediately**, **at once**, **without delay**

### 3.2 Idiomatic Metaphors
| Alarmist metaphors | Reassuring metaphors |
|--------------------|----------------------|
| ticking time-bomb, powder keg, house of cards, domino effect, opening Pandora's box, slippery slope, runaway train, perfect storm, rolling the dice | silver bullet, safety net, firm foundation, beacon of hope, light at the end of the tunnel |

---

## 4 Moderate Verbs (scale-dependent)  
*(Trigger Alarmist **only when** paired with explicit scale/impact)*

hit, hard hit, swept, swept across, surged, soared, prompted, plunged, plummeted, culled, wave of, losses mounted

---

## 5 Negated-Reassurance & Uncertainty Cues
not ruled out, cannot be discounted, still possible, no guarantee that…, uncertainty remains, questions linger, limited evidence of safety, inconclusive, cannot exclude the possibility, could yet turn into…, no end in sight

---

## 6 Neutral Verbs **and** Adverbs (default Neutral)

| Neutral verbs | Neutral adverbs (econ/metric reporting) |
|---------------|-----------------------------------------|
| hit, affect, affected, impact, impacted, raise concerns, warned, reported, detected, confirmed, trend, trended, fluctuate, fluctuated, volatility, volatile, increase, decrease, rise, drop, change, observed, documented, ongoing, under investigation | sharply, significantly, notably, slightly, marginally, steadily |

*Stay Neutral unless paired with intensifiers, vivid verbs, or risk adjectives.*

---

## 7 Minimiser Words & Scale-Contrast Examples (Reassuring)

only, just, merely, slight, minimal, minor, modest, limited, small fraction, relatively low, comparatively mild, pales in comparison, dwarfed by, offset by, outweighed by, so far so good

---

## 8 Bare-Negation Glossary (Neutral)

no evidence, not linked, not associated, no indication, no sign of, not connected, not caused by, no relationship, not related, no proof, nothing to suggest, no reason to believe

---

## 9 Provenance
* Burgers & de Graaf (2013) — language intensity & sensationalism  
* Dudo et al. (2007) — avian-influenza risk coverage

</details>

***
<!-- CHUNK_END -->
