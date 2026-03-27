# Phase 70 — System Prompt Optimization for SAR Extraction

**Version:** 1.0 | **Tier:** Standard | **Date:** 2026-03-27

## Goal
Compare two system prompts for SAR extraction accuracy: a minimal prompt vs a detailed expert prompt.
Measures whether prompt engineering improves structured data extraction from free-text compound descriptions.

CLI: `python main.py --input data/compounds.csv --n 5`

Outputs: prompt_comparison.json, optimization_report.txt

## Logic
- Define two system prompts: "minimal" (generic instruction) and "expert" (domain-specific with examples)
- For each of 5 compounds, build a natural language SAR description
- Send each description to Claude with both prompts, asking for JSON extraction
- Compare: which prompt produces more accurate compound_name, pIC50, activity_class, scaffold_family?
- Report: per-prompt accuracy, field-level comparison, cost difference

## Key Concepts
- System prompt engineering: specificity, domain terms, examples improve extraction
- A/B comparison: same model, same user message, different system prompts
- Accuracy metric: exact match on compound_name, activity_class, scaffold_family; ±0.1 on pIC50
- Minimal prompt: "Extract compound data from the text. Return JSON."
- Expert prompt: includes classification thresholds, field definitions, scaffold family list, example JSON

## Verification Checklist
- [ ] Both prompts produce valid JSON
- [ ] Expert prompt accuracy >= minimal prompt accuracy
- [ ] Per-field comparison reported
- [ ] 2 API calls per compound (10 total for n=5)

## Risks
- Small n (5) may not show statistical significance
- Both prompts may achieve 100% on easy examples (our compounds have explicit data)
- Cost: 2× API calls per compound
