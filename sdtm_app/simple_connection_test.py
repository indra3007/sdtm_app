#!/usr/bin/env python3
"""
🔧 Simple Connection Test
Minimal test to isolate connection issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QPointF
import pandas as pd

def simple_connection_test():
    """Simple connection test with direct port interaction."""
    
    app = QApplication(sys.argv)
    
    try:
        from ui.main_window import MainWindow
        from ui.flow_canvas import NodeConnection
        
        window = MainWindow()
        window.show()
        
        # Create minimal test data
        test_data = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        
        # Add nodes
        window.flow_canvas.add_input_node("test.sas7bdat", test_data)
        window.flow_canvas.add_transformation_node("Column Renamer", QPointF(300, 100))
        
        def test_direct_connection():
            """Test connection directly without mouse events."""
            try:
                print("🧪 Starting direct connection test...")
                
                # Get nodes
                data_node = window.flow_canvas.nodes[0]
                rename_node = window.flow_canvas.nodes[1]
                
                print(f"📊 Data node: {data_node.title}")
                print(f"🏷️ Rename node: {rename_node.title}")
                
                # Check ports
                print(f"📤 Data output ports: {len(data_node.output_ports)}")
                print(f"📥 Rename input ports: {len(rename_node.input_ports)}")
                
                if len(data_node.output_ports) > 0 and len(rename_node.input_ports) > 0:
                    output_port = data_node.output_ports[0]
                    input_port = rename_node.input_ports[0]
                    
                    print(f"🔴 Output port: {output_port.port_type}")
                    print(f"🔵 Input port: {input_port.port_type}")
                    
                    # Test canvas references
                    print(f"🖼️ Output port canvas: {output_port.canvas is not None}")
                    print(f"🖼️ Input port canvas: {input_port.canvas is not None}")
                    
                    # Test start_connection method directly
                    print("🚀 Testing start_connection...")
                    window.flow_canvas.start_connection(output_port)
                    
                    print(f"🔗 Connection mode: {window.flow_canvas.connection_mode}")
                    print(f"📍 Start port set: {window.flow_canvas.connection_start_port is not None}")
                    
                    # Test end_connection method
                    print("🎯 Testing end_connection...")
                    window.flow_canvas.end_connection(input_port)
                    
                    # Check if connection was created
                    connections_count = len(window.flow_canvas.connections)
                    print(f"🔗 Connections created: {connections_count}")
                    
                    if connections_count > 0:
                        result_msg = """
✅ **DIRECT CONNECTION TEST SUCCESSFUL!**

The connection system works programmatically.

**Issue diagnosis:**
The problem is likely with mouse event handling, not the connection logic itself.

**Solutions to try:**
1. **Larger ports**: Ports are now bigger (24x24 pixels)
2. **Right-click menu**: Try right-clicking ports for menu
3. **Direct approach**: Use the auto-connect button
4. **Mouse precision**: Click exactly in center of ports

**Next steps:**
1. Try the auto-connect button in the helper
2. Check if ports are visible and large enough
3. Try different mouse click techniques
                        """
                        QMessageBox.information(window, "✅ Test Success", result_msg)
                    else:
                        QMessageBox.warning(window, "❌ Test Failed", 
                                          "Direct connection method failed.\nCheck console for error details.")
                else:
                    QMessageBox.critical(window, "❌ Port Error", 
                                       "Nodes don't have the required ports!")
                    
            except Exception as e:
                print(f"❌ Test error: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(window, "❌ Test Error", f"Test failed: {str(e)}")
        
        # Run test after UI loads
        QTimer.singleShot(1500, test_direct_connection)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("🧪 Starting Simple Connection Test...")
    print("This will test the connection mechanism directly.")
    
    exit_code = simple_connection_test()
    sys.exit(exit_code)