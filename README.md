# VGK Lineup Optimizer

REST API that recommends optimal Vegas Golden Knights line combinations based on recent game performance. Uses the free, unauthenticated NHL public API — no keys needed.

---

## Quick start guide

```bash
tar -xzf vgk-lineup-optimizer.tgz
cd vgk-lineup-optimizer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Server runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Endpoints

### `GET /lineup`

Returns the optimal lineup for a given situation.

| Parameter | Required | Values | Default |
|---|---|---|---|
| `situation` | yes | `es`, `pp`, `sh` | — |
| `games` | no | 1–82 | `10` |

```bash
# Even strength — last 10 games
curl "http://localhost:8000/lineup?situation=es"

# Power play — last 5 games
curl "http://localhost:8000/lineup?situation=pp&games=5"

# Penalty kill — last 15 games
curl "http://localhost:8000/lineup?situation=sh&games=15"
```

**Even strength response** (`es`): 3 forward lines + 3 defense pairs.  
**Power play response** (`pp`): 1 unit — 3 forwards + 2 defensemen.  
**Penalty kill response** (`sh`): 1 unit — 2 forwards + 2 defensemen.

### `GET /roster`

Returns the full current VGK roster with player IDs, positions, and jersey numbers.

---

## How it works

Three layers, each independently testable:

```
GET /lineup
    │
    ▼
[Layer 3] api.py        — calls the pipeline and returns JSON
    │
    ▼
[Layer 2] engine.py     — ranks players by situation-specific points
    │
    ▼
[Layer 1] fetcher.py    — fetches roster and game logs from the NHL API
```

### Data source

All data comes from `https://api-web.nhle.com`:

- `GET /v1/roster/VGK/current` — active roster
- `GET /v1/player/{id}/game-log/now` — per-game stats for the current season

### Ranking metric

Players are ranked by **points** (goals + assists) in the relevant situation:

- **Even strength**: `total_points - power_play_points - shorthanded_points`
- **Power play**: `power_play_points` (provided directly by the API)
- **Penalty kill**: `shorthanded_points` (provided directly by the API)

The `games` parameter controls the lookback window. With `games=10`, only each player's 10 most recent games are counted.

### Lineup algorithm

1. Split skaters into forwards (C/L/R) and defensemen (D). Exclude goalies.
2. Sort each group by the situation's point total, descending.
3. Fill slots top-down: best 3 forwards → line 1, next 3 → line 2, etc.

---

## Project structure

```
├── main.py              # entry point — starts uvicorn
├── requirements.txt
└── src/
    ├── models.py        # Player, GameStats, PlayerSummary dataclasses
    ├── fetcher.py       # NHL API calls and data normalization
    ├── engine.py        # lineup ranking and selection logic
    └── api.py           # FastAPI app
```

---