# Multi-Coder Analysis with Tree of Thoughts

This project provides a comprehensive pipeline for claim framing analysis, featuring both traditional multi-model consensus approaches and a novel 12-hop Tree of Thoughts (ToT) reasoning chain.

## Features

- **12-Hop Tree of Thoughts**: Deterministic, auditable claim framing analysis
- **Rule-Based Decision Tree**: Transparent classification following predefined precedence rules
- **Comprehensive Audit Trails**: Complete traceability of reasoning steps
- **Modular Architecture**: Easy integration with existing analysis pipelines
- **Consensus-Across-Permutations**: Run eight row-order permutations in parallel and apply per-hop majority voting.
- **Lazy Materialisation (RAM-Friendly)**: Concluded segments are streamed to on-disk JSONL archives so that memory usage stays bounded even on very large datasets.

## Quick Start

### Prerequisites

```bash
pip install pandas tqdm openai pyyaml
```

### Environment Setup

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Basic Usage

Run the Tree of Thoughts pipeline:

```bash
cd multi_coder_analysis
python main.py --use-tot --phase test --dimension framing
```

### Command Line Options

- `--use-tot`: Activate the 12-hop Tree of Thoughts reasoning chain
- `--phase`: Analysis phase (test, pilot, validation)
- `--dimension`: Analysis dimension (framing)
- `--config`: Configuration file path (default: config.yaml)
- `--limit`: Limit number of statements (for testing)
- `--consensus {none,hop}`: Enable hop-level voting across permutations.
- `--batch-size N`: Number of segments sent to the LLM per request.
- `--perm-workers N`: Number of OS processes that each handle one permutation set (P1 … P8).
- `--archive-enable/--no-archive-enable`: Toggle lazy materialisation (enabled by default).

## How It Works

The ToT pipeline processes each text segment through a sequential 12-hop reasoning chain:

1. **Q1**: Intensifier + Risk-Adjective → Alarmist
2. **Q2**: High-Potency Verb/Metaphor → Alarmist  
3. **Q3**: Moderate Verb + Scale/Impact → Alarmist
4. **Q4**: Loaded Rhetorical Question → Alarmist
5. **Q5**: Explicit Calming Cue → Reassuring
6. **Q6**: Minimiser + Scale Contrast → Reassuring
7. **Q7**: Bare Negation → Neutral
8. **Q8**: Capability/Preparedness → Neutral
9. **Q9**: Factual Reporting → Neutral
10. **Q10**: Speculation about Relief → Neutral
11. **Q11**: Framed Quotations → Variable
12. **Q12**: Default → Neutral

### Consensus-Across-Permutations (New)

When you add `--permutations --consensus hop` the runner duplicates the dataset **eight times** and re-orders each copy according to a predefined AB / BA / … scheme.  All copies are then split into equal-sized batches (default *10* or the value you pass via `--batch-size`).

At every hop:

1. The *same* batch index is processed concurrently in **all** permutation sets using a single batched LLM call per permutation.  You will therefore see the familiar log line

   ```
   Batch Q05: attempt 1 succeeded for 200/200 objects; still missing 0
   ```

   eight times (one per permutation tag).
2. The hop-level voting rule aggregates the eight answers for each segment.  If the rule determines a final frame the segment is marked *concluded* in **every** permutation set.
3. An `_ArchivePruneStep` immediately streams all concluded segments to `output/archive/<run_id>_<tag>.jsonl` and removes them from memory.  Only the unresolved remainder continues to the next hop.

Memory usage therefore scales with *unresolved* items, not with total dataset size, making it feasible to process tens of thousands of rows on commodity hardware.

### JSONL Archive Format

Each worker appends to its own file:

```
output/archive/<run_id>_<tag>.jsonl
```

Every line has the schema:

```jsonc
{
  "statement_id": "S1234",
  "permutation": 3,   // P4 = index 3
  "hop": 5,
  "frame": "alarmist yes"
}
```

These files are append-only and can be consumed by downstream analytics without waiting for the entire run to finish.

## Output

Each segment produces:

- **Main Output**: CSV with `Dim1_Frame`, `Dim4_AmbiguityNote`, etc.
- **Audit Trail**: `traces_tot/<StatementID>.jsonl` with hop-by-hop decisions
- **Complete Reasoning**: Full rationale for each classification

## Project Structure

```
multi_coder_analysis/
├── main.py                     # Main entry point
├── run_multi_coder_tot.py      # ToT pipeline controller
├── hop_context.py              # State management
├── utils/
│   └── tracing.py              # Audit trail utilities
└── prompts/                    # Prompt repository
    ├── global_header.txt       # Global instructions
    ├── hop_Q01.txt             # Question 1: Intensifiers
    ├── hop_Q02.txt             # Question 2: High-potency verbs
    ├── ...                     # Questions 3-12
    └── hop_Q12.txt             # Question 12: Default
```

## Examples

### Alarmist Classification
Input: "The flu is so deadly that entire flocks are culled."
- Q1: YES (intensifier "so" + risk-adjective "deadly")
- Output: Alarmist

### Reassuring Classification  
Input: "Health officials say the outbreak is fully under control."
- Q5: YES (explicit calming cue "fully under control")
- Output: Reassuring

### Neutral Classification
Input: "Three cases were confirmed at the facility on Tuesday."
- Q1-Q11: NO
- Q12: YES (factual reporting without explicit framing)
- Output: Neutral

## Configuration

The system uses a YAML configuration file. A minimal example:

```yaml
logging:
  level: INFO
file_paths:
  file_patterns:
    model_majority_output: '{phase}_model_labels.csv'
```

## Development

### Adding New Hop Questions

1. Create `prompts/hop_Q##.txt` with few-shot examples
2. Update `Q_TO_FRAME` mapping in `run_multi_coder_tot.py`
3. Update documentation

### Testing

The system includes automatic test data generation for development:

```bash
python main.py --use-tot --phase test --limit 5
```

## Architecture

See `docs/architecture.md` for detailed technical documentation.

<!-- API-REFERENCE:START -->
This section will be automatically updated with API documentation when code changes are detected.
<!-- API-REFERENCE:END -->

## License

[Add your license information here]

## Provider Support

The pipeline supports multiple LLM providers:

### Gemini (Default)
Set up your environment:
```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

### OpenRouter
For accessing diverse models through OpenRouter:
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

## Running the Pipeline

### Basic Usage
```bash
python multi_coder_analysis/main.py --use-tot --limit 1 --input data/gold_standard.csv
```

### With Different Providers
```bash
# Use Gemini (default)
python multi_coder_analysis/main.py --use-tot --provider gemini --model models/gemini-2.0-flash

# Use OpenRouter with different models  
python multi_coder_analysis/main.py --use-tot --provider openrouter --model mistralai/mistral-small-latest
python multi_coder_analysis/main.py --use-tot --provider openrouter --model anthropic/claude-3-haiku
```

### Command Line Options
- `--provider {gemini,openrouter}`: Choose LLM provider (default: gemini)
- `--model MODEL`: Specify model name
- `--limit N`: Process only first N statements  
- `--input FILE`: Input CSV file path
- `--use-tot`: Enable Tree-of-Thought reasoning (required)

## Configuration

Edit `multi_coder_analysis/config.yaml` to set default provider:
```yaml
provider: gemini  # or openrouter
```

## Examples

Process a single statement with confidence analysis:
```bash
python multi_coder_analysis/main.py --use-tot --limit 1 \
  --input multi_coder_analysis/data/gold_standard.csv \
  --provider openrouter \
  --model mistralai/mistral-small-latest
``` 