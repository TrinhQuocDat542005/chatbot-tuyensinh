"""Fail closed on malformed or unverified admission data."""

import json
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from actions.admissions import normalize

DATA_DIR = Path(__file__).parent / "data"
SCHEMA_DIR = Path(__file__).parent / "schemas"


class DataError(ValueError):
    pass


def load_document(name, data_dir=DATA_DIR):
    try:
        document = json.loads((data_dir / f"{name}.json").read_text(encoding="utf-8"))
        schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    except (OSError, ValueError, ValidationError) as exc:
        # Keep details in server logs; callers return a stable public message.
        raise DataError(f"Invalid data document: {name}") from exc
    sources = {s["id"]: s for s in document["sources"]}
    if len(sources) != len(document["sources"]):
        raise DataError("Duplicate source ID")
    for source in sources.values():
        host = urlparse(source["url"]).hostname or ""
        if source["verification"] == "verified" and not (host == "ut.edu.vn" or host.endswith(".ut.edu.vn")):
            raise DataError("Verified source must belong to UTH")
    if name == "school":
        for fact in document["facts"].values():
            if not set(fact["source_ids"]) <= sources.keys():
                raise DataError("Unknown school fact source")
            if fact["verification"] == "verified" and (not fact["text"] or any(
                sources[s]["verification"] != "verified" for s in fact["source_ids"])):
                raise DataError("Verified school fact requires verified sources")
    return document


def load_catalog(data_dir=DATA_DIR):
    doc = load_document("nganh", data_dir)
    majors = doc["majors"]
    ids = [m["id"] for m in majors]
    if len(ids) != len(set(ids)):
        raise DataError("Duplicate major ID")
    by_id = {m["id"]: m for m in majors}
    for major in majors:
        if major["parent_id"] is not None:
            parent = by_id.get(major["parent_id"])
            if not parent or parent["kind"] != "major" or parent["id"] == major["id"]:
                raise DataError("Invalid parent ID")
    aliases = {}
    for major in majors:
        for alias in [major["ten_nganh"], *major["aliases"]]:
            key = normalize(alias)
            if key in aliases and aliases[key] != major["id"]:
                raise DataError(f"Ambiguous alias: {key}")
            aliases[key] = major["id"]
    source_map = {s["id"]: s for s in doc["sources"]}
    sources = set(source_map)
    for major in majors:
        if not set(major["source_ids"]) <= sources:
            raise DataError("Unknown major source")
        if not set(major["profile"]["source_ids"]) <= sources:
            raise DataError("Unknown profile source")
        if major["profile"]["verification"] == "verified" and not major["profile"]["source_ids"]:
            raise DataError("Verified profile requires a source")
        if major["profile"]["verification"] == "verified" and any(
            source_map[s]["verification"] != "verified" for s in major["profile"]["source_ids"]):
            raise DataError("Verified profile requires verified sources")
        if major["verification"] == "verified" and any(
            source_map[s]["verification"] != "verified" for s in major["source_ids"]):
            raise DataError("Verified major requires verified sources")
        if major["code_verification"] == "verified" and not major["ma_nganh"]:
            raise DataError("Verified official code cannot be empty")
    for admission in doc["admissions"]:
        if admission["major_id"] not in by_id or admission["source_id"] not in sources:
            raise DataError("Unknown admission reference")
        if admission["cutoff"] is not None and admission["score_max"] is not None:
            if admission["cutoff"] > admission["score_max"]:
                raise DataError("Cutoff outside score scale")
        if admission["verification"] == "verified" and admission["method"] == "unknown":
            raise DataError("Verified cutoff requires a method")
        if admission["verification"] == "verified" and any(
            s["id"] == admission["source_id"] and s["verification"] != "verified" for s in doc["sources"]):
            raise DataError("Verified cutoff requires a verified source")
        for specialization_id in admission["specialization_ids"]:
            specialization = by_id.get(specialization_id)
            if not specialization or specialization["parent_id"] != admission["major_id"]:
                raise DataError("Admission specialization belongs to a different major")
    keys = [(a["program_code"], a["year"], a["method"], a["round"]) for a in doc["admissions"]]
    if len(keys) != len(set(keys)):
        raise DataError("Duplicate admission record")
    return doc


def find_major(query, document):
    key = normalize(query)
    matches = [m for m in document["majors"] if m["verification"] == "verified"
               and key in {normalize(a) for a in [m["ten_nganh"], *m["aliases"]]}]
    return matches[0] if len(matches) == 1 else None


def verified_admissions(document, major_id=None, year=None, method=None):
    records = [a for a in document["admissions"] if a["verification"] == "verified"
               and a["cutoff"] is not None
               and (major_id is None or a["major_id"] == major_id)
               and (year is None or a["year"] == year)
               and (method is None or a["method"] == method)]
    if year is None and records:
        latest = max(a["year"] for a in records)
        records = [a for a in records if a["year"] == latest]
    return sorted(records, key=lambda a: (a["year"], a["program_code"], a["round"]), reverse=True)


def source_text(document, source_ids):
    sources = {s["id"]: s for s in document["sources"]}
    return "\n".join(f"Nguồn: {sources[s]['url']} (kiểm tra {sources[s]['checked_at']})"
                     for s in dict.fromkeys(source_ids))
