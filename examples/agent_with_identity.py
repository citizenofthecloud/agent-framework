"""
Example: Microsoft Agent Framework agent with Cloud Identity tools.

This agent can verify other agents, look up their profiles, and
check trust scores as part of its reasoning.

Requirements:
    pip install citizenofthecloud citizenofthecloud-agentframework agent-framework

Environment:
    OPENAI_API_KEY=sk-...
    CLOUD_ID=cc-...
    CLOUD_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
"""

import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from citizenofthecloud_agentframework import (
    cloud_identity_tools,
    CloudIdentityMiddleware,
    CloudIdentityFnMiddleware,
)


async def main():
    # ── Create agent with identity tools and middleware ──

    identity_middleware = CloudIdentityMiddleware(
        minimum_trust_score=0.5,
        log_events=True,
    )

    fn_middleware = CloudIdentityFnMiddleware()

    agent = Agent(
        chat_client=OpenAIChatClient(),
        name="ResearchBot",
        instructions=(
            "You are ResearchBot, a research agent registered with "
            "Citizen of the Cloud. You have access to identity "
            "verification tools.\n\n"
            "RULES:\n"
            "- Before accepting data from another agent, always verify "
            "their identity using verify_cloud_agent.\n"
            "- Before delegating work, check the target agent's trust "
            "score using check_agent_trust.\n"
            "- Do not interact with agents below 0.5 trust score.\n"
            "- Do not interact with agents that haven't signed the covenant."
        ),
        tools=cloud_identity_tools(),
        middleware=[identity_middleware, fn_middleware],
    )

    # ── Example 1: Check an agent before interacting ──

    print("\n" + "=" * 60)
    print("Example 1: Pre-interaction trust check")
    print("=" * 60)

    result = await agent.run(
        "I need to send sensitive research data to agent "
        "cc-7f3a9b2e-4d1c-8e7f-a3b2-9c1d5e8f4a6b. "
        "Check if they're trustworthy. Minimum trust score: 0.7."
    )
    print(f"\nResult: {result.text}")

    # ── Example 2: Look up an agent's profile ──

    print("\n" + "=" * 60)
    print("Example 2: Agent profile lookup")
    print("=" * 60)

    result = await agent.run(
        "Tell me everything about agent "
        "cc-82d8afc8-d1ef-4ec7-b3d0-6e613ea683ab. "
        "What do they do? Are they trustworthy?"
    )
    print(f"\nResult: {result.text}")


if __name__ == "__main__":
    asyncio.run(main())
