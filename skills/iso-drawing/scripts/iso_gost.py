# -*- coding: utf-8 -*-
"""Прямоугольная изометрия по ГОСТ 2.317 на листе А4 — библиотека для Hermes.

Проекция: приведённые коэффициенты искажения =1 (ГОСТ 2.317). Горизонтальная
окружность Ø d проецируется в эллипс с большой осью 1,22 d (горизонтальной) и
малой 0,71 d — проверено аналитически (см. вывод в SKILL.md).

Оси: X вправо-вниз под 30° к горизонту, Y влево-вниз под 30°, Z вертикально.
u = (x − y)·cos30°,  v = z − (x + y)·sin30°.  Наблюдатель видит сверху, спереди
(грань −Y) и справа (грань +X).

Принципы чистого чертежа (зашиты в примитивы):
- окружности — ТОЛЬКО эллипсы (параметрически), никогда не круг;
- перекрытие тел «алгоритмом художника»: тело заливается белым и рисуется
  поверх более дальних → невидимый контур не виден (его не рисуем вовсе,
  ГОСТ 2.317 это разрешает — так чище);
- штрихи линий по ГОСТ 2.303 (основная s, тонкая s/3, осевая штрихпунктирная);
- размеры и выноски по ГОСТ 2.307.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

COS30 = math.cos(math.radians(30))
SIN30 = 0.5

PT = 72 / 25.4
LW_MAIN = 0.7 * PT
LW_THIN = 0.25 * PT


def iso(p):
    x, y, z = p
    return ((x - y) * COS30, z - (x + y) * SIN30)


def project(pts3, dx=0.0, dy=0.0):
    return [(iso(p)[0] + dx, iso(p)[1] + dy) for p in pts3]


def circle3(center, r, plane="xy", t0=0.0, t1=360.0, n=120):
    """Окружность/дуга в координатной плоскости → 3D точки. t в градусах."""
    cx, cy, cz = center
    pts = []
    steps = max(2, n)
    for i in range(steps + 1):
        t = math.radians(t0 + (t1 - t0) * i / steps)
        c, s = math.cos(t), math.sin(t)
        if plane == "xy":
            pts.append((cx + r * c, cy + r * s, cz))
        elif plane == "xz":
            pts.append((cx + r * c, cy, cz + r * s))
        else:  # yz
            pts.append((cx, cy + r * c, cz + r * s))
    return pts


def convex_hull(points):
    pts = sorted(set((round(p[0], 4), round(p[1], 4)) for p in points))
    if len(pts) <= 2:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


@dataclass
class Sheet:
    title: str = ""
    subtitle: str = ""
    designer: str = "Hermes"
    date: str = ""
    scale: str = "1:1"
    fig: object = field(default=None, repr=False)
    ax: object = field(default=None, repr=False)
    _z: float = 10.0

    def __post_init__(self):
        self.fig = plt.figure(figsize=(210 / 25.4, 297 / 25.4), dpi=200)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 210)
        self.ax.set_ylim(0, 297)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    def next_layer(self) -> float:
        self._z += 4.0
        return self._z

    # ── примитивы рисования ─────────────────────────────────────────────
    def stroke(self, pts2, lw=LW_MAIN, style="-", color="black", z=None):
        xs = [p[0] for p in pts2]
        ys = [p[1] for p in pts2]
        zorder = self._z + 3 if z is None else z
        if style == "--":
            self.ax.plot(xs, ys, lw=lw, color=color, dashes=(4, 1.5),
                         solid_capstyle="round", zorder=zorder)
        elif style == "-.":
            self.ax.plot(xs, ys, lw=lw, color=color, dashes=(8, 1.5, 1.5, 1.5),
                         zorder=zorder)
        else:
            self.ax.plot(xs, ys, lw=lw, color=color, solid_capstyle="round",
                         zorder=zorder)

    def fill(self, pts2, color="white", z=None):
        self.ax.add_patch(MplPolygon(
            pts2, closed=True, facecolor=color, edgecolor="none",
            zorder=self._z if z is None else z))

    def text(self, x, y, s, size=10, ha="center", va="center", bold=False,
             z=200, rotation=0):
        self.ax.text(x, y, s, fontsize=size, ha=ha, va=va,
                     fontweight="bold" if bold else "normal",
                     zorder=z, rotation=rotation, color="black")

    # ── вертикальный цилиндр (ось ‖ Z) ─────────────────────────────────
    def vcylinder(self, cx, cy, r, z1, z2, dx, dy, *,
                  draw_top=True, draw_bottom=True):
        """Залить и обвести вертикальный цилиндр. Возвращает базовый слой.

        Силуэтные образующие — в точках θ=−45°/135° (экстремумы по экрану).
        Видимая нижняя дуга — передняя половина θ∈(−45°,135°)."""
        layer = self.next_layer()
        top2 = project(circle3((cx, cy, z2), r, "xy"), dx, dy)
        bot2 = project(circle3((cx, cy, z1), r, "xy"), dx, dy)
        self.fill(convex_hull(top2 + bot2), z=layer)
        if draw_top:
            self.stroke(top2, z=layer + 3)
        if draw_bottom:
            self.stroke(project(circle3((cx, cy, z1), r, "xy", -45, 135), dx, dy),
                        z=layer + 3)
        for t in (-45.0, 135.0):
            a = math.radians(t)
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            self.stroke(project([(px, py, z1), (px, py, z2)], dx, dy),
                        z=layer + 3)
        return layer

    # ── проушина-вилка: цилиндр с пазом сверху (паз ‖ Y) ────────────────
    def clevis_y(self, cx, cy, r, z1, ztop, zfloor, hw, dx, dy):
        """Ø-цилиндр z1..ztop, в верхней части прорезан паз шириной 2·hw до
        zfloor вдоль оси Y → две проушины на +X и −X. Чистая вилка.

        Видны: внешний силуэт цилиндра, верхние сегменты обеих проушин,
        внутренние стенки паза, дно паза. Скрытое не рисуем."""
        b = math.degrees(math.acos(hw / r))
        yend = math.sqrt(r * r - hw * hw)
        L = self.next_layer()

        # 1. Внешний силуэт всего цилиндра как белый окклюдер + образующие
        top_full = project(circle3((cx, cy, ztop), r, "xy"), dx, dy)
        bot_full = project(circle3((cx, cy, z1), r, "xy"), dx, dy)
        self.fill(convex_hull(top_full + bot_full), z=L)
        for t in (-45.0, 135.0):
            a = math.radians(t)
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            self.stroke(project([(px, py, z1), (px, py, ztop)], dx, dy), z=L + 6)
        # нижняя видимая дуга (на опоре)
        self.stroke(project(circle3((cx, cy, z1), r, "xy", -45, 135), dx, dy),
                    z=L + 6)

        # 2. Дно паза z=zfloor (полигон |x|<hw, внутри цилиндра)
        floor3 = (circle3((cx, cy, zfloor), r, "xy", b, 180 - b, 24)
                  + circle3((cx, cy, zfloor), r, "xy", 180 + b, 360 - b, 24))
        self.fill(project(floor3, dx, dy), z=L + 1)
        self.stroke(project(circle3((cx, cy, zfloor), r, "xy", b, 180 - b, 24),
                            dx, dy), z=L + 6)
        self.stroke(project(circle3((cx, cy, zfloor), r, "xy", 180 + b, 360 - b, 24),
                            dx, dy), z=L + 6)

        # 3. Проушины. Дальняя (левая, x≤−hw) — потом ближняя (правая, x≥hw).
        def prong(theta_lo, theta_hi, chord_x, zlayer):
            arc = circle3((cx, cy, ztop), r, "xy", theta_lo, theta_hi, 40)
            top_loop = arc + [arc[0]]
            floor_loop = [(p[0], p[1], zfloor) for p in arc]
            self.fill(convex_hull(project(arc + floor_loop, dx, dy)), z=zlayer)
            # верхний сегмент (дуга + хорда)
            self.stroke(project(top_loop, dx, dy), z=zlayer + 6)
            # внутренняя стенка паза (плоскость x=chord_x)
            y_a, y_b = arc[0][1], arc[-1][1]
            self.stroke(project([
                (chord_x, y_a, zfloor), (chord_x, y_a, ztop),
                (chord_x, y_b, ztop), (chord_x, y_b, zfloor)], dx, dy),
                z=zlayer + 6)

        prong(180 - b, 180 + b, -hw, self.next_layer())   # дальняя (−X)
        right_layer = self.next_layer()
        prong(-b, b, hw, right_layer)                     # ближняя (+X)
        return right_layer

    # ── устье отверстия на боковой поверхности вертикального цилиндра ───
    def hole_on_cyl(self, R, axis, c_along, c_z, r, dx, dy, n=64):
        """Устье отверстия Ø2r с горизонтальной осью в цилиндре Ø2R.

        axis='x': ось ‖ X, видимая грань +X (x=+√(R²−y²)), c_along=y центра.
        axis='y': ось ‖ Y, видимая грань −Y (y=−√(R²−x²)), c_along=x центра."""
        layer = self.next_layer()
        pts = []
        for i in range(n + 1):
            phi = 2 * math.pi * i / n
            a = c_along + r * math.cos(phi)
            z = c_z + r * math.sin(phi)
            a = max(-R + 1e-6, min(R - 1e-6, a))
            s = math.sqrt(R * R - a * a)
            pts.append((s, a, z) if axis == "x" else (a, -s, z))
        self.stroke(project(pts, dx, dy), z=layer + 6)
        return layer

    # ── отверстие на горизонтальной грани (ось ‖ Z) ─────────────────────
    def hole_xy(self, cx, cy, z, r, dx, dy, depth_arc=2.5):
        layer = self.next_layer()
        self.stroke(project(circle3((cx, cy, z), r, "xy"), dx, dy), z=layer + 6)
        if depth_arc > 0:
            self.stroke(project(circle3((cx, cy, z - depth_arc), r, "xy", 135, 315),
                                dx, dy), lw=LW_THIN, z=layer + 6)
        return layer

    # ── осевые штрихпунктирные ──────────────────────────────────────────
    def axis_line(self, p3a, p3b, dx, dy):
        self.stroke(project([p3a, p3b], dx, dy), lw=LW_THIN, style="-.", z=150)

    # ── размеры (ГОСТ 2.307) ─────────────────────────────────────────────
    def _arrow(self, tip, direction, z=185, length=3.2, half_w=0.55):
        ux, uy = direction
        n = math.hypot(ux, uy) or 1.0
        ux, uy = ux / n, uy / n
        px, py = -uy, ux
        a = (tip[0] - ux * length + px * half_w, tip[1] - uy * length + py * half_w)
        b = (tip[0] - ux * length - px * half_w, tip[1] - uy * length - py * half_w)
        self.ax.add_patch(MplPolygon([tip, a, b], closed=True,
                                     facecolor="black", edgecolor="none", zorder=z))

    def vdim(self, p3_lo, p3_hi, side_x, side_y, label, dx, dy, text_dx=0.0):
        """Вертикальный (по высоте) размер. Выносные вдоль (side_x,side_y,0)
        от точек детали к общей вертикальной размерной линии."""
        a3 = (side_x, side_y, p3_lo[2])
        b3 = (side_x, side_y, p3_hi[2])
        self.stroke(project([p3_lo, a3], dx, dy), lw=LW_THIN, z=178)
        self.stroke(project([p3_hi, b3], dx, dy), lw=LW_THIN, z=178)
        a2 = project([a3], dx, dy)[0]
        b2 = project([b3], dx, dy)[0]
        self.stroke([a2, b2], lw=LW_THIN, z=178)
        self._arrow(a2, (0, -1))
        self._arrow(b2, (0, 1))
        self.text((a2[0] + b2[0]) / 2 + text_dx, (a2[1] + b2[1]) / 2, label, size=9)

    def leader(self, p3, dx, dy, elbow=(14, 10), text="", text_size=9):
        a = project([p3], dx, dy)[0]
        e = (a[0] + elbow[0], a[1] + elbow[1])
        shelf_dir = 1 if elbow[0] >= 0 else -1
        s = (e[0] + shelf_dir * max(7, 2 + 2.3 * len(text)), e[1])
        self.stroke([a, e, s], lw=LW_THIN, z=178)
        self._arrow(a, (a[0] - e[0], a[1] - e[1]))
        self.text((e[0] + s[0]) / 2, e[1] + 2.4, text, size=text_size)

    # ── рамка и основная надпись ────────────────────────────────────────
    def frame(self):
        self.stroke([(0.5, 0.5), (209.5, 0.5), (209.5, 296.5), (0.5, 296.5),
                     (0.5, 0.5)], lw=LW_THIN, z=160)
        self.stroke([(20, 5), (205, 5), (205, 292), (20, 292), (20, 5)],
                    lw=LW_MAIN, z=160)

    def title_block(self):
        x0, y0, w, h = 20, 5, 185, 55
        z = 161
        self.stroke([(x0, y0 + h), (x0 + w, y0 + h)], lw=LW_MAIN, z=z)
        xl, xr = x0 + 65, x0 + w - 50
        self.stroke([(xl, y0), (xl, y0 + h)], lw=LW_MAIN, z=z)
        self.stroke([(xr, y0), (xr, y0 + h)], lw=LW_MAIN, z=z)
        for i in range(1, 5):
            yy = y0 + h * i / 5
            self.stroke([(x0, yy), (xl, yy)], lw=LW_THIN, z=z)
        self.text(x0 + 12, y0 + h * 4.5 / 5, "Разраб.", size=7, ha="left")
        self.text(x0 + 35, y0 + h * 4.5 / 5, self.designer, size=7, ha="left")
        self.text(x0 + 12, y0 + h * 3.5 / 5, "Дата", size=7, ha="left")
        self.text(x0 + 35, y0 + h * 3.5 / 5, self.date, size=7, ha="left")
        self.text(x0 + 12, y0 + h * 2.5 / 5, "Метод", size=7, ha="left")
        self.text(x0 + 35, y0 + h * 2.5 / 5, "ГОСТ 2.317", size=7, ha="left")
        self.text((xl + xr) / 2, y0 + h * 0.66, self.title, size=14, bold=True)
        self.text((xl + xr) / 2, y0 + h * 0.30, self.subtitle, size=8)
        self.stroke([(xr, y0 + h / 2), (x0 + w, y0 + h / 2)], lw=LW_THIN, z=z)
        self.text(xr + 25, y0 + h * 0.74, "Масштаб", size=7)
        self.text(xr + 25, y0 + h * 0.60, self.scale, size=10, bold=True)
        self.text(xr + 25, y0 + h * 0.28, "Лист 1", size=8)

    def note(self, x, y, lines, size=8):
        for i, line in enumerate(lines):
            self.text(x, y - i * 4.6, line, size=size, ha="left")

    def save(self, pdf_path, png_path=None):
        self.fig.savefig(pdf_path, format="pdf")
        if png_path:
            self.fig.savefig(png_path, format="png", dpi=150)
        plt.close(self.fig)
