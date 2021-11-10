from abc import abstractmethod
from ..client.algorithm import Algorithm, Heuristic
from ..common import PlayPacket, MovePacket, MoveStatistics, Tile, make_line
from typing import List, Tuple, Set, Union
import random
import itertools
import time
from abc import ABC, abstractmethod

# TODO: Implement these classes.

class ClientAlgorithm(Algorithm, ABC):
    blocks: any
    board_size: int
    order: any

    def _get_tile_positions(self, tiles: Set[Tuple[int, int, Tile]]) -> Set[Tuple[int, int]]:
        return set([(x, y) for x, y, _ in tiles])

    def _get_moves(self, moves: List[Tuple[int, int, Tile]]) -> Set[Tuple[int, int]]:
        tile_positions = self._get_tile_positions(moves)
        invalid = tile_positions | self.blocks
        moves = set()

        for (x, y) in tile_positions:
            for (dx, dy) in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                nx, ny = dx + x, dy + y

                if (nx, ny) in invalid: continue
                if nx < 0 or nx >= self.board_size or ny < 0 or ny >= self.board_size: continue

                moves.add((nx, ny))

        return moves

    def _next_tile(self, tile: Tile) -> Tile:
        return self.order[(self.order.index(tile) + 1) % len(self.order)]

    def _random_move(self, moves: List[Tuple[int, int, Tile]]) -> Tuple[int, int]:
        invalid = self._get_tile_positions(tiles=moves) | self.blocks
        empty = set([(x, y) for x, y in itertools.product(range(self.board_size), range(self.board_size))]) - invalid

        if len(empty) == 0:
            return None
        else:
            return random.choice(list(empty))

    def _get_tile_score(self, score: List[float], index: int) -> float:
        score_copy = score.copy()
        self_score = score_copy.pop(index)
        max_other_score = max(score_copy)

        return self_score - max_other_score

    @abstractmethod
    def run(self, packet: PlayPacket) -> MovePacket:
        pass

    def next_move(self, packet: PlayPacket) -> MovePacket:
        self.start_time = time.time()
        self.blocks = set(packet.blocks)
        self.order = packet.order
        self.node_times = []
        self.depth_counts = [0] * self.max_depth

        return self.run(packet)

class MiniMax(ClientAlgorithm):
    def search(self, depth: int, moves: List[Tuple[int, int, Tile]], tile: Tile) -> Tuple[Tuple[int, int], List[float]]:
        start_time = time.time()
        if depth == 0 or start_time > self.start_time + self.max_time:
            score = self.get_score({
                "moves": moves,
                "depth": self.max_depth - depth,
                "order": self.order,
                "blocks": self.blocks
            })
            end_time = time.time()

            self.node_times.append(end_time - start_time)
            self.depth_counts[self.max_depth - depth - 1] += 1

            return (None, score)

        max_nexts = []
        for x, y in self._get_moves(moves=moves):
            move = (x, y, tile)
            max_move, max_score = self.search(
                depth=depth-1,
                moves=moves + [move],
                tile=self._next_tile(tile=tile)
            )
            max_nexts.append((move, max_score))

        tile_index = self.order.index(tile)

        if len(max_nexts) == 0:
            return self._random_move(moves=moves), [0] * len(self.order)

        max_move, max_score = max(max_nexts, key=lambda move_score: self._get_tile_score(score=move_score[1], index=tile_index))

        return (max_move, max_score)

    def run(self, packet: PlayPacket) -> MovePacket:
        move, score = self.search(
            depth=self.max_depth,
            moves=packet.moves,
            tile=self.tile
        )

        print("Play:", move, "Score:", score)

        return MovePacket(
            move=(move[0], move[1]),
            statistics=MoveStatistics(
                node_times=self.node_times,
                depth_counts=self.depth_counts,
                average_recursive_depth=0
            )
        )

class AlphaBeta(ClientAlgorithm):
    def search(self, depth: int, moves: List[Tuple[int, int, Tile]], tile: Tile, bounds: List[Tuple[int, int]]) -> Tuple[Tuple[int, int], List[float], List[Tuple[int, int]]]:
        start_time = time.time()
        if depth == 0 or start_time > self.start_time + self.max_time:
            score = self.get_score({
                "moves": moves,
                "depth": self.max_depth - depth,
                "order": self.order,
                "blocks": self.blocks
            })
            end_time = time.time()

            self.node_times.append(end_time - start_time)
            self.depth_counts[self.max_depth - depth - 1] += 1

            return (None, score, list(zip(score, score)))

        tile_index = self.order.index(tile)

        next_bounds = bounds.copy()
        max_nexts = []
        for x, y in self._get_moves(moves=moves):
            move = (x, y, tile)
            max_move, max_score, iter_bounds = self.search(
                depth=depth-1,
                moves=moves + [move],
                tile=self._next_tile(tile=tile),
                bounds=next_bounds
            )

            for ti in range(len(self.order)):
                if ti == tile_index:
                    next_bounds[ti] = (max(next_bounds[ti][0], iter_bounds[ti][1]), next_bounds[ti][1])
                else:
                    next_bounds[ti] = (next_bounds[ti][0], min(next_bounds[ti][1], iter_bounds[ti][0]))

            if next_bounds[ti][1] < next_bounds[ti][0]:
                break

            max_nexts.append((move, max_score))

        if len(max_nexts) == 0:
            return (self._random_move(moves=moves), [0] * len(self.order), [(float('-inf'), float('inf')) for _ in range(len(self.order))])

        max_move, max_score = max(max_nexts, key=lambda move_score: self._get_tile_score(score=move_score[1], index=tile_index))

        return (max_move, max_score, next_bounds)

    def run(self, packet: PlayPacket) -> MovePacket:
        move, score, _ = self.search(
            depth=self.max_depth,
            moves=packet.moves,
            tile=self.tile,
            bounds=[(float('-inf'), float('inf')) for _ in range(len(self.order))]
        )

        print("Play:", move, "Score:", score)

        return MovePacket(
            move=(move[0], move[1]),
            statistics=MoveStatistics(
                node_times=self.node_times,
                depth_counts=self.depth_counts,
                average_recursive_depth=0
            )
        )

class Heuristic2(Heuristic):
    def get_score(self, data: any) -> List[float]:
        moves: List[Tuple[int, int, Tile]] = data["moves"]
        blocks: Set[Tuple[int, int]] = data["blocks"]
        depth: int = data["depth"]
        order: List[Tile] = data["order"]

        invalid: Set[Tuple[int, int]] = set([(x, y) for x, y, _ in moves]) | blocks

        score = [0] * len(order)
        for i, (x, y, tile) in enumerate(moves[-depth:]):
            tile_index = order.index(tile)
            local_depth = self.max_depth - i + 1
            local_score = 0

            for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                for offset in range(self.line_up_size + 1):
                    line = make_line(
                        point=(x - dx * offset, y - dy * offset), 
                        direction=(dx, dy), 
                        length=self.line_up_size,
                        board_size=self.board_size
                    )

                    if not line: continue

                    line_count = 0
                    for lx, ly in line:
                        if (lx, ly, tile) in moves:
                            line_count += 1
                        elif (lx, ly) in invalid:
                            line_count = 0
                            break

                    local_score = max(local_score, min(self.line_up_size, line_count))

            score[tile_index] += local_score ** local_depth

        return score

class Heuristic1(Heuristic):
    def get_score(self, data: any) -> float:
        moves: List[Tuple[int, int, Tile]] = data["moves"]
        blocks: Set[Tuple[int, int]] = data["blocks"]
        order: List[Tile] = data["order"]

        closed = set([(x, y) for x, y, _ in moves])

        score = [0] * len(order)
        for x, y, tile in moves:
            tile_index = order.index(tile)

            neighbors = 0
            invalids = 0

            for (dx, dy) in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                ox, oy = x + dx, y + dy

                if (ox, oy, tile) in moves:
                    neighbors += 1
                elif (ox, oy) in closed or (ox, oy) in blocks:
                    invalids += 1

            score[tile_index] += (4 - neighbors) * neighbors - invalids + (8 - neighbors - invalids) * 2

        return score
