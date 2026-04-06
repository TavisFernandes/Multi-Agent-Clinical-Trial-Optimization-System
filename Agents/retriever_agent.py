"""
Retriever Agent Module
Primary: ClinicalTrials.gov API v2. Fallback: local dataset as structured records.
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

CT_GOV_STUDIES = "https://clinicaltrials.gov/api/v2/studies"


def _dedupe_terms_preserve_order(parts: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for p in parts:
        t = (p or "").strip()
        if not t:
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
    return out


def _normalize_study_from_api(study: Dict[str, Any]) -> Dict[str, str]:
    """Map raw API study JSON to the unified schema (all string values)."""
    proto = study.get("protocolSection") or {}
    ident = proto.get("identificationModule") or {}
    cond_mod = proto.get("conditionsModule") or {}
    arms = proto.get("armsInterventionsModule") or {}
    status_mod = proto.get("statusModule") or {}

    title = (ident.get("briefTitle") or ident.get("officialTitle") or "Untitled study").strip()

    conditions = cond_mod.get("conditions") or []
    if isinstance(conditions, list):
        condition = ", ".join(str(c).strip() for c in conditions[:4] if c)
    else:
        condition = str(conditions or "")

    interventions: List[str] = []
    raw_iv = arms.get("interventions")
    if isinstance(raw_iv, list):
        for iv in raw_iv[:5]:
            if isinstance(iv, dict):
                name = (iv.get("name") or "").strip()
                if name:
                    interventions.append(name)
            elif iv:
                interventions.append(str(iv).strip())
    intervention = "; ".join(interventions) if interventions else "Not specified in registry record"

    status = (status_mod.get("overallStatus") or "Unknown").strip()

    nct = ident.get("nctId") or ""

    rec: Dict[str, str] = {
        "title": title,
        "condition": condition or "Not specified",
        "intervention": intervention,
        "status": status,
        "source": "clinicaltrials_gov_api",
    }
    if nct:
        rec["nct_id"] = nct
    # Backward compatibility for older code expecting these keys
    rec["treatment"] = intervention
    rec["snippet"] = f"{condition[:200]} | {intervention[:200]}".strip(" |")
    return rec


class RetrieverAgent:
    """
    Retriever: ClinicalTrials.gov REST API first, then scored local CSV rows as structured records.
    Does not emit keyword-template "fake" trials.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path) if dataset_path else None
        self.data: List[Dict[str, Any]] = []
        self.headers: List[str] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        if self.dataset_path is None:
            default_path = Path(__file__).parent.parent / "Datasets" / "Clinical Data_Discovery_Cohort.csv"
            if default_path.exists():
                self.dataset_path = default_path

        if self.dataset_path and self.dataset_path.exists():
            try:
                self._parse_csv()
                logger.info("Retriever: loaded %d local rows from %s", len(self.data), self.dataset_path)
            except Exception as e:
                logger.warning("Retriever: failed to load dataset: %s", e)
        else:
            logger.warning("Retriever: no local CSV path found")

    def _parse_csv(self) -> None:
        with open(self.dataset_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            self.headers = list(reader.fieldnames or [])
            for row in reader:
                self.data.append({k: (v or "") for k, v in row.items()})

    def _sanitize_ctgov_query(self, q: str) -> str:
        """ClinicalTrials.gov rejects long / noisy `query.term` strings ('Too complicated query')."""
        q = re.sub(r"[=\^~`]", " ", q or "")
        q = re.sub(r"\s+", " ", q).strip()
        if len(q) > 200:
            q = q[:200].rsplit(" ", 1)[0]
        return q or "cancer"

    def _build_query_term(self, query: str, entities: Optional[List[Dict[str, str]]]) -> str:
        """Short, registry-friendly phrase: top entity strings (exact) + light query fallback."""
        entity_texts: List[str] = []
        if entities:
            for ent in entities:
                raw = (ent.get("text") or "").strip()
                if len(raw) > 1:
                    entity_texts.append(raw)
        entity_texts = _dedupe_terms_preserve_order(entity_texts)

        if entity_texts:
            entity_texts.sort(key=len, reverse=True)
            raw = " ".join(entity_texts[:2])
        else:
            raw = " ".join((query or "").strip().split()[:10])

        if len(raw) < 4 and (query or "").strip():
            raw = " ".join((query or "").strip().split()[:10])

        return self._sanitize_ctgov_query(raw)

    def _api_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        top_k = max(3, min(int(top_k), 5))
        params = {"query.term": query, "pageSize": top_k}
        try:
            resp = requests.get(CT_GOV_STUDIES, params=params, timeout=12)
            resp.raise_for_status()
            payload = resp.json()
            studies = payload.get("studies") or []
            out: List[Dict[str, Any]] = []
            for s in studies[:top_k]:
                if isinstance(s, dict):
                    out.append(_normalize_study_from_api(s))
            if out:
                titles = [r.get("title", "")[:60] for r in out]
                logger.info("Retriever: ClinicalTrials.gov returned %d studies: %s", len(out), titles)
            return out
        except Exception as exc:
            logger.warning("Retriever: ClinicalTrials.gov API error — using fallback: %s", exc)
            return []

    def _row_to_structured_record(self, row: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """Map a discovery-cohort CSV row to the same schema as API results (factual, not templated)."""
        pid = row.get("PatientID") or row.get("patientid") or str(rank)
        stage = (row.get("Stage") or row.get("stage") or "").strip()
        sex = (row.get("sex") or "").strip()
        race = (row.get("race") or "").strip()
        vital = (row.get("Dead or Alive") or row.get("dead or alive") or "").strip()

        cond_bits = [b for b in (stage, sex, race) if b]
        condition = " · ".join(cond_bits) if cond_bits else "Cohort participant (demographics/pathology in dataset)"

        title = f"Discovery cohort — participant {pid}"
        if stage:
            title = f"Discovery cohort — participant {pid}, stage {stage}"

        status_note = "Vital status: " + vital if vital else "Observational row (local dataset)"

        return {
            "title": title,
            "condition": condition,
            "intervention": "Observational cohort entry (not an interventional trial arm in this dataset)",
            "status": status_note,
            "source": "local_dataset",
            "snippet": condition[:240],
            "treatment": "Observational cohort entry (not an interventional trial arm in this dataset)",
        }

    def _dataset_fallback(self, query: str, entities: Optional[List[Dict[str, str]]], top_k: int) -> List[Dict[str, Any]]:
        """Score local rows and return structured records (never keyword-title templates)."""
        if not self.data:
            return self._minimal_fallback_explanation()

        search_terms = self._extract_search_terms(query, entities)
        scored: List[tuple[float, Dict[str, Any]]] = []
        for row in self.data:
            s = self._score_row(row, search_terms)
            if s > 0:
                scored.append((s, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            # Still return real rows as context rather than invented titles
            sample = self.data[: min(top_k, len(self.data))]
            return [self._row_to_structured_record(r, i + 1) for i, r in enumerate(sample)]

        return [self._row_to_structured_record(row, i + 1) for i, (_, row) in enumerate(scored[:top_k])]

    def _minimal_fallback_explanation(self) -> List[Dict[str, Any]]:
        """Honest single record when no API and no CSV."""
        return [
            {
                "title": "No clinical trial registry hits and no local dataset rows",
                "condition": "-",
                "intervention": "-",
                "status": "Retrieve with network access or add Datasets/*.csv",
                "source": "none",
                "snippet": "",
                "treatment": "-",
            }
        ]

    def search(
        self,
        query: str,
        entities: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Return 3–5 structured trial/cohort records: API first, then local dataset.
        """
        top_k = max(3, min(int(top_k), 5))
        qterm = self._build_query_term(query, entities)
        logger.info("Retriever: API query.term (trunc preview)=%s", qterm[:200])

        api_results = self._api_search(qterm, top_k=top_k)
        if api_results:
            return api_results[:top_k]

        logger.info("Retriever: falling back to structured local dataset rows")
        return self._dataset_fallback(query, entities, top_k)[:top_k]

    def _extract_search_terms(
        self,
        query: str,
        entities: Optional[List[Dict[str, str]]] = None,
    ) -> List[str]:
        terms: set[str] = set()
        for word in (query or "").lower().split():
            w = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", word)
            if len(w) > 2:
                terms.add(w)
        if entities:
            for entity in entities:
                text = (entity.get("text") or "").lower().strip()
                if text:
                    terms.add(text)
        return list(terms)

    def _score_row(self, row: Dict[str, Any], search_terms: List[str]) -> float:
        score = 0.0
        row_text = " ".join(str(v).lower() for v in row.values())
        for term in search_terms:
            if term in row_text:
                score += 1.0
        return score

    def filter_by_column(
        self,
        column: str,
        value: Any,
        exact_match: bool = False,
    ) -> List[Dict[str, Any]]:
        """Filter dataset by column value."""
        if not self.data:
            return []
        results: List[Dict[str, Any]] = []
        value_str = str(value).lower()
        for row in self.data:
            if column in row:
                row_value = str(row[column]).lower()
                if exact_match:
                    if row_value == value_str:
                        results.append(row)
                elif value_str in row_value:
                    results.append(row)
        return results

    def get_statistics(self) -> Dict[str, Any]:
        if not self.data:
            return {"total_rows": 0, "columns": [], "source": "no_data"}
        return {
            "total_rows": len(self.data),
            "columns": self.headers,
            "source": str(self.dataset_path) if self.dataset_path else "unknown",
        }


def retrieve(
    query: str,
    entities: Optional[List[Dict[str, str]]] = None,
    dataset_path: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    retriever = RetrieverAgent(dataset_path)
    return retriever.search(query, entities, top_k)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = RetrieverAgent()
    out = r.search("Patient with stage II breast cancer treated with tamoxifen", top_k=3)
    for row in out:
        print(row)
