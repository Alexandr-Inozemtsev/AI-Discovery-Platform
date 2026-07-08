from dataclasses import dataclass, field


@dataclass(frozen=True)
class MCPServerConfig:
    name: str
    url_env: str
    token_env: str
    allowed_tools: list[str] = field(default_factory=list)


class MCPGateway:
    """Skeleton boundary for future MCP/MSP reuse.

    Runtime credentials are intentionally not accepted here. Production wiring
    must resolve env references outside repository code and pass only short-lived
    client handles into concrete adapters.
    """

    def __init__(self, servers: list[MCPServerConfig] | None = None):
        self.servers = servers or []

    def list_safe_servers(self) -> list[dict]:
        return [
            {
                "name": server.name,
                "url_env": server.url_env,
                "token_env": server.token_env,
                "allowed_tools": list(server.allowed_tools),
            }
            for server in self.servers
        ]
