import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse, os, json, re, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from dotenv import load_dotenv
import anthropic

load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

MINIMAL_SYSTEM = "Extract compound data from the text. Return JSON with compound_name, pic50, activity_class, scaffold_family."

EXPERT_SYSTEM = """You are a medicinal chemistry data extraction specialist.

Extract structured data from compound descriptions. Use these exact definitions:

Activity classes by pIC50:
- inactive: pIC50 < 5.0
- weak: 5.0 <= pIC50 < 6.0
- moderate: 6.0 <= pIC50 < 7.0
- potent: 7.0 <= pIC50 < 8.0
- highly_potent: pIC50 >= 8.0

Scaffold families (determined by compound name prefix):
- benz, naph, ind, quin, pyr, bzim, other

Return JSON: {"compound_name": "exact name", "pic50": <float>, "activity_class": "<class>", "scaffold_family": "<family>"}

Example: "benz_001_F with pIC50 of 7.25" → {"compound_name": "benz_001_F", "pic50": 7.25, "activity_class": "potent", "scaffold_family": "benz"}"""


def pic50_to_class(pic50: float) -> str:
    if pic50 < 5.0:   return "inactive"
    elif pic50 < 6.0: return "weak"
    elif pic50 < 7.0: return "moderate"
    elif pic50 < 8.0: return "potent"
    else:             return "highly_potent"


def build_description(row) -> str:
    """Build a natural language SAR description to extract from."""
    cls = pic50_to_class(row["pic50"])
    return (
        f"Compound {row['compound_name']} (SMILES: {row['smiles']}) showed a measured pIC50 of {row['pic50']:.2f}, "
        f"placing it in the {cls} activity range for CETP inhibition."
    )


def extract_json(text: str) -> dict:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {}


def score(parsed: dict, row) -> dict:
    true_class = pic50_to_class(row["pic50"])
    true_family = row["compound_name"].split("_")[0]
    name_ok = parsed.get("compound_name") == row["compound_name"]
    pic50_ok = abs(parsed.get("pic50", 0) - row["pic50"]) < 0.1
    class_ok = parsed.get("activity_class") == true_class
    family_ok = parsed.get("scaffold_family") == true_family
    return {"name_ok": name_ok, "pic50_ok": pic50_ok, "class_ok": class_ok, "family_ok": family_ok,
            "all_ok": name_ok and pic50_ok and class_ok and family_ok}


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", required=True)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    df = pd.read_csv(args.input).head(args.n)
    client = anthropic.Anthropic()

    print(f"\nPhase 70 — System Prompt Optimization")
    print(f"Model: {args.model} | Compounds: {args.n}\n")

    results = {"minimal": [], "expert": []}
    total_input = 0
    total_output = 0

    for prompt_name, system_prompt in [("minimal", MINIMAL_SYSTEM), ("expert", EXPERT_SYSTEM)]:
        print(f"--- {prompt_name.upper()} prompt ---")
        for _, row in df.iterrows():
            desc = build_description(row)
            response = client.messages.create(
                model=args.model, max_tokens=256,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Extract data from: {desc}"}],
            )
            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            parsed = extract_json(text)
            scores = score(parsed, row)
            total_input += response.usage.input_tokens
            total_output += response.usage.output_tokens

            tag = "OK" if scores["all_ok"] else "MISS"
            print(f"  {row['compound_name']:20s} [{tag}] name={scores['name_ok']} pic50={scores['pic50_ok']} class={scores['class_ok']} fam={scores['family_ok']}")
            results[prompt_name].append({"compound": row["compound_name"], "parsed": parsed, **scores})
        print()

    # Compare
    min_acc = sum(1 for r in results["minimal"] if r["all_ok"]) / args.n
    exp_acc = sum(1 for r in results["expert"] if r["all_ok"]) / args.n

    cost = (total_input / 1e6 * 0.80) + (total_output / 1e6 * 4.0)
    report = (
        f"Phase 70 — System Prompt Optimization\n{'='*50}\n"
        f"Model: {args.model}\nCompounds: {args.n}\n\n"
        f"Minimal prompt accuracy: {min_acc:.0%}\n"
        f"Expert prompt accuracy:  {exp_acc:.0%}\n"
        f"Improvement: {exp_acc - min_acc:+.0%}\n\n"
        f"Total tokens: in={total_input} out={total_output}\n"
        f"Cost: ${cost:.4f}\n"
    )
    print(report)

    with open(os.path.join(args.output_dir, "prompt_comparison.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.output_dir, "optimization_report.txt"), "w") as f:
        f.write(report)
    print("Done.")


if __name__ == "__main__":
    main()
