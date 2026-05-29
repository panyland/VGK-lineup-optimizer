"""
Layer 3: REST API

FastAPI wrapper around the fetcher and engine. Validates inputs,
calls the pipeline, and returns JSON.

Endpoints:
  GET /lineup?situation={es|pp|sh}&games={N}   → optimal lineup
  GET /roster                                  → full VGK roster
  GET /live/status                             → live polling status (added Step 7)
"""

from typing import Annotated
from fastapi import FastAPI, HTTPException, Query
from .fetcher import fetch_roster, get_player_summaries
from .engine import build_lineup


app = FastAPI(
    title="VGK Lineup Optimizer",
    description="Optimal Vegas Golden Knights lineup recommendations based on recent performance.",
    version="0.1.0",
)


@app.get("/lineup")
def get_lineup(
    situation: Annotated[str, Query(description="es = even strength | pp = power play | sh = shorthanded")],
    games: Annotated[int, Query(ge=1, le=82, description="Number of recent games to consider")] = 10,
):
    """
    Return the optimal VGK lineup for the given situation.

    """
    if situation not in ("es", "pp", "sh"):
        raise HTTPException(status_code=422, detail="situation must be one of: es, pp, sh")

    summaries = get_player_summaries(n_games=games)
    lineup = build_lineup(summaries, situation)

    return {
        "situation": situation,
        "games": games,
        "lineup": lineup,
    }


@app.get("/roster")
def get_roster():
    """
    Return the full current VGK roster.
    
    """
    players = fetch_roster()
    return {
        "team": "VGK",
        "players": [
            {
                "player_id": p.player_id,
                "name": p.name,
                "position": p.position,
                "jersey_number": p.jersey_number,
            }
            for p in players
        ],
    }
