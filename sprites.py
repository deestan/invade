import random

import pyglet
from pyglet.window import key

class _Shield(object):
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.sprites = [
            None,
            pyglet.resource.image('shield_dam02.png'),
            pyglet.resource.image('shield_dam01.png'),
            pyglet.resource.image('shield_full.png'),
            pyglet.resource.image('shield_nw.png'),
            pyglet.resource.image('shield_ne.png'),
            ]
        self.states = [
            [0, 4, 3, 3, 3, 3, 5, 0],
            [4, 3, 3, 3, 3, 3, 3, 5],
            [3, 3, 0, 0, 0, 0, 3, 3],
            [3, 3, 0, 0, 0, 0, 3, 3],
            ]
        self.IW = self.sprites[3].width
        self.IH = self.sprites[3].height
        self.RC = range(len(self.states))
        self.CC = range(len(self.states[0]))
        self.width = len(self.states[0]) * self.IW
    def update(self):
        pass
    def paint(self):
        for s_r in self.RC:
            for s_c in self.CC:
                s = self.sprites[self.states[s_r][s_c]]
                x = self.x + s_c * self.IW
                y = self.y - s_r * self.IH
                if s: s.blit(x, y)
    def absorb(self, (xl, yl, xh, yh)):
        x = (xl + xh) / 2
        for r in self.RC:
            ry = self.y - r * self.IH
            if yl >= ry + self.IH: continue
            if yh < ry: continue
            for c in self.CC:
                cx = self.x + c * self.IW
                if not self.states[r][c]: continue
                if x < cx: continue
                if x >= cx + self.IW: continue
                s = self.states[r][c]
                self.states[r][c] = min(3, s) - 1
                return True
        
        
class Shields(object):
    def __init__(self, window):
        sw = _Shield(0, 0).width
        pad = 128
        num = 4
        y = 96
        i_pad = (window.width - 2 * pad - sw) / (num-1)
        self.subs = [_Shield(pad + i_pad*i_x, y)
                     for i_x in range(4)]
    def absorb(self, bounds):
        for s in self.subs:
            if s.absorb(bounds):
                return True
        return False
    def update(self):
        pass
    def paint(self):
        for s in self.subs:
            s.paint()

class Player(object):
    def __init__(self, window, gun, keys):
        self.w = window
        self.g = gun
        self.s = pyglet.resource.image('player.png')
        self.x, self.y = self.w.width/2, 4
        self.keys = keys
    def update(self):
        vx = 0
        if self.keys[key.LEFT]: vx -= 10
        if self.keys[key.RIGHT]: vx += 10
        self.x += vx
        self.x = max(self.x, 0)
        self.x = min(self.x, self.w.width - self.s.width)
        if self.keys[key.SPACE]: self._pewpew()
    def paint(self):
        self.s.blit(self.x, self.y)
    def _pewpew(self):
        self.g.fire(self.x + (self.s.width/2), self.y + self.s.height)

class Gun(object):
    def __init__(self, window, invaders):
        self.w = window
        self.i = invaders
        self.s = pyglet.resource.image('pewpew.png')
        self.cx, self.cy = self.s.width/2, 0
        self.x, self.y = 0, 0
        self.firing = False
    def bounds(self):
        if not self.firing:
            return None
        return self.x, self.y, self.x + self.s.width, self.y + self.s.height
    def fire(self, x, y):
        if self.firing: return
        self.x = x - self.cx
        self.y = y - self.cy
        self.firing = True
    def die(self):
        self.firing = False
    def update(self):
        if not self.firing: return
        self.y += 15
        if self.y > self.w.height:
            self.firing = False
            return
        if self.i.collide(self.x, self.y, self.s.width, self.s.height):
            self.firing = False
    def paint(self):
        if not self.firing: return
        self.s.blit(self.x, self.y)

class InvaderExplode(object):
    def __init__(self):
        s = [pyglet.resource.image('invaderexplode0.png'),
             pyglet.resource.image('invaderexplode1.png')]
        self.x, self.y = 0, 0
        self.sm = {'inactive': {'d': 0, 'next': None, 's': None},
                   'explode0': {'d': 5, 'next': 'explode1', 's': s[0]},
                   'explode1': {'d': 10, 'next': 'inactive', 's': s[1]}}
        self.st = 'inactive'
        self.st_c = 0
    def trans(self, state):
        self.st = state
        self.st_c = self.sm[state]['d']
    def boom(self, x, y):
        self.x, self.y = x, y
        self.trans('explode0')
    def paint(self):
        s = self.sm[self.st]['s']
        if not s: return
        s.blit(self.x, self.y)
    def update(self):
        if not self.st_c: return
        self.st_c -= 1
        if self.st_c: return
        self.trans(self.sm[self.st]['next'])

class InvaderZap(object):
    def __init__(self, window, shields):
        self.w = window
        self.s = pyglet.resource.image('zapzap.png')
        self.cx, self.cy = self.s.width/2, 0
        self.xyl = []
        self.wh = (self.s.width, self.s.height)
        self.shields = shields
    def fire(self, x, y):
        self.xyl.append([x - self.cx, y - self.cy])
    def update(self):
        xyl2 = []
        for p in self.xyl:
            p[1] -= 10
            bounds = (p[0], p[1], p[0]+self.s.width, p[1]+self.s.height)
            if self.shields.absorb(bounds): continue
            if p[1] <= 0: continue
            xyl2.append(p)
        self.xyl = xyl2
    def paint(self):
        for [x, y] in self.xyl:
            self.s.blit(x, y)

class Invaders(object):
    def __init__(self, window, zap, invadersExp):
        self.explode = invadersExp
        self.ROWS = 6
        self.COLS = 8
        self.zap = zap
        self.w = window
        self.invader0 = [
            pyglet.resource.image('invader01.png'),
            pyglet.resource.image('invader02.png')]
        self.iw, self.ih = self.invader0[0].width, self.invader0[0].height
        self.pad = 16
        self.x = 2 * self.pad
        self.y = self.w.height - (self.ih + 2 * self.pad)
        self.il = [[True]*self.COLS for _ in [None]*self.ROWS]
        self.bipbop = 0
        self.bipcnt = 0
        self.zapcnt = 100
        self.vx = self.iw/4
        self.vy = -self.ih
        self.calcWidth()

    def collide(self, xl, yl, w, h):
        xh, yh = xl + w, yl + h
        for i_r in xrange(self.ROWS):
            i_yl = self.y - (self.ih + self.pad) * i_r
            i_yh = i_yl + self.ih
            if yh < i_yl: continue
            if yl > i_yh: continue
            for i_c in xrange(self.COLS):
                i_xl = self. x + (self.iw + self.pad) * i_c
                i_xh = i_xl + self.iw
                if xh < i_xl: continue
                if xl > i_xh: continue
                if self.il[i_r][i_c]:
                    self.il[i_r][i_c] = False
                    self.explode.boom(i_xl, i_yl)
                    self.reduceSizeIfNeeded()
                    return True
        return False

    def reduceSizeIfNeeded(self):
        if not self.COLS: return
        for i_c in [0, -1]:
            if not sum([self.il[i_r][i_c]
                        for i_r in range(self.ROWS)]):
                self.stripCol(i_c)
                self.reduceSizeIfNeeded()

    def stripCol(self, i_c):
        self.COLS -= 1
        for r in self.il:
            r.pop(i_c)
        if i_c == 0:
            self.x += self.iw + self.pad
        self.calcWidth()

    def calcWidth(self):
        self.totWidth = len(self.il[0]) * (self.iw + self.pad) - self.pad

    def getBottomOfRandomRow(self):
        candidates = []
        for i_c in xrange(self.COLS):
            for i_r in xrange(self.ROWS-1, -1, -1):
                if self.il[i_r][i_c]:
                    candidates.append((i_r, i_c))
                    break
        if not candidates:
            return None, None
        r, c = random.choice(candidates)
        x, y = self.pos(r, c)
        x += self.invader0[0].width / 2
        return x, y

    def update(self):
        self.bipcnt = (self.bipcnt + 1)%20
        if self.bipcnt == 0:
            self.bipbop = (self.bipbop + 1)%2
            self.x += self.vx
            if (self.x + self.totWidth > self.w.width) or (self.x < 0):
                self.vx *= -1
                self.x += self.vx
                self.y += self.vy
        self.zapcnt -= 1
        if self.zapcnt == 0:
            self.zapcnt = random.randrange(10, 120)
            x, y = self.getBottomOfRandomRow()
            if x != None:
                self.zap.fire(x, y)

    def pos(self, r, c):
        return (self.x + c*(self.iw + self.pad),
                self.y - r*(self.ih + self.pad))

    def paint(self):
        def paintOne(row, col):
            x, y = self.pos(row, col)
            s = self.invader0[self.bipbop]
            s.blit(x, y)
        for ir in xrange(len(self.il)):
            row = self.il[ir]
            for ic in xrange(len(row)):
                row[ic] and paintOne(ir, ic)
