from ludo.model import GameConfig


def compute_begin_offsets(config: GameConfig) -> tuple[int, ...]:
    step = config.board_size // config.num_players
    return tuple(1 + i * step for i in range(config.num_players))


def player_to_global(player_pos: int, player: int, config: GameConfig) -> int:
    if player_pos == 0 or player_pos > config.board_size:
        return player_pos
    begin = compute_begin_offsets(config)[player]
    return ((player_pos - 1 + begin - 1) % config.board_size) + 1


def global_to_player(global_pos: int, player: int, config: GameConfig) -> int:
    if global_pos == 0 or global_pos > config.board_size:
        return global_pos
    begin = compute_begin_offsets(config)[player]
    return ((global_pos - begin) % config.board_size) + 1