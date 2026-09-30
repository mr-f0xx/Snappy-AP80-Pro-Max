#!/usr/bin/env python3
"""
Generates the 1-bit BMP sprites used by the tactile controls, the progress
bar, the USB/charging gauge and the peak-meter mask.

Rockbox maps black pixels to the theme foreground and white pixels to the
theme background, so every sprite follows the theme colours automatically.

    python3 tools/gen_assets.py [--boxed]   (needs Pillow)

Output goes to .rockbox/wps/Snappy/
"""
import os, sys
from PIL import Image, ImageDraw

OUT = os.environ.get('ASSET_OUT') or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..',
    '.rockbox', 'wps', 'Snappy')
FLAT = '--boxed' not in sys.argv   # borderless keys (icon only); --boxed = raised keys
INK, BG = 0, 255        # black = theme foreground, white = theme background
SH = 3                  # depth of the "raised" shadow


def canvas(w, h, fill=BG):
    return Image.new('1', (w, h), fill)


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path, format='BMP')
    return path


def stack(frames):
    w, h = frames[0].size
    out = canvas(w, h * len(frames))
    for i, f in enumerate(frames):
        assert f.size == (w, h), (f.size, (w, h))
        out.paste(f, (0, i * h))
    return out


# ---------------------------------------------------------------- glyphs --
def g_tri(w, h, right=True):
    g = canvas(w, h)
    d = ImageDraw.Draw(g)
    for y in range(h):
        span = 1 - abs(2 * y + 1 - h) / h
        n = max(1, round(w * span))
        if right:
            d.line([(0, y), (n - 1, y)], fill=INK)
        else:
            d.line([(w - n, y), (w - 1, y)], fill=INK)
    return g


def g_play():
    return g_tri(13, 16, True)


def g_pause():
    g = canvas(14, 16)
    d = ImageDraw.Draw(g)
    d.rectangle((0, 0, 4, 15), fill=INK)
    d.rectangle((9, 0, 13, 15), fill=INK)
    return g


def g_prev():
    g = canvas(21, 14)
    d = ImageDraw.Draw(g)
    d.rectangle((0, 0, 2, 13), fill=INK)
    for off in (4, 12):
        for y in range(14):
            span = 1 - abs(2 * y + 1 - 14) / 14
            n = max(1, round(9 * span))
            d.line([(off + 9 - n, y), (off + 8, y)], fill=INK)
    return g


def g_next():
    return g_prev().transpose(Image.FLIP_LEFT_RIGHT)


def head_right(d, tip_x, cy, half):
    """solid arrow head pointing right, tip column tip_x, centred on row cy
    (cy may be x.5 -> pass the upper of the two centre rows and half=n rows
    above/below incl.). Drawn column by column."""
    for i in range(half + 1):
        x = tip_x - i
        d.line([(x, cy - i), (x, cy + 1 + i)], fill=INK)


def sq(d, x, y, n=2):
    d.rectangle((x, y, x + n - 1, y + n - 1), fill=INK)


def g_shuffle():
    W, H = 22, 17
    g = canvas(W, H)
    d = ImageDraw.Draw(g)
    ya, yb = 3, 12                      # centre rows (upper of 2) of the paths
    x0, x1 = 6, 14                      # 45 degree section spans x0..x1
    # path A: top-left -> bottom-right
    d.rectangle((0, ya, x0, ya + 1), fill=INK)
    for i in range(yb - ya + 1):
        sq(d, x0 + i, ya + i)
    d.rectangle((x0 + (yb - ya), yb, 15, yb + 1), fill=INK)
    # path B: bottom-left -> top-right, drawn "over" A with a 1px halo
    halo = []
    for i in range(yb - ya + 1):
        halo.append((x0 + i, yb - i))
    for (x, y) in halo:
        d.rectangle((x - 1, y - 1, x + 2, y + 2), fill=BG)
    d.rectangle((0, yb, x0, yb + 1), fill=INK)
    for (x, y) in halo:
        sq(d, x, y)
    d.rectangle((x0 + (yb - ya), ya, 15, ya + 1), fill=INK)
    # arrow heads
    head_right(d, 21, ya, 3)
    head_right(d, 21, yb, 3)
    return g


def g_repeat(one=False):
    W, H = 22, 18
    g = canvas(W, H)
    d = ImageDraw.Draw(g)
    top = Image.new('1', (W, H), BG)
    t = ImageDraw.Draw(top)
    t.rectangle((0, 3, 15, 4), fill=INK)       # top edge
    head_right(t, 19, 3, 3)                    # arrow head, tip at x=19
    t.rectangle((20, 3, 21, 14), fill=INK)     # right side
    rot = top.transpose(Image.ROTATE_180)
    # union of the two halves (ink = 0 -> use min)
    a, b = top.load(), rot.load()
    gp = g.load()
    for y in range(H):
        for x in range(W):
            if a[x, y] == INK or b[x, y] == INK:
                gp[x, y] = INK
    if one:
        for r, row in enumerate(("..#.", ".##.", "..#.", "..#.", "..#.", ".###")):
            for c, ch in enumerate(row):
                if ch == '#':
                    gp[9 + c, 6 + r] = INK
    return g


FONT5x7 = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'N': ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    '-': ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
}


def g_text(s, scale=1, gap=1):
    cw, ch = 5, 7
    w = len(s) * cw + (len(s) - 1) * gap
    g = canvas(w * scale, ch * scale)
    d = ImageDraw.Draw(g)
    x = 0
    for c in s:
        for yy, row in enumerate(FONT5x7[c]):
            for xx, bit in enumerate(row):
                if bit == '1':
                    d.rectangle(((x + xx) * scale, yy * scale,
                                 (x + xx + 1) * scale - 1, (yy + 1) * scale - 1), fill=INK)
        x += cw + gap
    return g


# --------------------------------------------------------------- buttons --
def glyph_onto(img, glyph, box, ink):
    """centre `glyph` (ink pixels) inside box=(x0,y0,x1,y1); ink True=draw ink"""
    x0, y0, x1, y1 = box
    gw, gh = glyph.size
    ox = x0 + (x1 - x0 + 1 - gw) // 2
    oy = y0 + (y1 - y0 + 1 - gh) // 2
    px = glyph.load()
    ip = img.load()
    for y in range(gh):
        for x in range(gw):
            if px[x, y] == INK:
                ip[ox + x, oy + y] = INK if ink else BG


def button(W, H, glyph, filled=False, pressed=False):
    """raised key. Not pressed: body at 0,0 with a dithered shadow on the
    right/bottom edge. Pressed: body sits 'down' on the shadow (shadow gone)."""
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    bw, bh = W - SH, H - SH
    off = SH if pressed else 0
    if not pressed:
        ip = img.load()
        for y in range(SH, H):
            for x in range(SH, W):
                inside_body = (x < bw and y < bh)
                if not inside_body and (x + y) % 2 == 0:
                    ip[x, y] = INK
    body = (off, off, off + bw - 1, off + bh - 1)
    d.rectangle(body, fill=INK if filled else BG)
    if not filled:
        d.rectangle(body, outline=INK)
        d.rectangle((body[0] + 1, body[1] + 1, body[2] - 1, body[3] - 1), outline=INK)
    if glyph is not None:
        glyph_onto(img, glyph, body, ink=not filled)
    return img


def dither(img, box, phase=0):
    ip = img.load()
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x + y + phase) % 2 == 0:
                ip[x, y] = INK


def pressed_soft(W, H, glyph, filled):
    """pressed look for a *toggle* that is currently off (outlined): the body
    gets a 50% dither so it reads as 'being pushed'. For a lit toggle the
    pressed look is simply the filled key moved down."""
    img = button(W, H, None, filled=False, pressed=True)
    bw, bh = W - SH, H - SH
    dither(img, (SH + 2, SH + 2, SH + bw - 3, SH + bh - 3))
    # solid plate behind glyph so it stays readable
    gw, gh = glyph.size
    ox = SH + (bw - gw) // 2
    oy = SH + (bh - gh) // 2
    d = ImageDraw.Draw(img)
    d.rectangle((ox - 2, oy - 2, ox + gw + 1, oy + gh + 1), fill=BG)
    glyph_onto(img, glyph, (SH, SH, SH + bw - 1, SH + bh - 1), ink=True)
    return img


BH = 33   # button sprite height (30 body + 3 shadow)


def scaled(g, num, den):
    w, h = g.size
    return g.resize((w * num // den, h * num // den), Image.NEAREST)


def flat_key(W, H, glyph, lit=False, pressed=False):
    """borderless key: just the icon. A lit toggle gets an underline marker,
    a pressed key flashes as an inverted block."""
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    if pressed:
        d.rectangle((3, 2, W - 4, H - 3), fill=INK)
        glyph_onto(img, glyph, (0, 0, W - 1, H - 1), ink=False)
        return img
    glyph_onto(img, glyph, (0, 0, W - 1, H - 7 if lit else H - 1), ink=True)
    if lit:
        bx = (W - 18) // 2
        d.rectangle((bx, H - 6, bx + 17, H - 5), fill=INK)
    return img


def build_buttons_flat():
    W, H = 52, BH
    wide = 59
    for k, g in (('prev', g_prev()), ('next', g_next())):
        save(stack([flat_key(wide, H, g), flat_key(wide, H, g, pressed=True)]),
             'btn_%s.bmp' % k)
    gp, gq = scaled(g_play(), 5, 4), scaled(g_pause(), 5, 4)
    save(stack([flat_key(69, H, gp), flat_key(69, H, gp, pressed=True),
                flat_key(69, H, gq), flat_key(69, H, gq, pressed=True)]),
         'btn_play.bmp')
    g = g_shuffle()
    save(stack([flat_key(W, H, g), flat_key(W, H, g, pressed=True),
                flat_key(W, H, g, lit=True), flat_key(W, H, g, pressed=True)]),
         'btn_shf.bmp')
    frames = []
    for g, lit in [(g_repeat(False), False), (g_repeat(False), True),
                   (g_repeat(True), True), (g_text('RND', 1), True),
                   (g_text('A-B', 1), True)]:
        frames += [flat_key(W, H, g, lit=lit), flat_key(W, H, g, pressed=True)]
    save(stack(frames), 'btn_rpt.bmp')


def build_buttons():
    if FLAT:
        return build_buttons_flat()
    widths = dict(shf=52, prev=59, play=69, next=59, rpt=52)
    # prev / next: outline, pressed = filled
    for k, g in (('prev', g_prev()), ('next', g_next())):
        W = widths[k]
        save(stack([button(W, BH, g), button(W, BH, g, filled=True, pressed=True)]),
             'btn_%s.bmp' % k)
    # play/pause (hero key): filled when idle, outline when pressed
    W = widths['play']
    save(stack([
        button(W, BH, g_play(), filled=True),
        button(W, BH, g_play(), filled=False, pressed=True),
        button(W, BH, g_pause(), filled=True),
        button(W, BH, g_pause(), filled=False, pressed=True),
    ]), 'btn_play.bmp')
    # shuffle: off / off pressed / on / on pressed
    W = widths['shf']
    g = g_shuffle()
    save(stack([
        button(W, BH, g),
        pressed_soft(W, BH, g, False),
        button(W, BH, g, filled=True),
        button(W, BH, g, filled=True, pressed=True),
    ]), 'btn_shf.bmp')
    # repeat: off, all, one, rnd(shuffle), a-b  (each: idle, pressed)
    W = widths['rpt']
    frames = []
    glyphs = [(g_repeat(False), False), (g_repeat(False), True), (g_repeat(True), True),
              (g_text('RND', 1), True), (g_text('A-B', 1), True)]
    for g, lit in glyphs:
        if lit:
            frames += [button(W, BH, g, filled=True), button(W, BH, g, filled=True, pressed=True)]
        else:
            frames += [button(W, BH, g), pressed_soft(W, BH, g, False)]
    save(stack(frames), 'btn_rpt.bmp')


# ---------------------------------------------------- footer (menu) key --
FW, FH = 42, 38


def build_footer_button():
    frames = []
    if FLAT:
        for g in (g_pause(), g_play()):
            frames += [flat_key(FW, FH, g), flat_key(FW, FH, g, pressed=True)]
        return save(stack(frames), 'ftr_play.bmp')
    for g in (g_pause(), g_play()):
        frames += [button(FW, FH, g, filled=True),
                   button(FW, FH, g, filled=False, pressed=True)]
    save(stack(frames), 'ftr_play.bmp')


# ---------------------------------------------------------- progress bar --
PBW, PBH = 315, 27          # bar area
KW = 21                     # knob sprite width
TRACK_Y0, TRACK_H = 9, 9    # track band inside the bar area


def build_progress():
    # empty track (backdrop): 2px rails, end caps, dotted groove
    t = canvas(PBW, PBH)
    d = ImageDraw.Draw(t)
    y0, y1 = TRACK_Y0, TRACK_Y0 + TRACK_H - 1
    d.rectangle((0, y0, PBW - 1, y0 + 1), fill=INK)
    d.rectangle((0, y1 - 1, PBW - 1, y1), fill=INK)
    d.rectangle((0, y0, 1, y1), fill=INK)
    d.rectangle((PBW - 2, y0, PBW - 1, y1), fill=INK)
    ip = t.load()
    for y in range(y0 + 2, y1 - 1):
        for x in range(3, PBW - 3):
            if (x % 4 == 1) and ((y - y0) % 2 == 0):
                ip[x, y] = INK
    save(t, 'pbt_track.bmp')
    # elapsed part (fill): solid band, same height as the rails
    f = canvas(PBW - KW, PBH)
    d = ImageDraw.Draw(f)
    d.rectangle((0, y0, PBW - KW - 1, y1), fill=INK)
    save(f, 'pbt_fill.bmp')
    # knob: [idle, pressed]
    kh = PBH
    halo = 2
    bw, bh = 14, 19
    for pressed in (False, True):
        k = canvas(KW, kh)
        d = ImageDraw.Draw(k)
        ox = halo + (SH if pressed else 0)
        oy = halo + (SH if pressed else 0)
        oy -= 1
        if not pressed:
            ip = k.load()
            for y in range(oy + SH, oy + bh + SH):
                for x in range(ox + SH, ox + bw + SH):
                    inside = (x < ox + bw and y < oy + bh)
                    if not inside and (x + y) % 2 == 0:
                        ip[x, y] = INK
        body = (ox, oy, ox + bw - 1, oy + bh - 1)
        if pressed:
            d.rectangle(body, fill=INK)
            grip = BG
        else:
            d.rectangle(body, fill=BG)
            d.rectangle(body, outline=INK)
            d.rectangle((body[0] + 1, body[1] + 1, body[2] - 1, body[3] - 1), outline=INK)
            grip = INK
        # three grip ridges
        cx = ox + bw // 2
        for gx in (cx - 3, cx, cx + 3):
            d.line([(gx, oy + 5), (gx, oy + bh - 6)], fill=grip)
        save(k, 'pbt_knob_p.bmp' if pressed else 'pbt_knob.bmp')


# ---------------------------------------------------------- peak-meter --
def build_pm_mask():
    # plain background: hides the scale-mark dots the firmware paints in the
    # 3px gap between the left and right bars of %pm
    save(canvas(128, 3), 'pm_mask.bmp')


# ----------------------------------------------------------- USB screen --
GW, GH = 315, 40
CELLS = 10
GAP = 3


def cell_bounds():
    total = GW - GAP * (CELLS - 1)
    base, extra = divmod(total, CELLS)
    x = 0
    out = []
    for i in range(CELLS):
        w = base + (1 if i >= CELLS - extra else 0) if extra else base
        out.append((x, x + w - 1))
        x += w + GAP
    return out


def build_gauge():
    cells = cell_bounds()
    back = canvas(GW, GH)
    fill = canvas(GW, GH)
    db, df = ImageDraw.Draw(back), ImageDraw.Draw(fill)
    bp = back.load()
    for x0, x1 in cells:
        db.rectangle((x0, 0, x1, GH - 1), outline=INK)
        db.rectangle((x0 + 1, 1, x1 - 1, GH - 2), outline=INK)
        for y in range(3, GH - 3):
            for x in range(x0 + 2, x1 - 1):
                if (x + y) % 4 == 0:
                    bp[x, y] = INK
        df.rectangle((x0, 0, x1, GH - 1), fill=INK)
    save(back, 'chg_back.bmp')
    save(fill, 'chg_fill.bmp')


def build_usb_icons():
    src = Image.open(os.path.join(OUT, 'usb.bmp')).convert('1')
    # 2x version of the plain icon for the USB screen's eject section
    save(src.resize((src.width * 2, src.height * 2), Image.NEAREST).convert('1'),
         'usb_big.bmp')


if __name__ == '__main__':
    build_buttons()
    build_footer_button()
    build_progress()
    build_pm_mask()
    build_gauge()
    build_usb_icons()
    print('ok')
