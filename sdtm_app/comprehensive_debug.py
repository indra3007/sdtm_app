#!/usr/bin/env python3
"""
🔧 Comprehensive Connection Debug Tool
Tests all aspects of the connection system with detailed logging
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, QPointF
import pandas as pd

def comprehensive_connection_test():
    """Test all connection system components."""
    
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
        window.flow_canvas.add_input_node("debug_test.sas7bdat", test_data)
        window.flow_canvas.add_transformation_node("Column Renamer", QPointF(350, 100))
        
        def show_debug_helper():
            """Show debug helper dialog."""
            
            # Create helper widget
            helper = QWidget()
            helper.setWindowTitle("🔧 Connection Debug Helper")
            helper.resize(500, 400)
            
            layout = QVBoxLayout(helper)
            
            # Status info
            status_label = QLabel(f"""
🔧 CONNECTION DEBUG STATUS

Nodes Created: {len(window.flow_canvas.nodes)}
Current Connections: {len(window.flow_canvas.connections)}
Connection Mode: {window.flow_canvas.connection_mode}
Start Port Set: {window.flow_canvas.connection_start_port is not None}

🎯 DEBUG ACTIONS:
            """)
            status_label.setWordWrap(True)
            layout.addWidget(status_label)
            
            # Test buttons
            test1_btn = QPushButton("🧪 Test Port Detection")
            test1_btn.clicked.connect(lambda: test_port_detection(window))
            layout.addWidget(test1_btn)
            
            test2_btn = QPushButton("🔴 Simulate Output Port Click")
            test2_btn.clicked.connect(lambda: simulate_output_click(window))
            layout.addWidget(test2_btn)
            
            test3_btn = QPushButton("🔵 Simulate Input Port Click") 
            test3_btn.clicked.connect(lambda: simulate_input_click(window))
            layout.addWidget(test3_btn)
            
            auto_btn = QPushButton("🤖 Force Auto-Connection")
            auto_btn.clicked.connect(lambda: force_auto_connection(window))
            layout.addWidget(auto_btn)
            
            # Instructions
            instructions = QLabel("""
🔗 MANUAL CONNECTION INSTRUCTIONS:

Since auto methods work but manual doesn't, try this:

1. 🔴 Look for LARGE ORANGE circle on data node
2. 👆 Click EXACTLY in center of orange circle
3. 🖱️ Should see dotted line start following mouse
4. 🔵 Click EXACTLY in center of blue circle on renamer
5. ✅ Should see solid blue line connect nodes

If it still doesn't work, use "Force Auto-Connection" above.
            """)
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            helper.show()
        
        def test_port_detection(window):
            """Test if ports are properly detected."""
            try:
                results = []
                
                for i, node in enumerate(window.flow_canvas.nodes):
                    results.append(f"Node {i}: {node.title}")
                    results.append(f"  Input ports: {len(node.input_ports)}")
                    results.append(f"  Output ports: {len(node.output_ports)}")
                    
                    # Test port positions and canvas refs
                    if len(node.output_ports) > 0:
                        port = node.output_ports[0]
                        results.append(f"  Output port canvas: {port.canvas is not None}")
                        results.append(f"  Output port pos: {port.get_scene_position()}")
                        
                    if len(node.input_ports) > 0:
                        port = node.input_ports[0]
                        results.append(f"  Input port canvas: {port.canvas is not None}")
                        results.append(f"  Input port pos: {port.get_scene_position()}")
                        
                    results.append("")
                
                QMessageBox.information(window, "🧪 Port Detection Results", "\n".join(results))
                
            except Exception as e:
                QMessageBox.critical(window, "❌ Test Failed", f"Error: {str(e)}")
        
        def simulate_output_click(window):
            """Simulate clicking the output port."""
            try:
                if len(window.flow_canvas.nodes) > 0:
                    data_node = window.flow_canvas.nodes[0]
                    if len(data_node.output_ports) > 0:
                        output_port = data_node.output_ports[0]
                        print("🧪 Simulating output port click...")
                        window.flow_canvas.start_connection(output_port)
                        
                        QMessageBox.information(window, "🔴 Output Click", 
                                              f"Simulated output port click.\n\n"
                                              f"Connection mode: {window.flow_canvas.connection_mode}\n"
                                              f"Start port set: {window.flow_canvas.connection_start_port is not None}\n\n"
                                              f"Now try clicking the blue port on Column Renamer!")
                    else:
                        QMessageBox.warning(window, "❌ Error", "No output ports found")
                else:
                    QMessageBox.warning(window, "❌ Error", "No nodes found")
                    
            except Exception as e:
                QMessageBox.critical(window, "❌ Error", f"Simulation failed: {str(e)}")
        
        def simulate_input_click(window):
            """Simulate clicking the input port."""
            try:
                if len(window.flow_canvas.nodes) > 1:
                    rename_node = window.flow_canvas.nodes[1]
                    if len(rename_node.input_ports) > 0:
                        input_port = rename_node.input_ports[0]
                        print("🧪 Simulating input port click...")
                        window.flow_canvas.end_connection(input_port)
                        
                        connections_count = len(window.flow_canvas.connections)
                        QMessageBox.information(window, "🔵 Input Click", 
                                              f"Simulated input port click.\n\n"
                                              f"Total connections: {connections_count}\n"
                                              f"Connection created: {'✅ Yes' if connections_count > 0 else '❌ No'}")
                    else:
                        QMessageBox.warning(window, "❌ Error", "No input ports found")
                else:
                    QMessageBox.warning(window, "❌ Error", "Need at least 2 nodes")
                    
            except Exception as e:
                QMessageBox.critical(window, "❌ Error", f"Simulation failed: {str(e)}")
        
        def force_auto_connection(window):
            """Force an automatic connection."""
            try:
                if len(window.flow_canvas.nodes) >= 2:
                    data_node = window.flow_canvas.nodes[0]
                    rename_node = window.flow_canvas.nodes[1]
                    
                    if (len(data_node.output_ports) > 0 and len(rename_node.input_ports) > 0):
                        output_port = data_node.output_ports[0]
                        input_port = rename_node.input_ports[0]
                        
                        # Create connection directly
                        connection = NodeConnection(output_port, input_port)
                        window.flow_canvas.scene.addItem(connection)
                        window.flow_canvas.connections.append(connection)
                        
                        QMessageBox.information(window, "🤖 Auto-Connection", 
                                              "✅ Connection forced successfully!\n\n"
                                              "Now try:\n"
                                              "1. Click Column Renamer node\n"
                                              "2. Configure properties in right panel")
                    else:
                        QMessageBox.warning(window, "❌ Error", "Nodes missing required ports")
                else:
                    QMessageBox.warning(window, "❌ Error", "Need at least 2 nodes")
                    
            except Exception as e:
                QMessageBox.critical(window, "❌ Error", f"Auto-connection failed: {str(e)}")
        
        # Show helper after UI loads
        QTimer.singleShot(1000, show_debug_helper)
        
        return app.exec()
        
    except Exception as e:
        QMessageBox.critical(None, "❌ Debug Tool Failed", f"Error: {str(e)}")
        print(f"Debug tool error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("🔧 Starting Comprehensive Connection Debug...")
    print("This will help identify exactly why manual connections aren't working.")
    
    exit_code = comprehensive_connection_test()
    sys.exit(exit_code)