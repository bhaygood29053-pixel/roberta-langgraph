from roberta.learning import InMemorySourceStore, ingest_utf8_source


def test_ingested_static_source_never_authorizes_live_state() -> None:
    result = ingest_utf8_source(
        store=InMemorySourceStore(),
        content="static technical source\n",
        origin="project://static-source",
        title="Static source",
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    )

    assert result.record.live_state_authorized is False
