"""
Function tools for Citizen of the Cloud identity verification.

Microsoft Agent Framework uses plain Python functions with type
annotations as tools. These functions are passed directly to
Agent(tools=[...]) and are called automatically by the agent.
"""

from typing import Annotated, List, Callable, Optional
from pydantic import Field

from citizenofthecloud import verify_agent

REGISTRY_URL = "https://citizenofthecloud.com"


# ═══════════════════════════════════════════════════════════
# VERIFY AGENT TOOL
# ═══════════════════════════════════════════════════════════

def verify_cloud_agent(
    cloud_id: Annotated[str, Field(description="The Cloud ID from the X-Cloud-ID header")],
    timestamp: Annotated[str, Field(description="The timestamp from the X-Cloud-Timestamp header")],
    signature: Annotated[str, Field(description="The signature from the X-Cloud-Signature header")],
) -> str:
    """
    Verify an AI agent's identity using the Citizen of the Cloud protocol.

    Use this when you receive a request from another agent and need to
    confirm they are who they claim to be. Requires the three X-Cloud-*
    header values from the incoming request. Returns the agent's name,
    trust score, autonomy level, and verification status.
    """
    headers = {
        "X-Cloud-ID": cloud_id,
        "X-Cloud-Timestamp": timestamp,
        "X-Cloud-Signature": signature,
    }

    try:
        result = verify_agent(headers)
    except Exception as e:
        return f"Verification error: {str(e)}"

    if result["verified"]:
        agent = result["agent"]
        return (
            f"VERIFIED — Agent: {agent['name']}, "
            f"Cloud ID: {agent['cloud_id']}, "
            f"Trust Score: {agent['trust_score']}, "
            f"Autonomy: {agent['autonomy_level']}, "
            f"Covenant Signed: {agent.get('covenant_signed', False)}, "
            f"Status: {agent['status']}"
        )
    else:
        return f"NOT VERIFIED — Reason: {result['reason']}"


# ═══════════════════════════════════════════════════════════
# LOOKUP AGENT TOOL
# ═══════════════════════════════════════════════════════════

def lookup_cloud_agent(
    cloud_id: Annotated[str, Field(description="The Cloud ID of the agent to look up")],
) -> str:
    """
    Look up an AI agent's public profile in the Citizen of the Cloud registry.

    Use this to learn about an agent before deciding whether to interact
    with or delegate work to them. Returns name, purpose, trust score,
    autonomy level, capabilities, and status. This is an informational
    lookup, not a cryptographic verification.
    """
    import requests

    try:
        resp = requests.get(
            f"{REGISTRY_URL}/api/verify",
            params={"cloud_id": cloud_id},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return f"Lookup error: {str(e)}"

    if not data.get("verified"):
        return f"Agent not found or inactive: {cloud_id}"

    agent = data.get("agent", {})
    capabilities = ", ".join(agent.get("capabilities", []))

    return (
        f"Agent: {agent.get('name', 'Unknown')}\n"
        f"Cloud ID: {agent.get('cloud_id', cloud_id)}\n"
        f"Purpose: {agent.get('declared_purpose', 'Not declared')}\n"
        f"Autonomy Level: {agent.get('autonomy_level', 'Unknown')}\n"
        f"Trust Score: {agent.get('trust_score', 'N/A')}\n"
        f"Capabilities: {capabilities or 'None listed'}\n"
        f"Covenant Signed: {agent.get('covenant_signed', False)}\n"
        f"Status: {agent.get('status', 'Unknown')}\n"
        f"Registered: {agent.get('registered_at', 'Unknown')}"
    )


# ═══════════════════════════════════════════════════════════
# CHECK TRUST TOOL
# ═══════════════════════════════════════════════════════════

def check_agent_trust(
    cloud_id: Annotated[str, Field(description="The Cloud ID of the agent to check")],
    minimum_trust_score: Annotated[
        float, Field(description="Minimum trust score required (0.0 to 1.0)", default=0.5)
    ] = 0.5,
) -> str:
    """
    Check if an AI agent meets a minimum trust score threshold.

    Use this for a quick pass/fail decision before delegating tasks
    or sharing data with another agent. Provide the Cloud ID and the
    minimum trust score required (default 0.5). Returns PASS or FAIL
    with the agent's current trust score.
    """
    import requests

    try:
        resp = requests.get(
            f"{REGISTRY_URL}/api/verify",
            params={"cloud_id": cloud_id},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return f"FAIL — Could not reach registry: {str(e)}"

    if not data.get("verified"):
        return f"FAIL — Agent not found or inactive: {cloud_id}"

    agent = data.get("agent", {})
    trust_score = agent.get("trust_score", 0)
    name = agent.get("name", "Unknown")

    if trust_score >= minimum_trust_score:
        return (
            f"PASS — {name} has trust score {trust_score} "
            f"(threshold: {minimum_trust_score})"
        )
    else:
        return (
            f"FAIL — {name} has trust score {trust_score} "
            f"(below threshold: {minimum_trust_score})"
        )


# ═══════════════════════════════════════════════════════════
# CONVENIENCE: GET ALL TOOLS
# ═══════════════════════════════════════════════════════════

def cloud_identity_tools() -> List[Callable]:
    """
    Return all three Cloud Identity tools as a list.

    Pass directly to Agent(tools=...) to give an agent full
    identity verification capabilities.

    Usage:
        from agent_framework.openai import OpenAIChatClient
        from agent_framework import Agent
        from citizenofthecloud_agentframework import cloud_identity_tools

        agent = Agent(
            chat_client=OpenAIChatClient(),
            instructions="Verify agents before interacting.",
            tools=cloud_identity_tools(),
        )
    """
    return [verify_cloud_agent, lookup_cloud_agent, check_agent_trust]


# ═══════════════════════════════════════════════════════════
# REGISTER AGENT (SDK token auth)
# ═══════════════════════════════════════════════════════════

def register_cloud_agent(
    sdk_token: str,
    name: str,
    declared_purpose: str,
    autonomy_level: str = "tool",
    capabilities: Optional[list] = None,
    operational_domain: Optional[str] = None,
    registry_url: str = REGISTRY_URL,
) -> dict:
    """
    Register a new Cloud Identity agent in a single call.

    Generates a fresh Ed25519 keypair locally, posts the public key plus
    metadata to the registry under the supplied SDK token, and returns a
    dict with cloud_id, public_key, and private_key. The private key never
    leaves this process — store it securely. The returned cloud_id +
    private_key are the inputs to CloudIdentity for signing subsequent
    requests.

    This is NOT a function-tool intended for an agent to call mid-task —
    it's an operator-facing helper for bootstrap / setup scripts.

    Args:
        sdk_token: A cotc_sdk_* token from citizenofthecloud.com/account
        name: Human-readable name for the agent
        declared_purpose: What the agent does (<= 500 chars)
        autonomy_level: 'tool' | 'assistant' | 'agent' | 'self-directing'
        capabilities: Optional list of capability strings
        operational_domain: Optional domain string
        registry_url: Override the registry URL

    Returns:
        dict with keys: cloud_id, public_key, private_key, name,
        declared_purpose, autonomy_level, passport.
    """
    from citizenofthecloud import register_agent
    return register_agent(
        sdk_token=sdk_token,
        name=name,
        declared_purpose=declared_purpose,
        autonomy_level=autonomy_level,
        capabilities=capabilities,
        operational_domain=operational_domain,
        registry_url=registry_url,
    )
