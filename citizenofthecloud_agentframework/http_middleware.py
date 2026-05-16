"""
FastAPI route-guard middleware for serving Microsoft Agent Framework
agents behind Cloud Identity verification.

Companion to:
- CloudIdentityMiddleware — the framework's AgentMiddleware (in-process,
  intercepts agent runs)
- CloudIdentityFnMiddleware — the framework's FunctionMiddleware (in-process,
  intercepts tool calls)

This http_middleware module adds the structural item #18: a FastAPI
BaseHTTPMiddleware that verifies inbound X-Cloud-* headers before a
request reaches an agent.run() endpoint.
"""

from typing import Optional

try:
    from citizenofthecloud.fastapi import CloudGuard as _CloudGuard
    from citizenofthecloud.fastapi import cloud_guard_decorator as _decorator
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "FastAPI extras required. Install with: "
        "pip install 'citizenofthecloud[fastapi]'"
    ) from e

from citizenofthecloud import TrustPolicy


class CloudIdentityRouteGuard(_CloudGuard):
    """
    FastAPI route-guard middleware for Microsoft Agent Framework endpoints.

    Usage:
        from fastapi import FastAPI
        from citizenofthecloud_agentframework import CloudIdentityRouteGuard
        from citizenofthecloud import TrustPolicy

        app = FastAPI()
        app.add_middleware(
            CloudIdentityRouteGuard,
            policy=TrustPolicy(minimum_trust_score=0.5),
            registry_url="https://www.citizenofthecloud.com",
        )

        @app.post("/agent")
        async def run_agent(request: Request):
            return await agent.run(await request.json())
    """
    pass


def cloud_guard_route(policy: Optional[TrustPolicy] = None, **kwargs):
    """Decorator form for FastAPI routes that serve Agent Framework agents."""
    return _decorator(policy=policy, **kwargs)
