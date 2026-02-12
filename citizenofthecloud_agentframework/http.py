"""
Signed HTTP client for Microsoft Agent Framework agents.

Wraps the requests library to automatically sign all outbound HTTP
requests with Cloud Identity headers. Use this when your agent
needs to call other agents or external services.
"""

import os
import requests
from typing import Optional, Any
from citizenofthecloud import CloudIdentity


class CloudIdentityHTTPClient:
    """
    HTTP client that automatically signs requests with Cloud Identity headers.

    Usage:
        from citizenofthecloud_agentframework import CloudIdentityHTTPClient

        client = CloudIdentityHTTPClient.from_env()
        response = client.get("https://other-agent.com/api/data")
        response = client.post("https://other-agent.com/api/task", json={"task": "analyze"})

    As a tool in an Agent Framework agent:
        client = CloudIdentityHTTPClient.from_env()

        def call_external_agent(
            url: Annotated[str, Field(description="URL of the agent to call")],
            payload: Annotated[str, Field(description="JSON payload to send")],
        ) -> str:
            \"\"\"Call an external agent with signed Cloud Identity headers.\"\"\"
            import json
            response = client.post(url, json=json.loads(payload))
            return response.text

        agent = Agent(
            chat_client=OpenAIChatClient(),
            tools=[call_external_agent],
        )
    """

    def __init__(self, cloud_id: str, private_key: str):
        self.identity = CloudIdentity(
            cloud_id=cloud_id,
            private_key=private_key,
        )
        self.session = requests.Session()

    @classmethod
    def from_env(
        cls,
        cloud_id_var: str = "CLOUD_ID",
        private_key_var: str = "CLOUD_PRIVATE_KEY",
    ) -> "CloudIdentityHTTPClient":
        """Create client from environment variables."""
        cloud_id = os.environ.get(cloud_id_var)
        private_key = os.environ.get(private_key_var)

        if not cloud_id or not private_key:
            raise ValueError(
                f"Missing environment variables: {cloud_id_var} and/or "
                f"{private_key_var}"
            )

        return cls(cloud_id=cloud_id, private_key=private_key)

    def _signed_headers(self, extra_headers: Optional[dict] = None) -> dict:
        """Generate signed headers, merged with any extra headers."""
        headers = self.identity.sign()
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def get(self, url: str, headers: Optional[dict] = None, **kwargs: Any) -> requests.Response:
        """Signed GET request."""
        return self.session.get(url, headers=self._signed_headers(headers), **kwargs)

    def post(self, url: str, headers: Optional[dict] = None, **kwargs: Any) -> requests.Response:
        """Signed POST request."""
        return self.session.post(url, headers=self._signed_headers(headers), **kwargs)

    def put(self, url: str, headers: Optional[dict] = None, **kwargs: Any) -> requests.Response:
        """Signed PUT request."""
        return self.session.put(url, headers=self._signed_headers(headers), **kwargs)

    def delete(self, url: str, headers: Optional[dict] = None, **kwargs: Any) -> requests.Response:
        """Signed DELETE request."""
        return self.session.delete(url, headers=self._signed_headers(headers), **kwargs)
