# Self-Consistency Decoding

The *Self-Consistency* strategy samples multiple stochastic paths through the
Tree-of-Thought (ToT) pipeline and aggregates them with a voting rule.

## 1  CLI Usage

```bash
# N=8 stochastic paths, ranked-list answers, Borda aggregation
mca run statements.csv out/ \
  --decode-mode self-consistency \
  --votes 8 \
  --ranked-list \
  --sc-rule borda \
  --sc-temperature 0.7 --sc-top-k 40 --sc-top-p 0.95
```

Available `--sc-rule` values:

| Rule      | Description                               |
|-----------|-------------------------------------------|
| majority  | Hard vote on top answer                   |
| ranked    | Vote count tie-break with cost weighting  |
| ranked-raw| Same as `ranked` but ignores normalisation|
| irv       | Instant-Runoff Voting on ranked lists     |
| borda     | Borda count                                |
| mrr       | Mean Reciprocal Rank                       |

`--decode-mode self-consistency-hop` performs voting **per hop** and stops as
soon as a decisive "yes" answer is reached, saving tokens.

## 2  Ranked-List Output Format

The LLM should append a line starting with `Ranking:` followed by up to *N*
frame labels in descending likelihood.  The parser is liberal:

```
Ranking: Alarmist > Neutral > Reassuring
Ranking – Alarmist → Neutral → Reassuring
Ranking:
1. Alarmist
2. Neutral
3. Reassuring
```

Delimiters recognised: `>`, `→`, `->`, `⇒`, commas, newlines.
Numbering / bullet prefixes are stripped automatically.

## 3  Confidence Calculation (ranked rule)

```
conf = vote_share × (1 – best_cost / worst_cost)
```

* **vote_share** – winner votes ÷ total votes
* **cost**       – average token cost per candidate (lower = better)

This yields 0 ≤ *conf* ≤ 1 and scales naturally with both agreement and model
likelihood.

## 4  Provider Usage Accounting

Providers now implement:

```python
provider.reset_usage()      # zero counters before sampling
usage = provider.get_acc_usage()  # returns dict with token deltas
```

Self-consistency helpers use these APIs for accurate, thread-safe cost
estimation.

---

For implementation details see `multi_coder_analysis/core/self_consistency*.py`. 