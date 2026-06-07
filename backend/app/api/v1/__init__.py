"""Aggregate the v1 API routers."""

from fastapi import APIRouter

from app.api.v1 import compare, cost, diagram, graph, sessions, timeline, traces

api_router = APIRouter()
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(traces.router, tags=["traces"])
api_router.include_router(graph.router, tags=["graph"])
api_router.include_router(timeline.router, tags=["timeline"])
api_router.include_router(cost.router, tags=["cost"])
api_router.include_router(diagram.router, tags=["diagram"])
api_router.include_router(compare.router, tags=["compare"])
