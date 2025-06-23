## Claim Framing Codebook

> **Version 2.16 - Surgical Patch Applied**  
> *Enhanced intensifier + risk-adjective detection, bare negation clarification, moderate verb guidance*

### ⏩ 60-Second Cue Cheat-Sheet — *Start here*

| If you see… | Frame | Quick test |
|-------------|-------|------------|
| **Intensifier/Comparative + Risk-Adjective** | Alarmist | **Any single match is sufficient (Precedence #1)** |
| - so/very/extremely/highly/frighteningly/particularly + deadly/lethal/dangerous/brutal/severe/contagious/virulent/destructive | | |
| - more/less/deadlier/safer/higher/lower + same risk adjectives | | |
| *(Risk-adjective list is illustrative, not exhaustive)* | | |
| **High-potency verb/metaphor** ("ravaged", "skyrocketed", "crippling") | Alarmist | Check *Potent Verb* list in Appendix A |
| **Moderate verbs** ("swept across", "hard hit", "soared", "plummeted") | Alarmist | **Only when** paired with scale/impact ("millions culled", "record losses") |
| **Loaded rhetorical question** ("Should consumers worry…?") | Alarmist | Q implies heightened danger |
| **'Minimiser + scale contrast'** ("*only* one barn out of thousands") | Reassuring | Both elements required |
| **Explicit calming cue** ("no cause for alarm", "public can rest easy") | Reassuring | Direct statement of *current* safety |
| **Bare negation** ("not expected", "unlikely to affect") | Neutral | Stays Neutral unless paired with explicit calming cue |
| **Everything else → start Neutral** → then run the **Decision Tree ▼** |

> **🚨 LLM PROCESSING REMINDER: One match of the INTENSIFIER+RISK_ADJ table or a moderate/high-potency verb with scale is sufficient for Alarmist. Bare negations ("not expected to…") stay Neutral unless explicit calming cues present.**

<details>
<summary>Quick Decision Tree ▼</summary>

1. **Potent cue present?**  
   • Yes → label Alarmist or Reassuring per cue.  
   • No → go to 2.  

2. **Is the statement purely capability / future action?**  
   • Yes → Neutral (see Rule C).  
   • No → go to 3.  

3. **Is it reporting prices or other metrics?**  
   • If verbs like "rose/declined" or adverbs like "sharply" appear **without** a vivid verb or risk adjective → Neutral.  

4. **Does it speculate about relief ("may be short-lived", "could ease soon")?**  
   • Without an explicit calming cue → Neutral.  

5. **Default-to-Neutral Rule**  
</details>

> **Rule C — Capability ≠ Reassurance.**  
> A statement of capability, preparedness, or hopeful possibility ("officials are working to contain…", "restrictions may be short-lived") remains **Neutral** unless it *explicitly* links to present safety ("so the public can relax").

**⚠ Verbs and Intensified Adjectives Can Also Frame (Examples for Alarmist):**
*   **Potent Verbs (Author/Source Driven):** `ravaged`, `soared` (e.g., prices soared), `swept across` (e.g., outbreak swept across), `plummeted` (when used to describe impact dramatically).
*   **Intensified Adjectives (Author/Source Driven):** `so deadly`, `particularly brutal`, `frighteningly contagious`, `catastrophic` (when used as part of author/source framing, not just a reported fact).
*   **(Note: These often become Alarmist when the author/source uses them to actively frame the situation, rather than as a purely technical or factual description. Context and the 'Principle of Cue Sufficiency' are key.)**

+++ IMPORTANT CALL-OUT: LOADED RHETORICAL QUESTIONS AS ALARMIST CUES +++
**Direct questions from the author or a quoted source that use explicitly loaded or emotionally charged language designed to imply an Alarmist frame, instill fear/urgency, or suggest a worrisome threat are often strong Alarmist cues.**
*   **Example (Author-driven, implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if context suggests framing a worrisome threat).
*   **Example (Quote-driven, implying disaster):** 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist.
*   **Critical Distinction:** Carefully distinguish these from neutral, purely information-seeking questions (which are Neutral).
+++ END CALL-OUT +++

> 🟢 **PRECEDENCE LADDER**  
> 1. Intensifier/Comparative + Risk-Adjective Rule (Sufficient for Alarmist)
> 2. Cue-Sufficiency & Intensity Rules  
> 3. Category Definitions  
> 4. Inclusion Criteria  
> 5. Exclusion Caveats  
> If a lower-level caveat appears to conflict with a higher-level rule, **apply the higher-level rule**.

**SYSTEM_INSTRUCTION_BLOCK_START**
IMPORTANT: You MUST output valid JSONL.
This means EACH line of your output MUST be a single, complete, and independently valid JSON object corresponding to one segment.
DO NOT output partial JSON objects or run-on JSON across lines.
Each JSON object per line MUST contain EXACTLY these fields: "StatementID", "Dim1_Frame", "Dim4_AmbiguityNote", and "ContextUseNote".
Follow all other formatting rules from the main prompt precisely, especially for ENUM values and field presence.
**SYSTEM_INSTRUCTION_BLOCK_END**

!! MANDATORY OUTPUT INSTRUCTIONS & SCHEMA FOR CLAIM FRAMING (Dimension 1) — CRITICAL: READ FIRST !!
§5 Final Schema Check & Self-Audit (MUST-FOLLOW)
Before replying, silently verify your answer passes ALL rules in the "MANDATORY OUTPUT & SCHEMA DEFINITION" banner and this checklist. If not, you MUST correct it until it passes or output the exact string RETRY_AUDIT_FAILURE if perfect correction is impossible after attempting.

* **Output Format:** Is the output EITHER the exact string "NA/Not Applicable" OR a JSON object?
* **JSON SYNTAX CRITICAL:** If JSON, does it use ONLY double quotes (") for ALL keys and ALL string values? (If single quotes were generated, I must correct this or output RETRY_SYNTAX_ERROR).
* **Canonical Labels CRITICAL:** If JSON, is "labels_present" a non-empty list of one or more labels chosen EXCLUSIVELY from the §2.1 Canonical Label List? (No invented labels. Default to \["General Economic Concern / Unspecified Impact"\] if applicable).
* **CRITICAL - ATTRIBUTE ACCURACY & COMPLETENESS:** If JSON, for EVERY label listed in "labels_present", are ALL 5 corresponding attribute keys (valence_, level_, distributional_focus_, time_horizon_, certainty_ + correct suffix from §2.3) present AND correctly filled with ENUM values from §2.2? AND CRITICALLY, are there NO attributes or attribute sets present for any label NOT listed in "labels_present"? (All 5 attributes are mandatory for each listed label, and ONLY for listed labels; no extras).
* **"Unknown" Values:** Are unknown attribute values correctly filled as "Unknown" (with all keys still present)? (No empty attribute objects for a label).
* **CRITICAL RULE D (Content Trigger):** If the segment contained monetary figures or numerals > 0 explicitly linked to economic terms (cost, price, loss, compensation, culling counts), is the output a VALID JSON object (per rules 2-5) and NOT "NA/Not Applicable"? (This rule takes precedence).

A. YOUR TASK & ABSOLUTE OUTPUT RULE:
You are an information-extraction model. For EACH segment, your output MUST BE a PERFECTLY VALID JSON OBJECT adhering to all rules below.‼️ JSON SYNTAX CRITICAL FAILURE CONDITION: Using single quotes (''') anywhere (for keys or string values) instead of double quotes (") is a CRITICAL FAILURE. You MUST use double quotes exclusively for all JSON keys and string values. If you realize you have produced single quotes, you MUST regenerate your response with correct double quotes or, if unable to self-correct perfectly, output an error indicator if the system allows, or a minimally valid JSON like {"error": "RETRY_SYNTAX_ERROR"}.

B. REQUIRED FIELDS, VALID VALUES, AND FIELD EXCLUSIVITY (ALL MUST BE PRESENT AND CORRECT):
Your JSON response for this Claim Framing task MUST ONLY contain the fields listed below (1-4).CRITICAL FIELD EXCLUSIVITY RULE: DO NOT include any fields related to other dimensions or tasks, such as Dim22_EconomicFraming or ANY OTHER DimXX_... fields not specified here. The presence of ANY unspecified fields will result in a validation ERROR and rejection of your response.

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

C. JSON OUTPUT TEMPLATE:
\`\`\`json
{
"StatementID": "<statement_id_from_input>",
"Dim1_Frame": "<Value from §B.2>",
"Dim4_AmbiguityNote": "<MANDATORY free text note explaining the reasoning for the Dim1 coding decision. Cannot be N/A or empty.>",
"ContextUseNote": "<String based on guidance in §B.4>"
}
\`\`\`
(Implementation Note: For training/calibration, coders/LLMs should first process a standard calibration set (e.g., 3-5 pre-coded segments covering key distinctions) and compare results to a gold standard key. If significant discrepancies (e.g., ≥2/5 mismatches on Dim1 Frame) occur, halt and review codebook examples and guidance, paying special attention to the 'Dimension 1 - Guidance Note: Primacy of Framed Quotations,' 'Dimension 1 - Guidance Note: Principle of Cue Sufficiency,' and the 'Default-to-Neutral Rule,' before proceeding with live coding. A separate "Coder Implementation Guide & Checklist" document provides further practical advice and quality control procedures.)

## Dimension 1: Claim Framing

**!! CORE PRINCIPLES & COMMON PITFALLS (READ THIS FIRST!) !!**
1.  **Bedrock Principle: CODE THE PRESENTATION, NOT THE FACTS**
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

**⚠ Verbs and Intensified Adjectives Can Also Frame (Examples for Alarmist):**
*   **Potent Verbs (Author/Source Driven):** `ravaged`, `soared` (e.g., prices soared), `swept across` (e.g., outbreak swept across), `plummeted` (when used to describe impact dramatically).
*   **Intensified Adjectives (Author/Source Driven):** `so deadly`, `particularly brutal`, `frighteningly contagious`, `catastrophic` (when used as part of author/source framing, not just a reported fact).
*   **(Note: These often become Alarmist when the author/source uses them to actively frame the situation, rather than as a purely technical or factual description. Context and the 'Principle of Cue Sufficiency' are key.)**

**Additional Nuanced Examples:**
* **Slightly Negative Fact + Neutral Framing:**
  * Segment: "Market prices for wheat decreased by 2% this month."
  * Reasoning: "Neutral. Factual report of a minor negative change. No explicit alarmist framing from the author."

* **Slightly Negative Fact + Alarmist Framing (Exaggeration):**
  * Segment: "Market prices for wheat took a devastating 2% dive this month, spelling trouble for farmers."
  * Reasoning: "Alarmist (Author-driven). Author uses 'devastating dive' and 'spelling trouble' to frame a minor decrease alarmingly. Decisive cues: 'devastating dive,' 'spelling trouble'."

2.  **Common Pitfalls & Guiding Micro-Rules:**
    **(A) Positive Facts / Absence of Negative Events ≠ Active Reassurance**
    * Micro-Rule: Statements merely reporting positive factual outcomes (e.g., "no further cases were reported," "tests were negative," "patient recovered") or the simple absence of negative events are categorically Neutral unless explicitly framed otherwise by the author/source.
    * To be Reassuring, the author or quoted source MUST actively and explicitly employ calming, optimistic, or risk-minimizing language designed to reduce audience concern or highlight safety/control regarding the broader situation, beyond simply stating the positive fact.
    * Canonical NON-EXAMPLE for Reassuring (Code: Neutral):
        * Text: "Despite the health department conducting contact tracing, no further cases of bird flu connected to the case have been reported at the time of writing."
        * Incorrect Reasoning (to avoid): "This is good news and implies containment, so it's Reassuring."
        * Correct Codebook Reasoning: "Neutral. The author reports a positive fact (absence of new cases) using descriptive, neutral language. No explicit reassuring language (e.g., 'providing significant relief,' 'which is very encouraging news,' 'fortunately') is used by the author to actively frame these facts reassuringly."
    * **Minimal Pair Examples:**
        * **Neutral:** "The company announced profits increased by 10%."
          * Reasoning: "Neutral. Factual report of a positive outcome. No active reassuring framing from the author/source."
        * **Reassuring:** "The company was pleased to announce profits soared by 10%, a reassuring sign that our strategy is working and the future looks secure."
          * Reasoning: "Reassuring (Author/Source-driven). Uses 'pleased to announce,' 'soared,' 'reassuring sign,' and 'future looks secure' to actively frame the positive outcome. Decisive cues: 'reassuring sign,' 'future looks secure'."
        * **Neutral:** "Segment: 'The latest tests on the water supply showed no contaminants.'"
          * Reasoning: "Neutral. Reports absence of negative. No explicit reassuring language from the author/source about broader safety."
        * **Reassuring:** "Segment: 'Officials confirmed the latest tests on the water supply showed no contaminants, declaring, "This is excellent news, and residents can be fully confident in the safety of their drinking water."'"
          * Reasoning: "Reassuring (Quote-driven). The official's quote explicitly frames the negative test as 'excellent news' and a reason for 'full confidence' and 'safety.' Decisive cues: 'excellent news,' 'fully confident in the safety'."

    **(B) Severe Characteristics / Negative Facts ≠ Active Alarm**
    * Micro-Rule: Listing objectively severe characteristics, properties, or statistics (e.g., "high mutation rate," "high mortality rates," "significant number of outbreaks," "virus spread to new areas") is categorically Neutral if presented by the author/source factually, without additional explicit alarmist framing language, tone, or rhetorical emphasis (e.g., "a terrifyingly high rate," "these characteristics paint a catastrophic picture," "this grave list signals imminent danger," "an explosive spread").
    * Descriptive terms inherent to the phenomenon (e.g., 'high' as part of 'high mortality rate,' 'explosive' if used by a scientist as a technical descriptor of spread dynamics and attributed as such, rather than an authorial emotional amplifier) are part of the factual description and do not, in themselves, constitute alarmist framing by the author or source. The alarm must come from additional, explicit framing choices.
    * Canonical NON-EXAMPLE for Alarmist (Code: Neutral):
        * Text: "These \[characteristics\] include a wide host range, high mutation rate, genetic reassortment, high mortality rates, and genetic reassortment."
        * Incorrect Reasoning (to avoid): "High mortality and mutation rates are inherently alarming, so it's Alarmist."
        * Correct Codebook Reasoning: "Neutral. The author lists factual characteristics using neutral, descriptive language. No loaded adjectives (e.g., 'terrifying,' 'devastating') or explicit alarmist rhetoric are used by the author to actively frame these characteristics beyond their factual statement."
    * **Minimal Pair Examples:**
        * **Neutral:** "The virus is known to cause severe respiratory distress in vulnerable populations."
          * Reasoning: "Neutral. 'Severe respiratory distress' is a factual description of a known medical characteristic. No additional alarmist framing by the author."
        * **Alarmist:** "The virus unleashes a terrifyingly severe respiratory distress in vulnerable populations, often leading to a horrifying end."
          * Reasoning: "Alarmist (Author-driven). Author uses 'unleashes,' 'terrifyingly severe,' and 'horrifying end' to frame the characteristic alarmingly. Decisive cues: 'terrifyingly severe,' 'horrifying end'."
        * **Neutral:** "A report detailed the culling of 1 million animals."
          * Reasoning: "Neutral. Factual report of a severe action and large number. No added alarmist framing by the author."
        * **Alarmist:** "A shocking report detailed the brutal culling of a staggering 1 million animals, a grim testament to the crisis."
          * Reasoning: "Alarmist (Author-driven). Author uses 'shocking,' 'brutal culling,' 'staggering,' and 'grim testament to the crisis' to frame the event. Decisive cues: 'shocking,' 'brutal culling,' 'staggering'."

    **(C) Capability / Preparedness Statements ≠ Active Reassurance**
    * Micro-Rule: Statements describing capabilities, preparedness measures (future or existing), implemented safeguards, capacities, or potential positive future actions (e.g., "a vaccine can be made in X weeks," "systems are in place to detect X," "we have the resources to respond," "new safeguards have been enacted") are categorically Neutral unless explicitly and actively framed by the author/source as a reason for current calm, safety, or substantially minimized present risk.
    * To be Reassuring, the author or quoted source MUST go beyond stating the capability and actively use explicit language to connect that capability to a state of present calm, safety, or significantly reduced current risk for the audience.
    * Canonical NON-EXAMPLE for Reassuring (Code: Neutral):
        * Text: "'If a pandemic arises, once the genome sequence is known, an exact matched vaccine can be made in 6 weeks with mRNA technology and 4 months using the old egg-base methods,' she said."
        * Incorrect Reasoning (to avoid): "Fast vaccine development is reassuring about capability, so it's Reassuring."
        * Correct Codebook Reasoning: "Neutral. The quoted expert states a technical capability and timeline for a hypothetical future event. This statement lacks explicit calming or risk-minimizing language from the source (e.g., no 'fortunately,' 'this makes us very safe,' 'this is excellent news for our current preparedness,' 'the public can be reassured by this speed') to actively frame this capability as a reason for reassurance about existing or imminent risks."
    * **Minimal Pair Examples:**
        * **Neutral:** "The agency has developed a rapid deployment plan for emergencies."
          * Reasoning: "Neutral. States a capability. No explicit framing linking it to current reassurance."
        * **Reassuring:** "The agency's new rapid deployment plan is a game-changer, meaning that in the event of an emergency, the public can rest assured that help will arrive swiftly and effectively, significantly reducing any potential danger."
          * Reasoning: "Reassuring (Author-driven). Author explicitly links the plan to 'rest assured,' 'swiftly and effectively,' and 'significantly reducing potential danger.' Decisive cues: 'rest assured,' 'significantly reducing potential danger'."
        * **Neutral:** "Quote: 'We have stockpiled 30 million doses of the antiviral.'"
          * Reasoning: "Neutral. Quoted source states a fact about preparedness. Lacks explicit language from the source framing this as a reason for current public calm or safety."
        * **Reassuring:** "Quote: 'We have stockpiled 30 million doses of the antiviral, which is excellent news and means our citizens are very well protected against any immediate threat from this virus.'"
          * Reasoning: "Reassuring (Quote-driven). Quoted source explicitly frames the stockpile as 'excellent news' and a reason for being 'very well protected against any immediate threat.' Decisive cues: 'excellent news,' 'very well protected'."

**KEY QUESTION FOR SELF-CORRECTION:** 
Am I coding based on explicit framing language I can highlight in the text (the *how* it is said by the author/source), OR am I coding based on the inferred positive/negative implications of the facts themselves (the *what* is being said)? The frame lies in the *how*.

Is the emotion I'm sensing coming from the facts themselves, or from the author's/source's specific word choices and rhetorical strategies layered on top of those facts?

CRITICAL DISTINCTION: Information Severity vs. Framing Style
A core principle of this codebook is the absolute and non-negotiable separation between the objective severity or positivity of an event/fact and the framing style used by the author/source to present it. Segments are NEVER coded Alarmist simply because they report bad news (e.g., deaths, outbreaks, high costs, risks) NOR Reassuring simply because they report good news (e.g., recovery, low numbers, successful prevention). The code MUST ALWAYS be based on the presence of explicit Alarmist or Reassuring framing cues in the language deliberately chosen by the author or quoted source (see specific criteria under Alarmist/Reassuring). In the complete absence of such explicit framing cues from both author and quote, the segment is unquestionably Neutral, regardless of how concerning or encouraging the underlying facts may be to the coder or a general reader.

Mini-Glossary: Content vs. Presentation
Content/Fact: The underlying event, statistic, or piece of information being reported (e.g., '100 birds died,' 'a vaccine was approved').
Presentational Cue: The specific word choice, phrasing, tone, rhetorical strategy, or explicit evaluative language intentionally employed by the source or author to frame or make salient that content/fact, aiming to influence the audience's perception or emotional response.
Example (Content): 5 cases were reported. Example (Presentational Cue - Reassuring): "Officials were pleased to announce that actually only 5 cases were reported, a reassuringly low number."
Example (Content): A new variant was identified. Example (Presentational Cue - Alarmist): "Experts warned of a dangerous new variant, describing it as a ticking time-bomb."
**Example (Content):** "The company's stock fell 50%."
**Example (Presentational Cue - Alarmist):** "The company's stock suffered a catastrophic collapse, plummeting by a disastrous 50%." (Cue: 'catastrophic collapse,' 'plummeting,' 'disastrous').
**Example (Presentational Cue - Neutral):** "The company's stock decreased by 50%." (Cue: Neutral, factual verbs).

(Theoretical Note: This dimension identifies the overall emotional tone or rhetorical angle (i.e., the salience and presentation) used to present information regarding the subject at hand. Consistent with claim framing theory (e.g., Entman, 1993), it assesses how language, selection of facts, and rhetorical devices are used to make certain aspects of the subject more salient, thereby shaping understanding and evoking particular responses. While Entman's four functions of framing (problem definition, causal interpretation, moral evaluation, treatment recommendation) are not explicitly coded as separate labels in Dimension 1, this dimension primarily captures how the salience of these functions (or the overall issue) is established through linguistic and rhetorical choices. Dimension 1 generally ignores these functions except insofar as the specific wording used to convey them makes a particular frame (Alarmist, Reassuring, Neutral) salient. Crucially, for Dim1, if a directly quoted source within the segment provides a clear Alarmist or Reassuring frame, that frame takes precedence in determining the segment's overall frame, even if the author's surrounding narrative is neutral. If quoted sources are neutral or unfraged, the focus is on how the information is presented by the segment's author.)

(Associated impacts means effects caused by or explicitly linked back to the subject at hand). Any topic related to the subject (e.g., economic, scientific, political, health, environmental concerns) can be framed in an alarmist, reassuring, or neutral way. The coding should reflect this framing based on the presentation by the quoted source or the author.

Refer to Appendix A for an Illustrative Cue Lexicon. CRITICAL: This appendix is NOT an exhaustive inclusion criterion for determining the categorical frame (e.g., Alarmist). The categorical frame is determined by the primary definitions and inclusion/exclusion criteria in Dimension 1. Holistic judgment of cue potency, as outlined in the "Dimension 1 - Guidance Note: Principle of Cue Sufficiency," is paramount.

DETERMINE THE CATEGORICAL FRAME!
You MUST determine the primary Dim1_Frame ("Reassuring", "Neutral", or "Alarmist") based on the comprehensive definitions, inclusion/exclusion criteria, and general guidance notes for Dimension 1, paying special attention to the Guidance Note: Primacy of Framed Quotations and the Quick Decision Tree.

+++ IMPORTANT BOXED NOTE START +++
**A single high-potency cue (e.g., a vivid verb describing impactful action + scale, a loaded rhetorical question implying danger, or an intensifier + high-valence/loaded adjective) is often sufficient to assign Alarmist, per the Principle of Cue Sufficiency.**
+++ IMPORTANT BOXED NOTE END +++

+++ IMPORTANT CALL-OUT: LOADED RHETORICAL QUESTIONS AS ALARMIST CUES +++
**Direct questions from the author or a quoted source that use explicitly loaded or emotionally charged language designed to imply an Alarmist frame, instill fear/urgency, or suggest a worrisome threat are often strong Alarmist cues.**
*   **Example (Author-driven, implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if context suggests framing a worrisome threat).
*   **Example (Quote-driven, implying disaster):** 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist.
*   **Critical Distinction:** Carefully distinguish these from neutral, purely information-seeking questions (which are Neutral).
+++ END CALL-OUT +++

**Code: Alarmist** (Value for Dim1_Frame)

(Reminder: One vivid cue from a quoted source or the author may qualify this frame—see Dimension 1 - Guidance Note: Principle of Cue Sufficiency under Core Foundational Principles below.)

Definition: Statement, either through a directly quoted source or the author's own presentation, demonstrably employs explicit language, tone, or rhetorical devices specifically chosen by the author or quoted source to evoke fear, a sense of urgency, extreme concern, or a strong sense of danger regarding the subject or its impacts. The intent to alarm must be evident in the presentation, not inferred from the facts. If a quoted source is Alarmist, the segment is Alarmist even if the author's narration is neutral.

**Key Differentiators from Neutral (Crucial for Borderline Cases)**
* Neutral reports severe facts; Alarmist adds explicit emotional amplification
* Neutral uses standard descriptive terms; Alarmist intensifies them dramatically
* Neutral states risks/threats factually; Alarmist frames them as imminent dangers
* Neutral reports problems; Alarmist characterizes them as crises or disasters

> ⚠ **TECHNICAL OR CLINICAL TERMS**  
> A term like *deadly, lethal, fatal* **by itself** can still be Neutral when used *clinically* (e.g. "lethal dose 50").  
> **BUT** if the same term is paired with *any intensifier or emotive verb* (see Cue-Intensity Table) → **Alarmist (Precedence #1)**.

**Inclusion Criteria:**

* A directly quoted source uses language fitting the Alarmist criteria below.
* Use of strong negative adjectives ("deadly," "catastrophic," "nightmare scenario," "terrifyingly high") by the quoted source or author that go beyond factual description of severity and serve to amplify negative emotion; emphasis on worst-case scenarios ("could kill millions"); urgent tone ("Now is the time...," "crisis"); highlighting pathogenic/detrimental potential in a way that emphasizes danger through language.
* Expressions of "enormous concern," "great concern," or feeling "nervous" if these are part of the framing by the quoted source or author, rather than just reported emotions.
* Authorial use of high-valence impact adjectives/phrases (e.g., severe, worst-ever, devastating, catastrophic, record-breaking loss, failed dismally) when directly describing or characterizing large-scale harm or significant negative events/failures. This requires the author to be making an evaluative judgment using these terms, not just reporting them as part of a technical classification or a direct, unframed quote from another source. This includes the author's deliberate selection of superlatives (e.g., 'highest,' 'worst,' 'most critical') or other emphatic terms that characterize the subject, or a specific aspect/group related to it, as being at an extreme end of a risk or negative impact spectrum, thereby framing it to evoke heightened concern or a sense of danger. (This applies mainly if quotes are neutral or absent and the author's framing is dominant).
* Authorial use of intensifiers (e.g., 'so,' 'very,' 'extremely,' 'incredibly,' 'particularly,' 'frighteningly') coupled with high-valence negative adjectives (e.g., 'destructive,' 'contagious') to describe the subject or its characteristics. The intensifier must clearly serve to heighten the emotional impact of the negative descriptor, pushing it beyond a factual statement of degree. Example: Author: 'Because the virus is *so deadly* to this species, culling is the only option.' → Alarmist. (Rationale: The intensifier 'so' amplifies 'deadly,' emphasizing the extreme nature and justifying the severe consequence, thereby framing the virus itself in alarming terms.)
    * **Clarification on "deadly," "fatal," "lethal":** These terms when modified by an intensifier (e.g., 'so deadly,' 'extremely fatal,' 'particularly lethal,' 'frighteningly deadly') are Alarmist. Without such direct intensification, "deadly" (etc.) describing a factual characteristic (e.g., 'Avian flu can be deadly in domestic poultry') is typically Neutral unless other alarmist cues are present.
    * **Minimal Pair Example:**
        * **Neutral:** "The virus is contagious."
        * **Alarmist (Author):** "The virus is frighteningly contagious, spreading like wildfire." (Cue: 'frighteningly,' 'spreading like wildfire').
    * **New Comparative Minimal Pair Example:**
        * **Alarmist:** "Scientists warn the virus is becoming deadlier each season."
        * **Neutral:** "Scientists track how the virus becomes more common each season."
* Authorial use of vivid, active verbs or metaphors to describe the spread or impact of a threat, especially when combined with its scale or severity, thereby emphasizing its uncontrolled, rapid, or overwhelming nature. Example: Author: 'The wildfire swept across the valley, devouring homes and forcing thousands to flee.' → Alarmist. (Rationale: 'Swept across' and 'devouring' are vivid, active verbs creating a sense of uncontrolled destructive power.)
* Conditional statements where the potential consequence is framed by the quoted source or author with loaded language, strong negative adjectives, or an urgent tone (e.g., Quote: 'If mutations occur, it could cause devastation,' or Author: 'But the risk could be quite big').
* Discussions of problems, challenges, deficiencies, or potential negative consequences ONLY IF the source or author frames these with explicitly loaded language (e.g., "critical failure," "dangerous deficiency," "disastrous consequences," "catastrophic risk"), a demonstrably urgent/fearful tone, or strong negative adjectives that go beyond factual description to evoke fear or extreme concern. (For factual, non-alarmist reporting of challenges or potential negative outcomes, see Neutral).
* Use of a strongly accusatory or critical tone by the quoted source or author, only if that tone is conveyed through language that also meets other Alarmist criteria, such as employing loaded terms that frame the situation as a crisis, disaster, or an an immediate, severe threat, beyond a direct and factual (though critical) statement of wrongdoing, unfairness, or a problem.
* Strong, generalized, or fatalistic statements by the quoted source or author about the expected negative behavior or adaptation/escalation of the subject.
* Framing of long-term or high-magnitude threats by the quoted source or author with language that evokes strong fear or extreme concern.
* Direct questions from the author that use explicitly loaded or emotionally charged language clearly designed to imply an Alarmist frame or instill fear/urgency in the reader.
    * **Example:**
        * **Author:** "With the system collapsing, can anyone truly feel safe anymore?" (Alarmist. Cues: 'system collapsing,' 'truly feel safe anymore?' - rhetorical question implying no).
        * **Non-Example (Neutral):** Author: "What are the safety protocols in place?" (Information-seeking).
* Use of loaded rhetorical questions by the quoted source or author that are designed to evoke fear, urgency, or strong concern by implying a severe problem or a dire lack of action.
    * Example (Author-driven): 'How many more animals have to die before we finally act decisively?' → Alarmist. (Rationale: The rhetorical question uses emotive language 'have to die' and implies criticism of inaction, framing the situation as urgent and severe.)
    * Example (Quote-driven): 'The activist asked, "Are we simply going to stand by while this disaster unfolds?"' → Alarmist. (Rationale: The quoted rhetorical question uses 'disaster unfolds' to frame the situation alarmingly.)
    * **Example (Rhetorical question from author implying worry):** Author: "With new variants emerging rapidly, should humans be worried about the next pandemic?" → Alarmist (if the context suggests this is not a simple information request but a way to frame emerging variants as a worrisome threat).
* Framing unknowns or lack of data with an alarming tone by the quoted source or author.
    * **Example:**
        * **Quote:** "We simply don't know how far this has spread, and that ignorance is precisely what makes this situation so terrifying." (Alarmist. Cues: 'ignorance...so terrifying').
        * **Non-Example (Neutral):** Quote: "Data on the full extent of the spread is not yet available."
* In statements with contrasting conjunctions (e.g., 'but,' 'although'), if the main clause or concluding point from the quoted source or author clearly carries an Alarmist frame.
* Use of imperative or deontic constructions (e.g., verbs like 'must,' 'have to,' 'need to,' 'should'; calls for 'increased vigilance/action') by the quoted source or author, WHEN these are explicitly linked to averting a stated severe negative outcome, convey significant urgency (e.g., through adverbs like 'immediately,' 'as soon as possible'), or depict current responses/preparedness as critically inadequate or ad-hoc (e.g., 'winging it,' 'equivalent of hoping for the best').
    * Example (Quote-driven): 'The expert warned, "We must act immediately to prevent a catastrophic spillover."' → Alarmist. (Rationale: Deontic verb 'must' + urgency adverb 'immediately' + stated severe negative outcome 'catastrophic spillover' from the quoted expert.)
    * Example (Author-driven): 'Scientists are calling for increased vigilance as the virus is now threatening human health.' → Alarmist. (Rationale: Call for action 'increased vigilance' directly linked by the author to protecting against a significant, broad risk 'human health,' implying an urgent need due to a heightened threat.)
    * Example (Quote-driven): 'He said the carcasses have to be buried or incinerated as soon as possible to reduce the risk of contaminating humans.' → Alarmist. (Rationale: Imperative 'have to be' + urgency 'as soon as possible' + significant risk 'contaminating humans' from the quoted source.)
    * Counter-Example: 'Scientists are calling for increased research funding.' → Neutral (if presented without additional alarmist framing regarding the consequences of not getting funding). The call for action alone is not sufficient.
* Statements of negated reassurance, where a typically reassuring statement is explicitly denied or ruled out concerning a significant negative potential.
    * Example (Author-driven): 'While the current risk is low, virologists have not ruled out future variations of the virus having pandemic potential.' → Alarmist. (Rationale: The phrase 'not ruled out' applied to a highly potent negative outcome like 'pandemic potential' functions as an alarm cue, emphasizing the continued existence of a severe threat.)
* Rhetorical framing that emphasizes the expansion, accumulation, or compounding of threats, especially when discussing multiple negative events or impacts.
    * Example (Author-driven): 'That \[recorded infections\] is in addition to outbreaks among laying hens, turkeys and chickens.' → Alarmist. (Rationale: The author's use of 'in addition to' explicitly frames the new information as an expansion of existing 'outbreaks,' thereby amplifying the perceived scale and spread of the threat.)
* **Authorial Selection of Extreme Exemplars/Anecdotes Framed for Alarm**
    * When the author chooses to highlight a particularly extreme or emotionally charged negative example/anecdote AND frames its presentation with additional alarmist language or rhetoric to suggest broader, severe implications or to evoke strong fear, beyond merely reporting the anecdote factually.
    * **Example:** Author: "Consider the tragic case of Farmer Giles, whose entire livelihood was wiped out overnight by this insidious disease – a stark warning of the devastation that awaits us all if we don't act." (Alarmist. The anecdote is framed with 'insidious disease,' 'stark warning,' 'devastation that awaits us all').
    * **Non-Example (Neutral):** Author: "One affected individual, Farmer Giles, reported losing his flock. Health officials are investigating." (Factual report of an anecdote).

**Common Alarmist Cues** (Heuristic Hint: These are indicators; overall context, intent, and potency are paramount. See also Appendix A.): \`catastrophic\`, \`nightmare\`, \`devastating\`, \`imminent\`, \`crisis\`, \`soaring\`, \`surge\`, \`threat\`, \`disastrous\`, \`ticking time-bomb\`, \`grave concern\`, \`urgent\`. (See also Appendix A for more, including verbs and metaphors).

(Note: Common descriptive phrases for negative events, like 'market is down' or 'company faces challenges,' are generally Neutral unless accompanied by stronger alarmist intensifiers or framing from the list above.)

**Exclusion Criteria:**
* Neutral presentation of facts/figures by both the author and any quoted sources, even if those facts are objectively severe; reassuring language/presentation from either author or quoted source; neutral predictions; neutral conditional statements. Listing a fatality/damage rate, case/incident count, or R-value/metric without evaluative language or alarming tone from either the quoted source or the author is Neutral. Reminder (Exclusion Caveat, Precedence #4): One **mild** adjective (*concerning, affected, hit, impacted*) is not enough **unless** the term appears in the High-Potency list above. Reporting objectively severe facts (e.g., 'mammal-to-mammal transmission now confirmed') remains Neutral if the presentation by the author and any quoted source lacks explicit alarmist linguistic cues.
* Clarification: The mere use of standard descriptive terms for negative events (e.g., 'outbreak,' 'death,' 'illness,' 'culling,' 'risk,' 'concern,' 'epidemic,' 'potential for X,' 'active outbreaks') by an author or quoted source, when presenting factual information or discussing possibilities, does not automatically make a segment Alarmist, even if these terms are repeated or refer to multiple instances. The framing must come from additional explicit cues. Weak or ambiguous cues do not accumulate to meet the threshold for Alarmist; a clear and sufficiently potent cue (or set of tightly coupled potent cues from the author/source) is required. For an Alarmist frame, these terms must be coupled with or contextualized by other explicit alarmist cues such as:
    * Strong negative/loaded adjectives (e.g., 'a devastating outbreak,' 'a terrifying risk').
    * An overtly urgent, fearful, or grave tone from the source/author.
    * Deontic urgency (as defined in Inclusion Criteria).
    * Rhetorical emphasis on worst-case scenarios that goes beyond factual prediction (e.g., 'this is a ticking time-bomb').
    * Additive framing that significantly amplifies perceived threat (as defined in Inclusion Criteria).
    * Loaded rhetorical questions (as defined in Inclusion Criteria).
* Epistemic modals (e.g., 'could,' 'might,' 'may') expressing possibility alone do not trigger an Alarmist frame unless the potential outcome they describe is itself framed with strong alarmist intensifiers, or the modal is paired with other alarmist cues like an urgent tone or deontic urgency from the source/author (e.g., 'it could become a catastrophic pandemic,' not just 'it could spread').
* Factual descriptions of phenomena that inherently possess negative-sounding descriptors (e.g., 'a high fever,' 'a high mortality rate,' 'a rapidly spreading virus') are Neutral if the author/source does not add further explicit alarmist framing language, tone, or rhetorical emphasis beyond the standard terminology used to describe the phenomenon. However, if the author chooses to significantly intensify these descriptors (e.g., 'the *remarkably* high mortality rate,' 'its *frighteningly* rapid spread'), this can cross into Alarmist framing by emphasizing the extremity beyond a standard factual statement.

**Examples**:
* "An official stated the epidemic was 'the worst the country ever experienced,' leading to 20 million poultry being culled." (Alarmist → The official's direct quote uses strong alarmist language ("worst the country ever experienced"). Even if the author reports this quote neutrally, the frame of the quoted source determines the segment's frame.)
* "The economic impact of the subject on the agricultural sector is a ticking time-bomb for food security," said the analyst. (Alarmist → The analyst's quote uses a potent metaphor "ticking time-bomb," framing the economic impact with fear/urgency.)
* Author: "Political inaction is steering us towards a catastrophic crisis related to the subject." (Alarmist → Author's framing of political aspect through loaded language like "catastrophic crisis," assuming no overriding framed quote.)
* Author: "The region was severely hit by the virus, resulting in record losses." (Alarmist → Author's use of "severely hit" and "record losses" to describe large-scale harm, assuming no overriding framed quote.)
* Quoted expert: "If the subject mutates, it could unleash a devastating pandemic." (Alarmist → The expert's quote uses "devastating" to frame the conditional consequence.)
* "Segment: 'Initial reports suggest symptoms are mild, but we know this pathogen has a history of rapid and concerning mutations,' stated the health official. (Alarmist → Quote-driven. Although the quote mentions 'mild symptoms' initially, the conjunction 'but' shifts the focus to the 'history of rapid and concerning mutations.' This latter part, with its emphasis on known negative potential, is a potent alarm cue that makes the overall quote Alarmist.)"
* Author: 'Among the potential environmental impacts discussed, contamination of the local water supply poses the single greatest threat to the community.' (Alarmist → The author uses a superlative phrase 'single greatest threat' to emphasize the extreme level of danger from one specific impact, framing it in a way likely to evoke significant concern, assuming no overriding framed quote.)
* Author: 'From Wyoming to Maine, the highly contagious bird flu swept across farms and backyard flocks, prompting millions of chickens and turkeys to be culled.' (Alarmist → The author's use of 'swept across' combined with 'highly contagious' and the large-scale consequence 'millions...culled' creates an alarmist depiction of an overwhelming, uncontrolled event, assuming no overriding framed quote.)
* **Example (Deontic Urgency):**
    * Quote: "The minister declared, 'We are on the brink of a crisis. We absolutely must implement these drastic measures now, or face consequences too dire to contemplate.'"
    * Reasoning: "Alarmist (Quote-driven). Quote uses 'brink of a crisis,' 'absolutely must implement drastic measures now,' and 'consequences too dire to contemplate.' Decisive cues: 'brink of a crisis,' 'absolutely must...now,' 'dire to contemplate'."
* **Example (Author-driven, vivid metaphor & intensifier):**
    * Author: "The virus is a raging inferno, tearing through populations with terrifying speed, leaving devastation in its wake."
    * Reasoning: "Alarmist (Author-driven). Author uses vivid metaphor 'raging inferno,' 'tearing through,' 'terrifying speed,' and 'devastation in its wake.' Decisive cues: 'raging inferno,' 'terrifying speed'."
* **Example (Vivid verb + scale from Author):** Author: "The disease ravaged poultry flocks across three states, leading to immense economic losses." (Alarmist → 'Ravaged' + 'across three states' + 'immense economic losses' create a strong alarmist frame).
* **Example (Vivid verb + scale from Author):** Author: "Confirmed cases soared past one million, overwhelming healthcare systems." (Alarmist → 'Soared past one million' + 'overwhelming healthcare systems' creates a strong alarmist frame).
* **Example (Evaluative adjective + scale from Author):** Author: "The agricultural sector was hard hit by the drought, with crop yields plummeting by over 50%." (Alarmist → 'Hard hit' coupled with the specific, severe scale of 'plummeting by over 50%' framed by the author).

**Non-Examples**:
* "Segment: 'Analysis suggests the species is likely to face significant population decline in the coming decade,' the report concluded." → Neutral.

---
## Dimension 1 - General Rules & Guidance Notes
This section outlines foundational principles for determining the Dim1_Frame.

### A. Core Foundational Principles

**Guidance Note: Primacy of Framed Quotations (SUPERSEDES PREVIOUS QUOTE RULES)**
Core Principle: If a direct quotation (or a clearly attributed statement from a specific source) within the segment carries a distinct Alarmist or Reassuring frame, the segment's Dim1_Frame MUST reflect the frame of that quotation/attributed statement. This principle applies even if the author's narrative surrounding the quote is Neutral. The frame is determined by the language and tone used by the quoted source itself.

* **Author's Neutrality:** When the author neutrally reports a framed quote, the quote's frame dictates the segment's frame.
* **Author Reinforces Quote's Frame:** If the author's narrative also adopts or amplifies the same frame as the quote, this further strengthens the coding of the quote's frame.
* **Author Challenges Quote's Frame (Advanced):** If the author explicitly challenges, refutes, or heavily recontextualizes the quote's frame using their own explicit framing language, the coder must determine the overall dominant frame of the segment. If the author merely presents a factual counterpoint after a framed quote, without adding their own framing to that counterpoint, the original quote's frame is more likely to prevail or be balanced to Neutral (see Mixed Messages). This scenario requires careful judgment of which frame is more salient. (For most cases, assume the author is not overtly challenging if they present the quote straightforwardly).
* **Multiple Framed Quotes & Mixed Messages within a Single Quote:**
    * If a segment contains multiple quotes with different frames, determine the dominant frame. If one quote is significantly more potent or central to the segment's point, its frame may prevail.
    * **Handling Mixed Messages with Contrastive Conjunctions (e.g., 'but,' 'however'):**
        * When a single quoted statement contains potentially mixed framing elements, particularly when linked by contrasting conjunctions (e.g., 'but,' 'however'):
            * Evaluate Each Clause for Explicit Framing: Independently assess the clause before the conjunction and the clause after the conjunction for the presence of explicit framing cues that meet the definitions for Alarmist or Reassuring in this codebook. This means applying the full Alarmist/Reassuring/Neutral definitions to each part of the source's statement.
            * Framing Strength of the Concluding Clause: For the clause after the conjunction to override or neutralize an explicitly framed initial clause, it MUST ITSELF contain clear and explicit framing language that meets the criteria for Reassuring or Alarmist. A neutrally worded factual statement, even if it factually counters or mitigates the initial clause, does not typically establish a new frame nor neutralize a potent initial frame on its own.
            * Resolution Scenarios:
                * Explicit Frame in Second Clause: If the second clause contains explicit framing cues (Reassuring or Alarmist) that are at least as potent as, or more potent than, the first clause (per 'Principle of Cue Sufficiency'), it will generally determine or significantly influence the segment's frame.
                * No Explicit Framing in Second Clause (Canonical Example):
                    Text: "Meanwhile, Kirby Institute head of biosecurity Professor Raina MacIntyre described the bird flu news as 'concerning.' She \[Professor Raina MacIntyre\] said, however, that Avian flu viruses do not transmit easily in humans because they \[Avian flu viruses\] are adapted for birds."
                    Correct Code: Neutral.
                    Reasoning: "The source provides an initial mild-to-moderate alarm cue ('concerning'). The subsequent clause, introduced by 'however,' states a fact ('do not transmit easily') that has reassuring implications but is itself presented by the source without any explicit reassuring language from the source (e.g., no 'thankfully,' 'which is excellent news,' 'so the public can rest easy,' 'this low transmissibility means the risk is negligible'). The neutrally-presented factual counter-statement balances the initial mild concern without the second part actively meeting the criteria for a Reassuring frame on its own. Thus, the overall segment is Neutral."
                * Strong Initial Frame, Neutral Counter: If the first clause has strong/potent framing (e.g., 'This is a disaster!') and the second is a neutral factual counter (e.g., 'but containment measures are in place.'), the initial strong frame is very likely to prevail. The neutral fact does not actively reassure enough to override potent alarm.
                * Scenario: Initial Neutral Fact, Followed by Framed Statement:
                    Text: Quote: "Cases have risen by 10%, but I want to assure everyone that this is well within our projections and our health system is fully prepared to manage it effectively; there is no cause for panic."
                    Code: Reassuring (Quote-driven).
                    Reasoning: "The initial clause states a negative fact neutrally. The second clause, introduced by 'but,' contains multiple explicit reassuring cues from the source ('want to assure everyone,' 'well within our projections,' 'fully prepared to manage it effectively,' 'no cause for panic'). The reassuring part clearly dominates. Decisive cues: 'assure everyone,' 'no cause for panic'."
                * Conflicting Explicit Frames: If both clauses contain explicit but opposing framing cues of roughly equal potency, and no clear overall dominant frame emerges, Neutral might be appropriate if no single frame ultimately dominates.
    * If frames from multiple quotes or within a single quote are genuinely balanced and conflicting with no clear dominant or more potent element (and the above mixed message guidance doesn't resolve to a single frame), Neutral might be appropriate if no single frame ultimately dominates.
    * **Mixed Information without Strong Contrastive Conjunctions:** If a quote contains both negative/neutral factual information and a positive factual statement (e.g., absence of a negative outcome) joined by 'and' or simple sequencing, the positive factual statement must *itself* be framed with explicit reassuring language by the source to make the overall segment Reassuring. Otherwise, if both parts are factually stated and neither contains dominant alarmist or reassuring framing from the source, the segment is likely Neutral.
        * Example: Quote: 'The agency confirmed that containment efforts are underway in the affected zones, including restrictions on movement, and that currently no spread to adjacent areas has been found.' → Neutral. (Rationale: The quote states control measures and a positive fact ('no spread'). The 'no spread' is stated factually by the source, without added reassuring framing like 'which is excellent news and means the situation is contained.')
* **Examples:**
    * Quote drives Alarmist frame: Author: "Regarding the new variant, Dr. Smith stated," Quote: "'This is a catastrophic development with potentially devastating consequences.'" → Code Alarmist based on Dr. Smith's framed statement.
    * Quote drives Reassuring frame: Author: "An agency spokesperson commented on the recent measures," Quote: "'We are pleased to report that all tests have been negative, and the situation is now fully contained.'" → Code Reassuring based on the spokesperson's framed statement.

**Default-to-Neutral Rule (Strictly Presentation-Focused)**
Heuristic: In the absence of explicit emotional language, specific framing cues (e.g., loaded adjectives, urgent tone, calming words), or a distinct rhetorical tone from EITHER the segment's author OR any directly quoted source within the segment, Neutral is the appropriate code for Dim1_Frame.Crucial Clarification: This rule applies if both the author's presentation and the presentation by any quoted sources are neutral.

* If a segment reports objectively severe facts, and both the author and any quoted source commenting on these facts use neutral, factual language without added alarmist rhetoric, the Dim1_Frame is Neutral.
* Similarly, if a segment reports objectively positive facts, and both the author and any quoted source use neutral, factual language without added reassuring rhetoric, the Dim1_Frame is Neutral.
* The focus remains on the presentation by the author and by any quoted sources.

**Precedence if Multiple Dimension 1 Guidance Notes Apply (Highest First):**
1.  Guidance Note: Primacy of Framed Quotations.
2.  Directly loaded Alarmist or reassuring language from the author (if quotes are neutral/absent).
3.  Dimension 1 - Guidance Note: Principle of Cue Sufficiency (applied to author or quoted source).
4.  Default-to-Neutral Rule (Strictly Presentation-Focused).

**Guidance Note: Framing of Calls to Action, Directives, and Urgings**
Statements reporting calls for action (e.g., 'scientists call for vigilance'), directives ('X must be done'), or urgings ('officials urged X') require careful attention to the framing provided by the source of the call/directive or the author reporting it.

* They are typically Neutral IF reported factually as a response/recommendation without the source/author adding explicit alarmist or reassuring language.
    * Example (Neutral): 'Cooke said there are things you must do to protect your birds from disease.' (Rationale: Cooke's directive, as quoted, is instructional. It lacks explicit alarmist rhetoric about the disease itself from Cooke, or additional deontic urgency cues as defined under Alarmist.)
* They become Alarmist IF the call/directive is explicitly framed by the source/author with:
    * Strong deontic urgency (e.g., 'must act immediately,' 'have to as soon as possible') directly linked to averting a stated severe negative outcome (e.g., 'to prevent catastrophic spillover,' 'to protect human health from an imminent threat'). (See Alarmist Inclusion Criteria for more examples).
    * Language depicting current responses as critically inadequate (e.g., 'equivalent of winging it').
    * An overtly urgent/fearful tone accompanying the call.
* They are NOT Reassuring simply because they propose a protective action. Reassurance requires active calming about the current state of risk.
    * Example (Alarmist): 'Experts issued a grave warning, stating that unless immediate, drastic action is taken, a catastrophic health crisis is unavoidable.'
    * Example (Alarmist): Author: 'Officials urgently pleaded with the public to evacuate, emphasizing that remaining posed an extreme and immediate lethal threat.'

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

---
**Quick Decision Tree (for Dimension 1 Framing)**

0.  **Dominant Vivid Cue Check:** Does a single, highly vivid, potent, or strategically emphasized framing cue (per the 'Principle of Cue Sufficiency,' including strong metaphors, deontic urgency, negated reassurance, loaded rhetorical questions, unequivocal statements of extreme danger/safety, etc.) from either a quoted source or the author clearly dominate the segment?
    * → If Yes, code according to that dominant cue (Alarmist or Reassuring) and proceed to justification.
    * → If No, or if unclear, proceed to Step 1.
1.  Does any directly quoted source in the segment present with a clear Alarmist frame (using loaded alarm words, high-valence impact adjectives, urgent tone, deontic urgency etc., per Alarmist Inclusions)?
    * → **Alarmist**
2.  Else, does any directly quoted source in the segment present with a clear Reassuring frame (using explicit calming words, optimistic tone, downplaying risk, rhetorical emphasis on positive aspects, etc., per Reassuring Inclusions)?
    * → **Reassuring**
3.  Else (i.e., all quotes are Neutral, unfraged by the source, or absent), does the segment's author's presentation use loaded alarm words, high-valence impact adjectives, deontic urgency or other potent cues to evoke fear or extreme concern (see Alarmist Inclusions)?
    * → **Alarmist**
4.  Else (all quotes Neutral or absent), does the segment's author's presentation use explicit calming or control language, rhetorical emphasis on positive aspects, or other potent reassuring cues (see Reassuring Inclusions)?
    * → **Reassuring**
5.  Otherwise (i.e., both the author and all quoted sources present information neutrally, or any framing cues are insufficient to meet Alarmist or Reassuring criteria per the above steps, including the Core Principles & Common Pitfalls guidance)
    * → **Neutral**

---
**Common LLM Misinterpretations & How to Avoid Them**
1. **Mistaking Large Numbers/Severe Outcomes for Alarmist Framing:** Large casualty counts, high costs, or severe statistics are Neutral if reported factually without explicit alarmist language from the author/source. Focus on *how* the numbers are presented, not their magnitude. (See Neutral - Inclusion Criteria for factual reporting of negative statistics.)
2. **Assuming Positive Facts (e.g., 'no human cases') are Always Reassuring:** The absence of negative events is Neutral unless the author/source adds explicit reassuring language to actively calm broader concerns. (See Reassuring - Exclusion Criteria for simple absence of negative events.)
3. **Treating Technical Terms as Inherently Alarmist:** Terms like "highly pathogenic," "depopulated," or "high mortality rate" are often Neutral when used as standard descriptors or official classifications. (See Guidance Note: Handling Technical Terms.)
4. **Confusing Capability/Preparedness Statements with Active Reassurance:** Describing safeguards, capabilities, or control measures is Neutral unless explicitly framed as a reason for current calm or minimized risk. (See Common Pitfalls (C) and Reassuring - Exclusion Criteria.)
5. **Overweighting Single Negative Adjectives:** Mild terms like "concerning" or standard descriptors like "deadly" (when describing disease characteristics) are often Neutral unless part of broader alarmist rhetoric. (See Alarmist - Exclusion Criteria for factual descriptions.)
6. **NEW (v2.10) - Treating Bare Negations as Reassuring:** Statements like "not expected to cause problems" or "unlikely to affect production" are Neutral unless paired with explicit calming/safety cues (e.g., "so the risk remains low," "meaning consumers can be confident"). The negation alone is insufficient for Reassuring framing.

---
**Dimension 1 - Guidance Note: Principle of Cue Sufficiency**
Consistent with established framing theory, a single, highly vivid, potent, or strategically emphasized framing cue in the presentation by either a quoted source or the author can be sufficient to categorize a segment as Alarmist or Reassuring. This includes powerful metaphors, stark worst-case scenarios phrased alarmingly, unequivocal statements of extreme danger or safety, brief but intensely emotional language, or strategically employed verbs (e.g., imperatives, deontic modals like 'must,' 'have to'), adverbs (e.g., 'immediately,' 'as soon as possible'), loaded rhetorical questions, or specific rhetorical constructions (e.g., negated reassurance) that convey a strong sense of urgency, risk, or (conversely) control and safety. The presence of such a cue should be evaluated holistically for its likely impact.
* **Example of Sufficient Alarmist Cue (from Quote):** "The virologist warned, 'This pathogen is a clear and present existential threat to public health.'"
    * Coding Rationale: Alarmist due to the extreme potency of the 'clear and present existential threat' statement from the quoted virologist.
* **Example of Sufficient Reassuring Cue (from Quote):** "The Health Minister announced, 'Following extensive testing, this product is unequivocally safe for all consumers.'"
    * Coding Rationale: Reassuring due to the definitive statement from the quoted Health Minister.
* **Counter-Example (Insufficient Cue from Author, no framed quote):** Author: "The situation is, well, a bit concerning if you look at it one way, but not really a big deal."
    * Coding Rationale: Likely Neutral. The author's vague and contradicted "concerning" is insufficient, assuming no framed quotes.

---
## Dimension 4: Justification Note (Mandatory)
Purpose: Provide a comprehensive free-text explanation for the Dimension 1 coding decision (Frame) for EVERY segment. This note is crucial for understanding the coder's rationale, ensuring consistency, and aiding in review or adjudication. It should specify whether the frame is driven by a quoted source or the author.
**Code: \[MANDATORY Free Text Note\]** This field must not be empty or "N/A".
Definition: A MANDATORY string. This note MUST provide the reasoning for the Dimension 1 coding decision. It cannot be "N/A" or an empty string. The note must briefly explain why the chosen frame applies, indicating if it's quote-driven or author-driven. Critically, the note MUST include a direct quotation of the primary word(s) or short phrase (ideally ≤12 words, but longer if necessary to capture a complex rhetorical device) from the segment text that served as the most decisive linguistic cue(s) for the Dim1_Frame determination. If the frame choice was difficult due to suspected sarcasm/irony (from author or quote) or because it relied on an accumulation of subtle cues rather than one single potent cue (especially for Neutral when potential weak cues were dismissed), the note MUST identify the specific phrase(s) or describe the situation, briefly explain the difficulty, and state why the chosen frame was selected.
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

---
## Few-Shot Exemplars (Crystal-Clear Demonstrations)

**These four examples demonstrate the core framing patterns. Learn from these precise distinctions:**

| **Category** | **Example Sentence** | **Correct Label** | **Key Cue** |
|--------------|---------------------|-------------------|--------------|
| **Alarmist – Intensifier + adjective** | "The flu is so deadly that entire flocks are culled." | **Alarmist** | "so deadly" (intensifier + risk adjective) |
| **Alarmist – High-potency verb** | "An outbreak ravaged farms across three states." | **Alarmist** | "ravaged" (vivid, destructive verb) |
| **Alarmist – Loaded Q** | "Should consumers be worried about buying eggs?" | **Alarmist** | Loaded rhetorical question implying worry |
| **Reassuring – Minimiser + contrast** | "Only one barn was infected out of thousands nationwide." | **Reassuring** | "Only...out of thousands" (minimizer + scale contrast) |

**Key Learning Points:**
- **Alarmist requires explicit intensification** beyond factual reporting
- **High-potency verbs** like "ravaged" create vivid, alarming imagery
- **Loaded questions** that imply worry/danger are strong Alarmist cues
- **Reassuring requires both minimization AND contrast** to show scale

Text Segment to Analyze:
\`\`\`text
{statement_text}
\`\`\`

**Coder Sanity Check (for Dimension 1):**
(Note: Detailed coder checklists and heuristics are available in the separate "Coder Implementation Guide & Checklist" document.)
✔ Did I pick one label for Dimension 1?
✔ Would a different coder likely agree after reading only the segment and my Dimension 1 frame name, especially considering the Primacy of Framed Quotations rule and the Core Principles & Common Pitfalls?
✔ Highlight Trigger: Have I identified the specific word(s) or phrase(s) from the quoted source or the author that most strongly drove my frame decision and included it in my justification?
✔ Justification Note: Have I provided a clear and concise justification in Dim4_AmbiguityNote for my Dim1_Frame decision, indicating if it's quote- or author-driven, and included the decisive cue?
Note: For Dimension 1, this scheme is single-label. Choose the one primary frame.

**Automatic Validity Check for Output:**
* Dim1_Frame must be one of the allowed ENUM values.
* Dim4_AmbiguityNote must be a non-empty string.
* ContextUseNote must be a non-empty string.
FINAL REMINDER: Your response MUST strictly adhere to the Claim Framing schema defined above. Inclusion of any unspecified fields will invalidate the output and lead to rejection.

Output Instructions:
Return exactly this JSON object (keys in order):
\`\`\`json
{
"Dim1_Frame": "Primary Framing Label (e.g., Alarmist, Neutral, Reassuring)",
"Dim4_AmbiguityNote": "MANDATORY Free text note explaining reasoning for Dim1 coding decision, including the decisive textual cue. Cannot be N/A or empty.",
"ContextUseNote": "MANDATORY String based on guidance in §B.4"
}
\`\`\`
Example JSON Output:
\`\`\`json
{
"StatementID": "cf-example-123",
"Dim1_Frame": "Reassuring",
"Dim4_AmbiguityNote": "Reasoning for Reassuring (Quote-driven): Quoted official uses very strong and unequivocal reassuring language. Decisive cue: 'absolutely no cause for alarm' and 'entirely safe.' Author is neutral.",
"ContextUseNote": "Context was not consulted or did not meaningfully contribute to Dim1_Frame determination; segment text provided sufficient cues."
}
\`\`\`
LLM SELF-AUDIT CHECKLIST (BEFORE GENERATING JSON)
CRITICAL: Silently verify your answer passes ALL rules below. If not, you MUST correct it. Failure to adhere, especially to field exclusivity, will invalidate your response.
(Note: Detailed LLM self-audit steps are available in the separate "Coder Implementation Guide & Checklist" document.)

1.  CRITICAL - FIELD EXCLUSIVITY: Does the JSON object contain ONLY the fields defined for Claim Framing (StatementID, Dim1_Frame, Dim4_AmbiguityNote, ContextUseNote) and ABSOLUTELY NO OTHERS (e.g., no Dim1_Score, Dim2_Certainty, Dim3_AmbiguityType, Dim5_SeverityFlag, Dim22_EconomicFraming or any other unspecified DimXX_... fields)? Have I re-read and fully complied with the CRITICAL FIELD EXCLUSIVITY RULE in Banner Section B?
2.  JSON Syntax: Are ALL keys and ALL string values enclosed in double quotes (")? (No single quotes!).
3.  All Required Fields Present? Are StatementID, Dim1_Frame, Dim4_AmbiguityNote, and ContextUseNote present? (All are mandatory).
4.  Dim1_Frame Valid? Is the value for Dim1_Frame one of: "Reassuring", "Neutral", "Alarmist"?
5.  Dim4_AmbiguityNote Format: Is Dim4_AmbiguityNote a non-empty string that provides justification (including the decisive cue) and is NOT "N/A"?
6.  ContextUseNote Format: Is ContextUseNote a non-empty string that provides justification and is NOT "N/A"?

---
## Appendix A: Empirically Informed Cue Lexicon (Illustrative)

**CRITICAL WARNING: This Lexicon is ILLUSTRATIVE and HEURISTIC ONLY. It is NOT a definitive checklist. The presence of a word from this list DOES NOT automatically assign a frame. The main definitions, inclusion/exclusion criteria, and the 'Principle of Cue Sufficiency' in Dimension 1 are ALWAYS PARAMOUNT. Context, speaker (author vs. quote), and the overall rhetorical presentation determine the frame. This lexicon primarily serves to sensitize coders to potentially salient terms that might contribute to a frame if used in specific ways consistent with the main definitions.**

**Cue Potency Scale (Conceptual Guide)**
To aid in applying the 'Principle of Cue Sufficiency,' consider the conceptual potency of cues. This is not a rigid scale but a way to think about cue strength:

**High Potency Cues (Often Sufficient Alone if Unambiguous and from Author/Dominant Quote):**
* **Alarmist Examples:** 'catastrophe,' 'existential threat,' 'nightmare scenario,' 'unmitigated disaster,' 'ticking time-bomb' (when used seriously), direct and urgent calls to action explicitly linked to preventing immediate, severe, named consequences (e.g., "We must act now or face total collapse!"). Explicit statements of extreme fear from a source (e.g., "I am terrified by this prospect.").
* **Reassuring Examples:** 'completely safe,' 'no danger whatsoever,' 'fully under control,' 'situation is entirely manageable and poses no risk,' 'absolutely no cause for alarm,' 'public can be fully at ease.' Explicit statements of strong confidence/calm from a source (e.g., "We are 100% confident in our safety measures.").

**Moderate Potency Cues (May be sufficient if clear and central; often contribute strongly in accumulation ONLY if tightly coupled and reinforcing an explicit primary cue):**
* **Alarmist Examples:** 'crisis' (when framed as such by author/source, not just mentioned), 'severe impact/damage' (when emphasized by author), 'devastating,' 'soaring/plummeting' (for critical metrics, framed dramatically), 'grave concern' (from authoritative source), 'urgent need' (if context implies high stakes).
* **Reassuring Examples:** 'manageable,' 'low risk' (when actively framed as such with additional reassuring language), 'situation contained/stabilized,' 'good progress,' 'optimistic outlook' (from source, if explicitly linked to reassurance). Rhetorical minimization when coupled with explicit calming phrases.

**Low Potency / Context-Dependent Cues (RARELY sufficient alone; require strong contextual support from more potent cues to contribute to a frame. DO NOT accumulate on their own to shift from Neutral):**
* **Alarmist Examples:** 'concerning,' 'worrying,' 'threat/risk' (when stated factually without amplification), 'problematic,' 'difficult,' 'potential for negative outcome' (stated factually).
* **Reassuring Examples:** 'hopeful signs,' 'positive development' (stated factually), 'efforts underway,' 'plan in place' (without explicit link to current safety/calm). Simple reporting of low numbers or absence of negative events. Minimizers like 'only,' 'just,' 'rare' without accompanying explicit reassuring language.

**Reorganized Lexicon Entries (Illustrative):**
This appendix provides an illustrative list of terms that media effects research (e.g., Burgers & de Graaf, 2013; Dudo et al., 2007) suggests can function as intensifiers or loaded words, potentially increasing perceived sensationalism or risk. Their inclusion here is to aid coders in recognizing language that might contribute to an Alarmist or, in some cases, a Reassuring frame, especially when used directly by a quoted source or the segment's author. Context and intent remain paramount.

* **Potentially Alarmist Intensifiers/Loaded Words (Examples):** \`severe\`, \`worst\`, \`record\` (e.g., record loss/death, record outbreak), \`catastrophic\`, \`crisis\`, \`deadly\` (Often Neutral when used factually to describe a known characteristic or potential impact on a specific group, e.g., 'Disease X is deadly for species Y.' Becomes Alarmist if the author uses it with additional framing to evoke fear beyond this factual description, e.g., 'a terrifyingly deadly virus.'), \`lethal\`, \`devastating\`, \`disastrous\`, \`nightmare\`, \`threat\`, \`imminent\`, \`urgent\`, \`soaring\`, \`surge\`, \`existential\`, \`uncontrolled\`, \`skyrocketing\`, \`grave\`, \`failed dismally\`, \`high\` (Often Neutral when used as a factual descriptor of a characteristic, e.g., 'high mortality rate'; becomes Alarmist if the author/source significantly intensifies it, e.g., 'terrifyingly high' or uses it as part of broader alarmist rhetoric).
* **Verbs/Modals/Adverbs (Potentially Alarmist):** \`must\` (act), \`have to\` (prevent), \`need to\` (address), \`calling for increased vigilance\` (to protect human health) (when linked to severe outcome/inadequacy), \`immediately\`, \`as soon as possible\` (when linked to urgent action against risk). Many verbs (e.g., 'skyrocketed,' 'plummeted,' 'erupted,' 'decimated,' 'crippled') and adverbs (e.g., 'alarmingly,' 'dangerously') can significantly contribute to framing. Evaluate their use in context for potency and whether they accompany other explicit framing cues.
* **Negated Reassurance (Potentially Alarmist):** \`not ruled out\` (pandemic potential).
* **Potentially Reassuring Intensifiers/Loaded Words (Examples):** \`completely safe\`, \`no danger whatsoever\`, \`fully mitigated\`, \`guaranteed safety\`, \`robust protection\`, \`under control\`, \`manageable\`, \`contained\`, \`low risk\`, \`unlikely\`, \`rare\`.
* \`avoided an outbreak\` (of a major threat, implying current safety) (with careful contextual caveats as noted in Reassuring definition).
* **Verbs/Adverbs (Potentially Reassuring):** 'reassuringly,' 'safely,' 'effectively' (when linked to control/management).
* **Illustrative Idiomatic Metaphors**
    * (Note: Context is still paramount for metaphors. Their interpretation depends on how they are used by the source/author.)
    * Potentially Alarmist Metaphors: \`ticking time-bomb\`, \`powder keg\`, \`house of cards\`, \`domino effect\`, \`opening Pandora's box\`, \`slippery slope\`, \`winging it\`, \`rolling the dice\`, \`equivalent of hoping for the best\`.
    * Potentially Reassuring Metaphors: \`silver bullet\`, \`safety net\`, \`firm foundation\`, \`beacon of hope\`.

**Note:** The mere presence of a word from this list does not automatically determine the frame. The word's usage by the quoted source or author, its context, its target, and the overall rhetorical effect must be considered. See Dimension 1 definitions, particularly the "Guidance Note: Primacy of Framed Quotations."
**References (Conceptual Basis for Lexicon Approach):**
* Burgers, C., & de Graaf, A. (2013). Language intensity as a sensationalistic news feature. *Communications, 38*(2), 167-188.
* Dudo, A. D., Dahlstrom, M. F., & Brossard, D. (2007). Reporting a potential pandemic: A risk-related assessment of avian-influenza coverage in U.S. newspapers. *Science Communication, 28*(4), 429-454.

---
## Appendix B: Glossary of Key Terms

**Active Reassurance:** An explicit linguistic or rhetorical effort by the author or quoted source to directly calm audience concerns, minimize perceived current risk, or emphasize present safety/control, going beyond the mere statement of positive facts. This typically involves explicit calming phrases or clear risk-minimizing evaluations.
**Passive Good News:** The factual reporting of positive information, low negative numbers, or the absence of negative events, without additional explicit framing language from the author/source designed to actively reassure or calm broader concerns.
**Explicit Linguistic Cue:** Specific words, phrases, sentence structures, or rhetorical figures demonstrably present in the text that directly contribute to establishing an Alarmist, Reassuring, or Neutral presentational frame, as chosen by the author or quoted source.
**Salience (in context of Dim1):** The quality of being particularly noticeable or important in the author's/source's presentation due to explicit linguistic or rhetorical emphasis, thereby shaping the audience's perception of the topic's urgency, danger, or safety.
**Potent Cue:** A word, phrase, or piece of information in the presentation by a quoted source or the author that is highly likely to strongly influence an average reader's perception of risk or safety due to its intensity, explicitness, authoritativeness, or emotional resonance.
**Vivid Cue:** A presentational cue from a quoted source or the author that is particularly graphic, memorable, or emotionally engaging, making it stand out and potentially have a stronger framing effect.
**Loaded Language:** Words or phrases with strong emotional connotations (positive or negative) used by a quoted source or the author to influence the audience's perception beyond the literal meaning of the words.
**Explicit Framing:** Direct statements by a quoted source or the author that tell the audience how to interpret a situation or what emotional response is appropriate.
**Rhetorical Devices:** Techniques used by a quoted source or the author to persuade or influence an audience.
**High-Valence Impact Adjective/Phrase:** A strong descriptive adjective or short phrase used by a quoted source or the author that emphasizes the severity or scale of a negative event, harm, or failure.
**Deontic Urgency:** The use of imperative or modal language (e.g., 'must,' 'have to') combined with a sense of immediacy or necessity to address a stated risk or severe negative outcome, or to highlight critical inadequacy of current responses.

---
**SIDEBAR: The Symmetry Rule**

The codebook now enforces symmetric standards between Alarmist and Reassuring frames:

**For Alarmist:** Severe facts require explicit intensification
- "50 million birds culled" → Neutral (factual)
- "A catastrophic 50 million birds slaughtered" → Alarmist (intensified)

**For Reassuring:** Positive facts require explicit calming cues
- "Not expected to lower production" → Neutral (bare negation)
- "Not expected to lower production, so the risk remains very low" → Reassuring (calming cue added)

Both frames now require active linguistic effort beyond stating facts.

<details>
<summary>Neutral Verbs Reference (always Neutral unless paired with other alarm cues) ▼</summary>

| hit | affect/affected | impact/impacted | raise(d) concern(s) | concern(s) | warn(ed) | trend(ing) | fluctuate(d) | volatility / volatile |
</details>

*Using a low-potency verb **alone** (e.g., "experts *warned* prices *could* rise") does **not** escalate the frame beyond Neutral.*

##### Economic & Price Language Quick-Reference

| Phrase (example) | Frame | Rationale |
|------------------|-------|-----------|
| "Prices **soared / skyrocketed**" | Alarmist | vivid verb |
| "Prices **trended sharply higher**" | Neutral | descriptive verb + adverb only |
| "Experts warn prices **could become volatile**" | Neutral | modal + mild adjective |

Adverbs such as **sharply, significantly, notably** do **not** raise potency *unless* paired with a vivid verb or risk adjective ("sharply worsening crisis").