#!/usr/bin/env python3
"""
🔗 Connection Demo - Shows How Nodes Connect
This demo automatically creates and connects nodes to demonstrate the flow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QPointF
import pandas as pd

def demo_connection_workflow():
    """Demonstrate complete connection workflow."""
    
    app = QApplication(sys.argv)
    
    try:
        from ui.main_window import MainWindow
        from ui.flow_canvas import NodeConnection
        
        window = MainWindow()
        window.show()
        
        # Create test data (simulating loaded SAS file)
        test_data = pd.DataFrame({
            'subject_id': ['SUBJ001', 'SUBJ002', 'SUBJ003'], 
            'age': [25, 30, 35],
            'sex': ['M', 'F', 'M'],
            'race': ['WHITE', 'BLACK', 'ASIAN'],
            'adverse_event': ['Headache', 'Nausea', 'Fatigue']
        })
        
        print("📊 Creating test data node...")
        
        # Step 1: Add data input node (like loading SAS file)
        window.flow_canvas.add_input_node("test_dm.sas7bdat", test_data)
        data_node = window.flow_canvas.nodes[0]  # First node is the data source
        
        # Step 2: Add Column Renamer transformation node  
        print("🏷️ Creating Column Renamer node...")
        window.flow_canvas.add_transformation_node("Column Renamer", QPointF(300, 100))
        rename_node = window.flow_canvas.nodes[1]  # Second node is the renamer
        
        def create_auto_connection():
            """Automatically create connection between nodes."""
            try:
                print("🔗 Creating connection...")
                
                # Get ports from both nodes
                data_output_port = data_node.output_ports[0]  # Output port from data
                rename_input_port = rename_node.input_ports[0]  # Input port to renamer
                
                print(f"📤 Data node output port: {data_output_port}")
                print(f"📥 Rename node input port: {rename_input_port}")
                
                # Create the connection programmatically
                connection = NodeConnection(data_output_port, rename_input_port)
                window.flow_canvas.scene.addItem(connection)
                window.flow_canvas.connections.append(connection)
                
                print("✅ Connection created successfully!")
                
                # Show connection details
                def show_connection_details():
                    msg = f"""
🎯 **Connection Successfully Created!**

**Data Flow:**
📊 test_dm.sas7bdat → 🏷️ Column Renamer

**Connection Details:**
• Source: {data_node.title} (Output Port)
• Target: {rename_node.title} (Input Port)  
• Status: ✅ Connected

**Available Data Columns:**
{', '.join(test_data.columns.tolist())}

**Next Steps:**
1. 👆 **Click the Column Renamer node**
2. ⚙️ **Property panel will show on right**
3. 🏷️ **Add column mappings:**
   - subject_id → USUBJID
   - age → AGE  
   - sex → SEX
   - race → RACE
   - adverse_event → AETERM

4. 💡 **Use "Suggest SDTM Names"** for automatic mapping
5. ▶️ **Execute flow** to see transformed data

**You can now:**
• Click nodes to configure properties
• Add more transformation nodes  
• Create additional connections
• Build complete SDTM flows
                    """
                    
                    QMessageBox.information(window, "🔗 Connection Demo", msg)
                
                QTimer.singleShot(500, show_connection_details)
                
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                QMessageBox.critical(window, "❌ Connection Error", 
                                   f"Failed to create connection:\n{str(e)}")
        
        # Create connection after UI is fully loaded
        QTimer.singleShot(1000, create_auto_connection)
        
        return app.exec()
        
    except Exception as e:
        QMessageBox.critical(None, "❌ Demo Failed", f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    print("🚀 Starting Connection Demo...")
    print("This will show you exactly how test_dm connects to Column Renamer!")
    
    exit_code = demo_connection_workflow()
    sys.exit(exit_code)