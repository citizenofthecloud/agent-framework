"""
Citizen of the Cloud — Microsoft Agent Framework Integration

Adds cryptographic identity and trust verification to Microsoft Agent
Framework agents and workflows. Wraps the citizenofthecloud Python SDK
into Agent Framework-compatible tools, middleware, and workflow nodes.

Tools (function tools):
    verify_cloud_agent      — Verify another agent's identity and trust score
    lookup_cloud_agent      — Look up an agent's profile by Cloud ID
    check_agent_trust       — Quick trust score check with pass/fail threshold

Middleware:
    CloudIdentityMiddleware     — Agent middleware for signing/verification
    CloudIdentityFnMiddleware   — Function middleware for identity-aware tool calls

Workflow:
    cloud_guard_node            — Workflow node for pre-execution verification

Usage:
    from citizenofthecloud_agentframework import (
        verify_cloud_agent,
        lookup_cloud_agent,
        check_agent_trust,
        CloudIdentityMiddleware,
        CloudIdentityFnMiddleware,
        cloud_guard_node,
    )
"""

from citizenofthecloud_agentframework.tools import (
    verify_cloud_agent,
    lookup_cloud_agent,
    check_agent_trust,
    cloud_identity_tools,
)
from citizenofthecloud_agentframework.middleware import (
    CloudIdentityMiddleware,
    CloudIdentityFnMiddleware,
)
from citizenofthecloud_agentframework.guard import cloud_guard_node
from citizenofthecloud_agentframework.http import CloudIdentityHTTPClient

__all__ = [
    "verify_cloud_agent",
    "lookup_cloud_agent",
    "check_agent_trust",
    "cloud_identity_tools",
    "CloudIdentityMiddleware",
    "CloudIdentityFnMiddleware",
    "cloud_guard_node",
    "CloudIdentityHTTPClient",
]

__version__ = "0.1.0"
