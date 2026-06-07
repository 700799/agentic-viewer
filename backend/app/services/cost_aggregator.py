"""Cost rollups for the Cost view, computed on read with SQL aggregates."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.db.models import Agent, Cost, Span
from app.schemas.api import (
    CostCumulativePoint,
    CostPerAgent,
    CostPerModel,
    CostPerStep,
    CostReport,
    CostTotal,
)


def build_cost_report(db: DbSession, session_id: uuid.UUID) -> CostReport:
    # Totals
    totals = db.execute(
        select(
            func.coalesce(func.sum(Cost.input_tokens), 0),
            func.coalesce(func.sum(Cost.output_tokens), 0),
            func.coalesce(func.sum(Cost.cache_read_tokens), 0),
            func.coalesce(func.sum(Cost.cache_write_tokens), 0),
            func.coalesce(func.sum(Cost.cost_usd), 0),
        ).where(Cost.session_id == session_id)
    ).one()
    total = CostTotal(
        input_tokens=int(totals[0]),
        output_tokens=int(totals[1]),
        cache_read_tokens=int(totals[2]),
        cache_write_tokens=int(totals[3]),
        cost_usd=float(totals[4]),
    )

    # Per agent (left join so agents with cost rows show names).
    per_agent_rows = db.execute(
        select(
            Cost.agent_id,
            func.coalesce(func.sum(Cost.cost_usd), 0),
            func.coalesce(func.sum(Cost.input_tokens), 0),
            func.coalesce(func.sum(Cost.output_tokens), 0),
        )
        .where(Cost.session_id == session_id)
        .group_by(Cost.agent_id)
    ).all()
    agent_names = {a.id: a.name for a in db.scalars(select(Agent).where(Agent.session_id == session_id))}
    per_agent = [
        CostPerAgent(
            agent_id=row[0],
            name=agent_names.get(row[0], "unknown") if row[0] else "unattributed",
            cost_usd=float(row[1]),
            input_tokens=int(row[2]),
            output_tokens=int(row[3]),
        )
        for row in per_agent_rows
    ]

    # Per model
    per_model_rows = db.execute(
        select(
            func.coalesce(Cost.model, "unknown"),
            func.coalesce(func.sum(Cost.cost_usd), 0),
            func.coalesce(func.sum(Cost.input_tokens), 0),
            func.coalesce(func.sum(Cost.output_tokens), 0),
        )
        .where(Cost.session_id == session_id)
        .group_by(Cost.model)
    ).all()
    per_model = [
        CostPerModel(
            model=row[0], cost_usd=float(row[1]), input_tokens=int(row[2]), output_tokens=int(row[3])
        )
        for row in per_model_rows
    ]

    # Per step (ordered by sequence) + cumulative timeline
    step_rows = db.execute(
        select(Span.id, Span.name, Span.sequence, Cost.cost_usd)
        .join(Cost, Cost.span_id == Span.id)
        .where(Span.session_id == session_id)
        .order_by(Span.sequence)
    ).all()
    per_step: list[CostPerStep] = []
    timeline: list[CostCumulativePoint] = []
    cumulative = 0.0
    for span_id, name, seq, cost_usd in step_rows:
        c = float(cost_usd or 0)
        per_step.append(CostPerStep(span_id=span_id, name=name, sequence=seq, cost_usd=c))
        cumulative += c
        timeline.append(CostCumulativePoint(sequence=seq, cumulative_cost_usd=round(cumulative, 6)))

    return CostReport(
        total=total,
        per_agent=sorted(per_agent, key=lambda x: x.cost_usd, reverse=True),
        per_model=sorted(per_model, key=lambda x: x.cost_usd, reverse=True),
        per_step=per_step,
        timeline=timeline,
    )
