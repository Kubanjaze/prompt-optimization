# Phase 70 — System Prompt Optimization for SAR Extraction

**Version:** 1.1 | **Tier:** Standard | **Date:** 2026-03-27

## Goal
Compare two system prompts for SAR extraction accuracy: a minimal prompt vs a detailed expert prompt.
Measures whether prompt engineering improves structured data extraction from free-text compound descriptions.

CLI: `python main.py --input data/compounds.csv --n 5`

Outputs: prompt_comparison.json, optimization_report.txt

## Logic
- Define two system prompts: "minimal" (generic instruction) and "expert" (domain-specific with thresholds, family list, example)
- For each of 5 compounds, build a natural language SAR description
- Send each description to Claude with both prompts, compare extraction accuracy
- Accuracy: exact match on compound_name, activity_class, scaffold_family; ±0.1 on pIC50

## Key Concepts
- System prompt engineering: specificity, domain terms, and examples improve extraction
- A/B comparison: same model, same user message, different system prompts
- Minimal: "Extract compound data from the text. Return JSON."
- Expert: includes pIC50 classification thresholds, scaffold family list, example JSON
- The expert prompt provides the knowledge model needs to derive scaffold_family from name prefix

## Verification Checklist
- [x] Both prompts produce valid JSON
- [x] Expert prompt accuracy >> minimal prompt accuracy
- [x] Per-field comparison shows scaffold_family as the differentiator
- [x] 10 total API calls (2 per compound × 5)

## Results
| Metric | Value |
|--------|-------|
| Minimal prompt accuracy | 0% (all failed on scaffold_family) |
| Expert prompt accuracy | 100% (all fields correct) |
| Improvement | +100% |
| Failure mode | Minimal prompt doesn't know scaffold family taxonomy |
| Total input tokens | 2102 |
| Total output tokens | 800 |
| Est. cost | $0.0049 |

Key finding: The minimal prompt got name, pIC50, and activity_class correct but failed on scaffold_family for all 5 compounds. The expert prompt achieved 100% by defining the exact taxonomy (benz/naph/ind/quin/pyr/bzim) and the prefix-to-family mapping rule. This demonstrates that domain-specific definitions in system prompts are critical for extraction tasks with implicit ontologies.
