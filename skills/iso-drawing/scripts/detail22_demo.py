# -*- coding: utf-8 -*-
"""Эталон скилла iso-drawing: деталь №22 (фланец-вилка) в изометрии ГОСТ 2.317.

Состав детали (по исходному ортогональному чертежу №22):
- основание-фланец Ø92, h=15; 4 сквозных отв. Ø12 на окружности Ø70;
- ступень Ø50, z 15…35;
- стойка Ø36, z 35…66, прорезанная сверху пазом 10 мм (вдоль Y) до z=55 —
  получается вилка из двух проушин;
- сквозное отв. Ø10 через проушины (ось ‖ X) на z≈60.

Запуск (на сервере, в venv шлюза, с лимитом памяти):
  systemd-run --scope -q -p MemoryMax=350M \
    /usr/local/lib/hermes-agent/venv/bin/python detail22_demo.py /root/.hermes/outbox
"""
import math
import sys

sys.path.insert(0, "/root/.hermes/agent-knowledge/skills/iso-drawing/scripts")
from iso_gost import LW_THIN, Sheet, circle3, project  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
DX, DY = 103.0, 150.0

sh = Sheet(title="Деталь 22", subtitle="Прямоугольная изометрия",
           date="11.06.2026")

# ── 1. Основание Ø92 (r46), z 0…15 ──────────────────────────────────────
sh.vcylinder(0, 0, 46, 0, 15, DX, DY)

# 4 отверстия Ø12 (r6) на Ø70 (r35), по диагоналям
for ang in (45, 135, 225, 315):
    a = math.radians(ang)
    sh.hole_xy(35 * math.cos(a), 35 * math.sin(a), 15, 6, DX, DY)

# ── 2. Ступень Ø50 (r25), z 15…35 ──────────────────────────────────────
sh.vcylinder(0, 0, 25, 15, 35, DX, DY, draw_bottom=False)

# ── 3. Стойка-вилка Ø36 (r18), z 35…66, паз 10 (hw 5) до z 55 ──────────
sh.vcylinder(0, 0, 18, 35, 55, DX, DY, draw_top=False, draw_bottom=False)
sh.clevis_y(0, 0, 18, 35, 66, 55, 5, DX, DY)

# ── 4. Сквозное отв. Ø10 (r5) через проушины, ось ‖ X, z=60 ────────────
sh.hole_on_cyl(18, "x", 0.0, 60.0, 5, DX, DY)

# ── Осевая вертикальная (тонкая штрихпунктирная), коротко ───────────────
sh.axis_line((0, 0, -8), (0, 0, 74), DX, DY)

# ── Размеры (ГОСТ 2.307) ────────────────────────────────────────────────
SQ = math.sqrt(2) / 2
# Габаритная высота 66 — справа, размерная линия у x≈178 (в поле листа)
sh.vdim((46 * SQ, -46 * SQ, 0), (18 * SQ, -18 * SQ, 66), 43, -43, "66", DX, DY,
        text_dx=4)
# Высота основания 15 — слева, размерная линия у x≈32
sh.vdim((-46 * SQ, 46 * SQ, 0), (-46 * SQ, 46 * SQ, 15),
        -41, 41, "15", DX, DY, text_dx=-5)

# Диаметры и элементы — выносками с полками (наружу, без пересечений)
sh.leader((46 * math.cos(math.radians(-18)), 46 * math.sin(math.radians(-18)), 15),
          DX, DY, elbow=(20, -10), text="Ø92")
sh.leader((25 * math.cos(math.radians(-40)), 25 * math.sin(math.radians(-40)), 35),
          DX, DY, elbow=(26, 6), text="Ø50")
sh.leader((18 * math.cos(math.radians(18)), 18 * math.sin(math.radians(18)), 66),
          DX, DY, elbow=(26, 16), text="Ø36")
# 4 отв. Ø12 — от переднего-центрального отверстия (θ=45) вниз-влево
ha = math.radians(45)
sh.leader((35 * math.cos(ha), 35 * math.sin(ha), 15),
          DX, DY, elbow=(-14, -18), text="4 отв. Ø12")
# устье Ø10 на ближней грани проушины (+X)
hx = 18.0
sh.leader((hx, 0.0, 60), DX, DY, elbow=(22, -2), text="2 отв. Ø10")
# паз 10 — выноска ко дну паза
sh.leader((0, 8, 55), DX, DY, elbow=(-24, 12), text="паз 10")

# ── Оформление листа ────────────────────────────────────────────────────
sh.frame()
sh.title_block()
sh.note(26, 286, [
    "Прямоугольная изометрическая проекция — ГОСТ 2.317",
    "(приведённые коэффициенты, размеры действительные).",
])

sh.save(f"{OUT}/detail22_isometry.pdf", f"{OUT}/detail22_isometry.png")
print("SAVED", f"{OUT}/detail22_isometry.pdf")
