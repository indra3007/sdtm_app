"""
Flow Canvas - Visual node-based interface for data transformations
Handles drag-drop, node connections, and flow visualization.
"""

import os
import pandas as pd
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QMenu,
    QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPainterPath, QLinearGradient, QRadialGradient, QTransform
import math


class FlowCanvas(QGraphicsView):
    """Main canvas for visual flow building."""
    
    # Signals
    node_selected = pyqtSignal(object)  # Selected node
    flow_changed = pyqtSignal()  # Flow structure changed
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.setup_canvas()
        self.nodes = []
        self.connections = []
        self.connection_mode = False
        self.temp_connection = None
        self.connection_start_port = None
        
    def setup_canvas(self):
        """Configure enhanced canvas appearance and behavior."""
        # Set large scene size for complex workflows
        self.scene.setSceneRect(-3000, -3000, 6000, 6000)
        
        # Enhanced canvas styling with light purple gradient background
        gradient = QRadialGradient(0, 0, 1000)
        gradient.setColorAt(0, QColor(230, 220, 240))  # Light purple center
        gradient.setColorAt(1, QColor(210, 195, 225))  # Slightly darker purple edges
        self.setBackgroundBrush(QBrush(gradient))
        
        # Enhanced rendering
        self.setRenderHints(QPainter.RenderHint.Antialiasing | 
                           QPainter.RenderHint.SmoothPixmapTransform |
                           QPainter.RenderHint.TextAntialiasing)
        
        # Enable advanced interaction - scroll bar navigation preferred
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setAcceptDrops(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Ensure scroll bars are always available
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Mouse tracking for connections
        self.setMouseTracking(True)
        
        # Enable focus for key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        # Enhanced grid pattern
        self.draw_enhanced_grid()
        
    def draw_enhanced_grid(self):
        """Draw enhanced background grid with modern styling."""
        grid_size = 25  # Slightly larger grid
        scene_rect = self.scene.sceneRect()
        
        # Create pen for grid lines
        light_pen = QPen(QColor(55, 55, 65, 80), 0.5)  # Light grid lines
        heavy_pen = QPen(QColor(75, 75, 85, 120), 1.0)  # Heavy grid lines every 5th
        
        # Vertical lines
        x = scene_rect.left()
        count = 0
        while x < scene_rect.right():
            pen = heavy_pen if count % 5 == 0 else light_pen
            line = self.scene.addLine(x, scene_rect.top(), x, scene_rect.bottom(), pen)
            line.setZValue(-1000)  # Behind everything
            x += grid_size
            count += 1
            
        # Horizontal lines
        y = scene_rect.top()
        count = 0
        while y < scene_rect.bottom():
            pen = heavy_pen if count % 5 == 0 else light_pen
            line = self.scene.addLine(scene_rect.left(), y, scene_rect.right(), y, pen)
            line.setZValue(-1000)  # Behind everything
            y += grid_size
            count += 1
            
        # Add subtle center cross for reference
        center_pen = QPen(QColor(100, 100, 120, 150), 2.0)
        center_x = self.scene.addLine(0, scene_rect.top()/4, 0, scene_rect.bottom()/4, center_pen)
        center_y = self.scene.addLine(scene_rect.left()/4, 0, scene_rect.right()/4, 0, center_pen)
        center_x.setZValue(-999)
        center_y.setZValue(-999)
        
    def wheelEvent(self, event):
        """Enhanced zoom functionality with smooth scaling."""
        # Get the zoom factor
        zoom_factor = 1.15
        
        # Check if Ctrl is pressed for zooming
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom in or out
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1/zoom_factor, 1/zoom_factor)
        else:
            # Normal scrolling
            super().wheelEvent(event)
    
    def zoom_in(self):
        """Zoom in on the canvas."""
        self.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out on the canvas."""
        self.scale(0.8, 0.8)
        
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.setTransform(QTransform())
        self.scale(1.0, 1.0)
        print("📏 Zoom reset to 100%")
        
    def set_optimal_zoom(self):
        """Set optimal zoom level for current workflow."""
        if self.nodes:
            # Get bounding rect of all nodes
            rect = None
            for node in self.nodes:
                if rect is None:
                    rect = node.sceneBoundingRect()
                else:
                    rect = rect.united(node.sceneBoundingRect())
            
            if rect:
                # Calculate optimal zoom (similar to fit_to_window but with better limits)
                padding = 150
                rect.adjust(-padding, -padding, padding, padding)
                
                view_rect = self.viewport().rect()
                scale_x = view_rect.width() / rect.width()
                scale_y = view_rect.height() / rect.height()
                target_scale = min(scale_x, scale_y)
                
                # Better zoom limits for optimal viewing
                min_scale = 0.5  # Don't go below 50%
                max_scale = 1.5  # Don't go above 150%
                
                target_scale = max(min_scale, min(max_scale, target_scale))
                
                # Apply the zoom
                self.setTransform(QTransform())
                self.scale(target_scale, target_scale)
                self.centerOn(rect.center())
                
                print(f"📏 Set optimal zoom: {target_scale:.2f}x")
            else:
                self.reset_zoom()
        else:
            self.reset_zoom()
        
    def fit_to_window(self):
        """Fit all nodes to the window with reasonable zoom limits."""
        if self.nodes:
            # Get bounding rect of all nodes
            rect = None
            for node in self.nodes:
                if rect is None:
                    rect = node.sceneBoundingRect()
                else:
                    rect = rect.united(node.sceneBoundingRect())
            
            if rect:
                # Add some padding
                padding = 100
                rect.adjust(-padding, -padding, padding, padding)
                
                # Calculate what scale would be needed
                view_rect = self.viewport().rect()
                scale_x = view_rect.width() / rect.width()
                scale_y = view_rect.height() / rect.height()
                target_scale = min(scale_x, scale_y)
                
                # Set reasonable zoom limits to prevent extreme zoom out
                min_scale = 0.3  # Don't zoom out more than 30%
                max_scale = 2.0  # Don't zoom in more than 200%
                
                # Clamp the scale to reasonable limits
                if target_scale < min_scale:
                    print(f"📏 Limiting zoom out: calculated {target_scale:.2f}, using {min_scale}")
                    target_scale = min_scale
                elif target_scale > max_scale:
                    print(f"📏 Limiting zoom in: calculated {target_scale:.2f}, using {max_scale}")
                    target_scale = max_scale
                
                # Reset transform and apply the limited scale
                self.setTransform(QTransform())
                self.scale(target_scale, target_scale)
                
                # Center the view on the nodes
                self.centerOn(rect.center())
                
                print(f"📏 Applied zoom level: {target_scale:.2f}x")
        else:
            # Reset to default view with reasonable zoom
            self.setTransform(QTransform())
            self.scale(1.0, 1.0)  # 100% zoom for empty canvas
            
    def add_input_node(self, filename, dataframe, file_path=None):
        """Add a data input node to the canvas."""
        node = DataInputNode(filename, dataframe, file_path)
        node.setPos(50, 80 + len(self.nodes) * 120)  # Even more spacing for text above nodes
        self.scene.addItem(node)
        self.nodes.append(node)
        
        # Set canvas reference for port connections
        node.set_canvas(self)
        
        # Connect signals
        node.connect_selected(self.on_node_selected)
        
    def add_transformation_node(self, node_type, position=None):
        """Add a transformation node to the canvas."""
        if position is None:
            position = QPointF(200, 80 + len(self.nodes) * 120)  # Even more spacing for text above nodes
            
        print(f"🏗️ Creating node type: '{node_type}'")
            
        # Create appropriate node type
        if node_type == "Column Renamer":
            node = ColumnRenamerNode()
            print(f"✅ Created ColumnRenamerNode: {node.title}")
        elif node_type == "Expression Builder":
            node = ExpressionBuilderNode()
            print(f"✅ Created ExpressionBuilderNode: {node.title}")
        elif node_type == "Constant Value Column":
            node = ConstantValueColumnNode()
            print(f"✅ Created ConstantValueColumnNode: {node.title}")
        elif node_type == "Row Filter":
            node = RowFilterNode()
            print(f"✅ Created RowFilterNode: {node.title}")
        elif node_type == "Conditional Mapping":
            node = ConditionalMappingNode(position.x(), position.y())
            print(f"✅ Created ConditionalMappingNode: {node.title}")
        elif node_type == "Domain":
            node = DomainNode()
            print(f"✅ Created DomainNode: {node.title}")
        elif node_type == "Column Keep" or node_type == "Column Drop" or node_type == "Column Keep/Drop":
            node = ColumnKeepDropNode()
            print(f"✅ Created ColumnKeepDropNode: {node.title}")
        elif node_type == "Join":
            node = JoinNode()
            print(f"✅ Created JoinNode: {node.title}")
        # TODO: Add other node types
        else:
            node = GenericTransformationNode(node_type)
            print(f"⚠️ Created GenericTransformationNode: {node.title}")
            
        node.setPos(position)
        self.scene.addItem(node)
        self.nodes.append(node)
        
        # Set canvas reference for port connections
        node.set_canvas(self)
        
        # Connect signals
        node.connect_selected(self.on_node_selected)
        
    def on_node_selected(self, node):
        """Handle node selection."""
        print(f"🎯 CANVAS: Node selected: {node.title} ({type(node).__name__})")
        
        # Clear previous selection
        for n in self.nodes:
            n.setSelected(False)
            
        # Select current node
        node.setSelected(True)
        
        # Emit the signal to property panel and other listeners
        print(f"📡 CANVAS: Emitting node_selected signal for: {node.title}")
        self.node_selected.emit(node)
        
    def zoom_in(self):
        """Zoom in the canvas."""
        self.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out the canvas."""
        self.scale(0.8, 0.8)
        
    def fit_to_window(self):
        """Fit all nodes to window."""
        if self.nodes:
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
    def mousePressEvent(self, event):
        """Handle mouse press events for connections."""
        print(f"🖱️ Canvas mouse press at {event.position().toPoint()}")
        
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            print(f"🎯 Item at click position: {type(item).__name__ if item else 'None'}")
            
            # Check if user clicked on a connection port
            if isinstance(item, ConnectionPort):
                print(f"🔌 Port clicked: {item.port_type}")
                if item.port_type == "output" and not self.connection_mode:
                    print("🔴 Starting connection from output port")
                    self.start_connection(item)
                    event.accept()  # Accept the event
                    return
                elif item.port_type == "input" and self.connection_mode:
                    print("🔵 Ending connection at input port")
                    self.end_connection(item) 
                    event.accept()  # Accept the event
                    return
                else:
                    print("❌ Wrong port type or connection state")
            
            # If in connection mode and clicked elsewhere, cancel
            if self.connection_mode:
                print("🚫 Canceling connection - clicked elsewhere")
                self.cancel_connection()
                
        super().mousePressEvent(event)
        
    def contextMenuEvent(self, event):
        """Handle right-click context menu for the canvas."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        # Only show context menu if clicking on empty canvas (not on nodes)
        item = self.itemAt(event.pos())
        if item and hasattr(item, 'parent_node'):  # Clicked on a node or its component
            super().contextMenuEvent(event)
            return
        
        menu = QMenu()
        
        # Auto Align Nodes action
        align_action = QAction("🎯 Auto Align Nodes", menu)
        align_action.setToolTip("Automatically arrange nodes in a clean grid layout")
        align_action.triggered.connect(self.auto_align_nodes)
        menu.addAction(align_action)
        
        menu.addSeparator()
        
        # Clear Canvas action
        clear_action = QAction("🗑️ Clear Canvas", menu)
        clear_action.setToolTip("Remove all nodes and connections")
        clear_action.triggered.connect(self.clear_canvas)
        menu.addAction(clear_action)
        
        # Show menu at cursor position
        menu.exec(event.globalPos())
        
    def auto_align_nodes(self):
        """Automatically align nodes in a clean grid layout."""
        if not self.nodes:
            print("ℹ️ No nodes to align")
            return
        
        print(f"🎯 Auto-aligning {len(self.nodes)} nodes...")
        
        # Configuration
        cols = 4  # Number of columns
        spacing_x = 200  # Horizontal spacing
        spacing_y = 150  # Vertical spacing
        start_x = -400  # Starting X position
        start_y = -300  # Starting Y position
        
        # Sort nodes by type for better organization
        sorted_nodes = sorted(self.nodes, key=lambda n: (
            0 if hasattr(n, 'filename') else  # Data input nodes first
            1 if hasattr(n, 'rename_mappings') else  # Rename nodes
            2 if hasattr(n, 'domain_codes') else  # Domain nodes
            3 if hasattr(n, 'filter_column') else  # Filter nodes
            4 if hasattr(n, 'expressions') else  # Expression nodes
            5  # Other nodes
        ))
        
        # Arrange nodes in grid
        for i, node in enumerate(sorted_nodes):
            row = i // cols
            col = i % cols
            
            new_x = start_x + (col * spacing_x)
            new_y = start_y + (row * spacing_y)
            
            # Animate the movement
            node.setPos(new_x, new_y)
            print(f"   📍 Moved {node.title} to ({new_x}, {new_y})")
        
        # Update connections to reflect new positions
        for connection in self.connections:
            connection.update_path()
        
        # Center view on the arranged nodes
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        print(f"✅ Auto-alignment complete! Arranged {len(sorted_nodes)} nodes in {len(sorted_nodes)//cols + 1} rows")
        
        # Emit flow changed signal
        self.flow_changed.emit()
        
    def clear_canvas(self):
        """Clear all nodes and connections from the canvas."""
        from PyQt6.QtWidgets import QMessageBox
        
        if not self.nodes and not self.connections:
            print("ℹ️ Canvas is already empty")
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            None, 
            "Clear Canvas", 
            f"Are you sure you want to remove all {len(self.nodes)} nodes and {len(self.connections)} connections?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"🗑️ Clearing canvas: {len(self.nodes)} nodes, {len(self.connections)} connections")
            
            # Remove all connections
            for connection in self.connections[:]:  # Copy list to avoid modification during iteration
                self.scene.removeItem(connection)
            self.connections.clear()
            
            # Remove all nodes
            for node in self.nodes[:]:  # Copy list to avoid modification during iteration
                self.scene.removeItem(node)
            self.nodes.clear()
            
            # Emit flow changed signal
            self.flow_changed.emit()
            
            print("✅ Canvas cleared successfully!")
        else:
            print("❌ Canvas clear cancelled by user")
        
    def mouseMoveEvent(self, event):
        """Handle mouse move for temporary connection drawing."""
        # Handle connection drawing
        if self.connection_mode and self.temp_connection:
            # Update temporary connection line
            scene_pos = self.mapToScene(event.position().toPoint())
            self.temp_connection.update_end_point(scene_pos)
            
        super().mouseMoveEvent(event)
        
    def start_connection(self, port):
        """Start creating a connection from a port."""
        print(f"🚀 FlowCanvas.start_connection called with {port.port_type} port")
        
        if port.port_type == "output":
            self.connection_mode = True
            self.connection_start_port = port
            
            # Create temporary connection line
            start_pos = port.get_scene_position()
            print(f"📍 Connection start position: {start_pos}")
            
            self.temp_connection = TempConnection(start_pos)
            self.scene.addItem(self.temp_connection)
            print(f"✅ Temporary connection created")
        else:
            print(f"❌ Cannot start connection from input port")
            
    def end_connection(self, port):
        """End creating a connection at a port."""
        print(f"🎯 FlowCanvas.end_connection called with {port.port_type} port")
        
        if (port.port_type == "input" and 
            self.connection_start_port and 
            self.connection_start_port != port and
            self.connection_start_port.port_type == "output"):
            
            print(f"✅ Creating permanent connection from {self.connection_start_port.port_type} to {port.port_type}")
            
            # Create actual connection
            connection = NodeConnection(self.connection_start_port, port)
            connection.set_canvas(self)  # Set canvas reference for deletion
            self.scene.addItem(connection)
            self.connections.append(connection)
            
            # Clear cached output data for the target node (new input data available)
            target_node = port.parent_node
            self.clear_node_outputs_downstream(target_node)
            
            print(f"🔗 Connection created successfully! Total connections: {len(self.connections)}")
            
            # Emit flow changed signal to update UI
            self.flow_changed.emit()
            
        else:
            if not self.connection_start_port:
                print(f"❌ Connection failed - No start port set. You must click an OUTPUT port first!")
            elif self.connection_start_port.port_type != "output":
                print(f"❌ Connection failed - Start port is {self.connection_start_port.port_type}, should be output")
            elif port.port_type != "input":
                print(f"❌ Connection failed - End port is {port.port_type}, should be input")
            else:
                print(f"❌ Connection failed - Unknown reason")
            
        self.cancel_connection()
        
    def start_reverse_connection(self, input_port):
        """Start a reverse connection from an input port (finds compatible outputs)."""
        print(f"🔄 Starting reverse connection from input port")
        
        # Find compatible output ports in the canvas
        compatible_outputs = []
        for node in self.nodes:
            for output_port in node.output_ports:
                if self.can_connect_ports(output_port, input_port):
                    compatible_outputs.append(output_port)
        
        if len(compatible_outputs) == 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(None, "🔍 No Compatible Outputs", 
                                  "No compatible output ports found!\n\n"
                                  "Make sure you have:\n"
                                  "• A data source node (with orange output port)\n"
                                  "• Or another transformation node with outputs\n\n"
                                  "Try loading data first using the 'Load Data' button.")
            return
        
        elif len(compatible_outputs) == 1:
            # Auto-connect to the single compatible output
            output_port = compatible_outputs[0]
            print(f"🤖 Auto-connecting to single compatible output")
            
            connection = NodeConnection(output_port, input_port)
            connection.set_canvas(self)  # Set canvas reference for deletion
            self.scene.addItem(connection)
            self.connections.append(connection)
            
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(None, "✅ Auto-Connected!", 
                                  f"Automatically connected to the available output!\n\n"
                                  f"Connection: {output_port.parent_node.get_display_name()} → {input_port.parent_node.get_display_name()}")
            
        else:
            # Multiple compatible outputs - show selection dialog
            self.show_output_selection_dialog(compatible_outputs, input_port)
    
    def can_connect_ports(self, output_port, input_port):
        """Check if two ports can be connected."""
        # Basic compatibility check
        if output_port.port_type != "output" or input_port.port_type != "input":
            return False
        
        # Don't connect to same node
        if output_port.parent_node == input_port.parent_node:
            return False
            
        # Check if already connected
        for connection in self.connections:
            if (connection.output_port == output_port and connection.input_port == input_port):
                return False
        
        return True
    
    def show_output_selection_dialog(self, compatible_outputs, input_port):
        """Show dialog to select which output to connect to."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout
        
        dialog = QDialog()
        dialog.setWindowTitle("🔗 Select Output to Connect")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Multiple compatible outputs found. Select one to connect:")
        layout.addWidget(label)
        
        list_widget = QListWidget()
        for output_port in compatible_outputs:
            item_text = f"🔴 {output_port.parent_node.get_display_name()}"
            list_widget.addItem(item_text)
        layout.addWidget(list_widget)
        
        button_layout = QHBoxLayout()
        connect_btn = QPushButton("✅ Connect")
        cancel_btn = QPushButton("❌ Cancel")
        
        button_layout.addWidget(connect_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def on_connect():
            current_row = list_widget.currentRow()
            if current_row >= 0:
                selected_output = compatible_outputs[current_row]
                connection = NodeConnection(selected_output, input_port)
                connection.set_canvas(self)  # Set canvas reference for deletion
                self.scene.addItem(connection)
                self.connections.append(connection)
                print(f"🔗 Manual connection created: {selected_output.parent_node.get_display_name()} → {input_port.parent_node.get_display_name()}")
            dialog.accept()
        
        connect_btn.clicked.connect(on_connect)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
        
    def cancel_connection(self):
        """Cancel current connection creation."""
        print(f"🚫 Canceling connection")
        
        if self.temp_connection:
            self.scene.removeItem(self.temp_connection)
            self.temp_connection = None
            
        self.connection_mode = False
        self.connection_start_port = None
        
    def delete_connection(self, connection):
        """Delete a connection from the canvas."""
        try:
            print(f"🗑️ Deleting connection: {connection.start_port.parent_node.get_display_name()} → {connection.end_port.parent_node.get_display_name()}")
            
            # Clear cached output data for the target node AND all downstream nodes
            target_node = connection.end_port.parent_node
            self.clear_node_outputs_downstream(target_node)
            
            # ALSO clear the target node itself
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'execution_engine'):
                execution_engine = self.main_window.execution_engine
                if target_node in execution_engine.node_outputs:
                    del execution_engine.node_outputs[target_node]
                    print(f"🧹 Cleared cached output for target node: {target_node.get_display_name()}")
            
            # Remove from scene
            self.scene.removeItem(connection)
            
            # Remove from connections list
            if connection in self.connections:
                self.connections.remove(connection)
                
            print(f"✅ Connection deleted successfully! Remaining connections: {len(self.connections)}")
            
            # Emit flow changed signal to trigger updates
            self.flow_changed.emit()
            
            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(None, "🗑️ Connection Deleted", 
                                  f"Connection removed successfully!\n\n"
                                  f"Deleted: {connection.start_port.parent_node.get_display_name()} → {connection.end_port.parent_node.get_display_name()}\n"
                                  f"Remaining connections: {len(self.connections)}")
                                  
        except Exception as e:
            print(f"❌ Error deleting connection: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "❌ Deletion Error", f"Failed to delete connection: {str(e)}")
            
    def clear_node_outputs_downstream(self, node):
        """Clear cached output data for this node and all downstream nodes."""
        try:
            # Get execution engine from main window
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'execution_engine'):
                execution_engine = self.main_window.execution_engine
                
                # Collect all nodes to clear (this node + downstream)
                nodes_to_clear = [node]
                downstream_nodes = self.find_downstream_nodes(node)
                nodes_to_clear.extend(downstream_nodes)
                
                # Clear outputs for all nodes
                for node_to_clear in nodes_to_clear:
                    if node_to_clear in execution_engine.node_outputs:
                        del execution_engine.node_outputs[node_to_clear]
                        print(f"🧹 Cleared cached output for node: {node_to_clear.get_display_name()}")
                
                # Also clear the property panel data viewer if it's showing a cleared node
                if hasattr(self.main_window, 'property_panel') and self.main_window.property_panel:
                    property_panel = self.main_window.property_panel
                    if hasattr(property_panel, 'current_node') and property_panel.current_node in nodes_to_clear:
                        # Clear the data viewer by showing empty data
                        if hasattr(property_panel, 'data_viewer'):
                            property_panel.data_viewer.show_data_flow(None)
                            print(f"🔄 Cleared data viewer for: {property_panel.current_node.get_display_name()}")
                
                print(f"✅ Cleared cached outputs for {len(nodes_to_clear)} nodes total")
                
        except Exception as e:
            print(f"⚠️ Error clearing node outputs: {e}")
    
    def find_downstream_nodes(self, node):
        """Find all nodes that are downstream from the given node."""
        downstream = set()
        to_check = [node]
        
        while to_check:
            current = to_check.pop()
            # Find connections where current node is the source
            for conn in self.connections:
                if conn.start_port.parent_node == current:
                    target = conn.end_port.parent_node
                    if target not in downstream:
                        downstream.add(target)
                        to_check.append(target)
        
        return list(downstream)
            
    def delete_all_connections(self):
        """Delete all connections from the canvas."""
        if not self.connections:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(None, "ℹ️ No Connections", "No connections to delete.")
            return
            
        # Ask for confirmation
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(None, "🗑️ Delete All Connections", 
                                   f"Delete all {len(self.connections)} connections?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            connections_copy = self.connections.copy()
            for connection in connections_copy:
                self.delete_connection(connection)
        
    def dragEnterEvent(self, event):
        """Handle drag enter for node creation."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """Handle drag move."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        event.accept()
            
    def dropEvent(self, event):
        """Handle drop to create new nodes."""
        if event.mimeData().hasText():
            node_type = event.mimeData().text()
            drop_pos = self.mapToScene(event.position().toPoint())
            
            # The node_type should already be clean (e.g., "Column Renamer", "Expression Builder")
            # No need to remove anything since the UserRole data is set correctly
            clean_node_type = node_type
            
            print(f"🎯 DROP EVENT: Original type: '{node_type}' → Clean type: '{clean_node_type}'")
            
            self.add_transformation_node(clean_node_type, drop_pos)
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def serialize_flow(self):
        """Serialize the current flow to JSON."""
        flow_data = {
            "nodes": [],
            "connections": []
        }
        
        for node in self.nodes:
            flow_data["nodes"].append(node.serialize())
            
        for connection in self.connections:
            flow_data["connections"].append(connection.serialize())
            
        return flow_data
    
    def keyPressEvent(self, event):
        """Handle key press events for the canvas."""
        if event.key() == Qt.Key.Key_Delete:
            # Check for selected connections first
            selected_connections = [conn for conn in self.connections if conn.isSelected()]
            if selected_connections:
                print(f"🗑️ Deleting {len(selected_connections)} selected connection(s)")
                for connection in selected_connections:
                    self.delete_connection(connection)
                event.accept()
                return
            
            # If no connections selected, check for selected nodes
            self.delete_selected_nodes()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def delete_selected_nodes(self):
        """Delete all selected nodes and their connections."""
        selected_nodes = [node for node in self.nodes if node.isSelected()]
        
        if not selected_nodes:
            print("ℹ️ No nodes selected for deletion")
            return
        
        print(f"🗑️ Deleting {len(selected_nodes)} selected node(s)")
        
        for node in selected_nodes:
            self.delete_node(node)
        
        # Emit flow changed signal
        self.flow_changed.emit()
    
    def delete_node(self, node):
        """Delete a specific node and all its connections."""
        print(f"🗑️ Deleting node: {node.title}")
        
        # Find and remove all connections involving this node
        connections_to_remove = []
        for connection in self.connections:
            if (connection.start_port.parent_node == node or 
                connection.end_port.parent_node == node):
                connections_to_remove.append(connection)
        
        print(f"🔗 Removing {len(connections_to_remove)} connection(s)")
        for connection in connections_to_remove:
            self.delete_connection(connection)
        
        # Remove node from scene and nodes list
        self.scene.removeItem(node)
        if node in self.nodes:
            self.nodes.remove(node)
        
        print(f"✅ Node {node.title} deleted successfully")
    
    def get_current_selected_node(self):
        """Get the currently selected node."""
        for node in self.nodes:
            if node.isSelected():
                return node
        return None

    # === FLOW SERIALIZATION METHODS ===
    
    def serialize_flow(self):
        """Serialize the entire flow to a dictionary."""
        flow_data = {
            "version": "1.0",
            "nodes": [],
            "connections": []
        }
        
        # Serialize nodes
        for node in self.nodes:
            node_data = {
                "id": getattr(node, 'node_id', f"node_{id(node)}"),
                "type": node.__class__.__name__,
                "title": node.title,
                "custom_name": getattr(node, 'custom_name', ''),
                "custom_description": getattr(node, 'custom_description', ''),
                "position": {
                    "x": node.pos().x(),
                    "y": node.pos().y()
                },
                "properties": self._safe_serialize(node.get_properties() if hasattr(node, 'get_properties') else {}),
                "data": self._safe_serialize(getattr(node, 'data', None))
            }
            
            # Handle special node types
            if hasattr(node, 'filename'):
                node_data['filename'] = node.filename
                # Also save the full file path if available
                if hasattr(node, 'file_path'):
                    node_data['file_path'] = node.file_path
                elif hasattr(node, 'dataframe') and node.dataframe is not None:
                    # Try to get file path from node's stored info
                    node_data['file_path'] = getattr(node, 'file_path', None)
                    
            if hasattr(node, 'dataframe') and node.dataframe is not None:
                # Store basic info about dataframe
                node_data['dataframe_info'] = {
                    'shape': node.dataframe.shape,
                    'columns': list(node.dataframe.columns)
                }
                
            flow_data["nodes"].append(node_data)
            
        # Serialize connections
        for connection in self.connections:
            if hasattr(connection, 'serialize'):
                flow_data["connections"].append(connection.serialize())
                
        return flow_data
        
    def _safe_serialize(self, obj):
        """Safely serialize an object, handling non-JSON-serializable types."""
        if obj is None:
            return None
        
        import json
        
        try:
            # Try to serialize the object
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # If it fails, convert to string representation
            if isinstance(obj, dict):
                return {k: self._safe_serialize(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [self._safe_serialize(item) for item in obj]
            else:
                return str(obj)  # Convert to string as fallback
        
    def load_flow(self, flow_data):
        """Load a flow from serialized data."""
        # Check if flow_data is valid
        if flow_data is None:
            print("❌ Error: Cannot load flow - flow_data is None")
            return False
            
        if not isinstance(flow_data, dict):
            print(f"❌ Error: Cannot load flow - flow_data must be a dictionary, got {type(flow_data)}")
            return False
        
        # Clear existing flow
        self.clear_flow()
        
        # Load nodes
        node_map = {}  # Map node IDs to actual nodes
        
        for node_data in flow_data.get("nodes", []):
            node = self.create_node_from_data(node_data)
            if node:
                node_map[node_data["id"]] = node
                self.scene.addItem(node)
                self.nodes.append(node)
                
                # Set canvas reference
                node.set_canvas(self)
                node.connect_selected(self.on_node_selected)
                
        # Load connections
        for conn_data in flow_data.get("connections", []):
            self.create_connection_from_data(conn_data, node_map)
            
        # Set a reasonable default zoom instead of auto-fitting
        # This prevents extreme zoom out for workflows with spread-out nodes
        self.set_reasonable_zoom_after_load()
        
        print(f"✅ Flow loaded: {len(self.nodes)} nodes, {len(self.connections)} connections")
        return True
    
    def set_reasonable_zoom_after_load(self):
        """Set a reasonable zoom level after loading a workflow."""
        if self.nodes:
            # Get bounding rect of all nodes
            rect = None
            for node in self.nodes:
                if rect is None:
                    rect = node.sceneBoundingRect()
                else:
                    rect = rect.united(node.sceneBoundingRect())
            
            if rect:
                # Center the view on the nodes
                self.centerOn(rect.center())
                
                # Set a reasonable default zoom (75% - good for most workflows)
                default_zoom = 0.75
                self.setTransform(QTransform())
                self.scale(default_zoom, default_zoom)
                
                print(f"📏 Set default zoom level: {default_zoom}x (centered on workflow)")
            else:
                # No valid rect, use standard zoom
                self.setTransform(QTransform())
                self.scale(1.0, 1.0)
        else:
            # Empty workflow, reset to 100% zoom
            self.setTransform(QTransform())
            self.scale(1.0, 1.0)
        
    def create_node_from_data(self, node_data):
        """Create a node from serialized data."""
        node_type = node_data.get("type", "")
        
        # Create node based on type
        if node_type == "DataInputNode":
            # For data input nodes, we need the file
            filename = node_data.get("filename", "Unknown File")
            file_path = node_data.get("file_path", None)
            
            # Try to reload the data if file path is available
            dataframe = None
            if file_path and os.path.exists(file_path):
                try:
                    print(f"🔄 Attempting to reload data from: {file_path}")
                    
                    # Determine file type and load accordingly
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    if file_ext == '.csv':
                        import pandas as pd
                        dataframe = pd.read_csv(file_path)
                        print(f"✅ Successfully reloaded CSV data: {dataframe.shape}")
                    elif file_ext in ['.sas7bdat', '.xpt']:
                        # Import here to avoid circular imports
                        from data.data_manager import DataManager
                        data_manager = DataManager()
                        dataframe = data_manager.load_sas_dataset(file_path)
                        print(f"✅ Successfully reloaded SAS data: {dataframe.shape}")
                    elif file_ext in ['.xlsx', '.xls']:
                        import pandas as pd
                        dataframe = pd.read_excel(file_path)
                        print(f"✅ Successfully reloaded Excel data: {dataframe.shape}")
                    else:
                        print(f"⚠️ Unsupported file type: {file_ext}")
                        
                except Exception as e:
                    print(f"⚠️ Failed to reload data from {file_path}: {e}")
                    dataframe = None
            else:
                if file_path:
                    print(f"⚠️ File not found: {file_path}")
                    # Store the missing file path for potential manual reloading
                    setattr(self, '_missing_file_path', file_path)
                else:
                    print(f"⚠️ No file path saved for {filename}")
            
            node = DataInputNode(filename, dataframe, file_path)
            
            # Add a method to reload data manually if automatic reload failed
            if dataframe is None and file_path:
                def reload_data_manually():
                    """Allow user to browse for the missing file."""
                    from PyQt6.QtWidgets import QFileDialog, QMessageBox
                    from PyQt6.QtWidgets import QApplication
                    
                    app = QApplication.instance()
                    if app:
                        file_path_new, _ = QFileDialog.getOpenFileName(
                            None,
                            f"Locate missing file: {os.path.basename(file_path)}",
                            os.path.dirname(file_path),
                            "Data Files (*.csv *.sas7bdat *.xpt *.xlsx *.xls);;All Files (*)"
                        )
                        
                        if file_path_new:
                            try:
                                # Try to load the new file
                                file_ext = os.path.splitext(file_path_new)[1].lower()
                                
                                if file_ext == '.csv':
                                    import pandas as pd
                                    new_dataframe = pd.read_csv(file_path_new)
                                elif file_ext in ['.sas7bdat', '.xpt']:
                                    from data.data_manager import DataManager
                                    data_manager = DataManager()
                                    new_dataframe = data_manager.load_sas_dataset(file_path_new)
                                elif file_ext in ['.xlsx', '.xls']:
                                    import pandas as pd
                                    new_dataframe = pd.read_excel(file_path_new)
                                else:
                                    raise ValueError(f"Unsupported file type: {file_ext}")
                                
                                # Update the node
                                node.dataframe = new_dataframe
                                node.file_path = file_path_new
                                
                                # Update the display
                                if hasattr(node, 'info_text'):
                                    node.info_text.setPlainText(f"{len(new_dataframe)} rows, {len(new_dataframe.columns)} cols")
                                
                                QMessageBox.information(None, "Success", f"Data reloaded successfully!\n{new_dataframe.shape[0]} rows, {new_dataframe.shape[1]} columns")
                                
                            except Exception as e:
                                QMessageBox.critical(None, "Error", f"Failed to load data:\n{str(e)}")
                
                node.reload_data_manually = reload_data_manually
        elif node_type == "ColumnRenamerNode":
            node = ColumnRenamerNode()
        elif node_type == "ColumnKeepDropNode":
            node = ColumnKeepDropNode()
        elif node_type == "ExpressionBuilderNode":
            node = ExpressionBuilderNode()
        elif node_type == "ConstantValueColumnNode":
            node = ConstantValueColumnNode()
        elif node_type == "RowFilterNode":
            node = RowFilterNode()
        elif node_type == "ConditionalMappingNode":
            node = ConditionalMappingNode()
        elif node_type == "DomainNode":
            node = DomainNode()
        elif node_type == "JoinNode":
            node = JoinNode()
        else:
            # Generic node
            node = GenericTransformationNode(node_data.get("title", "Unknown"))
            
        # Set basic properties
        if hasattr(node, 'node_id'):
            node.node_id = node_data["id"]
        else:
            setattr(node, 'node_id', node_data["id"])
            
        # Set position
        pos_data = node_data.get("position", {"x": 0, "y": 0})
        node.setPos(pos_data["x"], pos_data["y"])
        
        # Set custom name and description
        if node_data.get("custom_name"):
            node.custom_name = node_data["custom_name"]
        if node_data.get("custom_description"):
            node.custom_description = node_data["custom_description"]
            
        # Update display
        if hasattr(node, 'update_display_info'):
            node.update_display_info()
            
        # Call the node's deserialize method to restore node-specific data
        if hasattr(node, 'deserialize'):
            print(f"🔄 LOAD: Deserializing node {node_data.get('title', 'Unknown')} of type {node_type}")
            node.deserialize(node_data)
            
        # Set properties using the node's specific restoration method (fallback)
        saved_properties = node_data.get("properties", {})
        if saved_properties and hasattr(node, 'set_properties'):
            node.set_properties(saved_properties)
        elif hasattr(node, 'properties'):
            node.properties = saved_properties
            
        return node
        
    def create_connection_from_data(self, conn_data, node_map):
        """Create a connection from serialized data."""
        start_node_id = conn_data.get("start_node")
        end_node_id = conn_data.get("end_node")
        
        start_node = node_map.get(start_node_id)
        end_node = node_map.get(end_node_id)
        
        if start_node and end_node:
            # Find the appropriate ports
            start_port = None
            end_port = None
            
            for item in start_node.childItems():
                if isinstance(item, ConnectionPort) and item.port_type == "output":
                    start_port = item
                    break
                    
            for item in end_node.childItems():
                if isinstance(item, ConnectionPort) and item.port_type == "input":
                    end_port = item
                    break
                    
            if start_port and end_port:
                print(f"🔧 Creating NodeConnection with start_port={type(start_port)} end_port={type(end_port)}")
                try:
                    connection = NodeConnection(start_port, end_port)
                    self.scene.addItem(connection)
                    self.connections.append(connection)
                    print(f"✅ Connection created successfully")
                except Exception as e:
                    print(f"❌ Error creating connection: {e}")
                    print(f"🔍 Arguments: start_port={start_port}, end_port={end_port}")
                    import traceback
                    traceback.print_exc()
                    raise
                
    def clear_flow(self):
        """Clear all nodes and connections from the canvas."""
        # Remove all connections
        for connection in self.connections[:]:
            self.scene.removeItem(connection)
        self.connections.clear()
        
        # Remove all nodes
        for node in self.nodes[:]:
            self.scene.removeItem(node)
        self.nodes.clear()
        
        print("🧹 Flow cleared")
        
    def get_flow_summary(self):
        """Get a summary of the current flow."""
        return {
            "node_count": len(self.nodes),
            "connection_count": len(self.connections),
            "node_types": [node.__class__.__name__ for node in self.nodes]
        }


        
        
class RoundedProgressBar(QGraphicsRectItem):
    """Custom rounded progress bar with modern styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0  # 0-100
        self.status = "idle"  # idle, running, success, error
        
    def set_progress(self, progress, status="running"):
        """Set progress and status."""
        self.progress = max(0, min(100, progress))
        self.status = status
        self.update()  # Trigger repaint
        
    def paint(self, painter, option, widget):
        """Custom paint with rounded corners and gradient effects."""
        rect = self.rect()
        
        # Enable antialiasing for smooth curves
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background (rounded rectangle)
        bg_color = QColor(50, 50, 50)  # Dark background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.drawRoundedRect(rect, 5, 5)  # Rounded corners
        
        # Draw progress fill if there's progress
        if self.progress > 0:
            # Calculate fill width
            fill_width = (rect.width() - 2) * self.progress / 100
            fill_rect = QRectF(rect.x() + 1, rect.y() + 1, fill_width, rect.height() - 2)
            
            # Choose color based on status
            if self.status == "running":
                # Animated blue gradient
                gradient = QLinearGradient(fill_rect.left(), 0, fill_rect.right(), 0)
                gradient.setColorAt(0, QColor(30, 144, 255))  # Dodger blue
                gradient.setColorAt(1, QColor(100, 149, 237))  # Cornflower blue
                painter.setBrush(QBrush(gradient))
            elif self.status == "success":
                # Green gradient
                gradient = QLinearGradient(fill_rect.left(), 0, fill_rect.right(), 0)
                gradient.setColorAt(0, QColor(50, 205, 50))   # Lime green
                gradient.setColorAt(1, QColor(34, 139, 34))   # Forest green
                painter.setBrush(QBrush(gradient))
            elif self.status == "error":
                # Red gradient
                gradient = QLinearGradient(fill_rect.left(), 0, fill_rect.right(), 0)
                gradient.setColorAt(0, QColor(255, 69, 0))    # Red orange
                gradient.setColorAt(1, QColor(220, 20, 60))   # Crimson
                painter.setBrush(QBrush(gradient))
            
            painter.setPen(QPen(Qt.GlobalColor.transparent))
            painter.drawRoundedRect(fill_rect, 4, 4)  # Slightly smaller radius for fill


class BaseNode(QGraphicsRectItem):
    """Base class for all flow nodes."""
    
    def __init__(self, title, width=80, height=80):
        super().__init__(0, 0, width, height)
        
        self.title = title
        self.custom_name = None  # User-defined name for the node
        self.custom_description = None  # User-defined description
        self.node_id = id(self)
        self._selected_callbacks = []
        
        # Enhanced node styling with gradient and shadow effect
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(90, 150, 200))
        gradient.setColorAt(1, QColor(50, 100, 150))
        
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(120, 180, 230), 3))
        
        # Make node selectable and movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        
        # Add subtle shadow effect
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Add title text ABOVE the node (outside the node boundary)
        self.title_text = QGraphicsTextItem(title, self)
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)  # Slightly larger font for visibility
        self.title_text.setFont(font)
        self.title_text.setDefaultTextColor(QColor(0, 0, 0))  # Black text for visibility
        
        # Position title ABOVE the node (negative Y to be outside/above)
        text_rect = self.title_text.boundingRect()
        title_x = (width - text_rect.width()) / 2
        title_y = -text_rect.height() - 8  # ABOVE the node with more gap
        self.title_text.setPos(title_x, title_y)
        
        # Make sure text stays on top layer and is visible
        self.title_text.setZValue(1000)  # Very high Z value
        self.title_text.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)
        
        # Create compact text items BELOW the node 
        # Custom name text (below node, smaller)
        self.name_text = QGraphicsTextItem("", self)
        name_font = QFont("Segoe UI", 7, QFont.Weight.Bold)  # Smaller font
        self.name_text.setFont(name_font)
        self.name_text.setDefaultTextColor(QColor(255, 255, 0))  # Yellow for name
        
        # Custom description text (below name)
        self.desc_text = QGraphicsTextItem("", self)
        desc_font = QFont("Segoe UI", 7, QFont.Weight.Normal)
        self.desc_text.setFont(desc_font)
        self.desc_text.setDefaultTextColor(QColor(200, 255, 200))  # Light green for description
        
        # Progress bar (below the node) - Custom rounded progress bar
        self.progress_bar = RoundedProgressBar(self)
        progress_height = 10  # Even bigger for more visibility
        self.progress_bar.setRect(0, height + 10, width, progress_height)  # Below node with more gap
        self.progress_bar.setVisible(False)  # Hidden by default
        
        # Execution status
        self.execution_status = "idle"  # idle, running, success, error
        
        # Add node type icon/symbol (will be overridden by subclasses)
        self.add_node_icon()
        
        # Input/output ports
        self.input_ports = []
        self.output_ports = []
        self.create_ports()
        
        # Update display with initial values
        self.update_display_info()
        
    def paint(self, painter, option, widget):
        """Custom paint method with enhanced selection and shadow effects."""
        # Draw shadow first
        if not self.isSelected():
            shadow_rect = self.rect().translated(3, 3)
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.setPen(QPen(Qt.GlobalColor.transparent))
            painter.drawRoundedRect(shadow_rect, 8, 8)
        
        # Draw main node with rounded corners
        if self.isSelected():
            # Bright selection outline
            selection_pen = QPen(QColor(255, 215, 0), 4)  # Gold selection
            painter.setPen(selection_pen)
            painter.setBrush(self.brush())
            painter.drawRoundedRect(self.rect(), 8, 8)
        else:
            painter.setPen(self.pen())
            painter.setBrush(self.brush())
            painter.drawRoundedRect(self.rect(), 8, 8)
        
    def set_canvas(self, canvas):
        """Set canvas reference for port connections and node itself."""
        self.canvas = canvas  # Store canvas reference on the node
        for port in self.input_ports + self.output_ports:
            port.set_canvas(canvas)
        
    def add_node_icon(self):
        """Add a relevant icon to the center area of the node (not overlapping text)."""
        # Create icon positioned in center area, below text but above bottom
        icon_size = 32
        
        # Position icon in center area (not at very bottom to avoid port overlap)
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Slightly below center
        
        # Default icon text - will be overridden by subclasses
        icon_text = QGraphicsTextItem("⚙️", self)
        icon_text.setFont(QFont("Segoe UI", 20))
        icon_text.setDefaultTextColor(QColor(255, 255, 255, 180))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)  # Below text but above background
        
        return icon_text
        
    def connect_selected(self, callback):
        """Connect a callback for selection events."""
        self._selected_callbacks.append(callback)
        
    def _emit_selected(self):
        """Emit selection event to all connected callbacks."""
        for callback in self._selected_callbacks:
            callback(self)
        
    def create_ports(self):
        """Create input/output connection ports for compact square nodes."""
        # Input port (left side) - Adjusted for 80x80 square
        input_port = ConnectionPort(-15, 28, 24, 24, "input", self)
        input_port.setBrush(QBrush(QColor(64, 128, 255)))  # Blue for input
        input_port.setPen(QPen(QColor(255, 255, 255), 3))
        input_port.setToolTip("🔵 INPUT: Drag connections TO this port")
        input_port.setZValue(10)  # Ensure ports are above other items
        self.input_ports.append(input_port)
        
        # Output port (right side) - Adjusted for 80x80 square
        output_port = ConnectionPort(self.rect().width() - 9, 28, 24, 24, "output", self)
        output_port.setBrush(QBrush(QColor(255, 128, 64)))  # Orange for output
        output_port.setPen(QPen(QColor(255, 255, 255), 3))
        output_port.setToolTip("🔴 OUTPUT: Drag connections FROM this port")
        output_port.setZValue(10)  # Ensure ports are above other items
        self.output_ports.append(output_port)
        
    def mousePressEvent(self, event):
        """Handle mouse press - selection."""
        super().mousePressEvent(event)
        self._emit_selected()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to configure node name and description."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
        
        dialog = QDialog()
        dialog.setWindowTitle(f"Configure {self.title}")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Name input
        layout.addWidget(QLabel("Node Name:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter custom name (optional)")
        name_input.setText(self.custom_name or "")
        layout.addWidget(name_input)
        
        # Description input
        layout.addWidget(QLabel("Description:"))
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Enter description of what this node does (optional)")
        desc_input.setPlainText(self.custom_description or "")
        desc_input.setMaximumHeight(100)
        layout.addWidget(desc_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.custom_name = name_input.text().strip() or None
            self.custom_description = desc_input.toPlainText().strip() or None
            self.update_display_info()
            
    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu()
        
        # Configure action
        configure_action = QAction("Configure Node", menu)
        configure_action.triggered.connect(lambda: self.mouseDoubleClickEvent(event))
        menu.addAction(configure_action)
        
        # Reset action
        if self.custom_name or self.custom_description:
            reset_action = QAction("Reset to Default", menu)
            reset_action.triggered.connect(self.reset_info)
            menu.addAction(reset_action)
        
        menu.exec(event.screenPos())
    
    def reset_info(self):
        """Reset to default node information."""
        self.custom_name = None
        self.custom_description = None
        self.update_display_info()
    
    def update_display_info(self):
        """Update the displayed information with title ABOVE the node."""
        # Keep title ABOVE the node (outside the node boundary)
        self.title_text.setPlainText(self.title)
        text_rect = self.title_text.boundingRect()
        title_x = (self.rect().width() - text_rect.width()) / 2
        title_y = -text_rect.height() - 8  # ABOVE the node with more gap
        self.title_text.setPos(title_x, title_y)
        
        # Ensure text is visible
        self.title_text.setDefaultTextColor(QColor(0, 0, 0))  # Black text
        self.title_text.setZValue(1000)  # Very high Z value
        
        # Position custom name BELOW the node (like KNIME)
        if self.custom_name:
            self.name_text.setPlainText(self.custom_name)
            name_rect = self.name_text.boundingRect()
            name_x = (self.rect().width() - name_rect.width()) / 2
            name_y = self.rect().height() + 5  # 5px below node
            self.name_text.setPos(name_x, name_y)
        else:
            self.name_text.setPlainText("")
        
        # Position custom description BELOW the name
        if self.custom_description:
            # Truncate long descriptions
            desc = self.custom_description
            if len(desc) > 30:
                desc = desc[:27] + "..."
            self.desc_text.setPlainText(desc)
            desc_rect = self.desc_text.boundingRect()
            desc_x = (self.rect().width() - desc_rect.width()) / 2
            desc_y = self.rect().height() + 25 if self.custom_name else self.rect().height() + 5
            self.desc_text.setPos(desc_x, desc_y)
        else:
            self.desc_text.setPlainText("")
    
    def get_display_name(self):
        """Get the current display name."""
        return self.custom_name if self.custom_name else self.title
    
    def itemChange(self, change, value):
        """Handle item changes like position updates."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Update connection positions when node moves
            self.update_connections()
        return super().itemChange(change, value)
    
    def update_connections(self):
        """Update all connections connected to this node."""
        if hasattr(self, 'canvas') and self.canvas:
            for connection in self.canvas.connections:
                if (connection.start_port.parent_node == self or 
                    connection.end_port.parent_node == self):
                    connection.update_path()
        else:
            print(f"⚠️ Node {self.title} has no canvas reference")
    
    def serialize(self):
        """Serialize node data."""
        return {
            "id": self.node_id,
            "type": self.__class__.__name__,
            "title": self.title,
            "custom_name": self.custom_name,
            "custom_description": self.custom_description,
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "properties": self.get_properties()
        }
        
    def get_properties(self):
        """Get node-specific properties."""
        return {}
    
    def set_execution_status(self, status, progress=0):
        """Set the execution status and update progress bar.
        
        Args:
            status: 'idle', 'running', 'success', 'error'
            progress: 0-100 for running status
        """
        print(f"🔄 PROGRESS: {self.title} - Status: {status}, Progress: {progress}%")
        self.execution_status = status
        
        if status == "idle":
            self.progress_bar.setVisible(False)
        elif status == "running":
            self.progress_bar.setVisible(True)
            self.progress_bar.set_progress(progress, "running")
        elif status == "success":
            self.progress_bar.setVisible(True)
            self.progress_bar.set_progress(100, "success")
        elif status == "error":
            self.progress_bar.setVisible(True)
            self.progress_bar.set_progress(100, "error")
    
    def reset_execution_status(self):
        """Reset execution status to idle."""
        self.set_execution_status("idle")


class DataInputNode(BaseNode):
    """Node representing input data."""
    
    def __init__(self, filename, dataframe, file_path=None):
        super().__init__(f"📥 {filename}")
        self.filename = filename
        self.dataframe = dataframe
        self.file_path = file_path  # Store the full file path for reloading
        
        # Fancy green gradient for input nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(76, 175, 80))   # Light green
        gradient.setColorAt(1, QColor(46, 125, 50))   # Dark green
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(129, 199, 132), 3))
        
        # Add data info with better styling
        if dataframe is not None:
            info_text = f"{len(dataframe)} rows, {len(dataframe.columns)} cols"
        else:
            info_text = "Data not loaded"
            
        self.info_text = QGraphicsTextItem(info_text, self)
        self.info_text.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.info_text.setDefaultTextColor(QColor(255, 255, 255, 220))
        self.info_text.setPos(10, 50)
        
    def add_node_icon(self):
        """Add data input icon."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Center area
        
        icon_text = QGraphicsTextItem("📊", self)
        icon_text.setFont(QFont("Segoe UI", 16))
        icon_text.setDefaultTextColor(QColor(100, 255, 100, 200))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)
        return icon_text
        
    def add_node_icon(self):
        """Add a database icon for input nodes."""
        icon_size = 28
        icon_bg = QGraphicsEllipseItem(0, 0, icon_size, icon_size, self)
        
        # Database icon background
        gradient = QLinearGradient(0, 0, icon_size, icon_size)
        gradient.setColorAt(0, QColor(255, 255, 255, 240))
        gradient.setColorAt(1, QColor(200, 255, 200, 200))
        icon_bg.setBrush(QBrush(gradient))
        icon_bg.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Position in top-right
        icon_bg.setPos(self.rect().width() - icon_size - 6, 6)
        
        # Database icon
        icon_text = QGraphicsTextItem("💾", icon_bg)
        icon_text.setFont(QFont("Segoe UI", 14))
        icon_text.setPos(4, 2)
        
        return icon_bg
        
    def set_custom_property(self, property_name, prompt):
        """Set a custom property with user input."""
        from PyQt6.QtWidgets import QInputDialog
        current_value = getattr(self, property_name, "")
        text, ok = QInputDialog.getText(None, "Set Property", prompt, text=current_value)
        if ok and text:
            setattr(self, property_name, text)
            print(f"✅ {property_name} set to: {text}")
    
    def reset_info(self):
        """Reset custom name and description."""
        self.custom_name = ""
        self.custom_description = ""
        print("🔄 Node info reset")
        
    def contextMenuEvent(self, event):
        """Handle right-click context menu for DataInputNode."""
        menu = QMenu()
        
        # Standard options from BaseNode
        menu.addAction("🏷️ Set Custom Name", lambda: self.set_custom_property("custom_name", "Enter custom name"))
        menu.addAction("📝 Set Description", lambda: self.set_custom_property("custom_description", "Enter description"))
        menu.addAction("🔄 Reset Info", self.reset_info)
        menu.addSeparator()
        
        # Data-specific options
        if self.dataframe is not None:
            menu.addAction("📊 View Data", lambda: print("View data functionality"))
        else:
            # Add reload option when data is missing
            reload_action = menu.addAction("🔄 Reload Data", self.reload_data_manually)
            reload_action.setToolTip("Browse for the missing data file")
            
        menu.addSeparator()
        menu.addAction("🗑️ Delete Node", lambda: self.canvas.delete_node(self))
        
        menu.exec(event.screenPos())
        
    def get_properties(self):
        """Get input node properties."""
        if self.dataframe is not None:
            return {
                "filename": self.filename,
                "rows": len(self.dataframe),
                "columns": len(self.dataframe.columns)
            }
        else:
            return {
                "filename": self.filename,
                "rows": "No data",
                "columns": "No data"
            }


class ColumnRenamerNode(BaseNode):
    """Node for renaming columns."""
    
    def __init__(self):
        super().__init__("🏷️ Renamer")  # Shorter title for compact design
        self.rename_mappings = {}
        
        # Fancy purple gradient for renamer nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(156, 39, 176))   # Light purple
        gradient.setColorAt(1, QColor(106, 27, 154))   # Dark purple
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(186, 104, 200), 3))
        
    def add_node_icon(self):
        """Add label icon for column renamer."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Center area
        
        icon_text = QGraphicsTextItem("🏷️", self)
        icon_text.setFont(QFont("Segoe UI", 16))
        icon_text.setDefaultTextColor(QColor(200, 150, 255, 200))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)
        return icon_text
        gradient.setColorAt(0, QColor(255, 255, 255, 240))
        gradient.setColorAt(1, QColor(255, 200, 255, 200))
        icon_bg.setBrush(QBrush(gradient))
        icon_bg.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Position in top-right
        icon_bg.setPos(self.rect().width() - icon_size - 6, 6)
        
        # Label icon
        icon_text = QGraphicsTextItem("🏷️", icon_bg)
        icon_text.setFont(QFont("Segoe UI", 14))
        icon_text.setPos(3, 2)
        
        return icon_bg
        
    def get_properties(self):
        """Get column renamer properties."""
        return {"mappings": self.rename_mappings}
    
    def set_properties(self, properties):
        """Restore column renamer properties."""
        if "mappings" in properties:
            self.rename_mappings = properties["mappings"]
            print(f"✅ Restored column rename mappings: {self.rename_mappings}")

    def execute(self):
        """Execute column renaming transformation during flow execution."""
        try:
            print(f"🏷️ RENAMER EXECUTE: Starting column renaming for {self.title}")
            
            # Get input data from execution engine
            if hasattr(self, 'canvas') and hasattr(self.canvas, 'execution_engine'):
                input_data = self.canvas.execution_engine.get_node_input_data(self)
            else:
                print(f"❌ RENAMER EXECUTE: No execution engine available")
                return False
                
            if input_data is None:
                print(f"❌ RENAMER EXECUTE: No input data available")
                return False
                
            print(f"🏷️ RENAMER EXECUTE: Input data shape: {input_data.shape}")
            print(f"🏷️ RENAMER EXECUTE: Current mappings: {self.rename_mappings}")
            
            # Apply column renaming
            if self.rename_mappings:
                # Only rename columns that exist in the data
                valid_mappings = {}
                for old_name, new_name in self.rename_mappings.items():
                    if old_name in input_data.columns:
                        valid_mappings[old_name] = new_name
                    else:
                        print(f"⚠️ RENAMER WARNING: Column '{old_name}' not found in data")
                
                if valid_mappings:
                    self.output_data = input_data.rename(columns=valid_mappings)
                    
                    # Add column highlighting information for UI feedback
                    if not hasattr(self, 'transformed_columns'):
                        self.transformed_columns = []
                    
                    # Track renamed columns (new names)
                    for old_name, new_name in valid_mappings.items():
                        if new_name not in self.transformed_columns:
                            self.transformed_columns.append(new_name)
                    
                    print(f"✅ RENAMER EXECUTE: Renamed {len(valid_mappings)} columns")
                    print(f"🏷️ RENAMER EXECUTE: New columns: {list(self.output_data.columns)}")
                    print(f"🏷️ RENAMER EXECUTE: Highlighted columns: {self.transformed_columns}")
                else:
                    print(f"⚠️ RENAMER EXECUTE: No valid mappings found, passing through data unchanged")
                    self.output_data = input_data.copy()
            else:
                print(f"⚠️ RENAMER EXECUTE: No mappings defined, passing through data unchanged")
                self.output_data = input_data.copy()
                
            return True
            
        except Exception as e:
            print(f"❌ RENAMER EXECUTE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class ExpressionBuilderNode(BaseNode):
    """Node for building expressions with SAS-like functions."""
    
    def __init__(self):
        super().__init__("📝 Expression")  # Shorter title for compact design
        self.expression = ""
        self.target_column = ""  # Column to apply expression to
        self.new_column_name = ""  # Name for new column (if creating new)
        self.operation_mode = "replace"  # "replace" or "append"
        self.function_type = "strip"  # Default SAS function
        
        # Multiple expressions support
        self.expressions = []  # List of expression dictionaries
        self.is_multiple_mode = False  # Flag for mode
        
        # Fancy orange gradient for expression nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(255, 152, 0))    # Light orange
        gradient.setColorAt(1, QColor(230, 119, 0))    # Dark orange
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(255, 183, 77), 3))
        
    def add_node_icon(self):
        """Add calculator icon for expression builder."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Center area
        
        icon_text = QGraphicsTextItem("📝", self)
        icon_text.setFont(QFont("Segoe UI", 16))
        icon_text.setDefaultTextColor(QColor(255, 200, 100, 200))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)
        return icon_text
        
    def get_properties(self):
        """Get expression builder properties."""
        properties = {
            "expression": self.expression,
            "target_column": self.target_column,
            "new_column_name": self.new_column_name,
            "operation_mode": self.operation_mode,
            "function_type": self.function_type,
            "is_multiple_mode": getattr(self, 'is_multiple_mode', False),
            "expressions": getattr(self, 'expressions', [])
        }
        print(f"🔄 SAVE: Saving expression node with {len(properties.get('expressions', []))} expressions, mode: {properties.get('is_multiple_mode', False)}")
        return properties
    
    def set_properties(self, properties):
        """Restore expression builder properties."""
        if "expression" in properties:
            self.expression = properties["expression"]
        if "target_column" in properties:
            self.target_column = properties["target_column"]
        if "new_column_name" in properties:
            self.new_column_name = properties["new_column_name"]
        if "operation_mode" in properties:
            self.operation_mode = properties["operation_mode"]
        if "function_type" in properties:
            self.function_type = properties["function_type"]
        if "is_multiple_mode" in properties:
            self.is_multiple_mode = properties["is_multiple_mode"]
        if "expressions" in properties:
            self.expressions = properties["expressions"]
        
        print(f"✅ LOAD: Restored expression node with {len(getattr(self, 'expressions', []))} expressions, mode: {getattr(self, 'is_multiple_mode', False)}")
    
    def process_data(self, input_dataframe):
        """Apply expression(s) to the dataframe."""
        if input_dataframe is None or input_dataframe.empty:
            print("⚠️ Warning: No input data for expression builder node")
            return None
            
        try:
            # Create a copy of the input dataframe
            df_copy = input_dataframe.copy()
            
            # Check if we're in multiple expressions mode
            if hasattr(self, 'is_multiple_mode') and self.is_multiple_mode and hasattr(self, 'expressions') and self.expressions:
                return self.process_multiple_expressions(df_copy)
            else:
                return self.process_single_expression(df_copy)
                
        except Exception as e:
            print(f"❌ Error applying expression: {str(e)}")
            return input_dataframe
    
    def process_single_expression(self, df_copy):
        """Process a single expression (original functionality)."""
        # Determine target column
        if not self.target_column or self.target_column not in df_copy.columns:
            print(f"❌ Target column '{self.target_column}' not found in data")
            return df_copy
        
        # Determine output column name
        if self.operation_mode == "replace" or not hasattr(self, 'new_column_name') or not self.new_column_name.strip():
            output_column = self.target_column
        else:  # append
            output_column = self.new_column_name
        
        # Apply the SAS function
        result_series = self.apply_sas_function(df_copy[self.target_column])
        
        if result_series is not None:
            df_copy[output_column] = result_series
            print(f"✅ Applied {self.function_type} expression to column '{output_column}'")
        else:
            print(f"❌ Failed to apply expression")
        
        return df_copy
    
    def process_multiple_expressions(self, df_copy):
        """Process multiple expressions in batch."""
        print(f"🔄 Processing {len(self.expressions)} expressions...")
        
        for i, expr in enumerate(self.expressions):
            try:
                column = expr.get('column', '')
                function = expr.get('function', 'strip')
                parameters = expr.get('parameters', '')
                mode = expr.get('mode', 'Replace')
                new_column = expr.get('new_column', '')
                
                if not column or column not in df_copy.columns:
                    print(f"⚠️ Expression {i+1}: Column '{column}' not found, skipping")
                    continue
                
                # Determine output column
                if mode == "Replace":
                    output_column = column
                else:  # Append
                    if not new_column.strip():
                        print(f"⚠️ Expression {i+1}: No new column name for append mode, skipping")
                        continue
                    output_column = new_column
                
                # Apply function with parameters
                old_function = self.function_type
                old_expression = self.expression
                self.function_type = function
                self.expression = parameters
                
                result_series = self.apply_sas_function(df_copy[column])
                
                # Restore original values
                self.function_type = old_function
                self.expression = old_expression
                
                if result_series is not None:
                    df_copy[output_column] = result_series
                    print(f"✅ Expression {i+1}: Applied {function} to '{column}' -> '{output_column}'")
                else:
                    print(f"❌ Expression {i+1}: Failed to apply {function}")
                    
            except Exception as e:
                print(f"❌ Expression {i+1}: Error - {str(e)}")
        
        return df_copy
    
    def apply_sas_function(self, series):
        """Apply SAS-like functions to a pandas series."""
        try:
            if self.function_type == "strip":
                return series.astype(str).str.strip()
            elif self.function_type == "upper":
                return series.astype(str).str.upper()
            elif self.function_type == "lower":
                return series.astype(str).str.lower()
            elif self.function_type == "substr":
                # Extract parameters from expression (start, length)
                return self.apply_substr(series)
            elif self.function_type == "scan":
                # Extract parameters from expression (delimiter, word_number)
                return self.apply_scan(series)
            elif self.function_type == "compress":
                # Remove specified characters
                return self.apply_compress(series)
            elif self.function_type == "catx":
                # Concatenate with delimiter
                return self.apply_catx(series)
            elif self.function_type == "length":
                return series.astype(str).str.len()
            elif self.function_type == "trim":
                return series.astype(str).str.strip()
            elif self.function_type == "left":
                return series.astype(str).str.lstrip()
            elif self.function_type == "right":
                return series.astype(str).str.rstrip()
            else:
                # Custom expression
                return self.apply_custom_expression(series)
                
        except Exception as e:
            print(f"❌ Error in SAS function '{self.function_type}': {str(e)}")
            return None
    
    def apply_substr(self, series):
        """Apply SAS SUBSTR function."""
        # Parse expression for start and length parameters
        # Expected format: "start,length" or just "start"
        parts = self.expression.split(',')
        try:
            start = int(parts[0].strip()) - 1  # SAS is 1-indexed, Python is 0-indexed
            length = int(parts[1].strip()) if len(parts) > 1 else None
            
            if length:
                return series.astype(str).str[start:start+length]
            else:
                return series.astype(str).str[start:]
        except (ValueError, IndexError):
            print(f"❌ Invalid SUBSTR parameters: '{self.expression}'. Expected: start,length")
            return series
    
    def apply_scan(self, series):
        """Apply SAS SCAN function."""
        # Parse expression for delimiter and word number
        # Expected format: "delimiter,word_number"
        parts = self.expression.split(',')
        try:
            delimiter = parts[0].strip().strip('"\'') if parts[0].strip() else ' '
            word_num = int(parts[1].strip()) - 1  # SAS is 1-indexed
            
            return series.astype(str).str.split(delimiter).str[word_num]
        except (ValueError, IndexError):
            print(f"❌ Invalid SCAN parameters: '{self.expression}'. Expected: delimiter,word_number")
            return series
    
    def apply_compress(self, series):
        """Apply SAS COMPRESS function."""
        # Remove specified characters
        # Expected format: "characters_to_remove"
        chars_to_remove = self.expression.strip().strip('"\'')
        if chars_to_remove:
            return series.astype(str).str.replace(f'[{chars_to_remove}]', '', regex=True)
        else:
            # Default: remove all whitespace
            return series.astype(str).str.replace(r'\s+', '', regex=True)
    
    def apply_catx(self, series):
        """Apply SAS CATX function (concatenate with delimiter)."""
        # For single column, just return the column (CATX typically combines multiple)
        # User can specify a prefix/suffix in expression
        delimiter = self.expression.strip().strip('"\'') if self.expression.strip() else ''
        return delimiter + series.astype(str)
    
    def apply_custom_expression(self, series):
        """Apply custom expression."""
        # For advanced users who want to write custom Python expressions
        try:
            # Create a safe namespace for evaluation
            namespace = {
                'series': series,
                'pd': __import__('pandas'),
                'np': __import__('numpy'),
                'str': str,
                'len': len,
                'int': int,
                'float': float,
            }
            
            # Evaluate the expression
            return eval(self.expression, {"__builtins__": {}}, namespace)
        except Exception as e:
            print(f"❌ Error in custom expression '{self.expression}': {str(e)}")
            return series

    def execute(self):
        """Execute expression transformation during flow execution."""
        try:
            print(f"📝 EXPRESSION EXECUTE: Starting expression transformation for {self.title}")
            
            # Get input data from execution engine
            if hasattr(self, 'canvas') and hasattr(self.canvas, 'execution_engine'):
                input_data = self.canvas.execution_engine.get_node_input_data(self)
            else:
                print(f"❌ EXPRESSION EXECUTE: No execution engine available")
                return False
                
            if input_data is None:
                print(f"❌ EXPRESSION EXECUTE: No input data available")
                return False
                
            print(f"📝 EXPRESSION EXECUTE: Input data shape: {input_data.shape}")
            print(f"📝 EXPRESSION EXECUTE: Target column: '{self.target_column}', function: '{self.function_type}'")
            
            # Use the existing process_data method
            self.output_data = self.process_data(input_data)
            
            if self.output_data is not None:
                # Add column highlighting information for UI feedback
                if self.target_column:
                    if not hasattr(self, 'transformed_columns'):
                        self.transformed_columns = []
                    
                    if self.target_column not in self.transformed_columns:
                        self.transformed_columns.append(self.target_column)
                    
                    print(f"📝 EXPRESSION EXECUTE: Highlighted column: {self.target_column}")
                
                print(f"✅ EXPRESSION EXECUTE: Output data shape: {self.output_data.shape}")
                return True
            else:
                print(f"❌ EXPRESSION EXECUTE: Failed to process data")
                return False
                
        except Exception as e:
            print(f"❌ EXPRESSION EXECUTE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class ConstantValueColumnNode(BaseNode):
    """Node for adding constant value columns (like KNIME) - supports multiple columns."""
    
    def __init__(self):
        super().__init__("Constant")  # Use simple text to avoid encoding issues
        
        # Support multiple columns - list of dictionaries
        self.columns = [
            {
                'column_name': '',
                'constant_value': '',
                'data_type': 'string'
            }
        ]
        
        # Backward compatibility properties (for existing single column interface)
        self.column_name = ""
        self.constant_value = ""
        self.data_type = "string"
        
        # Fancy teal gradient for constant value nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(0, 188, 212))    # Light teal
        gradient.setColorAt(1, QColor(0, 150, 136))    # Dark teal
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(77, 208, 225), 3))
        
    def add_node_icon(self):
        """Add constant/number icon for constant value nodes."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Center area like other nodes
        
        # Create icon background circle
        icon_bg = QGraphicsEllipseItem(icon_x, icon_y, icon_size, icon_size, self)
        icon_bg.setBrush(QBrush(QColor(255, 255, 255, 180)))
        icon_bg.setPen(QPen(QColor(0, 150, 136), 2))
        
        # Add number/constant symbol
        icon_text = QGraphicsTextItem("123", self)
        icon_text.setDefaultTextColor(QColor(0, 150, 136))
        icon_font = QFont("Arial", 12, QFont.Weight.Bold)
        icon_text.setFont(icon_font)
        
        # Center the text in the circle
        text_rect = icon_text.boundingRect()
        text_x = icon_x + (icon_size - text_rect.width()) / 2
        text_y = icon_y + (icon_size - text_rect.height()) / 2
        icon_text.setPos(text_x, text_y)
        icon_text.setZValue(50)
        
    def process_data(self, input_dataframe):
        """Add multiple constant value columns to the dataframe."""
        if input_dataframe is None or input_dataframe.empty:
            print("⚠️ Warning: No input data for constant value column node")
            return None
            
        try:
            # Create a copy of the input dataframe
            df_copy = input_dataframe.copy()
            
            # Process all columns in the list
            for i, col_def in enumerate(self.columns):
                column_name = col_def.get('column_name', '').strip()
                constant_value = col_def.get('constant_value', '')
                data_type = col_def.get('data_type', 'string')
                
                if not column_name:
                    print(f"⚠️ Warning: Empty column name for column {i+1}, skipping")
                    continue
                
                # Convert value based on data type
                if data_type == "integer":
                    try:
                        value = int(constant_value) if constant_value.strip() else 0
                    except ValueError:
                        print(f"⚠️ Warning: Invalid integer value '{constant_value}' for column '{column_name}', using 0")
                        value = 0
                elif data_type == "float":
                    try:
                        value = float(constant_value) if constant_value.strip() else 0.0
                    except ValueError:
                        print(f"⚠️ Warning: Invalid float value '{constant_value}' for column '{column_name}', using 0.0")
                        value = 0.0
                elif data_type == "boolean":
                    value = constant_value.lower() in ['true', '1', 'yes', 'on'] if constant_value.strip() else False
                else:  # string (default)
                    value = constant_value if constant_value is not None else ""
                
                # Add the constant value column
                df_copy[column_name] = value
                print(f"✅ Added constant column '{column_name}' with value '{value}' (type: {data_type})")
            
            return df_copy
            
        except Exception as e:
            print(f"❌ Error adding constant value columns: {str(e)}")
            return input_dataframe
    
    def get_properties(self):
        """Get constant value column properties."""
        return {
            "column_name": self.column_name,
            "constant_value": self.constant_value,
            "data_type": self.data_type,
            "columns": self.columns  # Include the new columns list format
        }
    
    def set_properties(self, properties):
        """Restore constant value column properties."""
        # Restore backward compatibility properties
        if "column_name" in properties:
            self.column_name = properties["column_name"]
        if "constant_value" in properties:
            self.constant_value = properties["constant_value"]
        if "data_type" in properties:
            self.data_type = properties["data_type"]
            
        # Restore the columns list (new format)
        if "columns" in properties:
            self.columns = properties["columns"]
        else:
            # For backward compatibility, create columns list from old format
            self.columns = [{
                'column_name': self.column_name,
                'constant_value': self.constant_value,
                'data_type': self.data_type
            }]
            
        print(f"✅ Restored constant column: '{self.column_name}' = '{self.constant_value}' ({self.data_type})")
        print(f"✅ Restored {len(self.columns)} column(s) in columns list")

    def execute(self):
        """Execute constant column transformation during flow execution."""
        try:
            print(f"🔢 CONSTANT EXECUTE: Starting constant column addition for {self.title}")
            
            # Get input data from execution engine
            if hasattr(self, 'canvas') and hasattr(self.canvas, 'execution_engine'):
                input_data = self.canvas.execution_engine.get_node_input_data(self)
            else:
                print(f"❌ CONSTANT EXECUTE: No execution engine available")
                return False
                
            if input_data is None:
                print(f"❌ CONSTANT EXECUTE: No input data available")
                return False
                
            print(f"🔢 CONSTANT EXECUTE: Input data shape: {input_data.shape}")
            print(f"🔢 CONSTANT EXECUTE: Adding {len(self.columns)} constant column(s)")
            
            # Use the existing process_data method
            self.output_data = self.process_data(input_data)
            
            if self.output_data is not None:
                # Add column highlighting information for UI feedback
                added_columns = []
                for col_def in self.columns:
                    column_name = col_def.get('column_name', '').strip()
                    if column_name:
                        added_columns.append(column_name)
                
                if added_columns:
                    if not hasattr(self, 'transformed_columns'):
                        self.transformed_columns = []
                    
                    for col_name in added_columns:
                        if col_name not in self.transformed_columns:
                            self.transformed_columns.append(col_name)
                    
                    print(f"🔢 CONSTANT EXECUTE: Highlighted columns: {self.transformed_columns}")
                
                print(f"✅ CONSTANT EXECUTE: Output data shape: {self.output_data.shape}")
                return True
            else:
                print(f"❌ CONSTANT EXECUTE: Failed to process data")
                return False
                
        except Exception as e:
            print(f"❌ CONSTANT EXECUTE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class GenericTransformationNode(BaseNode):
    """Generic transformation node."""
    
    def __init__(self, node_type):
        super().__init__(node_type)
        self.node_type = node_type
        self.parameters = {}
        
        # Fancy blue gradient for generic transformation nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(33, 150, 243))   # Light blue
        gradient.setColorAt(1, QColor(21, 101, 192))   # Dark blue
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(100, 181, 246), 3))
        
    def add_node_icon(self):
        """Add a transformation icon for generic nodes."""
        icon_size = 28
        icon_bg = QGraphicsEllipseItem(0, 0, icon_size, icon_size, self)
        
        # Blue transformation background
        gradient = QLinearGradient(0, 0, icon_size, icon_size)
        gradient.setColorAt(0, QColor(255, 255, 255, 240))
        gradient.setColorAt(1, QColor(180, 220, 255, 200))
        icon_bg.setBrush(QBrush(gradient))
        icon_bg.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Position in top-right
        icon_bg.setPos(self.rect().width() - icon_size - 6, 6)
        
        # Transformation icon (arrows or gears)
        icon_text = QGraphicsTextItem("🔄", icon_bg)
        icon_text.setFont(QFont("Segoe UI", 14))
        icon_text.setPos(3, 2)
        
        return icon_bg
        
    def get_properties(self):
        """Get generic node properties."""
        return {"parameters": self.parameters}
    
    def set_properties(self, properties):
        """Restore generic node properties."""
        if "parameters" in properties:
            self.parameters = properties["parameters"]
            print(f"✅ Restored node parameters: {self.parameters}")


class RowFilterNode(BaseNode):
    """Node for filtering data rows based on conditions."""
    
    def __init__(self):
        super().__init__("🔍 Row Filter")  # Shorter title for compact design
        self.filter_column = ""
        self.filter_operator = "equals"
        self.filter_value = ""
        self.case_sensitive = False
        self.output_mode = "matching"  # "matching" or "non-matching"
        self.conditions = []  # List of conditions for multiple filters
        self.logic_operator = "AND"  # "AND" or "OR" for combining conditions
        self.use_multiple_conditions = False  # Toggle for multiple conditions UI
        
        # Fancy green gradient for filter nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(76, 175, 80))    # Light green
        gradient.setColorAt(1, QColor(56, 142, 60))    # Dark green
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(129, 199, 132), 3))
        
    def add_node_icon(self):
        """Add filter icon for row filter."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Center area
        
        icon_text = QGraphicsTextItem("🔍", self)
        icon_text.setFont(QFont("Segoe UI", 16))
        icon_text.setDefaultTextColor(QColor(100, 255, 150, 200))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)
        return icon_text
        """Add a filter icon for row filter node."""
        icon_size = 28
        icon_bg = QGraphicsEllipseItem(0, 0, icon_size, icon_size, self)
        
        # Green filter background
        gradient = QLinearGradient(0, 0, icon_size, icon_size)
        gradient.setColorAt(0, QColor(255, 255, 255, 240))
        gradient.setColorAt(1, QColor(200, 255, 200, 200))
        icon_bg.setBrush(QBrush(gradient))
        icon_bg.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Position in top-right
        icon_bg.setPos(self.rect().width() - icon_size - 6, 6)
        
        # Filter icon
        icon_text = QGraphicsTextItem("🔍", icon_bg)
        icon_text.setFont(QFont("Segoe UI", 14))
        icon_text.setPos(3, 2)
        
        return icon_bg
        
    def get_properties(self):
        """Get row filter properties."""
        return {
            "filter_column": self.filter_column,
            "filter_operator": self.filter_operator,
            "filter_value": self.filter_value,
            "case_sensitive": self.case_sensitive,
            "output_mode": self.output_mode,
            "conditions": self.conditions,
            "logic_operator": self.logic_operator,
            "use_multiple_conditions": self.use_multiple_conditions
        }
    
    def set_properties(self, properties):
        """Restore row filter properties."""
        if "filter_column" in properties:
            self.filter_column = properties["filter_column"]
        if "filter_operator" in properties:
            self.filter_operator = properties["filter_operator"]
        if "filter_value" in properties:
            self.filter_value = properties["filter_value"]
        if "case_sensitive" in properties:
            self.case_sensitive = properties["case_sensitive"]
        if "output_mode" in properties:
            self.output_mode = properties["output_mode"]
        if "conditions" in properties:
            self.conditions = properties["conditions"]
        if "logic_operator" in properties:
            self.logic_operator = properties["logic_operator"]
        if "use_multiple_conditions" in properties:
            self.use_multiple_conditions = properties["use_multiple_conditions"]
        print(f"✅ Restored row filter: column='{self.filter_column}', operator='{self.filter_operator}', value='{self.filter_value}', case_sensitive={self.case_sensitive}, output_mode='{self.output_mode}', conditions={len(self.conditions)}, logic='{self.logic_operator}', multiple_enabled={self.use_multiple_conditions}")

    def execute(self):
        """Execute row filtering transformation during flow execution."""
        try:
            print(f"🔍 FILTER EXECUTE: Starting row filtering for {self.title}")
            
            # Get input data from execution engine
            if hasattr(self, 'canvas') and hasattr(self.canvas, 'execution_engine'):
                input_data = self.canvas.execution_engine.get_node_input_data(self)
            else:
                print(f"❌ FILTER EXECUTE: No execution engine available")
                return False
                
            if input_data is None:
                print(f"❌ FILTER EXECUTE: No input data available")
                return False
                
            print(f"🔍 FILTER EXECUTE: Input data shape: {input_data.shape}")
            print(f"🔍 FILTER EXECUTE: Filter column: '{self.filter_column}', operator: '{self.filter_operator}', value: '{self.filter_value}'")
            
            # Apply row filtering
            if self.filter_column and self.filter_column in input_data.columns:
                column_data = input_data[self.filter_column]
                
                # Apply filter based on operator
                if self.filter_operator == "equals":
                    if self.case_sensitive:
                        mask = column_data == self.filter_value
                    else:
                        mask = column_data.astype(str).str.lower() == str(self.filter_value).lower()
                elif self.filter_operator == "contains":
                    if self.case_sensitive:
                        mask = column_data.astype(str).str.contains(self.filter_value, na=False)
                    else:
                        mask = column_data.astype(str).str.lower().str.contains(str(self.filter_value).lower(), na=False)
                elif self.filter_operator == "greater_than":
                    try:
                        mask = pd.to_numeric(column_data, errors='coerce') > float(self.filter_value)
                    except:
                        mask = column_data > self.filter_value
                elif self.filter_operator == "less_than":
                    try:
                        mask = pd.to_numeric(column_data, errors='coerce') < float(self.filter_value)
                    except:
                        mask = column_data < self.filter_value
                elif self.filter_operator == "not_equals":
                    if self.case_sensitive:
                        mask = column_data != self.filter_value
                    else:
                        mask = column_data.astype(str).str.lower() != str(self.filter_value).lower()
                elif self.filter_operator == "starts_with":
                    if self.case_sensitive:
                        mask = column_data.astype(str).str.startswith(self.filter_value, na=False)
                    else:
                        mask = column_data.astype(str).str.lower().str.startswith(str(self.filter_value).lower(), na=False)
                elif self.filter_operator == "ends_with":
                    if self.case_sensitive:
                        mask = column_data.astype(str).str.endswith(self.filter_value, na=False)
                    else:
                        mask = column_data.astype(str).str.lower().str.endswith(str(self.filter_value).lower(), na=False)
                else:
                    print(f"⚠️ FILTER WARNING: Unknown operator '{self.filter_operator}', no filtering applied")
                    mask = pd.Series([True] * len(input_data), index=input_data.index)
                
                # Apply output mode
                if self.output_mode == "non-matching":
                    mask = ~mask
                    
                self.output_data = input_data[mask].copy()
                print(f"✅ FILTER EXECUTE: Filtered from {len(input_data)} to {len(self.output_data)} rows")
            else:
                print(f"⚠️ FILTER EXECUTE: No valid filter column, passing through data unchanged")
                self.output_data = input_data.copy()
                
            return True
            
        except Exception as e:
            print(f"❌ FILTER EXECUTE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class ConditionalMappingNode(BaseNode):
    """Node for conditional value mapping with user-friendly table interface."""
    
    def __init__(self, x=0, y=0):
        super().__init__("�️ Conditional Mapping", 180, 80)  # Call BaseNode with title, width, height
        
        # Set position
        self.setPos(x, y)
        
        # Mapping properties
        self.source_column = ""
        self.target_column = ""
        self.mappings = []  # List of {"condition": "value", "result": "mapped_value"}
        self.default_value = ""
        self.operation_mode = "append"  # "replace", "append", or "codelist"
        self.ct_selection = None  # Selected controlled terminology codelist name
        
        # Enhanced styling for conditional mapping
        gradient = QLinearGradient(0, 0, 0, self.rect().height())
        gradient.setColorAt(0, QColor(186, 104, 200, 220))  # Light purple
        gradient.setColorAt(1, QColor(156, 39, 176, 255))   # Darker purple
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(186, 104, 200), 3))
        
    def add_node_icon(self):
        """Add mapping icon for conditional mapping."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5  # Center area
        
        icon_text = QGraphicsTextItem("🔀", self)
        icon_text.setFont(QFont("Segoe UI", 16))
        icon_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)
        return icon_text
    
    def get_properties(self):
        """Get conditional mapping properties with enhanced multi-configuration support."""
        properties = {
            "source_column": self.source_column,
            "target_column": self.target_column,
            "mappings": self.mappings,
            "default_value": self.default_value,
            "operation_mode": self.operation_mode,
            "ct_selection": self.ct_selection
        }
        
        # Include the new mapping_configs structure if it exists
        if hasattr(self, 'mapping_configs') and self.mapping_configs:
            properties["mapping_configs"] = self.mapping_configs
        
        return properties
    
    def set_properties(self, properties):
        """Restore conditional mapping properties with enhanced multi-configuration support."""
        if "source_column" in properties:
            self.source_column = properties["source_column"]
        if "target_column" in properties:
            self.target_column = properties["target_column"]
        if "mappings" in properties:
            self.mappings = properties["mappings"]
        if "default_value" in properties:
            self.default_value = properties["default_value"]
        if "operation_mode" in properties:
            self.operation_mode = properties["operation_mode"]
        if "ct_selection" in properties:
            self.ct_selection = properties["ct_selection"]
        
        # Restore the new mapping_configs structure if it exists
        if "mapping_configs" in properties:
            self.mapping_configs = properties["mapping_configs"]
            print(f"🔄 RESTORED mapping_configs: {len(self.mapping_configs)} configurations with CT selections")
            
            # Debug log the CT selections that were restored
            for i, config in enumerate(self.mapping_configs):
                ct_selection = config.get('ct_selection')
                if ct_selection:
                    print(f"   Config {i+1}: CT selection = '{ct_selection}'")
        else:
            # Initialize mapping_configs if not present (for backward compatibility)
            if not hasattr(self, 'mapping_configs'):
                self.mapping_configs = []
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu for ConditionalMappingNode."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu()
        
        # Configure action
        configure_action = QAction("⚙️ Configure Mapping", menu)
        configure_action.triggered.connect(lambda: self.mouseDoubleClickEvent(event))
        menu.addAction(configure_action)
        
        menu.addSeparator()
        
        # Execute actions
        execute_flow_action = QAction("▶️ Execute Flow", menu)
        execute_flow_action.triggered.connect(self.execute_flow)
        menu.addAction(execute_flow_action)
        
        execute_node_action = QAction("🚀 Execute This Node", menu)
        execute_node_action.triggered.connect(self.execute_single_node)
        menu.addAction(execute_node_action)
        
        menu.addSeparator()
        
        # Reset action
        if self.custom_name or self.custom_description:
            reset_action = QAction("🔄 Reset to Default", menu)
            reset_action.triggered.connect(self.reset_info)
            menu.addAction(reset_action)
        
        menu.exec(event.screenPos())
    
    def execute_flow(self):
        """Execute the entire flow."""
        if hasattr(self.canvas, 'execute_flow'):
            self.canvas.execute_flow()
        elif hasattr(self.canvas, 'parent') and hasattr(self.canvas.parent(), 'execute_flow'):
            self.canvas.parent().execute_flow()
        else:
            print("🚀 Flow execution not available from node context")
    
    def execute_single_node(self):
        """Execute just this node and its dependencies."""
        if hasattr(self.canvas, 'execute_single_node'):
            self.canvas.execute_single_node(self)
        else:
            print("🚀 Single node execution not available - executing full flow instead")
            self.execute_flow()
        print(f"✅ Restored conditional mapping: source='{self.source_column}', target='{self.target_column}', mappings={len(self.mappings)}, default='{self.default_value}', mode='{self.operation_mode}'")

    def execute(self):
        """Execute conditional mapping transformation during flow execution."""
        try:
            print(f"🗺️ MAPPING EXECUTE: Starting conditional mapping for {self.title}")
            
            # Get input data from execution engine
            if hasattr(self, 'canvas') and hasattr(self.canvas, 'execution_engine'):
                input_data = self.canvas.execution_engine.get_node_input_data(self)
            else:
                print(f"❌ MAPPING EXECUTE: No execution engine available")
                return False
                
            if input_data is None:
                print(f"❌ MAPPING EXECUTE: No input data available")
                return False
                
            print(f"🗺️ MAPPING EXECUTE: Input data shape: {input_data.shape}")
            print(f"🗺️ MAPPING EXECUTE: Source column: '{self.source_column}', Target: '{self.target_column}'")
            print(f"🗺️ MAPPING EXECUTE: Operation mode: '{self.operation_mode}'")
            print(f"🗺️ MAPPING EXECUTE: {len(self.mappings)} mappings, default: '{self.default_value}'")
            
            # Validate source column
            if not self.source_column or self.source_column not in input_data.columns:
                print(f"❌ MAPPING EXECUTE: Source column '{self.source_column}' not found in data")
                print(f"🗺️ MAPPING EXECUTE: Available columns: {list(input_data.columns)}")
                self.output_data = input_data.copy()
                return True
                
            # Create output dataframe copy
            self.output_data = input_data.copy()
            
            # Determine target column name based on operation mode
            # Handle both old and new operation mode values
            if self.operation_mode in ["append", "add_column"]:  # Create new column
                if not self.target_column:
                    print(f"❌ MAPPING EXECUTE: No target column specified for 'append/add_column' mode")
                    return False
                target_col = self.target_column
                print(f"🗺️ MAPPING EXECUTE: Creating new column '{target_col}'")
            elif self.operation_mode in ["replace", "replace_column"]:  # Replace existing column
                target_col = self.source_column
                print(f"🗺️ MAPPING EXECUTE: Replacing values in existing column '{target_col}'")
            elif self.operation_mode == "codelist":  # SDTM Codelist mapping
                if not self.target_column:
                    target_col = self.source_column + "_MAPPED"
                else:
                    target_col = self.target_column
                print(f"🗺️ MAPPING EXECUTE: SDTM codelist mapping to column '{target_col}'")
            else:
                # Fallback to old logic for backward compatibility
                if self.operation_mode == "Create New Column" and self.target_column:
                    target_col = self.target_column
                elif self.operation_mode == "Replace Values":
                    target_col = self.source_column
                else:
                    print(f"⚠️ MAPPING EXECUTE: Unknown operation mode '{self.operation_mode}', using source column")
                    target_col = self.source_column
            
            # Check if we have mappings
            if not self.mappings:
                print(f"⚠️ MAPPING EXECUTE: No mappings defined")
                if self.operation_mode == "append":
                    # For new column, just copy source column
                    self.output_data[target_col] = self.output_data[self.source_column]
                return True
            
            # Get source column data
            source_data = self.output_data[self.source_column].astype(str)
            
            # Initialize target column with source values (for unmapped items)
            if self.operation_mode in ["append", "add_column"]:
                # For new column, start with default value or empty
                if self.default_value:
                    mapped_values = pd.Series([self.default_value] * len(source_data), index=source_data.index)
                else:
                    mapped_values = source_data.copy()  # Copy original values as fallback
            else:
                # For replace mode, start with original values
                mapped_values = source_data.copy()
            
            # Apply each mapping condition
            mapping_count = 0
            for mapping in self.mappings:
                condition = str(mapping.get('condition', '')).strip()
                result = str(mapping.get('result', '')).strip()
                
                if condition and result:
                    # Find rows that match the condition
                    mask = source_data == condition
                    matched_count = mask.sum()
                    
                    if matched_count > 0:
                        mapped_values[mask] = result
                        mapping_count += matched_count
                        print(f"🗺️ MAPPING: '{condition}' -> '{result}' (matched {matched_count} rows)")
                    else:
                        print(f"🗺️ MAPPING: '{condition}' -> '{result}' (no matches)")
            
            # Apply default value for unmapped items (only if specified and in append mode)
            if self.default_value and self.operation_mode in ["append", "add_column"]:
                # Find rows that still have their original values (unmapped)
                mapped_conditions = [str(m.get('condition', '')) for m in self.mappings if m.get('condition')]
                if mapped_conditions:
                    unmapped_mask = ~source_data.isin(mapped_conditions)
                    unmapped_count = unmapped_mask.sum()
                    if unmapped_count > 0:
                        mapped_values[unmapped_mask] = self.default_value
                        print(f"🗺️ MAPPING: Applied default '{self.default_value}' to {unmapped_count} unmapped rows")
            
            # Set the target column
            self.output_data[target_col] = mapped_values
            
            # Add column highlighting information for UI feedback
            if not hasattr(self, 'transformed_columns'):
                self.transformed_columns = []
            
            if target_col not in self.transformed_columns:
                self.transformed_columns.append(target_col)
            
            print(f"✅ MAPPING EXECUTE: Successfully applied mappings to column '{target_col}'")
            print(f"🗺️ MAPPING EXECUTE: Applied {mapping_count} mappings total")
            print(f"🗺️ MAPPING EXECUTE: Output data shape: {self.output_data.shape}")
            print(f"🗺️ MAPPING EXECUTE: New columns: {list(self.output_data.columns)}")
            
            return True
            
        except Exception as e:
            print(f"❌ MAPPING EXECUTE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            print(f"✅ MAPPING EXECUTE: Successfully applied mappings to column '{target_col}'")
            
            return True
            
        except Exception as e:
            print(f"❌ MAPPING EXECUTE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class ConnectionPort(QGraphicsPathItem):
    """Enhanced connection port with fancy plug/connector shapes."""
    
    def __init__(self, x, y, width, height, port_type, parent):
        super().__init__(parent)
        self.port_type = port_type  # "input" or "output"
        self.parent_node = parent
        
        # Create simple + and - symbols for connection ports
        path = QPainterPath()
        
        if port_type == "input":
            # Create a + symbol for input ports
            center_x, center_y = x + width/2, y + height/2
            line_thickness = 3
            line_length = min(width, height) * 0.6
            
            # Horizontal line of +
            path.addRect(center_x - line_length/2, center_y - line_thickness/2, 
                        line_length, line_thickness)
            # Vertical line of +
            path.addRect(center_x - line_thickness/2, center_y - line_length/2, 
                        line_thickness, line_length)
            
            # Background circle
            circle_path = QPainterPath()
            circle_path.addEllipse(x, y, width, height)
            path = circle_path.united(path)
            
            # Green color for input ports (+)
            self.gradient = QRadialGradient(x + width/2, y + height/2, width/2)
            self.gradient.setColorAt(0, QColor(100, 255, 100, 255))  # Bright center
            self.gradient.setColorAt(1, QColor(50, 200, 50, 255))    # Darker edge
            self.hover_brush = QBrush(QColor(120, 255, 120))
        else:  # output
            # Create a - symbol for output ports
            center_x, center_y = x + width/2, y + height/2
            line_thickness = 3
            line_length = min(width, height) * 0.6
            
            # Horizontal line of -
            path.addRect(center_x - line_length/2, center_y - line_thickness/2, 
                        line_length, line_thickness)
            
            # Background circle
            circle_path = QPainterPath()
            circle_path.addEllipse(x, y, width, height)
            path = circle_path.united(path)
            
            # Red color for output ports (-)
            self.gradient = QRadialGradient(x + width/2, y + height/2, width/2)
            self.gradient.setColorAt(0, QColor(255, 100, 100, 255))  # Bright center
            self.gradient.setColorAt(1, QColor(200, 50, 50, 255))    # Darker edge
            self.hover_brush = QBrush(QColor(255, 120, 120))
            
        self.setPath(path)
        self.setBrush(QBrush(self.gradient))
        self.setPen(QPen(QColor(255, 255, 255), 2))
        self.normal_brush = self.brush()
        
        # Make port interactive
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # Store reference to canvas for connection handling
        self.canvas = None
        
    def hoverEnterEvent(self, event):
        """Enhanced hover effect."""
        self.setBrush(self.hover_brush)
        self.setPen(QPen(QColor(255, 255, 255), 3))
        port_name = "Input Port (+)" if self.port_type == "input" else "Output Port (-)"
        connector_symbol = "+" if self.port_type == "input" else "-"
        self.setToolTip(f"{connector_symbol} {port_name}\nClick and drag to create connections")
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Restore normal appearance."""
        self.setBrush(self.normal_brush)
        self.setPen(QPen(QColor(255, 255, 255), 2))
        super().hoverLeaveEvent(event)
        
    def set_canvas(self, canvas):
        """Set reference to the canvas for connection handling."""
        self.canvas = canvas
        
    def get_scene_position(self):
        """Get the center position of the port in scene coordinates."""
        rect = self.boundingRect()
        center = QPointF(rect.x() + rect.width()/2, rect.y() + rect.height()/2)
        return self.mapToScene(center)
        
    def mousePressEvent(self, event):
        """Handle mouse press for starting connections."""
        print(f"🖱️ Port ({self.port_type}) mouse press event")
        
        if event.button() == Qt.MouseButton.LeftButton and self.canvas:
            if self.port_type == "output":
                print(f"🔴 Port starting connection from output")
                self.canvas.start_connection(self)
                event.accept()  # Don't propagate to canvas
            elif self.port_type == "input":
                print(f"🔵 Port clicked (input)")
                if not self.canvas.connection_start_port:
                    print(f"💡 Input port clicked first - offering to start backwards connection")
                    # Allow starting connection from input port (backwards)
                    self.canvas.start_reverse_connection(self)
                else:
                    print(f"🔵 Completing connection at input port")
                    self.canvas.end_connection(self)
                event.accept()  # Don't propagate to canvas
            else:
                event.ignore()  # Let canvas handle it
        elif event.button() == Qt.MouseButton.RightButton:
            # Right-click for context menu
            self.show_port_menu(event)
            event.accept()
        else:
            print(f"❌ Port click failed - Button: {event.button()}, Canvas: {self.canvas is not None}")
            event.ignore()  # Let canvas handle it
        
    def show_port_menu(self, event):
        """Show context menu for port operations."""
        if not self.canvas:
            return
            
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        
        if self.port_type == "output":
            menu.addAction("🔴 Start Connection From Here", lambda: self.canvas.start_connection(self))
            menu.addAction("📋 List Available Targets", self.show_available_targets)
        else:
            if self.canvas.connection_start_port:
                menu.addAction("🔵 Complete Connection Here", lambda: self.canvas.end_connection(self))
            menu.addAction("📋 Show Connection Info", self.show_connection_info)
            
        # Fix PyQt6 compatibility - use globalPos() instead of screenPos()
        global_pos = event.globalPos() if hasattr(event, 'globalPos') else event.globalPosition().toPoint()
        menu.exec(global_pos)
        
    def show_available_targets(self):
        """Show available connection targets."""
        if not self.canvas:
            return
            
        from PyQt6.QtWidgets import QMessageBox
        
        targets = []
        for node in self.canvas.nodes:
            if node != self.parent_node and hasattr(node, 'input_ports'):
                for port in node.input_ports:
                    targets.append(f"🔵 {node.title} - Input Port")
                    
        target_list = "\n".join(targets) if targets else "No available targets"
        
        QMessageBox.information(None, "Available Connection Targets", 
                              f"🎯 Available input ports:\n\n{target_list}")
        
    def show_connection_info(self):
        """Show connection information."""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = f"""
🔵 INPUT PORT INFO

Node: {self.parent_node.title}
Port Type: {self.port_type}
Position: {self.get_scene_position()}

🔗 Connection Status:
{"✅ Connected" if any(conn.end_port == self for conn in self.canvas.connections) else "❌ Not Connected"}

💡 To connect:
1. Click orange port on source node
2. Drag to this blue port
3. Or right-click for menu options
        """
        
        QMessageBox.information(None, "Port Information", msg)
        
    def hoverEnterEvent(self, event):
        """Highlight port on hover."""
        if self.port_type == "input":
            self.setBrush(QBrush(QColor(84, 148, 255)))  # Lighter blue
        else:
            self.setBrush(QBrush(QColor(255, 148, 84)))  # Lighter orange
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Remove highlight when not hovering."""
        if self.port_type == "input":
            self.setBrush(QBrush(QColor(64, 128, 255)))  # Original blue
        else:
            self.setBrush(QBrush(QColor(255, 128, 64)))  # Original orange
        super().hoverLeaveEvent(event)


class TempConnection(QGraphicsPathItem):
    """Temporary connection line while dragging."""
    
    def __init__(self, start_pos):
        super().__init__()
        self.start_pos = start_pos
        self.end_pos = start_pos
        
        # Make transparent to mouse events so clicks pass through to ports underneath
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        # Styling
        pen = QPen(QColor(255, 255, 255, 128), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)
        
        self.update_path()
        
    def update_end_point(self, end_pos):
        """Update the end point of the temporary connection."""
        self.end_pos = end_pos
        self.update_path()
        
    def update_path(self):
        """Update the connection path."""
        path = QPainterPath()
        path.moveTo(self.start_pos)
        
        # Create curved connection
        control_offset = abs(self.end_pos.x() - self.start_pos.x()) * 0.5
        control1 = QPointF(self.start_pos.x() + control_offset, self.start_pos.y())
        control2 = QPointF(self.end_pos.x() - control_offset, self.end_pos.y())
        
        path.cubicTo(control1, control2, self.end_pos)
        self.setPath(path)


class DomainNode(BaseNode):
    """Node for adding SDTM Domain column with selected value."""
    
    def __init__(self):
        super().__init__("🏷️ Domain")
        
        # Store selected domain value
        self.selected_domain = ""
        
        # SDTM Domain codes list
        self.domain_codes = [
            "TA", "TD", "TE", "TI", "TM", "TS", "TV",  # Trial Design
            "DM", "SV", "SE", "CO", "SM",              # Special Purpose
            "AG", "CM", "EC", "EX", "ML", "PR", "SU",  # Interventions
            "AE", "APMH", "CE", "DS",                  # Events
            "DV", "HO", "MH", "CV", "DA", "DD",        # Findings
            "EG", "FT", "IE", "IS", "LB", "LC",        # Findings (continued)
            "MB", "MI", "MK", "MO", "MS", "NV",        # Findings (continued)
            "OE", "PC", "PE", "PP", "QS", "RE",        # Findings (continued)
            "RP", "RS", "SC", "SS", "TR", "TU",        # Findings (continued)
            "UR", "VS", "FA", "SR", "OI"               # Findings (continued)
        ]
        
    def get_input_data(self):
        """Get input data from connected nodes using execution engine."""
        if not hasattr(self, 'canvas') or not self.canvas:
            print("🏷️ DOMAIN: No canvas available")
            return None
            
        print(f"🏷️ DOMAIN: Looking for input data, checking {len(self.canvas.connections)} connections")
        
        # Check if execution engine is available
        if hasattr(self.canvas, 'execution_engine') and self.canvas.execution_engine:
            execution_engine = self.canvas.execution_engine
            
            # Access the cache directly (not via get_node_outputs method)
            if hasattr(execution_engine, 'node_outputs'):
                cache = execution_engine.node_outputs
                print(f"🏷️ DOMAIN: Found {len(cache)} cached outputs in execution engine")
                
                # Debug: show cache keys with their string representations
                cache_info = []
                for key in cache.keys():
                    if hasattr(key, 'title'):
                        cache_info.append(f"{key.title}")
                    else:
                        cache_info.append(f"{key}")
                print(f"🏷️ DOMAIN: Cache keys: {cache_info}")
                
                # Find input connections to this node
                for i, connection in enumerate(self.canvas.connections):
                    if connection.end_port.parent_node == self:  # This node is the end/input of the connection
                        input_node = connection.start_port.parent_node  # The start/output node
                        print(f"🏷️ DOMAIN: Found input connection from {input_node.title}")
                        
                        # Method 1: Try to find by the actual node object (most direct)
                        if input_node in cache:
                            cached_data = cache[input_node]
                            print(f"🏷️ DOMAIN: SUCCESS - Found cached data by node object: {cached_data.shape if hasattr(cached_data, 'shape') else type(cached_data)}")
                            return cached_data
                        
                        # Method 2: Try to find by title match
                        for cache_key, cache_value in cache.items():
                            if hasattr(cache_key, 'title') and cache_key.title == input_node.title:
                                print(f"🏷️ DOMAIN: SUCCESS - Found cached data by title match '{input_node.title}': {cache_value.shape if hasattr(cache_value, 'shape') else type(cache_value)}")
                                return cache_value
                        
                        # Method 3: Try by node_id as fallback
                        if hasattr(input_node, 'node_id'):
                            for cache_key, cache_value in cache.items():
                                if hasattr(cache_key, 'node_id') and cache_key.node_id == input_node.node_id:
                                    print(f"🏷️ DOMAIN: SUCCESS - Found cached data by node_id match '{input_node.node_id}': {cache_value.shape if hasattr(cache_value, 'shape') else type(cache_value)}")
                                    return cache_value
                        
                        # Method 4: Direct output_data access as last resort
                        if hasattr(input_node, 'output_data') and input_node.output_data is not None:
                            print(f"🏷️ DOMAIN: SUCCESS - Using direct output_data: {input_node.output_data.shape if hasattr(input_node.output_data, 'shape') else type(input_node.output_data)}")
                            return input_node.output_data
                            
        print(f"🏷️ DOMAIN: FAILED - No input data found")
        return None
        
    def execute(self):
        """Execute the domain assignment."""
        print(f"🏷️ DOMAIN EXECUTE: Starting execution for node {self.title}")
        print(f"🏷️ DOMAIN EXECUTE: Current selected_domain = '{getattr(self, 'selected_domain', 'MISSING_ATTRIBUTE')}'")
        
        if not hasattr(self, 'selected_domain'):
            print(f"❌ DOMAIN ERROR: Node missing selected_domain attribute")
            self.set_execution_status("error", 0)
            return False
            
        if not self.selected_domain:
            print(f"❌ DOMAIN: No domain selected (selected_domain='{self.selected_domain}')")
            self.set_execution_status("error", 0)
            return False
            
        try:
            # Set running status
            self.set_execution_status("running", 30)
            
            # Get input data
            input_data = self.get_input_data()
            if input_data is None or input_data.empty:
                print(f"❌ DOMAIN: No input data available")
                self.set_execution_status("error", 0)
                return False
            
            self.set_execution_status("running", 70)
                
            # Create a copy of the input data
            output_data = input_data.copy()
            
            # Add or update the DOMAIN column
            output_data['DOMAIN'] = self.selected_domain
            
            # Store the output data
            self.output_data = output_data
            
            # Also store in execution engine cache if available
            if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'execution_engine'):
                cache = self.canvas.execution_engine.node_outputs
                cache[self] = output_data
                print(f"🏷️ DOMAIN: Stored in execution engine cache")
            
            print(f"🏷️ DOMAIN: Added DOMAIN column with value '{self.selected_domain}' to {len(output_data)} rows")
            
            # Set success status
            self.set_execution_status("success", 0)
            return True
            
        except Exception as e:
            print(f"❌ DOMAIN ERROR: {str(e)}")
            self.set_execution_status("error", 0)
            return False
            
    def get_output_data(self):
        """Get the output data with domain column added."""
        return getattr(self, 'output_data', None)
    
    def has_output_data(self):
        """Check if node has output data available."""
        return hasattr(self, 'output_data') and self.output_data is not None
        
    def serialize(self):
        """Serialize the domain node state."""
        base_data = super().serialize()
        
        # Ensure selected_domain is saved in multiple places for redundancy
        selected_domain = getattr(self, 'selected_domain', '')
        
        base_data.update({
            'type': 'DomainNode',
            'selected_domain': selected_domain
        })
        
        # Also save in properties for extra safety
        if not hasattr(self, 'properties'):
            self.properties = {}
        self.properties['selected_domain'] = selected_domain
        base_data['properties'] = self.properties
        
        print(f"🏷️ SERIALIZE: Saving domain '{selected_domain}' in both selected_domain and properties")
        return base_data
        
    def deserialize(self, data):
        """Deserialize the domain node state."""
        # Set basic properties directly since BaseNode doesn't have deserialize
        if 'title' in data:
            self.title = data['title']
        if 'custom_name' in data:
            self.custom_name = data['custom_name']
        if 'custom_description' in data:
            self.custom_description = data['custom_description']
        if 'position' in data:
            pos_data = data['position']
            self.setPos(pos_data['x'], pos_data['y'])
        
        # Set domain-specific properties - check multiple sources
        selected_domain = ""
        if 'selected_domain' in data:
            selected_domain = data['selected_domain']
        elif 'properties' in data and data['properties'].get('selected_domain'):
            selected_domain = data['properties']['selected_domain']
        
        if selected_domain:
            self.selected_domain = selected_domain
            # Also save to properties for consistency
            if not hasattr(self, 'properties'):
                self.properties = {}
            self.properties['selected_domain'] = selected_domain
            print(f"🏷️ DESERIALIZE: Restored domain '{selected_domain}' from saved data")
        else:
            print(f"🏷️ DESERIALIZE: No domain found in saved data")
            
    def get_properties(self):
        """Get node-specific properties including selected domain."""
        properties = {}
        if hasattr(self, 'selected_domain'):
            properties['selected_domain'] = self.selected_domain
        return properties


class NodeConnection(QGraphicsPathItem):
    """Permanent connection between two nodes."""
    
    def __init__(self, start_port, end_port):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.output_port = start_port  # For compatibility
        self.input_port = end_port     # For compatibility
        
        # Make connection selectable and interactive
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # Styling - normal state
        self.normal_pen = QPen(QColor(100, 150, 255), 2)  # Blue connection
        self.hover_pen = QPen(QColor(255, 100, 100), 3)   # Red on hover
        self.selected_pen = QPen(QColor(255, 255, 0), 3)  # Yellow when selected
        
        self.setPen(self.normal_pen)
        self.canvas = None  # Will be set by canvas
        
        self.update_path()
        
    def update_path(self):
        """Update the connection path between ports."""
        start_pos = self.start_port.get_scene_position()
        end_pos = self.end_port.get_scene_position()
        
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # Create curved connection
        control_offset = abs(end_pos.x() - start_pos.x()) * 0.5
        control1 = QPointF(start_pos.x() + control_offset, start_pos.y())
        control2 = QPointF(end_pos.x() - control_offset, end_pos.y())
        
        path.cubicTo(control1, control2, end_pos)
        self.setPath(path)
    
    def set_canvas(self, canvas):
        """Set reference to canvas for deletion operations."""
        self.canvas = canvas
        
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter - highlight connection for deletion."""
        self.setPen(self.hover_pen)
        self.setToolTip("🗑️ Right-click to delete connection\n📋 Double-click for connection info")
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave - restore normal appearance."""
        if self.isSelected():
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
            self.setPen(self.selected_pen)
            print(f"🔗 Connection selected: {self.start_port.parent_node.get_display_name()} → {self.end_port.parent_node.get_display_name()}")
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to show connection info."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.show_connection_info()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
            
    def show_context_menu(self, event):
        """Show context menu for connection operations."""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu()
        
        # Connection info
        info_text = f"{self.start_port.parent_node.get_display_name()} → {self.end_port.parent_node.get_display_name()}"
        menu.addAction(f"📋 {info_text}").setEnabled(False)
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete Connection")
        delete_action.triggered.connect(self.delete_connection)
        
        # Show connection details
        details_action = menu.addAction("📊 Connection Details")
        details_action.triggered.connect(self.show_connection_info)
        
        # Execute menu
        if hasattr(event, 'screenPos'):
            menu.exec(event.screenPos())
        else:
            menu.exec(event.globalPosition().toPoint())
            
    def show_connection_info(self):
        """Show detailed connection information."""
        from PyQt6.QtWidgets import QMessageBox
        
        info_text = f"""
🔗 CONNECTION DETAILS

📤 From: {self.start_port.parent_node.get_display_name()}
   Port: {self.start_port.port_type.upper()}
   
📥 To: {self.end_port.parent_node.get_display_name()}
   Port: {self.end_port.port_type.upper()}

🎛️ DELETION OPTIONS:
• Right-click connection → Delete
• Select connection → Press Delete key
• Double-click connection → Details dialog

💡 The connection transfers data from the output node to the input node.
        """
        
        QMessageBox.information(None, "📊 Connection Information", info_text)
        
    def delete_connection(self):
        """Delete this connection."""
        if self.canvas:
            print(f"🗑️ Deleting connection: {self.start_port.parent_node.get_display_name()} → {self.end_port.parent_node.get_display_name()}")
            self.canvas.delete_connection(self)
        
    def keyPressEvent(self, event):
        """Handle delete key press."""
        if event.key() == Qt.Key.Key_Delete:
            self.delete_connection()
            event.accept()
        else:
            super().keyPressEvent(event)
        
    def serialize(self):
        """Serialize connection data."""
        return {
            "start_node": self.start_port.parent_node.node_id,
            "end_node": self.end_port.parent_node.node_id,
            "start_port": self.start_port.port_type,
            "end_port": self.end_port.port_type
        }


class ColumnKeepDropNode(BaseNode):
    """Node for keeping or dropping columns with dual pane interface."""
    
    def __init__(self):
        super().__init__("📋 Column Keep/Drop")
        self.included_columns = []  # Columns to keep (default: all)
        self.excluded_columns = []  # Columns to drop (user selections)
        self.available_columns = []  # All available columns from input
        
        # Purple gradient for column management nodes
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(156, 39, 176))    # Light purple
        gradient.setColorAt(1, QColor(123, 31, 162))    # Dark purple
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(186, 104, 200), 3))
        
    def add_node_icon(self):
        """Add column management icon."""
        icon_size = 32
        icon_x = (self.rect().width() - icon_size) / 2
        icon_y = (self.rect().height() - icon_size) / 2 + 5
        
        icon_text = QGraphicsTextItem("📋", self)
        icon_text.setFont(QFont("Segoe UI", 16))
        icon_text.setDefaultTextColor(QColor(255, 255, 255, 200))
        icon_text.setPos(icon_x, icon_y)
        icon_text.setZValue(50)
        return icon_text
    
    def get_properties(self):
        """Get column keep/drop properties with multiple data source support."""
        properties = {}
        
        # Get included columns from multiple sources for robustness
        included_columns = []
        if hasattr(self, 'included_columns'):
            included_columns = self.included_columns or []
        elif hasattr(self, 'properties') and 'included_columns' in self.properties:
            included_columns = self.properties['included_columns'] or []
        
        # Get excluded columns from multiple sources for robustness
        excluded_columns = []
        if hasattr(self, 'excluded_columns'):
            excluded_columns = self.excluded_columns or []
        elif hasattr(self, 'properties') and 'excluded_columns' in self.properties:
            excluded_columns = self.properties['excluded_columns'] or []
            
        # Get available columns
        available_columns = getattr(self, 'available_columns', [])
        
        properties.update({
            "included_columns": included_columns,
            "excluded_columns": excluded_columns,
            "available_columns": available_columns
        })
        
        print(f"📋 GET_PROPERTIES: Returning included={len(included_columns)}, excluded={len(excluded_columns)}, available={len(available_columns)}")
        return properties
    
    def set_properties(self, properties):
        """Restore column keep/drop properties with enhanced error handling."""
        print(f"📋 SET_PROPERTIES: Restoring properties: {properties}")
        
        # Restore included columns
        if "included_columns" in properties:
            self.included_columns = properties["included_columns"] or []
        
        # Restore excluded columns  
        if "excluded_columns" in properties:
            self.excluded_columns = properties["excluded_columns"] or []
            
        # Restore available columns
        if "available_columns" in properties:
            self.available_columns = properties["available_columns"] or []
        
        # Also save to properties dict for consistency (like DomainNode)
        if not hasattr(self, 'properties'):
            self.properties = {}
        self.properties.update({
            'included_columns': self.included_columns,
            'excluded_columns': self.excluded_columns,
            'available_columns': self.available_columns
        })
        
        print(f"✅ RESTORED column keep/drop: included={len(self.included_columns)}, excluded={len(self.excluded_columns)}, available={len(self.available_columns)}")
        print(f"📋 INCLUDED COLUMNS: {self.included_columns}")
        print(f"📋 EXCLUDED COLUMNS: {self.excluded_columns}")
    
    def serialize(self):
        """Serialize the column keep/drop node state."""
        base_data = super().serialize()
        
        # Ensure column selections are saved in multiple places for redundancy
        included_columns = getattr(self, 'included_columns', [])
        excluded_columns = getattr(self, 'excluded_columns', [])
        available_columns = getattr(self, 'available_columns', [])
        
        base_data.update({
            'type': 'ColumnKeepDropNode',
            'included_columns': included_columns,
            'excluded_columns': excluded_columns,
            'available_columns': available_columns
        })
        
        # Also save in properties for extra safety (like DomainNode)
        if not hasattr(self, 'properties'):
            self.properties = {}
        self.properties.update({
            'included_columns': included_columns,
            'excluded_columns': excluded_columns,
            'available_columns': available_columns
        })
        base_data['properties'] = self.properties
        
        print(f"📋 SERIALIZE: Saving column keep/drop - included={len(included_columns)}, excluded={len(excluded_columns)}, available={len(available_columns)}")
        return base_data
    
    def deserialize(self, data):
        """Deserialize the column keep/drop node state."""
        # Set basic properties directly since BaseNode doesn't have deserialize
        if 'title' in data:
            self.title = data['title']
        if 'custom_name' in data:
            self.custom_name = data['custom_name']
        if 'custom_description' in data:
            self.custom_description = data['custom_description']
        if 'position' in data:
            pos_data = data['position']
            self.setPos(pos_data['x'], pos_data['y'])
        
        # Set column keep/drop specific properties - check multiple sources
        included_columns = []
        excluded_columns = []
        available_columns = []
        
        # Check direct properties first
        if 'included_columns' in data:
            included_columns = data['included_columns'] or []
        elif 'properties' in data and data['properties'].get('included_columns'):
            included_columns = data['properties']['included_columns'] or []
            
        if 'excluded_columns' in data:
            excluded_columns = data['excluded_columns'] or []
        elif 'properties' in data and data['properties'].get('excluded_columns'):
            excluded_columns = data['properties']['excluded_columns'] or []
            
        if 'available_columns' in data:
            available_columns = data['available_columns'] or []
        elif 'properties' in data and data['properties'].get('available_columns'):
            available_columns = data['properties']['available_columns'] or []
        
        # Set the attributes
        self.included_columns = included_columns
        self.excluded_columns = excluded_columns  
        self.available_columns = available_columns
        
        # Also save to properties for consistency
        if not hasattr(self, 'properties'):
            self.properties = {}
        self.properties.update({
            'included_columns': included_columns,
            'excluded_columns': excluded_columns,
            'available_columns': available_columns
        })
        
        print(f"📋 DESERIALIZE: Restored column keep/drop - included={len(included_columns)}, excluded={len(excluded_columns)}, available={len(available_columns)}")
        print(f"📋 LOADED INCLUDED: {included_columns}")
        print(f"📋 LOADED EXCLUDED: {excluded_columns}")
    
    def has_output_data(self):
        """Check if this node has output data available."""
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'execution_engine'):
            execution_engine = self.canvas.execution_engine
            return execution_engine and hasattr(execution_engine, 'node_outputs') and self in execution_engine.node_outputs
        return False
    
    def get_output_data(self):
        """Get the output data from this node."""
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'execution_engine'):
            execution_engine = self.canvas.execution_engine
            if execution_engine and hasattr(execution_engine, 'node_outputs') and self in execution_engine.node_outputs:
                return execution_engine.node_outputs[self]
        return None
    
    def refresh_available_columns(self):
        """Refresh available columns from connected input nodes with robust error handling."""
        try:
            if not hasattr(self, 'canvas') or not self.canvas:
                print(f"📋 No canvas available for column refresh")
                return
            
            # Get available columns from connected input nodes
            available_columns = []
            connection_count = 0
            
            # Safely iterate through connections
            connections = getattr(self.canvas, 'connections', [])
            if not connections:
                print(f"📋 No connections found on canvas")
                return
            
            for connection in connections:
                try:
                    if (hasattr(connection, 'end_port') and 
                        hasattr(connection.end_port, 'parent_node') and 
                        connection.end_port.parent_node == self):
                        
                        connection_count += 1
                        start_node = connection.start_port.parent_node
                        
                        # Safely check for execution engine and data
                        if (hasattr(start_node, 'canvas') and 
                            start_node.canvas and 
                            hasattr(start_node.canvas, 'execution_engine') and
                            start_node.canvas.execution_engine):
                            
                            execution_engine = start_node.canvas.execution_engine
                            
                            if (hasattr(execution_engine, 'node_outputs') and 
                                start_node in execution_engine.node_outputs):
                                
                                input_data = execution_engine.node_outputs[start_node]
                                if input_data is not None and hasattr(input_data, 'columns'):
                                    column_list = list(input_data.columns)
                                    available_columns.extend(column_list)
                                    print(f"📋 Found {len(column_list)} columns from {getattr(start_node, 'title', 'Unknown Node')}")
                                else:
                                    print(f"📋 No data available from {getattr(start_node, 'title', 'Unknown Node')}")
                            else:
                                print(f"📋 No output data for {getattr(start_node, 'title', 'Unknown Node')}")
                        else:
                            print(f"📋 No execution engine for {getattr(start_node, 'title', 'Unknown Node')}")
                            
                except Exception as e:
                    print(f"⚠️ Error processing connection: {e}")
                    continue
            
            print(f"📋 Processed {connection_count} connections")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_columns = []
            for col in available_columns:
                if col and col not in seen:  # Also check for empty/None columns
                    seen.add(col)
                    unique_columns.append(col)
            
            # Update available columns
            previous_available = len(getattr(self, 'available_columns', []))
            self.available_columns = unique_columns
            
            # Initialize with ALL COLUMNS IN EXCLUDED by default (user requirement)
            # Only do this if this is a fresh initialization
            if (not getattr(self, 'included_columns', []) and 
                not getattr(self, 'excluded_columns', []) and 
                self.available_columns):
                
                print(f"📋 Fresh initialization - putting all {len(self.available_columns)} columns in EXCLUDED section")
                self.included_columns = []  # Start empty
                self.excluded_columns = self.available_columns.copy()  # All columns in excluded
                
            elif previous_available != len(self.available_columns):
                # Available columns changed - add new ones to excluded
                if not hasattr(self, 'included_columns'):
                    self.included_columns = []
                if not hasattr(self, 'excluded_columns'):
                    self.excluded_columns = []
                    
                for col in self.available_columns:
                    if col not in self.included_columns and col not in self.excluded_columns:
                        self.excluded_columns.append(col)
                        print(f"📋 Added new column '{col}' to excluded section")
            
            print(f"📋 Column Keep/Drop: Refreshed columns - Available: {len(self.available_columns)}, Included: {len(getattr(self, 'included_columns', []))}, Excluded: {len(getattr(self, 'excluded_columns', []))}")
            
        except Exception as e:
            print(f"❌ Error in refresh_available_columns: {e}")
            import traceback
            traceback.print_exc()
            
            # Initialize with safe defaults if refresh fails
            if not hasattr(self, 'available_columns'):
                self.available_columns = []
            if not hasattr(self, 'included_columns'):
                self.included_columns = []
            if not hasattr(self, 'excluded_columns'):
                self.excluded_columns = []


class JoinNode(BaseNode):
    """KNIME-style Join node for combining datasets"""
    
    def __init__(self):
        super().__init__("🔗 Join", width=120, height=80)
        
        # Join configuration
        self.join_type = "inner"  # inner, left, right, outer
        self.left_columns = []    # Columns from left dataset for joining
        self.right_columns = []   # Columns from right dataset for joining
        self.duplicate_handling = "skip"  # append, skip
        self.column_suffix_left = "_left"
        self.column_suffix_right = "_right"
        
        # Available columns from input datasets
        self.left_available_columns = []
        self.right_available_columns = []
        
        # Join node specific styling - Orange gradient for database operations
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(255, 152, 0))   # Bright orange
        gradient.setColorAt(1, QColor(255, 87, 34))   # Deep orange
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(255, 193, 7), 3))  # Amber border
        
    def execute(self, input_data=None):
        """Execute the join operation"""
        try:
            print(f"🔗 JOIN EXECUTE: Starting join operation for {self.title}")
            
            # Get input data from connected nodes
            left_data, right_data = self._get_input_datasets()
            
            if left_data is None or right_data is None:
                raise ValueError("Both left and right datasets are required for join")
            
            if not self.left_columns or not self.right_columns:
                raise ValueError("Join columns must be specified for both datasets")
            
            if len(self.left_columns) != len(self.right_columns):
                raise ValueError("Number of join columns must match between left and right datasets")
                
            print(f"🔗 JOIN EXECUTE: Left data shape: {left_data.shape}")
            print(f"🔗 JOIN EXECUTE: Right data shape: {right_data.shape}")
            print(f"🔗 JOIN EXECUTE: Join type: {self.join_type}")
            print(f"🔗 JOIN EXECUTE: Left columns: {self.left_columns}")
            print(f"🔗 JOIN EXECUTE: Right columns: {self.right_columns}")
            
            # Create a copy to avoid modifying original data
            left_df = left_data.copy()
            right_df = right_data.copy()
            
            # Handle column name conflicts before join
            left_df, right_df = self._handle_column_conflicts(left_df, right_df)
            
            # Determine pandas join parameters
            how = self.join_type
            if self.join_type == "outer":
                how = "outer"
            elif self.join_type == "left":
                how = "left"
            elif self.join_type == "right":
                how = "right"
            else:
                how = "inner"
            
            # Perform the join
            if len(self.left_columns) == 1 and len(self.right_columns) == 1:
                # Single column join
                result_df = pd.merge(
                    left_df, 
                    right_df,
                    left_on=self.left_columns[0],
                    right_on=self.right_columns[0],
                    how=how,
                    suffixes=(self.column_suffix_left, self.column_suffix_right)
                )
            else:
                # Multiple column join
                result_df = pd.merge(
                    left_df,
                    right_df,
                    left_on=self.left_columns,
                    right_on=self.right_columns,
                    how=how,
                    suffixes=(self.column_suffix_left, self.column_suffix_right)
                )
            
            print(f"🔗 JOIN EXECUTE: Result shape: {result_df.shape}")
            
            # Apply column selection if configured
            if hasattr(self, 'selected_left_columns') or hasattr(self, 'selected_right_columns'):
                result_df = self._apply_column_selection(result_df, left_df, right_df)
                print(f"🔗 JOIN EXECUTE: After column selection: {result_df.shape}")
            
            print(f"🔗 JOIN EXECUTE: Join completed successfully")
            
            # Store output data for execution engine
            self.output_data = result_df
            
            # Return True for execution engine (not the DataFrame)
            return True
            
        except Exception as e:
            print(f"❌ JOIN EXECUTE ERROR: {str(e)}")
            raise e
    
    def _get_input_datasets(self):
        """Get left and right datasets from connected input nodes"""
        left_data = None
        right_data = None
        connected_inputs = 0
        
        # Check for connected input nodes
        for connection in self.canvas.connections if self.canvas else []:
            if connection.end_port and connection.end_port.parent_node == self:
                connected_inputs += 1
                source_node = connection.start_port.parent_node
                
                print(f"🔗 JOIN: Processing input {connected_inputs} from {source_node.title}")
                
                # Try to get data from execution engine cache first
                data = None
                if hasattr(self.canvas, 'execution_engine') and self.canvas.execution_engine:
                    execution_engine = self.canvas.execution_engine
                    
                    # Try both node object and title as keys
                    if source_node in execution_engine.node_outputs:
                        data = execution_engine.node_outputs[source_node]
                        print(f"🔗 JOIN: Found data in cache (node object key)")
                    elif hasattr(source_node, 'title') and source_node.title in execution_engine.node_outputs:
                        data = execution_engine.node_outputs[source_node.title]
                        print(f"🔗 JOIN: Found data in cache (title key)")
                    else:
                        # Data not in cache, try to execute upstream node
                        print(f"🔗 JOIN: Data not cached, executing upstream node: {source_node.title}")
                        success = execution_engine.execute_node(source_node)
                        if success:
                            # Try again after execution
                            if source_node in execution_engine.node_outputs:
                                data = execution_engine.node_outputs[source_node]
                                print(f"🔗 JOIN: Got data after execution (node object key)")
                            elif hasattr(source_node, 'title') and source_node.title in execution_engine.node_outputs:
                                data = execution_engine.node_outputs[source_node.title]
                                print(f"🔗 JOIN: Got data after execution (title key)")
                
                # If execution engine didn't work, try direct node access
                if data is None and hasattr(source_node, 'dataframe') and source_node.dataframe is not None:
                    data = source_node.dataframe
                    print(f"🔗 JOIN: Using node's direct dataframe attribute")
                
                if data is not None:
                    print(f"🔗 JOIN: Got data with shape: {data.shape}")
                    if connected_inputs == 1:
                        left_data = data
                    elif connected_inputs == 2:
                        right_data = data
                else:
                    print(f"❌ JOIN: No data available from {source_node.title}")
        
        print(f"🔗 JOIN: Final datasets - Left: {left_data.shape if left_data is not None else 'None'}, Right: {right_data.shape if right_data is not None else 'None'}")
        return left_data, right_data
    
    def _handle_column_conflicts(self, left_df, right_df):
        """Handle conflicting column names between datasets"""
        left_cols = set(left_df.columns)
        right_cols = set(right_df.columns)
        
        # Find join columns to exclude from conflict checking
        join_cols_left = set(self.left_columns)
        join_cols_right = set(self.right_columns)
        
        # Find conflicting columns (excluding join columns)
        conflicting = (left_cols & right_cols) - join_cols_left - join_cols_right
        
        if conflicting:
            print(f"🔗 Handling {len(conflicting)} conflicting columns: {conflicting}")
            
            # Apply suffix to conflicting columns
            left_rename = {}
            right_rename = {}
            
            for col in conflicting:
                if self.duplicate_handling == "append":
                    # Add suffix to both
                    left_rename[col] = f"{col}{self.column_suffix_left}"
                    right_rename[col] = f"{col}{self.column_suffix_right}"
                elif self.duplicate_handling == "skip":
                    # Keep left, rename right
                    right_rename[col] = f"{col}{self.column_suffix_right}"
            
            if left_rename:
                left_df = left_df.rename(columns=left_rename)
            if right_rename:
                right_df = right_df.rename(columns=right_rename)
        
        return left_df, right_df
    
    def _apply_column_selection(self, result_df, left_df, right_df):
        """Apply column selection to the join result"""
        try:
            # Get selected columns for left and right datasets
            selected_left = getattr(self, 'selected_left_columns', [])
            selected_right = getattr(self, 'selected_right_columns', [])
            
            if not selected_left and not selected_right:
                # No column selection specified, return all columns
                return result_df
                
            # Build list of columns to keep
            columns_to_keep = []
            
            # Always include join columns (they are essential)
            join_columns = set()
            if hasattr(self, 'left_columns') and hasattr(self, 'right_columns'):
                # Add the actual join columns from the result
                for left_col, right_col in zip(self.left_columns, self.right_columns):
                    if left_col in result_df.columns:
                        join_columns.add(left_col)
                        columns_to_keep.append(left_col)
                    elif right_col in result_df.columns:
                        join_columns.add(right_col)
                        columns_to_keep.append(right_col)
            
            # Add selected left columns (excluding join columns already added)
            if selected_left:
                for col in selected_left:
                    # Handle renamed columns due to suffix
                    original_col = col
                    suffixed_col = f"{col}{self.column_suffix_left}"
                    
                    if original_col in result_df.columns and original_col not in join_columns:
                        columns_to_keep.append(original_col)
                    elif suffixed_col in result_df.columns:
                        columns_to_keep.append(suffixed_col)
            
            # Add selected right columns (excluding join columns already added)
            if selected_right:
                for col in selected_right:
                    # Handle renamed columns due to suffix
                    original_col = col
                    suffixed_col = f"{col}{self.column_suffix_right}"
                    
                    if original_col in result_df.columns and original_col not in join_columns:
                        columns_to_keep.append(original_col)
                    elif suffixed_col in result_df.columns:
                        columns_to_keep.append(suffixed_col)
            
            # Remove duplicates while preserving order
            final_columns = []
            for col in columns_to_keep:
                if col not in final_columns and col in result_df.columns:
                    final_columns.append(col)
            
            if final_columns:
                print(f"🔗 Column selection: Keeping {len(final_columns)} of {len(result_df.columns)} columns")
                print(f"🔗 Selected columns: {final_columns}")
                result_df = result_df[final_columns]
            else:
                print("⚠️ Column selection resulted in no columns, keeping all")
            
            return result_df
            
        except Exception as e:
            print(f"❌ Error applying column selection: {e}")
            # Return original dataframe if column selection fails
            return result_df
    
    
    def get_properties(self):
        """Return current join configuration"""
        return {
            "join_type": self.join_type,
            "left_columns": self.left_columns,
            "right_columns": self.right_columns,
            "duplicate_handling": self.duplicate_handling,
            "column_suffix_left": self.column_suffix_left,
            "column_suffix_right": self.column_suffix_right,
            "left_available_columns": self.left_available_columns,
            "right_available_columns": self.right_available_columns,
            "selected_left_columns": getattr(self, 'selected_left_columns', []),
            "selected_right_columns": getattr(self, 'selected_right_columns', [])
        }
    
    def set_properties(self, properties):
        """Set join configuration from saved properties"""
        self.join_type = properties.get("join_type", "inner")
        self.left_columns = properties.get("left_columns", [])
        self.right_columns = properties.get("right_columns", [])
        self.duplicate_handling = properties.get("duplicate_handling", "skip")
        self.column_suffix_left = properties.get("column_suffix_left", "_left")
        self.column_suffix_right = properties.get("column_suffix_right", "_right")
        self.left_available_columns = properties.get("left_available_columns", [])
        self.right_available_columns = properties.get("right_available_columns", [])
        self.selected_left_columns = properties.get("selected_left_columns", [])
        self.selected_right_columns = properties.get("selected_right_columns", [])
        
        print(f"🔗 JOIN SET_PROPERTIES: Restored join configuration")
        print(f"🔗 Join type: {self.join_type}")
        print(f"🔗 Left columns: {self.left_columns}")
        print(f"🔗 Right columns: {self.right_columns}")
    
    def serialize(self):
        """Serialize join configuration for saving"""
        data = super().serialize()
        data.update({
            "join_type": self.join_type,
            "left_columns": self.left_columns,
            "right_columns": self.right_columns,
            "duplicate_handling": self.duplicate_handling,
            "column_suffix_left": self.column_suffix_left,
            "column_suffix_right": self.column_suffix_right,
            "left_available_columns": self.left_available_columns,
            "right_available_columns": self.right_available_columns,
            "selected_left_columns": getattr(self, 'selected_left_columns', []),
            "selected_right_columns": getattr(self, 'selected_right_columns', [])
        })
        return data
    
    def deserialize(self, data):
        """Deserialize join configuration from saved data"""
        # Set basic properties directly since BaseNode doesn't have deserialize
        if 'title' in data:
            self.title = data['title']
        if 'custom_name' in data:
            self.custom_name = data['custom_name']
        if 'custom_description' in data:
            self.custom_description = data['custom_description']
        if 'position' in data:
            pos_data = data['position']
            self.setPos(pos_data['x'], pos_data['y'])
        
        # Set join-specific properties
        self.set_properties(data)
    
    def update_available_columns(self):
        """Update available columns from connected input nodes"""
        try:
            self.left_available_columns = []
            self.right_available_columns = []
            
            # Get canvas reference - try multiple approaches
            canvas = None
            
            # Method 1: Check scene and views
            if hasattr(self, 'scene') and self.scene():
                views = self.scene().views()
                for view in views:
                    if hasattr(view, 'parent') and view.parent():
                        parent = view.parent()
                        if hasattr(parent, 'canvas'):
                            canvas = parent.canvas
                            break
                        if hasattr(parent, 'flow_canvas'):
                            canvas = parent.flow_canvas
                            break
            
            # Method 2: Direct canvas reference
            if not canvas and hasattr(self, 'canvas'):
                canvas = self.canvas
            
            # Method 3: Try to find canvas in scene items
            if not canvas and hasattr(self, 'scene') and self.scene():
                scene_items = self.scene().items()
                for item in scene_items:
                    if hasattr(item, 'canvas') and hasattr(item.canvas, 'connections'):
                        canvas = item.canvas
                        break
            
            if not canvas:
                print("🔗 JOIN: No canvas found for column detection")
                return
                
            print(f"🔗 JOIN: Found canvas with {len(canvas.connections)} total connections")
            
            # Find connections TO this join node (input connections)
            input_connections = []
            for connection in canvas.connections:
                try:
                    if hasattr(connection, 'end_port') and connection.end_port:
                        # Check if this connection ends at our join node
                        end_node = getattr(connection.end_port, 'parent_node', None) or getattr(connection.end_port, 'node', None)
                        if end_node == self:
                            input_connections.append(connection)
                            print(f"🔗 JOIN: Found input connection from {getattr(connection.start_port.parent_node if hasattr(connection.start_port, 'parent_node') else connection.start_port.node, 'title', 'Unknown')}")
                except Exception as conn_err:
                    print(f"🔗 JOIN: Error checking connection: {conn_err}")
                    continue
            
            print(f"🔗 JOIN: Found {len(input_connections)} input connections")
            
            # Process each input connection
            for i, connection in enumerate(input_connections):
                try:
                    source_node = getattr(connection.start_port, 'parent_node', None) or getattr(connection.start_port, 'node', None)
                    if source_node:
                        print(f"🔗 JOIN: Processing connection {i+1} from {getattr(source_node, 'title', 'Unknown')}")
                        columns = self._get_columns_from_node(source_node, canvas)
                        
                        if i == 0:  # First connection = left dataset
                            self.left_available_columns = columns
                            print(f"🔗 JOIN: Set left columns ({len(columns)}): {columns[:3]}..." if len(columns) > 3 else f"🔗 JOIN: Set left columns: {columns}")
                        elif i == 1:  # Second connection = right dataset
                            self.right_available_columns = columns
                            print(f"🔗 JOIN: Set right columns ({len(columns)}): {columns[:3]}..." if len(columns) > 3 else f"🔗 JOIN: Set right columns: {columns}")
                except Exception as proc_err:
                    print(f"🔗 JOIN: Error processing connection {i}: {proc_err}")
            
            print(f"🔗 JOIN: Final available columns - Left: {len(self.left_available_columns)}, Right: {len(self.right_available_columns)}")
            
        except Exception as e:
            print(f"❌ Error updating available columns for join: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_columns_from_node(self, source_node, canvas):
        """Get column names from a source node - prioritize execution engine cache"""
        columns = []
        
        try:
            # Method 1: Try from execution engine cache (most reliable)
            if hasattr(canvas, 'execution_engine') and canvas.execution_engine:
                # Try both node object and title as keys
                node_outputs = canvas.execution_engine.node_outputs
                
                # Check with node object as key
                if source_node in node_outputs:
                    data = node_outputs[source_node]
                    if hasattr(data, 'columns'):
                        columns = list(data.columns)
                        print(f"🔗 JOIN: Got {len(columns)} columns from execution engine (node object)")
                        return columns
                
                # Check with node title as key
                if hasattr(source_node, 'title') and source_node.title in node_outputs:
                    data = node_outputs[source_node.title]
                    if hasattr(data, 'columns'):
                        columns = list(data.columns)
                        print(f"🔗 JOIN: Got {len(columns)} columns from execution engine (title)")
                        return columns
            
            # Method 2: Check if node has dataframe attribute directly
            if hasattr(source_node, 'dataframe') and source_node.dataframe is not None:
                if hasattr(source_node.dataframe, 'columns'):
                    columns = list(source_node.dataframe.columns)
                    print(f"🔗 JOIN: Got {len(columns)} columns from node dataframe")
                    return columns
            
            # Method 3: For data input nodes, try to get from data manager
            if hasattr(source_node, 'filename'):
                try:
                    import sys
                    import os
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
                    from data.data_manager import DataManager
                    data_mgr = DataManager()
                    # Try to get cached data first
                    file_path = source_node.filename
                    if file_path in data_mgr.cache:
                        data = data_mgr.cache[file_path]
                        if hasattr(data, 'columns'):
                            columns = list(data.columns)
                            print(f"🔗 JOIN: Got {len(columns)} columns from data manager cache")
                            return columns
                except Exception as dm_err:
                    print(f"🔗 JOIN: Could not get columns from data manager: {dm_err}")
            
            # Method 3: Try from node's available_columns attribute
            if hasattr(source_node, 'available_columns') and source_node.available_columns:
                columns = source_node.available_columns
                print(f"🔗 JOIN: Got {len(columns)} columns from node attribute")
                return columns
            
            # Method 4: For column keep/drop nodes, try included_columns or excluded_columns
            if hasattr(source_node, 'included_columns') and source_node.included_columns:
                columns = source_node.included_columns
                print(f"🔗 JOIN: Got {len(columns)} columns from included_columns")
                return columns
                
            print(f"🔗 JOIN: No columns found for node {getattr(source_node, 'title', 'Unknown')}")
            return []
            
        except Exception as e:
            print(f"🔗 JOIN: Error getting columns from {getattr(source_node, 'title', 'Unknown')}: {e}")
            return []
            
    def refresh_available_columns(self):
        """Refresh available columns from connected nodes (alias for update_available_columns)"""
        self.update_available_columns()
    
    def create_ports(self):
        """Create dual input ports and single output port for Join node."""
        # Left input port (for left dataset)
        left_input = ConnectionPort(-15, 18, 24, 24, "input", self)
        left_input.setToolTip("🔌 LEFT INPUT: Connect first dataset here")
        left_input.setZValue(10)
        self.input_ports.append(left_input)
        
        # Right input port (for right dataset) 
        right_input = ConnectionPort(-15, 42, 24, 24, "input", self)
        right_input.setToolTip("🔌 RIGHT INPUT: Connect second dataset here")
        right_input.setZValue(10)
        self.input_ports.append(right_input)
        
        # Single output port (right side)
        output_port = ConnectionPort(self.rect().width() - 9, 28, 24, 24, "output", self)
        output_port.setToolTip("🔗 OUTPUT: Joined dataset output")
        output_port.setZValue(10)
        self.output_ports.append(output_port)
        
