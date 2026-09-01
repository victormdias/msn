"""
MSN Messenger Themes and QSS Stylesheet
Faithfully replicates the Windows Live Messenger / MSN 7.5/8.5 aqua, aero glass and gloss aesthetics.
"""

MSN_QSS = """
/* =========================================================
   MSN Messenger / Windows Live Messenger Master Stylesheet
   ========================================================= */

QWidget {
    font-family: "Segoe UI", "Tahoma", "Verdana", sans-serif;
    font-size: 13px;
    color: #2c3e50;
}

/* Main Windows Background */
QMainWindow, QDialog {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #dcedf9,
        stop: 0.15 #e8f4fc,
        stop: 0.85 #d2e7f7,
        stop: 1 #beddf2
    );
}

/* Header & Banner Areas */
#HeaderFrame {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff,
        stop: 0.3 #eef7fc,
        stop: 1 #cde5f7
    );
    border-bottom: 1px solid #9fc8e8;
    border-radius: 8px;
}

#ChatTopBanner {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #f0f7fd,
        stop: 0.6 #dcecf9,
        stop: 1 #c5e1f5
    );
    border-bottom: 1px solid #a3cce9;
}

/* Glossy MSN Buttons */
QPushButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff,
        stop: 0.5 #e2f1fc,
        stop: 0.51 #cde5f7,
        stop: 1 #badbf3
    );
    border: 1px solid #7eaed3;
    border-radius: 5px;
    padding: 6px 14px;
    font-weight: 500;
    color: #1a4a6e;
}

QPushButton:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff,
        stop: 0.5 #eef7fe,
        stop: 0.51 #dbeffe,
        stop: 1 #cbe7fc
    );
    border: 1px solid #4a94cb;
    color: #0b375b;
}

QPushButton:pressed {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #bcdcf5,
        stop: 1 #e0f0fa
    );
    border: 1px solid #3b81b5;
}

QPushButton:disabled {
    background: #eef2f5;
    border: 1px solid #c8d3dc;
    color: #8fa0af;
}

/* Primary Action Buttons (e.g., Login / Sign In) */
QPushButton#PrimaryBtn {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #85dc69,
        stop: 0.5 #57c732,
        stop: 0.51 #45b720,
        stop: 1 #329e10
    );
    border: 1px solid #2d8c0e;
    color: #ffffff;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 20px;
    border-radius: 6px;
}

QPushButton#PrimaryBtn:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #9bee80,
        stop: 0.5 #66da40,
        stop: 0.51 #52ca2c,
        stop: 1 #3bb414
    );
    border: 1px solid #237709;
}

/* Nudge Action Button */
QPushButton#NudgeBtn {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffebaa,
        stop: 0.5 #ffd557,
        stop: 0.51 #ffc82a,
        stop: 1 #f1b207
    );
    border: 1px solid #d49800;
    color: #6d4b00;
    font-weight: bold;
    border-radius: 4px;
    padding: 4px 10px;
}

QPushButton#NudgeBtn:hover {
    background: #ffe380;
    border: 1px solid #ad7b00;
}

/* Input Fields (QLineEdit, QTextEdit) */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #99c2e0;
    border-radius: 4px;
    padding: 6px;
    selection-background-color: #3b99db;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid #2980b9;
    background-color: #fafdff;
}

/* Contact List & Tree View */
QTreeWidget, QListWidget {
    background-color: #ffffff;
    border: 1px solid #a3c8e5;
    border-radius: 6px;
    padding: 4px;
    alternate-background-color: #f7fbfe;
}

QTreeWidget::item, QListWidget::item {
    padding: 6px 4px;
    border-radius: 4px;
    margin-bottom: 2px;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #eaf5fc,
        stop: 1 #d8ebfa
    );
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #c2e2f9,
        stop: 1 #a3d2f5
    );
    color: #0b375b;
}

/* Group Headers */
QTreeWidget::branch {
    background: transparent;
}

/* Combo Box */
QComboBox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff,
        stop: 1 #e5f1fa
    );
    border: 1px solid #99c2e0;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
}

QComboBox:hover {
    border: 1px solid #4a94cb;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #bad3e8;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #eef5fa;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #b5d5ed;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #8ec3e8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #a3c8e5;
    background: #ffffff;
    border-radius: 6px;
}

QTabBar::tab {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #e4f1fa,
        stop: 1 #cde3f5
    );
    border: 1px solid #9fc8e8;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:selected {
    background: #ffffff;
    border-bottom: 1px solid #ffffff;
    font-weight: bold;
    color: #0b375b;
}

/* ToolBar & Menu */
QToolBar {
    background: transparent;
    border: none;
    spacing: 4px;
}

QMenuBar {
    background: transparent;
    border-bottom: 1px solid #b8daf2;
}

QMenuBar::item:selected {
    background: #cce7fa;
    border-radius: 3px;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #99c2e0;
    padding: 4px;
    border-radius: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 16px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #e5f2fc;
    color: #0b375b;
}

/* Toast Notifications */
#ToastWidget {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff,
        stop: 0.15 #f2f9ff,
        stop: 0.85 #d6ebfb,
        stop: 1 #c2e1f8
    );
    border: 2px solid #5da9df;
    border-radius: 10px;
}
"""
