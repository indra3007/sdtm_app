"""
FINAL DATA VIEWER INTEGRATION TEST

This script will help verify that the data viewer integration is working correctly.
"""
import sys
sys.path.append('src')

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

print("=== FINAL DATA VIEWER INTEGRATION TEST ===")
print("Starting application...")

app = QApplication(sys.argv)
window = MainWindow()
window.show()

print("\n✅ Application launched successfully!")
print("\n📋 PLEASE FOLLOW THESE EXACT STEPS:")
print("1. Click 'File' -> 'Open Project' -> Select 'STUDY XYZ' project")
print("2. Load the 'AE_copy' workflow from the workflow list")
print("3. Click the '🚀 Execute' button in the toolbar")
print("4. Wait for all nodes to show green checkmarks (✅)")
print("5. Click on ANY node (data input, transform, or output node)")
print("6. Look at the data viewer panel on the right")
print("7. Check the terminal output for debug messages starting with '📊 DATA VIEWER:'")

print("\n🔍 EXPECTED RESULTS:")
print("- You should see debug messages like '📊 DATA VIEWER: set_dataframe called'")
print("- You should see dataframe shape information")
print("- You should see data displayed in the data viewer panel")
print("- If using ag-Grid: Web view should show interactive table")
print("- If using fallback: QTableWidget should show data")

print("\n❗ IF DATA DOESN'T APPEAR:")
print("- Check terminal for '📊 DATA VIEWER:' messages")
print("- Check terminal for '🔄 AUTO REFRESH:' messages") 
print("- Check terminal for 'CACHE INFO:' messages")
print("- Try clicking on different nodes")
print("- Try clicking Execute again")

print("\n🚀 Starting application - perform the test steps above...")

app.exec()