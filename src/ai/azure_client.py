
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")

if not all([endpoint, deployment, api_key]):
    raise RuntimeError("Azure OpenAI environment variables are missing")

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)


def generate_response(prompt: str) -> str:
    response = client.responses.create(
        model=deployment,
        input=prompt
    )

    return response.output_text
