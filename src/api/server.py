"""
TypeRead Localhost Bridge Server (Headless Integration & Test Suite)
Matches api.json server endpoint: http://127.0.0.1:8765/api/v1
"""

from __future__ import annotations
import json
from typing import Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Route

from src.app import ApplicationContainer, create_app


def create_api_app(container: Optional[ApplicationContainer] = None) -> Starlette:
    app_container = container or create_app()

    async def handle_request(request: Request) -> Response:
        # Strip '/api/v1' prefix if present
        path = request.url.path
        if path.startswith("/api/v1"):
            path = path[len("/api/v1"):]
        if not path:
            path = "/"

        method = request.method
        params = dict(request.query_params)
        body = {}
        if method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
            except Exception:
                body = {}

        api_resp = app_container.dispatcher.dispatch(
            method=method,
            path=path,
            body=body,
            params=params,
        )

        if api_resp.status_code == 204:
            return Response(status_code=204)

        return JSONResponse(
            status_code=api_resp.status_code,
            content=api_resp.data,
        )

    # Catch-all route for any method and sub-path
    routes = [
        Route("/{full_path:path}", handle_request, methods=["GET", "POST", "PUT", "PATCH", "DELETE"]),
    ]

    return Starlette(routes=routes)
