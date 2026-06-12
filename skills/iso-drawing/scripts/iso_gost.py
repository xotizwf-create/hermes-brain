# -*- coding: utf-8 -*-
"""Прямоугольная изометрия по ГОСТ 2.317 на листе А4 — библиотека для Hermes.

Даёт всё, из чего строится аккуратный учебный/рабочий чертёж:
- проекция прямоугольной изометрии с приведёнными коэффициентами (=1);
- эллипсы (проекции окружностей в плоскостях XY/XZ/YZ) как параметрические кривые;
- контур вертикального цилиндра с автоматическим силуэтом;
- перекрытие тел «алгоритмом художника»: каждое тело заливается белым и рисуется
  ПОВЕРХ более дальних (стройте деталь снизу вверх);
- лист А4 с рамкой по ГОСТ 2.301 и упрощённой основной надписью (ГОСТ 2.104);
- линии по ГОСТ 2.303 (основная s, тонкая s/3, штриховая, штрихпунктирная);
- размеры: линейные со стрелками и выноски с полками (ГОСТ 2.307).

Координаты детали — миллиметры, z вверх. Проекция: u=(x−y)·cos30°,
v=z−(x+y)·sin30° (ось X уходит вправо-вниз, Y — влево-вниз, Z — вверх).
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

# Толщины линий, мм → pt (ГОСТ 2.303: основная 0.5–1.4, тонкая в 2–3 раза тоньше)
PT = 72 / 25.4
LW_MAIN = 0.7 * PT
LW_THIN = 0.25 * PT


def iso(p):
    """3D точка (мм) → 2D точка листа (мм, без смещения)."""
    x, y, z = p
    return ((x - y) * COS30, z - (x + y) * SIN30)


def project(pts3, dx=0.0, dy=0.0):
    """Список 3D точек → список 2D точек листа со смещением (dx, dy)."""
    out = []
    for p in pts3:
        u, v = iso(p)
        out.append((u + dx, v + dy))
    return out


def circle3(center, r, plane="xy", t0=0.0, t1=360.0, n=120):
    """Окружность (дуга) в координатной плоскости → список 3D точек.

    plane: 'xy' (горизонтальная), 'xz' (фронтальная), 'yz' (профильная).
    Параметр t — угол в градусах в локальной плоскости.
    """
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
    """Монотонная цепь Эндрю; точки 2D → вершины выпуклой оболочки (CCW)."""
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
    """Лист А4 (портрет) с рамкой и основной надписью."""

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

    # ── слои ────────────────────────────────────────────────────────────
    def next_layer(self) -> float:
        """Новый слой поверх всего нарисованного (painter's algorithm)."""
        self._z += 2.0
        return self._z

    # ── примитивы ───────────────────────────────────────────────────────
    def stroke(self, pts2, lw=LW_MAIN, style="-", color="black", z=None):
        xs = [p[0] for p in pts2]
        ys = [p[1] for p in pts2]
        kwargs = {}
        if style == "--":           # штриховая (невидимый контур), ГОСТ 2.303
            kwargs["dashes"] = (4, 1.5)
        elif style == "-.":         # штрихпунктирная (осевая)
            kwargs["dashes"] = (8, 1.5, 1.5, 1.5)
        self.ax.plot(xs, ys, linestyle="-" if not kwargs else "--",
                     lw=lw, color=color, solid_capstyle="round",
                     zorder=self._z if z is None else z, **kwargs)

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
    def vcylinder(self, cx, cy, r, z1, z2, dx, dy, *, draw_bottom=True):
        """Залить и обвести вертикальный цилиндр. Возвращает слой."""
        layer = self.next_layer()
        top3 = circle3((cx, cy, z2), r, "xy")
        bot3 = circle3((cx, cy, z1), r, "xy")
        top2 = project(top3, dx, dy)
        bot2 = project(bot3, dx, dy)
        hull = convex_hull(top2 + bot2)
        self.fill(hull, z=layer)
        # верхний эллипс — целиком
        self.stroke(top2, z=layer + 0.5)
        # нижняя видимая дуга: t ∈ (−45°, 135°) — ближняя к наблюдателю половина
        bot_front = project(circle3((cx, cy, z1), r, "xy", -45, 135), dx, dy)
        if draw_bottom:
            self.stroke(bot_front, z=layer + 0.5)
        # образующие силуэта — в точках t = −45° и 135°
        for t in (-45.0, 135.0):
            a = math.radians(t)
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            self.stroke(project([(px, py, z1), (px, py, z2)], dx, dy),
                        z=layer + 0.5)
        return layer

    # ── паз/прорезь вдоль X в вертикальном цилиндре ─────────────────────
    def slot_x(self, cx, cy, r, half_w, z_top, z_floor, dx, dy):
        """Открытый паз шириной 2·half_w вдоль оси X, прорезанный сверху.

        Срезает в цилиндре (верх z_top) полосу |y−cy|≤half_w до глубины
        z_floor: белая заливка полости + рёбра (хорды, стенки, дно).
        """
        layer = self.next_layer()
        xc = math.sqrt(max(r * r - half_w * half_w, 0.0))
        t1 = math.degrees(math.asin(half_w / r))
        yf, yn = cy + half_w, cy - half_w     # дальняя/ближняя стенки

        # Полость как замкнутый многоугольник (по контуру отверстия паза)
        loop3 = []
        loop3 += [(cx - xc, yf, z_top), (cx + xc, yf, z_top)]          # дальняя хорда
        loop3 += [(cx + xc, yf, z_floor)]                              # угол вниз
        loop3 += circle3((cx, cy, z_floor), r, "xy", t1, -t1, 24)      # дно, ближний торец
        loop3 += [(cx + xc, yn, z_floor), (cx - xc, yn, z_floor)]
        loop3 += [(cx - xc, yn, z_top)]                                # ближняя хорда край
        loop3 += [(cx - xc, yn, z_floor)]
        loop3 += circle3((cx, cy, z_floor), r, "xy", 180 + t1, 180 - t1, 24)
        loop3 += [(cx - xc, yf, z_floor)]
        self.fill(project(loop3, dx, dy), z=layer)

        e = layer + 0.5
        # хорды на верхнем торце
        self.stroke(project([(cx - xc, yf, z_top), (cx + xc, yf, z_top)], dx, dy), z=e)
        self.stroke(project([(cx - xc, yn, z_top), (cx + xc, yn, z_top)], dx, dy), z=e)
        # вертикальные рёбра на торцах паза
        for px, py in ((cx + xc, yf), (cx + xc, yn), (cx - xc, yf), (cx - xc, yn)):
            self.stroke(project([(px, py, z_top), (px, py, z_floor)], dx, dy), z=e)
        # дно: продольные рёбра и торцевые дуги
        self.stroke(project([(cx - xc, yf, z_floor), (cx + xc, yf, z_floor)], dx, dy), z=e)
        self.stroke(project([(cx - xc, yn, z_floor), (cx + xc, yn, z_floor)], dx, dy), z=e)
        self.stroke(project(circle3((cx, cy, z_floor), r, "xy", -t1, t1, 24), dx, dy), z=e)
        self.stroke(project(circle3((cx, cy, z_floor), r, "xy", 180 - t1, 180 + t1, 24), dx, dy), z=e)
        return layer

    # ── отверстие на горизонтальной грани ───────────────────────────────
    def hole_xy(self, cx, cy, z, r, dx, dy, depth_arc=2.5):
        """Отверстие на верхней грани: эллипс + тень глубины (дуга)."""
        layer = self.next_layer()
        self.stroke(project(circle3((cx, cy, z), r, "xy"), dx, dy), z=layer)
        if depth_arc > 0:
            # дальняя стенка отверстия чуть видна: дуга, опущенная на depth_arc
            self.stroke(project(circle3((cx, cy, z - depth_arc), r, "xy", 135, 315),
                                dx, dy), lw=LW_THIN, z=layer)
        return layer

    # ── устье отверстия (ось ‖ Y) на боковой поверхности цилиндра ───────
    def hole_on_vcyl_y(self, R, xh, zh, r, dx, dy, n=72):
        """Видимое устье отверстия радиуса r с осью вдоль Y в вертикальном
        цилиндре радиуса R (истинная кривая на поверхности, ближняя ветвь
        y=+√(R²−x²) — обращена к наблюдателю)."""
        layer = self.next_layer()
        pts3 = []
        for i in range(n + 1):
            phi = 2 * math.pi * i / n
            x = xh + r * math.cos(phi)
            z = zh + r * math.sin(phi)
            x = max(-R + 1e-6, min(R - 1e-6, x))
            y = math.sqrt(R * R - x * x)
            pts3.append((x, y, z))
        self.stroke(project(pts3, dx, dy), z=layer)
        return layer

    # ── оси ──────────────────────────────────────────────────────────────
    def axis_line(self, p3a, p3b, dx, dy):
        self.stroke(project([p3a, p3b], dx, dy), lw=LW_THIN, style="-.", z=150)

    # ── размеры (ГОСТ 2.307) ─────────────────────────────────────────────
    def _arrow(self, tip, direction, z=180, length=3.5, half_w=0.6):
        ux, uy = direction
        n = math.hypot(ux, uy) or 1.0
        ux, uy = ux / n, uy / n
        px, py = -uy, ux
        a = (tip[0] - ux * length + px * half_w, tip[1] - uy * length + py * half_w)
        b = (tip[0] - ux * length - px * half_w, tip[1] - uy * length - py * half_w)
        self.ax.add_patch(MplPolygon([tip, a, b], closed=True,
                                     facecolor="black", edgecolor="none", zorder=z))

    def dim(self, p3a, p3b, off3, off, text, dx, dy, text_shift=(0, 2.5),
            text_size=9):
        """Линейный размер: точки в 3D, выносные линии вдоль off3 (ед. вектор)."""
        ox, oy, oz = off3
        pa = (p3a[0] + ox * off, p3a[1] + oy * off, p3a[2] + oz * off)
        pb = (p3b[0] + ox * off, p3b[1] + oy * off, p3b[2] + oz * off)
        pa_e = (p3a[0] + ox * (off + 2), p3a[1] + oy * (off + 2), p3a[2] + oz * (off + 2))
        pb_e = (p3b[0] + ox * (off + 2), p3b[1] + oy * (off + 2), p3b[2] + oz * (off + 2))
        # выносные
        self.stroke(project([p3a, pa_e], dx, dy), lw=LW_THIN, z=170)
        self.stroke(project([p3b, pb_e], dx, dy), lw=LW_THIN, z=170)
        # размерная
        a2 = project([pa], dx, dy)[0]
        b2 = project([pb], dx, dy)[0]
        self.stroke([a2, b2], lw=LW_THIN, z=170)
        d = (b2[0] - a2[0], b2[1] - a2[1])
        self._arrow(a2, (-d[0], -d[1]))
        self._arrow(b2, d)
        mx, my = (a2[0] + b2[0]) / 2 + text_shift[0], (a2[1] + b2[1]) / 2 + text_shift[1]
        self.text(mx, my, text, size=text_size)

    def leader(self, p3, dx, dy, elbow=(14, 10), text="", text_size=9,
               dot=False):
        """Выноска с полкой: от точки на детали — наклонная, полка, текст."""
        a = project([p3], dx, dy)[0]
        e = (a[0] + elbow[0], a[1] + elbow[1])
        shelf_dir = 1 if elbow[0] >= 0 else -1
        s = (e[0] + shelf_dir * max(6, 2 + 2.2 * len(text)), e[1])
        self.stroke([a, e, s], lw=LW_THIN, z=170)
        if dot:
            self.ax.plot([a[0]], [a[1]], marker="o", markersize=2.2,
                         color="black", zorder=171)
        else:
            self._arrow(a, (a[0] - e[0], a[1] - e[1]))
        self.text((e[0] + s[0]) / 2, e[1] + 2.4, text, size=text_size)

    # ── рамка и основная надпись ────────────────────────────────────────
    def frame(self):
        # внешняя граница листа (тонкая) и рамка поля чертежа (основная)
        self.stroke([(0.5, 0.5), (209.5, 0.5), (209.5, 296.5), (0.5, 296.5),
                     (0.5, 0.5)], lw=LW_THIN, z=160)
        self.stroke([(20, 5), (205, 5), (205, 292), (20, 292), (20, 5)],
                    lw=LW_MAIN, z=160)

    def title_block(self):
        """Упрощённая основная надпись (форма 1, 185×55) в правом нижнем углу."""
        x0, y0, w, h = 20, 5, 185, 55
        z = 160
        self.stroke([(x0, y0 + h), (x0 + w, y0 + h)], lw=LW_MAIN, z=z)
        # вертикальное деление: левый блок граф 65 мм, центр, правый блок 50 мм
        xl, xr = x0 + 65, x0 + w - 50
        self.stroke([(xl, y0), (xl, y0 + h)], lw=LW_MAIN, z=z)
        self.stroke([(xr, y0), (xr, y0 + h)], lw=LW_MAIN, z=z)
        # левый блок: строки граф
        for i in range(1, 5):
            yy = y0 + h * i / 5
            self.stroke([(x0, yy), (xl, yy)], lw=LW_THIN, z=z)
        self.text(x0 + 12, y0 + h * 4.5 / 5, "Разраб.", size=7, ha="left")
        self.text(x0 + 35, y0 + h * 4.5 / 5, self.designer, size=7, ha="left")
        self.text(x0 + 12, y0 + h * 3.5 / 5, "Дата", size=7, ha="left")
        self.text(x0 + 35, y0 + h * 3.5 / 5, self.date, size=7, ha="left")
        self.text(x0 + 12, y0 + h * 2.5 / 5, "Метод", size=7, ha="left")
        self.text(x0 + 35, y0 + h * 2.5 / 5, "ГОСТ 2.317", size=7, ha="left")
        # центральный блок: наименование
        self.text((xl + xr) / 2, y0 + h * 0.68, self.title, size=14, bold=True)
        self.text((xl + xr) / 2, y0 + h * 0.32, self.subtitle, size=8)
        # правый блок: масштаб / лист
        self.stroke([(xr, y0 + h / 2), (x0 + w, y0 + h / 2)], lw=LW_THIN, z=z)
        self.text(xr + 25, y0 + h * 0.75, "Масштаб", size=7)
        self.text(xr + 25, y0 + h * 0.62, self.scale, size=10, bold=True)
        self.text(xr + 25, y0 + h * 0.30, "Лист 1", size=8)

    def note(self, x, y, lines, size=8):
        for i, line in enumerate(lines):
            self.text(x, y - i * 4.6, line, size=size, ha="left")

    def save(self, pdf_path, png_path=None):
        self.fig.savefig(pdf_path, format="pdf")
        if png_path:
            self.fig.savefig(png_path, format="png", dpi=150)
        plt.close(self.fig)
