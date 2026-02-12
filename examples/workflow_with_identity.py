"""
Example: Multi-agent workflow with Cloud Identity verification.

Demonstrates a graph-based workflow where:
1. An identity verification node gates the entire workflow
2. A researcher agent gathers information
3. An analyst agent produces findings
4. Results are returned to the verified requester

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
    cloud_guard_node,
    CloudIdentityHTTPClient,
)


async def run_verified_workflow(request_headers: dict, query: str):
    """
    Execute a multi-agent workflow with identity verification.

    The requesting agent is verified before any work begins.
    """

    # ── Step 1: Verify the requester ──

    print("\n[WORKFLOW] Step 1: Verifying requester...")

    guard = cloud_guard_node(
        headers=request_headers,
        minimum_trust_score=0.5,
        require_covenant=True,
    )

    if not guard["verified"]:
        print(f"[WORKFLOW] REJECTED: {guard['reason']}")
        return {"error": guard["reason"]}

    requester = guard["agent"]
    print(f"[WORKFLOW] VERIFIED: {requester['name']} (trust: {requester['trust_score']})")

    # ── Step 2: Research agent gathers information ──

    print("\n[WORKFLOW] Step 2: Research agent gathering information...")

    researcher = Agent(
        chat_client=OpenAIChatClient(),
        name="Researcher",
        instructions=(
            "You are a research agent. Gather comprehensive information "
            "on the given topic. Be thorough and cite your reasoning."
        ),
        tools=cloud_identity_tools(),
        middleware=[CloudIdentityFnMiddleware()],
    )

    research_result = await researcher.run(
        f"Research the following topic for verified agent "
        f"'{requester['name']}': {query}"
    )

    print(f"[WORKFLOW] Research complete: {len(research_result.text)} chars")

    # ── Step 3: Analysis agent produces findings ──

    print("\n[WORKFLOW] Step 3: Analysis agent producing findings...")

    analyst = Agent(
        chat_client=OpenAIChatClient(),
        name="Analyst",
        instructions=(
            "You are an analysis agent. Take research findings and "
            "produce a concise, actionable summary with key insights."
        ),
    )

    analysis_result = await analyst.run(
        f"Analyze these research findings and produce key insights:\n\n"
        f"{research_result.text}"
    )

    print(f"[WORKFLOW] Analysis complete: {len(analysis_result.text)} chars")

    # ── Step 4: Return results ──

    return {
        "status": "complete",
        "query": query,
        "requester": requester["name"],
        "requester_trust": requester["trust_score"],
        "research": research_result.text,
        "analysis": analysis_result.text,
    }


async def main():
    """
    Simulate a verified workflow.

    In production, request_headers would come from an actual HTTP
    request from another agent.
    """

    # Simulate incoming signed headers (in production these come
    # from the requesting agent's SDK)
    mock_headers = {
        "X-Cloud-ID": "cc-7f3a9b2e-4d1c-8e7f-a3b2-9c1d5e8f4a6b",
        "X-Cloud-Timestamp": "2026-02-12T08:00:00Z",
        "X-Cloud-Signature": "mock-signature-for-demo",
    }

    result = await run_verified_workflow(
        request_headers=mock_headers,
        query="Current trends in AI agent identity and trust",
    )

    print("\n" + "=" * 60)
    print("WORKFLOW RESULT")
    print("=" * 60)

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Requester: {result['requester']} (trust: {result['requester_trust']})")
        print(f"\nAnalysis:\n{result['analysis']}")


if __name__ == "__main__":
    asyncio.run(main())
