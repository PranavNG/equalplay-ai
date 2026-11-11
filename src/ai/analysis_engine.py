
import json
from functools import lru_cache

from src.ai.azure_client import generate_response
from src.ai.context_builder import build_match_context


PROMPTS = {
    "recap": """
You are a professional football commentator.

Write an engaging match recap of approximately 150-200 words.

Requirements:
- Describe the final score and goalscorers.
- Explain important turning points chronologically.
- Use match statistics to support the narrative.
- Write naturally, like a football journalist.
- Do not invent events, assists, injuries or tactical changes.
- Treat the winning-goal label as a verified match fact.
""",

    "tactical": """
You are a professional football performance analyst.

Write approximately 150-200 words analysing the match.

Focus on:
- Possession and passing accuracy.
- Shot volume and shot accuracy.
- Expected goals (xG) and chance quality.
- How statistical differences relate to the result.

Requirements:
- Distinguish chance creation from finishing efficiency.
- Do not infer formations, pressing or build-up patterns.
- Do not claim to have watched the match.
- Explain what the statistics suggest, not what they prove.
- Use accessible, natural football language.
"""
}


@lru_cache(maxsize=32)
def generate_analysis(mode="recap"):
    if mode not in PROMPTS:
        raise ValueError(f"Unsupported analysis mode: {mode}")

    context = build_match_context()

    prompt = f"""
{PROMPTS[mode]}

General requirements:
- Use only the provided synthetic match data.
- Do not mention internal match IDs.
- Identify the match as fictional once, naturally.
- Do not invent unsupported facts.
- Do not describe scoring above xG as proof of above-average
  finishing ability.

Match context:
{json.dumps(context, indent=2)}
"""

    return generate_response(prompt)


if __name__ == "__main__":
    for mode in PROMPTS:
        print(f"\n{'=' * 20} {mode.upper()} {'=' * 20}")
        print(generate_analysis(mode))
