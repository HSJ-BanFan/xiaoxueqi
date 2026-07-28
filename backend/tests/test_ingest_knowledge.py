from collections import Counter

from scripts.ingest_knowledge import (
    Fetcher,
    USER_AGENT,
    _NUMBER_PATTERN,
    _protect_numeric_literals,
    _restore_numeric_literals,
    _translation_is_complete,
    chunk_english,
    extract_page,
    repair_numeric_fidelity,
    validate_numeric_fidelity,
)
from scripts.sources import get_sources


def test_active_source_allowlist_has_60_unique_redistributable_pages():
    sources = get_sources()

    assert len(sources) == 60
    assert len({source.url for source in sources}) == 60
    assert Counter(source.source_key for source in sources) == {
        "niddk": 38,
        "medlineplus": 22,
    }


def test_extract_page_drops_superscript_citations_and_noncontent_tail():
    body = " ".join(["Useful diabetes self-management information."] * 30)
    html = f"""
    <html><head><title>Example</title></head><body><main>
      <p>Home Health Information Diabetes</p>
      <h1>Useful Page</h1>
      <ul><li>Clinical Trials on Useful Page</li></ul>
      <p>{body}<sup>1</sup></p>
      <h2>Clinical Trials for Useful Page</h2>
      <p>This research recruitment tail must not enter the corpus.</p>
      <h2>References</h2><p>Reference 2026.</p>
    </main></body></html>
    """

    title, text = extract_page(html, source_key="niddk")

    assert title == "Useful Page"
    assert "Home Health Information" not in text
    assert "self-management information" in text
    assert "Clinical Trials" not in text
    assert "research recruitment" not in text
    assert "Reference 2026" not in text
    assert "information. 1" not in text


def test_chunking_uses_word_boundaries_for_long_paragraphs():
    sentence = "Alpha beta gamma delta epsilon zeta eta theta iota kappa."
    chunks = chunk_english(" ".join([sentence] * 80), target_min=180, target_max=260, overlap=40)
    valid_first_words = {"Alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa."}

    assert len(chunks) > 2
    assert all(chunk.split(maxsplit=1)[0] in valid_first_words for chunk in chunks)


def test_compound_number_placeholder_round_trip_is_exact():
    source = "More than 1 in 4 people and 11.3% of adults were included."
    protected, replacements = _protect_numeric_literals(source)

    assert "1 in 4" not in protected
    assert _restore_numeric_literals(protected, replacements) == source


def test_numeric_repair_keeps_source_literals_and_word_numbers():
    source = "The result was 95 percent after three visits."
    translated = "结果为95%，共3次就诊。"

    repaired = repair_numeric_fidelity(source, translated)

    validate_numeric_fidelity(source, repaired)
    assert _NUMBER_PATTERN.findall(repaired) == ["95"]
    assert "三次" in repaired


def test_translation_quality_gate_rejects_untranslated_sentences():
    source = "A long source sentence about diabetes self-management. " * 8

    assert _translation_is_complete(
        source,
        "这是一段完整、清楚并且足够长的中文翻译，包含必要的健康管理信息和上下文。",
    )
    assert not _translation_is_complete(
        source,
        "这是一段中文。 This whole sentence remains untranslated and contains many English words.",
    )
    assert _translation_is_complete(
        source,
        "请访问 HealthCare.gov，或在 ShrinersHospitalsforChildren.org 查询援助计划。"
        "SHIP 顾问也可以帮助选择合适的保险方案。",
    )


def test_fetcher_honors_robots_crawl_delay(monkeypatch):
    origin = "https://example.test"
    fetcher = Fetcher()

    class FakeRobots:
        def crawl_delay(self, user_agent):
            return 10 if user_agent == "*" else None

        def can_fetch(self, user_agent, url):
            return user_agent == USER_AGENT and url.startswith(origin)

    class FakeResponse:
        text = "<main><p>ok</p></main>"
        apparent_encoding = "utf-8"
        encoding = "utf-8"

        def raise_for_status(self):
            return None

    sleeps = []
    times = iter([101.0, 111.0])
    fetcher._robots[origin] = FakeRobots()
    fetcher._last_request_at[origin] = 100.0
    monkeypatch.setattr("scripts.ingest_knowledge.time.monotonic", lambda: next(times))
    monkeypatch.setattr("scripts.ingest_knowledge.time.sleep", sleeps.append)
    monkeypatch.setattr(fetcher.session, "get", lambda url, timeout: FakeResponse())

    fetcher.get(f"{origin}/page")

    assert sleeps == [9.0]
