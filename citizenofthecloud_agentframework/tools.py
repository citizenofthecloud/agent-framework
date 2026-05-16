"""
Function tools for Citizen of the Cloud identity verification.

Microsoft Agent Framework uses plain Python functions with type
annotations as tools. These functions are passed directly to
Agent(tools=[...]) and called automatically by the agent.

Full 17 agent-callable tools — see __init__.py for the structural
primitives (middleware / route guard / observability) that complete
the 20-item framework target.
"""

from typing import Annotated, Optional, List, Callable
from pydantic import Field

from citizenofthecloud import (
    verify_agent,
    verify_request,
    generate_key_pair,
    cloud_fetch,
    request_challenge,
    submit_challenge_response,
    lookup_agent,
    list_directory,
    get_governance_feed,
    register_agent,
    CloudIdentity,
)

# Canonical host is www. The bare apex 307-redirects here, and HTTP
# clients strip the Authorization header on cross-host redirects — so
# callers using the bare apex silently fail register_agent with a 401.
REGISTRY_URL = "https://www.citizenofthecloud.com"


def _fmt_agent(agent: dict) -> str:
    caps = ", ".join(agent.get("capabilities") or []) or "None listed"
    return (
        f"Agent: {agent.get('name', 'Unknown')}\n"
        f"Cloud ID: {agent.get('cloud_id', 'Unknown')}\n"
        f"Purpose: {agent.get('declared_purpose', 'Not declared')}\n"
        f"Autonomy: {agent.get('autonomy_level', 'Unknown')}\n"
        f"Trust Score: {agent.get('trust_score', 'N/A')}\n"
        f"Capabilities: {caps}\n"
        f"Covenant Signed: {agent.get('covenant_signed', False)}\n"
        f"Status: {agent.get('status', 'Unknown')}"
    )


# 1. lookup-agent
def lookup_cloud_agent(
    cloud_id: Annotated[str, Field(description="The Cloud ID of the agent to look up")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """Look up an AI agent's public profile in the Citizen of the Cloud registry."""
    agent = lookup_agent(registry_url, cloud_id)
    if not agent:
        return f"Agent not found or inactive: {cloud_id}"
    return _fmt_agent(agent)


# 2. get-server-identity
def get_server_identity(
    cloud_id: Annotated[str, Field(description="This agent's Cloud ID")],
    private_key: Annotated[str, Field(description="This agent's PEM-encoded Ed25519 private key")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """Fetch this agent's own passport from the registry."""
    identity = CloudIdentity(cloud_id=cloud_id, private_key=private_key, registry_url=registry_url)
    passport = identity.get_passport()
    if not passport:
        return f"No passport found for {cloud_id}"
    return _fmt_agent(passport)


# 3. list-directory
def list_cloud_directory(
    limit: Annotated[int, Field(description="Max entries to summarize", default=20)] = 20,
    registry_url: str = REGISTRY_URL,
) -> str:
    """List public entries in the Citizen of the Cloud agent directory."""
    agents = list_directory(registry_url)
    if not agents:
        return "Directory is empty."
    lines = [f"{len(agents)} agent(s) (showing up to {limit}):"]
    for a in agents[:limit]:
        lines.append(
            f"  - {a.get('name','?')} ({a.get('cloud_id','?')}) "
            f"trust={a.get('trust_score','?')} status={a.get('status','?')}"
        )
    return "\n".join(lines)


# 4. governance-feed
def governance_feed(
    limit: Annotated[int, Field(description="Max events to summarize", default=20)] = 20,
    registry_url: str = REGISTRY_URL,
) -> str:
    """Read the Citizen of the Cloud governance activity feed."""
    feed = get_governance_feed(registry_url)
    if not feed:
        return "Governance feed is empty."
    lines = [f"{len(feed)} event(s) (showing up to {limit}):"]
    for ev in feed[:limit]:
        lines.append(
            f"  - {ev.get('event_type', ev.get('type','?'))} "
            f"at {ev.get('created_at', ev.get('timestamp','?'))}"
        )
    return "\n".join(lines)


# 5. verify-agent
def verify_cloud_agent(
    cloud_id: Annotated[str, Field(description="X-Cloud-ID header")],
    timestamp: Annotated[str, Field(description="X-Cloud-Timestamp header")],
    signature: Annotated[str, Field(description="X-Cloud-Signature header")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """Verify an AI agent's identity using the Citizen of the Cloud protocol."""
    headers = {"X-Cloud-ID": cloud_id, "X-Cloud-Timestamp": timestamp, "X-Cloud-Signature": signature}
    result = verify_agent(headers, registry_url=registry_url)
    if result.get("verified"):
        return f"VERIFIED — {_fmt_agent(result['agent'])}"
    return f"NOT VERIFIED — Reason: {result.get('reason')}"


# 6. verify-request
def verify_cloud_request(
    cloud_id: Annotated[str, Field(description="X-Cloud-ID header")],
    timestamp: Annotated[str, Field(description="X-Cloud-Timestamp header")],
    signature: Annotated[str, Field(description="X-Cloud-Signature header")],
    url: Annotated[str, Field(description="The exact request URL the signature is bound to")],
    method: Annotated[str, Field(description="HTTP method")],
    body: Annotated[str, Field(description="Request body", default="")] = "",
    registry_url: str = REGISTRY_URL,
) -> str:
    """Verify a request-bound Cloud Identity signature (covers URL, method, body)."""
    from citizenofthecloud import TrustPolicy
    headers = {
        "X-Cloud-ID": cloud_id,
        "X-Cloud-Timestamp": timestamp,
        "X-Cloud-Signature": signature,
        "X-Cloud-Request-Bound": "true",
    }
    policy = TrustPolicy(registry_url=registry_url)
    result = verify_request(headers, url=url, method=method, body=body, policy=policy)
    if result.get("verified"):
        return f"VERIFIED (request-bound) — {_fmt_agent(result['agent'])}"
    return f"NOT VERIFIED — Reason: {result.get('reason')}"


# 7. request-challenge
def request_cloud_challenge(
    cloud_id: Annotated[str, Field(description="The Cloud ID requesting a challenge")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """Request a verification challenge nonce for a Cloud ID."""
    ch = request_challenge(registry_url, cloud_id)
    return f"nonce={ch['nonce']} expires_in={ch.get('expires_in','?')}s"


# 8. respond-to-challenge
def respond_to_cloud_challenge(
    cloud_id: Annotated[str, Field(description="The Cloud ID being verified")],
    nonce: Annotated[str, Field(description="The hex nonce from request_cloud_challenge")],
    signature: Annotated[str, Field(description="Base64 signature over the UTF-8 nonce bytes")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """Submit a signed challenge response."""
    result = submit_challenge_response(registry_url, cloud_id, nonce, signature)
    if result.get("verified"):
        return f"VERIFIED via challenge — {_fmt_agent(result['agent'])}"
    return f"NOT VERIFIED — Reason: {result.get('error') or result.get('reason')}"


# 9. sign-challenge
def sign_cloud_challenge(
    nonce: Annotated[str, Field(description="The hex nonce from request_cloud_challenge")],
    private_key: Annotated[str, Field(description="PEM-encoded Ed25519 private key")],
) -> str:
    """Sign a challenge nonce locally with the agent's Ed25519 private key."""
    import base64
    from cryptography.hazmat.primitives import serialization
    key = serialization.load_pem_private_key(private_key.encode("utf-8"), password=None)
    sig = key.sign(nonce.encode("utf-8"))
    return base64.b64encode(sig).decode("ascii")


# 10. prove-identity
def prove_cloud_identity(
    cloud_id: Annotated[str, Field(description="The agent's Cloud ID")],
    private_key: Annotated[str, Field(description="PEM-encoded Ed25519 private key")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """Prove this agent's identity via the full challenge/sign/respond loop."""
    identity = CloudIdentity(cloud_id=cloud_id, private_key=private_key, registry_url=registry_url)
    result = identity.prove_identity()
    if result.get("verified"):
        return f"VERIFIED — {_fmt_agent(result['agent'])}"
    return f"NOT VERIFIED — Reason: {result.get('error') or result.get('reason')}"


# 11. sign-headers
def sign_cloud_headers(
    cloud_id: Annotated[str, Field(description="The agent's Cloud ID")],
    private_key: Annotated[str, Field(description="PEM-encoded Ed25519 private key")],
) -> str:
    """Produce signed X-Cloud-* headers for an outbound request."""
    identity = CloudIdentity(cloud_id=cloud_id, private_key=private_key)
    h = identity.sign()
    return (
        f"X-Cloud-ID: {h['X-Cloud-ID']}\n"
        f"X-Cloud-Timestamp: {h['X-Cloud-Timestamp']}\n"
        f"X-Cloud-Signature: {h['X-Cloud-Signature']}"
    )


# 12. sign-request
def sign_cloud_request(
    cloud_id: Annotated[str, Field(description="The agent's Cloud ID")],
    private_key: Annotated[str, Field(description="PEM-encoded Ed25519 private key")],
    url: Annotated[str, Field(description="Target request URL")],
    method: Annotated[str, Field(description="HTTP method")],
    body: Annotated[str, Field(description="Request body", default="")] = "",
) -> str:
    """Produce request-bound X-Cloud-* headers (covers URL, method, body hash)."""
    identity = CloudIdentity(cloud_id=cloud_id, private_key=private_key)
    h = identity.sign_request(url, method, body)
    return (
        f"X-Cloud-ID: {h['X-Cloud-ID']}\n"
        f"X-Cloud-Timestamp: {h['X-Cloud-Timestamp']}\n"
        f"X-Cloud-Signature: {h['X-Cloud-Signature']}\n"
        f"X-Cloud-Request-Bound: true"
    )


# 13. cloud-fetch
def cloud_fetch_tool(
    cloud_id: Annotated[str, Field(description="The caller's Cloud ID")],
    private_key: Annotated[str, Field(description="PEM-encoded Ed25519 private key")],
    url: Annotated[str, Field(description="Target URL")],
    method: Annotated[str, Field(description="HTTP method", default="GET")] = "GET",
    body: Annotated[Optional[str], Field(description="Request body", default=None)] = None,
) -> str:
    """Make an HTTP request with automatic Cloud Identity signing."""
    identity = CloudIdentity(cloud_id=cloud_id, private_key=private_key)
    resp = cloud_fetch(identity, url, method=method, body=body)
    body_str = resp.get("body")
    if isinstance(body_str, (dict, list)):
        import json
        body_str = json.dumps(body_str)
    return f"status={resp['status']}\nbody={body_str}"


# 14. generate-keypair
def generate_cloud_keypair() -> str:
    """Generate a fresh Ed25519 keypair locally."""
    keys = generate_key_pair()
    return (
        f"public_key:\n{keys['public_key']}\n"
        f"private_key (STORE SECURELY):\n{keys['private_key']}"
    )


# 15. register-agent
def register_cloud_agent(
    sdk_token: str,
    name: str,
    declared_purpose: str,
    autonomy_level: str = "tool",
    capabilities: Optional[list] = None,
    operational_domain: Optional[str] = None,
    registry_url: str = REGISTRY_URL,
) -> dict:
    """Register a new Cloud Identity agent (SDK-token auth). Bootstrap helper."""
    return register_agent(
        sdk_token=sdk_token,
        name=name,
        declared_purpose=declared_purpose,
        autonomy_level=autonomy_level,
        capabilities=capabilities,
        operational_domain=operational_domain,
        registry_url=registry_url,
    )


# 16. report-agent
def report_cloud_agent(
    sdk_token: Annotated[str, Field(description="cotc_sdk_* with 'manage' scope, or user JWT")],
    cloud_id: Annotated[str, Field(description="Cloud ID of the agent being reported")],
    report_type: Annotated[str, Field(description="impersonation | malicious_behavior | spam | covenant_violation | inaccurate_registration")],
    evidence: Annotated[str, Field(description="Evidence text (20–2000 chars)")],
    registry_url: str = REGISTRY_URL,
) -> str:
    """File a governance report against another agent."""
    import json
    import urllib.request
    import urllib.error
    body = json.dumps({"cloud_id": cloud_id, "report_type": report_type, "evidence": evidence}).encode("utf-8")
    req = urllib.request.Request(
        f"{registry_url.rstrip('/')}/api/report",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {sdk_token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return f"Report filed: id={data.get('report_id') or data.get('id') or 'ok'}"
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            return f"Report error ({e.code}): {err.get('error', str(e))}"
        except Exception:
            return f"Report error: HTTP {e.code}"
    except urllib.error.URLError as e:
        return f"Report error: registry unreachable: {e}"


# 17. check-trust
def check_agent_trust(
    cloud_id: Annotated[str, Field(description="The Cloud ID of the agent to check")],
    minimum_trust_score: Annotated[float, Field(description="Minimum trust score required", default=0.5)] = 0.5,
    registry_url: str = REGISTRY_URL,
) -> str:
    """Check if an AI agent meets a minimum trust score threshold."""
    agent = lookup_agent(registry_url, cloud_id)
    if not agent:
        return f"FAIL — Agent not found or inactive: {cloud_id}"
    score = agent.get("trust_score", 0) or 0
    name = agent.get("name", "Unknown")
    if score >= minimum_trust_score:
        return f"PASS — {name} trust={score} (threshold={minimum_trust_score})"
    return f"FAIL — {name} trust={score} (below threshold={minimum_trust_score})"


# Convenience — all 17 agent-callable function tools
def cloud_identity_tools() -> List[Callable]:
    """Return all 17 agent-callable function tools in one list."""
    return [
        lookup_cloud_agent,
        get_server_identity,
        list_cloud_directory,
        governance_feed,
        verify_cloud_agent,
        verify_cloud_request,
        request_cloud_challenge,
        respond_to_cloud_challenge,
        sign_cloud_challenge,
        prove_cloud_identity,
        sign_cloud_headers,
        sign_cloud_request,
        cloud_fetch_tool,
        generate_cloud_keypair,
        register_cloud_agent,
        report_cloud_agent,
        check_agent_trust,
    ]
