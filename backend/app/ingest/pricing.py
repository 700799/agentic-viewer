"""Model pricing: seed data and cost computation.

Prices are USD per million tokens (MTok). The ``model_price`` table is the source of
truth at runtime; this module seeds it and provides the compute helper. Prices are
illustrative defaults for the MVP and should be reviewed against current rate cards.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session as DbSession

from app.db.models import ModelPrice
from app.schemas.canonical import CostRecord

# model -> (input, output, cache_read, cache_write) USD per MTok
SEED_PRICES: dict[str, tuple[float, float, float, float]] = {
    "claude-opus-4-8": (15.0, 75.0, 1.5, 18.75),
    "claude-sonnet-4-6": (3.0, 15.0, 0.3, 3.75),
    "claude-haiku-4-5": (1.0, 5.0, 0.1, 1.25),
    "gpt-4o": (2.5, 10.0, 1.25, 0.0),
    "gpt-4o-mini": (0.15, 0.6, 0.075, 0.0),
    "o3": (10.0, 40.0, 2.5, 0.0),
}


def seed_prices(db: DbSession) -> None:
    """Insert any missing seed prices (idempotent)."""
    existing = {m for (m,) in db.query(ModelPrice.model).all()}
    for model, (inp, out, cr, cw) in SEED_PRICES.items():
        if model in existing:
            continue
        db.add(
            ModelPrice(
                model=model,
                input_per_mtok=inp,
                output_per_mtok=out,
                cache_read_per_mtok=cr,
                cache_write_per_mtok=cw,
            )
        )
    db.flush()


def compute_cost(db: DbSession, cost: CostRecord) -> tuple[Decimal, bool]:
    """Return (cost_usd, estimated).

    If the envelope already carries ``cost_usd`` it is trusted. Otherwise we look up the
    model price; if unknown, cost is 0 and ``estimated`` is flagged True.
    """
    if cost.cost_usd is not None:
        return Decimal(str(cost.cost_usd)), False

    if not cost.model:
        return Decimal(0), True

    price = db.get(ModelPrice, cost.model)
    if price is None:
        return Decimal(0), True

    mtok = Decimal(1_000_000)
    total = (
        Decimal(cost.input_tokens) * Decimal(price.input_per_mtok)
        + Decimal(cost.output_tokens) * Decimal(price.output_per_mtok)
        + Decimal(cost.cache_read_tokens) * Decimal(price.cache_read_per_mtok)
        + Decimal(cost.cache_write_tokens) * Decimal(price.cache_write_per_mtok)
    ) / mtok
    return total.quantize(Decimal("0.000001")), False
