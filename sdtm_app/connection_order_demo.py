#!/usr/bin/env python3
"""
🎯 Correct Connection Order Demo
Shows the proper sequence: Orange FIRST, then Blue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QPointF
import pandas as pd

def demo_correct_connection_order():
    """Demonstrate the correct connection order."""
    
    app = QApplication(sys.argv)
    
    try:
        from ui.main_window import MainWindow
        
        window = MainWindow()
        window.show()
        
        # Create test data
        test_data = pd.DataFrame({
            'subject_id': ['SUBJ001', 'SUBJ002'],
            'age': [25, 30],
            'sex': ['M', 'F']
        })
        
        # Add nodes
        window.flow_canvas.add_input_node("test_data.sas7bdat", test_data)
        window.flow_canvas.add_transformation_node("Column Renamer", QPointF(350, 100))
        
        def show_connection_tutorial():
            """Show step-by-step connection tutorial."""
            
            msg = f"""
🎯 **CONNECTION ORDER TUTORIAL**

**Problem Identified:**
You clicked the BLUE (input) port first, but no connection was started.

**Correct Order:**

**Step 1:** 🔴 **Click ORANGE port FIRST**
• Find the orange circle on the LEFT side of data node
• This STARTS the connection
• You'll see a dotted line following your mouse

**Step 2:** 🔵 **Click BLUE port SECOND**  
• Find the blue circle on the LEFT side of Column Renamer
• This COMPLETES the connection
• You'll see a solid blue line connecting the nodes

**Visual Guide:**
```
[Data Node]🔴  ←── CLICK THIS FIRST (orange)
     │
     │ (drag/move to)
     ▼
[Column Renamer]🔵  ←── CLICK THIS SECOND (blue)
```

**Why it failed:**
- You clicked blue port first (no start point set)
- Need to establish start point with orange port first

**Try again with correct order:**
1. Orange FIRST (data output)
2. Blue SECOND (renamer input)

**Alternative:** Use the "🔗 Auto-Connect" button in toolbar!
            """
            
            QMessageBox.information(window, "🎯 Connection Tutorial", msg)
        
        # Show tutorial after UI loads
        QTimer.singleShot(1000, show_connection_tutorial)
        
        return app.exec()
        
    except Exception as e:
        QMessageBox.critical(None, "❌ Demo Failed", f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    print("🎯 Starting Connection Order Demo...")
    print("This shows the correct sequence: Orange FIRST, then Blue")
    
    exit_code = demo_correct_connection_order()
    sys.exit(exit_code)