"""Regression detection: compare a prompt version's avg scores to baseline."""
from __future__ import annotations
from sqlalchemy.orm import Session
from ..models import Evaluation, Span, RegressionAlert

THRESHOLD = 0.5
BASELINE_WINDOW = 50


def _avg_scores_for_version(db: Session, version_id: str) -> dict[str, float] | None:
    """Average of the most recent BASELINE_WINDOW evaluations; None if there are none."""
    rows = (
        db.query(Evaluation)
        .join(Span, Span.span_id == Evaluation.span_id)
        .filter(Span.version_id == version_id)
        .filter(Span.name == "response_complete")
        .order_by(Evaluation.eval_timestamp.desc())
        .limit(BASELINE_WINDOW)
        .all()
    )
    if not rows:
        return None

    def mean(attr: str) -> float:
        vals = [getattr(r, attr) for r in rows if getattr(r, attr) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    return {m: mean(m) for m in ("faithfulness", "relevance", "groundedness")}


def check_regression(
    db: Session,
    *,
    baseline_version_id: str,
    candidate_version_id: str,
) -> list[RegressionAlert]:
    baseline = _avg_scores_for_version(db, baseline_version_id)
    candidate = _avg_scores_for_version(db, candidate_version_id)
    if baseline is None or candidate is None:
        return []  # nothing to compare yet; avoid alerting on missing data

    alerts = []
    for metric in ("faithfulness", "relevance", "groundedness"):
        delta = candidate[metric] - baseline[metric]
        if delta < -THRESHOLD:
            alert = RegressionAlert(
                version_id=candidate_version_id,
                metric=metric,
                baseline_score=round(baseline[metric], 2),
                current_score=round(candidate[metric], 2),
                threshold=THRESHOLD,
            )
            db.add(alert)
            alerts.append(alert)
    db.commit()
    return alerts
