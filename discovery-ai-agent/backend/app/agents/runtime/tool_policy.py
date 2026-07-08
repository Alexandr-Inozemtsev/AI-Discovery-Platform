from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolAction:
    name: str
    target: str
    requires_user_confirmation: bool = False


@dataclass
class ToolPolicy:
    allowed_actions: set[str] = field(default_factory=set)
    denied_actions: set[str] = field(default_factory=set)
    apply_actions: set[str] = field(default_factory=set)

    @classmethod
    def for_ai_discovery_chat(cls) -> "ToolPolicy":
        return cls(
            allowed_actions={
                "artifact.read",
                "context.read",
                "completion.read",
                "confluence.read",
                "confluence.search",
                "git.read",
                "jira.read",
                "jira.search",
                "patch.preview",
                "proposed_patch.create",
                "question.create",
                "rag.read",
                "rag.search",
                "stage.status.read",
            },
            denied_actions={
                "confluence.write",
                "credential.read",
                "discovery_artifacts.write",
                "git.push",
                "git.write",
                "jira.write",
                "llm_settings.write_secret",
                "mcp.credentials.read",
                "prompt.raw_log",
                "rag.write",
            },
            apply_actions={"patch.apply"},
        )

    def is_allowed(self, action: ToolAction) -> bool:
        if action.name in self.denied_actions:
            return False
        if action.name in self.apply_actions:
            return action.requires_user_confirmation
        return action.name in self.allowed_actions
