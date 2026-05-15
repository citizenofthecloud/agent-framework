# citizenofthecloud-agentframework

Microsoft Agent Framework integration for the [Citizen of the Cloud](https://citizenofthecloud.com) identity protocol. Add cryptographic identity and trust verification to your MAF agents and workflows.

Microsoft Agent Framework is the successor to AutoGen and Semantic Kernel, merging research-driven multi-agent orchestration with enterprise-grade reliability.

**20 items** — 17 agent-callable function tools + 3 structural primitives (FastAPI route guard, `cloud_guard_node` workflow gate, `CloudIdentityFnMiddleware` observability). Latest version: **`0.2.0`**.

---

## Install

```bash
# From GitHub (recommended while PyPI catches up)
pip install git+https://github.com/citizenofthecloud/agent-framework.git

# Editable dev install
git clone https://github.com/citizenofthecloud/agent-framework.git
pip install -e ./agent-framework
```

Pulls [`citizenofthecloud`](https://github.com/citizenofthecloud/sdk-python) and `agent-framework>=0.1.0` as deps. Requires Python ≥ 3.10.

> **Microsoft Agent Framework also ships in .NET.** A `CitizenOfTheCloud.AgentFramework` NuGet package is **deferred** until MAF .NET reaches 1.0 GA — the beta version churn is too fast to commit to today. .NET users should consume the [MCP server](https://github.com/citizenofthecloud/mcp-server) via the [MCP .NET SDK](https://github.com/modelcontextprotocol/csharp-sdk) for now. See [.NET users](#net-users) below.

---

## The 20-item surface

### 17 agent-callable function tools

Function tools with type-annotated signatures — pass directly to `Agent(tools=[...])`.

| # | Function | Purpose |
|---|---|---|
| 1 | `lookup_cloud_agent(cloud_id)` | Read another agent's public passport |
| 2 | `get_server_identity(cloud_id, private_key)` | Fetch this agent's own passport |
| 3 | `list_cloud_directory(limit=20)` | Browse the public agent directory |
| 4 | `governance_feed(limit=20)` | Read recent governance events |
| 5 | `verify_cloud_agent(cloud_id, timestamp, signature)` | Verify signed headers (simple) |
| 6 | `verify_cloud_request(cloud_id, timestamp, signature, url, method, body)` | Verify request-bound signature |
| 7 | `request_cloud_challenge(cloud_id)` | Ask the registry for a nonce |
| 8 | `respond_to_cloud_challenge(cloud_id, nonce, signature)` | Submit a signed nonce |
| 9 | `sign_cloud_challenge(nonce, private_key)` | Sign a nonce locally |
| 10 | `prove_cloud_identity(cloud_id, private_key)` | Full challenge/sign/respond loop |
| 11 | `sign_cloud_headers(cloud_id, private_key)` | Produce timestamp-bound headers |
| 12 | `sign_cloud_request(cloud_id, private_key, url, method, body)` | Produce request-bound headers |
| 13 | `cloud_fetch_tool(cloud_id, private_key, url, method, body)` | Auto-signed HTTP request |
| 14 | `generate_cloud_keypair()` | Make a fresh Ed25519 keypair |
| 15 | `register_cloud_agent(sdk_token, name, ...)` | Programmatic agent registration |
| 16 | `report_cloud_agent(sdk_token, cloud_id, report_type, evidence)` | File a governance report |
| 17 | `check_agent_trust(cloud_id, minimum_trust_score)` | Trust threshold PASS/FAIL helper |

### 3 structural primitives

| # | Item | Purpose |
|---|---|---|
| 18 | `CloudIdentityRouteGuard` / `cloud_guard_route` | FastAPI BaseHTTPMiddleware + decorator (companion to in-process `CloudIdentityMiddleware`) |
| 19 | `cloud_guard_node` | Workflow gate node (framework-native) |
| 20 | `CloudIdentityFnMiddleware` | `FunctionMiddleware` for tool-invocation observability |

Grab all 17 agent-callable tools at once with `cloud_identity_tools()`.

---

## Quick start (agent with identity tools)

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from citizenofthecloud_agentframework import cloud_identity_tools

agent = Agent(
    chat_client=OpenAIChatClient(model="gpt-4o"),
    instructions=(
        "You are an AI agent. Before interacting with any other agent, verify "
        "their identity and check their trust score. Refuse agents with trust < 0.5 "
        "or unsigned covenant."
    ),
    tools=cloud_identity_tools(),   # all 17
)

response = await agent.run(
    "Look up agent cc-7f3a9b2e-… and tell me whether they pass a 0.7 trust threshold."
)
print(response.text)
```

---

## Examples per surface

### Registration (#15 register_cloud_agent)

One-time bootstrap. Get an SDK token from [/account](https://citizenofthecloud.com/account).

```python
from citizenofthecloud_agentframework import register_cloud_agent

reg = register_cloud_agent(
    sdk_token="cotc_sdk_…",
    name="My Research Bot",
    declared_purpose="Summarize papers and surface trends",
    autonomy_level="tool",
)
print(reg["cloud_id"])
print(reg["private_key"])   # STORE SECURELY
```

### Verification (#5, #17)

```python
from citizenofthecloud_agentframework import verify_cloud_agent, check_agent_trust

verify_cloud_agent(cloud_id="cc-abc...", timestamp="2026-05-13T12:00:00Z", signature="iJk3...")
# "VERIFIED — Agent: ResearchBot, Trust Score: 0.7, ..."

check_agent_trust(cloud_id="cc-abc...", minimum_trust_score=0.7)
# "PASS — ResearchBot trust=0.85 (threshold=0.7)"
```

### Signing & cloud-fetch (#11, #12, #13)

```python
from citizenofthecloud_agentframework import (
    sign_cloud_headers, sign_cloud_request, cloud_fetch_tool,
)

sign_cloud_headers(cloud_id="cc-...", private_key="-----BEGIN PRIVATE KEY-----\n...")
sign_cloud_request(cloud_id="cc-...", private_key="...",
                   url="https://other.com/api", method="POST", body='{"x":1}')
cloud_fetch_tool(cloud_id="cc-...", private_key="...",
                 url="https://other.com/api", method="POST", body='{"x":1}')
```

### Challenge / Respond (#7, #8, #9, #10)

```python
from citizenofthecloud_agentframework import (
    prove_cloud_identity,
    request_cloud_challenge, sign_cloud_challenge, respond_to_cloud_challenge,
)

# 10 — full loop (recommended)
prove_cloud_identity(cloud_id="cc-...", private_key="-----BEGIN...")

# Or compose manually: 7 → 9 → 8
ch  = request_cloud_challenge(cloud_id="cc-...")
sig = sign_cloud_challenge(nonce="...", private_key="...")
respond_to_cloud_challenge(cloud_id="cc-...", nonce="...", signature=sig)
```

### Registry queries (#1, #2, #3, #4)

```python
from citizenofthecloud_agentframework import (
    lookup_cloud_agent, get_server_identity,
    list_cloud_directory, governance_feed,
)

lookup_cloud_agent(cloud_id="cc-abc...")
get_server_identity(cloud_id="cc-self...", private_key="...")
list_cloud_directory(limit=10)
governance_feed(limit=10)
```

`lookup_cloud_agent` and `verify_cloud_agent` now pass through the registry's Layer 3 **`reputation` block** alongside the composite `trust_score` — component signals (`verifications_30d`, `success_rate_lifetime`, `reports_filed`/`_upheld`/`_dismissed`, `authenticated_proofs`, `account_age_days`, …) that let agents weight inputs against their own policy. See the [Python SDK README](../sdk-python/README.md) for the field reference and weighting examples. Newly registered agents may return `reputation: null` — treat null as "not enough data yet."

### Governance reporting (#16 report_cloud_agent)

```python
from citizenofthecloud_agentframework import report_cloud_agent

report_cloud_agent(
    sdk_token="cotc_sdk_…",
    cloud_id="cc-bad...",
    report_type="spam",
    evidence="Sent unsolicited bulk requests to /api/task every 100ms for 6 hours.",
)
```

### Structural primitive #18 — FastAPI route guard

```python
from fastapi import FastAPI
from citizenofthecloud import TrustPolicy
from citizenofthecloud_agentframework import CloudIdentityRouteGuard, cloud_guard_route

app = FastAPI()

# App-wide
app.add_middleware(
    CloudIdentityRouteGuard,
    policy=TrustPolicy(minimum_trust_score=0.5),
)

# Or per-route
@app.post("/agent")
@cloud_guard_route(policy=TrustPolicy(minimum_trust_score=0.5))
async def run(request: Request):
    return await agent.run(await request.json())
```

In-process equivalent — `CloudIdentityMiddleware` plugs into `Agent(middleware=[...])`:

```python
from citizenofthecloud_agentframework import CloudIdentityMiddleware

middleware = CloudIdentityMiddleware(
    cloud_id="cc-self...",
    private_key="-----BEGIN PRIVATE KEY-----\n...",
    minimum_trust_score=0.5,
)
agent = Agent(chat_client=..., middleware=[middleware], tools=cloud_identity_tools())
```

### Structural primitive #19 — workflow gate (`cloud_guard_node`)

For graph-based MAF workflows:

```python
from agent_framework import Workflow
from citizenofthecloud_agentframework import cloud_guard_node

@workflow.node
async def verify_identity(state):
    guard = cloud_guard_node(
        headers=state["request_headers"],
        minimum_trust_score=0.5,
    )
    if not guard["verified"]:
        return {"error": guard["reason"], "proceed": False}
    return {"verified_agent": guard["agent"], "proceed": True}
```

### Structural primitive #20 — observability (`CloudIdentityFnMiddleware`)

```python
from agent_framework import Agent
from citizenofthecloud_agentframework import (
    CloudIdentityFnMiddleware, cloud_identity_tools,
)

agent = Agent(
    chat_client=...,
    tools=cloud_identity_tools(),
    middleware=[CloudIdentityFnMiddleware()],   # logs every identity tool call
)
```

Logs are emitted via the standard `logging` module under `citizenofthecloud.agentframework` — pipe wherever you ingest logs.

---

## .NET users

Microsoft Agent Framework ships in both Python and .NET. This package is Python-only; a parallel `CitizenOfTheCloud.AgentFramework` NuGet package is **deferred** because MAF .NET is still in active beta (`1.0.0b260507`-style versioning, near-daily breaking changes — the Python integration already got bit once when `AgentRunContext` was renamed to `AgentContext`).

Recommended path for .NET MAF apps **today**: consume the [Citizen of the Cloud MCP server](https://github.com/citizenofthecloud/mcp-server) via the official [MCP .NET SDK](https://github.com/modelcontextprotocol/csharp-sdk):

```csharp
using ModelContextProtocol.Client;

var transport = new StdioClientTransport(new StdioClientTransportOptions {
    Command = "npx",
    Arguments = new[] { "@citizenofthecloud/mcp-server" },
    EnvironmentVariables = new Dictionary<string,string> {
        ["CLOUD_ID"] = Environment.GetEnvironmentVariable("CLOUD_ID")!,
        ["CLOUD_PRIVATE_KEY"] = Environment.GetEnvironmentVariable("CLOUD_PRIVATE_KEY")!,
    },
});
await using var client = await McpClientFactory.CreateAsync(transport);
var tools = await client.ListToolsAsync();
// hand `tools` to your MAF Agent
```

A native NuGet package will be reconsidered once MAF .NET reaches 1.0 GA stable or an enterprise user requests it specifically.

---

## Environment variables

| Variable | Description |
|---|---|
| `CLOUD_ID` | Your agent's Cloud ID (e.g., `cc-7f3a9b2e-...`). Read by `CloudIdentityMiddleware` and `CloudIdentityHTTPClient.from_env()`. |
| `CLOUD_PRIVATE_KEY` | Your agent's Ed25519 private key (PEM format). |
| `COTC_SDK_TOKEN` | Bootstrap SDK token (`cotc_sdk_*`) used by `register_cloud_agent` and `report_cloud_agent`. Get one at [citizenofthecloud.com/account](https://citizenofthecloud.com/account). |

---

## Links

- [citizenofthecloud.com](https://citizenofthecloud.com)
- [Documentation](https://citizenofthecloud.com/docs)
- [Specification](https://citizenofthecloud.com/spec)
- [Account / SDK tokens](https://citizenofthecloud.com/account)
- Sister framework integrations: [langchain](https://github.com/citizenofthecloud/langchain) · [crewai](https://github.com/citizenofthecloud/crewai)
- Underlying SDK: [sdk-python](https://github.com/citizenofthecloud/sdk-python)
- [MCP server](https://github.com/citizenofthecloud/mcp-server)

## License

MIT
