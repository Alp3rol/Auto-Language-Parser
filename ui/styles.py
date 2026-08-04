"""
A.L.P. (Auto Language Parser) Merkezi QSS Stil ve Tema Modülü (Obsidian Dark Theme)
"""

OBSIDIAN_DARK_MAIN = """
QWidget#centralWidget {
    background-color: #09090B;
    border: 1px solid #27272A;
    border-radius: 10px;
}
QWidget {
    color: #F4F4F5;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QTabWidget::pane {
    border: 1px solid #27272A;
    background-color: #18181B;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: transparent;
    color: #A1A1AA;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 12px;
    border-radius: 6px;
    margin: 2px;
}
QTabBar::tab:selected {
    background-color: #27272A;
    color: #F4F4F5;
}
QTabBar::tab:hover:!selected {
    background-color: #18181B;
    color: #FFFFFF;
}
QTextEdit {
    background-color: #09090B;
    color: #F4F4F5;
    border: 1px solid #27272A;
    border-radius: 6px;
    padding: 10px;
    font-size: 13px;
    line-height: 1.4;
}
"""

PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: #0078D4;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    border-radius: 6px;
    border: none;
}
QPushButton:hover {
    background-color: #106EBE;
}
"""

ACCENT_BUTTON_GREEN = """
QPushButton {
    background-color: #18181B;
    color: #00FF88;
    font-size: 12px;
    font-weight: 700;
    border-radius: 6px;
    border: 1px solid #00FF88;
}
QPushButton:hover {
    background-color: #00FF88;
    color: #000000;
}
"""

CARD_FRAME_STYLE = """
QFrame {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
}
"""
