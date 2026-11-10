"""Génération procédurale du donjon, champs de vision et objets de décor."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

WALL = "#"
FLOOR = "."
STAIRS = ">"
CHEST = "C"
INSCRIPTION = "†"
SHRINE = "Φ"
THRONE = "T"
WATER = "~"


@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def cx(self) -> int:
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        return self.y + self.h // 2

    @property
    def center(self) -> tuple[int, int]:
        return self.cx, self.cy

    def tiles(self):
        for yy in range(self.y, self.y + self.h):
            for xx in range(self.x, self.x + self.w):
                yield xx, yy

    def overlaps(self, other: "Room", margin: int = 1) -> bool:
        return not (
            self.x - margin >= other.x + other.w
            or self.x + self.w + margin <= other.x
            or self.y - margin >= other.y + other.h
            or self.y + self.h + margin <= other.y
        )


@dataclass
class Feature:
    x: int
    y: int
    kind: str
    data: dict = field(default_factory=dict)


@dataclass
class Dungeon:
    width: int
    height: int
    grid: list[list[str]]
    rooms: list[Room]
    start: tuple[int, int]
    stairs: tuple[int, int]
    features: list[Feature] = field(default_factory=list)
    explored: set[tuple[int, int]] = field(default_factory=set)

    def tile(self, x: int, y: int) -> str:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return WALL

    def set_tile(self, x: int, y: int, ch: str) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = ch

    def walkable(self, x: int, y: int) -> bool:
        return self.tile(x, y) not in (WALL, WATER)

    def feature_at(self, x: int, y: int) -> Feature | None:
        for f in self.features:
            if f.x == x and f.y == y:
                return f
        return None

    def free_tile(self, rng: random.Random, avoid: set[tuple[int, int]] | None = None,
                  rooms: list[Room] | None = None) -> tuple[int, int]:
        avoid = avoid or set()
        for _ in range(400):
            pool = rooms if rooms else self.rooms
            room = rng.choice(pool)
            x, y = room.center if rng.random() < 0.5 else (
                rng.randint(room.x, room.x + room.w - 1),
                rng.randint(room.y, room.y + room.h - 1),
            )
            if (x, y) in avoid:
                continue
            if self.tile(x, y) == FLOOR:
                return x, y
        # fallback : première case libre
        for y in range(self.height):
            for x in range(self.width):
                if self.tile(x, y) == FLOOR and (x, y) not in avoid:
                    return x, y
        return self.start


def _carve_h(grid, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        grid[y][x] = FLOOR


def _carve_v(grid, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        grid[y][x] = FLOOR


def generate(depth: int, rng: random.Random) -> Dungeon:
    W, H = 58, 26
    grid = [[WALL for _ in range(W)] for _ in range(H)]
    rooms: list[Room] = []

    attempts = 90
    while attempts > 0 and len(rooms) < 9 + (depth >= 4):
        attempts -= 1
        w = rng.randint(5, 10)
        h = rng.randint(3, 5)
        x = rng.randint(1, W - w - 2)
        y = rng.randint(1, H - h - 2)
        room = Room(x, y, w, h)
        if any(room.overlaps(r, 1) for r in rooms):
            continue
        rooms.append(room)
        for xx, yy in room.tiles():
            grid[yy][xx] = FLOOR

    if len(rooms) < 2:  # filet de sécurité
        rooms = [Room(2, 2, 8, 4), Room(30, 15, 8, 4)]
        for r in rooms:
            for xx, yy in r.tiles():
                grid[yy][xx] = FLOOR

    # corridors reliant chaque pièce à la précédente
    for i in range(1, len(rooms)):
        ax, ay = rooms[i - 1].center
        bx, by = rooms[i].center
        if rng.random() < 0.5:
            _carve_h(grid, ax, bx, ay)
            _carve_v(grid, ay, by, bx)
        else:
            _carve_v(grid, ay, by, ax)
            _carve_h(grid, ax, bx, by)

    # boucle supplémentaire pour éviter les culs-de-sac trop nombreux
    if len(rooms) > 3:
        a, b = rng.sample(rooms, 2)
        ax, ay = a.center
        bx, by = b.center
        _carve_h(grid, ax, bx, ay)
        _carve_v(grid, ay, by, bx)

    start = rooms[0].center
    # escalier dans la pièce la plus éloignée
    far = max(rooms[1:], key=lambda r: abs(r.cx - start[0]) + abs(r.cy - start[1]))
    stairs_room = far
    stairs = far.center
    grid[stairs[1]][stairs[0]] = STAIRS

    dng = Dungeon(W, H, grid, rooms, start, stairs)

    # --- décor : coffre au fragment, inscription, sanctuaire -----------------
    reserved = {start, stairs}
    chest_rooms = [r for r in rooms if r is not far and r is not rooms[0]]
    chest_room = rng.choice(chest_rooms or rooms[1:])
    cx, cy = dng.free_tile(rng, reserved, [chest_room])
    dng.set_tile(cx, cy, CHEST)
    dng.features.append(Feature(cx, cy, "chest", {"fragment": True, "opened": False}))
    reserved.add((cx, cy))

    ins_room = rng.choice(rooms[1:])
    ix, iy = dng.free_tile(rng, reserved, [ins_room])
    dng.set_tile(ix, iy, INSCRIPTION)
    dng.features.append(Feature(ix, iy, "inscription", {"read": False}))
    reserved.add((ix, iy))

    if len(rooms) > 4 and rng.random() < 0.75:
        sh_room = rng.choice([r for r in rooms[1:] if r is not far] or rooms[1:])
        sx, sy = dng.free_tile(rng, reserved, [sh_room])
        dng.set_tile(sx, sy, SHRINE)
        dng.features.append(Feature(sx, sy, "shrine", {"used": False}))
        reserved.add((sx, sy))

    # deuxième inscription (mémoire du cycle) sur les étages profonds
    if depth >= 3 and len(rooms) > 5:
        rx = rng.choice(rooms[2:])
        mx, my = dng.free_tile(rng, reserved, [rx])
        dng.set_tile(mx, my, INSCRIPTION)
        dng.features.append(Feature(mx, my, "inscription", {"read": False}))

    return dng


# --------------------------------------------------------------------- FOV
def _line(x0: int, y0: int, x1: int, y1: int):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        yield x, y
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def compute_fov(dng: Dungeon, px: int, py: int, radius: int = 8) -> set[tuple[int, int]]:
    visible = {(px, py)}
    for y in range(py - radius, py + radius + 1):
        for x in range(px - radius, px + radius + 1):
            if (x - px) ** 2 + (y - py) ** 2 > radius * radius:
                continue
            if not (0 <= x < dng.width and 0 <= y < dng.height):
                continue
            blocked = False
            for lx, ly in _line(px, py, x, y):
                if blocked and (lx, ly) != (px, py):
                    break
                if (lx, ly) == (x, y):
                    visible.add((x, y))
                if dng.tile(lx, ly) == WALL and (lx, ly) != (px, py):
                    blocked = True
    dng.explored |= visible
    return visible
