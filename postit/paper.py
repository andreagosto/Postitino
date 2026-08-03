import math
import random

import cairo

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_foreign("cairo")
except ImportError:
    from .lang import tr

    print(tr("missing_gi_cairo"))
    raise
from gi.repository import Gtk

# color_name -> (light, dark) for a soft paper gradient
COLORS = {
    "yellow": ("#fff59d", "#f0dc62"),
    "pink": ("#ffd6e0", "#ffa9c3"),
    "blue": ("#d6ecff", "#a4d0ff"),
    "green": ("#d9f7cf", "#a8df96"),
    "white": ("#ffffff", "#e6e6e6"),
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def make_points(x, y, w, h, rng, jitter):
    """Irregular, hand-cut paper outline (closed list of points)."""
    n = 6

    def j():
        return rng.uniform(-jitter, jitter)

    def snip():
        return -abs(j())

    top = [(x + w * (i / n), y + j()) for i in range(n + 1)]
    right = [(x + w + j(), y + h * (i / n)) for i in range(1, n + 1)]
    bottom = [(x + w * (i / n), y + h + j()) for i in range(n - 1, -1, -1)]
    left = [(x + j(), y + h * (i / n)) for i in range(n - 1, 0, -1)]

    pts = top + right + bottom + left
    # slightly truncated corners -> "torn" paper look
    pts[0] = (x + snip(), y + snip())
    pts[n] = (x + w - abs(j()), y + snip())
    pts[2 * n] = (x + w - abs(j()), y + h - abs(j()))
    pts[3 * n] = (x + snip(), y + h - abs(j()))
    return pts


def trace_path(cr, pts):
    cr.move_to(*pts[0])
    for p in pts[1:]:
        cr.line_to(*p)
    cr.close_path()


class PostItPaper(Gtk.Box):
    def __init__(self, seed, color="yellow", rotation=0.0):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_name("postit-paper")
        self.seed = seed
        self.color = color
        self.rotation = math.radians(rotation)
        self.connect("draw", self.on_draw)

    def on_draw(self, widget, cr):
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height
        margin = 12.0
        rng = random.Random(self.seed)  # deterministic per note -> stable edges

        cr.save()
        cr.translate(w / 2, h / 2)
        cr.rotate(self.rotation)
        cr.translate(-w / 2, -h / 2)

        pw, ph = w - 2 * margin, h - 2 * margin
        x, y = margin, margin
        jitter = max(1.2, min(3.5, min(pw, ph) * 0.012))
        pts = make_points(x, y, pw, ph, rng, jitter)

        # soft drop shadow (multiple offset fills)
        for dx, dy, a in ((3, 4, 0.10), (1.5, 2, 0.08), (0.5, 1, 0.05)):
            cr.save()
            cr.translate(dx, dy)
            trace_path(cr, pts)
            cr.set_source_rgba(0, 0, 0, a)
            cr.fill()
            cr.restore()

        # paper gradient
        light, dark = COLORS.get(self.color, COLORS["yellow"])
        r1, g1, b1 = hex_to_rgb(light)
        r2, g2, b2 = hex_to_rgb(dark)
        grad = cairo.LinearGradient(x, y, x + pw, y + ph)
        grad.add_color_stop_rgb(0, r1, g1, b1)
        grad.add_color_stop_rgb(1, r2, g2, b2)
        trace_path(cr, pts)
        cr.set_source(grad)
        cr.fill()

        # faint edge
        trace_path(cr, pts)
        cr.set_source_rgba(0, 0, 0, 0.06)
        cr.set_line_width(1.2)
        cr.stroke()

        self._draw_tape(cr, x, y, pw, rng)
        cr.restore()
        return False

    def _draw_tape(self, cr, x, y, pw, rng):
        tw, th = 64.0, 26.0
        cx = x + pw / 2 + rng.uniform(-12, 12)
        cy = y + 2
        r = 4.0
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(math.radians(rng.uniform(-8, 8)))
        cr.new_path()
        cr.arc(-tw / 2 + r, -th / 2 + r, r, math.pi, 1.5 * math.pi)
        cr.arc(tw / 2 - r, -th / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
        cr.arc(tw / 2 - r, th / 2 - r, r, 0, 0.5 * math.pi)
        cr.arc(-tw / 2 + r, th / 2 - r, r, 0.5 * math.pi, math.pi)
        cr.close_path()
        cr.set_source_rgba(1, 1, 1, 0.55)
        cr.fill()
        cr.set_source_rgba(0, 0, 0, 0.06)
        cr.set_line_width(1.0)
        cr.stroke()
        cr.restore()
