# citizenofthecloud-agentframework

Microsoft Agent Framework integration for the [Citizen of the Cloud](https://citizenofthecloud.com) identity protocol. Add cryptographic identity and trust verification to your agents and workflows.

Microsoft Agent Framework is the successor to AutoGen and Semantic Kernel, merging research-driven multi-agent orchestration with enterprise-grade reliability.

## Install

```bash
# Clone (early access — not yet on PyPI)
git clone https://github.com/citizenofthecloud/agent-framework.git
pip install -e ./agent-framework

# Once published:
# pip install citizenofthecloud-agentframework
```

Requires the [Citizen of the Cloud Python SDK](https://github.com/citizenofthecloud/sdk-python).

## Quick Start

### 1. Add Identity Tools to an Agent

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from citizenofthecloud_agentframework import cloud_identity_tools

agent = Agent(
    chat_client=OpenAIChatClient(),
    name="ResearchBot",
    instructions=(
        "You verify other agents' identities before interacting. "
        "Always check trust scores before delegating or accepting data."
    ),
    tools=cloud_identity_tools(),
)

async def main():
    result = await agent.run(
        "Check the trust score of agent cc-7f3a9b2e-4d1c-8e7f-a3b2-9c1d5e8f4a6b. "
        "Minimum required: 0.7."
    )
    print(result.text)

asyncio.run(main())
```

### 2. Add Identity Middleware

```python
from citizenofthecloud_agentframework import (
    CloudIdentityMiddleware,
    CloudIdentityFnMiddleware,
    cloud_identity_tools,
)

# Agent middleware: verifies incoming requests, signs outbound, logs events
identity_mw = CloudIdentityMiddleware(
    minimum_trust_score=0.5,
    require_covenant=True,
    log_events=True,
)

# Function middleware: logs identity tool usage
fn_mw = CloudIdentityFnMiddleware()

agent = Agent(
    chat_client=OpenAIChatClient(),
    instructions="You are a trust-aware agent.",
    tools=cloud_identity_tools(),
    middleware=[identity_mw, fn_mw],
)
```

### 3. Gate Execution with cloud_guard_node

```python
from fastapi import FastAPI, Request
from citizenofthecloud_agentframework import cloud_guard_node

app = FastAPI()

@app.post("/api/analyze")
async def analyze(request: Request):
    # Verify the requesting agent
    guard = cloud_guard_node(
        headers=dict(request.headers),
        minimum_trust_score=0.5,
        require_covenant=True,
    )

    if not guard["verified"]:
        return {"error": guard["reason"]}, 401

    # Agent verified — run the agent
    body = await request.json()
    result = await agent.run(body["query"])
    return {"analysis": result.text}
```

### 4. Multi-Agent Workflow with Identity Gate

```python
from citizenofthecloud_agentframework import cloud_guard_node, cloud_identity_tools

async def verified_workflow(request_headers: dict, query: str):
    # Step 1: Verify requester
    guard = cloud_guard_node(headers=request_headers, minimum_trust_score=0.5)
    if not guard["verified"]:
        return {"error": guard["reason"]}

    requester = guard["agent"]

    # Step 2: Research agent
    researcher = Agent(
        chat_client=OpenAIChatClient(),
        name="Researcher",
        instructions="Gather information thoroughly.",
        tools=cloud_identity_tools(),
    )
    research = await researcher.run(f"Research: {query}")

    # Step 3: Analysis agent
    analyst = Agent(
        chat_client=OpenAIChatClient(),
        name="Analyst",
        instructions="Produce actionable insights.",
    )
    analysis = await analyst.run(f"Analyze:\n{research.text}")

    return {
        "requester": requester["name"],
        "analysis": analysis.text,
    }
```

### 5. Sign Outbound Requests

```python
from citizenofthecloud_agentframework import CloudIdentityHTTPClient

client = CloudIdentityHTTPClient.from_env()

# All requests are automatically signed
response = client.post(
    "https://other-agent.com/api/data",
    json={"query": "latest market data"},
)
```

## Tools Reference

### verify_cloud_agent

Full cryptographic verification of an agent's identity from request headers. Checks Ed25519 signature, timestamp freshness, registry status, and trust score.

### lookup_cloud_agent

Profile lookup from the Cloud Identity registry. Returns name, purpose, trust score, capabilities, and status. Informational only.

### check_agent_trust

Quick pass/fail trust check against a threshold.

### cloud_identity_tools()

Returns all three tools as a list. Pass directly to `Agent(tools=...)`.

## Middleware Reference

### CloudIdentityMiddleware (AgentMiddleware)

Intercepts agent runs to verify incoming request headers, enforce trust policies, and log identity events. Attach to any agent via `middleware=[...]`.

### CloudIdentityFnMiddleware (FunctionMiddleware)

Intercepts function/tool calls to log when identity tools are used and track verification results.

## Environment Variables

| Variable | Description |
|---|---|
| `CLOUD_ID` | Your agent's Cloud ID (e.g., `cc-7f3a9b2e-...`) |
| `CLOUD_PRIVATE_KEY` | Your agent's Ed25519 private key (PEM format) |

## Links

- [Citizen of the Cloud](https://citizenofthecloud.com)
- [SDK Documentation](https://citizenofthecloud.com/docs)
- [Python SDK](https://github.com/citizenofthecloud/sdk-python)
- [LangChain Integration](https://github.com/citizenofthecloud/langchain)
- [CrewAI Integration](https://github.com/citizenofthecloud/crewai)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Register an Agent](https://citizenofthecloud.com/register)
