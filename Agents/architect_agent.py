"""
Architect Agent Module
Grounded reports: exact entity spans, retrieved registry/dataset rows, clinical interpretation.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


def _unique_preserve_order(items: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for x in items:
        t = (x or "").strip()
        if not t:
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
    return out


class ArchitectAgent:
    """Builds markdown reports from pipeline output + structured retrieval — no generic trial filler."""

    def __init__(self) -> None:
        self.missing_fields: List[str] = []

    def _verbatim_by_labels(self, entities: List[Dict[str, str]], labels: Tuple[str, ...]) -> List[str]:
        found: List[str] = []
        for e in entities:
            if not isinstance(e, dict):
                continue
            lab = (e.get("label") or "").upper().strip()
            txt = (e.get("text") or "").strip()
            if lab in labels and txt:
                found.append(txt)
        return found

    def _frequency_from_text(self, text: str) -> str:
        t = text or ""
        if re.search(r"\bQD\b", t, re.I):
            return "once daily (QD)"
        if re.search(r"\bBID\b", t, re.I):
            return "twice daily (BID)"
        if re.search(r"\bTID\b", t, re.I):
            return "three times daily (TID)"
        if re.search(r"\bQOL\b|\bQoL\b", t):
            return ""  # avoid false QD from QoL
        if re.search(r"\bonce daily\b", t, re.I):
            return "once daily"
        return ""

    def _parse_n_count(self, text: str, enrollment_entity: str) -> Optional[int]:
        blob = f"{enrollment_entity} {text}"
        m = re.search(r"\bN\s*=\s*(\d+)\b", blob, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"\b(\d+)\s*patients?\b", blob, re.I)
        if m:
            return int(m.group(1))
        return None

    def _enrollment_size_label(self, n: int) -> str:
        if n < 30:
            return "small (typically early-phase or single-site signal)"
        if n <= 200:
            return "moderate (common for Phase II single-arm or randomized cohorts)"
        return "large (often Phase III–style enrollment)"

    def _clinical_context(
        self,
        pipeline_result: Any,
        entities: List[Dict[str, str]],
    ) -> Tuple[str, Dict[str, str]]:
        text = (getattr(pipeline_result, "raw_input_preview", None) or "").strip()
        if not text:
            text = " ".join(self._verbatim_by_labels(entities, ("DISEASE", "THERAPY", "DRUG", "CHEMICAL")))

        # Exact spans from NER first (never normalize away tokens like "Drug X")
        drugs = _unique_preserve_order(
            self._verbatim_by_labels(
                entities,
                ("THERAPY", "DRUG", "TREATMENT", "CHEMICAL", "MEDICATION"),
            )
        )
        treatment = ", ".join(drugs) if drugs else ""

        diseases = _unique_preserve_order(
            self._verbatim_by_labels(entities, ("DISEASE", "CONDITION", "CANCER", "FINDING"))
        )
        disease = ", ".join(diseases) if diseases else ""

        doses = _unique_preserve_order(self._verbatim_by_labels(entities, ("DOSAGE", "DOSE")))
        dosage = ", ".join(doses) if doses else ""

        enrolls = _unique_preserve_order(
            self._verbatim_by_labels(entities, ("ENROLLMENT", "COHORT", "SAMPLE", "POPULATION"))
        )
        enrollment_literal = ", ".join(enrolls) if enrolls else ""

        phases = _unique_preserve_order(
            self._verbatim_by_labels(entities, ("PHASE", "TRIAL", "STUDY_PHASE"))
        )
        phase = ", ".join(phases) if phases else ""

        # Regex fallbacks only when fields still empty (preserve multi-word drugs)
        if not treatment:
            m = re.search(
                r"(?:treated with|receiving|therapy with|with)\s+(.+?)(?=\s+in\s+patients|\s+for\s+|\s*\.|\s*$)",
                text,
                re.I,
            )
            if m:
                treatment = m.group(1).strip().rstrip(",;")

        if not disease:
            if re.search(r"breast cancer", text, re.I):
                st = re.search(r"stage\s+(?:0|I{1,3}|IV|1|2|3|4)\b", text, re.I)
                disease = f"{st.group(0)} breast cancer" if st else "breast cancer"
            else:
                m = re.search(
                    r"\b(stage\s+(?:0|I{1,3}|IV|1|2|3|4)|[A-Za-z\-]+ cancer|lung cancer|melanoma)\b",
                    text,
                    re.I,
                )
                if m:
                    disease = m.group(1).strip()

        if not phase:
            m = re.search(r"\bphase\s*(?:i{1,3}|iv|[1-4])\b", text, re.I)
            if m:
                phase = m.group(0).strip()
        if not phase:
            m = re.search(r"\bstage\s+(?:0|I{1,3}|IV|1|2|3|4)\b", text, re.I)
            if m:
                phase = m.group(0).strip()

        if not dosage:
            m = re.search(
                r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|µg|IU)(?:\s*/\s*(?:kg|m2|d|day|week|wk))?)\b",
                text,
                re.I,
            )
            if m:
                dosage = m.group(1).strip()

        if not enrollment_literal:
            m = re.search(r"\bN\s*=\s*(\d+)|(\d+)\s*patients?\b", text, re.I)
            if m:
                enrollment_literal = f"N={next(g for g in m.groups() if g)}"

        n_int = self._parse_n_count(text, enrollment_literal)
        enrollment_display = enrollment_literal
        if n_int is not None:
            enrollment_display = f"{enrollment_literal} (~{n_int} patients)" if enrollment_literal else f"{n_int} patients"

        freq = self._frequency_from_text(text)
        for e in entities:
            if isinstance(e, dict):
                freq = freq or self._frequency_from_text(e.get("text") or "")

        objective = ""
        mobj = re.search(
            r"(?:primary\s+endpoint|objective|goal|aim)\s*(?:is|:)?\s*([^.\n]+)",
            text,
            re.I,
        )
        if mobj:
            objective = mobj.group(1).strip()[:400]
        if not objective and len(text) > 10:
            # Ground objective in user words, not templates
            clipped = text.strip()
            if len(clipped) > 320:
                clipped = clipped[:320].rsplit(" ", 1)[0] + "…"
            objective = (
                "Clinical intent stated in the source: "
                f"_{clipped}_"
            )

        meta = {
            "disease": disease,
            "treatment": treatment,
            "phase": phase,
            "dosage": dosage,
            "enrollment": enrollment_display or enrollment_literal,
            "enrollment_literal": enrollment_literal,
            "n_patients": str(n_int) if n_int is not None else "",
            "frequency": freq,
            "objective": objective,
        }
        return text, meta

    def _interpretation_block(self, text: str, meta: Dict[str, str]) -> List[str]:
        lines: List[str] = []
        low = (text or "").lower()
        if (
            "dose-escalation" in low
            or "dose escalation" in low
            or ("escalation" in low and "dose" in low)
        ):
            lines.append(
                "- **Dose escalation:** Stepwise dose increases across cohorts support estimation of **Maximum Tolerated Dose (MTD)** or an RP2D under pre-specified escalation and stopping rules."
            )

        if meta.get("frequency"):
            lines.append(f"- **Administration:** {meta['frequency']} (expanded from source abbreviations where present).")

        n_s = (meta.get("n_patients") or "").strip()
        if n_s.isdigit():
            n = int(n_s)
            lines.append(
                f"- **Sample size:** Approximately **{n} patients**, interpreted as a **{self._enrollment_size_label(n)}** cohort for statistical and operational planning."
            )

        if not lines:
            lines.append(
                "- **Interpretation:** Cross-check dosing, schedule, and eligibility bullets against the full protocol and registry entries below before operational decisions."
            )
        return lines

    def _format_retrieved_evidence(self, retrieved_docs: List[Dict[str, Any]]) -> List[str]:
        lines: List[str] = []
        for i, doc in enumerate(retrieved_docs[:5], 1):
            title = str(doc.get("title") or "Untitled").strip()
            condition = str(doc.get("condition") or "-").strip()
            intervention = str(
                doc.get("intervention") or doc.get("treatment") or "-"
            ).strip()
            status = str(doc.get("status") or "-").strip()
            nct = str(doc.get("nct_id") or "").strip()
            hdr = f"#### {i}. {title}"
            lines.extend(
                [
                    hdr,
                    f"- **Condition:** {condition}",
                    f"- **Intervention:** {intervention}",
                    f"- **Status:** {status}",
                ]
            )
            if nct:
                lines.append(f"- **Registry ID:** {nct}")
            lines.append("")
        return lines

    def _validate_report(
        self,
        report: str,
        meta: Dict[str, str],
        retrieved_docs: List[Dict[str, Any]],
    ) -> str:
        """Ensure critical facts and evidence surfaced; light-touch append only."""
        additions: List[str] = []
        drug = (meta.get("treatment") or "").strip()
        if drug and drug not in report:
            additions.append(f"\n\n> **Verification note:** Named therapy **{drug}** must appear verbatim from extraction (see synopsis bullets).")

        if retrieved_docs and "## Retrieved Clinical Evidence" not in report:
            additions.append("\n\n## Retrieved Clinical Evidence\n*(validation recovery)*\n")
            additions.extend(self._format_retrieved_evidence(retrieved_docs))

        if meta.get("dosage") and meta["dosage"] not in report:
            additions.append(f"\n\n> **Dosage check:** {meta['dosage']}")

        if meta.get("phase") and meta["phase"].lower() not in report.lower():
            additions.append(f"\n\n> **Phase / stage check:** {meta['phase']}")

        if additions:
            return report.rstrip() + "".join(additions)
        return report

    def generate_report(
        self,
        pipeline_result: Any,
        retrieved_docs: List[Dict[str, Any]],
        missing_fields: Optional[List[str]] = None,
        iteration: int = 1,
    ) -> str:
        route = getattr(pipeline_result, "route", "unknown")
        entities = list(getattr(pipeline_result, "ner_entities", []) or [])
        model_outputs = getattr(pipeline_result, "model_outputs", {}) or {}
        warnings = list(getattr(pipeline_result, "warnings", []) or [])
        image_predictions = getattr(pipeline_result, "image_predictions", None)

        entity_summary = [
            f"{(e.get('text') or '').strip()}[{((e.get('label') or '').strip())}]"
            for e in entities
            if isinstance(e, dict) and (e.get("text") or "").strip()
        ]
        logger.info(
            "Architect: iteration=%s entities=%s retrieved_titles=%s",
            iteration,
            entity_summary[:20],
            [str(d.get("title", ""))[:70] for d in retrieved_docs[:5]],
        )

        sections: List[str] = []
        sections.append("# Clinical Trial Intelligence Summary")
        sections.append("")

        raw_text, ctx = self._clinical_context(pipeline_result, entities)

        # --- 1. Clinical Trial Synopsis ---
        sections.append("## Clinical Trial Synopsis")
        if route == "image":
            sections.append(
                "Image-based input was scored by the vision pipeline; synopsis focuses on model outputs and safety follow-up rather than dosing tables."
            )
            sections.append("")
        else:
            bullets: List[str] = []
            if ctx.get("phase"):
                bullets.append(f"- **Phase / stage:** {ctx['phase']}")
            if ctx.get("treatment"):
                bullets.append(f"- **Drug / intervention (verbatim from text & NER):** {ctx['treatment']}")
            if ctx.get("dosage"):
                bullets.append(f"- **Dosage (with unit):** {ctx['dosage']}")
            if ctx.get("frequency"):
                bullets.append(f"- **Frequency:** {ctx['frequency']}")
            elif re.search(r"\bQD\b", raw_text, re.I):
                bullets.append("- **Frequency:** once daily (QD)")
            if ctx.get("n_patients"):
                pc = f"{ctx['n_patients']} patients"
                lit = (ctx.get("enrollment_literal") or "").strip()
                if lit and lit.upper().replace(" ", "") != f"N={ctx['n_patients']}".upper():
                    pc = f"{pc} (notation in source: {lit})"
                bullets.append(f"- **Patient count:** {pc}")
            elif ctx.get("enrollment"):
                bullets.append(f"- **Patient count / enrollment:** {ctx['enrollment']}")
            if ctx.get("objective"):
                bullets.append(f"- **Trial objective (from input):** {ctx['objective']}")
            if ctx.get("disease"):
                bullets.append(f"- **Disease context:** {ctx['disease']}")
            if not bullets:
                bullets.append("- **Context:** See source excerpt and entities below; add dosing and phase when available in the narrative.")
            sections.extend(bullets)
            sections.append("")

        # --- 2. Executive Overview ---
        sections.append("## Executive Overview")
        if route == "text":
            preview = (raw_text[:360] + "…") if len(raw_text) > 360 else raw_text
            sections.append(
                f"The narrative was processed with the **text pipeline** (NER + sequence model). **{len(entities)}** entity spans were preserved as extracted below."
            )
            if preview:
                sections.append(f"**Source excerpt:** _{preview}_")
            if retrieved_docs:
                srcs = {str(d.get("source", "")) for d in retrieved_docs}
                sections.append(
                    f"**Retrieval:** {len(retrieved_docs)} structured record(s) from **{', '.join(sorted(srcs))}** inform external context."
                )
        elif route == "image":
            if image_predictions:
                pred_class = image_predictions.get("predicted_class", "unknown")
                confidence = float(image_predictions.get("confidence") or 0.0)
                sections.append(
                    f"Model prediction: **{pred_class}** ({confidence:.1%} reported confidence). Correlate with pathology and staging before treatment decisions."
                )
            else:
                sections.append("Image classification completed; attach radiology/pathology reads for full context.")
        else:
            sections.append(f"Route **{route}**; see pipeline telemetry.")
        sections.append("")

        # --- 3. Extracted Entities ---
        sections.append("## Extracted Entities")
        if entities:
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                et = (entity.get("text") or "N/A").strip()
                lab = (entity.get("label") or "N/A").strip()
                sections.append(f"- **{et}** (`{lab}`)")
        else:
            sections.append("- *(No structured entities returned for this run.)*")
        sections.append("")

        # --- 4. Retrieved Clinical Evidence ---
        sections.append("## Retrieved Clinical Evidence")
        if retrieved_docs:
            sections.extend(self._format_retrieved_evidence(retrieved_docs))
        else:
            sections.append("- No retrieval rows available for this request.")
            sections.append("")

        # --- 5. Clinical interpretation (rule-based) ---
        sections.append("## Clinical Interpretation")
        sections.extend(self._interpretation_block(raw_text, ctx))
        sections.append("")

        # Telemetry & QC (short)
        sections.append("## Model Telemetry")
        if model_outputs:
            for key, value in model_outputs.items():
                sections.append(f"- **{key}**: {value}")
        else:
            sections.append("- *(No auxiliary model telemetry attached.)*")
        sections.append("")

        sections.append("## Safety & Data Quality Notes")
        if warnings:
            for w in warnings:
                sections.append(f"- {w}")
        else:
            sections.append("- No pipeline warnings on this run.")
        sections.append("")

        if missing_fields:
            sections.append("## Required Information (Critic follow-up)")
            for field in missing_fields:
                sections.append(self._generate_field_content(field))
            sections.append("")

        sections.append("## Recommendations")
        sections.append(
            self._generate_recommendations(route, entities, image_predictions, retrieved_docs)
        )
        sections.append("")
        sections.append("---")
        sections.append(f"*Architect iteration {iteration}; entities and registry rows kept verbatim where provided.*")

        report = "\n".join(sections)
        report = self._validate_report(report, ctx, retrieved_docs)

        logger.info(
            "Architect: report_len=%s synopsis_drug_present=%s evidence_rows=%s",
            len(report),
            bool(ctx.get("treatment") and ctx["treatment"] in report),
            len(retrieved_docs),
        )
        return report

    def _generate_field_content(self, field: str) -> str:
        """Critic-triggered placeholders — keep clinically neutral, not fabricated NCT text."""
        return {
            "Dosage": "### Dosage\nAdd the exact regimen from the protocol (dose, route, schedule).",
            "Phase": "### Phase\nState trial phase or disease stage explicitly using sponsor language.",
            "Patient Count": "### Enrollment\nProvide planned or actual **N** with cohort definition.",
            "Endpoints": "### Endpoints\nList primary/secondary endpoints as registered or in the SAP.",
            "Safety": "### Safety\nSummarize expected risks and monitoring from the IB/protocol.",
        }.get(field, f"### {field}\nComplete using source documents.")

    def _generate_recommendations(
        self,
        route: str,
        entities: List[Dict[str, str]],
        image_predictions: Optional[Dict[str, Any]],
        retrieved_docs: List[Dict[str, Any]],
    ) -> str:
        recs: List[str] = []
        labels = {(e.get("label") or "").upper() for e in entities if isinstance(e, dict)}
        if route == "text":
            if labels & {"DISEASE", "CONDITION", "CANCER", "FINDING"}:
                recs.append("- Reconcile disease wording with the latest diagnostic report.")
            if labels & {"THERAPY", "DRUG", "CHEMICAL", "MEDICATION", "TREATMENT"}:
                recs.append("- Cross-check drug name, strength, and schedule against the pharmacy monograph.")
            if retrieved_docs:
                recs.append(
                    "- Compare internal case facts with the **Retrieved Clinical Evidence** rows (conditions, arms, status)."
                )
        elif route == "image" and image_predictions:
            pc = str(image_predictions.get("predicted_class", ""))
            if pc == "malignant":
                recs.append("- Escalate for multidisciplinary review given malignant-class signal.")
            elif pc == "benign":
                recs.append("- Continue routine surveillance unless symptoms change.")
            else:
                recs.append("- Resolve uncertainty with additional diagnostic workup.")

        if not recs:
            recs.append("- Apply routine sponsor/medical monitor review before relying on this summary.")
        return "\n".join(recs)

    def improve_report(
        self,
        existing_report: str,
        missing_fields: List[str],
        iteration: int = 2,
    ) -> str:
        additions: List[str] = []
        for field in missing_fields:
            content = self._generate_field_content(field)
            if content not in existing_report:
                additions.append(content)
        if additions:
            return existing_report + "\n\n## Additions (Iteration {})\n".format(iteration) + "\n".join(additions)
        return existing_report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    class MockResult:
        route = "text"
        ner_entities = [
            {"text": "Drug X", "label": "DRUG"},
            {"text": "150 mg", "label": "DOSAGE"},
            {"text": "QD", "label": "FREQUENCY"},
            {"text": "N=90", "label": "ENROLLMENT"},
            {"text": "Phase II", "label": "PHASE"},
        ]
        model_outputs = {"lstm_source": "mock"}
        warnings = []
        image_predictions = None
        raw_input_preview = "Phase II dose-escalation of Drug X at 150 mg QD; planned enrollment N=90."

    ar = ArchitectAgent()
    mock_docs = [
        {
            "title": "Example Phase II Study of Drug X",
            "condition": "Solid tumors",
            "intervention": "Drug X 150 mg",
            "status": "Recruiting",
            "source": "fixture",
        }
    ]
    print(ar.generate_report(MockResult(), mock_docs, [], 1))
