import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont

from utils.database import get_all_stats

# ── Palette sặc sỡ ──────────────────────────────────────────
C = {
    'bg'      : '#080810',
    'bg2'     : '#0F0F1A',
    'surface' : '#141428',
    'surface2': '#1C1C35',
    'border'  : '#2A2A50',

    'purple'  : '#7C3AED',
    'purple2' : '#9D5CF6',
    'pink'    : '#EC4899',
    'pink2'   : '#F472B6',
    'teal'    : '#06B6D4',
    'teal2'   : '#22D3EE',
    'amber'   : '#F59E0B',
    'amber2'  : '#FCD34D',
    'green'   : '#10B981',
    'green2'  : '#34D399',
    'red'     : '#EF4444',
    'blue'    : '#3B82F6',
    'blue2'   : '#60A5FA',

    'text'    : '#F1F0FF',
    'text2'   : '#9090C0',
    'text3'   : '#4A4A70',
    'white'   : '#FFFFFF',
}


def _shadow(w, blur=30, offset=8, alpha=120):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setColor(QColor(0, 0, 0, alpha))
    fx.setOffset(0, offset)
    w.setGraphicsEffect(fx)
    return w


class HomeScreen(QWidget):
    go_practice = pyqtSignal()
    go_vocab    = pyqtSignal()
    go_stats    = pyqtSignal()

    def __init__(self, all_data):
        super().__init__()
        self.all_data = all_data
        self._sample_chars = (
            all_data.get('hiragana', []) +
            all_data.get('katakana', []) +
            all_data.get('kanji', [])
        )
        self._build()

        # Timer đổi chữ mỗi 3 giây
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate_char)
        self._timer.start(3000)

    def _build(self):
        self.setStyleSheet(f"background:{C['bg']};")
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 36, 48, 36)
        root.setSpacing(0)

        # ── Header ───────────────────────────────────────────
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        lbl_title = QLabel("日本語")
        lbl_title.setStyleSheet(f"""
            font-size: 56px;
            font-weight: 900;
            color: {C['amber2']};
            letter-spacing: 6px;
            background: transparent;
        """)
        _shadow(lbl_title, blur=40, alpha=160)

        lbl_sub = QLabel("Japanese Writing Practice")
        lbl_sub.setStyleSheet(f"""
            font-size: 15px;
            color: {C['text2']};
            letter-spacing: 2px;
            background: transparent;
        """)

        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)
        header.addLayout(title_col)
        header.addStretch()

        # Stats badge
        stats   = get_all_stats()
        total   = sum(len(v) for v in self.all_data.values())
        learned = len([s for s in stats if s[2] > 0])

        badge = QFrame()
        badge.setStyleSheet(f"""
            QFrame {{
                background: {C['surface2']};
                border: 1px solid {C['purple']};
                border-radius: 16px;
                padding: 4px;
            }}
        """)
        _shadow(badge, blur=20, alpha=100)
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(20, 12, 20, 12)
        badge_layout.setSpacing(2)

        badge_num = QLabel(f"{learned}/{total}")
        badge_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_num.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 800;
            color: {C['purple2']};
            background: transparent;
        """)
        badge_lbl = QLabel("ký tự đã học")
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_lbl.setStyleSheet(f"font-size:11px; color:{C['text3']}; background:transparent;")
        badge_layout.addWidget(badge_num)
        badge_layout.addWidget(badge_lbl)
        header.addWidget(badge)
        root.addLayout(header)
        root.addSpacing(32)

        # ── Hero card ─────────────────────────────────────────
        hero = QFrame()
        hero.setMinimumHeight(240)
        hero.setStyleSheet(f"""
            QFrame {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 24px;
            }}
        """)
        _shadow(hero, blur=40, offset=12, alpha=140)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(40, 30, 40, 30)
        hero_layout.setSpacing(32)

        # Chữ ngẫu nhiên
        char_col = QVBoxLayout()
        char_col.setSpacing(8)
        char_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_hero_char = QLabel()
        self.lbl_hero_char.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_hero_char.setMinimumWidth(200)
        self.lbl_hero_char.setStyleSheet(f"""
            font-size: 150px;
            color: {C['white']};
            background: transparent;
            letter-spacing: -4px;
        """)

        self.lbl_hero_type = QLabel()
        self.lbl_hero_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_hero_type.setFixedHeight(28)
        self.lbl_hero_type.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {C['bg']};
            background: {C['purple2']};
            border-radius: 14px;
            padding: 0 16px;
            letter-spacing: 1.5px;
        """)

        char_col.addWidget(self.lbl_hero_char)
        char_col.addWidget(self.lbl_hero_type, alignment=Qt.AlignmentFlag.AlignCenter)
        hero_layout.addLayout(char_col)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setStyleSheet(f"background:{C['border']}; max-width:1px;")
        hero_layout.addWidget(div)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(16)
        info_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_hero_nghia = QLabel()
        self.lbl_hero_nghia.setWordWrap(True)
        self.lbl_hero_nghia.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {C['text']};
            background: transparent;
        """)

        self.lbl_hero_reading = QLabel()
        self.lbl_hero_reading.setStyleSheet(f"""
            font-size: 18px;
            color: {C['teal2']};
            background: transparent;
            letter-spacing: 1px;
        """)

        self.lbl_hero_ex = QLabel()
        self.lbl_hero_ex.setWordWrap(True)
        self.lbl_hero_ex.setStyleSheet(f"""
            font-size: 18px;
            color: {C['text3']};
            background: transparent;
            line-height: 1.6;
        """)

        info_col.addWidget(self.lbl_hero_nghia)
        info_col.addWidget(self.lbl_hero_reading)
        info_col.addWidget(self.lbl_hero_ex)
        info_col.addStretch()
        hero_layout.addLayout(info_col, 1)

        root.addWidget(hero)
        root.addSpacing(28)

        # ── 3 Action buttons ─────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        btn_configs = [
            ("✍  Luyện viết",   C['purple'],  C['pink'],   self.go_practice),
            ("📖  Từ vựng",      C['teal'],    C['blue'],   self.go_vocab),
            ("📊  Tiến độ",      C['amber'],   C['green'],  self.go_stats),
        ]

        for label, c1, c2, signal in btn_configs:
            btn = QPushButton(label)
            btn.setMinimumHeight(58)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {c1};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 14px;
                    font-size: 16px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background: {c2};
                }}
                QPushButton:pressed {{
                    background: {c1}BB;
                }}
            """)
            _shadow(btn, blur=24, offset=6, alpha=100)
            btn.clicked.connect(signal.emit)
            btn_row.addWidget(btn)

        root.addLayout(btn_row)
        root.addStretch()

        # ── Stats row ────────────────────────────────────────
        stats_row  = QHBoxLayout()
        stats_row.setSpacing(12)

        perfect  = len([s for s in stats if s[1]>0 and s[2]/s[1]>=0.9])
        avg_acc  = (sum(s[2]/s[1] for s in stats if s[1]>0) /
                    max(len([s for s in stats if s[1]>0]), 1))

        stat_items = [
            (f"{learned}",          "Đã học",         C['purple2']),
            (f"{perfect}",          "Thành thạo",     C['green2']),
            (f"{int(avg_acc*100)}%","Độ chính xác",   C['amber2']),
            (f"{total - learned}",  "Còn lại",        C['pink2']),
        ]

        for val, lbl, color in stat_items:
            f  = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background: {C['surface2']};
                    border: 1px solid {C['border']};
                    border-radius: 12px;
                }}
            """)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 10, 16, 10)
            fl.setSpacing(2)

            v = QLabel(val)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.setStyleSheet(f"""
                font-size: 22px;
                font-weight: 800;
                color: {color};
                background: transparent;
            """)
            lb = QLabel(lbl)
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lb.setStyleSheet(f"font-size:11px; color:{C['text3']}; background:transparent;")
            fl.addWidget(v)
            fl.addWidget(lb)
            stats_row.addWidget(f)

        root.addLayout(stats_row)

        # Init hero char
        self._rotate_char()

    def _rotate_char(self):
        if not self._sample_chars:
            return
        card = random.choice(self._sample_chars)
        char = card['char']

        self.lbl_hero_char.setText(char)
        self.lbl_hero_nghia.setText(card.get('nghia_vi', ''))

        onyomi  = card.get('onyomi', '') or card.get('romaji', '')
        kunyomi = card.get('kunyomi', '')
        reading = f"{onyomi}  /  {kunyomi}" if onyomi or kunyomi else onyomi
        self.lbl_hero_reading.setText(reading)

        examples = card.get('vi_du', [])[:1]
        ex = ''
        if examples:
            e  = examples[0]
            ex = f"{e['tu']}  ({e['doc']})  =  {e['nghia']}"
        self.lbl_hero_ex.setText(ex)

        # Màu + badge theo loại
        code = ord(char)
        if 0x3041 <= code <= 0x3096:
            color, bg, name = C['purple2'], C['purple'], 'HIRAGANA'
        elif 0x30A1 <= code <= 0x30F6:
            color, bg, name = C['teal2'],   C['teal'],   'KATAKANA'
        else:
            color, bg, name = C['amber2'],  C['amber'],  'KANJI'

        self.lbl_hero_char.setStyleSheet(f"""
            font-size: 150px;
            color: {color};
            background: transparent;
            letter-spacing: -4px;
        """)
        self.lbl_hero_type.setText(name)
        self.lbl_hero_type.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {C['bg']};
            background: {bg};
            border-radius: 14px;
            padding: 0 16px;
            letter-spacing: 1.5px;
        """)