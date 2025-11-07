#!/usr/bin/env python3
"""
🔧 Manual Connection Helper
Provides multiple ways to create connections when drag-drop isn't working
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, QPointF
import pandas as pd

def connection_helper():
    """Helper tool for manual connections."""
    
    app = QApplication(sys.argv)
    
    try:
        from ui.main_window import MainWindow
        from ui.flow_canvas import NodeConnection
        
        window = MainWindow()
        window.show()
        
        # Create test data
        test_data = pd.DataFrame({
            'subject_id': ['SUBJ001', 'SUBJ002'],
            'age': [25, 30],
            'sex': ['M', 'F'],
            'race': ['WHITE', 'BLACK']
        })
        
        # Add nodes
        window.flow_canvas.add_input_node("manual_test.sas7bdat", test_data)
        window.flow_canvas.add_transformation_node("Column Renamer", QPointF(350, 100))
        
        def show_connection_helper():
            """Show connection helper dialog."""
            
            # Create helper widget
            helper = QWidget()
            helper.setWindowTitle("🔗 Connection Helper")
            helper.resize(400, 300)
            
            layout = QVBoxLayout(helper)
            
            # Instructions
            instructions = QLabel("""
🎯 MANUAL CONNECTION TROUBLESHOOTING

Current Status:
✅ Data node created (test data loaded)
✅ Column Renamer node created
❌ Need to connect them manually

🔧 Multiple Connection Methods:

Method 1: Drag & Drop (Primary)
1. Look for LARGE colored circles on nodes
2. 🔴 Orange circle = OUTPUT (start here)
3. 🔵 Blue circle = INPUT (drag to here)
4. Click and HOLD on orange, drag to blue

Method 2: Right-Click Menu (Alternative)  
1. Right-click on orange port
2. Select "Start Connection"
3. Right-click on blue port
4. Select "Complete Connection"

Method 3: Automatic (Fallback)
Use button below to create connection automatically
            """)
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            # Auto-connect button
            auto_btn = QPushButton("🤖 Auto-Connect Nodes")
            auto_btn.clicked.connect(lambda: auto_connect_nodes(window))
            layout.addWidget(auto_btn)
            
            # Debug button
            debug_btn = QPushButton("🔍 Debug Connection System")
            debug_btn.clicked.connect(lambda: debug_ports(window))
            layout.addWidget(debug_btn)
            
            # Test ports button
            test_btn = QPushButton("🧪 Test Port Clicks")
            test_btn.clicked.connect(lambda: test_port_interaction(window))
            layout.addWidget(test_btn)
            
            helper.show()
        
        def auto_connect_nodes(window):
            """Automatically connect the nodes."""
            try:
                if len(window.flow_canvas.nodes) >= 2:
                    data_node = window.flow_canvas.nodes[0]
                    rename_node = window.flow_canvas.nodes[1]
                    
                    if (len(data_node.output_ports) > 0 and 
                        len(rename_node.input_ports) > 0):
                        
                        output_port = data_node.output_ports[0]
                        input_port = rename_node.input_ports[0]
                        
                        # Create connection
                        connection = NodeConnection(output_port, input_port)
                        window.flow_canvas.scene.addItem(connection)
                        window.flow_canvas.connections.append(connection)
                        
                        QMessageBox.information(window, "✅ Success", 
                                              "🔗 Auto-connection created!\n\nYou can now:\n1. Click Column Renamer node\n2. Configure properties\n3. Add column mappings")
                    else:
                        QMessageBox.warning(window, "❌ Error", "Nodes don't have required ports")
                else:
                    QMessageBox.warning(window, "❌ Error", "Not enough nodes to connect")
                    
            except Exception as e:
                QMessageBox.critical(window, "❌ Error", f"Auto-connect failed: {str(e)}")
        
        def debug_ports(window):
            """Debug port setup."""
            debug_info = []
            
            for i, node in enumerate(window.flow_canvas.nodes):
                debug_info.append(f"Node {i}: {node.title}")
                debug_info.append(f"  Input ports: {len(node.input_ports)}")
                debug_info.append(f"  Output ports: {len(node.output_ports)}")
                
                if hasattr(node, 'output_ports') and len(node.output_ports) > 0:
                    port = node.output_ports[0]
                    debug_info.append(f"  Output port canvas ref: {port.canvas is not None}")
                    debug_info.append(f"  Output port position: {port.get_scene_position()}")
                    
                if hasattr(node, 'input_ports') and len(node.input_ports) > 0:
                    port = node.input_ports[0]
                    debug_info.append(f"  Input port canvas ref: {port.canvas is not None}")
                    debug_info.append(f"  Input port position: {port.get_scene_position()}")
                    
                debug_info.append("")
            
            QMessageBox.information(window, "🔍 Debug Info", "\n".join(debug_info))
        
        def test_port_interaction(window):
            """Test port interaction programmatically."""
            try:
                if len(window.flow_canvas.nodes) >= 2:
                    data_node = window.flow_canvas.nodes[0]
                    
                    if len(data_node.output_ports) > 0:
                        output_port = data_node.output_ports[0]
                        
                        # Simulate port click
                        print("🧪 Testing port interaction...")
                        window.flow_canvas.start_connection(output_port)
                        
                        QMessageBox.information(window, "🧪 Test", 
                                              "Port click test executed.\nCheck console for debug output.\n\nLook for colored dotted line from orange port!")
                    else:
                        QMessageBox.warning(window, "❌ Error", "No output ports found")
                else:
                    QMessageBox.warning(window, "❌ Error", "Not enough nodes")
                    
            except Exception as e:
                QMessageBox.critical(window, "❌ Error", f"Port test failed: {str(e)}")
        
        # Show helper after UI loads
        QTimer.singleShot(1000, show_connection_helper)
        
        return app.exec()
        
    except Exception as e:
        QMessageBox.critical(None, "❌ Helper Failed", f"Error: {str(e)}")
        print(f"Helper error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("🔗 Starting Manual Connection Helper...")
    print("This provides multiple ways to create connections!")
    
    exit_code = connection_helper()
    sys.exit(exit_code)