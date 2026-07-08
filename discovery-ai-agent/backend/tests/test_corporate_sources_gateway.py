import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.corporate_sources import CorporateSource, CorporateToolGateway
from app.corporate_sources.adapters.confluence_adapter import ConfluenceAdapter
from app.corporate_sources.corporate_tool_gateway import mask_secrets, source_is_evidence


def test_corporate_tool_gateway_denies_write_and_credentials_read():
    gateway = CorporateToolGateway(adapters={})

    denied_write = gateway.handle_tool_request(
        {"tool": "confluence.write", "adapter": "confluence", "query": "DISC"}
    )
    denied_credentials = gateway.handle_tool_request(
        {"tool": "mcp.credentials.read", "adapter": "confluence", "query": "DISC"}
    )

    assert denied_write["ok"] is False
    assert denied_write["error_code"] == "TOOL_POLICY_DENIED"
    assert denied_credentials["ok"] is False
    assert denied_credentials["error_code"] == "TOOL_POLICY_DENIED"


def test_adapter_returns_corporate_source_contract():
    adapter = ConfluenceAdapter(
        sources=[
            CorporateSource(
                source_id="conf_1",
                source_type="confluence_page",
                source_name="Discovery page",
                url="https://example.invalid/confluence/pages/1",
                content_level="chunks",
                text_extraction_status="completed",
                chunks=[{"chunk_id": "c1", "text": "Контекст Discovery"}],
                metadata={"space": "DISC"},
                access_scope="read-only",
                source_trace=[{"source_id": "conf_1", "chunk_id": "c1"}],
            )
        ]
    )

    result = adapter.search({"query": "Discovery"})

    assert result[0].source_type == "confluence_page"
    assert result[0].to_public_dict()["source_name"] == "Discovery page"
    assert result[0].to_public_dict()["content_level"] == "chunks"
    assert result[0].to_public_dict()["chunks"][0]["chunk_id"] == "c1"


def test_metadata_only_source_is_not_evidence():
    source = CorporateSource(
        source_id="jira_meta",
        source_type="jira_issue",
        source_name="DISC-1",
        content_level="metadata_only",
        text_extraction_status="metadata_only",
        metadata={"status": "Open"},
    )

    assert source_is_evidence(source) is False
    assert source.to_public_dict()["extracted_text"] == ""
    assert source.to_evidence_dict() is None


def test_gateway_logs_only_safe_summary_and_masks_secrets():
    source = CorporateSource(
        source_id="rag_1",
        source_type="rag_chunk",
        source_name="Internal chunk",
        content_level="chunks",
        text_extraction_status="completed",
        extracted_text="Полный внутренний документ не должен попасть в лог.",
        chunks=[{"chunk_id": "c1", "text": "Секретный фрагмент документа"}],
        metadata={"token": "fixture-sensitive-value", "owner": "BA"},
        access_scope="read-only",
    )
    gateway = CorporateToolGateway(adapters={"rag": ConfluenceAdapter(sources=[source])})

    result = gateway.handle_tool_request(
        {
            "tool": "rag.search",
            "adapter": "rag",
            "query": "Internal",
            "api_key": "fixture-sensitive-key",
            "headers": {"Authorization": "fixture-sensitive-header"},
        }
    )
    serialized_logs = json.dumps(gateway.safe_audit_log, ensure_ascii=False)

    assert result["ok"] is True
    assert "Секретный фрагмент документа" not in serialized_logs
    assert "Полный внутренний документ" not in serialized_logs
    assert "fixture-sensitive-value" not in serialized_logs
    assert "fixture-sensitive-header" not in serialized_logs
    assert "fixture-sensitive-key" not in serialized_logs
    assert "[redacted]" in json.dumps(mask_secrets({"token": "fixture-sensitive-value"}))
