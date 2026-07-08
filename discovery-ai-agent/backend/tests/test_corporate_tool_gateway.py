import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.corporate.tool_gateway import CorporateSource, CorporateToolGateway


def test_corporate_source_public_dict_excludes_credentials_and_full_text_by_default():
    source = CorporateSource(
        source_id="conf_1",
        source_type="confluence",
        title="Discovery page",
        url="https://confluence.local/page",
        metadata={"space": "DISC", "token": "secret-token"},
        text="Полный корпоративный документ не должен попадать в audit log.",
    )

    payload = source.to_public_dict()

    assert payload["source_id"] == "conf_1"
    assert payload["metadata"] == {"space": "DISC"}
    assert "text" not in payload
    assert "secret-token" not in str(payload)


def test_corporate_tool_gateway_allows_only_read_and_search_actions():
    gateway = CorporateToolGateway()

    assert gateway.is_allowed("confluence.search")
    assert gateway.is_allowed("jira.read")
    assert gateway.is_allowed("git.read")
    assert gateway.is_allowed("rag.search")

    assert not gateway.is_allowed("confluence.write")
    assert not gateway.is_allowed("jira.write")
    assert not gateway.is_allowed("git.push")
    assert not gateway.is_allowed("mcp.credentials.read")


def test_corporate_tool_gateway_returns_registered_sources_without_full_document_text():
    source = CorporateSource(
        source_id="jira_1",
        source_type="jira",
        title="DISC-1",
        url="https://jira.local/browse/DISC-1",
        text="Закрытый текст задачи",
    )
    gateway = CorporateToolGateway(sources=[source])

    result = gateway.search("DISC")

    assert result["ok"] is True
    assert result["sources"][0]["source_id"] == "jira_1"
    assert "Закрытый текст задачи" not in str(result)
