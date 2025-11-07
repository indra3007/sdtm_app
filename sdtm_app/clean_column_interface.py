#!/usr/bin/env python3
"""
Clean Column Keep/Drop interface implementation
"""

def create_column_keep_drop_properties_clean(self, node):
    """Create clean Column Keep/Drop properties interface."""
    print("📋 Creating column keep/drop properties for:", node.title)
    
    # Get available columns
    available_columns = []
    for connection in node.input_connections:
        source_node = connection.start_port.parent_node
        if hasattr(source_node, 'get_output_data'):
            try:
                data = source_node.get_output_data()
                if data is not None and hasattr(data, 'columns'):
                    available_columns = list(data.columns)
                    break
            except:
                pass
    
    if not available_columns:
        print("📋 Found 0 columns - checking connections")
        return
    
    node.available_columns = available_columns
    print(f"📋 Found {len(available_columns)} columns from {source_node.title}")
    
    # Initialize column lists if needed
    if not hasattr(node, 'included_columns'):
        node.included_columns = []
    if not hasattr(node, 'excluded_columns'):
        node.excluded_columns = available_columns.copy()
        print(f"📋 Fresh initialization - putting all {len(available_columns)} columns in EXCLUDED section")
    
    # Main layout
    layout = QVBoxLayout()
    
    # Column selection area
    selection_label = QLabel("🎯 Select Columns to Keep:")
    selection_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px; margin-bottom: 10px;")
    layout.addWidget(selection_label)
    
    # Create checkboxes for each column in a scrollable area
    from PyQt6.QtWidgets import QCheckBox, QScrollArea
    
    scroll_area = QScrollArea()
    scroll_area.setMaximumHeight(300)
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    
    # Store checkbox references
    self.column_checkboxes = {}
    
    for col in available_columns:
        checkbox = QCheckBox(col)
        checkbox.setChecked(col in node.included_columns)
        checkbox.stateChanged.connect(lambda state, column=col: self.toggle_column_selection_clean(node, column, state))
        checkbox.setStyleSheet("""
            QCheckBox {
                font-family: monospace;
                font-size: 11px;
                padding: 3px;
                margin: 2px;
            }
            QCheckBox:checked {
                color: #27ae60;
                font-weight: bold;
            }
            QCheckBox:unchecked {
                color: #7f8c8d;
            }
        """)
        scroll_layout.addWidget(checkbox)
        self.column_checkboxes[col] = checkbox
    
    scroll_area.setWidget(scroll_widget)
    layout.addWidget(scroll_area)
    
    # Bulk action buttons
    bulk_layout = QHBoxLayout()
    
    keep_all_btn = QPushButton("✅ Keep All")
    keep_all_btn.setStyleSheet("""
        QPushButton {
            background: #27ae60;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover { background: #229954; }
    """)
    keep_all_btn.clicked.connect(lambda: self.keep_all_columns_clean(node))
    bulk_layout.addWidget(keep_all_btn)
    
    drop_all_btn = QPushButton("❌ Drop All")
    drop_all_btn.setStyleSheet("""
        QPushButton {
            background: #e74c3c;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover { background: #c0392b; }
    """)
    drop_all_btn.clicked.connect(lambda: self.drop_all_columns_clean(node))
    bulk_layout.addWidget(drop_all_btn)
    
    layout.addLayout(bulk_layout)
    
    # Status summary
    self.status_label = QLabel()
    self.update_status_summary_clean(node)
    layout.addWidget(self.status_label)
    
    # Standard buttons (Apply, Execute, Cancel)
    button_layout = QHBoxLayout()
    
    apply_btn = QPushButton("✅ Apply")
    apply_btn.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover { background: #2980b9; }
    """)
    apply_btn.clicked.connect(lambda: self.apply_column_selection_clean(node))
    button_layout.addWidget(apply_btn)
    
    execute_btn = QPushButton("🚀 Execute")
    execute_btn.setStyleSheet("""
        QPushButton {
            background: #e67e22;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover { background: #d35400; }
    """)
    execute_btn.clicked.connect(lambda: self.execute_column_selection_clean(node))
    button_layout.addWidget(execute_btn)
    
    cancel_btn = QPushButton("❌ Cancel")
    cancel_btn.setStyleSheet("""
        QPushButton {
            background: #95a5a6;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover { background: #7f8c8d; }
    """)
    cancel_btn.clicked.connect(lambda: self.cancel_column_selection_clean(node))
    button_layout.addWidget(cancel_btn)
    
    layout.addLayout(button_layout)
    
    # Add to main content
    columns_group = QGroupBox("📋 Column Keep/Drop Configuration")
    columns_group.setLayout(layout)
    columns_group.setStyleSheet("""
        QGroupBox {
            border: 2px solid #3498db;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
            background: #f8f9fa;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            background: white;
            color: #3498db;
            font-weight: bold;
        }
    """)
    self.content_layout.addWidget(columns_group)
    print("✅ Clean Column Keep/Drop interface created successfully")

# Helper functions
def update_status_summary_clean(self, node):
    """Update the status summary of included/excluded columns."""
    included_count = len(node.included_columns) if hasattr(node, 'included_columns') else 0
    excluded_count = len(node.excluded_columns) if hasattr(node, 'excluded_columns') else 0
    total_count = len(node.available_columns) if hasattr(node, 'available_columns') else 0
    
    summary_text = f"📊 Status: {included_count} included, {excluded_count} excluded ({total_count} total)"
    self.status_label.setText(summary_text)
    self.status_label.setStyleSheet("color: #34495e; font-weight: bold; padding: 5px; background: #ecf0f1; border-radius: 3px;")

def toggle_column_selection_clean(self, node, column, state):
    """Toggle individual column selection with checkbox."""
    try:
        print(f"🎯 TOGGLE: Column '{column}' state changed to {state}")
        
        if state == 2:  # Checked (keep/include)
            if column not in node.included_columns:
                node.included_columns.append(column)
            if column in node.excluded_columns:
                node.excluded_columns.remove(column)
        else:  # Unchecked (drop/exclude)
            if column in node.included_columns:
                node.included_columns.remove(column)
            if column not in node.excluded_columns:
                node.excluded_columns.append(column)
        
        # Update status summary
        self.update_status_summary_clean(node)
        print(f"🎯 TOGGLE: Updated - {len(node.included_columns)} included, {len(node.excluded_columns)} excluded")
        
    except Exception as e:
        print(f"❌ TOGGLE ERROR: {e}")

def keep_all_columns_clean(self, node):
    """Keep all columns (check all checkboxes)."""
    node.included_columns = node.available_columns.copy()
    node.excluded_columns = []
    
    # Update checkboxes
    if hasattr(self, 'column_checkboxes'):
        for checkbox in self.column_checkboxes.values():
            checkbox.setChecked(True)
    
    self.update_status_summary_clean(node)
    print(f"✅ KEEP ALL: All {len(node.available_columns)} columns included")

def drop_all_columns_clean(self, node):
    """Drop all columns (uncheck all checkboxes)."""
    node.included_columns = []
    node.excluded_columns = node.available_columns.copy()
    
    # Update checkboxes
    if hasattr(self, 'column_checkboxes'):
        for checkbox in self.column_checkboxes.values():
            checkbox.setChecked(False)
    
    self.update_status_summary_clean(node)
    print(f"❌ DROP ALL: All {len(node.available_columns)} columns excluded")

def apply_column_selection_clean(self, node):
    """Apply the current column selection without executing."""
    print(f"✅ APPLY: Column selection applied - {len(node.included_columns)} included")

def execute_column_selection_clean(self, node):
    """Execute the column keep/drop operation."""
    print(f"🚀 EXECUTE: Executing column keep/drop with {len(node.included_columns)} columns")

def cancel_column_selection_clean(self, node):
    """Cancel and reset column selection."""
    # Reset to original state (all excluded by default)
    node.included_columns = []
    node.excluded_columns = node.available_columns.copy()
    
    # Update checkboxes
    if hasattr(self, 'column_checkboxes'):
        for checkbox in self.column_checkboxes.values():
            checkbox.setChecked(False)
    
    self.update_status_summary_clean(node)
    print("❌ CANCEL: Column selection reset")