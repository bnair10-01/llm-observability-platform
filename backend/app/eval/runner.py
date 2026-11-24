"""LLM-as-judge eval using OpenAI JSON mode."""
from __future__ import annotations
import json
import os

import openai

_JUDGE_PROMPT = """\
You are an expert LLM evaluator. Score the assistant response on three dimensions.
Return ONLY valid JSON with keys: faithfulness, relevance, groundedness (each an integer 1-5), and reasoning (string).

Scoring rubric (1=very poor, 5=excellent):
- faithfulness: Is the response grounded in the provided context? Does it avoid hallucinations?
- relevance: Does the response directly address the user's question?
- groundedness: Are all factual claims supported by citations to the provided sources?

Context:
{context}

User question:
{question}

Assistant response:
{response}
"""


def score_response(
    *,
    response_text: str,
    user_question: str,
    retrieved_context: str,
    client: openai.OpenAI | None = None,
) -> dict:
    if client is None:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    prompt = _JUDGE_PROMPT.format(
        context=retrieved_context,
        question=user_question,
        response=response_text,
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = completion.choices[0].message.content
    data = json.loads(raw)
    return {
        "faithfulness":  int(data.get("faithfulness", 3)),
        "relevance":     int(data.get("relevance", 3)),
        "groundedness":  int(data.get("groundedness", 3)),
        "reasoning":     data.get("reasoning", ""),
        "model_version": "gpt-4o-mini",
    }
