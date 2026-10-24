"""Operator-facing compliance summaries, issue dispositions, and exports."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import ComplianceIssueResolution, ProcessedOutput
from app.services.cutout_service import get_output_compliance_audit, get_output_cutouts


def _stable_issue_id(issue: dict[str, Any], occurrence: int) -> str:
    # Preserve deterministic identity across requests while distinguishing duplicate findings.
    payload = json.dumps(issue, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(f"{payload}#{occurrence}".encode("utf-8")).hexdigest()


def _recommended_action(issue: dict[str, Any]) -> str:
    kind = issue.get("type")
    if kind == "misplaced_product" and issue.get("target_row_number"):
        actual = issue.get("product_name") or issue.get("sku") or "the detected product"
        expected = issue.get("expected_product_name") or issue.get("expected_sku") or "the expected product"
        return (f"Move {actual} from Row {int(issue.get('row_index', 0)) + 1} to its designated "
                f"Row {issue['target_row_number']} location, then put {expected} in the vacated facing.")
    if kind == "empty_space":
        expected = issue.get("expected_product_name") or issue.get("expected_sku") or "the expected product"
        return f"Fill the empty facing in Row {int(issue.get('row_index', 0)) + 1} with {expected}."
    actions = {
        "misplaced_product": "Move the detected product to its expected planogram slot, then capture a new shelf photo.",
        "missing_product": "Restock the expected product in this slot and capture a new shelf photo.",
        "insufficient_quantity": "Replenish the missing facing(s) to match the planogram.",
        "unexpected_product": "Confirm whether this product belongs on the selected shelf; remove or update the planogram.",
        "unrecognised_product": "Verify the product identity and ensure it is represented in this shelf's catalogue.",
        "wrong_product_label": "Check that the label is directly associated with the product above it.",
        "price_mismatch": "Verify the shelf label against the current approved product price.",
        "missing_label": "Add or reposition the expected shelf label below the assigned product.",
        "unreadable_label": "Clean, replace, or reposition the shelf label so its text can be verified.",
        "needs_review": "Review the image evidence manually; the available calibration or recognition evidence is inconclusive.",
    }
    return actions.get(str(kind), "Inspect the cited shelf location and resolve or document the finding.")


def get_compliance_report(db: Session, output_id: int) -> dict[str, Any]:
    audit = get_output_compliance_audit(db, output_id)
    records = db.query(ComplianceIssueResolution).filter_by(output_id=output_id).all()
    by_id = {record.issue_id: record for record in records}
    seen: dict[str, int] = {}
    issues = []
    for raw in audit.get("issues", []):
        issue = dict(raw)
        canonical = json.dumps(issue, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        seen[canonical] = seen.get(canonical, 0) + 1
        issue_id = _stable_issue_id(issue, seen[canonical])
        resolution = by_id.get(issue_id)
        issue.update({
            "issue_id": issue_id,
            "status": resolution.status if resolution else "open",
            "resolution_note": resolution.note if resolution else None,
            "resolution_updated_at": resolution.updated_at.isoformat() if resolution and resolution.updated_at else None,
            "recommended_action": _recommended_action(issue),
        })
        issues.append(issue)
    return {**audit, "issues": issues}


def update_issue_resolution(db: Session, output_id: int, issue_id: str, status: str, note: str | None) -> dict[str, Any]:
    if status not in {"open", "acknowledged", "resolved"}:
        raise HTTPException(status_code=422, detail="status must be open, acknowledged, or resolved")
    report = get_compliance_report(db, output_id)
    if not any(issue["issue_id"] == issue_id for issue in report["issues"]):
        raise HTTPException(status_code=404, detail="Compliance issue not found for this output")
    record = db.query(ComplianceIssueResolution).filter_by(output_id=output_id, issue_id=issue_id).one_or_none()
    if record is None:
        record = ComplianceIssueResolution(output_id=output_id, issue_id=issue_id, status=status, note=note)
        db.add(record)
    else:
        record.status = status
        record.note = note
    db.commit()
    db.refresh(record)
    return {"issue_id": issue_id, "status": record.status, "note": record.note,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None}


def get_dashboard_compliance_summary(db: Session) -> dict[str, Any]:
    outputs = db.query(ProcessedOutput).order_by(ProcessedOutput.created_at.desc(), ProcessedOutput.id.desc()).all()
    counts = {"audits": 0, "issues": 0, "open": 0, "acknowledged": 0, "resolved": 0, "needs_review": 0}
    history = []
    for output in outputs:
        audit = output.compliance_audit if isinstance(output.compliance_audit, dict) else None
        if not audit:
            continue
        counts["audits"] += 1
        issues = audit.get("issues") if isinstance(audit.get("issues"), list) else []
        resolutions = {row.issue_id: row.status for row in output.issue_resolutions}
        open_count = acknowledged = resolved = needs_review = 0
        seen: dict[str, int] = {}
        for raw in issues:
            if not isinstance(raw, dict):
                continue
            canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            seen[canonical] = seen.get(canonical, 0) + 1
            issue_id = _stable_issue_id(raw, seen[canonical])
            state = resolutions.get(issue_id, "open")
            counts["issues"] += 1
            counts[state] += 1
            open_count += state == "open"
            acknowledged += state == "acknowledged"
            resolved += state == "resolved"
            needs_review += raw.get("type") == "needs_review"
        inp = output.input_image
        snap = output.job.audit_snapshot if output.job else None
        planogram = (snap or {}).get("planogram", {}) if isinstance(snap, dict) else {}
        shelf = (snap or {}).get("shelf", {}) if isinstance(snap, dict) else {}
        history.append({"output_id": output.id, "source_filename": inp.original_filename if inp else "Unknown image",
                        "planogram_name": planogram.get("name"), "shelf_name": shelf.get("name"),
                        "created_at": output.created_at.isoformat(), "audit_status": audit.get("status", "needs_review"),
                        "issue_count": len(issues), "open_count": open_count,
                        "acknowledged_count": acknowledged, "resolved_count": resolved, "needs_review_count": needs_review,
                        "compliance_score": audit.get("compliance_score") if isinstance(audit.get("compliance_score"), dict) else None})
    return {"summary": counts, "history": history[:20]}


def export_compliance_report(db: Session, output_id: int) -> dict[str, Any]:
    report = get_compliance_report(db, output_id)
    output = db.query(ProcessedOutput).filter_by(id=output_id).one()
    cutouts = get_output_cutouts(db, output_id)
    evidence_assets = []
    for category in ("products", "empty_spaces", "shelves"):
        entries = cutouts.get(category, [])
        if not isinstance(entries, list):
            continue
        for item in entries:
            if not isinstance(item, dict):
                continue
            evidence_assets.append({
                "cutout_id": item.get("id"),
                "category": item.get("category"),
                "image_path": item.get("crop_path"),
                "bbox_xyxy": item.get("bbox_xyxy"),
                "confidence": item.get("confidence"),
                "quality_status": item.get("quality_status"),
                "quality_flags": item.get("quality_flags", []),
                "planogram_position": item.get("planogram_position"),
            })
    return {"export_schema_version": 2, "report": report,
            "source": {"input_image_id": output.input_image_id, "output_id": output.id,
                       "source_filename": output.input_image.original_filename if output.input_image else report.get("source_filename"),
                       "source_image_path": output.input_image.storage_path if output.input_image else None,
                       "annotated_image_path": output.annotated_image_path,
                       "detection_json_path": output.result_json_path,
                       "audit_snapshot": output.job.audit_snapshot if output.job else None},
            "evidence_assets": evidence_assets}
