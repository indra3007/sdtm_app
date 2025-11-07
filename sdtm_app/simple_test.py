"""
Simple test to see data viewer debug output
"""
import sys
sys.path.append('src')

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

print("Testing data viewer integration...")

app = QApplication(sys.argv)
window = MainWindow()
window.show()

# Minimal UI - just show the window and let user interact
print("Window opened. Please:")
print("1. Load AE_copy workflow") 
print("2. Click Execute")
print("3. Click on a data input node")
print("4. Observe debug output in terminal")

app.exec()