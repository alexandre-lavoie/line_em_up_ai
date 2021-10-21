from ..client.algorithm import Algorithm, Heuristic
from ..common import PlayPacket, Move, Board, Tile, make_line
from typing import List, Tuple, Set, Union
import random

# TODO: Implement these classes.

class MiniMax(Algorithm):
    def __get_tile_positions(self, tiles: Set[Tuple[int, int, Tile]]) -> Set[Tuple[int, int]]:
        return set([(x, y) for x, y, _ in tiles])

    def __get_moves(self, tiles: Set[Tuple[int, int, Tile]], blocks: Set[Tuple[int, int]]) -> Set[Move]:
        tile_positions = self.__get_tile_positions(tiles)
        invalid = blocks | tile_positions
        moves = set()

        for (x, y) in tile_positions:
            for (dx, dy) in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                nx, ny = dx + x, dy + y

                if (nx, ny) in invalid: continue
                if nx < 0 or nx >= self.board_size or ny < 0 or ny >= self.board_size: continue

                moves.add((nx, ny))

        return moves

    def __get_tile(self, is_self: bool) -> Tile:
        if is_self:
            return Tile.WHITE if self.player_index == 0 else Tile.BLACK
        else:
            return Tile.WHITE if self.player_index == 1 else Tile.BLACK

    def __dp(self, depth: int, tiles: Set[Tuple[int, int, Tile]], blocks: Set[Tuple[int, int]], is_self: bool=True) -> Union[Move, int]:
        if depth == 0: 
            return 0

        tile = self.__get_tile(is_self)
        moves = list(self.__get_moves(
            tiles=tiles,
            blocks=blocks
        ))

        scores = []
        for (x, y) in moves:
            next_score = self.get_score(
                data={"tiles": tiles, "blocks": blocks, "move": (x, y, tile)}
            )

            if next_score == float('inf') or next_score == float('-inf'):
                return next_score

            nt = tiles.copy()
            nt.add((x, y, tile))

            scores.append(next_score + self.__dp(
                depth=depth - 1, 
                tiles=nt,
                blocks=blocks,
                is_self=not is_self
            ))

        if depth == self.max_depth:
            if len(scores) == 0:
                invalid = blocks | self.__get_tile_positions(tiles)
                moves = set()

                for y in range(self.board_size):
                    for x in range(self.board_size):
                        moves.add((x, y))

                moves = moves - invalid

                return random.choice(list(moves))

            max_score = max(scores)
            max_index = scores.index(max_score)

            return moves[max_index]
        elif len(scores) == 0:
            return 0
        elif is_self:
            return max(scores)
        else:
            return min(scores)

    def next_move(self, packet: PlayPacket) -> Move:
        move = self.__dp(
            depth=self.max_depth, 
            tiles=packet.tiles,
            blocks=packet.blocks,
            is_self=True
        )

        return move

class AlphaBeta(Algorithm):
    def next_move(self, packet: PlayPacket) -> Move:
        return (0, 0)

class Heuristic1(Heuristic):
    def __get_tile(self, tile: Union[Tile, int]) -> Tile:
        return Tile(tile) if isinstance(tile, int) else tile
    
    def __other_tile(self, tile: Tile) -> Tile:
        return Tile.BLACK if tile == Tile.WHITE else Tile.WHITE

    def get_score(self, data: any) -> float:
        tiles: Set[Tuple[int, int, Tile]] = data["tiles"]
        blocks: Set[Tuple[int, int]] = data["blocks"]

        tile_positions = {
            Tile.WHITE: set(),
            Tile.BLACK: set()
        }

        for x, y, tile in tiles:
            tile_positions[self.__get_tile(tile)].add((x, y))

        player_scores = {
            Tile.WHITE: 0,
            Tile.BLACK: 0
        }

        x, y, tile = data["move"]
        for direction in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            line_up_size = self._parameters.line_up_size

            line = make_line(
                point=(x, y), 
                direction=direction, 
                length=line_up_size,
                board_size=self._parameters.board_size
            )

            if not line: continue

            line_count = 0
            empty_count = 0

            for lx, ly in line:
                if (lx, ly) in tile_positions[tile]:
                    line_count += 1
                if (lx, ly) in tile_positions[self.__other_tile(tile)] or (lx, ly) in blocks:
                    line_count = 0
                    break
                else:
                    empty_count += 1

            if line_count == line_up_size:
                player_scores[tile] = float('inf')
                break
            else:
                player_scores[tile] += (line_count + empty_count) ** (11 - line_up_size)

        my_tile = Tile.WHITE if self.player_index == 0 else Tile.BLACK
        other_tile = Tile.WHITE if my_tile == Tile.BLACK else Tile.BLACK
        score = player_scores[my_tile] - player_scores[other_tile]

        return score

class Heuristic2(Heuristic):
    def get_score(self, data: any) -> float:
        return 0
