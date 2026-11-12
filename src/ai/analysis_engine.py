
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
""",

    "key_moments": """
You are a professional football match analyst.

Explain the key moments that shaped this synthetic match.

Write approximately 150-200 words.

Focus on:
- Each goal and its impact on the score.
- Equalisers and changes in the lead.
- Why the match-winning goal was decisive.
- How the sequence of goals shaped the result.

Requirements:
- Explain events in chronological order.
- Use the verified key_moments data.
- Include the minute, goalscorer and score where relevant.
- Distinguish confirmed facts from interpretations.
- Do not invent assists, tactical changes, injuries or reactions.
- Do not claim momentum shifted without supporting evidence.
- Explain the importance of each moment naturally.
""",

    "simplified": """
You explain football matches to people who may be new to football.

Write a simple, accessible match explanation of 100-150 words.

Requirements:
- Use short, clear sentences and everyday language.
- Explain who won and the final score.
- Describe the most important goals in chronological order.
- Explain why the winning goal mattered.
- Avoid technical football jargon.
- If mentioning xG, explain it as the quality of scoring chances.
- Avoid unnecessary statistics and complicated percentages.
- Do not invent events or unsupported explanations.
- Write naturally without headings or bullet points.
- Make the explanation suitable for audio narration.
""",

    "team_focus": """
You are a football analyst providing a team-focused match review.

Write approximately 150 words.

Requirements:
- Focus primarily on the selected team's performance.
- Explain the team's goals and important match moments.
- Compare relevant statistics with the opposition.
- Discuss strengths and weaknesses supported by the data.
- Keep the analysis balanced, even when addressing a fan.
- Do not invent tactics, formations or player actions.
- Avoid unsupported conclusions.
- Write naturally without headings or bullet points.
"""
}


@lru_cache(maxsize=32)
def generate_analysis(mode="recap", team=None):
    if mode not in PROMPTS:
        raise ValueError(f"Unsupported analysis mode: {mode}")

    if mode == "team_focus" and team not in ("HOME", "AWAY"):
        raise ValueError("Team focus requires HOME or AWAY")
    if mode != "team_focus" and team is not None:
        raise ValueError("Team parameter is only supported for team_focus")

    context = build_match_context()

    selected_team = (
        context["teams"][team]
        if mode == "team_focus"
        else None
    )

    prompt = f"""
{PROMPTS[mode]}

General requirements:
- Use only the provided synthetic match data.
- Do not mention internal match IDs.
- Identify the match as fictional once, naturally.
- Do not invent unsupported facts.
- Do not describe scoring above xG as proof of above-average
  finishing ability.

Selected team: {selected_team if selected_team else "Not applicable"}

Match context:
{json.dumps(context, indent=2)}
    """

    return generate_response(prompt)
