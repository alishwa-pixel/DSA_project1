# theme.py - visual style only (no logic). Delete the apply_theme(app) line in main.py to go back.
# Cream + camel "classic chic" palette. Change a colour here and the whole app follows.
from PyQt5.QtGui import QFont

BG        = "#FAF6EF"   # cream page
PANEL     = "#FFFDF9"   # warm white cards
INPUT     = "#FFFFFF"
BORDER    = "#E6DAC7"   # soft sand
TEXT      = "#3B2F27"   # espresso
MUTED     = "#8C7D6D"
ACCENT    = "#A9763F"   # camel
ACCENT_HOVER = "#8F6230"
ON_ACCENT = "#FFFFFF"
ROW_ALT   = "#F7F0E4"
SELECT    = "#EBD9BD"
OFF_BG, OFF_TEXT, OFF_BORDER = "#F1EADF", "#B5A898", "#E9DFCF"

STYLE = f"""
* {{ font-family: 'Segoe UI', 'Inter', Arial; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QDialog, QWidget#root, QScrollArea {{ background: {BG}; border: none; }}
QHeaderView {{ background: {BG}; border: none; }}
QLabel {{ background: transparent; }}
QLabel#title {{ font-family: Georgia, 'Playfair Display', serif; font-size: 24pt;
                font-weight: 600; color: {TEXT}; }}
QLabel#subtitle, QLabel#hint {{ color: {MUTED}; font-size: 9pt; }}

QGroupBox {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
             margin-top: 14px; padding: 14px 10px 8px 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px;
                    color: {ACCENT}; font-weight: 600; background: {BG}; }}
QGroupBox:disabled {{ color: {MUTED}; }}

QLineEdit, QSpinBox, QComboBox {{ background: {INPUT}; border: 1px solid {BORDER};
                    border-radius: 8px; padding: 5px 10px; min-height: 22px; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{ background: {INPUT}; border: 1px solid {BORDER};
                    selection-background-color: {SELECT}; selection-color: {TEXT}; outline: 0; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: {OFF_TEXT}; background: {OFF_BG}; }}

QPushButton {{ background: {INPUT}; border: 1px solid {BORDER}; border-radius: 8px;
               padding: 6px 16px; min-height: 22px; }}
QPushButton:hover {{ border-color: {ACCENT}; background: {ROW_ALT}; }}
QPushButton:pressed {{ background: {SELECT}; }}
QPushButton:disabled {{ color: {OFF_TEXT}; background: {OFF_BG}; border-color: {OFF_BORDER}; }}
QPushButton#primary {{ background: {ACCENT}; border: none; color: {ON_ACCENT}; font-weight: 700; }}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primary:disabled {{ background: #D9C6AB; color: #FFF8EC; }}

QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #CDBB9F;
                        border-radius: 4px; background: {INPUT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QTableWidget {{ background: {PANEL}; alternate-background-color: {ROW_ALT};
                border: 1px solid {BORDER}; border-radius: 12px; gridline-color: transparent;
                selection-background-color: {SELECT}; selection-color: {TEXT}; }}
QTableWidget::item {{ padding: 4px 8px; border: none; }}
QHeaderView::section {{ background: {BG}; color: {ACCENT}; font-weight: 700;
                        padding: 8px; border: none; border-bottom: 2px solid {ACCENT}; }}
QTableCornerButton::section {{ background: {BG}; border: none; }}

QTextEdit {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
             padding: 6px; font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; }}

QProgressBar {{ background: {INPUT}; border: 1px solid {BORDER}; border-radius: 8px;
                text-align: center; min-height: 16px; color: {TEXT}; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 7px; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle {{ background: #D8C7AC; border-radius: 5px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {ACCENT}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QMessageBox {{ background: {PANEL}; }}
QToolTip {{ background: {PANEL}; color: {TEXT}; border: 1px solid {BORDER}; }}
"""


def apply_theme(app):
    app.setStyle("Fusion")          # same look on every Windows version
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLE)
