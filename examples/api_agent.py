"""
Example: Agent Framework agent exposed via FastAPI with identity verification.

Other agents can call this endpoint, but only verified agents with
sufficient trust scores are allowed to trigger execution.

Requirements:
    pip install citizenofthecloud citizenofthecloud-agentframework agent-framework fastapi uvicorn

Environment:
    OPENAI_API_KEY=sk-...
    CLOUD_ID=cc-...
    CLOUD_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."

Run:
    uvicorn examples.api_agent:app --port 4000
"""

import os
import asyncio
from fastapi import FastAPI, Request
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from citizenofthecloud_agentframework import (
    cloud_identity_tools,
    CloudIdentityMiddleware,
    cloud_guard_node,
)


# ── Build the agent ──

agent = Agent(
    chat_client=OpenAIChatClient(),
    name="AnalysisBot",
    instructions=(
        "You are AnalysisBot, a data analysis agent. You analyze topics "
        "and provide insights. When you know who requested the analysis "
        "and their trust level, incorporate that into your response."
    ),
    tools=cloud_identity_tools(),
    middleware=[
        CloudIdentityMiddleware(log_events=True),
    ],
)


# ── API ──

app = FastAPI(title="AnalysisBot — Agent Framework")


@app.post("/api/analyze")
async def analyze(request: Request):
    """
    Analyze a topic. Requires Cloud Identity headers.

    The requesting agent must:
    - Have valid X-Cloud-* headers
    - Have a trust score >= 0.5
    - Have signed the covenant
    """

    # Step 1: Verify the requesting agent
    guard = cloud_guard_node(
        headers=dict(request.headers),
        minimum_trust_score=0.5,
        require_covenant=True,
    )

    if not guard["verified"]:
        return {
            "error": "Cloud Identity verification failed",
            "reason": guard["reason"],
        }

    # Step 2: Run the agent with verified context
    body = await request.json()
    agent_info = guard["agent"]

    result = await agent.run(
        f"Analyze the following topic for verified agent "
        f"'{agent_info['name']}' (trust score: {agent_info['trust_score']}): "
        f"{body.get('query', 'general analysis')}"
    )

    # Step 3: Return result
    return {
        "status": "complete",
        "analysis": result.text,
        "analyzed_by": os.environ.get("CLOUD_ID"),
        "requested_by": agent_info["name"],
        "requester_trust": agent_info["trust_score"],
    }


@app.get("/health")
async def health():
    return {
        "status": "online",
        "cloud_id": os.environ.get("CLOUD_ID"),
        "minimum_trust_score": 0.5,
    }
