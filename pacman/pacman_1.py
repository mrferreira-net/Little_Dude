import pygame
import heapq
import random
import sys
import numpy as np

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)

pygame.mouse.set_visible(False)
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

MAP_COLS = 28
MAP_ROWS = 29

def _compute_layout(screen_w, screen_h):
    for tile in range(80,4,-1):
        map_w=MAP_COLS*tile
        map_h=MAP_ROWS*tile
        hud_h=tile
        if map_w>screen_w or map_h + hud_h>screen_h:
            continue
        if not any(tile % s == 0 for s in [2,3,4,6,8,12]):
            continue
        win_w = screen_w
        win_h = map_h + hud_h
        off_x = (screen_w-map_w)//2
        off_y = hud_h
        return tile, win_w, win_h, off_x, off_y
    return 8, screen_w, MAP_ROWS*8+8, (screen_w-MAP_COLS*8)//2,8

_info  = pygame.display.Info()
DISP_W = _info.current_w
DISP_H = _info.current_h

_IS_PI     = (DISP_W == 640 and DISP_H == 480)
_want_full = _IS_PI or "--fullscreen" in sys.argv
_usable_h  = DISP_H if _IS_PI else int(DISP_H * 0.85)

TILE, WIDTH, HEIGHT, OFFSET_X, OFFSET_Y = _compute_layout(DISP_W, _usable_h)

SPEED_DIVS = sorted(s for s in [2,3,4,6,8,12] if TILE % s == 0 and s >= 2)
if not SPEED_DIVS:
    SPEED_DIVS = [2]

_si = lambda i: SPEED_DIVS[min(i, len(SPEED_DIVS)-1)]

FRIGHT_SPEED = _si(0)
NORMAL_SPEED = _si(1)
POWER_SPEED  = _si(1)
RESPAWN_PX   = _si(3)

def _player_speed(level):
    return _si((level-1)//2+1)

def _ghost_speed(level):
    return _si((level-1)//3+1)

_flags = pygame.FULLSCREEN if _want_full else 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), _flags)
_is_fullscreen = _want_full
pygame.display.set_caption("Pac-Man")
clock  = pygame.time.Clock()

print(f"Display {DISP_W}x{DISP_H} | TILE={TILE} | window={WIDTH}x{HEIGHT} | "
      f"offset=({OFFSET_X},{OFFSET_Y}) | divs={SPEED_DIVS} | "
      f"fright={FRIGHT_SPEED} normal={NORMAL_SPEED} power={POWER_SPEED} respawn={RESPAWN_PX}")

RAW_MAP = [
    "1111111111111111111111111111",
    "1000000000000110000000000001",
    "1011110111110110111110111101",
    "1P111101111101101111101111P1",
    "1011110111110110111110111101",
    "1000000000000000000000000001",
    "1011110110111111110110111101",
    "1011110110111111110110111101",
    "1000000110000110000110000001",
    "1111110111110110111110111111",
    "1111110111110110111110111111",
    "111111011          110111111",
    "111111011 111DD111 110111111",
    "      0   11    11   0      ",
    "111111011 11111111 110111111",
    "111111011          110111111",
    "1111110110111111110110111111",
    "1111110110111111110110111111",
    "1000000000000110000000000001",
    "1011110111110110111110111101",
    "1011110111110110111110111101",
    "1P001100000000000000001100P1",
    "1110110110111111110110110111",
    "1110110110111111110110110111",
    "1000000110000110000110000001",
    "1011111111110110111111111101",
    "1011111111110110111111111101",
    "1000000000000000000000000001",
    "1111111111111111111111111111",
]

MAP_WIDTH  = len(RAW_MAP[0])
MAP_HEIGHT = len(RAW_MAP)

HOUSE_EXIT   = (13, 11)
HOUSE_CENTER = (13, 13)


FRUIT_TYPES = [
    ("Cherry",100,(220,30,30),5),
    ("Strawberry",300,(230,80,80),5),
    ("Orange",500,(255,165,0),6),
    ("Apple",700,(50,180,50),6),
    ("Melon",1000,(100,220,100),7),
    ("Galaxian",2000,(80,120,255),7),
    ("Bell",3000,(255,230,50),7),
    ("Key",5000,(200,200,200),7),
]

def _open_cells(raw_map):
    cells = []
    for y, row in enumerate(raw_map):
        for x, ch in enumerate(row):
            if ch == " " and y not in (12,13,14,15):
                cells.append((x,y))
    return cells

OPEN_CELLS = _open_cells(RAW_MAP)

import os as _os
_SND_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "sounds")

def _load_sound(filename):
    path = _os.path.join(_SND_DIR, filename)
    if _os.path.isfile(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[sound] could not load {filename}: {e}")
    return None

startup_sound= _load_sound("startup.wav")
waka_sound= _load_sound("waka.wav")
frightened_sound= _load_sound("frightened.wav")
eat_ghost_sound= _load_sound("eat_ghost.wav")
eyes_return_sound= _load_sound("eyes_return.wav")
eat_fruit_sound= _load_sound("eat_fruit.wav")
level_up_sound= _load_sound("level_up.wav")
death_sound= _load_sound("death.wav")

def _play(snd):
    if snd: snd.play()

def _play_loop(snd):
    if snd: snd.play(-1)

def _stop(snd):
    if snd: snd.stop()


_SPR_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "sprites")

def _load_sprite(filename, size=None):
    path = _os.path.join(_SPR_DIR, filename)
    if _os.path.isfile(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            sz  = size or (TILE, TILE)
            return pygame.transform.scale(img, sz)
        except Exception as e:
            print(f"[sprite] could not load {filename}: {e}")
    return None

SPR_PAC_OPEN = {
    (1,0): _load_sprite("pacman_right.png"),
    (-1,0): _load_sprite("pacman_left.png"),
    (0,-1): _load_sprite("pacman_up.png"),
    (0,1): _load_sprite("pacman_down.png"),
    (0,0): _load_sprite("pacman_right.png"),
}
SPR_PAC_HALF = {
    (1,0): _load_sprite("pacman_right_half.png"),
    (-1,0): _load_sprite("pacman_left_half.png"),
    (0,-1): _load_sprite("pacman_up_half.png"),
    (0,1): _load_sprite("pacman_down_half.png"),
    (0,0): _load_sprite("pacman_right_half.png"),
}
SPR_PAC_CLOSED = _load_sprite("pacman_closed.png")

SPR_PAC_DIE = [_load_sprite(f"pacman_die_{i:02d}.png") for i in range(10)]

_GHOST_COLOURS = ["red","pink","cyan","orange"]
_GHOST_DIRS    = {(1,0):"right", (-1,0):"left", (0,-1):"up", (0,1):"down", (0,0):"right"}

def _load_ghost_walk(colour):
    d = {}
    for vec, name in _GHOST_DIRS.items():
        fa = _load_sprite(f"ghost_{colour}_{name}_a.png")
        fb = _load_sprite(f"ghost_{colour}_{name}_b.png")
        if fa is None and fb is None:
            single = _load_sprite(f"ghost_{colour}.png")
            fa = fb = single
        elif fa is None:
            fa = fb
        elif fb is None:
            fb = fa
        d[vec] = [fa, fb]
    return d

SPR_GHOST_WALK = [_load_ghost_walk(c) for c in _GHOST_COLOURS]

def _load_pair(base):
    fa = _load_sprite(f"{base}_a.png")
    fb = _load_sprite(f"{base}_b.png")
    if fa is None and fb is None:
        single = _load_sprite(f"{base}.png")
        fa = fb = single
    elif fa is None:
        fa = fb
    elif fb is None:
        fb = fa
    return [fa, fb]

SPR_GHOST_BLUE_WALK  = _load_pair("ghost_blue")
SPR_GHOST_WHITE_WALK = _load_pair("ghost_white")

SPR_EYES = {
    (1,0): _load_sprite("eyes_right.png"),
    (-1,0): _load_sprite("eyes_left.png"),
    (0,-1): _load_sprite("eyes_up.png"),
    (0,1): _load_sprite("eyes_down.png"),
    (0,0): _load_sprite("eyes_right.png"),
}

_FRUIT_NAMES = ["cherry","strawberry","orange","apple","melon","galaxian","bell","key"]
SPR_FRUIT = [_load_sprite(f"fruit_{n}.png") for n in _FRUIT_NAMES]


def _blit_centered(surf, cx, cy):
    screen.blit(surf, (cx - surf.get_width()//2,cy-surf.get_height()//2))


class AStar:
    def __init__(self, grid, ghost_house_passable=False):
        self.grid = grid
        self.ghost_house_passable = ghost_house_passable

    def valid(self, x, y):
        return 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0])

    def passable(self, x, y):
        cell = self.grid[y][x]
        if cell == "1":
            return False
        if cell == "D" and not self.ghost_house_passable:
            return False
        return True

    def neighbors(self, node):
        x, y = node
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        return [
            (x + dx, y + dy)
            for dx, dy in dirs
            if self.valid(x+dx,y+dy) and self.passable(x+dx,y+dy)
        ]

    def search(self,start,goal):
        open_set = [(0, start)]
        came = {}
        g = {start: 0}
        while open_set:
            _, cur = heapq.heappop(open_set)
            if cur == goal:
                break
            for n in self.neighbors(cur):
                temp = g[cur] + 1
                if n not in g or temp < g[n]:
                    g[n] = temp
                    f = temp + abs(n[0] - goal[0]) + abs(n[1] - goal[1])
                    heapq.heappush(open_set,(f,n))
                    came[n] = cur
        return came

    def path(self, came, start, goal):
        if goal not in came and start != goal:
            return []
        if start == goal:
            return []
        node = goal
        path = []
        while node != start:
            path.append(node)
            if node not in came:
                return []
            node = came[node]
        return path[::-1]


class Player:
    def __init__(self, pos):
        self.start = pos
        self.pixel = [pos[0] * TILE + OFFSET_X, pos[1] * TILE + OFFSET_Y]
        self.grid = list(pos)
        self.dir = (0, 0)
        self.next_dir = (0, 0)
        self.base_speed = 2
        self.speed = 2
        self.ANIM_CYCLE = 12
        self.anim = 0
        self.score = 0
        self.lives = 3
        self.power_mode = 0
        self.moving = False

    def apply_level(self, level):
        self.speed = _player_speed(level)

    def reset(self):
        self.pixel = [self.start[0]*TILE+OFFSET_X,self.start[1]*TILE+OFFSET_Y]
        self.grid = list(self.start)
        self.dir = (0,0)
        self.next_dir = (0,0)
        self.power_mode = 0
        self.moving = False

    def set_dir(self,dx,dy):
        self.next_dir = (dx,dy)

    def at_center(self):
        return (
            (self.pixel[0]-OFFSET_X) % TILE == 0
            and (self.pixel[1]-OFFSET_Y) % TILE == 0
        )

    def grid_from_pixel(self):
        return [
            (self.pixel[0]-OFFSET_X)//TILE,
            (self.pixel[1]-OFFSET_Y)//TILE,
        ]

    def can_move(self, game, dx, dy):
        spd = int(self.speed) if not isinstance(self.speed, int) else self.speed
        nx_pixel = self.pixel[0]+dx*spd
        ny_pixel = self.pixel[1]+dy*spd
        corners = [
            (nx_pixel,ny_pixel),
            (nx_pixel+TILE-1,ny_pixel),
            (nx_pixel,ny_pixel+TILE-1),
            (nx_pixel+TILE-1,ny_pixel+TILE-1),
        ]
        for px, py in corners:
            gx=int((px-OFFSET_X)//TILE)
            gy=int((py-OFFSET_Y)//TILE)
            if not game.valid(gx, gy) or game.map[gy][gx] in ("1","D"):
                return False
        return True

    def update(self,game):
        spd = max(1,int(round(self.speed)))

        if self.at_center():
            self.grid=self.grid_from_pixel()
            nx = self.grid[0]+self.next_dir[0]
            ny = self.grid[1]+self.next_dir[1]
            if game.valid(nx,ny) and game.map[ny][nx] not in ("1","D"):
                self.dir = self.next_dir

        current_speed = POWER_SPEED if self.power_mode > 0 else spd
        prev_pixel=self.pixel[:]
        if self.can_move(game, self.dir[0], self.dir[1]):
            self.pixel[0] += self.dir[0]*current_speed
            self.pixel[1] += self.dir[1]*current_speed
        self.moving=(self.pixel!=prev_pixel)

        
        if self.moving:
            self.anim=(self.anim+1) % self.ANIM_CYCLE
        else:
            self.anim = 0

        if self.at_center():
            self.grid = self.grid_from_pixel()
            if self.grid[1] == 13:
                if self.grid[0] <= 0 and self.dir == (-1,0):
                    self.pixel[0] = (MAP_WIDTH-1) * TILE + OFFSET_X
                    self.grid[0] = MAP_WIDTH-1
                elif self.grid[0] >= MAP_WIDTH-1 and self.dir == (1,0):
                    self.pixel[0] = 0 * TILE+OFFSET_X
                    self.grid[0] = 0

        if self.power_mode > 0:
            self.power_mode -= 1
            if self.power_mode == 0:
                _stop(frightened_sound)

    def eat(self,game):
        gx, gy = self.grid
        if not game.valid(gx,gy):
            return
        cell = game.map[gy][gx]
        if cell == "0":
            self.score += 10
            game.map[gy][gx] = " "
            _play(waka_sound)
        elif cell == "P":
            self.score += 50
            game.map[gy][gx] = " "
            self.power_mode = 300
            game.ghosts_eaten_this_power = 0
            _stop(eyes_return_sound)
            _play_loop(frightened_sound)

        if game.fruit and (gx, gy) == game.fruit["pos"]:
            self.score += game.fruit["points"]
            game.fruit_score_display = {
                "text": f"+{game.fruit['points']}",
                "pos": game.fruit["pos"],
                "timer": 90,
            }
            _play(eat_fruit_sound)
            game.fruit = None


GHOST_COLORS=[(255,0,0), (255,128,0), (0,255,255), (255,192,203)]

GHOST_STARTS=[HOUSE_EXIT,(12,13),(14,13),(15,13)]
GHOST_IN_HOUSE=[False,True,True,True]

HOUSE_COLS=range(10,18)
HOUSE_ROWS=range(13,16)


class Ghost:
    def __init__(self, pos, color_id, level=1):
        self.color_id=color_id
        self.color=GHOST_COLORS[color_id % 4]
        self.base_speed=2
        self.level=level
        self.speed=self._level_speed(level)
        self.start_pos=pos
        self.start_in_house=GHOST_IN_HOUSE[color_id]
        self._init_state()

    def _level_speed(self,level):
        return _ghost_speed(level)

    def apply_level(self,level):
        self.level=level
        self.speed=self._level_speed(level)

    def _init_state(self):
        self._place(self.start_pos)
        self.in_house= self.start_in_house
        self.frightened= False
        self.eaten= False
        self.respawning= False
        self.respawn_timer=0
        self.RESPAWN_WAIT=60

        if self.start_in_house:
            self.respawn_timer=0
            self.release_timer=60+self.color_id*60
        else:
            self.respawn_timer=0
            self.release_timer=0

        self.respawn_delay=0
        self.anim=0

    def _place(self,pos):
        self.pixel=[pos[0]*TILE+OFFSET_X,pos[1]*TILE+OFFSET_Y]
        self.grid=list(pos)
        self.dir=(0,0)

    def snap_to_grid(self):
        gx=round((self.pixel[0]-OFFSET_X)/TILE)
        gy=round((self.pixel[1]-OFFSET_Y)/TILE)
        gx=max(0,min(MAP_WIDTH-1,gx))
        gy=max(0,min(MAP_HEIGHT-1,gy))
        self.pixel=[gx*TILE+OFFSET_X,gy*TILE+OFFSET_Y]
        self.grid=[gx,gy]
        self.dir=(0,0)

    def reset(self):
        self._init_state()

    def at_center(self):
        return (
            (self.pixel[0]-OFFSET_X) % TILE == 0
            and (self.pixel[1]-OFFSET_Y) % TILE == 0
        )

    def grid_from_pixel(self):
        return [
            (self.pixel[0]-OFFSET_X)//TILE,
            (self.pixel[1]-OFFSET_Y)//TILE,
        ]

    def _step_toward(self,game,target_grid,house_passable=True):
        astar=AStar(game.map,ghost_house_passable=house_passable)
        came=astar.search(tuple(self.grid), tuple(target_grid))
        path=astar.path(came,tuple(self.grid),tuple(target_grid))
        if path:
            nx,ny=path[0]
            self.dir=(nx-self.grid[0],ny-self.grid[1])
            return True
        return False

    def _try_move(self,game):
        move_speed = max(1, int(round(self.speed)))
        if self.frightened:
            move_speed = FRIGHT_SPEED
        nx_pixel=self.pixel[0]+self.dir[0]*move_speed
        ny_pixel=self.pixel[1]+self.dir[1]*move_speed
        corners = [
            (nx_pixel,ny_pixel),
            (nx_pixel+TILE-1,ny_pixel),
            (nx_pixel,ny_pixel+TILE-1),
            (nx_pixel+TILE-1,ny_pixel+TILE-1),
        ]
        for px,py in corners:
            gx=int((px-OFFSET_X)//TILE)
            gy=int((py-OFFSET_Y)//TILE)
            if not game.valid(gx,gy) or game.map[gy][gx] == "1":
                return
        self.pixel[0] += self.dir[0] * move_speed
        self.pixel[1] += self.dir[1] * move_speed

    def _respawn_step(self, game):
        if self.respawn_delay > 0:
            self.respawn_delay -= 1
            return

        target = HOUSE_CENTER

        if self.at_center():
            self.grid = self.grid_from_pixel()

            if tuple(self.grid) == target:
                self.respawning= False
                self.in_house= True
                self.eaten= False
                self.frightened= False
                self.dir=(0,0)
                self.respawn_timer=self.RESPAWN_WAIT
                self.release_timer=60+self.color_id*60

                if not any(g.eaten and g.respawning for g in game.ghosts if g is not self):
                    _stop(eyes_return_sound)
                return

            self._step_toward(game,target,house_passable=True)

        if self.dir == (0,0):
            return

        if self.dir[0] != 0:
            cur_off=(self.pixel[0]-OFFSET_X) % TILE
            remaining=(-cur_off) % TILE
            if remaining == 0:
                remaining=TILE
        else:
            cur_off=(self.pixel[1]-OFFSET_Y) % TILE
            remaining=(-cur_off) % TILE
            if remaining == 0:
                remaining=TILE

        step=min(RESPAWN_PX, remaining)
        self.pixel[0] += self.dir[0]*step
        self.pixel[1] += self.dir[1]*step

    def _bounce_in_house(self,game):
        if self.at_center():
            self.grid=self.grid_from_pixel()

            candidates=[]
            if self.dir !=(0,0):
                candidates.append(self.dir)
            for d in [(0,-1),(0,1),(1,0),(-1,0)]:
                if d not in candidates:
                    candidates.append(d)

            chosen = None
            for d in candidates:
                nx, ny = self.grid[0] + d[0], self.grid[1] + d[1]
                if not game.valid(nx, ny):
                    continue
                cell = game.map[ny][nx]
                if cell in ("1","D"):
                    continue
                if nx not in HOUSE_COLS or ny not in HOUSE_ROWS:
                    continue
                chosen = d
                break

            if chosen:
                self.dir=chosen
            else:
                self.dir=(-self.dir[0],-self.dir[1])

        self._try_move(game)

    def update(self, game):
        self.anim=(self.anim+1) % 20

        if self.eaten and self.respawning:
            self._respawn_step(game)
            return

        if self.eaten:
            return

        if self.in_house:
            if self.respawn_timer>0:
                self.respawn_timer -= 1
                self._bounce_in_house(game)
                return

            if self.release_timer>0:
                self.release_timer -= 1
                self._bounce_in_house(game)
                return

            self.in_house = False

        if self.at_center():
            self.grid = self.grid_from_pixel()
            target = list(game.player.grid)

            if game.player.power_mode>0:
                best_dist=-1
                best_dir=self.dir
                for mx,my in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx,ny=self.grid[0]+mx,self.grid[1]+my
                    if game.valid(nx, ny) and game.map[ny][nx] != "1":
                        dist=(nx-target[0])**2+(ny-target[1])**2
                        if dist>best_dist:
                            best_dist=dist
                            best_dir=(mx,my)
                self.dir=best_dir
                self.frightened=True
            else:
                self.frightened=False
                self._step_toward(game,target)

        self._try_move(game)


class Game:
    def __init__(self,level=1,score=0,lives=3):
        self.level=level
        self.map=[list(r) for r in RAW_MAP]
        self.player=Player((13, 21))
        self.player.score=score
        self.player.lives=lives
        self.player.apply_level(level)
        self.ghosts = [Ghost(GHOST_STARTS[i], i, level=level) for i in range(4)]
        fs=max(10,TILE-2)
        fs_big=max(14,int(TILE*1.6))
        fs_small=max(8,TILE-6)
        self.font=pygame.font.SysFont("monospace",fs)
        self.font_big=pygame.font.SysFont("monospace",fs_big,bold=True)
        self.font_small=pygame.font.SysFont("monospace",fs_small)
        self.game_over=False
        self.win=False
        self.level_clear_timer=0

        self.frame_counter=0
        self.ready_timer=135
        self.ready_shown=False

        self.fruit=None
        self.fruit_score_display=None
        self._dots_at_start=self.dots_remaining()
        self._fruit_spawned_at={0.75:False,0.50:False}
        self._fruit_spawn_counter = 0

        self.ghosts_eaten_this_power=0
        self.ghost_score_popups=[]
        self.eat_freeze_timer=0

        self.dying=False
        self.die_frame=0
        self.die_timer=0
        self.die_hold_timer=0
        self.DIE_FRAME_TICKS=5
        self.DIE_HOLD_TICKS=30

    def _fruit_type(self):
        idx = min(self.level-1,len(FRUIT_TYPES)-1)
        name,points,color,radius=FRUIT_TYPES[idx]
        return idx,name,points,color,radius

    def _maybe_spawn_fruit(self):
        if self.fruit or not OPEN_CELLS:
            return
        if self._fruit_spawn_counter>0:
            self._fruit_spawn_counter -= 1
            return

        remaining=self.dots_remaining()
        eaten_frac=1.0-remaining/max(1,self._dots_at_start)

        for threshold in [0.25,0.50]:
            key = round(1.0-threshold,2)
            if not self._fruit_spawned_at.get(key,False) and eaten_frac >= threshold:
                self._fruit_spawned_at[key] = True
                idx, name, points, color, radius = self._fruit_type()
                pos = random.choice(OPEN_CELLS)
                self.fruit = {
                    "pos":pos,
                    "points":points+(self.level-1)*50,
                    "color":color,
                    "radius":radius,
                    "name":name,
                    "type_idx":idx,
                    "timer":300,
                }
                self._fruit_spawn_counter=150
                break

    def valid(self,x,y):
        return 0 <= y<len(self.map) and 0 <= x<len(self.map[0])

    def dots_remaining(self):
        return sum(cell in ("0","P") for row in self.map for cell in row)

    def draw(self):
        screen.fill((0,0,0))

        pellet_visible=(self.frame_counter//15) % 2 == 0

        maze_blink=False
        if self.win and self.level_clear_timer>0 and self.level_clear_timer <= 90:
            maze_blink=(self.level_clear_timer//8) % 2 == 0

        wall_dark=(255,255,255) if maze_blink else (0,0,200)
        wall_light=(255,255,255) if maze_blink else (0,0,255)

        for y,row in enumerate(self.map):
            for x,col in enumerate(row):
                px = x*TILE+OFFSET_X
                py = y*TILE+OFFSET_Y
                if col == "1":
                    pygame.draw.rect(screen, wall_dark,(px,py,TILE,TILE))
                    pygame.draw.rect(screen, wall_light,(px+1,py+1,TILE-2,TILE-2))
                elif col == "D":
                    pygame.draw.rect(screen,(180,100,180),(px,py,TILE,TILE))
                    pygame.draw.rect(screen,(220,140,220),(px+1,py+1,TILE-2,TILE-2))
                elif col == "0":
                    pygame.draw.circle(
                        screen, (255,255,200),(px+TILE//2,py+TILE//2),3
                    )
                elif col == "P":
                    if pellet_visible:
                        pygame.draw.circle(
                            screen,(255,220,0),(px+TILE//2,py+TILE//2),6
                        )

        if self.fruit:
            fx,fy=self.fruit["pos"]
            fpx=fx*TILE+OFFSET_X+TILE//2
            fpy=fy*TILE+OFFSET_Y+TILE//2
            fruit_idx=self.fruit.get("type_idx",0)
            fspr=SPR_FRUIT[fruit_idx] if fruit_idx <len(SPR_FRUIT) else None
            if fspr:
                _blit_centered(fspr,fpx,fpy)
            else:
                pygame.draw.circle(screen,self.fruit["color"],(fpx,fpy),
                                   self.fruit["radius"])

        if self.fruit_score_display:
            fsd = self.fruit_score_display
            fsd["timer"] -= 1
            if fsd["timer"]>0:
                fx2,fy2=fsd["pos"]
                popup=self.font.render(fsd["text"],True,(255,220,50))
                offset_y=int((90-fsd["timer"])*0.3)
                screen.blit(popup, (
                    fx2*TILE+OFFSET_X-popup.get_width()//2,
                    fy2*TILE+OFFSET_Y-TILE-offset_y,
                ))
            else:
                self.fruit_score_display=None
        still_alive=[]
        panel_x=OFFSET_X+MAP_WIDTH*TILE+6   
        panel_y=OFFSET_Y+TILE*2               
        line_h=self.font.get_height()+2
        for i,popup in enumerate(self.ghost_score_popups):
            popup["timer"] -= 1
            if popup["timer"]>0:
                alpha=min(255,popup["timer"]*255//20)
                surf=self.font_big.render("+"+popup["text"],True,(100,255,255))
                surf.set_alpha(alpha)
                screen.blit(surf,(panel_x,panel_y+i*line_h))
                still_alive.append(popup)
        self.ghost_score_popups = still_alive

        px=self.player.pixel[0]+TILE//2
        py=self.player.pixel[1]+TILE//2
        pac_dir=self.player.dir

        if self.dying:
            spr=SPR_PAC_DIE[self.die_frame] if self.die_frame<len(SPR_PAC_DIE) else None
            if spr:
                _blit_centered(spr,px,py)
            else:
                r=max(2,(TILE//2-2)*(9-self.die_frame)//9)
                pygame.draw.circle(screen,(255,255,0),(px,py),r)
        else:
            t=self.player.anim
            idle=not self.player.moving
            if idle:
                spr=SPR_PAC_HALF.get(pac_dir) or SPR_PAC_OPEN.get(pac_dir)
            elif t<5:
                spr=SPR_PAC_OPEN.get(pac_dir)
            elif t<8:
                spr=SPR_PAC_HALF.get(pac_dir) or SPR_PAC_OPEN.get(pac_dir)
            else:
                spr=SPR_PAC_CLOSED or SPR_PAC_HALF.get(pac_dir) or SPR_PAC_OPEN.get(pac_dir)
            if spr:
                _blit_centered(spr,px,py)
            else:
                angle_map={(1,0):0,(-1,0):180,(0,-1):90,(0,1):270,(0,0):0}
                base_angle=angle_map.get(pac_dir,0)
                mouth=15 if idle else (30 if t<5 else (15 if t<8 else 0))
                start_a=base_angle+mouth
                end_a=base_angle+360-mouth
                pygame.draw.arc(
                    screen, (255,255,0),
                    (px-TILE//2+2,py-TILE//2+2,TILE-4,TILE-4),
                    np.radians(start_a),np.radians(end_a),TILE//2-2,
                )
                points = [(px, py)]
                for a in range(int(start_a), int(end_a), 5):
                    rad = np.radians(a)
                    points.append((px+int((TILE//2-2)*np.cos(rad)),
                                   py-int((TILE//2-2)*np.sin(rad))))
                if len(points) >= 3:
                    pygame.draw.polygon(screen,(255,255,0),points)

        if not self.dying:
            for g in self.ghosts:
                gx=g.pixel[0]+TILE//2
                gy=g.pixel[1]+TILE//2
                r=TILE//2-2

                if g.eaten and g.respawning:
                    eye_spr=SPR_EYES.get(tuple(g.dir)) or SPR_EYES.get((1,0))
                    if eye_spr:
                        _blit_centered(eye_spr,gx,gy)
                    else:
                        for ex in [gx-r//3,gx+r//3]:
                            pygame.draw.circle(screen,(255,255,255),(ex,gy-2),3)
                            pygame.draw.circle(screen,(0,0,180),(ex,gy-2),2)
                    continue

                if g.eaten:
                    continue

                frame_idx=(g.anim//10) % 2
                g_dir_key=tuple(g.dir) if tuple(g.dir) in _GHOST_DIRS else (1,0)

                if g.frightened:
                    flash=(self.player.power_mode<90 and
                             (self.frame_counter//8) % 2 == 0)
                    walk=SPR_GHOST_WHITE_WALK if flash else SPR_GHOST_BLUE_WALK
                    spr=walk[frame_idx]
                else:
                    walk_dict=SPR_GHOST_WALK[g.color_id % 4]
                    frames=walk_dict.get(g_dir_key) or walk_dict.get((1,0))
                    spr=frames[frame_idx] if frames else None

                if spr:
                    _blit_centered(spr,gx,gy)
                else:
                    color = (0,100,255) if g.frightened else g.color
                    pygame.draw.circle(screen,color,(gx,gy),r)
                    pygame.draw.rect(screen,color,(gx-r,gy,r*2,r))
                    for i in range(3):
                        cx=gx-r+i*(r*2//3)+r//3
                        pygame.draw.circle(screen,(0,0,0),(cx,gy+r),r//3)
                    for ex in [gx-r//3,gx+r//3]:
                        pygame.draw.circle(screen,(255,255,255),(ex,gy-2),3)
                        pygame.draw.circle(screen,(0,0,180),(ex,gy-2),2)

        hud_y=(OFFSET_Y-self.font.get_height())//2
        map_left=OFFSET_X
        map_right=OFFSET_X+MAP_WIDTH*TILE
        map_centre=OFFSET_X + MAP_WIDTH * TILE // 2
        score_surf=self.font.render(f"Score: {self.player.score}",True,(255,255,255))
        lives_surf=self.font.render(f"Lives: {self.player.lives}",True,(255,255,0))
        level_surf=self.font.render(f"Level: {self.level}",True,(100,200,255))
        screen.blit(score_surf,(map_left,hud_y))
        screen.blit(lives_surf,(map_right-lives_surf.get_width(),hud_y))
        screen.blit(level_surf,(map_centre-level_surf.get_width()//2,hud_y))

        if self.game_over:
            msg=self.font_big.render("GAME OVER",True,(255,50,50))
            sub=self.font.render("Press Y to restart",True,(200, 200,200))
            screen.blit(msg,(WIDTH//2-msg.get_width()//2,HEIGHT//2-30))
            screen.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//2+20))

        if self.win and self.level_clear_timer > 0:
            msg=self.font_big.render(f"LEVEL {self.level} CLEAR!",True,(50,255,50))
            sub=self.font.render("Get ready for the next level...", True, (200,255,200))
            screen.blit(msg,(WIDTH//2-msg.get_width()//2,HEIGHT//2-30))
            screen.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//2+20))

        if self.ready_timer>0 and not self.game_over and not self.win:
            cy=HEIGHT//2
            if self.level == 1 and not self.ready_shown:
                p1 =self.font_big.render("PLAYER 1",True,(100,200,255))
                rdy=self.font_big.render("READY!",True,(255,255,0))
                screen.blit(p1,(WIDTH//2-p1.get_width()//2,cy-78))
                screen.blit(rdy,(WIDTH//2-rdy.get_width()//2,cy+18))
            else:
                rdy=self.font_big.render("READY!",True,(255,255,0))
                screen.blit(rdy,(WIDTH//2-rdy.get_width()//2,cy))

def main():
    game = Game(level=1)
    _play(startup_sound)
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    game.player.set_dir(-1,0)
                if e.key == pygame.K_RIGHT:
                    game.player.set_dir(1,0)
                if e.key == pygame.K_UP:
                    game.player.set_dir(0,-1)
                if e.key == pygame.K_DOWN:
                    game.player.set_dir(0,1)
                if e.key == pygame.K_r:
                    game = Game(level=1)
                if e.key == pygame.K_F11:
                    global _is_fullscreen, screen
                    _is_fullscreen = not _is_fullscreen
                    flags = pygame.FULLSCREEN if _is_fullscreen else 0
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

        # Joystick handling
        for joystick in joysticks:
            if joystick.get_button(9):
                pygame.quit()
                sys.exit()
            if joystick.get_button(3):
                game = Game(level=1)
            
            hat_x = joystick.get_hat(0)[0]
            hat_y = joystick.get_hat(0)[1]
            if hat_x == -1:
                game.player.set_dir(-1,0)
            if hat_x == 1:
                game.player.set_dir(1,0)
            if hat_y == -1:
                game.player.set_dir(0,1)
            if hat_y == 1:
                game.player.set_dir(0,-1)

        if game.ready_timer > 0 and not game.game_over and not game.win:
            game.ready_timer -= 1
            if game.ready_timer == 0:
                game.ready_shown = True

        if not game.game_over and not game.win and game.ready_timer <= 0:

            if game.dying:
                if game.die_hold_timer>0:
                    game.die_hold_timer -= 1
                    if game.die_hold_timer == 0:
                        game.dying = False
                        if game.player.lives <= 0:
                            game.game_over = True
                        else:
                            game.player.reset()
                            for ghost in game.ghosts:
                                ghost.reset()
                            game.ready_timer=60
                else:
                    game.die_timer -= 1
                    if game.die_timer <= 0:
                        game.die_frame += 1
                        game.die_timer  = game.DIE_FRAME_TICKS
                        if game.die_frame >= 10:
                            game.die_frame=9
                            game.die_hold_timer = game.DIE_HOLD_TICKS

            elif game.eat_freeze_timer > 0:
                game.eat_freeze_timer -= 1
                for g in game.ghosts:
                    if g.eaten and g.respawning:
                        g.update(game)
            else:
                game.player.update(game)
                game.player.eat(game)

                if game.fruit:
                    game.fruit["timer"] -= 1
                    if game.fruit["timer"] <= 0:
                        game.fruit = None

                game._maybe_spawn_fruit()

                def _collides(g):
                    margin=TILE//4   
                    px0=game.player.pixel[0]+margin
                    py0=game.player.pixel[1]+margin
                    px1=px0+TILE-margin*2
                    py1=py0+TILE-margin*2
                    gx0=g.pixel[0]+margin
                    gy0=g.pixel[1]+margin
                    gx1=gx0+TILE-margin*2
                    gy1=gy0+TILE-margin*2
                    return px0<gx1 and px1>gx0 and py0<gy1 and py1>gy0

                for g in game.ghosts:
                    pre_hit=not g.eaten and _collides(g)
                    g.update(game)
                    post_hit=not g.eaten and _collides(g)
                    if not (pre_hit or post_hit):
                        continue
                    if game.player.power_mode>0:
                        game.ghosts_eaten_this_power += 1
                        points = 200*(2**(game.ghosts_eaten_this_power-1))
                        game.player.score += points
                        _play(eat_ghost_sound)
                        g.eaten=True
                        g.respawning=True
                        g.frightened=False
                        g.snap_to_grid()
                        g.respawn_delay=0
                        game.ghost_score_popups.append({
                            "text":str(points),
                            "px":g.pixel[0]+TILE//2,
                            "py":g.pixel[1]+TILE//2,
                            "timer":60,
                        })
                        game.eat_freeze_timer=45
                        _play(eyes_return_sound)
                        if not any(gh.frightened for gh in game.ghosts):
                            _stop(frightened_sound)
                    else:
                        game.player.lives -= 1
                        _stop(frightened_sound)
                        _stop(eyes_return_sound)
                        for ghost in game.ghosts:
                            ghost.eaten=True
                            ghost.respawning=False
                        game.dying=True
                        game.die_frame=0
                        game.die_timer=game.DIE_FRAME_TICKS
                        game.die_hold_timer=0
                        _play(death_sound)
                        break

                if game.dots_remaining() == 0:
                    game.win=True
                    game.level_clear_timer=120
                    _play(level_up_sound)

        elif game.win and not game.game_over:
            game.level_clear_timer -= 1
            if game.level_clear_timer <= 0:
                next_level = game.level+1
                game = Game(
                    level=next_level,
                    score=game.player.score,
                    lives=game.player.lives,
                )

        game.frame_counter += 1
        game.draw()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
