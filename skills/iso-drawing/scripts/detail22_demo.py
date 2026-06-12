# -*- coding: utf-8 -*-
"""Эталонный пример скилла iso-drawing: деталь №22 в прямоугольной изометрии.

Деталь (по исходному ортогональному чертежу):
- основание Ø92, h=15, четыре сквозных отверстия Ø12 на окружности Ø70;
- ступень Ø50, z 15…35, прорезанная открытым пазом шириной 10 вдоль оси X;
- стойка Ø36, z 35…66, с пазом шириной 10 сверху до z=55 (две «щёки»);
- два отверстия Ø10 в стойке (ось вдоль Y, видно ближнее устье).

Запуск (на сервере, в venv шлюза):
    /usr/local/lib/hermes-agent/venv/bin/python detail22_demo.py /root/.hermes/outbox
"""
import math
import sys

sys.path.insert(0, "/root/.hermes/agent-knowledge/skills/iso-drawing/scripts")
from iso_gost import LW_THIN, Sheet, circle3, project  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "."

DX, DY = 105.0, 142.0   # положение начала координат детали на листе, мм

sh = Sheet(title="Деталь 22", subtitle="Прямоугольная изометрия",
           date="11.06.2026")

# ── 1. Основание Ø92 (r46), z 0…15 ──────────────────────────────────────
sh.vcylinder(0, 0, 46, 0, 15, DX, DY)

# окружность центров Ø70 — штрихпунктирной тонкой на верхней грани
sh.stroke(project(circle3((0, 0, 15), 35, "xy"), DX, DY),
          lw=LW_THIN, style="-.", z=149)

# четыре отверстия Ø12 (r6) на Ø70, по диагоналям
for ang in (45, 135, 225, 315):
    a = math.radians(ang)
    sh.hole_xy(35 * math.cos(a), 35 * math.sin(a), 15, 6, DX, DY)

# ── 2. Ступень Ø50 (r25), z 15…35, с открытым пазом 10 вдоль X ──────────
sh.vcylinder(0, 0, 25, 15, 35, DX, DY)
sh.slot_x(0, 0, 25, 5, 35, 15, DX, DY)

# ── 3. Стойка Ø36 (r18), z 35…66, паз 10 сверху до z 55 ────────────────
sh.vcylinder(0, 0, 18, 35, 66, DX, DY)
sh.slot_x(0, 0, 18, 5, 66, 55, DX, DY)

# ── 4. Отверстие Ø10 в стойке (ось вдоль Y) — видимое устье ────────────
HX, HZ = -3.0, 45.0
sh.hole_on_vcyl_y(18, HX, HZ, 5, DX, DY)
hx, hy = HX, math.sqrt(18 * 18 - HX * HX)

# ── Оси (штрихпунктирные тонкие) ────────────────────────────────────────
sh.axis_line((-56, 0, 15), (56, 0, 15), DX, DY)
sh.axis_line((0, -56, 15), (0, 56, 15), DX, DY)
sh.axis_line((0, 0, -6), (0, 0, 74), DX, DY)

# ── Размеры (ГОСТ 2.307) ────────────────────────────────────────────────
SQ = math.sqrt(2) / 2

# Высота 66 — справа; выносные вдоль (1,−1,0), размерная вертикальна
def _ext(p3a, p3b):
    sh.stroke(project([p3a, p3b], DX, DY), lw=LW_THIN, z=170)

R_DIM = 39.5  # x = −y на правой размерной линии
_ext((46 * SQ, -46 * SQ, 0), (R_DIM + 2.5, -(R_DIM + 2.5), 0))
_ext((18 * SQ, -18 * SQ, 66), (R_DIM + 2.5, -(R_DIM + 2.5), 66))
a2 = project([(R_DIM, -R_DIM, 0)], DX, DY)[0]
b2 = project([(R_DIM, -R_DIM, 66)], DX, DY)[0]
sh.stroke([a2, b2], lw=LW_THIN, z=170)
sh._arrow(a2, (0, -1))
sh._arrow(b2, (0, 1))
sh.text(a2[0] + 5, (a2[1] + b2[1]) / 2, "66", size=9)

# Высота 15 — слева
L_DIM = 39.5
_ext((-46 * SQ, 46 * SQ, 0), (-(L_DIM + 2.5), L_DIM + 2.5, 0))
_ext((-46 * SQ, 46 * SQ, 15), (-(L_DIM + 2.5), L_DIM + 2.5, 15))
a2 = project([(-L_DIM, L_DIM, 0)], DX, DY)[0]
b2 = project([(-L_DIM, L_DIM, 15)], DX, DY)[0]
sh.stroke([a2, b2], lw=LW_THIN, z=170)
sh._arrow(a2, (0, -1))
sh._arrow(b2, (0, 1))
sh.text(a2[0] - 5.5, (a2[1] + b2[1]) / 2, "15", size=9)

# Диаметры и элементы — выносками с полками
sh.leader((46 * math.cos(math.radians(-20)), 46 * math.sin(math.radians(-20)), 15),
          DX, DY, elbow=(16, -9), text="Ø92")
sh.leader((25 * math.cos(math.radians(-35)), 25 * math.sin(math.radians(-35)), 35),
          DX, DY, elbow=(22, 9), text="Ø50")
sh.leader((-18 * SQ, 18 * SQ, 48), DX, DY, elbow=(-20, -10), text="Ø36")
ha = math.radians(45)
sh.leader((35 * math.cos(ha) - 6 * 0.7, 35 * math.sin(ha) - 6 * 0.7, 15),
          DX, DY, elbow=(-22, -13), text="4 отв. Ø12")
sh.leader((hx, hy, 45 + 5), DX, DY, elbow=(-16, 12), text="2 отв. Ø10")
sh.leader((-14, 5, 66), DX, DY, elbow=(-12, 14), text="паз 10")

# ── Оформление листа ────────────────────────────────────────────────────
sh.frame()
sh.title_block()
sh.note(26, 286, [
    "Прямоугольная изометрическая проекция — ГОСТ 2.317",
    "(приведённые коэффициенты искажения, размеры действительные).",
])

sh.save(f"{OUT}/detail22_isometry.pdf", f"{OUT}/detail22_isometry.png")
print("SAVED", f"{OUT}/detail22_isometry.pdf")
