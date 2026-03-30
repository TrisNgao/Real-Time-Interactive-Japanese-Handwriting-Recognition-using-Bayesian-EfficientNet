from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QProgressBar
)
from PyQt6.QtCore import pyqtSignal
from utils.styles import C, style_btn, card_frame
from utils.database import get_all_stats


class VocabScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, all_data):
        super().__init__()
        self.all_data = all_data
        self._build()

    def _build(self):
        self.setStyleSheet(f"background:{C['bg']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(16)

        # Top bar
        top = QHBoxLayout()
        btn_back = QPushButton("← Về trang chủ")
        style_btn(btn_back, C['surface'], C['text2'], size=13, pad='8px 16px')
        btn_back.clicked.connect(self.go_home.emit)

        total = sum(len(v) for v in self.all_data.values())
        title = QLabel(f"📖 Từ vựng — {total} ký tự")
        title.setStyleSheet(f"color:{C['text']}; font-size:16px; font-weight:600;")
        top.addWidget(btn_back)
        top.addStretch()
        top.addWidget(title)
        layout.addLayout(top)

        # Tabs
        tabs = QHBoxLayout()
        tabs.setSpacing(8)
        self.current_tab = 'hiragana'

        self.tab_btns = {}
        for key, label in [
            ('hiragana', 'Hiragana'),
            ('katakana', 'Katakana'),
            ('kanji',    'Kanji N5'),
        ]:
            btn = QPushButton(label)
            style_btn(btn,
                      C['blue'] if key == 'hiragana' else C['surface'],
                      size=13, pad='8px 20px')
            btn.clicked.connect(lambda _, k=key: self._switch_tab(k))
            self.tab_btns[key] = btn
            tabs.addWidget(btn)
        tabs.addStretch()
        layout.addLayout(tabs)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{C['bg']}; }}
            QScrollBar:vertical {{
                background:{C['bg2']}; width:6px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:{C['border']}; border-radius:3px;
            }}
        """)
        layout.addWidget(self.scroll)

        self._switch_tab('hiragana')

    def _switch_tab(self, key):
        self.current_tab = key
        for k, btn in self.tab_btns.items():
            style_btn(btn,
                      C['blue'] if k == key else C['surface'],
                      size=13, pad='8px 20px')

        data   = self.all_data.get(key, [])
        stats  = {s[0]: s for s in get_all_stats()}

        grid_widget = QWidget()
        grid_widget.setStyleSheet(f"background:{C['bg']};")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(12)

        for i, card in enumerate(data):
            row, col = divmod(i, 5)
            f = self._make_card(card, stats.get(card['char']))
            grid.addWidget(f, row, col)

        self.scroll.setWidget(grid_widget)

    def _make_card(self, card, stat):
        f  = card_frame()
        fl = QVBoxLayout(f)
        fl.setContentsMargins(12, 12, 12, 12)
        fl.setSpacing(4)
        f.setFixedSize(140, 160)

        if stat and stat[2] > 0:
            acc   = stat[2] / stat[1] if stat[1] > 0 else 0
            color = C['green'] if acc >= 0.7 else C['gold']
        else:
            color = C['text3']

        char_lbl = QLabel(card['char'])
        char_lbl.setAlignment(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.AlignmentFlag.AlignCenter)
        char_lbl.setStyleSheet(f"font-size:40px; color:{color}; background:transparent;")

        nghia_lbl = QLabel(card.get('nghia_vi', ''))
        nghia_lbl.setAlignment(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.AlignmentFlag.AlignCenter)
        nghia_lbl.setWordWrap(True)
        nghia_lbl.setStyleSheet(f"font-size:11px; color:{C['text2']}; background:transparent;")

        romaji = card.get('romaji', '')
        if not romaji:
            romaji = card.get('onyomi', '')
        romaji_lbl = QLabel(romaji[:15] if romaji else '')
        romaji_lbl.setAlignment(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.AlignmentFlag.AlignCenter)
        romaji_lbl.setStyleSheet(f"font-size:10px; color:{C['text3']}; background:transparent;")

        if stat and stat[1] > 0:
            acc = stat[2] / stat[1]
            bar = QProgressBar()
            bar.setValue(int(acc * 100))
            bar.setFixedHeight(4)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background:{C['bg']}; border-radius:2px; }}
                QProgressBar::chunk {{
                    background:{C['green'] if acc >= 0.7 else C['gold']};
                    border-radius:2px;
                }}
            """)
            fl.addWidget(bar)

        fl.addWidget(char_lbl)
        fl.addWidget(nghia_lbl)
        fl.addWidget(romaji_lbl)

        return f
