"""Phase 1 unit tests: publication-type mapping, novelty gate, qualifier counting."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from medbrain.enums import Certainty, ClaimStatus, EvidenceGrade, Predicate, SourceType
from medbrain.extractors.schema import (
    DoseRegimen,
    EffectSize,
    ExtractedClaim,
    Population,
    Qualifiers,
    Setting,
)
from medbrain.tools.publication_type import grade_from_publication_types


@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-p1-"))
    monkeypatch.setenv("BRAIN_DIR", str(tmp))
    import importlib

    import medbrain.config as config_mod
    import medbrain.db as db_mod

    importlib.reload(config_mod)
    importlib.reload(db_mod)
    return tmp


# ---------- publication type → grade ----------


def test_grade_picks_strongest():
    assert (
        grade_from_publication_types(["Journal Article", "Randomized Controlled Trial"])
        == EvidenceGrade.RCT
    )
    assert (
        grade_from_publication_types(["Meta-Analysis", "Review"])
        == EvidenceGrade.META_ANALYSIS
    )
    assert (
        grade_from_publication_types(["Case Reports", "Journal Article"])
        == EvidenceGrade.CASE_REPORT
    )
    assert grade_from_publication_types(["Practice Guideline"]) == EvidenceGrade.GUIDELINE


def test_grade_unknown_falls_back_to_expert_opinion():
    assert (
        grade_from_publication_types(["Journal Article", "Some Made Up Type"])
        == EvidenceGrade.EXPERT_OPINION
    )
    assert grade_from_publication_types([]) == EvidenceGrade.EXPERT_OPINION


# ---------- qualifier counting ----------


def test_populated_count_zero_for_empty():
    q = Qualifiers()
    assert q.populated_count() == 0


def test_populated_count_threshold():
    q = Qualifiers(
        population=Population(region="Greater Mekong", age_range="adults"),
        setting=Setting(care_level="outpatient"),
        effect_size=EffectSize(metric="day-3 positivity", value=0.18),
    )
    # region + age_range + care_level + effect_size = 4
    assert q.populated_count() >= 4


# ---------- novelty gate ----------


def _candidate(
    subject: str,
    predicate: Predicate,
    obj: str,
    region: str | None = None,
) -> ExtractedClaim:
    return ExtractedClaim(
        subject=subject,
        predicate=predicate,
        object=obj,
        qualifiers=Qualifiers(
            population=Population(region=region, age_range="adults"),
            setting=Setting(care_level="outpatient", endemic_status="endemic"),
            effect_size=EffectSize(metric="day-3 positivity", value=0.18),
        ),
        certainty=Certainty.MODERATE,
    )


def test_dedup_detects_identical_claim(tmp_brain: Path) -> None:
    from medbrain.db import init_schema, session_scope
    from medbrain.extractors.novelty import evaluate
    from medbrain.models import Claim, Source

    init_schema()
    cand = _candidate("P. falciparum", Predicate.RESISTS, "artemisinin", "Greater Mekong")

    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:1")
        sess.add(src)
        sess.flush()
        sess.add(
            Claim(
                subject_text=cand.subject,
                predicate=cand.predicate,
                object_text=cand.object,
                qualifiers=cand.qualifiers.to_storage(),
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.COHORT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )

    with session_scope() as sess:
        d = evaluate(sess, cand, EvidenceGrade.COHORT)
    assert d.is_duplicate
    assert d.duplicate_of_id is not None


def test_different_region_is_not_duplicate(tmp_brain: Path) -> None:
    from medbrain.db import init_schema, session_scope
    from medbrain.extractors.novelty import evaluate
    from medbrain.models import Claim, Source

    init_schema()
    mekong = _candidate("P. falciparum", Predicate.RESISTS, "artemisinin", "Greater Mekong")
    africa = _candidate("P. falciparum", Predicate.RESISTS, "artemisinin", "West Africa")

    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:2")
        sess.add(src)
        sess.flush()
        sess.add(
            Claim(
                subject_text=mekong.subject,
                predicate=mekong.predicate,
                object_text=mekong.object,
                qualifiers=mekong.qualifiers.to_storage(),
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.COHORT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )

    with session_scope() as sess:
        d = evaluate(sess, africa, EvidenceGrade.COHORT)
    assert not d.is_duplicate


def test_contradiction_detected(tmp_brain: Path) -> None:
    from medbrain.db import init_schema, session_scope
    from medbrain.extractors.novelty import evaluate
    from medbrain.models import Claim, Source

    init_schema()
    treats = _candidate("artemisinin", Predicate.TREATS, "malaria")
    causes = _candidate("artemisinin", Predicate.CAUSES, "malaria")

    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:3")
        sess.add(src)
        sess.flush()
        sess.add(
            Claim(
                subject_text=treats.subject,
                predicate=treats.predicate,
                object_text=treats.object,
                qualifiers=treats.qualifiers.to_storage(),
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.RCT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )

    with session_scope() as sess:
        d = evaluate(sess, causes, EvidenceGrade.COHORT)
    assert not d.is_duplicate
    assert len(d.contradicts) == 1
    # Contradiction always routes to review queue.
    assert d.status == ClaimStatus.PENDING_REVIEW


def test_auto_promote_requires_known_entities_and_qualifiers(tmp_brain: Path) -> None:
    from medbrain.db import init_schema, session_scope
    from medbrain.extractors.novelty import evaluate

    init_schema()
    # No prior claims = entities unknown -> pending_review
    cand = _candidate("artemisinin", Predicate.TREATS, "malaria")
    with session_scope() as sess:
        d = evaluate(sess, cand, EvidenceGrade.RCT)
    assert d.status == ClaimStatus.PENDING_REVIEW
    assert not d.entities_known


def test_auto_promote_succeeds_when_all_conditions_met(tmp_brain: Path) -> None:
    from medbrain.db import init_schema, session_scope
    from medbrain.extractors.novelty import evaluate
    from medbrain.models import Claim, Source

    init_schema()
    cand = _candidate("artemisinin", Predicate.TREATS, "malaria")

    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:4")
        sess.add(src)
        sess.flush()
        # Seed both entities so they are "known"
        for subj, obj in [("artemisinin", "P. falciparum"), ("chloroquine", "malaria")]:
            sess.add(
                Claim(
                    subject_text=subj,
                    predicate=Predicate.TREATS,
                    object_text=obj,
                    qualifiers={"population": {"region": "Africa"}},
                    source_id=src.source_id,
                    evidence_grade=EvidenceGrade.RCT,
                    status=ClaimStatus.AUTO_PROMOTED,
                )
            )

    with session_scope() as sess:
        d = evaluate(sess, cand, EvidenceGrade.RCT)
    assert d.entities_known
    assert d.status == ClaimStatus.AUTO_PROMOTED


# ---------- PubMed XML parser ----------


_FIXTURE_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999999</PMID>
      <Article>
        <Journal><Title>Test Journal</Title></Journal>
        <ArticleTitle>Test article on artemisinin resistance</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Background text.</AbstractText>
          <AbstractText Label="RESULTS">Day-3 positivity 18% in Greater Mekong.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><LastName>Smith</LastName><Initials>J</Initials></Author>
        </AuthorList>
        <PublicationTypeList>
          <PublicationType>Journal Article</PublicationType>
          <PublicationType>Observational Study</PublicationType>
        </PublicationTypeList>
        <ArticleDate><Year>2019</Year><Month>06</Month><Day>15</Day></ArticleDate>
      </Article>
      <MeshHeadingList>
        <MeshHeading><DescriptorName>Malaria</DescriptorName></MeshHeading>
      </MeshHeadingList>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_pubmed_xml_parser():
    from medbrain.tools.pubmed import _parse

    art = _parse("99999999", _FIXTURE_XML)
    assert art.pmid == "99999999"
    assert "artemisinin" in art.title
    assert "BACKGROUND" in art.abstract
    assert "RESULTS" in art.abstract
    assert "Observational Study" in art.publication_types
    assert art.publication_date is not None
    assert art.publication_date.year == 2019
    assert art.authors == ["Smith J"]
    assert art.mesh_terms == ["Malaria"]
    assert (
        grade_from_publication_types(art.publication_types) == EvidenceGrade.COHORT
    )
