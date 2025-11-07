#!/usr/bin/env python3
"""
SDTM Application - No-Code PyQt6 GUI for Clinical Data Processing
Entry point for the application.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

def main():
    """Initialize and run the SDTM application."""
    # Set WebEngine attribute before creating QApplication
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    
    app = QApplication(sys.argv)
    
    # Import main window after QApplication is created
    from ui.main_window import MainWindow
    
    # Set application properties
    app.setApplicationName("SDTM Flow Builder")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Clinical Data Solutions")
    
    # Enable high DPI scaling for modern displays
    # Note: These attributes are handled automatically in PyQt6
    # app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Apply modern dark theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #3c3c3c;
            color: #ffffff;
            border-bottom: 1px solid #555555;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 12px;
        }
        QMenuBar::item:selected {
            background-color: #0078d4;
        }
        QToolBar {
            background-color: #3c3c3c;
            border: none;
            spacing: 2px;
        }
        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            padding: 6px;
            margin: 2px;
            border-radius: 4px;
        }
        QToolButton:hover {
            background-color: #0078d4;
            border-color: #0078d4;
        }
        QDockWidget {
            background-color: #2b2b2b;
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(float.png);
        }
        QDockWidget::title {
            background-color: #3c3c3c;
            padding: 8px;
            border-bottom: 1px solid #555555;
        }
    """)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()