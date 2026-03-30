from PyQt6.QtWidgets import QPushButton, QFrame
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

C = {
    'bg'      : '#0F0F14',
    'bg2'     : '#16161E',
    'bg3'     : '#1E1E2E',
    'surface' : '#24243A',
    'border'  : '#2E2E4A',
    'red'     : '#E85D75',
    'gold'    : '#F5C842',
    'green'   : '#4ECDC4',
    'blue'    : '#6C63FF',
    'text'    : '#E8E8F0',
    'text2'   : '#9090B0',
    'text3'   : '#5A5A7A',
    'white'   : '#FFFFFF',
}


def style_btn(btn, bg=C['blue'], fg=C['white'], size=14, pad='12px 24px'):
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {bg};
            color: {fg};
            border: none;
            border-radius: 10px;
            padding: {pad};
            font-size: {size}px;
            font-weight: 600;
        }}
        QPushButton:hover   {{ background: {bg}DD; }}
        QPushButton:pressed {{ background: {bg}AA; }}
        QPushButton:disabled {{
            background: {C['border']};
            color: {C['text3']};
        }}
    """)


def card_frame(parent=None):
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background: {C['surface']};
            border: 1px solid {C['border']};
            border-radius: 16px;
        }}
    """)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setColor(QColor(0, 0, 0, 80))
    shadow.setOffset(0, 4)
    f.setGraphicsEffect(shadow)
    return f
