from __future__ import annotations

from src.plugins.who_is_spy.logic import games
from src.plugins.who_is_spy.models import Game, Player
from src.plugins.who_is_spy.session import resolve_game_sync


def test_resolve_game_sync_restores_from_memory() -> None:
    games.clear()
    game = Game(group_id=100, owner_id=1, ready=True)
    game.players[1] = Player(uid=1, nickname="a")
    game.alive_order = [1]
    games[100] = game

    resolved = resolve_game_sync(100)
    assert resolved is game
    games.clear()
