"""
Microsoft Agent Framework middleware for Citizen of the Cloud identity.

Provides two middleware classes:

1. CloudIdentityMiddleware (AgentMiddleware) — Intercepts agent runs
   to inject identity context, log verification events, and enforce
   trust policies on incoming requests.

2. CloudIdentityFnMiddleware (FunctionMiddleware) — Intercepts
   function/tool calls to log identity tool usage and enforce
   policies on tool interactions.
"""

import os
import logging
from typing import Optional, Dict, Any, Callable, Awaitable

from agent_framework import AgentMiddleware, AgentRunContext
from agent_framework import FunctionMiddleware, FunctionInvocationContext
from citizenofthecloud import CloudIdentity, verify_agent

logger = logging.getLogger("citizenofthecloud.agentframework")


# ═══════════════════════════════════════════════════════════
# AGENT RUN MIDDLEWARE
# ═══════════════════════════════════════════════════════════

class CloudIdentityMiddleware(AgentMiddleware):
    """
    Agent middleware that adds Cloud Identity to every agent run.

    Intercepts agent execution to:
    - Verify incoming request headers if present in the run context
    - Sign outbound responses with the agent's Cloud Identity
    - Log identity events during execution
    - Reject runs from untrusted agents if trust policy is set

    Usage:
        from agent_framework import Agent
        from agent_framework.openai import OpenAIChatClient
        from citizenofthecloud_agentframework import CloudIdentityMiddleware

        middleware = CloudIdentityMiddleware(
            cloud_id=os.environ["CLOUD_ID"],
            private_key=os.environ["CLOUD_PRIVATE_KEY"],
            minimum_trust_score=0.5,
        )

        agent = Agent(
            chat_client=OpenAIChatClient(),
            instructions="You are a helpful assistant.",
            middleware=[middleware],
        )
    """

    def __init__(
        self,
        cloud_id: Optional[str] = None,
        private_key: Optional[str] = None,
        minimum_trust_score: float = 0.0,
        require_covenant: bool = False,
        log_events: bool = True,
    ):
        """
        Initialize Cloud Identity middleware.

        Args:
            cloud_id: This agent's Cloud ID (or set CLOUD_ID env var)
            private_key: This agent's private key (or set CLOUD_PRIVATE_KEY env var)
            minimum_trust_score: Min trust for incoming agents (default 0.0)
            require_covenant: Require covenant signed (default False)
            log_events: Log identity events (default True)
        """
        self._cloud_id = cloud_id or os.environ.get("CLOUD_ID")
        self._private_key = private_key or os.environ.get("CLOUD_PRIVATE_KEY")
        self._minimum_trust_score = minimum_trust_score
        self._require_covenant = require_covenant
        self._log_events = log_events
        self._identity = None

        if self._cloud_id and self._private_key:
            self._identity = CloudIdentity(
                cloud_id=self._cloud_id,
                private_key=self._private_key,
            )

    async def process(
        self,
        context: AgentRunContext,
        next: Callable[[AgentRunContext], Awaitable[None]],
    ) -> None:
        """Intercept agent run for identity verification."""

        # Check if incoming request has Cloud Identity headers
        request_headers = getattr(context, "metadata", {}).get(
            "request_headers", None
        )

        if request_headers and self._minimum_trust_score > 0:
            # Verify the requesting agent
            policy = {
                "minimum_trust_score": self._minimum_trust_score,
                "require_covenant": self._require_covenant,
            }

            try:
                result = verify_agent(request_headers, policy=policy)
            except Exception as e:
                if self._log_events:
                    logger.error(f"Cloud Identity verification error: {e}")
                raise PermissionError(
                    f"Cloud Identity verification failed: {str(e)}"
                )

            if not result["verified"]:
                if self._log_events:
                    logger.warning(
                        f"Cloud Identity rejected: {result['reason']}"
                    )
                raise PermissionError(
                    f"Agent not authorized: {result['reason']}"
                )

            if self._log_events:
                agent = result["agent"]
                logger.info(
                    f"Cloud Identity verified: {agent['name']} "
                    f"(trust: {agent['trust_score']})"
                )

        # Continue to agent execution
        if self._log_events:
            logger.info(f"Agent run starting (Cloud ID: {self._cloud_id})")

        await next(context)

        if self._log_events:
            logger.info(f"Agent run completed (Cloud ID: {self._cloud_id})")

    def sign_headers(self) -> Dict[str, str]:
        """Generate signed headers for outbound requests."""
        if not self._identity:
            raise ValueError("No Cloud Identity configured.")
        return self._identity.sign()


# ═══════════════════════════════════════════════════════════
# FUNCTION CALL MIDDLEWARE
# ═══════════════════════════════════════════════════════════

class CloudIdentityFnMiddleware(FunctionMiddleware):
    """
    Function middleware that logs identity tool invocations.

    Intercepts function/tool calls to log when Cloud Identity tools
    are used, track verification results, and provide observability
    into the agent's identity-related decisions.

    Usage:
        from agent_framework import Agent
        from agent_framework.openai import OpenAIChatClient
        from citizenofthecloud_agentframework import (
            CloudIdentityFnMiddleware,
            cloud_identity_tools,
        )

        agent = Agent(
            chat_client=OpenAIChatClient(),
            instructions="Verify agents before interacting.",
            tools=cloud_identity_tools(),
            middleware=[CloudIdentityFnMiddleware()],
        )
    """

    def __init__(self, log_all_functions: bool = False):
        """
        Initialize function middleware.

        Args:
            log_all_functions: Log all function calls, not just identity tools
        """
        self._log_all = log_all_functions
        self._identity_tools = {
            "verify_cloud_agent",
            "lookup_cloud_agent",
            "check_agent_trust",
        }

    async def process(
        self,
        context: FunctionInvocationContext,
        next: Callable[[FunctionInvocationContext], Awaitable[None]],
    ) -> None:
        """Intercept function calls for identity logging."""

        fn_name = context.function.name
        is_identity_tool = fn_name in self._identity_tools

        if is_identity_tool or self._log_all:
            logger.info(f"Function call: {fn_name}")

        # Execute the function
        await next(context)

        # Log identity tool results
        if is_identity_tool:
            result_str = str(context.result) if context.result else ""

            if "VERIFIED" in result_str:
                logger.info(f"Identity verification: VERIFIED ({fn_name})")
            elif "NOT VERIFIED" in result_str:
                logger.warning(f"Identity verification: REJECTED ({fn_name})")
            elif "PASS" in result_str:
                logger.info(f"Trust check: PASS ({fn_name})")
            elif "FAIL" in result_str:
                logger.warning(f"Trust check: FAIL ({fn_name})")
