"""Exportacao de logs de eventos para analise experimental (F13.5)."""

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser
from app.core.event_logging import read_events

router = APIRouter(prefix="/logs", tags=["logs"])


def _flatten(value: Any) -> Any:
    """Serializa valores aninhados (dict/list) para celulas de CSV."""
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False)
    return value


@router.get("/export")
def export_logs(session_id: str, _current_user: CurrentUser) -> Response:
    """Retorna em CSV os eventos registrados para uma sessao (endpoint admin)."""
    events = read_events(session_id=session_id)
    if not events:
        return Response(content="", media_type="text/csv")

    columns = sorted({key for event in events for key in event})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for event in events:
        writer.writerow({key: _flatten(value) for key, value in event.items()})

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="logs_{session_id}.csv"'},
    )
