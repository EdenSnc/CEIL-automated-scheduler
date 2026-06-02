# theme.py
"""
Premium white and emerald green minimalist aesthetic.
"""

QSS_STYLE = """
QMainWindow {
    background-color: #FFFFFF;
}

QWidget {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    color: #334155;
}

QTabWidget::panel {
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    border-radius: 12px;
}

QTabBar::tab {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #64748B;
}

QTabBar::tab:selected {
    background: #FFFFFF;
    border-bottom: 2px solid #1B4332;
    color: #1B4332;
    font-weight: 600;
}

QGroupBox {
    border: 1px solid #F1F5F9;
    border-radius: 12px;
    margin-top: 20px;
    padding-top: 16px;
    font-weight: 600;
    color: #1B4332;
    background-color: #FFFFFF;
}

QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #E2E8F0;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #1B4332;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #1B4332;
    border: 1px solid #112A1F;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QPushButton {
    background-color: #1B4332;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2D6A4F;
}

QPushButton#SolverButton {
    background-color: #112A1F;
    font-size: 13px;
    padding: 12px;
    border-radius: 8px;
}

QPushButton#SolverButton:hover {
    background-color: #1B4332;
}

QPushButton#DangerButton {
    background-color: #FFF1F2;
    color: #9F1239;
    border: none;
}

QPushButton#DangerButton:hover {
    background-color: #FFE4E6;
}

QTableWidget {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    background-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    padding: 8px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid #E2E8F0;
}

QStatusBar {
    background-color: #F8FAFC;
    color: #64748B;
    border-top: 1px solid #E2E8F0;
}

QTextEdit#DebugLogConsole {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    background-color: #0F172A;
    color: #E2E8F0;
    border-radius: 6px;
    border: 1px solid #334155;
}
"""