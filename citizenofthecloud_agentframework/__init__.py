"""
Citizen of the Cloud — Microsoft Agent Framework Integration

Cryptographic identity and trust verification for Microsoft Agent Framework
agents and workflows.

Tool surface — 20 items (17 agent-callable + 3 structural primitives):

Agent-callable function tools (17):
    lookup_cloud_agent, get_server_identity, list_cloud_directory,
    governance_feed, verify_cloud_agent, verify_cloud_request,
    request_cloud_challenge, respond_to_cloud_challenge, sign_cloud_challenge,
    prove_cloud_identity, sign_cloud_headers, sign_cloud_request,
    cloud_fetch_tool, generate_cloud_keypair, register_cloud_agent,
    report_cloud_agent, check_agent_trust

Structural primitives (3):
    18. CloudIdentityRouteGuard / cloud_guard_route — FastAPI route-guard middleware
        (with CloudIdentityMiddleware as the in-process AgentMiddleware variant)
    19. cloud_guard_node — workflow gate node (framework-native)
    20. CloudIdentityFnMiddleware — observability via FunctionMiddleware
"""

from citizenofthecloud_agentframework.tools import (
    # Agent-callable tools (17)
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
    cloud_identity_tools,
)
from citizenofthecloud_agentframework.middleware import (
    CloudIdentityMiddleware,
    CloudIdentityFnMiddleware,
)
from citizenofthecloud_agentframework.guard import cloud_guard_node
from citizenofthecloud_agentframework.http import CloudIdentityHTTPClient
from citizenofthecloud_agentframework.http_middleware import (
    CloudIdentityRouteGuard,
    cloud_guard_route,
)

__all__ = [
    # Agent-callable tools (17)
    "lookup_cloud_agent",
    "get_server_identity",
    "list_cloud_directory",
    "governance_feed",
    "verify_cloud_agent",
    "verify_cloud_request",
    "request_cloud_challenge",
    "respond_to_cloud_challenge",
    "sign_cloud_challenge",
    "prove_cloud_identity",
    "sign_cloud_headers",
    "sign_cloud_request",
    "cloud_fetch_tool",
    "generate_cloud_keypair",
    "register_cloud_agent",
    "report_cloud_agent",
    "check_agent_trust",
    # Structural primitives (3)
    "CloudIdentityRouteGuard",     # 18 — http-middleware
    "cloud_guard_route",           # 18 — http-middleware (decorator form)
    "cloud_guard_node",            # 19 — framework-native gate
    "CloudIdentityFnMiddleware",   # 20 — observability (FunctionMiddleware)
    # Helpers
    "cloud_identity_tools",
    "CloudIdentityMiddleware",     # in-process AgentMiddleware variant
    "CloudIdentityHTTPClient",
]

__version__ = "0.2.0"
