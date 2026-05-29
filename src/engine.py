"""
Layer 2: Lineup Engine

Pure Python — no network calls, no I/O. Takes a list of PlayerSummary
objects and returns optimal lineup structures as plain dicts.

Lineup rules:
  Even strength (5v5): 3 forward lines of 3 + 3 defense pairs of 2
  Power play (5v4):    1 unit — 3 forwards + 2 defensemen
  Penalty kill (4v5):  1 unit — 2 forwards + 2 defensemen

Algorithm (v1 — intentionally naive):
  1. Split players into forwards (C/L/R) and defensemen (D).
  2. Sort each group by the situation-relevant point total, descending.
  3. Fill slots top-down: best players go to line/pair 1, next to line/pair 2, etc.

This ignores handedness, line chemistry, and within-group positional
constraints (e.g. C vs wing). That's fine for v1 — easy to layer in later.
"""

from .models import PlayerSummary


def _split(summaries: list[PlayerSummary]) -> tuple[list[PlayerSummary], list[PlayerSummary]]:
    """Separate skaters into forwards (C/L/R) and defensemen (D)."""
    forwards   = [s for s in summaries if s.player.position in ("C", "L", "R")]
    defensemen = [s for s in summaries if s.player.position == "D"]
    return forwards, defensemen


def _fmt(s: PlayerSummary, points_key: str, points_value: int) -> dict:
    """Serialize a PlayerSummary to a JSON-friendly dict for one situation."""
    return {
        "name": s.player.name,
        "position": s.player.position,
        "jersey_number": s.player.jersey_number,
        "games_played": s.games_played,
        points_key: points_value,
    }


def build_even_strength_lineup(summaries: list[PlayerSummary]) -> dict:
    """
    5v5 lineup: top 9 forwards split into 3 lines, top 6 defensemen into 3 pairs.
    Ranked by even-strength points over the lookback window.
    """
    forwards, defensemen = _split(summaries)
    forwards.sort(key=lambda s: s.total_even_strength_points, reverse=True)
    defensemen.sort(key=lambda s: s.total_even_strength_points, reverse=True)

    def fwd(s): return _fmt(s, "even_strength_points", s.total_even_strength_points)
    def def_(s): return _fmt(s, "even_strength_points", s.total_even_strength_points)

    f = [fwd(s) for s in forwards[:9]]
    d = [def_(s) for s in defensemen[:6]]

    return {
        "lines": [
            {"line": 1, "players": f[0:3]},
            {"line": 2, "players": f[3:6]},
            {"line": 3, "players": f[6:9]},
        ],
        "pairs": [
            {"pair": 1, "players": d[0:2]},
            {"pair": 2, "players": d[2:4]},
            {"pair": 3, "players": d[4:6]},
        ],
    }


def build_power_play_lineup(summaries: list[PlayerSummary]) -> dict:
    """
    5v4 lineup: top 3 forwards + top 2 defensemen by power-play points.
    Single unit only (v1 doesn't build a PP2).
    """
    forwards, defensemen = _split(summaries)
    forwards.sort(key=lambda s: s.total_power_play_points, reverse=True)
    defensemen.sort(key=lambda s: s.total_power_play_points, reverse=True)

    def fwd(s): return _fmt(s, "power_play_points", s.total_power_play_points)
    def def_(s): return _fmt(s, "power_play_points", s.total_power_play_points)

    return {
        "unit": {
            "forwards":   [fwd(s) for s in forwards[:3]],
            "defensemen": [def_(s) for s in defensemen[:2]],
        }
    }


def build_penalty_kill_lineup(summaries: list[PlayerSummary]) -> dict:
    """
    4v5 lineup: top 2 forwards + top 2 defensemen by shorthanded points.
    Single unit only.
    """
    forwards, defensemen = _split(summaries)
    forwards.sort(key=lambda s: s.total_shorthanded_points, reverse=True)
    defensemen.sort(key=lambda s: s.total_shorthanded_points, reverse=True)

    def fwd(s): return _fmt(s, "shorthanded_points", s.total_shorthanded_points)
    def def_(s): return _fmt(s, "shorthanded_points", s.total_shorthanded_points)

    return {
        "unit": {
            "forwards":   [fwd(s) for s in forwards[:2]],
            "defensemen": [def_(s) for s in defensemen[:2]],
        }
    }


def build_lineup(summaries: list[PlayerSummary], situation: str) -> dict:
    """
    Dispatch to the correct builder based on situation code.
      "es" → even strength
      "pp" → power play
      "sh" → shorthanded / penalty kill
    """
    if situation == "es":
        return build_even_strength_lineup(summaries)
    elif situation == "pp":
        return build_power_play_lineup(summaries)
    elif situation == "sh":
        return build_penalty_kill_lineup(summaries)
    else:
        raise ValueError(f"Unknown situation {situation!r} — must be 'es', 'pp', or 'sh'.")
