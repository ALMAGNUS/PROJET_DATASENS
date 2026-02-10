"""
Sources Routes - CRUD Endpoints
================================
CRUD pour les sources (E1 DB) avec RBAC.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.e2.api.dependencies import require_deleter, require_reader, require_writer
from src.e2.api.schemas.source import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/sources", tags=["Sources"])


def _get_db_path() -> str:
    import os
    from pathlib import Path

    return os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))


def _connect():
    import sqlite3

    return sqlite3.connect(_get_db_path())


@router.get("", response_model=list[SourceResponse])
def list_sources(_user=Depends(require_reader)):
    conn = _connect()
    rows = conn.execute(
        """
        SELECT source_id, name, source_type, url, sync_frequency, active, is_synthetic
        FROM source
        ORDER BY name
        """
    ).fetchall()
    conn.close()
    return [
        {
            "source_id": r[0],
            "name": r[1],
            "source_type": r[2],
            "url": r[3],
            "sync_frequency": r[4],
            "is_active": bool(r[5]),
            "is_synthetic": bool(r[6]),
        }
        for r in rows
    ]


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, _user=Depends(require_reader)):
    conn = _connect()
    row = conn.execute(
        """
        SELECT source_id, name, source_type, url, sync_frequency, active, is_synthetic
        FROM source
        WHERE source_id = ?
        """,
        (source_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {
        "source_id": row[0],
        "name": row[1],
        "source_type": row[2],
        "url": row[3],
        "sync_frequency": row[4],
        "is_active": bool(row[5]),
        "is_synthetic": bool(row[6]),
    }


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, _user=Depends(require_writer)):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO source (name, source_type, url, sync_frequency, active, is_synthetic, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            payload.name,
            payload.source_type,
            payload.url,
            payload.sync_frequency or "DAILY",
            1 if payload.is_active else 0,
            1 if payload.is_synthetic else 0,
        ),
    )
    conn.commit()
    source_id = cur.lastrowid
    conn.close()
    return SourceResponse(source_id=source_id, **payload.model_dump())


@router.put("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, payload: SourceUpdate, _user=Depends(require_writer)):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE source
        SET name = ?, source_type = ?, url = ?, sync_frequency = ?, active = ?, is_synthetic = ?
        WHERE source_id = ?
        """,
        (
            payload.name,
            payload.source_type,
            payload.url,
            payload.sync_frequency or "DAILY",
            1 if payload.is_active else 0,
            1 if payload.is_synthetic else 0,
            source_id,
        ),
    )
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    conn.close()
    return SourceResponse(source_id=source_id, **payload.model_dump())


@router.delete("/{source_id}")
def delete_source(source_id: int, _user=Depends(require_deleter)):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM source WHERE source_id = ?", (source_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {"status": "deleted", "source_id": source_id}
