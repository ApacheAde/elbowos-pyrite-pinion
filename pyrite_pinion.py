#!/usr/bin/env python3
"""Pyrite Pinion — neon gear-ride arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "PYRITE PINION"
HANDLE = "x.com/ElbowOS"
BG = (10, 7, 6)
INK = (255, 244, 220)
GOLD = (255, 196, 64)
COPP = (232, 118, 48)
TEAL = (48, 232, 196)
RUST = (186, 42, 38)
BRNZ = (48, 28, 16)
AMBR = (255, 158, 42)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Gear:
    __slots__ = ("x", "y", "r", "ang", "teeth", "col", "sign")

    def __init__(self, x, y, r, teeth, col, sign):
        self.x, self.y, self.r, self.teeth = x, y, r, teeth
        self.ang, self.col, self.sign = random.random() * math.tau, col, sign


class Nugget:
    __slots__ = ("gi", "th", "kind")

    def __init__(self, gi, th, kind):
        self.gi, self.th, self.kind = gi, th, kind  # kind: 1 gold, -1 rust


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 64)
        self.font_md = pygame.font.Font(None, 46)
        self.font_sm = pygame.font.Font(None, 30)
        self.reset()

    def reset(self) -> None:
        self.score = getattr(self, "score", 0) if getattr(self, "keep_score", False) else 0
        self.keep_score = True
        self.t = 0.0
        self.flash = 0.0
        self.hurt = 0.0
        self.combo = 1
        self.drive = 1.0
        self.sparks: list[Spark] = []
        cols = [GOLD, COPP, TEAL, AMBR]
        specs = [
            (540, 1560, 210, 16, cols[0], 1),
            (360, 1180, 170, 14, cols[1], -1),
            (740, 1120, 150, 12, cols[2], 1),
            (500, 780, 190, 16, cols[3], -1),
            (540, 420, 160, 13, cols[0], 1),
        ]
        self.gears = [Gear(*s) for s in specs]
        self.gi, self.th = 0, -math.pi / 2
        self.nugs: list[Nugget] = []
        self._seed_nugs(10)
        self.stars = [
            [random.uniform(0, W), random.uniform(0, H), random.uniform(0.8, 2.4)]
            for _ in range(70)
        ]

    def _seed_nugs(self, n: int) -> None:
        while len(self.nugs) < n:
            gi = random.randrange(len(self.gears))
            kind = 1 if random.random() < 0.78 else -1
            self.nugs.append(Nugget(gi, random.random() * math.tau, kind))

    def burst(self, x, y, col, n=14) -> None:
        for _ in range(n):
            a = random.random() * math.tau
            spd = random.uniform(80, 460)
            self.sparks.append(
                Spark(x, y, spd * math.cos(a), spd * math.sin(a),
                      random.uniform(0.16, 0.5), col, random.randint(3, 8))
            )

    def _pos(self, gi: int, th: float, pad: float = 18.0):
        g = self.gears[gi]
        rr = g.r + pad
        return g.x + math.cos(th) * rr, g.y + math.sin(th) * rr

    def _nearest_jump(self) -> int | None:
        px, py = self._pos(self.gi, self.th)
        best, bd = None, 1e9
        for i, g in enumerate(self.gears):
            if i == self.gi:
                continue
            d = math.hypot(g.x - px, g.y - py) - g.r
            if 8 < d < 88 and d < bd:
                best, bd = i, d
        return best

    def _jump_to(self, i: int) -> None:
        px, py = self._pos(self.gi, self.th)
        g = self.gears[i]
        self.gi = i
        self.th = math.atan2(py - g.y, px - g.x)

    def autoplay(self) -> None:
        px, py = self._pos(self.gi, self.th)
        gold = [n for n in self.nugs if n.kind == 1]
        if not gold:
            return
        def npt(n):
            return self._pos(n.gi, n.th + self.gears[n.gi].ang, 8)
        tgt = min(gold, key=lambda n: math.hypot(npt(n)[0] - px, npt(n)[1] - py))
        tx, ty = npt(tgt)
        if tgt.gi != self.gi:
            hop = self._nearest_jump()
            if hop is not None and (hop == tgt.gi or random.random() < 0.08):
                self._jump_to(hop)
                return
        g = self.gears[self.gi]
        want = math.atan2(ty - g.y, tx - g.x)
        err = (want - self.th + math.pi) % math.tau - math.pi
        self.drive = 1.0 if err * g.sign > 0 else -1.0

    def update(self, dt: float) -> None:
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.hurt = max(0.0, self.hurt - dt)
        if self.record:
            self.autoplay()
        else:
            keys = pygame.key.get_pressed()
            self.drive = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.drive -= 1.0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.drive += 1.0
            if keys[pygame.K_SPACE]:
                hop = self._nearest_jump()
                if hop is not None:
                    self._jump_to(hop)
        spd = 1.35 + min(1.1, self.score * 0.002)
        for g in self.gears:
            g.ang += self.drive * g.sign * spd * dt * (180 / g.r)
        self.th += self.drive * self.gears[self.gi].sign * spd * dt * (180 / self.gears[self.gi].r)
        px, py = self._pos(self.gi, self.th)
        kept: list[Nugget] = []
        for n in self.nugs:
            nx, ny = self._pos(n.gi, n.th + self.gears[n.gi].ang, 8)
            if math.hypot(nx - px, ny - py) < 42:
                if n.kind > 0:
                    self.score += 12 * self.combo
                    self.combo = min(8, self.combo + 1)
                    self.flash = 0.12
                    self.burst(nx, ny, TEAL if self.gi % 2 else GOLD, 16)
                else:
                    self.combo = 1
                    self.hurt = 0.4
                    self.burst(nx, ny, RUST, 18)
                    self.gi, self.th = 0, -math.pi / 2
                continue
            kept.append(n)
        self.nugs = kept
        self._seed_nugs(9)
        sparks = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sparks.append(sp)
        self.sparks = sparks
        for st in self.stars:
            st[1] += (10 + st[2] * 8) * dt
            if st[1] > H:
                st[1] = -4
                st[0] = random.uniform(0, W)

    def handle(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.keep_score = False
            self.reset()
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
            hop = self._nearest_jump()
            if hop is not None:
                self._jump_to(hop)

    def draw(self, s: pygame.Surface) -> None:
        s.fill(BG)
        pulse = 0.55 + 0.45 * math.sin(self.t * 2.2)
        for i in range(8):
            y = int(160 + i * 210 + math.sin(self.t * 0.6 + i) * 8)
            pygame.draw.line(s, (28 + i, 16, 10), (0, y), (W, y), 2)
        for x, y, r in self.stars:
            pygame.draw.circle(s, (90, 50, 22), (int(x) % W, int(y) % H), int(r))
        for g in self.gears:
            pygame.draw.circle(s, BRNZ, (int(g.x), int(g.y)), int(g.r + 16))
            pygame.draw.circle(s, g.col, (int(g.x), int(g.y)), int(g.r + 16), 5)
            pygame.draw.circle(s, (22, 12, 8), (int(g.x), int(g.y)), int(g.r - 26))
            pygame.draw.circle(s, g.col, (int(g.x), int(g.y)), 18)
            for k in range(g.teeth):
                a = g.ang + k * math.tau / g.teeth
                x0 = g.x + math.cos(a) * (g.r - 8)
                y0 = g.y + math.sin(a) * (g.r - 8)
                x1 = g.x + math.cos(a) * (g.r + 28)
                y1 = g.y + math.sin(a) * (g.r + 28)
                pygame.draw.line(s, g.col, (int(x0), int(y0)), (int(x1), int(y1)), 10)
        for n in self.nugs:
            nx, ny = self._pos(n.gi, n.th + self.gears[n.gi].ang, 8)
            col = GOLD if n.kind > 0 else RUST
            pygame.draw.circle(s, col, (int(nx), int(ny)), 16 if n.kind > 0 else 13)
            pygame.draw.circle(s, INK, (int(nx), int(ny)), 16 if n.kind > 0 else 13, 2)
        px, py = self._pos(self.gi, self.th)
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 196, 64, int(40 * pulse)), (int(px), int(py)), 54)
        s.blit(glow, (0, 0))
        pygame.draw.circle(s, INK, (int(px), int(py)), 22)
        pygame.draw.circle(s, TEAL, (int(px), int(py)), 16)
        hop = self._nearest_jump()
        if hop is not None:
            pygame.draw.circle(s, TEAL, (int(self.gears[hop].x), int(self.gears[hop].y)), 26, 2)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        if self.flash > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((255, 210, 80, int(48 * self.flash / 0.12)))
            s.blit(fl, (0, 0))
        if self.hurt > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((200, 30, 20, int(46 * self.hurt / 0.4)))
            s.blit(fl, (0, 0))
        title = self.font_lg.render(TITLE, True, GOLD)
        s.blit(title, title.get_rect(center=(W // 2, 58)))
        handle = self.font_sm.render(HANDLE, True, TEAL)
        s.blit(handle, handle.get_rect(center=(W // 2, 108)))
        hud = self.font_md.render(f"SCORE  {self.score}    x{self.combo}", True, AMBR)
        s.blit(hud, hud.get_rect(center=(W // 2, 158)))
        hint = self.font_sm.render("A / D spin gears   SPACE hop   R reset   x.com/ElbowOS", True, INK)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/PYRITE_PINION_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
