"""
Data models for the VGK lineup optimizer.

We use Python dataclasses — lightweight, no external dependencies,
and they give us free __repr__ for debugging.

Models are added here as we build each step:
  Step 1 → Player
  Step 2 → GameStats
  Step 4 → PlayerSummary
"""

from dataclasses import dataclass


@dataclass
class Player:
    player_id: int      # NHL API player ID — stable across seasons
    name: str           # Full name, e.g. "Jack Eichel"
    position: str       # "C", "L", "R", "D", or "G" (goalie)
    jersey_number: int


@dataclass
class GameStats:
    """Stats for a single player in a single game."""
    game_date: str              # "2025-01-15"
    goals: int
    assists: int
    points: int                 # goals + assists (provided directly by API)
    power_play_points: int      # PP goals + PP assists
    shorthanded_points: int     # SH goals + SH assists
    even_strength_points: int   # derived: points - pp_points - sh_points


@dataclass
class PlayerSummary:
    """A player's stats aggregated over the last N games. This is what the engine works with."""
    player: Player
    games_played: int
    total_even_strength_points: int
    total_power_play_points: int
    total_shorthanded_points: int
