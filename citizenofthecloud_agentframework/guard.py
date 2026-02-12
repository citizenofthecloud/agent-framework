"""
Workflow guard node for Citizen of the Cloud identity verification.

Provides a verification node that can be used in Microsoft Agent
Framework graph-based workflows to gate execution based on agent
identity and trust.
"""

import os
from typing import Optional, Dict, Any, Callable
from citizenofthecloud import verify_agent


def cloud_guard_node(
    headers: Dict[str, str],
    minimum_trust_score: float = 0.0,
    require_covenant: bool = True,
    allowed_autonomy_levels: Optional[list] = None,
    blocked_agents: Optional[list] = None,
    on_reject: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Verification gate for Agent Framework workflows.

    Use this as a step in a workflow to verify the requesting agent
    before allowing downstream agents or functions to execute.

    In a graph-based workflow:
        from agent_framework import Workflow

        @workflow.node
        async def verify_identity(state):
            guard = cloud_guard_node(
                headers=state["request_headers"],
                minimum_trust_score=0.5,
            )
            if not guard["verified"]:
                return {"error": guard["reason"], "proceed": False}
            return {
                "verified_agent": guard["agent"],
                "proceed": True,
            }

    As a pre-check before agent.run():
        guard = cloud_guard_node(
            headers=request.headers,
            minimum_trust_score=0.5,
        )
        if not guard["verified"]:
            return {"error": guard["reason"]}

        result = await agent.run(
            f"Process request from {guard['agent']['name']}:  {query}"
        )

    In a FastAPI endpoint:
        @app.post("/api/analyze")
        async def analyze(request: Request):
            guard = cloud_guard_node(
                headers=dict(request.headers),
                minimum_trust_score=0.5,
                require_covenant=True,
            )
            if not guard["verified"]:
                return {"error": guard["reason"]}, 401

            result = await agent.run(query)
            return {"result": result.text}

    Args:
        headers: Incoming request headers with X-Cloud-* values
        minimum_trust_score: Minimum trust score to allow (default 0.0)
        require_covenant: Require covenant signed (default True)
        allowed_autonomy_levels: Restrict to specific autonomy levels
        blocked_agents: List of Cloud IDs to block
        on_reject: Optional callback on rejection

    Returns:
        Dict with 'verified' (bool), 'agent' (if verified), 'reason' (if rejected)
    """
    policy = {}

    if minimum_trust_score > 0:
        policy["minimum_trust_score"] = minimum_trust_score
    if require_covenant:
        policy["require_covenant"] = require_covenant
    if allowed_autonomy_levels:
        policy["allowed_autonomy_levels"] = allowed_autonomy_levels
    if blocked_agents:
        policy["blocked_agents"] = blocked_agents

    try:
        result = verify_agent(headers, policy=policy if policy else None)
    except Exception as e:
        result = {"verified": False, "reason": f"verification_error: {str(e)}"}

    if not result["verified"] and on_reject:
        on_reject(result["reason"])

    return result
