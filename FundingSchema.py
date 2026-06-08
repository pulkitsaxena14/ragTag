from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Union

from pydantic import BaseModel, Field, field_validator


class Agency(BaseModel):
    name: str
    fullName: str = ""
    totalFunding: str = ""


class Program(BaseModel):
    name: str
    agency: str = ""
    funding: str = ""
    purpose: str = ""
    newOrContinuing: Literal["new", "continuing", "unspecified"] = "unspecified"


class Project(BaseModel):
    name: str
    sponsor: str = ""
    agency: str = ""
    amount: str = ""
    location: str = ""


class Directive(BaseModel):
    verbatim: str
    # A directive may target one agency (str) or several (list). Normalized to a
    # list so downstream consumers see one consistent type. This is the fix for
    # the schema-rigidity failure that discarded whole chunks when the model
    # emitted a list into a str field.
    targetAgency: List[str] = Field(default_factory=list)
    topic: str = ""
    type: Literal["directs", "encourages", "urges", "requires", "requests", "expects", "other"]

    @field_validator("targetAgency", mode="before")
    @classmethod
    def _coerce_target_agency(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [v]
        return v


class ResearchDomain(BaseModel):
    name: str
    evidence: Literal["directive", "funding", "program", "passing_mention"]
    verbatim_match: str = ""


class FundingFigure(BaseModel):
    amount: str
    agency: str = ""
    purpose: str = ""
    verbatim: str = ""


class CrossReference(BaseModel):
    kind: Literal["public_law", "fy_baseline", "exec_doc", "other_report", "jes", "statute", "other"]
    value: str
    label: str = ""
    direction: Literal["cites_prior", "amends", "authorizes", "references", "unspecified"] = "unspecified"


class FundingExtraction(BaseModel):
    agencies: List[Agency] = Field(default_factory=list)
    programs: List[Program] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    directives: List[Directive] = Field(default_factory=list)
    researchDomains: List[ResearchDomain] = Field(default_factory=list)
    fundingFigures: List[FundingFigure] = Field(default_factory=list)
    crossReferences: List[CrossReference] = Field(default_factory=list)


SYSTEM_PROMPT = Path(__file__).parent.joinpath("prompt.md").read_text(encoding="utf-8")


def funding_tag_fn(_chunk: dict, extraction: dict) -> dict:
    """Deterministic derived tags over the (institution-agnostic) extraction.

    These feed the two downstream questions — top-X research opportunities and
    early signals — which are computed in a later analysis pass, not here.
    Dollar amounts are kept as raw strings by design, so we do not sum them here.
    """
    domains = extraction.get("researchDomains", [])
    return {
        "agencies": [a["name"] for a in extraction.get("agencies", []) if a.get("name")],
        "domains": [d["name"] for d in domains if d.get("name")],
        # domains backed by a directive/funding/program (vs. passing_mention)
        "domains_supported": [
            d["name"] for d in domains
            if d.get("name") and d.get("evidence") in ("directive", "funding", "program")
        ],
        "fiscal_years": sorted({
            c["value"] for c in extraction.get("crossReferences", [])
            if c.get("kind") == "fy_baseline" and c.get("value")
        }),
        "directive_types": sorted({
            d["type"] for d in extraction.get("directives", []) if d.get("type")
        }),
        "has_funding": bool(extraction.get("fundingFigures")),
        "has_directives": bool(extraction.get("directives")),
        "program_count": len(extraction.get("programs", [])),
        "project_count": len(extraction.get("projects", [])),
    }
