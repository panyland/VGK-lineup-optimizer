"""
Layer 1: Data Fetcher

All NHL API communication lives here. This module converts raw JSON
responses into clean Python dataclasses (defined in models.py).
No business logic — only data retrieval and normalization.

NHL public API base URL: https://api-web.nhle.com
No authentication required.

Functions added as we build each step:
  Step 1 → fetch_roster()
  Step 2 → fetch_game_log()
  Step 3 → fetch_all_game_logs()
  Step 4 → summarize_player(), get_player_summaries()
"""

import requests

from .models import Player, GameStats, PlayerSummary

NHL_API_BASE = "https://api-web.nhle.com"
TEAM_CODE = "VGK"


def fetch_roster() -> list[Player]:
    """
    Fetch the current VGK roster from the NHL API.

    Endpoint: GET /v1/roster/VGK/current

    The response groups players by position type:
    {
      "forwards":   [{ "id": 8478402, "firstName": {"default": "Jack"},
                       "lastName": {"default": "Eichel"},
                       "sweaterNumber": 9, "positionCode": "C" }, ...],
      "defensemen": [...],
      "goalies":    [...]
    }

    We flatten all three groups into a single list of Player objects.
    Goalies are included here — they get filtered out later in the engine.
    """
    url = f"{NHL_API_BASE}/v1/roster/{TEAM_CODE}/current"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    players = []
    for group in ("forwards", "defensemen", "goalies"):
        for p in data.get(group, []):
            first = p["firstName"]["default"]
            last = p["lastName"]["default"]
            players.append(Player(
                player_id=p["id"],
                name=f"{first} {last}",
                position=p["positionCode"],
                jersey_number=p.get("sweaterNumber", 0),
            ))

    return players


def fetch_game_log(player_id: int) -> list[GameStats]:
    """
    Fetch the current-season game log for a single player.

    Endpoint: GET /v1/player/{playerId}/game-log/now

    Each entry in the "gameLog" array looks like:
    {
      "gameId": 2024020123,
      "gameDate": "2025-01-15",
      "goals": 1,
      "assists": 2,
      "points": 3,
      "powerPlayGoals": 1,
      "powerPlayPoints": 2,
      "shorthandedGoals": 0,
      "shorthandedPoints": 0,
      ...
    }

    Games the player didn't dress for are not included in the response.
    Returns entries sorted oldest-to-newest so slicing [-N:] gives the last N games.
    """
    url = f"{NHL_API_BASE}/v1/player/{player_id}/game-log/now"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    game_log = []
    for entry in data.get("gameLog", []):
        pp_points = entry.get("powerPlayPoints", 0)
        sh_points = entry.get("shorthandedPoints", 0)
        total_points = entry.get("points", 0)
        # Even-strength points aren't provided directly — we derive them.
        # Guard against negative values in case of data quirks.
        es_points = max(0, total_points - pp_points - sh_points)

        game_log.append(GameStats(
            game_date=entry["gameDate"],
            goals=entry.get("goals", 0),
            assists=entry.get("assists", 0),
            points=total_points,
            power_play_points=pp_points,
            shorthanded_points=sh_points,
            even_strength_points=es_points,
        ))

    game_log.sort(key=lambda g: g.game_date)
    return game_log


def fetch_all_game_logs(players: list[Player]) -> dict[int, list[GameStats]]:
    """
    Fetch game logs for every player on the roster.

    Returns a dict mapping player_id -> list[GameStats].
    Players with no games this season (e.g. injured, just called up) get an
    empty list rather than crashing the whole fetch.
    """
    logs: dict[int, list[GameStats]] = {}
    for player in players:
        try:
            logs[player.player_id] = fetch_game_log(player.player_id)
        except Exception as e:
            # One bad response shouldn't abort the entire roster fetch.
            print(f"  Warning: could not fetch log for {player.name} ({player.player_id}): {e}")
            logs[player.player_id] = []
    return logs


def summarize_player(player: Player, game_log: list[GameStats], n_games: int) -> PlayerSummary:
    """
    Aggregate a player's stats over their most recent N games.

    game_log must be sorted oldest-to-newest (fetch_game_log guarantees this),
    so we take the tail to get the most recent N entries.
    If fewer than N games exist we use all of them — no padding with zeros.
    """
    recent = game_log[-n_games:] if n_games > 0 else []

    return PlayerSummary(
        player=player,
        games_played=len(recent),
        total_even_strength_points=sum(g.even_strength_points for g in recent),
        total_power_play_points=sum(g.power_play_points for g in recent),
        total_shorthanded_points=sum(g.shorthanded_points for g in recent),
    )


def get_player_summaries(n_games: int = 10) -> list[PlayerSummary]:
    """
    Full pipeline: roster → game logs → summaries.

    This is the main entry point for the engine layer.
    Goalies are excluded here — they don't accumulate skater points.
    """
    players = fetch_roster()
    logs = fetch_all_game_logs(players)

    return [
        summarize_player(player, logs[player.player_id], n_games)
        for player in players
        if player.position != "G"
    ]
