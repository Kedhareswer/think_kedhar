"""PubMed eutils fetcher. Returns parsed article metadata + abstract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import httpx
from lxml import etree

from medbrain.config import PUBMED_API_KEY, PUBMED_EMAIL

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search(
    query: str,
    *,
    retmax: int = 20,
    sort: str = "relevance",
    timeout: float = 30.0,
) -> list[str]:
    """Search PubMed via esearch. Returns list of PMIDs (strings).

    `sort` options: relevance (default), pub_date, first_author.
    """
    url = f"{EUTILS_BASE}/esearch.fcgi"
    params = _params(
        {
            "db": "pubmed",
            "term": query,
            "retmax": str(retmax),
            "sort": sort,
            "retmode": "xml",
        }
    )
    with httpx.Client(timeout=timeout) as cli:
        r = cli.get(url, params=params)
        r.raise_for_status()
    root = etree.fromstring(r.text.encode("utf-8"))
    return [_text(idn) for idn in root.findall(".//IdList/Id") if _text(idn)]


@dataclass
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    publication_types: list[str]
    publication_date: datetime | None
    journal: str | None
    authors: list[str]
    mesh_terms: list[str]
    raw_xml: str

    @property
    def primary_publication_type(self) -> str | None:
        return self.publication_types[0] if self.publication_types else None

    @property
    def url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"


def _params(extra: dict[str, str]) -> dict[str, str]:
    base = {
        "tool": "medbrain",
        "email": PUBMED_EMAIL,
    }
    if PUBMED_API_KEY:
        base["api_key"] = PUBMED_API_KEY
    base.update(extra)
    return base


def fetch_article(pmid: str, *, timeout: float = 30.0) -> PubMedArticle:
    """Fetch a single article by PMID via efetch."""
    pmid = str(pmid).strip()
    url = f"{EUTILS_BASE}/efetch.fcgi"
    params = _params({"db": "pubmed", "id": pmid, "rettype": "xml", "retmode": "xml"})
    with httpx.Client(timeout=timeout) as cli:
        r = cli.get(url, params=params)
        r.raise_for_status()
    return _parse(pmid, r.text)


def _text(node: etree._Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def _parse(pmid: str, xml: str) -> PubMedArticle:
    root = etree.fromstring(xml.encode("utf-8"))
    article_node = root.find(".//PubmedArticle")
    if article_node is None:
        raise ValueError(f"No PubmedArticle node for PMID {pmid}")

    title = _text(article_node.find(".//ArticleTitle"))
    abstract_parts: list[str] = []
    for ab in article_node.findall(".//Abstract/AbstractText"):
        label = ab.get("Label")
        body = _text(ab)
        if label:
            abstract_parts.append(f"{label}: {body}")
        else:
            abstract_parts.append(body)
    abstract = "\n\n".join(p for p in abstract_parts if p)

    publication_types = [
        _text(pt) for pt in article_node.findall(".//PublicationTypeList/PublicationType")
    ]
    publication_types = [pt for pt in publication_types if pt]

    pub_date = _parse_pub_date(article_node)

    journal = _text(article_node.find(".//Journal/Title")) or None

    authors: list[str] = []
    for author in article_node.findall(".//AuthorList/Author"):
        last = _text(author.find("LastName"))
        initials = _text(author.find("Initials"))
        if last:
            authors.append(f"{last} {initials}".strip())

    mesh_terms = [
        _text(mh.find("DescriptorName"))
        for mh in article_node.findall(".//MeshHeadingList/MeshHeading")
    ]
    mesh_terms = [m for m in mesh_terms if m]

    return PubMedArticle(
        pmid=pmid,
        title=title,
        abstract=abstract,
        publication_types=publication_types,
        publication_date=pub_date,
        journal=journal,
        authors=authors,
        mesh_terms=mesh_terms,
        raw_xml=xml,
    )


def _parse_pub_date(article_node: etree._Element) -> datetime | None:
    candidates = [
        article_node.find(".//ArticleDate"),
        article_node.find(".//PubDate"),
        article_node.find(".//DateCompleted"),
    ]
    for c in candidates:
        if c is None:
            continue
        year = _text(c.find("Year"))
        month = _text(c.find("Month")) or "1"
        day = _text(c.find("Day")) or "1"
        if not year:
            continue
        try:
            month_num = _month_to_int(month)
            return datetime(int(year), month_num, int(day))
        except (ValueError, KeyError):
            continue
    return None


_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _month_to_int(s: str) -> int:
    s = s.strip().lower()
    if s.isdigit():
        return int(s)
    if s[:3] in _MONTHS:
        return _MONTHS[s[:3]]
    raise ValueError(f"unparseable month: {s}")
