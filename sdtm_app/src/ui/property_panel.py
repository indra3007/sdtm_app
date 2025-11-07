"""
Property Panel - Dynamic configuration interface for selected nodes
Provides context-sensitive property editing based on node type.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QPushButton, QCheckBox, QRadioButton,
    QSpinBox, QDoubleSpinBox, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem, QMessageBox,
    QAbstractItemView, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


# Standardized Button Styling Constants for the Application
BUTTON_STYLE_PRIMARY = "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px; min-width: 120px;"
BUTTON_STYLE_SECONDARY = "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px; min-width: 100px;"
BUTTON_STYLE_DANGER = "background-color: #f44336; color: white; font-weight: bold; padding: 8px 16px; min-width: 80px;"
BUTTON_STYLE_SMALL = "background-color: #2196F3; color: white; font-weight: bold; padding: 6px 12px; min-width: 80px;"


class CustomSizedComboBox(QComboBox):
    """Custom ComboBox that forces proper popup sizing and prevents wheel scrolling."""
    pass


class PropertyPanel(QScrollArea):
    """Dynamic property panel that adapts to selected node types."""
    
    # Signals
    data_refresh_requested = pyqtSignal(object)  # Signal to request data refresh for a node
    
    def __init__(self, parent=None):
        """Initialize the property panel."""
        super().__init__(parent)
        
        # Main content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        
        # Set the main widget
        self.setWidget(self.content_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Current node reference
        self.current_node = None
        self.canvas = None
        self._canvas_ref = None  # Initialize _canvas_ref to prevent AttributeError
        self.main_window = None
        
        # Initialize with empty state
        self.show_empty_state()
    
    def set_main_window_reference(self, main_window):
        """Set reference to the main window for SDTM suggestions and other features."""
        self.main_window = main_window
        print(f"🔗 PropertyPanel: Main window reference set")
    
    def set_canvas_reference(self, canvas):
        """Set reference to the flow canvas for node interactions."""
        self.canvas = canvas
        self._canvas_ref = canvas  # Also set _canvas_ref for backward compatibility
        print(f"🔗 PropertyPanel: Canvas reference set")
    
    def show_empty_state(self):
        """Show empty state when no node is selected."""
        self.clear_content()
        
        empty_label = QLabel("Select a node to view its properties")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("color: #888; font-size: 14px; margin: 50px;")
        self.content_layout.addWidget(empty_label)
    
    def clear_content(self):
        """Clear all widgets from the content layout."""
        try:
            if hasattr(self, 'content_layout') and self.content_layout:
                while self.content_layout.count():
                    child = self.content_layout.takeAt(0)
                    if child and child.widget():
                        child.widget().deleteLater()
        except (RuntimeError, SystemError) as e:
            # Layout was already deleted or corrupted, recreate it
            print(f"🔄 Layout recreation needed: {e}")
            try:
                # Recreate the entire content structure
                self.content_widget = QWidget()
                self.content_layout = QVBoxLayout(self.content_widget)
                self.content_layout.setContentsMargins(10, 10, 10, 10)
                self.content_layout.setSpacing(10)
                self.setWidget(self.content_widget)
                print("✅ Layout recreated successfully")
            except Exception as recreate_error:
                print(f"❌ Failed to recreate layout: {recreate_error}")
                # As last resort, try to get the existing layout
                if hasattr(self, 'content_widget') and self.content_widget:
                    existing_layout = self.content_widget.layout()
                    if existing_layout:
                        self.content_layout = existing_layout
    
    def show_properties(self, node):
        """Show properties for the given node."""
        if not node:
            self.show_empty_state()
            return
            
        self.current_node = node
        self.set_node(node)
    
    def set_node(self, node):
        """Set the current node and create appropriate properties interface."""
        try:
            self.clear_content()
            
            if hasattr(node, '__class__'):
                node_type = node.__class__.__name__
                print(f"PropertyPanel: Creating properties for {node_type}")
                
                if node_type == "DataInputNode":
                    self.create_input_node_properties(node)
                elif node_type == "ColumnRenamerNode":
                    self.create_column_renamer_properties(node)
                elif node_type == "ColumnKeepDropNode":
                    self.create_column_keep_drop_properties(node)
                elif node_type == "RowFilterNode":
                    self.create_row_filter_properties(node)
                elif node_type == "ExpressionBuilderNode":
                    self.create_expression_builder_properties(node)
                elif node_type == "ConditionalMappingNode":
                    self.create_conditional_mapping_properties(node)
                elif node_type == "DomainNode":
                    self.create_domain_properties(node)
                elif node_type == "ConstantValueColumnNode":
                    self.create_constant_value_properties(node)
                else:
                    self.create_generic_properties(node)
                    
        except Exception as e:
            print(f"ERROR in set_node: {str(e)}")
            try:
                # Try to show a simple error message instead of crashing
                from PyQt6.QtWidgets import QLabel
                error_label = QLabel(f"Error loading properties for {getattr(node, 'title', 'unknown node')}")
                error_label.setStyleSheet("color: red; padding: 20px;")
                if hasattr(self, 'content_layout') and self.content_layout:
                    self.content_layout.addWidget(error_label)
            except:
                print("Failed to show error message in property panel")
    
    def show_notification(self, message, is_error=False):
        """Show notification message."""
        print(f"NOTIFICATION: {message}")
    
    def get_execution_engine(self, node):
        """Get execution engine from canvas."""
        if hasattr(self, 'canvas') and self.canvas:
            return getattr(self.canvas, 'execution_engine', None)
        return None
    
    def view_node_data(self, node, data, title):
        """View node data in data viewer."""
        print(f"👁️ VIEW: {title} for {node.title}")
    
    def show_no_data_message(self, message):
        """Show no data available message."""
        print(f"⚠️ NO DATA: {message}")
    
    def get_available_columns_for_node(self, node):
        """Get available columns for a node."""
        if hasattr(node, 'available_columns'):
            return node.available_columns
        return ["⚠️ Connect input data to see available columns"]
    
    def create_generic_properties(self, node):
        """Create generic properties for unknown node types."""
        label = QLabel(f"Properties for {node.title}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(label)

    def create_input_node_properties(self, node):
        """Create properties for data input nodes."""
        # Node info group
        info_group = QGroupBox("Dataset Information")
        info_layout = QFormLayout(info_group)
        
        filename_label = QLabel(node.filename)
        filename_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Filename:", filename_label)
        
        # Check if node has been executed (has output data)
        execution_engine = self.get_execution_engine(node)
        output_data = None
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
        
        if output_data is not None:
            # Show executed data info
            rows_label = QLabel(f"{len(output_data)} (after execution)")
            rows_label.setStyleSheet("color: green; font-weight: bold;")
            info_layout.addRow("Rows:", rows_label)
            
            cols_label = QLabel(f"{len(output_data.columns)} (after execution)")
            cols_label.setStyleSheet("color: green; font-weight: bold;")
            info_layout.addRow("Columns:", cols_label)
            
            # Execution status
            status_label = QLabel("✅ Executed")
            status_label.setStyleSheet("color: green; font-weight: bold;")
            info_layout.addRow("Status:", status_label)
        else:
            # Show original data info
            if node.dataframe is not None:
                rows_label = QLabel(f"{len(node.dataframe)} (original)")
                info_layout.addRow("Rows:", rows_label)
                
                cols_label = QLabel(f"{len(node.dataframe.columns)} (original)")
                info_layout.addRow("Columns:", cols_label)
            else:
                # Data not loaded (e.g., from saved workflow)
                rows_label = QLabel("Data not loaded")
                info_layout.addRow("Rows:", rows_label)
                
                cols_label = QLabel("Data not loaded")
                info_layout.addRow("Columns:", cols_label)
            
            # Execution status
            status_label = QLabel("⏳ Not executed")
            status_label.setStyleSheet("color: orange;")
            info_layout.addRow("Status:", status_label)
        
        self.content_layout.addWidget(info_group)
        
        # Data viewing buttons
        buttons_group = QGroupBox("Data Actions")
        buttons_layout = QVBoxLayout(buttons_group)
        
        # View original data button
        view_original_btn = QPushButton("👁️ View Original Data")
        view_original_btn.setToolTip("View the original data for this node")
        if node.dataframe is not None:
            view_original_btn.setStyleSheet(BUTTON_STYLE_SECONDARY)
            view_original_btn.clicked.connect(lambda: self.view_node_data(node, node.dataframe, "Original Data"))
        else:
            view_original_btn.setStyleSheet("background-color: #cccccc; color: #666666; font-weight: bold; padding: 8px 16px; min-width: 100px;")
            view_original_btn.clicked.connect(lambda: self.show_no_data_message("Original data not available"))
        buttons_layout.addWidget(view_original_btn)
        
        # View executed data button (if available)
        if output_data is not None:
            view_executed_btn = QPushButton("🚀 View Executed Data")
            view_executed_btn.setToolTip("View the executed/transformed data")
            view_executed_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
            view_executed_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Executed Data"))
            buttons_layout.addWidget(view_executed_btn)
        
        self.content_layout.addWidget(buttons_group)
        
        # Column list
        columns_group = QGroupBox("Columns")
        columns_layout = QVBoxLayout(columns_group)
        
        # Show columns from executed data if available, otherwise original
        data_to_show = output_data if output_data is not None else node.dataframe
        
        columns_list = QListWidget()
        
        if data_to_show is not None:
            for col in data_to_show.columns:
                item = QListWidgetItem(col)
                # Highlight new/changed columns if this is executed data
                if output_data is not None and node.dataframe is not None and col not in node.dataframe.columns:
                    item.setBackground(Qt.GlobalColor.green)
                    item.setToolTip("New column created during execution")
                columns_list.addItem(item)
        else:
            # No data available
            item = QListWidgetItem("No data available")
            item.setForeground(Qt.GlobalColor.gray)
            columns_list.addItem(item)
            
        columns_layout.addWidget(columns_list)
        self.content_layout.addWidget(columns_group)
        
        self.content_layout.addStretch()
        
    def create_column_renamer_properties(self, node):
        """Create properties for column renamer nodes using standardized template."""
        # Clear any existing instance variables to prevent widget repetition
        self.checkbox_widget = None
        self.checkbox_layout = None  
        self.suffix_checkboxes = []
        self.suffix_input = None
        self.rename_table = None
        self.column_search_input = None
            
        layout = QVBoxLayout()
        
        print(f"🔧 Creating column renamer properties for: {node.title}")
        
        # Title (matching DomainNode template)
        title_label = QLabel("🏷️ Column Rename Configuration")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px 0px;")
        layout.addWidget(title_label)
        
        # Info (matching DomainNode template)
        info_label = QLabel("Create mappings to rename columns from original names to SDTM standard names.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; margin: 5px 0px;")
        layout.addWidget(info_label)
        
        # Connection Status (matching DomainNode template)
        available_columns = self.get_available_columns_for_node(node)
        print(f"📊 Available columns for renamer: {available_columns}")
        
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        if available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            status_icon = QLabel("🔗")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel(f"Connected - {len(available_columns)} columns available")
            status_text.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            status_icon = QLabel("⚠️")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel("No input connection detected")
            status_text.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 14px;")
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        status_widget.setStyleSheet("""
            QWidget {
                background: #f0f0f0;
                border: 1px solid #999;
            }
        """)
        layout.addWidget(status_widget)
        
        # Rename mappings group
        mappings_group = QGroupBox("📋 Column Rename Mappings")
        mappings_layout = QVBoxLayout(mappings_group)
        
        # Instructions
        instructions = QLabel("Map original column names to new SDTM standard names:")
        instructions.setStyleSheet("color: #888888; font-style: italic; padding: 5px;")
        mappings_layout.addWidget(instructions)
        
        # Table for rename mappings - Enhanced with cricket scoreboard style matching expression node
        self.rename_table = QTableWidget(0, 3)
        self.rename_table.setHorizontalHeaderLabels(["Original Column", "New Column Name", "Action"])
        
        # Configure column sizing to fit table width proportionally
        header = self.rename_table.horizontalHeader()
        header.setStretchLastSection(False)
        
        # Set proportional column widths using section resize modes
        # Column 0: Original Column - 40% of width (stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Column 1: New Column Name - 40% of width (stretch)  
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Column 2: Action button - Fixed small size
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.rename_table.setColumnWidth(2, 80)
        
        # Set minimum height to fit 10-15 rows comfortably
        row_height = 32  # Match expression node row height
        header_height = 25  # Header height
        min_rows = 10
        max_rows = 15
        min_height = header_height + (row_height * min_rows)
        max_height = header_height + (row_height * max_rows)
        
        self.rename_table.setMinimumHeight(min_height)  # ~345px for 10 rows
        self.rename_table.setMaximumHeight(max_height)  # ~505px for 15 rows
        self.rename_table.setAlternatingRowColors(True)
        self.rename_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rename_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.rename_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set compact row height for cricket scoreboard style matching expression node
        self.rename_table.verticalHeader().setDefaultSectionSize(32)
        self.rename_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.rename_table.setShowGrid(True)
        
        # Apply cricket scoreboard styling matching expression node
        self.rename_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e6e3;
                border: 2px solid #2c5234;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #d4edda;
                selection-color: #155724;
                font-size: 11px;
                font-family: 'Courier New', 'Consolas', monospace;
                outline: none;
                alternate-background-color: #f8fdf9;
            }
            QTableWidget::item {
                padding: 0px;
                border: none;
                border-bottom: 1px solid #e0e6e3;
                border-right: 1px solid #e0e6e3;
                min-height: 32px;
                max-height: 32px;
                color: #2c5234;
                font-weight: 500;
            }
            QTableWidget::item:selected {
                background-color: #d4edda;
                color: #155724;
                font-weight: 600;
            }
            QTableWidget::item:hover {
                background-color: #f0f8f4;
            }
            QTableWidget::item:alternate {
                background-color: #f8fdf9;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5234, stop:1 #1e3a26);
                border: 1px solid #1e3a26;
                border-right: 1px solid #4a6b52;
                color: #ffffff;
                padding: 3px 6px;
                font-weight: 700;
                font-size: 9px;
                text-align: center;
                font-family: 'Arial Black', 'Arial', sans-serif;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                min-height: 18px;
                max-height: 22px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 6px;
                border-left: 2px solid #1e3a26;
            }
            QHeaderView::section:last {
                border-top-right-radius: 6px;
                border-right: 2px solid #1e3a26;
            }
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6b52, stop:1 #2c5234);
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #2c5234;
                border-radius: 5px;
                min-height: 20px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a6b52;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #f8f9fa;
                height: 10px;
                border-radius: 5px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #2c5234;
                border-radius: 5px;
                min-width: 20px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #4a6b52;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Add current mappings
        for old_name, new_name in node.rename_mappings.items():
            self.add_rename_mapping_row(old_name, new_name, available_columns)
            
        mappings_layout.addWidget(self.rename_table)
        
        # Add mapping controls
        controls_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Mapping")
        add_btn.clicked.connect(lambda: self.add_rename_mapping_row("", "", available_columns))
        controls_layout.addWidget(add_btn)
        
        # Quick SDTM suggestions
        if available_columns:
            suggest_btn = QPushButton("💡 Suggest SDTM Names")
            suggest_btn.clicked.connect(lambda: self.suggest_sdtm_names(available_columns))
            controls_layout.addWidget(suggest_btn)
        
        controls_layout.addStretch()
        mappings_layout.addLayout(controls_layout)
        
        layout.addWidget(mappings_group)
        
        # Bulk Suffix Operations (SINGLE INSTANCE)
        suffix_group = QGroupBox("🏷️ Bulk Suffix Operations")
        suffix_layout = QVBoxLayout(suffix_group)
        
        # Suffix instruction
        suffix_instruction = QLabel("Add suffix to multiple columns at once (e.g., '_crf', '_dm', '_ae'):")
        suffix_instruction.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        suffix_layout.addWidget(suffix_instruction)
        
        # Suffix input and controls
        suffix_controls_layout = QHBoxLayout()
        
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Enter suffix (e.g., _crf)")
        self.suffix_input.setMaximumWidth(150)
        suffix_controls_layout.addWidget(QLabel("Suffix:"))
        suffix_controls_layout.addWidget(self.suffix_input)
        
        # Apply suffix button - simplified to just add to table
        apply_suffix_btn = QPushButton("Add Checked to Table")
        apply_suffix_btn.setToolTip("Add checked columns with suffix to the mapping table above")
        apply_suffix_btn.clicked.connect(lambda: self.apply_suffix_to_checked_columns())
        suffix_controls_layout.addWidget(apply_suffix_btn)
        
        suffix_controls_layout.addStretch()
        suffix_layout.addLayout(suffix_controls_layout)
        
        # Column selection with checkboxes - Enhanced scrollable list with search
        columns_selection_layout = QVBoxLayout()
        
        # Instructions for checkbox selection
        checkbox_instruction = QLabel("Select columns to add suffix to:")
        checkbox_instruction.setStyleSheet("color: #666; font-weight: bold; padding: 5px 0px;")
        columns_selection_layout.addWidget(checkbox_instruction)
        
        # Search bar for filtering columns
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Search:")
        self.column_search_input = QLineEdit()
        self.column_search_input.setPlaceholderText("Type to filter columns...")
        self.column_search_input.setMaximumWidth(200)
        self.column_search_input.textChanged.connect(self.filter_column_checkboxes)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.column_search_input)
        search_layout.addStretch()
        columns_selection_layout.addLayout(search_layout)
        
        # Create scrollable area for checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(250)  # Height for approximately 15 items
        scroll_area.setMinimumHeight(200)  # Minimum height
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget to contain checkboxes
        self.checkbox_widget = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_widget)
        self.checkbox_layout.setSpacing(2)  # Compact spacing
        
        # Store checkbox references and original columns
        self.suffix_checkboxes = []
        self.all_available_columns = available_columns.copy() if available_columns else []
        
        # Add checkboxes for each column (SINGLE INSTANCE)
        if available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            for col in available_columns:
                checkbox = QCheckBox(col)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: #333;
                        font-size: 11px;
                        padding: 2px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                    QCheckBox::indicator:unchecked {
                        border: 1px solid #999;
                        background-color: white;
                        border-radius: 3px;
                    }
                    QCheckBox::indicator:checked {
                        border: 1px solid #0078d4;
                        background-color: #0078d4;
                        border-radius: 3px;
                    }
                    QCheckBox::indicator:checked:hover {
                        background-color: #106ebe;
                    }
                    QCheckBox:hover {
                        background-color: #f0f8ff;
                    }
                """)
                self.suffix_checkboxes.append(checkbox)
                self.checkbox_layout.addWidget(checkbox)
        else:
            # No columns available message
            no_cols_label = QLabel("⚠️ No columns available. Connect input data first.")
            no_cols_label.setStyleSheet("color: orange; font-style: italic; padding: 10px;")
            self.checkbox_layout.addWidget(no_cols_label)
        
        self.checkbox_layout.addStretch()  # Push checkboxes to top
        scroll_area.setWidget(self.checkbox_widget)
        columns_selection_layout.addWidget(scroll_area)
        
        # Selection helper buttons
        selection_helpers_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("☑️ Check All")
        select_all_btn.setMaximumWidth(80)
        select_all_btn.setToolTip("Check all columns")
        select_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(True))
        selection_helpers_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("☐ Clear All")
        clear_all_btn.setMaximumWidth(80)
        clear_all_btn.setToolTip("Uncheck all columns")
        clear_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(False))
        selection_helpers_layout.addWidget(clear_all_btn)
        
        selection_helpers_layout.addStretch()
        columns_selection_layout.addLayout(selection_helpers_layout)
        
        suffix_layout.addLayout(columns_selection_layout)
        
        # Example
        suffix_example = QLabel("Example: Search 'AE' → Check AEREL, AESER → Enter '_crf' → Add to Table → Apply & Execute")
        suffix_example.setStyleSheet("color: #888; font-size: 10px; font-style: italic; padding: 5px;")
        suffix_layout.addWidget(suffix_example)
        
        layout.addWidget(suffix_group)
        
        # Apply Configuration Section (SINGLE INSTANCE - matching DomainNode template exactly)
        buttons_group = QGroupBox("🎯 Apply Configuration")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button (matching DomainNode exactly)
        apply_execute_btn = QPushButton("✅ Apply and Execute")
        apply_execute_btn.setToolTip("Apply rename mappings and execute transformation in one step")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_and_execute_renamer(node))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button (matching DomainNode exactly)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.cancel_renamer_changes(node))
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_group)
        
        # Store button references for enabling/disabling
        self.apply_renamer_button = apply_execute_btn
        self.cancel_renamer_button = cancel_btn
        
        # Status/result info
        self.renamer_result_label = QLabel("🔄 Ready to rename columns when mappings are configured")
        self.renamer_result_label.setWordWrap(True)
        self.renamer_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
        layout.addWidget(self.renamer_result_label)
        
        # Add renamer results section (matching DomainNode pattern exactly)
        self.add_renamer_results_section(node, layout)
        
        # Common SDTM mappings reference (SINGLE INSTANCE)
        ref_group = QGroupBox("📖 Common SDTM Mappings")
        ref_layout = QVBoxLayout(ref_group)
        
        ref_text = QTextEdit()
        ref_text.setMaximumHeight(100)
        ref_text.setReadOnly(True)
        ref_text.setText("""Common mappings:
• subject_id → USUBJID
• subject → SUBJID  
• age → AGE
• sex/gender → SEX
• race → RACE
• adverse_event → AETERM
• start_date → AESTDTC""")
        ref_layout.addWidget(ref_text)
        layout.addWidget(ref_group)
        
        # Spacer
        layout.addStretch()
        
        # Add all content to the main content layout
        widget = QWidget()
        widget.setLayout(layout)
        self.content_layout.addWidget(widget)
        
        # Store node reference
        self.current_node = node
        
    def apply_and_execute_renamer(self, node):
        """Apply renamer changes and execute (matching DomainNode pattern)."""
        try:
            # Collect all mappings from the table
            mappings = {}
            for row in range(self.rename_table.rowCount()):
                from_combo = self.rename_table.cellWidget(row, 0)
                to_edit = self.rename_table.cellWidget(row, 1)
                
                if from_combo and to_edit:
                    from_col = from_combo.currentText()
                    to_col = to_edit.text().strip()
                    
                    if from_col and to_col and from_col != "Select column...":
                        mappings[from_col] = to_col
            
            # Update node mappings
            node.rename_mappings = mappings
            print(f"🏷️ RENAMER: Updated mappings: {mappings}")
            
            # Execute the node if we have an execution engine
            if hasattr(self, 'main_window') and self.main_window:
                execution_engine = self.main_window.execution_engine
                if execution_engine:
                    execution_engine.execute_node(node)
                    print(f"🏷️ RENAMER: Node executed successfully")
            
            # Refresh the property panel to show results
            self.create_column_renamer_properties(node)
            
        except Exception as e:
            print(f"❌ RENAMER ERROR: {e}")
            
    def cancel_renamer_changes(self, node):
        """Cancel renamer changes (matching DomainNode pattern)."""
        # Clear any unsaved changes and refresh
        self.create_column_renamer_properties(node)
        
    def add_renamer_results_section(self, node, layout):
        """Add renamer results section (matching DomainNode pattern)."""
        # Execution status and data viewing
        execution_engine = self.get_execution_engine(node)
        output_data = None
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
        
        # Results group
        results_group = QGroupBox("📊 Results")
        results_layout = QVBoxLayout(results_group)
        
        if output_data is not None:
            status_label = QLabel("✅ Node has been executed")
            status_label.setStyleSheet("color: green; font-weight: bold;")
            results_layout.addWidget(status_label)
            
            info_label = QLabel(f"Output: {len(output_data)} rows, {len(output_data.columns)} columns")
            results_layout.addWidget(info_label)
            
            # View executed data button
            view_btn = QPushButton("👁️ View Transformed Data")
            view_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Transformed Data"))
            results_layout.addWidget(view_btn)
        else:
            status_label = QLabel("⏳ Node not executed yet")
            status_label.setStyleSheet("color: orange;")
            results_layout.addWidget(status_label)
            
            help_label = QLabel("Click 'Apply & Execute' to process data")
            help_label.setStyleSheet("color: #888888; font-style: italic;")
            results_layout.addWidget(help_label)
        
        layout.addWidget(results_group)
        
    def get_available_columns_for_node(self, node):
        """Get available columns from connected input nodes."""
        available_columns = []
        
        try:
            # Get the canvas from multiple sources
            canvas = None
            
            # Method 1: Direct canvas reference on node
            if hasattr(node, 'canvas') and node.canvas:
                canvas = node.canvas
                print(f"🎯 Found canvas via node.canvas")
            
            # Method 2: Through node's scene
            elif node.scene():
                scene = node.scene()
                if hasattr(scene, 'parent') and hasattr(scene.parent(), 'connections'):
                    canvas = scene.parent()
                    print(f"🎯 Found canvas via scene.parent()")
                elif hasattr(scene, 'views') and scene.views():
                    # Try to get canvas from the view
                    view = scene.views()[0]
                    if hasattr(view, 'parent') and hasattr(view.parent(), 'connections'):
                        canvas = view.parent()
                        print(f"🎯 Found canvas via view.parent()")
            
            # Method 3: Use the property panel's stored canvas reference
            if not canvas and hasattr(self, '_canvas_ref') and self._canvas_ref:
                canvas = self._canvas_ref
                print(f"🎯 Found canvas via property panel reference")
            
            if canvas and hasattr(canvas, 'connections'):
                print(f"🔍 Checking {len(canvas.connections)} connections for node {node.title}")
                
                # Find connections that feed into this node
                for i, connection in enumerate(canvas.connections):
                    print(f"  Connection {i}: {connection.start_port.parent_node.get_display_name()} → {connection.end_port.parent_node.get_display_name()}")
                    
                    # Check if this connection's end port belongs to our node
                    if (hasattr(connection, 'end_port') and 
                        hasattr(connection.end_port, 'parent_node') and
                        connection.end_port.parent_node == node):
                        
                        print(f"  ✅ Found input connection from {connection.start_port.parent_node.get_display_name()}")
                        
                        # Get the source node from the start port
                        source_node = connection.start_port.parent_node
                        
                        # Get columns from source node's data
                        if hasattr(source_node, 'dataframe') and source_node.dataframe is not None:
                            columns = source_node.dataframe.columns.tolist()
                            available_columns.extend(columns)
                            print(f"  📊 Added {len(columns)} columns from source node data")
                        
                        # Also check if source node has executed output
                        execution_engine = self.get_execution_engine(source_node)
                        if execution_engine:
                            output_data = execution_engine.get_node_output_data(source_node)
                            if output_data is not None:
                                exec_columns = output_data.columns.tolist()
                                available_columns.extend(exec_columns)
                                print(f"  🚀 Added {len(exec_columns)} columns from executed output")
            else:
                print(f"❌ No canvas found or canvas has no connections")
                if not canvas:
                    print(f"   Node: {node.title}, has canvas attr: {hasattr(node, 'canvas')}")
                    if hasattr(node, 'canvas'):
                        print(f"   Canvas value: {node.canvas}")
            
            # Remove duplicates while preserving order
            available_columns = list(dict.fromkeys(available_columns))
            
            # If no columns found from connections, show helpful message
            if not available_columns:
                available_columns = ["⚠️ Connect input data to see available columns"]
                print(f"⚠️ No columns found for node {node.title}")
            else:
                print(f"✅ Found {len(available_columns)} unique columns for node {node.title}")
                
        except Exception as e:
            print(f"❌ Error getting available columns: {e}")
            import traceback
            traceback.print_exc()
            available_columns = ["❌ Error: Connect input data first"]
            
        return available_columns
        
    def add_rename_mapping_row(self, old_name="", new_name="", available_columns=None):
        """Add a new rename mapping row with dropdowns."""
        if available_columns is None:
            available_columns = []
            
        row = self.rename_table.rowCount()
        self.rename_table.insertRow(row)
        
        # Original column dropdown - Pure dropdown for easy selection
        old_combo = CustomSizedComboBox()
        old_combo.setEditable(False)  # Make it a pure dropdown, not editable
        
        # Add placeholder and columns
        dropdown_items = ["Select column..."] + available_columns
        old_combo.addItems(dropdown_items)
        
        # Set current selection if provided
        if old_name and old_name in available_columns:
            old_combo.setCurrentText(old_name)
        else:
            old_combo.setCurrentIndex(0)  # Show placeholder
            
        old_combo.currentTextChanged.connect(self.on_rename_mapping_changed)
        
        # Enhanced styling for better dropdown experience
        old_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 8px;
                border: 2px solid #2c5234;
                border-radius: 6px;
                background: white;
                min-height: 24px;
                font-size: 12px;
                font-family: 'Segoe UI', 'Tahoma', Arial, sans-serif;
                font-weight: 500;
                color: #2c5234;
                selection-background-color: #d4edda;
            }
            QComboBox:focus {
                border-color: #1e3a26;
                background: #f8fdf9;
            }
            QComboBox:hover {
                border-color: #4a6b52;
                background: #f0f8f4;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5234, stop:1 #1e3a26);
                border-radius: 4px;
                margin: 2px;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 4px 4px 0px 4px;
                border-color: white transparent transparent transparent;
                width: 0px;
                height: 0px;
                margin: 2px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #f0f8f4;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 2px solid #2c5234;
                border-radius: 6px;
                selection-background-color: #d4edda;
                selection-color: #155724;
                outline: none;
                font-size: 12px;
                font-family: 'Segoe UI', 'Tahoma', Arial, sans-serif;
                font-weight: 500;
                color: #2c5234;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                color: #2c5234;
                background: white;
                min-height: 24px;
                border-bottom: 1px solid #e0e6e3;
            }
            QComboBox QAbstractItemView::item:first {
                color: #888;
                font-style: italic;
                background: #f8f9fa;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #d4edda;
                color: #155724;
                font-weight: 600;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f8f4;
                color: #2c5234;
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 12px;
                border: none;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #2c5234;
                border-radius: 6px;
                min-height: 20px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a6b52;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        self.rename_table.setCellWidget(row, 0, old_combo)
        
        # New column name input with validation
        new_edit = QLineEdit(new_name)
        new_edit.setPlaceholderText("Enter SDTM name...")
        
        # Add validation on text change
        def validate_rename_column():
            """Validate the renamed column name in real-time."""
            column_name = new_edit.text().strip()
            if column_name:
                is_valid, error_msg = self.validate_column_name(column_name, self.current_node, row)
                if not is_valid:
                    # Show error styling
                    new_edit.setStyleSheet("""
                        QLineEdit {
                            border: 2px solid #d73502;
                            border-radius: 3px;
                            padding: 4px 6px;
                            background: #ffeaa7;
                            font-size: 14px;
                            font-family: 'Segoe UI', Arial, sans-serif;
                            font-weight: 500;
                            color: #d73502;
                        }
                    """)
                    new_edit.setToolTip(error_msg)
                else:
                    # Show normal styling
                    new_edit.setStyleSheet("""
                        QLineEdit {
                            padding: 4px 6px;
                            border: 1px solid #ccc;
                            border-radius: 3px;
                            background: white;
                            font-size: 14px;
                            color: black;
                        }
                        QLineEdit:focus {
                            border-color: #0078d4;
                        }
                    """)
                    new_edit.setToolTip("")
        
        new_edit.textChanged.connect(validate_rename_column)
        new_edit.textChanged.connect(self.on_rename_mapping_changed)
        self.rename_table.setCellWidget(row, 1, new_edit)
        
        # Remove button
        remove_btn = QPushButton("🗑️")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_rename_mapping_row(row))
        self.rename_table.setCellWidget(row, 2, remove_btn)
        
    def remove_rename_mapping_row(self, row):
        """Remove a rename mapping row."""
        self.rename_table.removeRow(row)
        self.on_rename_mapping_changed()
        
    def suggest_sdtm_names(self, available_columns):
        """Suggest SDTM names for common columns."""
        suggestions = {
            'subject_id': 'USUBJID',
            'subject': 'SUBJID', 
            'age': 'AGE',
            'sex': 'SEX',
            'gender': 'SEX',
            'race': 'RACE',
            'adverse_event': 'AETERM',
            'ae_term': 'AETERM',
            'start_date': 'AESTDTC',
            'end_date': 'AEENDTC',
            'severity': 'AESEV'
        }
        
        # Clear existing mappings
        self.rename_table.setRowCount(0)
        
        # Add suggested mappings
        for col in available_columns:
            col_lower = col.lower().replace('_', '').replace(' ', '')
            for key, value in suggestions.items():
                if key.replace('_', '') in col_lower:
                    self.add_rename_mapping_row(col, value, available_columns)
                    break
    
    def filter_column_checkboxes(self):
        """Filter checkbox list based on search input."""
        if not hasattr(self, 'column_search_input') or not hasattr(self, 'suffix_checkboxes'):
            return
            
        search_text = self.column_search_input.text().lower().strip()
        
        # Show/hide checkboxes based on search
        for checkbox in self.suffix_checkboxes:
            column_name = checkbox.text().lower()
            if search_text == "" or search_text in column_name:
                checkbox.show()
            else:
                checkbox.hide()
    
    def apply_suffix_to_checked_columns(self, node=None):
        """Apply suffix to checked columns and add to mappings table (preserving checkbox states)."""
        if not hasattr(self, 'suffix_input') or not hasattr(self, 'suffix_checkboxes'):
            print("⚠️ Suffix controls not available")
            return
            
        # Use the node parameter or fall back to current_node
        if node is None:
            node = getattr(self, 'current_node', None)
            
        suffix = self.suffix_input.text().strip()
        
        if not suffix:
            QMessageBox.warning(self, "No Suffix", "Please enter a suffix to add.")
            return
            
        # Get checked columns
        checked_columns = []
        for checkbox in self.suffix_checkboxes:
            if checkbox.isChecked():
                checked_columns.append(checkbox.text())
        
        if not checked_columns:
            QMessageBox.warning(self, "No Columns Selected", 
                              "Please check at least one column to add the suffix to.")
            return
            
        print(f"🔧 Adding suffix '{suffix}' to {len(checked_columns)} checked columns: {checked_columns}")
        
        # Add mapping rows for checked columns to the table above
        available_columns = self.get_available_columns_for_node(self.current_node)
        for column in checked_columns:
            new_name = f"{column}{suffix}"
            print(f"   📝 Mapping: {column} → {new_name}")
            self.add_rename_mapping_row(column, new_name, available_columns)
        
        # Update node mappings immediately
        self.on_rename_mapping_changed()
        
        # Clear suffix input but PRESERVE checkbox states for further operations
        self.suffix_input.clear()
        # REMOVED: self.toggle_all_checkboxes(False)  # This was causing checkbox states to be lost
        
        # Keep search filter active - don't clear it
        # REMOVED: Clear search filter
        
        QMessageBox.information(self, "Mappings Added", 
                              f"Added {len(checked_columns)} column mappings to the table above.\n\n" +
                              "Checkbox selections preserved for additional suffix operations.\n" +
                              "Click 'Apply and Execute' to run the transformation.")
    
    def apply_checked_columns_and_execute(self):
        """Apply suffix to checked columns and immediately execute transformation (preserving workflow)."""
        if not hasattr(self, 'suffix_input') or not hasattr(self, 'suffix_checkboxes'):
            print("⚠️ Suffix controls not available")
            return
            
        suffix = self.suffix_input.text().strip()
        
        if not suffix:
            QMessageBox.warning(self, "No Suffix", "Please enter a suffix to add.")
            return
            
        # Get checked columns
        checked_columns = []
        for checkbox in self.suffix_checkboxes:
            if checkbox.isChecked():
                checked_columns.append(checkbox.text())
        
        if not checked_columns:
            QMessageBox.warning(self, "No Columns Selected", 
                              "Please check at least one column to add the suffix to.")
            return
            
        print(f"🚀 EXECUTE: Adding suffix '{suffix}' and executing for {len(checked_columns)} columns")
        
        # Add mapping rows for checked columns to existing table (don't clear existing)
        available_columns = self.get_available_columns_for_node(self.current_node)
        for column in checked_columns:
            new_name = f"{column}{suffix}"
            print(f"   📝 Mapping: {column} → {new_name}")
            self.add_rename_mapping_row(column, new_name, available_columns)
        
        # Update node mappings
        self.on_rename_mapping_changed()
        
        # Clear suffix input but preserve checkbox states for additional operations
        self.suffix_input.clear()
        # REMOVED: self.toggle_all_checkboxes(False)  # Preserve checkbox states
        
        # Execute the transformation immediately using standardized method
        print(f"🔄 Executing transformation with checked column mappings")
        self.apply_and_execute_renamer(self.current_node)
    
    def toggle_all_checkboxes(self, checked_state):
        """Check or uncheck all column checkboxes."""
        if hasattr(self, 'suffix_checkboxes'):
            for checkbox in self.suffix_checkboxes:
                checkbox.setChecked(checked_state)
        
    def apply_suffix_to_column(self):
        """Apply suffix to selected column."""
        if not hasattr(self, 'suffix_input') or not hasattr(self, 'suffix_columns_combo'):
            return
            
        suffix = self.suffix_input.text().strip()
        selected_column = self.suffix_columns_combo.currentText()
        
        if not suffix:
            QMessageBox.warning(self, "No Suffix", "Please enter a suffix to add.")
            return
            
        if selected_column == "Select columns to add suffix..." or not selected_column:
            QMessageBox.warning(self, "No Column Selected", "Please select a column to add the suffix to.")
            return
            
        # Add mapping row with suffix
        new_name = f"{selected_column}{suffix}"
        self.add_rename_mapping_row(selected_column, new_name, self.get_available_columns_for_node(self.current_node))
        
        # Clear suffix input for next use
        self.suffix_input.clear()
        
        QMessageBox.information(self, "Suffix Added", f"Added mapping: {selected_column} → {new_name}")
    
    def apply_suffix_to_all_columns(self, available_columns):
        """Apply suffix to all available columns."""
        if not hasattr(self, 'suffix_input'):
            return
            
        suffix = self.suffix_input.text().strip()
        
        if not suffix:
            QMessageBox.warning(self, "No Suffix", "Please enter a suffix to add.")
            return
            
        if not available_columns or available_columns[0] in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            QMessageBox.warning(self, "No Columns", "No columns available. Please connect input data first.")
            return
            
        # Confirm bulk operation
        reply = QMessageBox.question(self, "Bulk Suffix Operation", 
                                   f"Add suffix '{suffix}' to all {len(available_columns)} columns?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear existing mappings
            self.rename_table.setRowCount(0)
            
            # Add suffix to all columns
            for column in available_columns:
                new_name = f"{column}{suffix}"
                self.add_rename_mapping_row(column, new_name, available_columns)
            
            # Clear suffix input
            self.suffix_input.clear()
            
            QMessageBox.information(self, "Bulk Suffix Applied", 
                                  f"Added suffix '{suffix}' to all {len(available_columns)} columns.")
        
        
    def on_rename_mapping_changed(self):
        """Update node when rename mappings change."""
        if not self.current_node:
            return
        
        # Mark that changes have been made
        self.mark_changes_made()
            
        # Collect all mappings from table
        mappings = {}
        for row in range(self.rename_table.rowCount()):
            old_widget = self.rename_table.cellWidget(row, 0)
            new_widget = self.rename_table.cellWidget(row, 1)
            
            if old_widget and new_widget:
                old_name = old_widget.currentText() if hasattr(old_widget, 'currentText') else old_widget.text()
                new_name = new_widget.text()
                
                # Skip placeholder text and empty values
                if (old_name and new_name and 
                    old_name != "Select column..." and 
                    old_name.strip() != "" and 
                    new_name.strip() != ""):
                    mappings[old_name] = new_name
        
        # Update node
        self.current_node.rename_mappings = mappings
        
        # Trigger callback if available
        if self.update_callback:
            self.update_callback(self.current_node)
        
    def on_rename_mapping_changed(self):
        """Handle rename mapping changes."""
        if not self.current_node:
            return
            
        # Update node mappings
        mappings = {}
        for row in range(self.rename_table.rowCount()):
            old_item = self.rename_table.item(row, 0)
            new_item = self.rename_table.item(row, 1)
            
            if old_item and new_item and old_item.text() and new_item.text():
                mappings[old_item.text()] = new_item.text()
                
        self.current_node.rename_mappings = mappings
        self.property_changed.emit("rename_mappings", mappings)
        
    def create_expression_builder_properties(self, node):
        """Create properties for expression builder nodes with simplified expression list."""
        
        # Title
        title_label = QLabel("🧮 Expression Builder Configuration")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px 0px;")
        self.content_layout.addWidget(title_label)
        
        # Connection Status (matching renamer node template)
        available_columns = self.get_available_columns_for_node(node)
        print(f"📊 Available columns for expression builder: {available_columns}")
        
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        if available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            status_icon = QLabel("🔗")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel(f"Connected - {len(available_columns)} columns available")
            status_text.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            status_icon = QLabel("⚠️")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel("No input connection detected")
            status_text.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 14px;")
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        status_widget.setStyleSheet("""
            QWidget {
                background: #f0f0f0;
                border: 1px solid #999;
                border-radius: 4px;
            }
        """)
        self.content_layout.addWidget(status_widget)

        # Single expressions group (simplified)
        expressions_group = QGroupBox("Expressions")
        expressions_layout = QVBoxLayout(expressions_group)
        
        # Expressions table with cricket scoreboard style
        self.expressions_table = QTableWidget(0, 6)
        self.expressions_table.setHorizontalHeaderLabels(["Select Column", "FUNC", "PARAMS", "MODE", "New Column Name", "DEL"])
        
        # Configure column sizing to fit table width proportionally
        header = self.expressions_table.horizontalHeader()
        header.setStretchLastSection(False)
        
        # Set proportional column widths using section resize modes
        # Column 0: Select Column - 25% of width
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Column 1: Function - Fixed reasonable size
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.expressions_table.setColumnWidth(1, 80)
        
        # Column 2: Parameters - 20% of width  
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # Column 3: Mode - Fixed reasonable size
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.expressions_table.setColumnWidth(3, 70)
        
        # Column 4: New Column Name - 25% of width
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Column 5: Delete button - Fixed small size
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.expressions_table.setColumnWidth(5, 50)
        
        # Set same height as renamer table for consistency
        row_height = 32  # Match renamer node row height
        header_height = 25  # Header height
        min_rows = 10
        max_rows = 15
        min_height = header_height + (row_height * min_rows)
        max_height = header_height + (row_height * max_rows)
        
        self.expressions_table.setMinimumHeight(min_height)  # ~345px for 10 rows
        self.expressions_table.setMaximumHeight(max_height)  # ~505px for 15 rows
        self.expressions_table.setAlternatingRowColors(True)
        self.expressions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.expressions_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.expressions_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set compact row height for cricket scoreboard style
        self.expressions_table.verticalHeader().setDefaultSectionSize(32)
        self.expressions_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.expressions_table.setShowGrid(True)
        
        # Set consistent column widths
        header = self.expressions_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(120)
        
        self.expressions_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e6e3;
                border: 2px solid #2c5234;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #d4edda;
                selection-color: #155724;
                font-size: 11px;
                font-family: 'Courier New', 'Consolas', monospace;
                outline: none;
                alternate-background-color: #f8fdf9;
            }
            QTableWidget::item {
                padding: 0px;
                border: none;
                border-bottom: 1px solid #e0e6e3;
                border-right: 1px solid #e0e6e3;
                min-height: 32px;
                max-height: 32px;
                color: #2c5234;
                font-weight: 500;
            }
            QTableWidget::item:selected {
                background-color: #d4edda;
                color: #155724;
                font-weight: 600;
            }
            QTableWidget::item:hover {
                background-color: #f0f8f4;
            }
            QTableWidget::item:alternate {
                background-color: #f8fdf9;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5234, stop:1 #1e3a26);
                border: 1px solid #1e3a26;
                border-right: 1px solid #4a6b52;
                color: #ffffff;
                padding: 3px 6px;
                font-weight: 700;
                font-size: 9px;
                text-align: center;
                font-family: 'Arial Black', 'Arial', sans-serif;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                min-height: 18px;
                max-height: 22px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 6px;
                border-left: 2px solid #1e3a26;
            }
            QHeaderView::section:last {
                border-top-right-radius: 6px;
                border-right: 2px solid #1e3a26;
            }
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6b52, stop:1 #2c5234);
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #2c5234;
                border-radius: 5px;
                min-height: 20px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a6b52;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #f8f9fa;
                height: 10px;
                border-radius: 5px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #2c5234;
                border-radius: 5px;
                min-width: 20px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #4a6b52;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        expressions_layout.addWidget(self.expressions_table)
        
        # Add Expression button with modern styling
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 5)
        
        add_expression_btn = QPushButton("➕ Add Expression")
        add_expression_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #20a83a);
                color: white;
                font-weight: 600;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 6px 12px;
                border: none;
                border-radius: 5px;
                min-width: 100px;
                min-height: 28px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1e7e34);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #1c7430);
                padding: 9px 15px 7px 17px;
            }
        """)
        add_expression_btn.clicked.connect(self.add_expression_row)
        controls_layout.addWidget(add_expression_btn)
        controls_layout.addStretch()  # Push expand button to the right
        
        # Expand/Collapse button (KNIME-style on the right)
        self.expand_btn = QPushButton("⇲ Expand")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5234, stop:1 #1e3a26);
                color: white;
                font-weight: 600;
                font-size: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                min-width: 80px;
                min-height: 28px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6b52, stop:1 #2c5234);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3a26, stop:1 #152d1e);
            }
        """)
        self.expand_btn.clicked.connect(lambda: self.toggle_expression_table_view(node))
        controls_layout.addWidget(self.expand_btn)
        
        expressions_layout.addLayout(controls_layout)
        self.content_layout.addWidget(expressions_group)
        
        # Store references 
        self.expressions_group = expressions_group
        
        # Force proper sizing after table is fully configured
        self.setMinimumWidth(600)  # Ensure width is set after table creation
        # Note: Column sizing is now handled by resize modes set above (stretch, fixed, etc.)
        
        # Force a layout update to apply sizing immediately
        self.updateGeometry()
        self.update()

        # Action buttons group (same style as Row Filter)
        buttons_group = QGroupBox("🚀 Actions")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button
        apply_btn = QPushButton("✅ Apply and Execute")
        apply_btn.setToolTip("Apply expressions and execute transformation in one step")
        apply_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_btn.clicked.connect(lambda: self.apply_properties(node))
        buttons_layout.addWidget(apply_btn)
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.cancel_changes(node))
        buttons_layout.addWidget(cancel_btn)
        
        self.content_layout.addWidget(buttons_group)

        # Check if node has been executed and show result (same pattern as Row Filter)
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
            if output_data is not None:
                result_group = QGroupBox("✨ Expression Results")
                result_group.setStyleSheet("""
                    QGroupBox {
                        color: #27ae60;
                        border: 1px solid #999;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 2px;
                    }
                """)
                result_layout = QVBoxLayout(result_group)
                
                result_info = QLabel(f"✅ Expressions applied: {len(output_data)} rows processed")
                result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                result_layout.addWidget(result_info)
                
                # View transformed data button
                view_btn = QPushButton("👁️ View Transformed Data")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 5px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Transformed Data"))
                result_layout.addWidget(view_btn)
                
                self.content_layout.addWidget(result_group)
        
        # Populate columns for expressions
        self.populate_expression_builder_columns(node)
        
    def populate_expression_builder_columns(self, node):
        """Populate column dropdowns with input data and any previously created columns."""
        # Get available columns from input data
        execution_engine = self.get_execution_engine(node)
        available_columns = []
        
        if execution_engine:
            try:
                # ALWAYS get fresh input data based on current connections first
                input_data = execution_engine.get_node_input_data(node)
                if input_data is not None and not input_data.empty:
                    available_columns = input_data.columns.tolist()
                    print(f"✅ PROPERTY PANEL: Using fresh input data with {len(available_columns)} columns from connected nodes")
                else:
                    # Only fallback to output data if no input connections exist
                    output_data = execution_engine.get_node_output_data(node)
                    if output_data is not None and not output_data.empty:
                        available_columns = output_data.columns.tolist()
                        print(f"⚠️ PROPERTY PANEL: No input data, using cached output data with {len(available_columns)} columns")
                    else:
                        print("⚠️ PROPERTY PANEL: No input or output data available for expression builder")
            except Exception as e:
                print(f"⚠️ PROPERTY PANEL: Error getting data: {e}")
        
        # Store available columns for use in add_expression_row
        self.available_columns = available_columns
        
        # Load existing expressions if node has them
        if hasattr(node, 'expressions') and node.expressions:
            for expr in node.expressions:
                self.add_expression_row(expr)
        else:
            # Add one empty row to start
            self.add_expression_row()
            
        # Refresh existing column dropdowns AFTER rows are created
        if hasattr(self, 'expressions_table') and self.expressions_table.rowCount() > 0:
            self.refresh_existing_column_dropdowns()
    
    def refresh_existing_column_dropdowns(self):
        """Refresh all existing column dropdowns with updated column list while preserving ALL selections."""
        if not hasattr(self, 'expressions_table') or not hasattr(self, 'available_columns'):
            print("⚠️ Cannot refresh dropdowns - missing table or columns")
            return
            
        print(f"🔄 Starting comprehensive dropdown refresh for {self.expressions_table.rowCount()} rows with {len(self.available_columns)} columns")
        
        # Store all current selections before refresh
        current_selections = []
        for row in range(self.expressions_table.rowCount()):
            column_combo = self.expressions_table.cellWidget(row, 0)
            function_combo = self.expressions_table.cellWidget(row, 1)
            params_edit = self.expressions_table.cellWidget(row, 2)
            mode_combo = self.expressions_table.cellWidget(row, 3)
            new_col_edit = self.expressions_table.cellWidget(row, 4)
            
            selection = {
                'column': column_combo.currentText() if column_combo else "",
                'function': function_combo.currentText() if function_combo else "",
                'params': params_edit.text() if params_edit else "",
                'mode': mode_combo.currentText() if mode_combo else "",
                'new_column': new_col_edit.text() if new_col_edit else ""
            }
            current_selections.append(selection)
            print(f"  Row {row}: Stored selections - Column: '{selection['column']}', Function: '{selection['function']}', Mode: '{selection['mode']}', New Column: '{selection['new_column']}'")
            
        # Only refresh column dropdowns (other dropdowns don't need refreshing)
        for row in range(self.expressions_table.rowCount()):
            column_combo = self.expressions_table.cellWidget(row, 0)
            if column_combo and row < len(current_selections):
                current_selection = current_selections[row]
                
                # Clear and repopulate column dropdown
                column_combo.clear()
                column_combo.addItem("Select column...")
                if self.available_columns:
                    column_combo.addItems(self.available_columns)
                
                # Restore column selection
                index = column_combo.findText(current_selection['column'])
                if index >= 0:
                    column_combo.setCurrentIndex(index)
                    print(f"  Row {row}: Restored column selection to '{current_selection['column']}'")
                
                # Restore function selection
                function_combo = self.expressions_table.cellWidget(row, 1)
                if function_combo and current_selection['function']:
                    func_index = function_combo.findText(current_selection['function'])
                    if func_index >= 0:
                        function_combo.setCurrentIndex(func_index)
                        print(f"  Row {row}: Restored function selection to '{current_selection['function']}'")
                
                # Restore mode selection
                mode_combo = self.expressions_table.cellWidget(row, 3)
                if mode_combo and current_selection['mode']:
                    mode_index = mode_combo.findText(current_selection['mode'])
                    if mode_index >= 0:
                        mode_combo.setCurrentIndex(mode_index)
                        print(f"  Row {row}: Restored mode selection to '{current_selection['mode']}'")
                
                # Restore parameters
                params_edit = self.expressions_table.cellWidget(row, 2)
                if params_edit and current_selection['params']:
                    params_edit.setText(current_selection['params'])
                    print(f"  Row {row}: Restored params to '{current_selection['params']}'")
                
                # Restore new column name
                new_col_edit = self.expressions_table.cellWidget(row, 4)
                if new_col_edit and current_selection['new_column']:
                    new_col_edit.setText(current_selection['new_column'])
                    print(f"  Row {row}: Restored new column to '{current_selection['new_column']}'")
                    
        print(f"✅ Refreshed {self.expressions_table.rowCount()} rows with all selections preserved")
    
    def add_expression_row(self, expression_data=None):
        """Add a new row to the expressions table."""
        if not hasattr(self, 'expressions_table'):
            return
        row = self.expressions_table.rowCount()
        self.expressions_table.insertRow(row)
        
        # Column combo with cricket scoreboard styling
        column_combo = CustomSizedComboBox()
        column_combo.setMaxVisibleItems(15)
        column_combo.setMinimumHeight(28)
        column_combo.setMaximumHeight(28)
        column_combo.addItem("Select column...")
        if hasattr(self, 'available_columns'):
            column_combo.addItems(self.available_columns)
        column_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
        """)
        column_combo.currentTextChanged.connect(self.mark_changes_made)
        self.expressions_table.setCellWidget(row, 0, column_combo)
        
        # Function combo with cricket scoreboard styling
        function_combo = CustomSizedComboBox()
        function_combo.setMaxVisibleItems(15)
        function_combo.setMinimumHeight(28)
        function_combo.setMaximumHeight(28)
        # Comprehensive SDTM transformation functions
        functions = [
            # String Cleaning & Basic
            "strip", "upper", "lower", "trim", "compress", "left", "right",
            # String Manipulation
            "substr", "scan", "catx", "length", "reverse", "pad_start", "pad_end",
            # Parsing & Conversion
            "parse_int", "parse_float", "parse_date", "to_string", "to_numeric",
            # Regex Operations
            "regex_extract", "regex_replace", "regex_match", "regex_split",
            # String Operations
            "string_extract", "string_replace", "string_contains", "string_startswith", "string_endswith",
            # Math & Aggregation
            "sum", "mean", "median", "min", "max", "count", "std", "round", "abs", "ceil", "floor",
            # Date Functions
            "date_format", "date_parse", "date_diff", "date_add", "year", "month", "day",
            # Conditional
            "if_then_else", "coalesce", "nullif", "case_when",
            # SDTM Specific
            "domain_split", "visit_mapping", "ae_coding", "cm_mapping", "lb_standardize",
            # Advanced
            "custom"
        ]
        # Add default option first
        function_combo.addItem("Select function...", None)
        # Add functions with proper data values
        for func in functions:
            function_combo.addItem(func, func)  # text, data
        # Set default to "strip" for immediate usability
        strip_index = function_combo.findText("strip")
        if strip_index != -1:
            function_combo.setCurrentIndex(strip_index)
        function_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
        """)
        function_combo.currentTextChanged.connect(self.mark_changes_made)
        self.expressions_table.setCellWidget(row, 1, function_combo)
        
        # Parameters input with cricket scoreboard styling
        params_input = QLineEdit()
        params_input.setMinimumHeight(28)
        params_input.setMaximumHeight(28)
        params_input.setPlaceholderText("Enter parameters...")
        params_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #2c5234;
                border-radius: 3px;
                padding: 4px 6px;
                background: white;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                height: 26px;
                min-height: 26px;
                max-height: 26px;
                color: #2c5234;
            }
            QLineEdit:focus {
                border-color: #4a6b52;
                background: #f8fdf9;
            }
            QLineEdit::placeholder {
                color: #6c7b6e;
                font-style: italic;
            }
        """)
        params_input.textChanged.connect(self.mark_changes_made)
        self.expressions_table.setCellWidget(row, 2, params_input)
        
        # Mode combo with cricket scoreboard styling
        mode_combo = CustomSizedComboBox()
        mode_combo.setMinimumHeight(28)
        mode_combo.setMaximumHeight(28)
        # Add mode options (text only for consistency)
        mode_combo.addItems(["Replace", "Append"])
        # Set default to "Append" for SDTM workflows (more common) only for new expressions
        if expression_data is None:
            append_index = mode_combo.findText("Append")
            if append_index != -1:
                mode_combo.setCurrentIndex(append_index)
        mode_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
        """)
        mode_combo.currentTextChanged.connect(self.mark_changes_made)
        self.expressions_table.setCellWidget(row, 3, mode_combo)
        
        # New column input with cricket scoreboard styling and validation
        new_col_input = QLineEdit()
        new_col_input.setMinimumHeight(28)
        new_col_input.setMaximumHeight(28)
        new_col_input.setPlaceholderText("New column name...")
        
        # Add validation on text change
        def validate_new_column():
            """Validate the new column name in real-time."""
            column_name = new_col_input.text().strip()
            if column_name:
                is_valid, error_msg = self.validate_column_name(column_name, self.current_node, row)
                if not is_valid:
                    # Show error styling
                    new_col_input.setStyleSheet("""
                        QLineEdit {
                            border: 2px solid #d73502;
                            border-radius: 3px;
                            padding: 4px 6px;
                            background: #ffeaa7;
                            font-size: 14px;
                            font-family: 'Segoe UI', Arial, sans-serif;
                            font-weight: 500;
                            height: 26px;
                            min-height: 26px;
                            max-height: 26px;
                            color: #d73502;
                        }
                    """)
                    new_col_input.setToolTip(error_msg)
                else:
                    # Show normal styling
                    new_col_input.setStyleSheet("""
                        QLineEdit {
                            border: 1px solid #2c5234;
                            border-radius: 3px;
                            padding: 4px 6px;
                            background: white;
                            font-size: 14px;
                            font-family: 'Segoe UI', Arial, sans-serif;
                            font-weight: 500;
                            height: 26px;
                            min-height: 26px;
                            max-height: 26px;
                            color: #2c5234;
                        }
                        QLineEdit:focus {
                            border-color: #4a6b52;
                            background: #f8fdf9;
                        }
                        QLineEdit::placeholder {
                            color: #6c7b6e;
                            font-style: italic;
                        }
                    """)
                    new_col_input.setToolTip("")
        
        new_col_input.textChanged.connect(validate_new_column)
        new_col_input.textChanged.connect(self.mark_changes_made)
        
        new_col_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #2c5234;
                border-radius: 3px;
                padding: 4px 6px;
                background: white;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                height: 26px;
                min-height: 26px;
                max-height: 26px;
                color: #2c5234;
            }
            QLineEdit:focus {
                border-color: #4a6b52;
                background: #f8fdf9;
            }
            QLineEdit::placeholder {
                color: #6c7b6e;
                font-style: italic;
            }
        """)
        self.expressions_table.setCellWidget(row, 4, new_col_input)
        
        # Remove button with cricket scoreboard styling
        remove_btn = QPushButton("×")
        remove_btn.setMaximumWidth(30)
        remove_btn.setMinimumHeight(28)
        remove_btn.setMaximumHeight(28)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d73502, stop:1 #b82d02);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #b82d02;
                border-radius: 3px;
                padding: 2px;
                height: 26px;
                min-height: 26px;
                max-height: 26px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c02, stop:1 #d73502);
                border-color: #d73502;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #b82d02, stop:1 #9e2502);
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_expression_row(row))
        self.expressions_table.setCellWidget(row, 5, remove_btn)
        
        # Load expression data if provided
        if expression_data:
            if 'column' in expression_data:
                index = column_combo.findText(expression_data['column'])
                if index >= 0:
                    column_combo.setCurrentIndex(index)
            if 'function' in expression_data:
                index = function_combo.findText(expression_data['function'])
                if index >= 0:
                    function_combo.setCurrentIndex(index)
            if 'parameters' in expression_data:
                params_input.setText(expression_data['parameters'])
            if 'mode' in expression_data:
                index = mode_combo.findText(expression_data['mode'])
                if index >= 0:
                    mode_combo.setCurrentIndex(index)
            if 'new_column' in expression_data:
                new_col_input.setText(expression_data['new_column'])

    def remove_expression_row(self, row):
        """Remove a row from the expressions table."""
        if hasattr(self, 'expressions_table') and row < self.expressions_table.rowCount():
            self.expressions_table.removeRow(row)
        if execution_engine:
            try:
                # Get input data for the current node
                input_data = execution_engine.get_node_input_data(node)
                if input_data is not None and not input_data.empty:
                    self.target_column_combo.addItems(input_data.columns.tolist())
                    print(f"✅ PROPERTY PANEL: Loaded {len(input_data.columns)} columns for expression builder")
                else:
                    print("⚠️ PROPERTY PANEL: No input data available for expression builder")
            except Exception as e:
                print(f"⚠️ PROPERTY PANEL: Error getting input data: {e}")
        
        # Set current value
        if hasattr(node, 'target_column') and node.target_column:
            index = self.target_column_combo.findText(node.target_column)
            if index >= 0:
                self.target_column_combo.setCurrentIndex(index)
        
        self.target_column_combo.currentTextChanged.connect(
            lambda text: self.update_node_property('target_column', text if text != "Select column..." else "")
        )
        target_layout.addRow("Column to Transform:", self.target_column_combo)
        
        self.content_layout.addWidget(target_group)
        
        # SAS Function group
        function_group = QGroupBox("🔧 SAS Function")
        function_layout = QFormLayout(function_group)
        
        # Function type selection
        self.function_combo = CustomSizedComboBox()
        self.function_combo.setMaxVisibleItems(15)
        self.function_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 15px;
                border: none;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        sas_functions = [
            ("strip", "STRIP - Remove leading/trailing spaces"),
            ("upper", "UPCASE - Convert to uppercase"),
            ("lower", "LOWCASE - Convert to lowercase"),
            ("substr", "SUBSTR - Extract substring (start,length)"),
            ("scan", "SCAN - Extract word (delimiter,word_number)"),
            ("compress", "COMPRESS - Remove specified characters"),
            ("catx", "CATX - Concatenate with delimiter"),
            ("length", "LENGTH - Get string length"),
            ("trim", "TRIM - Remove trailing spaces"),
            ("left", "LEFT - Remove leading spaces"),
            ("right", "RIGHT - Remove trailing spaces"),
            ("custom", "Custom - Write custom expression")
        ]
        
        for func_code, func_desc in sas_functions:
            self.function_combo.addItem(func_desc, func_code)
        
        # Set current value
        if hasattr(node, 'function_type'):
            for i in range(self.function_combo.count()):
                if self.function_combo.itemData(i) == node.function_type:
                    self.function_combo.setCurrentIndex(i)
                    break
        
        self.function_combo.currentTextChanged.connect(self.on_function_changed)
        function_layout.addRow("SAS Function:", self.function_combo)
        
        # Expression/parameters input
        self.expression_edit = QLineEdit(node.expression if hasattr(node, 'expression') else "")
        self.expression_edit.textChanged.connect(
            lambda text: self.update_node_property('expression', text)
        )
        
        # Function help label
        self.function_help = QLabel("Select a function to see parameter help")
        self.function_help.setStyleSheet("color: #666; font-size: 10px; font-style: italic; padding: 5px;")
        self.function_help.setWordWrap(True)
        
        function_layout.addRow("Parameters:", self.expression_edit)
        function_layout.addRow("", self.function_help)
        
        self.content_layout.addWidget(function_group)
        
        # Output configuration group
        output_group = QGroupBox("📤 Output Configuration")
        output_layout = QFormLayout(output_group)
        
        # Operation mode selection
        self.operation_mode_combo = CustomSizedComboBox()
        self.operation_mode_combo.setMaxVisibleItems(15)
        self.operation_mode_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 15px;
                border: none;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        self.operation_mode_combo.addItem("Replace existing column", "replace")
        self.operation_mode_combo.addItem("Create new column", "append")
        self.operation_mode_combo.addItem("SDTM Codelist mapping", "codelist")
        
        # Set current value
        if hasattr(node, 'operation_mode'):
            for i in range(self.operation_mode_combo.count()):
                if self.operation_mode_combo.itemData(i) == node.operation_mode:
                    self.operation_mode_combo.setCurrentIndex(i)
                    break
        
        self.operation_mode_combo.currentTextChanged.connect(self.on_operation_mode_changed)
        output_layout.addRow("Operation:", self.operation_mode_combo)
        
        # New column name (only for append mode)
        self.new_column_edit = QLineEdit(node.new_column_name if hasattr(node, 'new_column_name') else "")
        self.new_column_edit.textChanged.connect(
            lambda text: self.update_node_property('new_column_name', text)
        )
        output_layout.addRow("New Column Name:", self.new_column_edit)
        
        # SDTM Codelist selection (only for codelist mode)
        codelist_layout = QHBoxLayout()
        self.codelist_combo = CustomSizedComboBox()
        self.codelist_combo.setMaxVisibleItems(15)
        self.codelist_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 2px solid #e1e5e9;
                border-radius: 6px;
                background-color: white;
                font-size: 12px;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007acc;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                width: 12px;
                height: 8px;
            }
        """)
        
        self.refresh_codelist_btn = QPushButton("🔄")
        self.refresh_codelist_btn.setFixedSize(28, 28)
        self.refresh_codelist_btn.setToolTip("Refresh available codelists")
        self.refresh_codelist_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.refresh_codelist_btn.clicked.connect(self.refresh_codelists)
        
        codelist_layout.addWidget(self.codelist_combo, 1)
        codelist_layout.addWidget(self.refresh_codelist_btn)
        
        self.codelist_widget = QWidget()
        self.codelist_widget.setLayout(codelist_layout)
        output_layout.addRow("SDTM Codelist:", self.codelist_widget)
        
        # Codelist info label
        self.codelist_info_label = QLabel("Select a codelist to auto-populate mappings")
        self.codelist_info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-style: italic;
                font-size: 11px;
                padding: 4px;
            }
        """)
        output_layout.addRow("", self.codelist_info_label)
        
        # Initially hide codelist elements (shown only in codelist mode)
        self.codelist_combo.setVisible(False)
        self.refresh_codelist_btn.setVisible(False)
        self.codelist_info_label.setVisible(False)
        self.codelist_widget.setVisible(False)
        
        self.content_layout.addWidget(output_group)
        
        # Function examples group
        examples_group = QGroupBox("💡 Function Examples")
        examples_layout = QVBoxLayout(examples_group)
        
        self.examples_text = QLabel()
        self.examples_text.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        self.examples_text.setWordWrap(True)
        examples_layout.addWidget(self.examples_text)
        
        self.content_layout.addWidget(examples_group)
        
        # Multiple expressions group
        multiple_group = QGroupBox("🔄 Multiple Expressions")
        multiple_layout = QVBoxLayout(multiple_group)
        
        # Toggle between single and multiple mode
        mode_layout = QHBoxLayout()
        self.single_mode_radio = QRadioButton("Single Expression Mode")
        self.multiple_mode_radio = QRadioButton("Multiple Expressions Mode")
        self.single_mode_radio.setChecked(True)  # Default to single mode
        
        mode_layout.addWidget(self.single_mode_radio)
        mode_layout.addWidget(self.multiple_mode_radio)
        mode_layout.addStretch()
        multiple_layout.addLayout(mode_layout)
        
        # Multiple expressions table
        self.expressions_table = QTableWidget(0, 6)
        self.expressions_table.setHorizontalHeaderLabels(["Select Column", "Function", "Parameters", "Mode", "New Column Name", "Action"])
        
        # Configure column sizing to fit table width proportionally (same as main table)
        header = self.expressions_table.horizontalHeader()
        header.setStretchLastSection(False)
        
        # Set proportional column widths using section resize modes
        # Column 0: Select Column - 25% of width
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Column 1: Function - Fixed reasonable size
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.expressions_table.setColumnWidth(1, 80)
        
        # Column 2: Parameters - 20% of width  
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # Column 3: Mode - Fixed reasonable size
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.expressions_table.setColumnWidth(3, 70)
        
        # Column 4: New Column Name - 25% of width
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Column 5: Delete button - Fixed small size
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.expressions_table.setColumnWidth(5, 50)
        
        self.expressions_table.setMaximumHeight(200)
        
        multiple_layout.addWidget(self.expressions_table)
        
        # Multiple expressions controls
        multi_controls_layout = QHBoxLayout()
        add_expression_btn = QPushButton("+ Add Expression")
        add_expression_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #20a83a);
                color: white;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 12px;
                border: none;
                border-radius: 5px;
                min-width: 100px;
                min-height: 28px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1e7e34);
            }
        """)
        add_expression_btn.clicked.connect(self.add_expression_row)
        multi_controls_layout.addWidget(add_expression_btn)
        
        apply_all_btn = QPushButton("✅ Apply All Expressions")
        apply_all_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_all_btn.clicked.connect(lambda: self.apply_all_expressions(node))
        multi_controls_layout.addWidget(apply_all_btn)
        
        multi_controls_layout.addStretch()
        multiple_layout.addLayout(multi_controls_layout)
        
        # Initially hide multiple expressions (single mode default)
        self.expressions_table.hide()
        add_expression_btn.hide()
        apply_all_btn.hide()
        
        # Connect radio buttons to toggle visibility
        self.single_mode_radio.toggled.connect(self.toggle_expression_mode)
        self.multiple_mode_radio.toggled.connect(self.toggle_expression_mode)
        
        self.content_layout.addWidget(multiple_group)
        
        # Action buttons group (same style as other nodes)
        buttons_group = QGroupBox("🚀 Actions")
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button
        apply_execute_btn = QPushButton("✅ Apply and Execute")
        apply_execute_btn.setToolTip("Apply expression and execute transformation in one step")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_expression_and_execute(node))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.reset_expression(node))
        buttons_layout.addWidget(cancel_btn)
        
        self.content_layout.addWidget(buttons_group)
        
        # Update UI based on current function and mode
        self.update_function_help()
        self.update_operation_mode_ui()
        
        self.content_layout.addStretch()
    
    def on_function_changed(self):
        """Handle function type change."""
        current_data = self.function_combo.currentData()
        if current_data:
            self.update_node_property('function_type', current_data)
            self.update_function_help()
    
    def on_ct_selection_changed(self):
        """Handle CT selection change and automatically populate result values."""
        selected_codelist = self.ct_selection_combo.currentData()
        
        # Update node property
        self.update_node_property('ct_selection', selected_codelist)
        
        if not selected_codelist:
            self.ct_info_label.setText("Select a controlled terminology codelist")
            return
            
        # Check if SDTM specifications are loaded
        main_window = self.get_main_window()
        if not main_window or not hasattr(main_window, 'sdtm_raw_data'):
            self.ct_info_label.setText("⚠️ Please upload SDTM specifications first")
            return
        
        # Update info label to show processing
        self.ct_info_label.setText(f"🔄 Loading values from codelist '{selected_codelist}'...")
        
        # Automatically map values if there are condition values
        self.auto_map_values_to_codelist()

    def on_operation_mode_changed(self):
        """Handle operation mode change."""
        current_data = self.operation_mode_combo.currentData()
        if current_data:
            self.update_node_property('operation_mode', current_data)
            self.update_operation_mode_ui()
    
    def update_function_help(self):
        """Update function help and examples based on selected function."""
        if not hasattr(self, 'function_combo'):
            return
            
        current_function = self.function_combo.currentData()
        
        help_text = ""
        examples_text = ""
        placeholder = ""
        
        if current_function == "strip":
            help_text = "Remove leading and trailing whitespace from text"
            examples_text = "STRIP function removes spaces from both ends.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "upper":
            help_text = "Convert text to uppercase"
            examples_text = "UPCASE function converts all letters to uppercase.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "lower":
            help_text = "Convert text to lowercase"
            examples_text = "LOWCASE function converts all letters to lowercase.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "trim":
            help_text = "Remove all leading and trailing whitespace"
            examples_text = "TRIM function removes spaces, tabs, newlines.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "length":
            help_text = "Get the length of text"
            examples_text = "LENGTH function returns character count.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "reverse":
            help_text = "Reverse the order of characters"
            examples_text = "REVERSE function flips text order.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "substr":
            help_text = "Extract substring starting at position with optional length"
            examples_text = """SUBSTR examples:
• 1,3 - Extract 3 characters starting from position 1
• 5 - Extract from position 5 to end
• 2,10 - Extract 10 characters starting from position 2"""
            placeholder = "start,length (e.g., 1,3 or 5 for rest)"
            
        elif current_function == "scan":
            help_text = "Extract specific word from delimited text"
            examples_text = """SCAN examples:
• ' ',1 - First word (space delimiter)
• ',',2 - Second item (comma delimiter)  
• '|',3 - Third item (pipe delimiter)"""
            placeholder = "delimiter,word_number (e.g., ' ',1)"
            
        elif current_function == "left":
            help_text = "Extract characters from the left (beginning)"
            examples_text = """LEFT examples:
• 3 - First 3 characters
• 5 - First 5 characters"""
            placeholder = "number_of_chars (e.g., 3)"
            
        elif current_function == "right":
            help_text = "Extract characters from the right (end)"
            examples_text = """RIGHT examples:
• 3 - Last 3 characters
• 4 - Last 4 characters"""
            placeholder = "number_of_chars (e.g., 3)"
            
        elif current_function == "compress":
            help_text = "Remove specified characters from text"
            examples_text = """COMPRESS examples:
• ' ' - Remove all spaces
• '()' - Remove parentheses
• '0123456789' - Remove all digits"""
            placeholder = "characters_to_remove (e.g., ' ' or '()' or '-')"
            
        elif current_function == "catx":
            help_text = "Concatenate with delimiter (for single column adds prefix/suffix)"
            examples_text = """CATX examples:
• '_SUFFIX' - Add suffix to values
• 'PREFIX_' - Add prefix to values
• ' - ' - Add dash prefix"""
            placeholder = "prefix_or_suffix (e.g., '_FINAL' or 'PREFIX_')"
            
        elif current_function == "pad_start":
            help_text = "Pad string to specified length at the beginning"
            examples_text = """PAD_START examples:
• 5,' ' - Pad to 5 chars with spaces
• 10,'0' - Pad to 10 chars with zeros"""
            placeholder = "length,pad_char (e.g., 5,' ' or 10,'0')"
            
        elif current_function == "pad_end":
            help_text = "Pad string to specified length at the end"
            examples_text = """PAD_END examples:
• 5,' ' - Pad to 5 chars with spaces
• 8,'.' - Pad to 8 chars with dots"""
            placeholder = "length,pad_char (e.g., 5,' ' or 8,'.')"
            
        elif current_function == "parse_int":
            help_text = "Convert string to integer"
            examples_text = "PARSE_INT converts text to whole numbers.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "parse_float":
            help_text = "Convert string to decimal number"
            examples_text = "PARSE_FLOAT converts text to decimal numbers.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "parse_date":
            help_text = "Convert string to date format"
            examples_text = """PARSE_DATE examples:
• 'YYYY-MM-DD' - Standard ISO format
• 'DD-MMM-YYYY' - Day-Month-Year format
• 'MM/DD/YYYY' - US format"""
            placeholder = "date_format (e.g., 'YYYY-MM-DD' or 'DD-MMM-YYYY')"
            
        elif current_function == "to_string":
            help_text = "Convert any data type to string"
            examples_text = "TO_STRING converts numbers/dates to text.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "to_numeric":
            help_text = "Convert string to numeric (intelligent conversion)"
            examples_text = "TO_NUMERIC converts text to best numeric type.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "regex_extract":
            help_text = "Extract text matching regex pattern"
            examples_text = """REGEX_EXTRACT examples:
• '[0-9]+' - Extract numbers
• '[A-Z]{2,}' - Extract uppercase letters
• 'SITE[0-9]+' - Extract site codes"""
            placeholder = "regex_pattern (e.g., '[0-9]+' or '[A-Z]+')"
            
        elif current_function == "regex_replace":
            help_text = "Replace text matching regex pattern"
            examples_text = """REGEX_REPLACE examples:
• '[^0-9]','' - Remove non-digits
• '\\s+','_' - Replace spaces with underscores
• '[()]','' - Remove parentheses"""
            placeholder = "pattern,replacement (e.g., '[^0-9]','' or '\\s+','_')"
            
        elif current_function == "regex_match":
            help_text = "Check if string matches regex pattern"
            examples_text = """REGEX_MATCH examples:
• '.*@.*\\.com' - Email validation
• '^[0-9]{3}$' - Exactly 3 digits
• 'SUB[0-9]+' - Subject ID pattern"""
            placeholder = "regex_pattern (e.g., '.*@.*\\.com' or '^[0-9]+$')"
            
        elif current_function == "string_contains":
            help_text = "Check if string contains specified text"
            examples_text = """STRING_CONTAINS examples:
• 'ADVERSE' - Contains word ADVERSE
• 'SITE' - Contains SITE anywhere
• '001' - Contains specific ID"""
            placeholder = "search_text (e.g., 'ADVERSE' or 'SITE' or '001')"
            
        elif current_function == "string_replace":
            help_text = "Replace all occurrences of text"
            examples_text = """STRING_REPLACE examples:
• 'old','new' - Replace old with new
• ' ','_' - Replace spaces with underscores
• '-','' - Remove all dashes"""
            placeholder = "old_text,new_text (e.g., 'old','new' or ' ','_')"
            
        elif current_function == "string_startswith":
            help_text = "Check if string starts with specified text"
            examples_text = """STRING_STARTSWITH examples:
• 'SUB' - Starts with SUB
• 'SITE' - Starts with SITE
• 'AE' - Starts with AE"""
            placeholder = "prefix_text (e.g., 'SUB' or 'SITE' or 'AE')"
            
        elif current_function == "string_endswith":
            help_text = "Check if string ends with specified text"
            examples_text = """STRING_ENDSWITH examples:
• '001' - Ends with 001
• '_FINAL' - Ends with _FINAL
• '.csv' - Ends with .csv"""
            placeholder = "suffix_text (e.g., '001' or '_FINAL' or '.csv')"
            
        elif current_function == "if_then_else":
            help_text = "Conditional logic - if condition then value1 else value2"
            examples_text = """IF_THEN_ELSE examples:
• AESER=='No','N','Y' - Map No to N, others to Y
• SEX=='M','MALE','FEMALE' - Gender mapping
• AGE>65,'ELDERLY','ADULT' - Age grouping
• DOSE==0,'NOT_DOSED','DOSED' - Dose status
• COUNTRY=='USA','US','OTHER' - Country mapping"""
            placeholder = "condition,true_value,false_value (e.g., AESER=='No','N','Y')"
            
        elif current_function == "coalesce":
            help_text = "Return first non-null value from list"
            examples_text = """COALESCE examples:
• AESTDTC,AESTDT,'UNKNOWN' - Use first available date
• PREF_NAME,ALT_NAME,'NO_NAME' - Name fallback
• PRIMARY_ID,BACKUP_ID,'' - ID fallback"""
            placeholder = "value1,value2,default (e.g., VAL1,VAL2,'DEFAULT')"
            
        elif current_function == "case_when":
            help_text = "Multiple condition mapping"
            examples_text = """CASE_WHEN examples:
• AGE<18,'PEDIATRIC',AGE>65,'ELDERLY','ADULT' - Age groups
• SEX='M','MALE',SEX='F','FEMALE','UNKNOWN' - Gender
• DOSE=0,'NONE',DOSE<10,'LOW','HIGH' - Dose levels"""
            placeholder = "cond1,val1,cond2,val2,default (e.g., AGE<18,'CHILD',AGE>65,'ELDERLY','ADULT')"
            
        elif current_function == "date_format":
            help_text = "Format date according to pattern"
            examples_text = """DATE_FORMAT examples:
• 'YYYY-MM-DD' - ISO standard format
• 'DD-MMM-YYYY' - Day-Month-Year
• 'MM/DD/YYYY' - US format"""
            placeholder = "date_format (e.g., 'YYYY-MM-DD' or 'DD-MMM-YYYY')"
            
        elif current_function == "date_diff":
            help_text = "Calculate difference between dates"
            examples_text = """DATE_DIFF examples:
• AESTDTC,'days' - Days since AE start
• VISIT_DATE,'months' - Months difference
• CONSENT_DATE,'years' - Years difference"""
            placeholder = "end_date,unit (e.g., AESTDTC,'days' or VISIT_DATE,'months')"
            
        elif current_function == "date_add":
            help_text = "Add specified time to date"
            examples_text = """DATE_ADD examples:
• 30,'days' - Add 30 days
• 6,'months' - Add 6 months
• 1,'years' - Add 1 year"""
            placeholder = "amount,unit (e.g., 30,'days' or 6,'months' or 1,'years')"
            
        elif current_function == "year":
            help_text = "Extract year from date"
            examples_text = "YEAR function extracts 4-digit year.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "month":
            help_text = "Extract month from date"
            examples_text = "MONTH function extracts month number (1-12).\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "day":
            help_text = "Extract day from date"
            examples_text = "DAY function extracts day of month (1-31).\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function in ["sum", "mean", "median", "min", "max", "count", "std"]:
            help_text = f"Calculate {current_function} of numeric values"
            examples_text = f"{current_function.upper()} function aggregates numbers.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function in ["round", "abs", "ceil", "floor"]:
            help_text = f"Mathematical {current_function} function"
            examples_text = f"{current_function.upper()} function processes numbers.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "domain_split":
            help_text = "Split domain-specific identifiers"
            examples_text = """DOMAIN_SPLIT examples:
• 'site' - Extract site code
• 'subject' - Extract subject number
• 'study' - Extract study identifier"""
            placeholder = "part_type (e.g., 'site' or 'subject' or 'study')"
            
        elif current_function in ["visit_mapping", "ae_coding", "cm_mapping", "lb_standardize"]:
            help_text = f"SDTM-specific {current_function.replace('_', ' ')} function"
            examples_text = f"{current_function.upper()} applies SDTM transformations.\nNo parameters needed."
            placeholder = "Leave blank - no parameters required"
            
        elif current_function == "custom":
            help_text = "Write custom Python expression using 'series' variable"
            examples_text = """Custom expression examples:
• series.str.replace('old', 'new')
• series.astype(str) + '_SUFFIX'
• pd.to_datetime(series)
• np.where(series > 0, 'POS', 'NEG')"""
            placeholder = "series.str.method() or custom code"
        
        # Update UI elements
        if hasattr(self, 'function_help'):
            self.function_help.setText(help_text)
        
        if hasattr(self, 'examples_text'):
            self.examples_text.setText(examples_text)
        
        if hasattr(self, 'expression_edit'):
            self.expression_edit.setPlaceholderText(placeholder)
    
    def update_operation_mode_ui(self):
        """Update UI based on operation mode."""
        if not hasattr(self, 'operation_mode_combo'):
            return
            
        current_mode = self.operation_mode_combo.currentData()
        
        # Show/hide CT selection based on mode
        if hasattr(self, 'ct_selection_widget'):
            ct_visible = current_mode == "codelist"
            self.ct_selection_widget.setVisible(ct_visible)
            
            if ct_visible:
                self.refresh_ct_codelists()
        
        # Show/hide new column name based on mode
        if hasattr(self, 'new_column_edit'):
            self.new_column_edit.setEnabled(current_mode == "append")
            if current_mode == "replace":
                self.new_column_edit.setPlaceholderText("Not needed for replace mode")
            elif current_mode == "codelist":
                self.new_column_edit.setPlaceholderText("Not needed for codelist mode")
            else:
                self.new_column_edit.setPlaceholderText("Enter new column name")
        
        # Show/hide old codelist selection based on mode (keeping for backward compatibility)
        if hasattr(self, 'codelist_combo'):
            codelist_visible = current_mode == "codelist"
            self.codelist_combo.setVisible(False)  # Hide old codelist combo as we have new CT selection
            if hasattr(self, 'refresh_codelist_btn'):
                self.refresh_codelist_btn.setVisible(False)
            if hasattr(self, 'codelist_info_label'):
                self.codelist_info_label.setVisible(False)
            
            # Also hide the old codelist widget container
            if hasattr(self, 'codelist_widget'):
                self.codelist_widget.setVisible(False)
    
    def refresh_codelists(self):
        """Refresh available codelists from SDTM specifications."""
        if not hasattr(self, 'codelist_combo'):
            return
            
        self.codelist_combo.clear()
        
        # Get main window to access SDTM specifications
        main_window = self.get_main_window()
        if not main_window or not hasattr(main_window, 'sdtm_specifications'):
            self.codelist_combo.addItem("No SDTM specifications loaded", None)
            self.codelist_info_label.setText("Load SDTM specifications first using the main toolbar button")
            return
        
        # Extract codelists from specifications
        codelists = {}
        
        # Load from the raw specifications (not the processed mappings)
        # We need to reload the original file data if it was processed
        if hasattr(main_window, 'sdtm_raw_data'):
            spec_data = main_window.sdtm_raw_data
        else:
            # For now, use processed data but this will be enhanced
            spec_data = main_window.sdtm_specifications
        
        for sheet_name, df in spec_data.items():
            if hasattr(df, 'columns'):  # Check if it's a DataFrame
                # Find the codelist column (case insensitive)
                codelist_col = None
                decode_col = None
                value_col = None
                
                for col in df.columns:
                    col_upper = col.upper()
                    if 'CODELIST' in col_upper:
                        codelist_col = col
                    elif any(keyword in col_upper for keyword in ['DECODE', 'LABEL', 'DESCRIPTION', 'MEANING']):
                        decode_col = col
                    elif any(keyword in col_upper for keyword in ['VALUE', 'CODE', 'TERM']):
                        value_col = col
                
                if codelist_col and decode_col and value_col:
                    # Group by codelist name
                    unique_codelists = df[codelist_col].dropna().unique()
                    
                    for codelist_name in unique_codelists:
                        if codelist_name and str(codelist_name).strip():
                            codelist_key = str(codelist_name).strip()
                            
                            if codelist_key not in codelists:
                                codelists[codelist_key] = {
                                    'mappings': [],
                                    'sheets': []
                                }
                            
                            # Get all rows for this codelist
                            codelist_rows = df[df[codelist_col] == codelist_name]
                            
                            # Extract mappings
                            for _, row in codelist_rows.iterrows():
                                decode_val = str(row[decode_col]).strip()
                                code_val = str(row[value_col]).strip()
                                
                                if decode_val and code_val and decode_val != 'nan' and code_val != 'nan':
                                    codelists[codelist_key]['mappings'].append({
                                        'condition': decode_val,
                                        'result': code_val,
                                        'sheet': sheet_name
                                    })
                            
                            if sheet_name not in codelists[codelist_key]['sheets']:
                                codelists[codelist_key]['sheets'].append(sheet_name)
        
        if not codelists:
            self.codelist_combo.addItem("No codelists found in specifications", None)
            self.codelist_info_label.setText("No CODELIST column found in loaded specifications")
            return
        
        # Populate combo box with codelists grouped by name
        self.codelist_combo.addItem("Select a codelist...", None)
        
        for codelist_name in sorted(codelists.keys()):
            mapping_count = len(codelists[codelist_name]['mappings'])
            sheet_info = ', '.join(codelists[codelist_name]['sheets'])
            
            self.codelist_combo.addItem(
                f"📋 {codelist_name} ({mapping_count} mappings from {sheet_info})", 
                {
                    'name': codelist_name,
                    'mappings': codelists[codelist_name]['mappings'],
                    'sheets': codelists[codelist_name]['sheets']
                }
            )
        
        # Connect selection handler
        self.codelist_combo.currentTextChanged.connect(self.on_codelist_selected)
        
        self.codelist_info_label.setText(f"Found {len(codelists)} codelists in specifications")
    
    def on_codelist_selected(self):
        """Handle codelist selection and auto-populate mappings."""
        if not hasattr(self, 'codelist_combo'):
            return
            
        selected_data = self.codelist_combo.currentData()
        if not selected_data:
            return
        
        codelist_name = selected_data['name']
        mappings = selected_data['mappings']
        sheets = selected_data['sheets']
        
        if mappings:
            # Auto-populate the first configuration with codelist mappings
            if hasattr(self, 'mapping_configs') and self.mapping_configs:
                first_config = self.mapping_configs[0]
                
                # Clear existing mappings
                mapping_table = first_config['mapping_table']
                mapping_table.setRowCount(0)
                
                # Add codelist mappings (condition = decode, result = code)
                for mapping in mappings:
                    row = mapping_table.rowCount()
                    mapping_table.insertRow(row)
                    
                    # Set condition value (the decode/label value)
                    condition_item = QTableWidgetItem(mapping['condition'])
                    condition_item.setToolTip(f"From codelist: {codelist_name}")
                    mapping_table.setItem(row, 0, condition_item)
                    
                    # Set result value (the coded value)
                    result_item = QTableWidgetItem(mapping['result'])
                    result_item.setToolTip(f"SDTM coded value from {mapping.get('sheet', 'unknown sheet')}")
                    mapping_table.setItem(row, 1, result_item)
                
                # Update info label
                sheet_info = ', '.join(sheets)
                self.codelist_info_label.setText(
                    f"Auto-populated {len(mappings)} mappings from codelist '{codelist_name}' "
                    f"(from {sheet_info})"
                )
                
                # Log the action
                main_window = self.get_main_window()
                if main_window:
                    main_window.log_message(
                        f"Auto-populated {len(mappings)} mappings from codelist '{codelist_name}' "
                        f"from sheets: {sheet_info}"
                    )
                    
                # Update the node's mappings
                self.update_config_mappings(first_config)
            
        else:
            self.codelist_info_label.setText(f"No valid mappings found in codelist '{codelist_name}'")
    
    def refresh_ct_codelists(self):
        """Refresh available CT (Controlled Terminology) codelists from SDTM specifications."""
        if not hasattr(self, 'ct_selection_combo'):
            return
            
        self.ct_selection_combo.clear()
        
        # Get main window to access SDTM specifications
        main_window = self.get_main_window()
        if not main_window or not hasattr(main_window, 'sdtm_raw_data'):
            self.ct_selection_combo.addItem("❌ Please upload SDTM specifications first", None)
            self.ct_info_label.setText("Upload SDTM specifications using the main toolbar button to enable CT selection")
            self.auto_map_btn.setEnabled(False)
            return
        
        # Extract unique codelist names from specifications
        unique_codelists = set()
        spec_data = main_window.sdtm_raw_data
        
        for sheet_name, df in spec_data.items():
            if hasattr(df, 'columns'):  # Check if it's a DataFrame
                # Find the codelist column (case insensitive)
                codelist_col = None
                
                for col in df.columns:
                    col_upper = col.upper()
                    if 'CODELIST' in col_upper or 'CT' in col_upper:
                        codelist_col = col
                        break
                
                if codelist_col:
                    # Get unique codelist names
                    codelist_values = df[codelist_col].dropna().unique()
                    for value in codelist_values:
                        if value and str(value).strip() and str(value).strip().lower() != 'nan':
                            unique_codelists.add(str(value).strip())
        
        if not unique_codelists:
            self.ct_selection_combo.addItem("❌ No codelists found in specifications", None)
            self.ct_info_label.setText("No CODELIST column found in loaded specifications")
            self.auto_map_btn.setEnabled(False)
            return
        
        # Populate combo box with unique codelist names
        self.ct_selection_combo.addItem("🎯 Select a codelist for mapping...", None)
        
        for codelist_name in sorted(unique_codelists):
            self.ct_selection_combo.addItem(f"📋 {codelist_name}", codelist_name)
        
        self.ct_info_label.setText(f"Found {len(unique_codelists)} unique codelists in specifications. Select one for auto-mapping.")
        self.auto_map_btn.setEnabled(len(unique_codelists) > 0)
    
    def auto_map_values_to_codelist(self):
        """Automatically map condition values to selected codelist codes."""
        if not hasattr(self, 'ct_selection_combo') or not hasattr(self, 'mapping_configs'):
            return
            
        selected_codelist = self.ct_selection_combo.currentData()
        if not selected_codelist:
            self.ct_info_label.setText("Select a controlled terminology codelist")
            return
        
        # Get main window to access SDTM specifications  
        main_window = self.get_main_window()
        if not main_window or not hasattr(main_window, 'sdtm_raw_data'):
            self.ct_info_label.setText("⚠️ Please upload SDTM specifications first")
            return
        
        # Get current condition values from mapping table
        condition_values = []
        mapping_table = None
        
        if self.mapping_configs:
            first_config = self.mapping_configs[0]
            mapping_table = first_config['mapping_table']
            
            for row in range(mapping_table.rowCount()):
                condition_item = mapping_table.item(row, 0)
                if condition_item and condition_item.text().strip():
                    condition_values.append(condition_item.text().strip())
        
        if not condition_values:
            self.ct_info_label.setText(f"📝 Add condition values to auto-map with codelist '{selected_codelist}'")
            return
        
        # Find mappings in the selected codelist
        spec_data = main_window.sdtm_raw_data
        mappings_found = {}
        total_mappings = 0
        available_values = []
        
        for sheet_name, df in spec_data.items():
            if not hasattr(df, 'columns'):
                continue
                
            # Find relevant columns - prioritize exact matches
            codelist_col = None
            decode_col = None 
            value_col = None
            
            # First pass: look for exact matches
            for col in df.columns:
                col_upper = col.upper()
                if 'CODELIST' in col_upper or 'CT' in col_upper:
                    codelist_col = col
                elif col_upper == 'DECODE':
                    decode_col = col
                elif col_upper == 'VALUE':
                    value_col = col
            
            # Second pass: fallback to partial matches if exact not found
            if not decode_col:
                for col in df.columns:
                    col_upper = col.upper()
                    if 'LABEL' in col_upper or 'MEANING' in col_upper:
                        decode_col = col
                        break
                        
            if not value_col:
                for col in df.columns:
                    col_upper = col.upper()
                    if 'CODE' in col_upper or 'TERM' in col_upper:
                        value_col = col
                        break
            
            if not (codelist_col and decode_col and value_col):
                continue
                
            # Filter rows for selected codelist and collect available values
            codelist_rows = df[df[codelist_col] == selected_codelist]
            
            for _, row in codelist_rows.iterrows():
                decode_val = str(row[decode_col]).strip()
                code_val = str(row[value_col]).strip()
                
                if decode_val and code_val and decode_val.lower() != 'nan' and code_val.lower() != 'nan':
                    available_values.append(f"{decode_val} → {code_val}")
            
            for condition_val in condition_values:
                if condition_val in mappings_found:
                    continue  # Already found mapping for this condition
                    
                best_match = None
                best_score = 0
                
                for _, row in codelist_rows.iterrows():
                    decode_val = str(row[decode_col]).strip()
                    code_val = str(row[value_col]).strip()
                    
                    if not decode_val or not code_val or decode_val.lower() == 'nan' or code_val.lower() == 'nan':
                        continue
                    
                    # Calculate match score
                    score = 0
                    condition_lower = condition_val.lower()
                    decode_lower = decode_val.lower()
                    
                    # Exact match (highest priority)
                    if condition_lower == decode_lower:
                        score = 100
                    # Starts with (high priority)
                    elif decode_lower.startswith(condition_lower) or condition_lower.startswith(decode_lower):
                        score = 80
                    # Contains (medium priority) 
                    elif condition_lower in decode_lower or decode_lower in condition_lower:
                        score = 60
                    # Similar words (low priority)
                    elif any(word in decode_lower for word in condition_lower.split() if len(word) > 2):
                        score = 40
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'condition': condition_val,
                            'result': code_val,
                            'decode': decode_val,
                            'sheet': sheet_name,
                            'score': score
                        }
                
                if best_match and best_score >= 40:  # Minimum threshold for auto-mapping
                    mappings_found[condition_val] = best_match
                    total_mappings += 1
        
        # Apply mappings to the table
        if mappings_found and mapping_table:
            for row in range(mapping_table.rowCount()):
                condition_item = mapping_table.item(row, 0)
                result_item = mapping_table.item(row, 1)
                
                if condition_item and condition_item.text().strip() in mappings_found:
                    mapping_data = mappings_found[condition_item.text().strip()]
                    
                    # Update result column
                    if not result_item:
                        result_item = QTableWidgetItem()
                        mapping_table.setItem(row, 1, result_item)
                    
                    result_item.setText(mapping_data['result'])
                    result_item.setToolTip(
                        f"Auto-mapped from codelist '{selected_codelist}'\n"
                        f"Matched with: {mapping_data['decode']}\n"
                        f"From sheet: {mapping_data['sheet']}\n"
                        f"Match score: {mapping_data['score']}%"
                    )
                    
                    # Color code based on match quality
                    if mapping_data['score'] >= 80:
                        result_item.setBackground(QColor(220, 255, 220))  # Light green for good matches
                    else:
                        result_item.setBackground(QColor(255, 248, 200))  # Light yellow for approximate matches
            
            # Update info and show summary
            unmapped_count = len(condition_values) - total_mappings
            
            if total_mappings > 0:
                if unmapped_count > 0:
                    self.ct_info_label.setText(
                        f"✅ Auto-mapped {total_mappings}/{len(condition_values)} values from '{selected_codelist}'. "
                        f"⚠️ {unmapped_count} values need manual entry."
                    )
                else:
                    self.ct_info_label.setText(
                        f"✅ All {total_mappings} values successfully auto-mapped from '{selected_codelist}'"
                    )
            else:
                self.ct_info_label.setText(
                    f"⚠️ No matches found in '{selected_codelist}'. Please enter values manually."
                )
            
            # Update the node's mappings
            if self.mapping_configs:
                self.update_config_mappings(self.mapping_configs[0])
                
        else:
            # Show available values if no condition values to map
            if available_values:
                values_preview = available_values[:5]  # Show first 5 values
                preview_text = ", ".join(values_preview)
                if len(available_values) > 5:
                    preview_text += f"... and {len(available_values)-5} more"
                self.ct_info_label.setText(
                    f"📋 Codelist '{selected_codelist}' contains {len(available_values)} values: {preview_text}"
                )
            else:
                self.ct_info_label.setText(
                    f"⚠️ No suitable mappings found in codelist '{selected_codelist}'"
                )
    
    def update_config_mappings(self, config):
        """Update the node's mapping configuration from the table."""
        if not config or 'mapping_table' not in config:
            return
            
        table = config['mapping_table']
        mappings = []
        
        for row in range(table.rowCount()):
            condition_item = table.item(row, 0)
            result_item = table.item(row, 1)
            
            if condition_item and result_item:
                condition = condition_item.text().strip()
                result = result_item.text().strip()
                
                if condition and result:
                    mappings.append({
                        'condition': condition,
                        'result': result
                    })
        
        # Update the config's mappings
        config['mappings'] = mappings
        
        # Also update the node if available
        if hasattr(self, 'current_node') and self.current_node:
            if hasattr(self.current_node, 'mapping_configs'):
                # Find and update the matching config
                for node_config in self.current_node.mapping_configs:
                    if node_config.get('id') == config.get('id'):
                        node_config['mappings'] = mappings
                        break
    
    def get_main_window(self):
        """Get reference to main window."""
        widget = self
        while widget is not None:
            if hasattr(widget, 'sdtm_specifications'):
                return widget
            widget = widget.parent()
        return None
        
    def get_parameter_placeholder(self, function_name):
        """Get parameter placeholder text for a specific function."""
        placeholders = {
            # No parameters needed
            "strip": "Leave blank - no parameters required",
            "upper": "Leave blank - no parameters required", 
            "lower": "Leave blank - no parameters required",
            "trim": "Leave blank - no parameters required",
            "length": "Leave blank - no parameters required",
            "reverse": "Leave blank - no parameters required",
            "parse_int": "Leave blank - no parameters required",
            "parse_float": "Leave blank - no parameters required",
            "to_string": "Leave blank - no parameters required",
            "to_numeric": "Leave blank - no parameters required",
            "year": "Leave blank - no parameters required",
            "month": "Leave blank - no parameters required",
            "day": "Leave blank - no parameters required",
            "sum": "Leave blank - no parameters required",
            "mean": "Leave blank - no parameters required",
            "median": "Leave blank - no parameters required",
            "min": "Leave blank - no parameters required",
            "max": "Leave blank - no parameters required",
            "count": "Leave blank - no parameters required",
            "std": "Leave blank - no parameters required",
            "round": "Leave blank - no parameters required",
            "abs": "Leave blank - no parameters required",
            "ceil": "Leave blank - no parameters required",
            "floor": "Leave blank - no parameters required",
            "visit_mapping": "Leave blank - no parameters required",
            "ae_coding": "Leave blank - no parameters required",
            "cm_mapping": "Leave blank - no parameters required",
            "lb_standardize": "Leave blank - no parameters required",
            
            # Parameters required
            "substr": "start,length (e.g., 1,3 or 5 for rest)",
            "scan": "delimiter,word_number (e.g., ' ',1)",
            "left": "number_of_chars (e.g., 3)",
            "right": "number_of_chars (e.g., 3)",
            "compress": "characters_to_remove (e.g., ' ' or '()' or '-')",
            "catx": "prefix_or_suffix (e.g., '_FINAL' or 'PREFIX_')",
            "pad_start": "length,pad_char (e.g., 5,' ' or 10,'0')",
            "pad_end": "length,pad_char (e.g., 5,' ' or 8,'.')",
            "parse_date": "date_format (e.g., 'YYYY-MM-DD' or 'DD-MMM-YYYY')",
            "regex_extract": "regex_pattern (e.g., '[0-9]+' or '[A-Z]+')",
            "regex_replace": "pattern,replacement (e.g., '[^0-9]','' or '\\s+','_')",
            "regex_match": "regex_pattern (e.g., '.*@.*\\.com' or '^[0-9]+$')",
            "regex_split": "delimiter_pattern (e.g., '\\s+' or ',')",
            "string_extract": "search_text (e.g., 'ADVERSE' or 'SITE')",
            "string_replace": "old_text,new_text (e.g., 'old','new' or ' ','_')",
            "string_contains": "search_text (e.g., 'ADVERSE' or 'SITE' or '001')",
            "string_startswith": "prefix_text (e.g., 'SUB' or 'SITE' or 'AE')",
            "string_endswith": "suffix_text (e.g., '001' or '_FINAL' or '.csv')",
            "if_then_else": "condition,true_value,false_value (e.g., AESER=='No','N','Y')",
            "coalesce": "value1,value2,default (e.g., VAL1,VAL2,'DEFAULT')",
            "nullif": "value_to_null,comparison (e.g., '','NULL')",
            "case_when": "cond1,val1,cond2,val2,default (e.g., AGE<18,'CHILD',AGE>65,'ELDERLY','ADULT')",
            "date_format": "date_format (e.g., 'YYYY-MM-DD' or 'DD-MMM-YYYY')",
            "date_parse": "format_pattern (e.g., 'YYYY-MM-DD' or 'DD-MMM-YYYY')",
            "date_diff": "end_date,unit (e.g., AESTDTC,'days' or VISIT_DATE,'months')",
            "date_add": "amount,unit (e.g., 30,'days' or 6,'months' or 1,'years')",
            "domain_split": "part_type (e.g., 'site' or 'subject' or 'study')",
            "custom": "series.str.method() or custom code"
        }
        
        return placeholders.get(function_name, "Enter parameters...")
        
    def add_expression_row(self, expression_data=None):
        """Add a new row to the expressions table."""
        if not hasattr(self, 'expressions_table'):
            return
            
        row = self.expressions_table.rowCount()
        self.expressions_table.insertRow(row)
        
        # Get available columns from input data
        execution_engine = self.get_execution_engine(self.current_node) if hasattr(self, 'current_node') else None
        columns = []
        if execution_engine:
            try:
                input_data = execution_engine.get_node_input_data(self.current_node)
                if input_data is not None and not input_data.empty:
                    columns = input_data.columns.tolist()
            except:
                pass
        
        # Column selection dropdown
        column_combo = CustomSizedComboBox()
        column_combo.setMaxVisibleItems(15)
        if columns:
            column_combo.addItems(columns)
        if expression_data and 'column' in expression_data:
            index = column_combo.findText(expression_data['column'])
            if index >= 0:
                column_combo.setCurrentIndex(index)
        # Add readable font styling
        column_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
                font-size: 14px;
            }
        """)
        self.expressions_table.setCellWidget(row, 0, column_combo)
        
        # Function selection dropdown - remove blank entry
        function_combo = CustomSizedComboBox()
        function_combo.setMaxVisibleItems(15)
        operations = [
            "strip", "upper", "lower", "trim", "compress", "left", "right",
            "substr", "scan", "catx", "length", "reverse", "pad_start", "pad_end",
            "parse_int", "parse_float", "parse_date", "to_string", "to_numeric",
            "regex_extract", "regex_replace", "regex_match", "regex_split",
            "string_extract", "string_replace", "string_contains", "string_startswith", "string_endswith",
            "sum", "mean", "median", "min", "max", "count", "std", "round", "abs", "ceil", "floor",
            "date_format", "date_parse", "date_diff", "date_add", "year", "month", "day",
            "if_then_else", "coalesce", "nullif", "case_when",
            "domain_split", "visit_mapping", "ae_coding", "cm_mapping", "lb_standardize",
            "custom"
        ]
        function_combo.addItems(operations)  # Use addItems to avoid blank entry
        if expression_data and 'function' in expression_data:
            index = function_combo.findText(expression_data['function'])
            if index >= 0:
                function_combo.setCurrentIndex(index)
        # Add readable font styling
        function_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
                font-size: 14px;
            }
        """)
        self.expressions_table.setCellWidget(row, 1, function_combo)
        
        # Parameters input
        parameters_edit = QLineEdit()
        if expression_data and 'parameters' in expression_data:
            parameters_edit.setText(expression_data['parameters'])
        else:
            # Set initial placeholder based on current function
            current_function = function_combo.currentText()
            parameters_edit.setPlaceholderText(self.get_parameter_placeholder(current_function))
        
        # Add readable font styling
        parameters_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        
        # Connect function change to update parameter placeholder
        function_combo.currentTextChanged.connect(
            lambda text: parameters_edit.setPlaceholderText(self.get_parameter_placeholder(text))
        )
        
        self.expressions_table.setCellWidget(row, 2, parameters_edit)
        
        # Mode selection dropdown
        mode_combo = CustomSizedComboBox()
        mode_combo.setMaxVisibleItems(2)
        mode_combo.addItems(["Replace", "Append"])
        if expression_data and 'mode' in expression_data:
            index = mode_combo.findText(expression_data['mode'])
            if index >= 0:
                mode_combo.setCurrentIndex(index)
        else:
            mode_combo.setCurrentText("Replace")  # Default to Replace
        # Add readable font styling
        mode_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
                font-size: 14px;
            }
        """)
        self.expressions_table.setCellWidget(row, 3, mode_combo)
        
        # New column name input
        new_column_edit = QLineEdit()
        if expression_data and 'new_column' in expression_data:
            new_column_edit.setText(expression_data['new_column'])
        new_column_edit.setEnabled(mode_combo.currentText() == "Append")
        # Add readable font styling
        new_column_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QLineEdit:disabled {
                background: #f5f5f5;
                color: #666;
            }
        """)
        
        # Connect mode change to enable/disable new column field
        mode_combo.currentTextChanged.connect(
            lambda text: new_column_edit.setEnabled(text == "Append")
        )
        self.expressions_table.setCellWidget(row, 4, new_column_edit)
        
        # Remove button
        remove_btn = QPushButton("🗑️")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_expression_row(row))
        self.expressions_table.setCellWidget(row, 5, remove_btn)
    
    def remove_expression_row(self, row):
        """Remove a row from the expressions table."""
        if hasattr(self, 'expressions_table') and row < self.expressions_table.rowCount():
            self.expressions_table.removeRow(row)
    
    def expand_to_docked_view(self, node):
        """Expand expression table to full window like docked/maximized view."""
        try:
            print("🔧 Starting expand_to_docked_view...")
            
            # Create full-window dialog for docked view
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter
            from PyQt6.QtCore import Qt
            
            print("🔧 Creating docked dialog...")
            # Create maximized dialog that takes full screen
            self.docked_dialog = QDialog(self.parent() if self.parent() else None)
            self.docked_dialog.setWindowTitle("🏏 Expression Builder - Docked View")
            self.docked_dialog.setModal(True)
            self.docked_dialog.setWindowState(Qt.WindowState.WindowMaximized)  # Maximized like docking
            
            print("🔧 Setting up main layout...")
            # Main layout with splitter for table + function reference
            main_layout = QVBoxLayout(self.docked_dialog)
            main_layout.setContentsMargins(10, 10, 10, 10)
            
            print("🔧 Creating header...")
            # Compact header for docked view (5% of space)
            header_label = QLabel("🚀 SDTM Expression Builder - Docked View")
            header_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c5234;
                    padding: 6px 10px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8fdf9, stop:1 #e8f5e8);
                    border: 1px solid #2c5234;
                    border-radius: 4px;
                    margin-bottom: 5px;
                    max-height: 30px;
                    min-height: 30px;
                }
            """)
            header_label.setMaximumHeight(30)  # Force small height
            header_label.setMinimumHeight(30)
            main_layout.addWidget(header_label)
            
            print("🔧 Creating splitter with table and function reference...")
            # Create horizontal splitter for table and function reference
            splitter = QSplitter(Qt.Orientation.Horizontal)
            
            # Left side: Expression table (60% width)
            table_widget = self.create_docked_expressions_table_widget(node)
            splitter.addWidget(table_widget)
            
            # Right side: Function reference panel (40% width)
            function_ref_widget = self.create_function_reference_panel()
            splitter.addWidget(function_ref_widget)
            
            # Set splitter proportions (60% table, 40% reference for better balance)
            splitter.setSizes([1200, 800])  # 60-40 split for params space
            
            main_layout.addWidget(splitter)
            
            print("🔧 Creating control buttons...")
            # Full-window control buttons
            self.create_docked_view_controls(main_layout, node)
            
            print("🔧 Showing dialog...")
            # Show the docked dialog
            self.docked_dialog.exec()
            print("🔧 Dialog closed successfully")
            
        except Exception as e:
            print(f"❌ Error creating docked view: {e}")
            import traceback
            traceback.print_exc()
    
    def create_docked_expressions_table_widget(self, node):
        """Create the expressions table widget for docked view."""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHeaderView
        
        # Create container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 5, 0)
        
        # Create table with optimized sizing
        self.docked_table = QTableWidget(0, 6)
        self.docked_table.setHorizontalHeaderLabels(["Select Column", "FUNC", "PARAMS", "MODE", "New Column Name", "DEL"])
        
        # Copy all data from current table to docked table
        if hasattr(self, 'expressions_table'):
            for row in range(self.expressions_table.rowCount()):
                self.docked_table.insertRow(row)
                
                for col in range(6):
                    widget = self.expressions_table.cellWidget(row, col)
                    if widget:
                        self.copy_widget_to_docked_table(widget, row, col)
        
        # Apply compact cricket scoreboard styling with auto-sizing
        self.docked_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d7d3;
                border: 2px solid #2c5234;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #d4edda;
                selection-color: #155724;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                outline: none;
                alternate-background-color: #f8fdf9;
            }
            QTableWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #e0e6e3;
                border-right: 1px solid #e0e6e3;
                min-height: 24px;
                max-height: 28px;
                color: #2c5234;
            }
            QTableWidget::item:selected {
                background-color: #d4edda;
                color: #155724;
                font-weight: 600;
            }
            QTableWidget::item:hover {
                background-color: #f0f8f4;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5234, stop:1 #1e3a26);
                border: 1px solid #1e3a26;
                color: #ffffff;
                padding: 8px 12px;
                font-weight: 700;
                font-size: 10px;
                text-align: center;
                font-family: 'Arial Black', 'Arial', sans-serif;
                text-transform: uppercase;
                letter-spacing: 1px;
                min-height: 25px;
                max-height: 30px;
            }
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6b52, stop:1 #2c5234);
            }
        """)
        
        # Enable alternating row colors
        self.docked_table.setAlternatingRowColors(True)
        
        # Auto-adjust column sizes to fill available space
        header = self.docked_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Column - can resize
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Function - can resize  
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Parameters - can resize (not stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Mode - can resize
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)      # New Column - stretch to fill
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)        # Delete - fixed small
        
        # Set initial proportional column widths
        self.docked_table.setColumnWidth(0, 150)  # Column (wider)
        self.docked_table.setColumnWidth(1, 130)  # Function (adequate)
        self.docked_table.setColumnWidth(2, 200)  # Parameters (fixed, reasonable size)
        self.docked_table.setColumnWidth(3, 90)   # Mode (compact)
        # Column 4 (New Column) will stretch to fill remaining space
        self.docked_table.setColumnWidth(5, 50)   # Delete button
        
        # Set row height to be more compact
        self.docked_table.verticalHeader().setDefaultSectionSize(32)
        self.docked_table.verticalHeader().setMinimumSectionSize(28)
        self.docked_table.verticalHeader().setMaximumSectionSize(36)
        
        layout.addWidget(self.docked_table)
        return container
    
    def create_function_reference_panel(self):
        """Create function reference panel like KNIME on the right side."""
        from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QListWidget, QTextEdit, QListWidgetItem, QSplitter)
        from PyQt6.QtCore import Qt
        
        # Create container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 0, 0, 0)
        
        # Title for function reference
        title = QLabel("📚 Function Reference")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c5234;
                padding: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fdf9, stop:1 #e8f5e8);
                border: 2px solid #2c5234;
                border-radius: 6px;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(title)
        
        # Create vertical splitter for function list and details
        ref_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Function list widget
        self.function_list = QListWidget()
        self.function_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #2c5234;
                border-radius: 4px;
                background: white;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #e8f5e8;
                color: #2c5234;
            }
            QListWidget::item:selected {
                background: #d4edda;
                color: #155724;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background: #f0f8f4;
            }
        """)
        
        # Add function categories
        self.populate_function_list()
        
        # Function details widget
        self.function_details = QTextEdit()
        self.function_details.setStyleSheet("""
            QTextEdit {
                border: 1px solid #2c5234;
                border-radius: 4px;
                background: white;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2c5234;
                padding: 6px;
            }
        """)
        self.function_details.setReadOnly(True)
        self.function_details.setPlainText("Select a function to see details, examples, and usage notes.")
        
        # Connect function selection to details update
        self.function_list.currentItemChanged.connect(self.update_function_details)
        
        # Add to splitter
        ref_splitter.addWidget(self.function_list)
        ref_splitter.addWidget(self.function_details)
        ref_splitter.setSizes([200, 300])  # More space for details
        
        layout.addWidget(ref_splitter)
        return container
        
    def populate_function_list(self):
        """Populate the function list with categorized functions."""
        from PyQt6.QtWidgets import QListWidgetItem
        from PyQt6.QtCore import Qt
        
        # Function categories with their functions
        function_categories = {
            "🧹 String Cleaning": ["strip", "upper", "lower", "trim", "compress"],
            "✂️ String Manipulation": ["substr", "scan", "catx", "length", "reverse", "pad_start", "pad_end"],
            "🔄 Data Conversion": ["parse_int", "parse_float", "parse_date", "to_string", "to_numeric"],
            "🔍 Regex Operations": ["regex_extract", "regex_replace", "regex_match", "regex_split"],
            "📝 String Operations": ["string_extract", "string_replace", "string_contains", "string_startswith", "string_endswith"],
            "🧮 Math & Aggregation": ["sum", "mean", "median", "min", "max", "count", "std", "round", "abs", "ceil", "floor"],
            "📅 Date Functions": ["date_format", "date_parse", "date_diff", "date_add", "year", "month", "day"],
            "🔀 Conditional Logic": ["if_then_else", "coalesce", "nullif", "case_when"],
            "🏥 SDTM Specific": ["domain_split", "visit_mapping", "ae_coding", "cm_mapping", "lb_standardize"],
            "⚙️ Advanced": ["custom"]
        }
        
        for category, functions in function_categories.items():
            # Add category header
            category_item = QListWidgetItem(category)
            category_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not selectable
            category_item.setBackground(self.function_list.palette().alternateBase())
            font = category_item.font()
            font.setBold(True)
            category_item.setFont(font)
            self.function_list.addItem(category_item)
            
            # Add functions in category
            for func in functions:
                func_item = QListWidgetItem(f"  {func}")
                func_item.setData(Qt.ItemDataRole.UserRole, func)  # Store function name
                self.function_list.addItem(func_item)
    
    def update_function_details(self, current_item, previous_item):
        """Update function details when a function is selected."""
        try:
            if not current_item:
                return
                
            func_name = current_item.data(Qt.ItemDataRole.UserRole)
            if not func_name:
                # This is likely a category header, show category info
                self.function_details.setPlainText("📚 Select a function from the list to see detailed documentation, syntax, and examples.")
                return
        
            # Function documentation
            function_docs = {
                "strip": {
                    "description": "Remove whitespace from both ends of a string",
                    "syntax": "strip(column)",
                    "example": "strip(AETERM) → 'Headache' (removes spaces)",
                    "notes": "Useful for cleaning imported data with extra spaces"
                },
                "upper": {
                    "description": "Convert string to uppercase",
                    "syntax": "upper(column)",
                    "example": "upper(SEX) → 'M' or 'F'",
                    "notes": "Standard for SDTM domain codes"
                },
                "lower": {
                    "description": "Convert string to lowercase", 
                    "syntax": "lower(column)",
                    "example": "lower(USUBJID) → 'sub001'",
                    "notes": "Use when lowercase format needed"
                },
                "trim": {
                    "description": "Remove all leading and trailing whitespace (alias for strip)",
                    "syntax": "trim(column)",
                    "example": "trim('  HEADACHE  ') → 'HEADACHE'",
                    "notes": "Same as strip function - removes spaces, tabs, newlines"
                },
                "compress": {
                    "description": "Remove or compress specified characters from strings",
                    "syntax": "compress(column, characters_to_remove)",
                    "example": "compress('SUBJECT-001', '-') → 'SUBJECT001'\ncompress('(555) 123-4567', '()- ') → '5551234567'\ncompress('ABC  123', ' ') → 'ABC123'",
                    "notes": "Multiple scenarios:\n• Remove dashes: compress(USUBJID, '-')\n• Remove spaces: compress(PHONE, ' ')\n• Remove punctuation: compress(TEXT, '()[]{}.,;:')\n• Remove digits: compress(NAME, '0123456789')"
                },
                "substr": {
                    "description": "Extract substring from specified position",
                    "syntax": "substr(column, start, length)",
                    "example": "substr(USUBJID, 1, 3) → 'SUB' (first 3 chars)\nsubstr('ABCDEF', 3, 2) → 'CD'\nsubstr('TEST', 2) → 'EST' (from pos 2 to end)",
                    "notes": "Position starts at 1, not 0. Length is optional - omit to get rest of string"
                },
                "scan": {
                    "description": "Extract nth word from delimited string",
                    "syntax": "scan(column, delimiter, word_number)",
                    "example": "scan('John,Doe,MD', ',', 2) → 'Doe'\nscan('SITE-001-SUB', '-', 3) → 'SUB'\nscan('A B C D', ' ', 1) → 'A'",
                    "notes": "Word numbers start from 1. Common delimiters: ' ', ',', '-', '|', ';'"
                },
                "catx": {
                    "description": "Concatenate strings with specified delimiter or add prefix/suffix",
                    "syntax": "catx(delimiter_or_text)",
                    "example": "catx('_FINAL') → adds '_FINAL' suffix\ncatx('PREFIX_') → adds 'PREFIX_' prefix\ncatx(' - ') → adds ' - ' before value",
                    "notes": "Single column operation adds text as prefix or suffix based on position"
                },
                "length": {
                    "description": "Calculate the length (number of characters) in a string",
                    "syntax": "length(column)",
                    "example": "length('HEADACHE') → 8\nlength('') → 0\nlength('A B C') → 5",
                    "notes": "Counts all characters including spaces. Useful for data validation"
                },
                "left": {
                    "description": "Extract specified number of characters from the left (beginning)",
                    "syntax": "left(column, count)",
                    "example": "left(USUBJID, 4) → 'SUBJ'\nleft('ABCDEF', 3) → 'ABC'",
                    "notes": "Similar to substr(column, 1, count) but simpler syntax"
                },
                "right": {
                    "description": "Extract specified number of characters from the right (end)",
                    "syntax": "right(column, count)",
                    "example": "right(USUBJID, 3) → '001'\nright('ABCDEF', 2) → 'EF'",
                    "notes": "Gets last N characters. Useful for extracting IDs or codes"
                },
                "reverse": {
                    "description": "Reverse the order of characters in a string",
                    "syntax": "reverse(column)",
                    "example": "reverse('ABC') → 'CBA'\nreverse('12345') → '54321'",
                    "notes": "Rarely used in SDTM but useful for special transformations"
                },
                "parse_int": {
                    "description": "Convert string to integer",
                    "syntax": "parse_int(column)",
                    "example": "parse_int('25') → 25\nparse_int('12.7') → 12\nparse_int('ABC') → null",
                    "notes": "Returns null for non-numeric strings. Truncates decimals."
                },
                "parse_float": {
                    "description": "Convert string to decimal number",
                    "syntax": "parse_float(column)",
                    "example": "parse_float('12.5') → 12.5\nparse_float('1.23e-4') → 0.000123\nparse_float('ABC') → null",
                    "notes": "Handles decimal points and scientific notation. Returns null for invalid numbers."
                },
                "parse_date": {
                    "description": "Convert string to date format",
                    "syntax": "parse_date(column, format)",
                    "example": "parse_date('2023-12-25', 'YYYY-MM-DD')\nparse_date('25Dec2023', 'DDMMMYYYY')",
                    "notes": "Essential for SDTM date standardization. Use ISO format when possible."
                },
                "to_string": {
                    "description": "Convert any data type to string representation",
                    "syntax": "to_string(column)",
                    "example": "to_string(25) → '25'\nto_string(12.5) → '12.5'",
                    "notes": "Useful for concatenation or when string format required"
                },
                "to_numeric": {
                    "description": "Convert string to numeric (intelligent conversion)",
                    "syntax": "to_numeric(column)",
                    "example": "to_numeric('25') → 25\nto_numeric('12.5') → 12.5",
                    "notes": "More flexible than parse_int/parse_float - chooses best numeric type"
                },
                "regex_extract": {
                    "description": "Extract text matching regex pattern",
                    "syntax": "regex_extract(column, pattern)",
                    "example": "regex_extract(AETERM, '[0-9]+') → '123'\nregex_extract(USUBJID, 'SITE[0-9]+') → 'SITE001'",
                    "notes": "Returns first match of pattern. Use for extracting specific patterns"
                },
                "regex_replace": {
                    "description": "Replace text matching regex pattern",
                    "syntax": "regex_replace(column, pattern, replacement)",
                    "example": "regex_replace(CMDOSE, '[^0-9.]', '') → '25.5'\nregex_replace(PHONE, '[^0-9]', '') → '5551234567'",
                    "notes": "Powerful for cleaning data. '[^0-9]' means 'not a digit'"
                },
                "regex_match": {
                    "description": "Check if string matches regex pattern (returns True/False)",
                    "syntax": "regex_match(column, pattern)",
                    "example": "regex_match(EMAIL, '.*@.*\\.com') → True/False\nregex_match(USUBJID, 'SUB[0-9]{3}') → True/False",
                    "notes": "Use for data validation and filtering"
                },
                "if_then_else": {
                    "description": "Conditional logic - if condition then value1 else value2",
                    "syntax": "if_then_else(condition, true_value, false_value)",
                    "example": "if_then_else(AESER=='No', 'N', 'Y')\nif_then_else(SEX=='M', 'MALE', 'FEMALE')\nif_then_else(AGE>65, 'ELDERLY', 'ADULT')",
                    "notes": "Use == for equality, not =. Use single quotes for text values. Examples: AESER=='No', AGE>65, DOSE==0"
                },
                "coalesce": {
                    "description": "Return first non-null value from list of values",
                    "syntax": "coalesce(value1, value2, value3, ...)",
                    "example": "coalesce(AESTDTC, AESTDT, 'UNKNOWN')\ncoalesce(PREFERRED_NAME, ALT_NAME, 'NO_NAME')",
                    "notes": "Useful for handling missing data with fallback values"
                },
                "sum": {
                    "description": "Calculate sum of numeric values",
                    "syntax": "sum(column)",
                    "example": "sum(LBSTRESN) → 125.5\nsum(DOSE_AMOUNT) → 750.0",
                    "notes": "Aggregates across all rows. Use for totals and calculations"
                },
                "mean": {
                    "description": "Calculate average (mean) of numeric values",
                    "syntax": "mean(column)",
                    "example": "mean(AGE) → 45.2\nmean(LBSTRESN) → 12.7",
                    "notes": "Statistical function for central tendency"
                },
                "date_format": {
                    "description": "Format date according to pattern",
                    "syntax": "date_format(column, format)",
                    "example": "date_format(AESTDTC, 'YYYY-MM-DD')\ndate_format(VISIT_DATE, 'DD-MMM-YYYY')",
                    "notes": "Use for ISO 8601 SDTM date formatting. Common patterns: YYYY-MM-DD, DD-MMM-YYYY"
                },
                "year": {
                    "description": "Extract year from date",
                    "syntax": "year(column)",
                    "example": "year('2023-12-25') → 2023\nyear(AESTDTC) → 2023",
                    "notes": "Returns 4-digit year as integer"
                },
                "month": {
                    "description": "Extract month from date",
                    "syntax": "month(column)",
                    "example": "month('2023-12-25') → 12\nmonth(AESTDTC) → 12",
                    "notes": "Returns month number (1-12)"
                },
                "day": {
                    "description": "Extract day from date",
                    "syntax": "day(column)",
                    "example": "day('2023-12-25') → 25\nday(AESTDTC) → 25",
                    "notes": "Returns day of month (1-31)"
                },
                "domain_split": {
                    "description": "Split domain-specific identifiers",
                    "syntax": "domain_split(column, part)",
                    "example": "domain_split(USUBJID, 'site') → 'SITE01'\ndomain_split(USUBJID, 'subject') → '001'",
                    "notes": "SDTM-specific for breaking down subject IDs into components"
                },
                "custom": {
                    "description": "Create custom expression with advanced logic",
                    "syntax": "custom(expression)",
                    "example": "custom('series.str.replace(\"old\", \"new\")')\ncustom('series.astype(str) + \"_SUFFIX\"')",
                    "notes": "For complex transformations not covered by built-in functions. Use 'series' variable for the column."
                }
            }
        
            # Get function documentation
            doc = function_docs.get(func_name, {
                "description": f"Function: {func_name}",
                "syntax": f"{func_name}(parameters)",
                "example": "No example available",
                "notes": "Documentation not available"
            })
        
            # Format the details text
            details_text = f"""🔧 FUNCTION: {func_name.upper()}

📝 Description:
{doc['description']}

📖 Syntax:
{doc['syntax']}

💡 Example:
{doc['example']}

📋 Notes:
{doc['notes']}
"""
        
            self.function_details.setPlainText(details_text)
            
        except Exception as e:
            print(f"❌ Error updating function details: {e}")
            if hasattr(self, 'function_details'):
                self.function_details.setPlainText("❌ Error loading function documentation.")
    
    def toggle_expression_table_view(self, node):
        """Toggle between normal and full-window docked view (single click)."""
        try:
            if not hasattr(self, 'expressions_table'):
                return
            
            # Always expand to docked view on click (no toggle state needed)
            self.expand_to_docked_view(node)
            print("🔼 Opening docked/maximized expression view")
                
        except Exception as e:
            print(f"❌ Error opening docked view: {e}")
            import traceback
            traceback.print_exc()
    
    def copy_widget_to_docked_table(self, widget, row, col):
        """Copy widget from normal table to docked table with compact styling."""
        from PyQt6.QtWidgets import QComboBox, QLineEdit, QPushButton
        
        try:
            if hasattr(widget, 'currentText'):  # ComboBox
                new_widget = QComboBox()
                new_widget.setStyleSheet("""
                    QComboBox {
                        border: 1px solid #2c5234;
                        border-radius: 3px;
                        padding: 4px 6px;
                        background: white;
                        font-size: 14px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 500;
                        min-height: 20px;
                        max-height: 24px;
                        color: #2c5234;
                    }
                    QComboBox:focus {
                        border-color: #4a6b52;
                        background: #f8fdf9;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 20px;
                    }
                    QComboBox::down-arrow {
                        width: 12px;
                        height: 12px;
                    }
                """)
                
                if col == 1:  # Function column - add all SDTM functions
                    functions = [
                        # String Cleaning & Basic
                        "strip", "upper", "lower", "trim", "compress", "left", "right",
                        # String Manipulation
                        "substr", "scan", "catx", "length", "reverse", "pad_start", "pad_end",
                        # Parsing & Conversion
                        "parse_int", "parse_float", "parse_date", "to_string", "to_numeric",
                        # Regex Operations
                        "regex_extract", "regex_replace", "regex_match", "regex_split",
                        # String Operations
                        "string_extract", "string_replace", "string_contains", "string_startswith", "string_endswith",
                        # Math & Aggregation
                        "sum", "mean", "median", "min", "max", "count", "std", "round", "abs", "ceil", "floor",
                        # Date Functions
                        "date_format", "date_parse", "date_diff", "date_add", "year", "month", "day",
                        # Conditional
                        "if_then_else", "coalesce", "nullif", "case_when",
                        # SDTM Specific
                        "domain_split", "visit_mapping", "ae_coding", "cm_mapping", "lb_standardize",
                        # Advanced
                        "custom"
                    ]
                    new_widget.addItems(functions)
                elif col == 0:  # Column
                    new_widget.addItems(self.available_columns if hasattr(self, 'available_columns') else [])
                elif col == 3:  # Mode
                    new_widget.addItems(["Replace", "Append"])
                
                # Set current selection
                current_text = widget.currentText()
                index = new_widget.findText(current_text)
                if index >= 0:
                    new_widget.setCurrentIndex(index)
                    
                self.docked_table.setCellWidget(row, col, new_widget)
                
            elif hasattr(widget, 'text') and not isinstance(widget, QPushButton):  # LineEdit (but not button)
                new_widget = QLineEdit()
                new_widget.setStyleSheet("""
                    QLineEdit {
                        border: 1px solid #2c5234;
                        border-radius: 3px;
                        padding: 4px 6px;
                        background: white;
                        font-size: 14px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 500;
                        min-height: 20px;
                        max-height: 24px;
                        color: #2c5234;
                    }
                    QLineEdit:focus {
                        border-color: #4a6b52;
                        background: #f8fdf9;
                    }
                    QLineEdit::placeholder {
                        color: #6c7b6e;
                        font-style: italic;
                    }
                """)
                new_widget.setText(widget.text())
                # Only set placeholder if widget has it
                if hasattr(widget, 'placeholderText'):
                    new_widget.setPlaceholderText(widget.placeholderText())
                self.docked_table.setCellWidget(row, col, new_widget)
                
            elif isinstance(widget, QPushButton) or col == 5:  # Remove button
                new_widget = QPushButton("×")
                new_widget.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #d73502, stop:1 #b82d02);
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                        border: 1px solid #b82d02;
                        border-radius: 3px;
                        padding: 2px;
                        min-height: 20px;
                        max-height: 24px;
                        max-width: 30px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #e74c02, stop:1 #d73502);
                    }
                """)
                new_widget.clicked.connect(lambda r=row: self.docked_table.removeRow(r))
                self.docked_table.setCellWidget(row, col, new_widget)
                
        except Exception as e:
            print(f"❌ Error copying widget at row {row}, col {col}: {e}")
            # Create a fallback widget
            if col == 5:
                fallback_widget = QPushButton("×")
                fallback_widget.clicked.connect(lambda r=row: self.docked_table.removeRow(r))
            else:
                fallback_widget = QLineEdit()
                fallback_widget.setPlaceholderText("Error copying widget")
            self.docked_table.setCellWidget(row, col, fallback_widget)
    
    def create_docked_view_controls(self, layout, node):
        """Create control buttons for docked view."""
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)
        
        # Add Expression button for docked view
        add_btn = QPushButton("➕ Add Expression")
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #20a83a);
                color: white;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                min-width: 120px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1e7e34);
            }
        """)
        add_btn.clicked.connect(lambda: self.add_docked_expression_row())
        
        # Save and Close button
        save_close_btn = QPushButton("💾 Save & Close Docked View")
        save_close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5234, stop:1 #1e3a26);
                color: white;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                min-width: 150px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6b52, stop:1 #2c5234);
            }
        """)
        save_close_btn.clicked.connect(lambda: self.save_and_close_docked_view())
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
                color: white;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                min-width: 90px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #bd2130);
            }
        """)
        cancel_btn.clicked.connect(lambda: self.cancel_docked_view())
        
        button_layout.addWidget(add_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_close_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def add_docked_expression_row(self):
        """Add a new expression row in docked view with compact styling."""
        from PyQt6.QtWidgets import QComboBox, QLineEdit, QPushButton
        
        row = self.docked_table.rowCount()
        self.docked_table.insertRow(row)
        
        # Compact styling for docked view widgets
        compact_combo_style = """
            QComboBox {
                border: 1px solid #2c5234;
                border-radius: 3px;
                padding: 4px 6px;
                background: white;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                min-height: 20px;
                max-height: 28px;
                color: #2c5234;
            }
            QComboBox:focus {
                border-color: #4a6b52;
                background: #f8fdf9;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #2c5234;
                selection-background-color: #4a6b52;
                selection-color: white;
                outline: none;
                color: #2c5234;
                font-size: 14px;
            }
        """
        
        compact_edit_style = """
            QLineEdit {
                border: 1px solid #2c5234;
                border-radius: 3px;
                padding: 4px 6px;
                background: white;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                min-height: 20px;
                max-height: 28px;
                color: #2c5234;
            }
            QLineEdit:focus {
                border-color: #4a6b52;
                background: #f8fdf9;
            }
        """
        
        # Column combo
        column_combo = QComboBox()
        column_combo.addItems(self.available_columns if hasattr(self, 'available_columns') else [])
        column_combo.setStyleSheet(compact_combo_style)
        self.docked_table.setCellWidget(row, 0, column_combo)
        
        # Function combo
        function_combo = QComboBox()
        functions = [
            "strip", "upper", "lower", "trim", "compress", "left", "right",
            "substr", "scan", "catx", "length", "reverse", "pad_start", "pad_end",
            "parse_int", "parse_float", "parse_date", "to_string", "to_numeric",
            "regex_extract", "regex_replace", "regex_match", "regex_split",
            "string_extract", "string_replace", "string_contains", "string_startswith", "string_endswith",
            "sum", "mean", "median", "min", "max", "count", "std", "round", "abs", "ceil", "floor",
            "date_format", "date_parse", "date_diff", "date_add", "year", "month", "day",
            "if_then_else", "coalesce", "nullif", "case_when",
            "domain_split", "visit_mapping", "ae_coding", "cm_mapping", "lb_standardize",
            "custom"
        ]
        function_combo.addItems(functions)
        function_combo.setStyleSheet(compact_combo_style)
        self.docked_table.setCellWidget(row, 1, function_combo)
        
        # Parameters input
        params_edit = QLineEdit()
        # Set initial placeholder based on first function
        initial_function = functions[0] if functions else ""
        params_edit.setPlaceholderText(self.get_parameter_placeholder(initial_function))
        params_edit.setStyleSheet(compact_edit_style)
        
        # Connect function change to update parameter placeholder
        function_combo.currentTextChanged.connect(
            lambda text: params_edit.setPlaceholderText(self.get_parameter_placeholder(text))
        )
        
        self.docked_table.setCellWidget(row, 2, params_edit)
        
        # Mode combo
        mode_combo = QComboBox()
        mode_combo.addItems(["Replace", "Append"])
        mode_combo.setStyleSheet(compact_combo_style)
        self.docked_table.setCellWidget(row, 3, mode_combo)
        
        # New column input
        new_col_edit = QLineEdit()
        new_col_edit.setPlaceholderText("New column name...")
        new_col_edit.setStyleSheet(compact_edit_style)
        self.docked_table.setCellWidget(row, 4, new_col_edit)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d73502, stop:1 #b82d02);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #b82d02;
                border-radius: 3px;
                padding: 2px;
                min-height: 20px;
                max-height: 24px;
                max-width: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c02, stop:1 #d73502);
            }
        """)
        remove_btn.clicked.connect(lambda: self.docked_table.removeRow(row))
        self.docked_table.setCellWidget(row, 5, remove_btn)
    
    def save_and_close_docked_view(self):
        """Save docked view data back to normal table and close."""
        try:
            # Clear current expressions table
            self.expressions_table.setRowCount(0)
            
            # Copy data from docked table back to normal table
            for row in range(self.docked_table.rowCount()):
                self.expressions_table.insertRow(row)
                
                for col in range(6):
                    docked_widget = self.docked_table.cellWidget(row, col)
                    if docked_widget:
                        # Create new widget for normal table
                        self.copy_widget_to_normal_table(docked_widget, row, col)
            
            print(f"✅ Saved {self.docked_table.rowCount()} expressions from docked view")
            
            # Close docked dialog
            if hasattr(self, 'docked_dialog'):
                self.docked_dialog.accept()
                
            # Reset expand state
            self.is_expanded = False
            self.expand_btn.setText("⇲ Expand")
            
        except Exception as e:
            print(f"❌ Error saving docked view: {e}")
    
    def copy_widget_to_normal_table(self, docked_widget, row, col):
        """Copy widget from docked table back to normal table."""
        from ui.property_panel import CustomSizedComboBox
        from PyQt6.QtWidgets import QLineEdit, QPushButton
        
        try:
            if hasattr(docked_widget, 'currentText'):  # ComboBox
                new_widget = CustomSizedComboBox()
                
                if col == 1:  # Function
                    functions = [
                        "strip", "upper", "lower", "trim", "compress", "left", "right",
                        "substr", "scan", "catx", "length", "reverse", "pad_start", "pad_end",
                        "parse_int", "parse_float", "parse_date", "to_string", "to_numeric",
                        "regex_extract", "regex_replace", "regex_match", "regex_split",
                        "string_extract", "string_replace", "string_contains", "string_startswith", "string_endswith",
                        "sum", "mean", "median", "min", "max", "count", "std", "round", "abs", "ceil", "floor",
                        "date_format", "date_parse", "date_diff", "date_add", "year", "month", "day",
                        "if_then_else", "coalesce", "nullif", "case_when",
                        "domain_split", "visit_mapping", "ae_coding", "cm_mapping", "lb_standardize",
                        "custom"
                    ]
                    new_widget.addItems(functions)
                elif col == 0:  # Column
                    new_widget.addItems(self.available_columns if hasattr(self, 'available_columns') else [])
                elif col == 3:  # Mode
                    new_widget.addItems(["Replace", "Append"])
                
                # Set selection
                current_text = docked_widget.currentText()
                index = new_widget.findText(current_text)
                if index >= 0:
                    new_widget.setCurrentIndex(index)
                
                # Apply readable font styling
                new_widget.setStyleSheet("""
                    QComboBox {
                        padding: 4px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background: white;
                        min-height: 20px;
                        color: black;
                        font-size: 14px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QComboBox:focus {
                        border-color: #0078d4;
                    }
                    QComboBox QAbstractItemView {
                        background: white;
                        border: 1px solid #ccc;
                        selection-background-color: #0078d4;
                        selection-color: white;
                        outline: none;
                        color: black;
                        font-size: 14px;
                    }
                """)
                
                self.expressions_table.setCellWidget(row, col, new_widget)
                
            elif hasattr(docked_widget, 'text') and not isinstance(docked_widget, QPushButton):  # LineEdit (but not button)
                new_widget = QLineEdit()
                new_widget.setText(docked_widget.text())
                # Only set placeholder if docked widget has it
                if hasattr(docked_widget, 'placeholderText'):
                    new_widget.setPlaceholderText(docked_widget.placeholderText())
                
                # Apply readable font styling
                new_widget.setStyleSheet("""
                    QLineEdit {
                        padding: 4px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background: white;
                        min-height: 20px;
                        color: black;
                        font-size: 14px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QLineEdit:focus {
                        border-color: #0078d4;
                    }
                """)
                
                self.expressions_table.setCellWidget(row, col, new_widget)
                
            elif isinstance(docked_widget, QPushButton) or col == 5:  # Remove button
                new_widget = QPushButton("×")
                new_widget.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #d73502, stop:1 #b82d02);
                        color: white;
                        font-size: 14px;
                        font-weight: bold;
                        border: 1px solid #b82d02;
                        border-radius: 3px;
                        padding: 2px;
                        height: 26px;
                        min-height: 26px;
                        max-height: 26px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #e74c02, stop:1 #d73502);
                    }
                """)
                new_widget.clicked.connect(lambda r=row: self.expressions_table.removeRow(r))
                self.expressions_table.setCellWidget(row, col, new_widget)
                
        except Exception as e:
            print(f"❌ Error copying widget from docked table at row {row}, col {col}: {e}")
            # Create a fallback widget
            if col == 5:
                fallback_widget = QPushButton("×")
                fallback_widget.clicked.connect(lambda r=row: self.expressions_table.removeRow(r))
            else:
                fallback_widget = QLineEdit()
                fallback_widget.setPlaceholderText("Error copying widget")
            self.expressions_table.setCellWidget(row, col, fallback_widget)
    
    def cancel_docked_view(self):
        """Cancel docked view without saving changes."""
        if hasattr(self, 'docked_dialog'):
            self.docked_dialog.reject()
        
        # Reset expand state
        self.is_expanded = False
        self.expand_btn.setText("⇲ Expand")
        print("❌ Docked view cancelled - no changes saved")
    
    def store_original_layout(self):
        """Store original layout state for restoration."""
        self.original_layout_stored = True
        # Could store more complex state here if needed
    
    def collapse_to_normal_view(self):
        """Collapse from any expanded state back to normal view."""
        # This is called when collapsing from docked view
        # The actual collapse happens when the docked dialog closes
        print("🔽 Collapsing from docked view to normal view")
    
    
    def apply_properties(self, node):
        """Apply expression builder properties to the node."""
        try:
            if not hasattr(self, 'expressions_table'):
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Error", "Expression table not found.")
                return
                
            # Collect all expressions from the table
            expressions = []
            for row in range(self.expressions_table.rowCount()):
                column_combo = self.expressions_table.cellWidget(row, 0)
                function_combo = self.expressions_table.cellWidget(row, 1)
                params_edit = self.expressions_table.cellWidget(row, 2)
                mode_combo = self.expressions_table.cellWidget(row, 3)
                new_col_edit = self.expressions_table.cellWidget(row, 4)
                
                if column_combo and function_combo and mode_combo:
                    column_name = column_combo.currentText()
                    function_type = function_combo.currentText()  # Changed from currentData to currentText
                    parameters = params_edit.text() if params_edit else ""
                    operation_mode = mode_combo.currentText()  # Changed from currentData to currentText
                    new_column_name = new_col_edit.text() if new_col_edit else ""
                    
                    # Debug data vs text values
                    print(f"🔧 Row {row}: Column='{column_name}', Function='{function_type}', Mode='{operation_mode}'")
                    
                    if (column_name and column_name != "Select column..." and 
                        not column_name.startswith("Select") and 
                        function_type and function_type not in ["None", "Select function..."] and
                        operation_mode and operation_mode not in ["None", "Select mode..."]):
                        # Validate append mode has new column name
                        if operation_mode.lower() == "append" and not new_column_name.strip():
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.warning(None, "Missing Column Name",
                                f"Row {row+1}: Please enter a new column name for append mode.")
                            return
                        
                        # CRITICAL VALIDATION: Check for duplicate column names before saving
                        if operation_mode.lower() == "append" and new_column_name.strip():
                            is_valid, error_msg = self.validate_column_name(new_column_name.strip(), node, row)
                            if not is_valid:
                                from PyQt6.QtWidgets import QMessageBox
                                QMessageBox.critical(None, "Duplicate Column Error", 
                                    f"Row {row+1}: {error_msg}\n\nPlease fix this issue before saving/executing expressions.")
                                return
                        
                        expressions.append({
                            'column': column_name,
                            'function': function_type,
                            'parameters': parameters,
                            'mode': operation_mode,
                            'new_column': new_column_name
                        })
            
            if not expressions:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "No Expressions", "Please add at least one expression.")
                return
                
            # Store expressions on node for execution and persistence
            node.multiple_expressions = expressions
            node.expressions = expressions  # For loading/saving to file
            node.is_multiple_mode = True
            
            print(f"✅ Saved {len(expressions)} expressions to node (both multiple_expressions and expressions)")
            
            # Execute the node
            execution_engine = self.get_execution_engine(node)
            if execution_engine:
                try:
                    execution_engine.execute_node(node)
                    print("✅ Expression builder executed successfully")
                    
                    # Emit signal to refresh data viewer
                    self.data_refresh_requested.emit(node)
                    print("🔄 Multiple expressions: Data refresh signal emitted")
                    
                    # Only refresh the available columns (for new columns created) instead of rebuilding entire panel
                    self.refresh_expression_builder_after_execution(node)
                    
                except Exception as e:
                    print(f"❌ Error executing expressions: {e}")
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(None, "Execution Error", f"Failed to execute expressions: {str(e)}")
            else:
                print("⚠️ Cannot execute - no execution engine available")
                
        except Exception as e:
            print(f"❌ Error applying expression builder properties: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Error", f"Failed to apply expression: {str(e)}")

    def refresh_expression_builder_after_execution(self, node):
        """Refresh expression builder after execution without rebuilding the expressions table."""
        print("🔄 Refreshing expression builder after execution (preserving user selections)")
        
        # Update available columns to include newly created ones
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            try:
                # Get output data (includes new columns from execution)
                output_data = execution_engine.get_node_output_data(node)
                if output_data is not None and not output_data.empty:
                    self.available_columns = output_data.columns.tolist()
                    print(f"✅ Updated available columns: {len(self.available_columns)} columns (includes new ones)")
                    
                    # Refresh existing column dropdowns while preserving ALL selections
                    if hasattr(self, 'expressions_table') and self.expressions_table.rowCount() > 0:
                        self.refresh_existing_column_dropdowns()
                        
                    # Update or add results section
                    self.update_expression_results_section(node, output_data)
                    
            except Exception as e:
                print(f"⚠️ Error refreshing after execution: {e}")
                
    def update_expression_results_section(self, node, output_data):
        """Update or add the results section without rebuilding the entire panel."""
        # Remove existing results section if present
        if hasattr(self, 'result_group') and self.result_group is not None:
            try:
                # Safely remove from layout first
                if self.result_group.parent():
                    layout = self.result_group.parent().layout()
                    if layout:
                        layout.removeWidget(self.result_group)
                self.result_group.setParent(None)
                self.result_group = None  # Clear reference immediately
            except RuntimeError:
                # Widget already deleted, ignore
                self.result_group = None
            
        # Add new results section
        self.result_group = QGroupBox("✨ Expression Results")
        self.result_group.setStyleSheet("""
            QGroupBox {
                color: #27ae60;
                border: 1px solid #999;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 2px;
            }
        """)
        result_layout = QVBoxLayout(self.result_group)
        
        result_info = QLabel(f"✅ Expressions applied: {len(output_data)} rows processed")
        result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
        result_layout.addWidget(result_info)
        
        # View transformed data button
        view_btn = QPushButton("👁️ View Transformed Data")
        view_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 5px 10px;
                border: none;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Transformed Data"))
        result_layout.addWidget(view_btn)
        
        # Add to content layout (after expressions group)
        self.content_layout.addWidget(self.result_group)

    def remove_expression_row(self, row):
        """Remove a row from the expressions table."""
        if hasattr(self, 'expressions_table') and row < self.expressions_table.rowCount():
            self.expressions_table.removeRow(row)
        
    def create_constant_value_properties(self, node):
        """Create properties for constant value column nodes with multiple column support."""
        # Store original properties for cancel functionality
        if not hasattr(node, '_original_properties'):
            node._original_properties = {
                'columns': [col.copy() for col in node.columns],
                'column_name': node.column_name,
                'constant_value': node.constant_value,
                'data_type': node.data_type
            }
        
        # Multiple columns configuration group
        self.columns_group = QGroupBox("Multiple Constant Value Columns")
        columns_layout = QVBoxLayout(self.columns_group)
        
        # Create scroll area for columns
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        scroll_area.setMaximumHeight(300)
        
        self.columns_widget = QWidget()
        self.columns_layout = QVBoxLayout(self.columns_widget)
        
        # Store column controls for updates
        self.column_controls = []
        
        # Create controls for each column
        self.refresh_column_controls(node)
        
        scroll_area.setWidget(self.columns_widget)
        columns_layout.addWidget(scroll_area)
        
        # Add/Remove buttons
        buttons_layout = QHBoxLayout()
        
        add_column_btn = QPushButton("➕ Add Column")
        add_column_btn.setStyleSheet(BUTTON_STYLE_SECONDARY)
        add_column_btn.clicked.connect(lambda: self.add_new_column(node))
        buttons_layout.addWidget(add_column_btn)
        
        remove_column_btn = QPushButton("➖ Remove Last")
        remove_column_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        remove_column_btn.clicked.connect(lambda: self.remove_last_column(node))
        buttons_layout.addWidget(remove_column_btn)
        
        columns_layout.addLayout(buttons_layout)
        
        self.content_layout.addWidget(self.columns_group)
        
        # Preview group
        preview_group = QGroupBox("🔍 Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.constant_preview_label = QLabel("Preview will appear here")
        self.constant_preview_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background: #f0f8ff;
                border: 1px solid #87ceeb;
                border-radius: 4px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        preview_layout.addWidget(self.constant_preview_label)
        
        # Update preview
        self.update_constant_preview(node)
        
        self.content_layout.addWidget(preview_group)
        
        # Action buttons group
        buttons_group = QGroupBox("🚀 Actions")
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button
        apply_execute_btn = QPushButton("✅ Apply and Execute")
        apply_execute_btn.setToolTip("Apply constant value columns and execute transformation")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_constant_value_and_execute(node))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button (like other nodes)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.cancel_constant_value(node))
        buttons_layout.addWidget(cancel_btn)
        
        self.content_layout.addWidget(buttons_group)
        
        self.content_layout.addStretch()
        
    def create_column_control_group(self, col_def, index, node):
        """Create control group for a single column definition."""
        group = QGroupBox(f"Column {index + 1}")
        layout = QFormLayout(group)
        
        # Column name
        name_edit = QLineEdit(col_def.get('column_name', ''))
        name_edit.setPlaceholderText("Enter column name")
        
        # Data type
        type_combo = QComboBox()
        type_combo.addItems(["string", "integer", "float", "boolean"])
        type_combo.setCurrentText(col_def.get('data_type', 'string'))
        
        # Constant value
        value_edit = QLineEdit(col_def.get('constant_value', ''))
        value_edit.setPlaceholderText("Enter constant value")
        
        layout.addRow("Column Name:", name_edit)
        layout.addRow("Data Type:", type_combo)
        layout.addRow("Constant Value:", value_edit)
        
        # Connect signals to update node
        def update_column():
            col_def['column_name'] = name_edit.text()
            col_def['data_type'] = type_combo.currentText()
            col_def['constant_value'] = value_edit.text()
            
            # Sync first column to backward compatibility properties for save/load
            if index == 0 and node.columns:
                node.column_name = node.columns[0].get('column_name', '')
                node.constant_value = node.columns[0].get('constant_value', '')
                node.data_type = node.columns[0].get('data_type', 'string')
            
            self.update_constant_preview(node)
            
        name_edit.textChanged.connect(update_column)
        type_combo.currentTextChanged.connect(update_column)
        value_edit.textChanged.connect(update_column)
        
        return group, (name_edit, type_combo, value_edit)
        
    def refresh_column_controls(self, node):
        """Refresh the column controls display."""
        # Clear existing controls
        for i in reversed(range(self.columns_layout.count())):
            child = self.columns_layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
        
        self.column_controls = []
        
        # Create controls for each column
        for i, col_def in enumerate(node.columns):
            group, controls = self.create_column_control_group(col_def, i, node)
            self.columns_layout.addWidget(group)
            self.column_controls.append(controls)
            
    def add_new_column(self, node):
        """Add a new column definition."""
        node.columns.append({
            'column_name': '',
            'constant_value': '',
            'data_type': 'string'
        })
        
        # Sync first column to backward compatibility properties
        if node.columns:
            node.column_name = node.columns[0].get('column_name', '')
            node.constant_value = node.columns[0].get('constant_value', '')
            node.data_type = node.columns[0].get('data_type', 'string')
        
        self.refresh_column_controls(node)
        self.update_constant_preview(node)
        
    def remove_last_column(self, node):
        """Remove the last column definition."""
        if len(node.columns) > 1:  # Keep at least one column
            node.columns.pop()
            
            # Sync first column to backward compatibility properties
            if node.columns:
                node.column_name = node.columns[0].get('column_name', '')
                node.constant_value = node.columns[0].get('constant_value', '')
                node.data_type = node.columns[0].get('data_type', 'string')
            
            self.refresh_column_controls(node)
            self.update_constant_preview(node)
            
    def update_constant_preview(self, node):
        """Update the preview text for constant value columns."""
        if not hasattr(self, 'constant_preview_label'):
            return
            
        if not node.columns or not any(col.get('column_name', '').strip() for col in node.columns):
            self.constant_preview_label.setText("No columns configured")
            return
            
        preview_lines = []
        for i, col_def in enumerate(node.columns):
            name = col_def.get('column_name', '').strip()
            value = col_def.get('constant_value', '')
            data_type = col_def.get('data_type', 'string')
            
            if name:
                preview_lines.append(f"{i+1}. '{name}' = {value} ({data_type})")
                
        if preview_lines:
            preview_text = "Will add columns:\n" + "\n".join(preview_lines)
        else:
            preview_text = "Enter column names and values"
            
        self.constant_preview_label.setText(preview_text)
    
    def create_row_filter_properties(self, node):
        """Create properties for row filter nodes with fancy UI."""
        print(f"ROW FILTER: Creating row filter properties for: {node.title}")
        
        # Get available columns from connected input nodes
        available_columns = self.get_available_columns_for_node(node)
        print(f"ROW FILTER: Available columns for filter: {available_columns}")
        
        # Initialize multiple conditions property if not exists
        if not hasattr(node, 'use_multiple_conditions'):
            node.use_multiple_conditions = False
            
        # Connection status header
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        if available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            status_icon = QLabel("🔗")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel(f"Connected - {len(available_columns)} columns available")
            status_text.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            status_icon = QLabel("⚠️")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel("No input connection detected")
            status_text.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 14px;")
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        status_widget.setStyleSheet("""
            QWidget {
                background: #f0f0f0;
                border: 1px solid #999;
            }
        """)
        self.content_layout.addWidget(status_widget)
        
        # Main filter configuration
        main_filter_group = QGroupBox("Primary Filter Condition")
        main_filter_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #999;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 2px;
            }
        """)
        main_filter_layout = QVBoxLayout(main_filter_group)
        main_filter_layout.setSpacing(15)
        
        # Create modern form layout
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(10)
        
        # Column selection
        col_label = QLabel("Column:")
        col_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        self.filter_column_combo = CustomSizedComboBox()
        self.filter_column_combo.addItems(available_columns)
        self.filter_column_combo.setMaxVisibleItems(10)
        
        # Simple, clean styling with better selection visibility
        self.filter_column_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 15px;
                border: none;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        if node.filter_column:
            index = self.filter_column_combo.findText(node.filter_column)
            if index >= 0:
                self.filter_column_combo.setCurrentIndex(index)
        self.filter_column_combo.currentTextChanged.connect(lambda text: self.update_filter_property(node, 'filter_column', text))
        
        form_layout.addWidget(col_label, 0, 0)
        form_layout.addWidget(self.filter_column_combo, 0, 1)
        
        # Operator selection
        op_label = QLabel("Operator:")
        op_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        self.filter_operator_combo = CustomSizedComboBox()
        operators = [
            "equals",
            "not equals", 
            "contains",
            "starts with",
            "ends with",
            "greater than",
            "less than",
            "greater or equal",
            "less or equal",
            "is missing",
            "is not missing"
        ]
        self.filter_operator_combo.addItems(operators)
        self.filter_operator_combo.setMaxVisibleItems(10)
        
        # Apply same clean styling with better visibility
        self.filter_operator_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                color: black;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                color: black;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border: none;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 15px;
                border: none;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        if node.filter_operator:
            index = self.filter_operator_combo.findText(node.filter_operator)
            if index >= 0:
                self.filter_operator_combo.setCurrentIndex(index)
        self.filter_operator_combo.currentTextChanged.connect(lambda text: self.on_filter_operator_changed(node, text))
        
        form_layout.addWidget(op_label, 1, 0)
        form_layout.addWidget(self.filter_operator_combo, 1, 1)
        
        # Value input
        val_label = QLabel("Value:")
        val_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        self.filter_value_input = QLineEdit()
        self.filter_value_input.setText(node.filter_value)
        self.filter_value_input.setPlaceholderText("Enter filter value...")
        self.filter_value_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
                color: black;
                font-size: 12px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QLineEdit:disabled {
                background-color: #f0f0f0;
                color: #999;
                border-color: #ddd;
            }
        """)
        self.filter_value_input.editingFinished.connect(lambda: self.update_filter_property(node, 'filter_value', self.filter_value_input.text()))
        
        form_layout.addWidget(val_label, 2, 0)
        form_layout.addWidget(self.filter_value_input, 2, 1)
        
        # Options row
        options_widget = QWidget()
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # Case sensitive checkbox
        self.case_sensitive_checkbox = QCheckBox("🔤 Case Sensitive")
        self.case_sensitive_checkbox.setChecked(node.case_sensitive)
        self.case_sensitive_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #999;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #0078d4;
                border-color: #0078d4;
            }
        """)
        self.case_sensitive_checkbox.toggled.connect(lambda checked: self.update_filter_property(node, 'case_sensitive', checked))
        options_layout.addWidget(self.case_sensitive_checkbox)
        options_layout.addStretch()
        
        form_layout.addWidget(options_widget, 3, 0, 1, 2)
        
        main_filter_layout.addWidget(form_widget)
        
        # Update value field state based on current operator
        self.update_value_field_state(node.filter_operator)
        
        # Add condition button
        add_condition_widget = QWidget()
        add_condition_layout = QHBoxLayout(add_condition_widget)
        add_condition_layout.setContentsMargins(0, 10, 0, 10)
        
        self.add_condition_btn = QPushButton("➕ Add to Combined Conditions")
        self.add_condition_btn.setToolTip("Add current filter condition to combined conditions list")
        self.add_condition_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        self.add_condition_btn.clicked.connect(lambda: self.add_current_condition_to_combined(node))
        add_condition_layout.addWidget(self.add_condition_btn)
        add_condition_layout.addStretch()
        
        main_filter_layout.addWidget(add_condition_widget)
        self.content_layout.addWidget(main_filter_group)
        
        # Multiple conditions toggle
        multiple_toggle_widget = QWidget()
        multiple_toggle_layout = QHBoxLayout(multiple_toggle_widget)
        multiple_toggle_layout.setContentsMargins(15, 10, 15, 10)
        
        self.multiple_conditions_checkbox = QCheckBox("🔗 Enable Multiple Conditions (Advanced)")
        self.multiple_conditions_checkbox.setChecked(node.use_multiple_conditions)
        self.multiple_conditions_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #999;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #0078d4;
                border-color: #0078d4;
            }
        """)
        self.multiple_conditions_checkbox.toggled.connect(lambda checked: self.toggle_multiple_conditions(node, checked))
        multiple_toggle_layout.addWidget(self.multiple_conditions_checkbox)
        multiple_toggle_layout.addStretch()
        
        multiple_toggle_widget.setStyleSheet("""
            QWidget {
                background: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        self.content_layout.addWidget(multiple_toggle_widget)
        
        # Combined conditions group (initially hidden)
        self.combined_conditions_group = QGroupBox("Combined Filter Conditions")
        self.combined_conditions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: white;
            }
        """)
        combined_layout = QVBoxLayout(self.combined_conditions_group)
        
        # Conditions list with fancy styling
        self.conditions_list_widget = QListWidget()
        self.conditions_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #999;
                background: white;
                min-height: 100px;
            }
            QListWidget::item {
                padding: 2px;
            }
            QListWidget::item:selected {
                background: #0078d4;
                color: white;
            }
        """)
        combined_layout.addWidget(self.conditions_list_widget)
        
        # Combined conditions management buttons
        combined_buttons_widget = QWidget()
        combined_buttons_layout = QHBoxLayout(combined_buttons_widget)
        
        clear_combined_btn = QPushButton("🗑️ Clear All")
        clear_combined_btn.setToolTip("Clear all combined conditions")
        clear_combined_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        clear_combined_btn.clicked.connect(lambda: self.clear_combined_conditions(node))
        combined_buttons_layout.addWidget(clear_combined_btn)
        combined_buttons_layout.addStretch()
        
        combined_layout.addWidget(combined_buttons_widget)
        
        # Load existing conditions
        self.refresh_combined_conditions_display(node)
        
        self.content_layout.addWidget(self.combined_conditions_group)
        
        # Output configuration
        output_group = QGroupBox("📊 Output Configuration")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 1px solid #ccc;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        output_layout = QHBoxLayout(output_group)
        
        output_label = QLabel("📤 Output Mode:")
        output_label.setStyleSheet("font-weight: bold; color: #34495e;")
        
        # Create radio buttons for the two options
        self.matching_radio = QRadioButton("🔍 Show Matching Rows")
        self.non_matching_radio = QRadioButton("❌ Show Non-Matching Rows")
        
        # Set default selection
        if node.output_mode == "non-matching":
            self.non_matching_radio.setChecked(True)
        else:
            self.matching_radio.setChecked(True)  # Default to matching
        
        # Style the radio buttons
        radio_style = """
            QRadioButton {
                font-size: 12px;
                color: #333;
                padding: 4px 8px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #ccc;
                border-radius: 10px;
                background: white;
            }
            QRadioButton::indicator:checked {
                background: #0078d4;
                border-color: #0078d4;
            }
            QRadioButton::indicator:checked::after {
                content: '';
                width: 6px;
                height: 6px;
                border-radius: 3px;
                background: white;
                margin: 3px;
            }
            QRadioButton:hover {
                color: #0078d4;
            }
        """
        
        self.matching_radio.setStyleSheet(radio_style)
        self.non_matching_radio.setStyleSheet(radio_style)
        
        # Connect radio button changes
        self.matching_radio.toggled.connect(lambda checked: self.update_filter_property(node, 'output_mode', 'matching') if checked else None)
        self.non_matching_radio.toggled.connect(lambda checked: self.update_filter_property(node, 'output_mode', 'non-matching') if checked else None)
        
        # Create a widget to hold the radio buttons
        radio_widget = QWidget()
        radio_layout = QVBoxLayout(radio_widget)
        radio_layout.setContentsMargins(10, 5, 10, 5)
        radio_layout.setSpacing(8)
        radio_layout.addWidget(self.matching_radio)
        radio_layout.addWidget(self.non_matching_radio)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(radio_widget)
        output_layout.addStretch()
        
        self.content_layout.addWidget(output_group)
        
        # Update UI state based on multiple conditions setting
        self.update_multiple_conditions_ui_state(node.use_multiple_conditions)
        
        # Action buttons group (same style as Column Renamer)
        buttons_group = QGroupBox("🚀 Actions")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button
        apply_execute_btn = QPushButton("✅ Apply and Execute")
        apply_execute_btn.setToolTip("Apply filter settings and execute transformation in one step")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_filter_and_execute(node))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.reset_filter(node))
        buttons_layout.addWidget(cancel_btn)
        
        self.content_layout.addWidget(buttons_group)

        # Check if node has been executed and show result
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
            if output_data is not None:
                result_group = QGroupBox("✨ Filter Results")
                result_group.setStyleSheet("""
                    QGroupBox {
                        color: #27ae60;
                        border: 1px solid #999;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 2px;
                    }
                """)
                result_layout = QVBoxLayout(result_group)
                
                result_info = QLabel(f"✅ Filter applied: {len(output_data)} rows remaining")
                result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                result_layout.addWidget(result_info)
                
                # View filtered data button
                view_btn = QPushButton("👁️ View Filtered Data")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 5px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Filtered Data"))
                result_layout.addWidget(view_btn)
                
                self.content_layout.addWidget(result_group)
        
        self.content_layout.addStretch()
        
    def toggle_multiple_conditions(self, node, enabled):
        """Toggle multiple conditions feature."""
        node.use_multiple_conditions = enabled
        self.update_multiple_conditions_ui_state(enabled)
        
        # Update flow state
        try:
            if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                self._canvas_ref.flow_changed.emit()
            elif hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'flow_changed'):
                self.canvas.flow_changed.emit()
        except Exception as e:
            print(f"Warning: Could not emit flow change signal: {e}")
    
    def update_multiple_conditions_ui_state(self, enabled):
        """Update UI state based on multiple conditions setting."""
        if hasattr(self, 'combined_conditions_group'):
            self.combined_conditions_group.setVisible(enabled)
        
        if hasattr(self, 'add_condition_btn'):
            self.add_condition_btn.setEnabled(enabled)
            if enabled:
                self.add_condition_btn.setText("➕ Add to Combined Conditions")
            else:
                self.add_condition_btn.setText("🔒 Enable Multiple Conditions First")
    
    def add_current_condition_to_combined(self, node):
        """Add the current main condition to the combined conditions list."""
        print(f"🔍 DEBUG: add_current_condition_to_combined called")
        
        # Prevent double execution
        if hasattr(self, '_adding_condition') and self._adding_condition:
            print(f"🔍 DEBUG: Already processing, ignoring duplicate call")
            return
        
        self._adding_condition = True
        
        try:
            if not node.filter_column:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Missing Information", "Please select a column for the condition first.")
                return
            
            # Auto-enable multiple conditions if not enabled
            if not node.use_multiple_conditions:
                node.use_multiple_conditions = True
                if hasattr(self, 'multiple_conditions_checkbox'):
                    self.multiple_conditions_checkbox.setChecked(True)
                self.update_multiple_conditions_ui_state(True)
            
            # Create condition from current main filter settings
            condition = {
                'column': node.filter_column,
                'operator': node.filter_operator,
                'value': node.filter_value,
                'case_sensitive': node.case_sensitive,
                'logic_operator': 'AND'  # Default to AND, user can change later
            }
            
            # Initialize conditions list if needed
            if not hasattr(node, 'conditions'):
                node.conditions = []
            
            # Add condition to list
            node.conditions.append(condition)
            print(f"✅ Added condition to combined list: {condition}")
            print(f"✅ Total conditions now: {len(node.conditions)}")
            
            # Refresh the display
            self.refresh_combined_conditions_display(node)
            
            # Clear main condition form
            self.filter_column_combo.setCurrentIndex(0)
            self.filter_operator_combo.setCurrentIndex(0)
            self.filter_value_input.clear()
            self.case_sensitive_checkbox.setChecked(False)
            
            # Update node properties
            node.filter_column = ""
            node.filter_operator = "equals"
            node.filter_value = ""
            node.case_sensitive = False
            
            # Update flow state
            try:
                if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                    self._canvas_ref.flow_changed.emit()
                elif hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'flow_changed'):
                    self.canvas.flow_changed.emit()
            except Exception as e:
                print(f"Warning: Could not emit flow change signal: {e}")
                
        finally:
            # Reset the processing flag
            self._adding_condition = False
    
    def refresh_combined_conditions_display(self, node):
        """Refresh the combined conditions display."""
        if not hasattr(self, 'conditions_list_widget'):
            return
        
        self.conditions_list_widget.clear()
        
        if hasattr(node, 'conditions') and node.conditions:
            print(f"🔄 Refreshing display with {len(node.conditions)} conditions")
            for i, condition in enumerate(node.conditions):
                # Create list item with custom widget
                item_widget = self.create_condition_item_widget(condition, i, node)
                item = QListWidgetItem()
                
                # Set proper size hint for the item
                item.setSizeHint(item_widget.sizeHint())
                
                self.conditions_list_widget.addItem(item)
                self.conditions_list_widget.setItemWidget(item, item_widget)
                
                print(f"✅ Added condition {i+1}: {condition}")
        else:
            # Add empty state message
            item = QListWidgetItem()
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setContentsMargins(20, 20, 20, 20)
            
            empty_label = QLabel("No conditions added yet")
            empty_label.setStyleSheet("""
                QLabel {
                    color: #a0aec0;
                    font-style: italic;
                    font-size: 12px;
                    text-align: center;
                }
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_label)
            
            item.setSizeHint(empty_widget.sizeHint())
            self.conditions_list_widget.addItem(item)
            self.conditions_list_widget.setItemWidget(item, empty_widget)
            
            print("📭 No conditions to display - showing empty state")
    
    def format_condition_display(self, condition, index):
        """Format condition for display."""
        logic = condition.get('logic_operator', 'AND')
        column = condition.get('column', 'Unknown')
        operator = condition.get('operator', 'equals')
        value = condition.get('value', '')
        case_sensitive = condition.get('case_sensitive', False)
        
        prefix = f"#{index + 1}"
        if index > 0:
            prefix = f"{logic} #{index + 1}"
        
        case_text = " (Case Sensitive)" if case_sensitive else ""
        value_text = f" '{value}'" if value else ""
        
        return f"{prefix}: {column} {operator}{value_text}{case_text}"
    
    def create_condition_item_widget(self, condition, index, node):
        """Create a professional widget for a condition item."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #ccc;
                border-radius: 2px;
                margin: 2px;
            }
            QWidget:hover {
                background: #f5f5f5;
                border-color: #999;
            }
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Logic operator dropdown (for conditions after the first)
        if index > 0:
            logic_combo = CustomSizedComboBox()
            logic_combo.addItems(["AND", "OR"])
            logic_combo.setCurrentText(condition.get('logic_operator', 'AND'))
            logic_combo.setMaxVisibleItems(2)  # Only 2 items
            logic_combo.setStyleSheet("""
                QComboBox {
                    font-weight: normal;
                    color: #333;
                    background: white;
                    border: 1px solid #ccc;
                    border-radius: 2px;
                    padding: 4px 8px;
                    min-width: 45px;
                    font-size: 11px;
                }
                QComboBox:hover {
                    background: #f5f5f5;
                }
                QComboBox QAbstractItemView {
                    background: white;
                    color: #333;
                    font-size: 11px;
                    border: 1px solid #ccc;
                    selection-background-color: #4CAF50;
                    selection-color: white;
                }
                QComboBox QAbstractItemView::item {
                    padding: 6px 8px;
                    margin: 1px;
                    border-radius: 3px;
                }
            """)
            logic_combo.currentTextChanged.connect(lambda text, idx=index: self.update_condition_logic(node, idx, text))
            layout.addWidget(logic_combo)
        
        # Condition text with professional styling
        condition_text = self.format_condition_display(condition, index)
        condition_label = QLabel(condition_text)
        condition_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #333;
                font-weight: normal;
                padding: 4px 8px;
                background: #f0f0f0;
                border-radius: 2px;
                border: 1px solid #ccc;
            }
        """)
        layout.addWidget(condition_label, 1)
        
        # Remove button with professional styling
        remove_btn = QPushButton("✕")
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #e53e3e;
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 2px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #eee;
                border-color: #999;
            }
            QPushButton:pressed {
                background: #ddd;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_condition(node, index))
        layout.addWidget(remove_btn)
        
        return widget
    
    def update_condition_logic(self, node, index, logic_operator):
        """Update the logic operator for a specific condition."""
        if hasattr(node, 'conditions') and 0 <= index < len(node.conditions):
            node.conditions[index]['logic_operator'] = logic_operator
            
            # Update flow state
            try:
                if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                    self._canvas_ref.flow_changed.emit()
                elif hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'flow_changed'):
                    self.canvas.flow_changed.emit()
            except Exception as e:
                print(f"Warning: Could not emit flow change signal: {e}")
            
            print(f"✅ Updated condition {index} logic to: {logic_operator}")
    
    def remove_condition(self, node, index):
        """Remove a condition from the combined list."""
        if hasattr(node, 'conditions') and 0 <= index < len(node.conditions):
            removed_condition = node.conditions.pop(index)
            self.refresh_combined_conditions_display(node)
            
            # Update flow state
            if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                self._canvas_ref.flow_changed.emit()
            
            print(f"✅ Removed condition: {removed_condition}")
    
    def clear_combined_conditions(self, node):
        """Clear all combined conditions."""
        if hasattr(node, 'conditions'):
            node.conditions.clear()
            self.refresh_combined_conditions_display(node)
            
            # Update flow state
            if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                self._canvas_ref.flow_changed.emit()
            
            print("✅ Cleared all combined conditions")
        
    def on_filter_operator_changed(self, node, operator_text):
        """Handle operator change and update value field state."""
        self.update_filter_property(node, 'filter_operator', operator_text)
        self.update_value_field_state(operator_text)
        
    def update_value_field_state(self, operator):
        """Enable/disable value field based on operator."""
        if hasattr(self, 'filter_value_input'):
            # Operators that don't need a value
            no_value_operators = ["is missing", "is not missing"]
            
            if operator in no_value_operators:
                # Grey out and disable the value field
                self.filter_value_input.setEnabled(False)
                self.filter_value_input.setStyleSheet("background-color: #f0f0f0; color: #888888;")
                self.filter_value_input.setPlaceholderText("(No value required)")
                self.filter_value_input.clear()
            else:
                # Enable and restore normal appearance
                self.filter_value_input.setEnabled(True)
                self.filter_value_input.setStyleSheet("")
                self.filter_value_input.setPlaceholderText("Enter filter value...")
        
    def update_filter_property(self, node, property_name, value):
        """Update a filter property and save the node state."""
        setattr(node, property_name, value)
        print(f"🔧 Updated {property_name} to: {value}")
        
        # Trigger flow change notification for auto-save
        if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
            self._canvas_ref.flow_changed.emit()
            
    def apply_filter_and_execute(self, node):
        """Apply the filter configuration and execute the node."""
        # Check if we have either a primary filter or combined conditions
        has_primary_filter = bool(node.filter_column)
        has_combined_conditions = bool(getattr(node, 'conditions', []))
        
        if not has_primary_filter and not has_combined_conditions:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Configuration Required", "Please configure at least one filter condition.")
            return
            
        # Check if primary filter value is required but missing
        if has_primary_filter:
            no_value_operators = ["is missing", "is not missing"]
            if node.filter_operator not in no_value_operators and not node.filter_value.strip():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Configuration Required", f"Please enter a filter value for '{node.filter_operator}' operation.")
                return
            
        # Trigger execution via the execution engine
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            try:
                print("🚀 ROW FILTER: Starting execution...")
                
                # Execute and wait for completion
                execution_engine.execute_flow()
                print("✅ Row filter executed successfully")
                
                # IMMEDIATE REFRESH: Get the output data and emit signal
                output_data = execution_engine.get_node_output_data(node)
                print(f"🔄 ROW FILTER REFRESH: Got output data: {output_data.shape if output_data is not None else 'None'}")
                
                # Force immediate data refresh - FIRST ATTEMPT
                print("🔄 AUTOMATIC REFRESH: Emitting data refresh signal for Row Filter (FIRST)")
                self.data_refresh_requested.emit(node)
                
                # Use QTimer for a second refresh attempt to ensure it works
                from PyQt6.QtCore import QTimer
                def second_refresh():
                    print("🔄 AUTOMATIC REFRESH: Emitting data refresh signal for Row Filter (SECOND)")
                    self.data_refresh_requested.emit(node)
                    print("🔄 AUTOMATIC REFRESH: Signal emitted - data viewer should update automatically")
                
                # Second refresh after 50ms to ensure first execution completes
                QTimer.singleShot(50, second_refresh)
                
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Execution Error", f"Failed to execute filter: {str(e)}")
        else:
            print("⚠️ Cannot execute - no execution engine available")
            
    def reset_filter(self, node):
        """Reset all filter settings to defaults."""
        node.filter_column = ""
        node.filter_operator = "equals"
        node.filter_value = ""
        node.case_sensitive = False
        node.output_mode = "matching"
        node.conditions = []
        node.logic_operator = "AND"
        
        # Update UI
        if hasattr(self, 'filter_column_combo'):
            self.filter_column_combo.setCurrentIndex(0)
        if hasattr(self, 'filter_operator_combo'):
            self.filter_operator_combo.setCurrentText("equals")
        if hasattr(self, 'filter_value_input'):
            self.filter_value_input.clear()
            self.update_value_field_state("equals")  # Reset value field state
        if hasattr(self, 'case_sensitive_checkbox'):
            self.case_sensitive_checkbox.setChecked(False)
        if hasattr(self, 'output_mode_combo'):
            self.output_mode_combo.setCurrentText("matching")
        if hasattr(self, 'logic_operator_combo'):
            self.logic_operator_combo.setCurrentText("AND")
        if hasattr(self, 'conditions_table'):
            self.conditions_table.setRowCount(0)
            
        print("🔄 Filter settings reset to defaults")
        
        # Trigger flow change notification
        if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
            self._canvas_ref.flow_changed.emit()
            
    def apply_expression_and_execute(self, node):
        """Apply the expression configuration and execute the node."""
        # Check target column is selected
        if not hasattr(node, 'target_column') or not node.target_column:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Configuration Required", "Please select a target column.")
            return
            
        # Check function type is selected
        if not hasattr(node, 'function_type') or not node.function_type:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Configuration Required", "Please select a function type.")
            return
            
        # For append mode, check new column name
        if hasattr(node, 'operation_mode') and node.operation_mode == 'append':
            if not hasattr(node, 'new_column_name') or not node.new_column_name.strip():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Configuration Required", "Please enter a new column name for append mode.")
                return
            
        # Only require expression for functions that need parameters
        functions_needing_params = ["substr", "scan", "compress", "catx", "custom"]
        if node.function_type in functions_needing_params:
            if not hasattr(node, 'expression') or not node.expression.strip():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Configuration Required", f"Please enter parameters for {node.function_type} function.")
                return
            
        # Trigger execution via the execution engine
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            try:
                execution_engine.execute_flow()
                print("✅ Expression builder executed successfully")
                # Emit signal to refresh data viewer
                self.data_refresh_requested.emit(node)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Execution Error", f"Failed to execute expression: {str(e)}")
        else:
            print("⚠️ Cannot execute - no execution engine available")
            
    def reset_expression(self, node):
        """Reset expression settings to defaults."""
        node.expression = ""
        node.new_column_name = ""
        
        # Update UI
        if hasattr(self, 'expression_edit'):
            self.expression_edit.clear()
        if hasattr(self, 'column_name_edit'):
            self.column_name_edit.clear()
            
        print("🔄 Expression settings reset to defaults")
        
        # Trigger flow change notification
        if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
            self._canvas_ref.flow_changed.emit()
        
        
    def create_conditional_mapping_properties(self, node):
        """Create properties for conditional mapping nodes with support for multiple configurations."""
        print(f"🗂️ Creating conditional mapping properties for: {node.title}")
        
        # Initialize multiple mapping configs if not exists
        if not hasattr(node, 'mapping_configs'):
            node.mapping_configs = []
            
        # Migrate legacy properties to new structure if needed
        if hasattr(node, 'source_column') and node.source_column and not node.mapping_configs:
            legacy_config = {
                "id": 1,
                "name": "Mapping 1",
                "source_column": node.source_column,
                "target_column": node.target_column,
                "mappings": node.mappings,
                "default_value": node.default_value,
                "operation_mode": getattr(node, 'operation_mode', 'add_column'),
                "ct_selection": getattr(node, 'ct_selection', None)  # Include CT selection in migration
            }
            node.mapping_configs = [legacy_config]
        
        # Ensure at least one mapping config exists
        if not node.mapping_configs:
            node.mapping_configs = [{
                "id": 1,
                "name": "Mapping 1",
                "source_column": "",
                "target_column": "",
                "mappings": [],
                "default_value": "",
                "operation_mode": "add_column",
                "ct_selection": None  # Initialize CT selection for new configs
            }]
        
        # Get available columns from connected input nodes
        available_columns = self.get_available_columns_for_node(node)
        print(f"📊 Available columns for mapping: {available_columns}")
        
        # Connection status header
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        if available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            status_icon = QLabel("🔗")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel(f"Connected - {len(available_columns)} columns available")
            status_text.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            status_icon = QLabel("⚠️")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel("No input connection detected")
            status_text.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 14px;")
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        status_widget.setStyleSheet("""
            QWidget {
                background: #f0f0f0;
                border: 1px solid #999;
            }
        """)
        self.content_layout.addWidget(status_widget)
        
        # Multiple Configurations Management
        configs_header = QWidget()
        configs_header_layout = QHBoxLayout(configs_header)
        configs_header_layout.setContentsMargins(10, 10, 10, 10)
        
        configs_title = QLabel(f"📋 Mapping Configurations ({len(node.mapping_configs)})")
        configs_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        
        add_config_btn = QPushButton("➕ Add Configuration")
        add_config_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        add_config_btn.setToolTip("Add a new mapping configuration for another column")
        add_config_btn.clicked.connect(lambda: self.add_mapping_configuration(node))
        
        configs_header_layout.addWidget(configs_title)
        configs_header_layout.addStretch()
        configs_header_layout.addWidget(add_config_btn)
        
        configs_header.setStyleSheet("""
            QWidget {
                background: #e8f5e8;
                border: 2px solid #28a745;
                border-radius: 5px;
            }
        """)
        self.content_layout.addWidget(configs_header)
        
        # Create accordion-style sections for each configuration
        self.config_sections = []
        for i, config in enumerate(node.mapping_configs):
            self.create_mapping_configuration_section(node, config, i, available_columns)
        
        # Apply Configuration Section (matching Row Filter style)
        buttons_group = QGroupBox("🎯 Apply Configuration")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button (matching Row Filter exactly)
        apply_execute_btn = QPushButton("✅ Apply and Execute")
        apply_execute_btn.setToolTip("Apply all mapping configurations and execute transformation in one step")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_and_execute_conditional_mapping(node))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button (matching Row Filter exactly)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.cancel_conditional_mapping(node))
        buttons_layout.addWidget(cancel_btn)
        
        self.content_layout.addWidget(buttons_group)
        
        # Add conditional mapping results section (matching Expression node pattern exactly)
        self.add_conditional_mapping_results_section(node)


    def add_conditional_mapping_results_section(self, node):
        """Add conditional mapping results section (matching Expression node pattern exactly)."""
        # Check if node has been executed and show result (same pattern as Expression)
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
            if output_data is not None:
                result_group = QGroupBox("🔄 Conditional Mapping Results")
                result_group.setStyleSheet("""
                    QGroupBox {
                        color: #27ae60;
                        border: 1px solid #999;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 2px;
                    }
                """)
                result_layout = QVBoxLayout(result_group)
                
                result_info = QLabel(f"✅ Conditional mapping applied: {len(output_data)} rows processed")
                result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                result_layout.addWidget(result_info)
                
                # View transformed data button (matching Expression exactly)
                view_btn = QPushButton("👁️ View Transformed Data")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 5px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Conditional Mapping Transformed Data"))
                result_layout.addWidget(view_btn)
                
                self.content_layout.addWidget(result_group)


    def on_text_editing_finished(self, node):
        """Handle text editing finished (focus loss or Enter key) - emit flow change."""
        print(f"🗂️ Text editing finished for node: {node.title}")
        if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
            self._canvas_ref.flow_changed.emit()

    def on_source_column_changed(self, node, column_name):
        """Handle source column selection change."""
        node.source_column = column_name
        print(f"🗂️ Source column changed to: {column_name}")
        if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
            self._canvas_ref.flow_changed.emit()
    
    def on_target_column_changed(self, node, column_name):
        """Handle target column name change."""
        node.target_column = column_name
        print(f"🗂️ Target column changed to: {column_name}")
        # Don't emit flow change for text editing - only on Enter/focus loss
        # if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
        #     self._canvas_ref.flow_changed.emit()
    
    def on_operation_mode_changed(self, node, mode):
        """Handle operation mode change."""
        node.operation_mode = mode
        print(f"🗂️ Operation mode changed to: {mode}")
        if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
            self._canvas_ref.flow_changed.emit()
    
    def on_default_value_changed(self, node, value):
        """Handle default value change."""
        node.default_value = value
        print(f"🗂️ Default value changed to: {value}")
        # Don't emit flow change for text editing - only on Enter/focus loss
        # if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
        #     self._canvas_ref.flow_changed.emit()
    
    def on_mapping_changed(self, node):
        """Handle mapping table changes."""
        mappings = []
        for row in range(self.mapping_table.rowCount()):
            condition_item = self.mapping_table.item(row, 0)
            result_item = self.mapping_table.item(row, 1)
            if condition_item and result_item:
                condition_text = condition_item.text().strip()
                result_text = result_item.text().strip()
                # Only add non-empty mappings
                if condition_text or result_text:
                    mappings.append({
                        'condition': condition_text,
                        'result': result_text
                    })
        node.mappings = mappings
        print(f"🗂️ Mappings updated: {len(mappings)} conditions")
        # Don't emit flow change for table editing - causes constant refreshes
        # if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
        #     self._canvas_ref.flow_changed.emit()
    
    def add_mapping_row(self, node):
        """Add a new mapping row to the table."""
        print(f"🗂️ Add mapping button clicked!")
        row_count = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row_count)
        
        # Create new empty items
        condition_item = QTableWidgetItem("")
        result_item = QTableWidgetItem("")
        
        self.mapping_table.setItem(row_count, 0, condition_item)
        self.mapping_table.setItem(row_count, 1, result_item)
        
        # Update the node mappings and trigger change notification
        self.on_mapping_changed(node)
        
        print(f"🗂️ Added new mapping row at position {row_count}, total rows: {self.mapping_table.rowCount()}")
        
        # Focus on the new condition cell for immediate editing
        self.mapping_table.setCurrentCell(row_count, 0)
        self.mapping_table.editItem(condition_item)
    
    def remove_mapping_row(self, node):
        """Remove selected mapping row from the table."""
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)
            self.on_mapping_changed(node)  # Update node mappings
            print(f"🗂️ Removed mapping row {current_row}")
        else:
            print("🗂️ No row selected for removal")

    def create_generic_properties(self, node):
        """Create generic properties for unknown node types."""
        # Node info group
        info_group = QGroupBox("Node Information")
        info_layout = QFormLayout(info_group)
        
        title_label = QLabel(node.get_display_name())
        title_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Display Name:", title_label)
        
        type_label = QLabel(node.__class__.__name__)
        info_layout.addRow("Type:", type_label)
        
        self.content_layout.addWidget(info_group)
        
        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)
        
        if hasattr(node, 'parameters'):
            for key, value in node.parameters.items():
                param_edit = QLineEdit(str(value))
                param_edit.textChanged.connect(
                    lambda text, k=key: self.update_node_parameter(k, text)
                )
                params_layout.addRow(f"{key}:", param_edit)
        else:
            no_params_label = QLabel("No configurable parameters")
            no_params_label.setStyleSheet("color: #888888; font-style: italic;")
            params_layout.addRow(no_params_label)
            
        self.content_layout.addWidget(params_group)
        self.content_layout.addStretch()
        
    def update_node_property(self, property_name, value):
        """Update a node property."""
        if self.current_node and hasattr(self.current_node, property_name):
            setattr(self.current_node, property_name, value)
            self.property_changed.emit(property_name, value)
            
    def update_node_parameter(self, parameter_name, value):
        """Update a node parameter."""
        if self.current_node and hasattr(self.current_node, 'parameters'):
            self.current_node.parameters[parameter_name] = value
            self.property_changed.emit(f"parameter_{parameter_name}", value)
    
    def get_execution_engine(self, node):
        """Get the execution engine from the node's canvas with fallback methods."""
        # Method 1: Direct canvas reference
        if hasattr(node, 'canvas') and node.canvas:
            engine = getattr(node.canvas, 'execution_engine', None)
            if engine:
                return engine
        
        # Method 2: Try to find canvas through scene
        if hasattr(node, 'scene') and node.scene():
            for view in node.scene().views():
                if hasattr(view, 'execution_engine'):
                    return view.execution_engine
        
        # Method 3: Search through parent widgets to find main window
        try:
            from PyQt6.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'flow_canvas') and hasattr(widget.flow_canvas, 'execution_engine'):
                    return widget.flow_canvas.execution_engine
        except:
            pass
        
        return None
    
    def view_node_data(self, node, dataframe, title):
        """Open a data viewer window for the node's data."""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
            
            # Create data viewer dialog
            dialog = QDialog()
            dialog.setWindowTitle(f"{title} - {node.get_display_name()}")
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Info header
            info_label = QLabel(f"📊 {title} for {node.get_display_name()}\n"
                              f"Rows: {len(dataframe)} | Columns: {len(dataframe.columns)}")
            info_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
            layout.addWidget(info_label)
            
            # Data table
            table = QTableWidget()
            
            # Limit to first 1000 rows for performance
            display_df = dataframe.head(1000)
            
            table.setRowCount(len(display_df))
            table.setColumnCount(len(display_df.columns))
            
            # Set headers
            table.setHorizontalHeaderLabels(display_df.columns.tolist())
            
            # Fill data
            for row in range(len(display_df)):
                for col in range(len(display_df.columns)):
                    value = str(display_df.iloc[row, col])
                    item = QTableWidgetItem(value)
                    table.setItem(row, col, item)
            
            # Configure table
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            
            layout.addWidget(table)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            # Export button
            export_btn = QPushButton("💾 Export to CSV")
            export_btn.clicked.connect(lambda: self.export_dataframe(dataframe, f"{node.title}_{title}"))
            button_layout.addWidget(export_btn)
            
            # Close button
            close_btn = QPushButton("❌ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            # Show dialog
            dialog.exec()
            
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Export Error")
            msg.setText(f"Failed to export data: {e}")
            msg.exec()
    
    def apply_rename_mappings(self, node):
        """Apply current rename mappings to the node with validation."""
        try:
            print(f"🔧 APPLY: Applying rename mappings to {node.title}")
            print(f"🔧 APPLY: Table has {self.rename_table.rowCount()} rows")
            
            # Get input data to check existing columns
            input_data = None
            if hasattr(self, 'main_window') and self.main_window.execution_engine:
                input_data = self.main_window.execution_engine.get_node_input_data(node)
            
            existing_columns = set()
            if input_data is not None:
                existing_columns = set(input_data.columns)
                print(f"🔧 VALIDATE: Found existing columns: {existing_columns}")
            
            # Clear existing mappings
            node.rename_mappings.clear()
            
            # Collect and validate mappings from table
            new_column_names = set()
            mappings_to_apply = {}
            validation_errors = []
            
            for row in range(self.rename_table.rowCount()):
                # Get the combo box and line edit widgets
                old_combo = self.rename_table.cellWidget(row, 0)
                new_edit = self.rename_table.cellWidget(row, 1)
                
                if old_combo and new_edit:
                    original_name = old_combo.currentText().strip()
                    new_name = new_edit.text().strip()
                    
                    print(f"🔧 APPLY: Row {row}: '{original_name}' → '{new_name}'")
                    
                    if original_name and new_name and original_name != new_name:
                        # Validation 1: Check if new name already exists in original columns
                        if new_name in existing_columns and new_name != original_name:
                            validation_errors.append(f"❌ Row {row + 1}: Cannot rename '{original_name}' to '{new_name}' - column '{new_name}' already exists!")
                            continue
                        
                        # Validation 2: Check for duplicate new names in this rename operation
                        if new_name in new_column_names:
                            validation_errors.append(f"❌ Row {row + 1}: Duplicate new column name '{new_name}' - each new name must be unique!")
                            continue
                        
                        # Validation 3: Check if trying to rename to a name that another column is being renamed to
                        if new_name in mappings_to_apply.values():
                            validation_errors.append(f"❌ Row {row + 1}: Cannot rename '{original_name}' to '{new_name}' - another column is already being renamed to this name!")
                            continue
                        
                        mappings_to_apply[original_name] = new_name
                        new_column_names.add(new_name)
                        print(f"🔧 APPLY: Valid mapping: {original_name} → {new_name}")
                    else:
                        print(f"🔧 APPLY: Skipped row {row} - invalid or unchanged mapping")
            
            # Show validation errors if any
            if validation_errors:
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("Validation Errors")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("❌ Column rename validation failed!")
                msg.setInformativeText("\n".join(validation_errors))
                msg.setDetailedText("Please fix these issues:\n\n" + "\n".join([
                    "• Cannot rename to existing column names",
                    "• Each new column name must be unique",
                    "• Cannot have duplicate target names in the same operation"
                ]))
                msg.exec()
                return
            
            # Apply valid mappings
            node.rename_mappings.update(mappings_to_apply)
            
            print(f"🔧 APPLY: Total mappings applied: {len(node.rename_mappings)}")
            print(f"🔧 APPLY: Final mappings: {node.rename_mappings}")
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Mappings Applied")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"✅ Applied {len(node.rename_mappings)} column rename mappings to {node.get_display_name()}")
            msg.setInformativeText("Click 'Execute Transform' to apply these changes to the data.")
            msg.exec()
            
        except Exception as e:
            print(f"❌ APPLY ERROR: {e}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Apply Error")
            msg.setText(f"Failed to apply mappings: {e}")
            msg.exec()
    
    def apply_and_execute_transformation(self, node):
        """Combined apply and execute - validates mappings and runs transformation in one step."""
        try:
            print(f"🚀 APPLY & EXECUTE: Starting combined operation for {node.title}")
            
            # Step 1: Apply and validate mappings (without showing success dialog)
            if not self.apply_rename_mappings_silent(node):
                return  # Validation failed, error already shown
            
            # Step 2: Execute the transformation
            print(f"🚀 APPLY & EXECUTE: Mappings applied, now executing transformation")
            self.execute_node_transformation(node)
            
            # Step 3: Ensure automatic data refresh happens
            print("🔄 APPLY & EXECUTE: Ensuring data viewer refresh")
            self.data_refresh_requested.emit(node)
            print("🔄 APPLY & EXECUTE: Data refresh signal emitted - viewer should update automatically")
            
        except Exception as e:
            print(f"❌ APPLY & EXECUTE ERROR: {e}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Apply & Execute Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"❌ Failed to apply and execute transformation")
            msg.setInformativeText(f"Error: {str(e)}")
            msg.exec()
    
    def apply_rename_mappings_silent(self, node):
        """Apply rename mappings with validation but without success dialog."""
        try:
            print(f"🔧 APPLY (SILENT): Applying rename mappings to {node.title}")
            print(f"🔧 APPLY (SILENT): Table has {self.rename_table.rowCount()} rows")
            
            # Get input data to check existing columns
            input_data = None
            if hasattr(self, 'main_window') and self.main_window.execution_engine:
                input_data = self.main_window.execution_engine.get_node_input_data(node)
            
            existing_columns = set()
            if input_data is not None:
                existing_columns = set(input_data.columns)
                print(f"🔧 VALIDATE: Found existing columns: {existing_columns}")
            
            # Clear existing mappings
            node.rename_mappings.clear()
            
            # Collect and validate mappings from table
            new_column_names = set()
            mappings_to_apply = {}
            validation_errors = []
            
            for row in range(self.rename_table.rowCount()):
                # Get the combo box and line edit widgets
                old_combo = self.rename_table.cellWidget(row, 0)
                new_edit = self.rename_table.cellWidget(row, 1)
                
                if old_combo and new_edit:
                    original_name = old_combo.currentText().strip()
                    new_name = new_edit.text().strip()
                    
                    print(f"🔧 APPLY (SILENT): Row {row}: '{original_name}' → '{new_name}'")
                    
                    if original_name and new_name and original_name != new_name:
                        # Validation 1: Check if new name already exists in original columns
                        if new_name in existing_columns and new_name != original_name:
                            validation_errors.append(f"❌ Row {row + 1}: Cannot rename '{original_name}' to '{new_name}' - column '{new_name}' already exists!")
                            continue
                        
                        # Validation 2: Check for duplicate new names in this rename operation
                        if new_name in new_column_names:
                            validation_errors.append(f"❌ Row {row + 1}: Duplicate new column name '{new_name}' - each new name must be unique!")
                            continue
                        
                        # Validation 3: Check if trying to rename to a name that another column is being renamed to
                        if new_name in mappings_to_apply.values():
                            validation_errors.append(f"❌ Row {row + 1}: Cannot rename '{original_name}' to '{new_name}' - another column is already being renamed to this name!")
                            continue
                        
                        mappings_to_apply[original_name] = new_name
                        new_column_names.add(new_name)
                        print(f"🔧 APPLY (SILENT): Valid mapping: {original_name} → {new_name}")
                    else:
                        print(f"🔧 APPLY (SILENT): Skipped row {row} - invalid or unchanged mapping")
            
            # Show validation errors if any
            if validation_errors:
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("Column Rename Validation Errors")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("❌ Column rename validation failed!")
                msg.setInformativeText("\n".join(validation_errors))
                msg.setDetailedText("Please fix these issues:\n\n" + "\n".join([
                    "• Cannot rename to existing column names",
                    "• Each new column name must be unique",
                    "• Cannot have duplicate target names in the same operation"
                ]))
                msg.exec()
                return False
            
            # Apply valid mappings
            node.rename_mappings.update(mappings_to_apply)
            
            print(f"🔧 APPLY (SILENT): Total mappings applied: {len(node.rename_mappings)}")
            print(f"🔧 APPLY (SILENT): Final mappings: {node.rename_mappings}")
            
            return True
            
        except Exception as e:
            print(f"❌ APPLY (SILENT) ERROR: {e}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Apply Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"❌ Failed to apply rename mappings")
            msg.setInformativeText(f"Error: {str(e)}")
            msg.exec()
            return False

    def execute_node_transformation(self, node):
        """Execute the transformation for this specific node."""
        try:
            print(f"🚀 EXECUTE: Starting transformation for {node.title}")
            
            # Get execution engine
            execution_engine = self.get_execution_engine(node)
            print(f"🚀 EXECUTE: Found execution engine: {execution_engine}")
            
            if not execution_engine:
                # Try to get it from main window directly
                from PyQt6.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'flow_canvas'):
                        canvas = widget.flow_canvas
                        if hasattr(canvas, 'execution_engine'):
                            execution_engine = canvas.execution_engine
                            print(f"🚀 EXECUTE: Found engine via main window: {execution_engine}")
                            break
                        else:
                            # Create a new one if none exists
                            from data.execution_engine import FlowExecutionEngine
                            execution_engine = FlowExecutionEngine(canvas)
                            canvas.execution_engine = execution_engine
                            print(f"🚀 EXECUTE: Created new execution engine: {execution_engine}")
                            break
            
            if not execution_engine:
                raise Exception("No execution engine available and could not create one")
            
            print(f"🚀 EXECUTE: Node mappings before execution: {getattr(node, 'rename_mappings', {})}")
            
            # Execute just this node
            success = execution_engine.execute_node(node)
            print(f"🚀 EXECUTE: Node execution result: {success}")
            
            if success:
                print(f"🚀 EXECUTE: Successfully executed {node.title}")
                
                # Get the transformed data immediately after execution
                output_data = execution_engine.get_node_output_data(node)
                print(f"🚀 EXECUTE: Output data shape: {output_data.shape if output_data is not None else 'None'}")
                
                # FIRST: Emit signal to refresh data viewer BEFORE showing success dialog
                print("🔄 FIRST REFRESH: Emitting data refresh signal immediately after execution")
                self.data_refresh_requested.emit(node)
                
                # Force a small delay to ensure signal processing
                from PyQt6.QtCore import QTimer
                def delayed_success_dialog():
                    # Show success message with results
                    from PyQt6.QtWidgets import QMessageBox
                    msg = QMessageBox()
                    msg.setWindowTitle("Transformation Complete")
                    
                    if output_data is not None:
                        msg.setText(f"✅ Successfully executed {node.get_display_name()}")
                        msg.setInformativeText(f"Output: {len(output_data)} rows, {len(output_data.columns)} columns\n"
                                             f"Applied {len(getattr(node, 'rename_mappings', {})) } column renames\n"
                                             f"Columns: {list(output_data.columns)[:5]}...")
                    else:
                        msg.setText(f"✅ Node executed but no output data available")
                    
                    msg.exec()
                    
                    # SECOND: Emit signal again after dialog to ensure refresh
                    print("🔄 SECOND REFRESH: Emitting data refresh signal after dialog")
                    self.data_refresh_requested.emit(node)
                
                # Execute success dialog after a short delay
                QTimer.singleShot(100, delayed_success_dialog)
                self.data_refresh_requested.emit(node)
                
                # Refresh the property panel to show updated status
                self.refresh_current_node()
                
            else:
                # Get the specific error from execution engine
                error_msg = "Node execution failed"
                if execution_engine and hasattr(execution_engine, 'get_last_error'):
                    specific_error = execution_engine.get_last_error()
                    if specific_error:
                        error_msg = specific_error
                
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"❌ EXECUTE ERROR: {e}")
            import traceback
            traceback.print_exc()
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Execution Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            
            # Show the actual error message from validation
            error_text = str(e)
            if "Column rename validation failed" in error_text:
                # Extract the validation errors
                validation_part = error_text.split("Column rename validation failed:\n", 1)[1] if "Column rename validation failed:\n" in error_text else error_text
                msg.setText("❌ Column Rename Validation Failed")
                msg.setInformativeText("The following validation errors must be fixed:")
                msg.setDetailedText(validation_part)
            else:
                msg.setText(f"❌ Failed to execute transformation")
                msg.setInformativeText(f"Error: {error_text}")
            
            msg.exec()
    
    def cancel_changes(self, node):
        """Cancel current changes and revert to saved state."""
        try:
            print(f"❌ CANCEL: Reverting changes for {node.title}")
            
            # Clear the table
            self.rename_table.setRowCount(0)
            
            # Reload saved mappings
            for old_name, new_name in node.rename_mappings.items():
                available_columns = self.get_available_columns_for_node(node)
                self.add_rename_mapping_row(old_name, new_name, available_columns)
            
            print(f"❌ CANCEL: Reverted to {len(node.rename_mappings)} saved mappings")
            
            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Changes Cancelled")
            msg.setText("❌ Reverted all unsaved changes")
            msg.exec()
            
        except Exception as e:
            print(f"❌ CANCEL ERROR: {e}")
    
    def refresh_current_node(self):
        """Refresh the property panel for the currently selected node."""
        try:
            if hasattr(self, 'current_node') and self.current_node:
                print(f"🔄 REFRESH: Refreshing properties for {self.current_node.title}")
                self.set_node(self.current_node)
        except Exception as e:
            print(f"❌ REFRESH ERROR: {e}")

    def export_dataframe(self, dataframe, suggested_name):
        """Export dataframe to CSV."""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Export Data",
                f"{suggested_name}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                dataframe.to_csv(file_path, index=False)
                QMessageBox.information(None, "✅ Export Successful", 
                                      f"Data exported successfully to:\n{file_path}")
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "❌ Export Error", f"Failed to export data:\n{str(e)}")
    
    def show_no_data_message(self, message):
        """Show a message dialog when data is not available."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, "⚠️ No Data Available", message)
    
    # ===== STANDARDIZED METHODS FOR COLUMN RENAMER NODE (matching DomainNode template) =====
    
    def apply_and_execute_renamer(self, node):
        """Apply and execute renamer transformation (matching DomainNode template exactly)."""
        try:
            print(f"🚀 RENAMER APPLY & EXECUTE: Starting combined operation for {node.title}")
            
            # Step 1: Apply and validate mappings (without showing success dialog)
            if not self.apply_rename_mappings_silent(node):
                return  # Validation failed, error already shown
            
            # Step 2: Execute the transformation
            print(f"🚀 RENAMER APPLY & EXECUTE: Mappings applied, now executing transformation")
            self.execute_node_transformation(node)
            
            # Step 3: Update UI status
            if hasattr(self, 'renamer_result_label'):
                self.renamer_result_label.setText("✅ Column renaming completed successfully")
                self.renamer_result_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px; border: 1px solid #27ae60; border-radius: 4px; background-color: #f8fff8;")
            
            # Step 4: Ensure automatic data refresh happens
            print("🔄 RENAMER APPLY & EXECUTE: Ensuring data viewer refresh")
            self.data_refresh_requested.emit(node)
            
            # Step 5: Emit refresh signal for property panel (like domain node)
            print("🔄 REFRESH: Refreshing properties for {node.title}")
            if hasattr(self, 'current_node') and self.current_node:
                self.set_node(self.current_node)
            
            print("🔄 RENAMER APPLY & EXECUTE: Data refresh signal emitted - viewer should update automatically")
            
        except Exception as e:
            print(f"❌ RENAMER APPLY & EXECUTE ERROR: {e}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Apply & Execute Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"❌ Failed to apply and execute column renaming")
            msg.setInformativeText(f"Error: {str(e)}")
            msg.exec()
    
    def cancel_renamer_changes(self, node):
        """Cancel renamer changes (matching DomainNode template exactly)."""
        try:
            print(f"❌ RENAMER CANCEL: Reverting changes for {node.title}")
            
            # Clear the table
            if hasattr(self, 'rename_table'):
                self.rename_table.setRowCount(0)
            
            # Reload saved mappings
            for old_name, new_name in node.rename_mappings.items():
                available_columns = self.get_available_columns_for_node(node)
                self.add_rename_mapping_row(old_name, new_name, available_columns)
            
            # Reset UI status
            if hasattr(self, 'renamer_result_label'):
                self.renamer_result_label.setText("🔄 Ready to rename columns when mappings are configured")
                self.renamer_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
            
            # Clear suffix inputs and checkboxes
            if hasattr(self, 'suffix_input'):
                self.suffix_input.clear()
            if hasattr(self, 'suffix_checkboxes'):
                self.toggle_all_checkboxes(False)
            if hasattr(self, 'column_search_input'):
                self.column_search_input.clear()
                self.filter_column_checkboxes()
            
            print(f"❌ RENAMER CANCEL: Reverted to {len(node.rename_mappings)} saved mappings")
            
            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Changes Cancelled")
            msg.setText("❌ Reverted all unsaved changes")
            msg.setInformativeText("All mappings and checkbox selections have been reset to their saved state.")
            msg.exec()
            
        except Exception as e:
            print(f"❌ RENAMER CANCEL ERROR: {e}")
    
    def add_renamer_results_section(self, node, layout):
        """Add renamer results section (matching DomainNode pattern exactly)."""
        # Check if node has been executed and show result (same pattern as Domain)
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
            if output_data is not None:
                result_group = QGroupBox("🏷️ Rename Results")
                result_group.setStyleSheet("""
                    QGroupBox {
                        color: #27ae60;
                        border: 1px solid #999;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 2px;
                    }
                """)
                result_layout = QVBoxLayout(result_group)
                
                # Count renamed columns
                renamed_count = len(node.rename_mappings) if hasattr(node, 'rename_mappings') else 0
                result_info = QLabel(f"✅ Columns renamed: {renamed_count} mappings applied to {len(output_data)} rows")
                result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                result_layout.addWidget(result_info)
                
                # Show mapping summary
                if hasattr(node, 'rename_mappings') and node.rename_mappings:
                    mapping_summary = QLabel("Mappings applied: " + ", ".join([f"{old}→{new}" for old, new in list(node.rename_mappings.items())[:3]]) + 
                                           (f" and {len(node.rename_mappings)-3} more..." if len(node.rename_mappings) > 3 else ""))
                    mapping_summary.setWordWrap(True)
                    mapping_summary.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
                    result_layout.addWidget(mapping_summary)
                
                # View transformed data button (matching DomainNode exactly)
                view_btn = QPushButton("👁️ View Transformed Data")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 5px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Column Renamed Data"))
                result_layout.addWidget(view_btn)
                
                layout.addWidget(result_group)
    
    def apply_constant_value_and_execute(self, node):
        """Apply constant value column settings and execute transformation."""
        try:
            print(f"🔢 CONSTANT VALUE: Applying settings for node: {node.title}")
            
            # Validate inputs
            if not node.column_name.strip():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "⚠️ Configuration Required", "Please enter a column name.")
                return
                
            # Trigger execution via the execution engine
            execution_engine = self.get_execution_engine(node)
            if execution_engine:
                try:
                    execution_engine.execute_flow()
                    print("✅ Constant value column executed successfully")
                    # Emit signal to refresh data viewer
                    self.data_refresh_requested.emit(node)
                except Exception as e:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(None, "Execution Error", f"Failed to execute constant value column: {str(e)}")
            else:
                print("⚠️ Cannot execute - no execution engine available")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "⚠️ No Execution Engine", "Cannot execute - no execution engine available")
            
        except Exception as e:
            print(f"❌ CONSTANT VALUE APPLY ERROR: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "❌ Error", f"Failed to apply constant value:\n{str(e)}")
    
    def cancel_constant_value(self, node):
        """Cancel constant value changes and revert to original values."""
        try:
            print(f"❌ CONSTANT VALUE: Canceling changes for node: {node.title}")
            
            # Get original properties if they exist
            original_props = getattr(node, '_original_properties', {
                'columns': [{'column_name': '', 'constant_value': '', 'data_type': 'string'}],
                'column_name': '',
                'constant_value': '',
                'data_type': 'string'
            })
            
            # Reset node properties to original values
            node.columns = [col.copy() for col in original_props.get('columns', [])]
            node.column_name = original_props.get('column_name', '')
            node.constant_value = original_props.get('constant_value', '')
            node.data_type = original_props.get('data_type', 'string')
            
            # Refresh the UI
            self.refresh_column_controls(node)
            self.update_constant_preview(node)
            
            print("✅ CONSTANT VALUE: Changes canceled successfully")
            
        except Exception as e:
            print(f"❌ CONSTANT VALUE: Error canceling changes: {str(e)}")
            QMessageBox.warning(self, "Cancel Error", f"Failed to cancel changes: {str(e)}")
            if hasattr(self, 'constant_column_name_edit'):
                self.constant_column_name_edit.setText(node.column_name)
            if hasattr(self, 'constant_value_edit'):
                self.constant_value_edit.setText(node.constant_value)
            if hasattr(self, 'data_type_combo'):
                self.data_type_combo.setCurrentText(node.data_type)
                
            print(f"✅ CONSTANT VALUE: Changes canceled for {node.title}")
            
        except Exception as e:
            print(f"❌ CONSTANT VALUE CANCEL ERROR: {e}")
    
    def add_data_viewing_section(self, node):
        """Add a section to view transformed data after execution."""
        # Check if node has been executed (has output data)
        execution_engine = self.get_execution_engine(node)
        output_data = None
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
        
        # Execution Status Group
        status_group = QGroupBox("Execution Status")
        status_layout = QHBoxLayout(status_group)
        
        if output_data is not None:
            status_label = QLabel("✅ Executed successfully")
            status_label.setStyleSheet("color: green; font-weight: bold;")
            status_layout.addWidget(status_label)
            
            info_label = QLabel(f"Output: {len(output_data)} rows, {len(output_data.columns)} columns")
            status_layout.addWidget(info_label)
            
            # View executed data button
            view_btn = QPushButton("👁️ View Transformed Data")
            view_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Transformed Data"))
            status_layout.addWidget(view_btn)
        else:
            status_label = QLabel("⏳ Node not executed yet")
            status_label.setStyleSheet("color: orange;")
            status_layout.addWidget(status_label)
            
            help_label = QLabel("Execute the expressions to see transformed data")
            help_label.setStyleSheet("color: #888888; font-style: italic;")
            status_layout.addWidget(help_label)
        
        self.content_layout.addWidget(status_group)
    
    def apply_and_execute_conditional_mapping(self, node):
        """Combined apply and execute - validates mappings and runs transformation in one step."""
        try:
            print(f"� CONDITIONAL MAPPING APPLY & EXECUTE: Starting combined operation for {node.title}")
            
            # Step 1: Apply and validate mappings (without showing success dialog)
            if not self.apply_conditional_mapping_silent(node):
                return  # Validation failed, error already shown
            
            # Step 2: Execute the transformation
            print(f"🚀 CONDITIONAL MAPPING APPLY & EXECUTE: Mappings applied, now executing transformation")
            self.execute_node_transformation(node)
            
            # Step 3: Ensure automatic data refresh happens
            print("🔄 CONDITIONAL MAPPING APPLY & EXECUTE: Ensuring data viewer refresh")
            self.data_refresh_requested.emit(node)
            print("🔄 CONDITIONAL MAPPING APPLY & EXECUTE: Data refresh signal emitted - viewer should update automatically")
            
        except Exception as e:
            print(f"❌ CONDITIONAL MAPPING APPLY & EXECUTE ERROR: {e}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Apply & Execute Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"❌ Failed to apply and execute conditional mapping")
            msg.setInformativeText(f"Error: {str(e)}")
            msg.exec()
    
    def apply_conditional_mapping_silent(self, node):
        """Apply conditional mapping configuration with validation but without success dialog."""
        try:
            print(f"🔧 CONDITIONAL MAPPING APPLY (SILENT): Applying settings for node: {node.title}")
            
            # Check if we have multiple configurations or legacy configuration
            if hasattr(node, 'mapping_configs') and node.mapping_configs:
                # Validate new multiple configuration structure
                valid_configs = 0
                config_errors = []
                
                for i, config in enumerate(node.mapping_configs):
                    config_num = i + 1
                    source_column = config.get('source_column', '').strip()
                    target_column = config.get('target_column', '').strip()
                    mappings = config.get('mappings', [])
                    operation_mode = config.get('operation_mode', 'add_column')
                    
                    print(f"🔍 Validating config {config_num}:")
                    print(f"   Source: '{source_column}'")
                    print(f"   Target: '{target_column}'")
                    print(f"   Operation Mode: '{operation_mode}'")
                    print(f"   Mappings: {len(mappings)} items")
                    
                    if not source_column:
                        config_errors.append(f"Configuration {config_num}: Please select a source column")
                        continue
                    
                    # For add_column mode, target column is required; for replace_column mode, it's not
                    if operation_mode == "add_column" and not target_column:
                        config_errors.append(f"Configuration {config_num}: Please enter a target column name")
                        continue
                        
                    if not mappings:
                        config_errors.append(f"Configuration {config_num}: Please add at least one mapping condition")
                        continue
                    
                    # Check if mappings have both condition and result values
                    valid_mappings = 0
                    for mapping in mappings:
                        condition = mapping.get('condition', '').strip()
                        result = mapping.get('result', '').strip()
                        if condition and result:
                            valid_mappings += 1
                    
                    if valid_mappings == 0:
                        config_errors.append(f"Configuration {config_num}: Please fill in both condition and result values")
                        continue
                    
                    print(f"✅ Config {config_num} valid: {valid_mappings} mappings")
                    valid_configs += 1
                
                if valid_configs == 0:
                    from PyQt6.QtWidgets import QMessageBox
                    error_msg = "⚠️ Configuration Required\n\n" + "\n".join(config_errors)
                    QMessageBox.warning(None, "⚠️ Configuration Required", error_msg)
                    return False
                
                print(f"✅ CONDITIONAL MAPPING APPLY: {valid_configs} valid configuration(s)")
                
            else:
                # Legacy validation
                if hasattr(node, 'source_column') and not node.source_column.strip():
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "⚠️ Configuration Required", "Please select a source column.")
                    return False
                    
                if hasattr(node, 'target_column') and not node.target_column.strip():
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "⚠️ Configuration Required", "Please enter a target column name.")
                    return False
                    
                if hasattr(node, 'mappings') and not node.mappings:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "⚠️ Configuration Required", "Please add at least one mapping condition.")
                    return False
                
                print(f"✅ CONDITIONAL MAPPING APPLY: Legacy configuration validated")
            
            print(f"� CONDITIONAL MAPPING APPLY (SILENT): Configuration validated successfully")
            print(f"   Source Column: {node.source_column}")
            print(f"   Target Column: {node.target_column}")
            print(f"   Mappings: {node.mappings}")
            print(f"   Default Value: {node.default_value}")
            print(f"   Operation Mode: {node.operation_mode}")
            
            # Trigger flow change to save the configuration
            if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                self._canvas_ref.flow_changed.emit()
            
            return True
                
        except Exception as e:
            print(f"❌ Error applying conditional mapping: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "❌ Error", f"Failed to apply configuration: {str(e)}")
            return False
    
    def cancel_conditional_mapping(self, node):
        """Cancel conditional mapping configuration and revert to previous state."""
        try:
            print(f"🗂️ CONDITIONAL MAPPING: Canceling configuration for node: {node.title}")
            
            # Reset node properties to defaults
            node.source_column = ""
            node.target_column = ""
            node.mappings = []
            node.default_value = ""
            node.operation_mode = "add_column"
            
            # Refresh the property panel to show reset state
            if hasattr(self, 'show_properties'):
                self.show_properties(node)
            
            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(None, "↶ Canceled", f"Configuration canceled and reset for '{node.title}'")
            
        except Exception as e:
            print(f"❌ Error canceling conditional mapping: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "❌ Error", f"Failed to cancel configuration: {str(e)}")
    
    def add_mapping_configuration(self, node):
        """Add a new mapping configuration to the node."""
        try:
            # Create new configuration
            new_id = len(node.mapping_configs) + 1
            new_config = {
                "id": new_id,
                "name": f"Mapping {new_id}",
                "source_column": "",
                "target_column": "",
                "mappings": [],
                "default_value": "",
                "operation_mode": "add_column"
            }
            
            node.mapping_configs.append(new_config)
            
            # Refresh the property panel to show the new configuration
            self.show_properties(node)
            
            print(f"➕ Added new mapping configuration: {new_config['name']}")
            
        except Exception as e:
            print(f"❌ Error adding mapping configuration: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "❌ Error", f"Failed to add configuration: {str(e)}")
    
    def remove_mapping_configuration(self, node, config_index):
        """Remove a mapping configuration from the node."""
        try:
            if 0 <= config_index < len(node.mapping_configs):
                removed_config = node.mapping_configs.pop(config_index)
                print(f"🗑️ Removed mapping configuration: {removed_config['name']}")
                
                # Ensure at least one configuration exists
                if not node.mapping_configs:
                    node.mapping_configs = [{
                        "id": 1,
                        "name": "Mapping 1",
                        "source_column": "",
                        "target_column": "",
                        "mappings": [],
                        "default_value": "",
                        "operation_mode": "add_column"
                    }]
                
                # Refresh the property panel
                self.show_properties(node)
                
        except Exception as e:
            print(f"❌ Error removing mapping configuration: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "❌ Error", f"Failed to remove configuration: {str(e)}")
    
    def create_mapping_configuration_section(self, node, config, config_index, available_columns):
        """Create a collapsible section for a single mapping configuration."""
        from PyQt6.QtWidgets import QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
        
        # Main configuration group
        config_group = QGroupBox(f"📝 {config['name']}")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: white;
                border-radius: 2px;
            }
        """)
        config_layout = QVBoxLayout(config_group)
        
        # Configuration header with remove button
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        config_title = QLabel(f"Configuration {config['id']}: Transform column data")
        config_title.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px;")
        
        remove_config_btn = QPushButton("🗑️ Remove")
        remove_config_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        remove_config_btn.setToolTip(f"Remove this mapping configuration")
        remove_config_btn.clicked.connect(lambda: self.remove_mapping_configuration(node, config_index))
        
        # Only show remove button if more than one configuration exists
        if len(node.mapping_configs) > 1:
            header_layout.addWidget(config_title)
            header_layout.addStretch()
            header_layout.addWidget(remove_config_btn)
        else:
            header_layout.addWidget(config_title)
            header_layout.addStretch()
        
        config_layout.addWidget(header_widget)
        
        # Column selection section with reduced spacing
        column_widget = QWidget()
        column_layout = QGridLayout(column_widget)
        column_layout.setSpacing(8)  # Reduced spacing
        column_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        
        # Source column selection
        source_label = QLabel("Source Column:")
        source_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        source_combo = QComboBox()
        source_combo.addItems(available_columns)
        if config['source_column']:
            index = source_combo.findText(config['source_column'])
            if index >= 0:
                source_combo.setCurrentIndex(index)
        source_combo.currentTextChanged.connect(lambda text, idx=config_index: self.on_config_source_column_changed(node, idx, text))
        
        # Target column name
        target_label = QLabel("Target Column:")
        target_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        target_edit = QLineEdit()
        target_edit.setText(config['target_column'])
        target_edit.setPlaceholderText("Enter new column name...")
        target_edit.textEdited.connect(lambda text, idx=config_index: self.on_config_target_column_changed(node, idx, text))
        target_edit.editingFinished.connect(lambda: self.on_text_editing_finished(node))
        
        # Operation mode selection
        mode_label = QLabel("Operation Mode:")
        mode_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        mode_combo = QComboBox()
        mode_combo.addItems(["add_column", "replace_column"])
        mode_combo.setCurrentText(config.get('operation_mode', 'add_column'))
        mode_combo.currentTextChanged.connect(lambda text, idx=config_index, te=target_edit: self.on_config_operation_mode_changed(node, idx, text, te))
        
        # Set initial state of target field based on operation mode
        current_mode = config.get('operation_mode', 'add_column')
        if current_mode == "replace_column":
            target_edit.setText("")
            target_edit.setEnabled(False)
            target_edit.setPlaceholderText("Source column will be replaced")
        else:
            target_edit.setEnabled(True)
            target_edit.setPlaceholderText("Enter new column name...")
        
        column_layout.addWidget(source_label, 0, 0)
        column_layout.addWidget(source_combo, 0, 1)
        column_layout.addWidget(target_label, 1, 0)
        column_layout.addWidget(target_edit, 1, 1)
        column_layout.addWidget(mode_label, 2, 0)
        column_layout.addWidget(mode_combo, 2, 1)
        
        # CT (Controlled Terminology) Selection - Always visible with search
        ct_label = QLabel("CT Selection:")
        ct_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        ct_label.setObjectName(f"ct_label_{config_index}")
        
        ct_selection_layout = QVBoxLayout()  # Changed to vertical layout
        ct_selection_layout.setSpacing(4)
        
        # Search field for CT selection
        ct_search_layout = QHBoxLayout()
        ct_search_field = QLineEdit()
        ct_search_field.setPlaceholderText("🔍 Search codelists...")
        ct_search_field.setObjectName(f"ct_search_field_{config_index}")
        ct_search_field.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
                min-height: 16px;
                color: black;
            }
            QLineEdit:focus {
                border-color: #007acc;
                outline: none;
            }
        """)
        
        # CT selection combo (made smaller)
        ct_combo_layout = QHBoxLayout()
        ct_selection_combo = QComboBox()
        ct_selection_combo.setObjectName(f"ct_selection_combo_{config_index}")
        ct_selection_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 2px solid #e1e5e9;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
                min-height: 16px;
                color: black;
                max-width: 200px;
            }
            QComboBox:focus {
                border-color: #007acc;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 6px;
            }
        """)
        
        refresh_ct_btn = QPushButton("🔄")
        refresh_ct_btn.setToolTip("Refresh CT codelists")
        refresh_ct_btn.setFixedSize(24, 24)
        refresh_ct_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #e1e5e9;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        refresh_ct_btn.clicked.connect(lambda: self.refresh_ct_codelists_for_config(ct_selection_combo, node, config_index))
        
        # Connect search functionality
        ct_search_field.textChanged.connect(
            lambda text: self.filter_ct_dropdown(ct_selection_combo, text, config_index)
        )
        
        ct_search_layout.addWidget(ct_search_field)
        ct_combo_layout.addWidget(ct_selection_combo)
        ct_combo_layout.addWidget(refresh_ct_btn)
        
        ct_selection_layout.addLayout(ct_search_layout)
        ct_selection_layout.addLayout(ct_combo_layout)
        
        ct_widget = QWidget()
        ct_widget.setLayout(ct_selection_layout)
        ct_widget.setObjectName(f"ct_widget_{config_index}")
        
        # CT Info label
        ct_info_label = QLabel("Select a controlled terminology codelist")
        ct_info_label.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic; padding: 4px;")
        ct_info_label.setWordWrap(True)
        ct_info_label.setObjectName(f"ct_info_label_{config_index}")
        
        column_layout.addWidget(ct_label, 3, 0)
        column_layout.addWidget(ct_widget, 3, 1)
        column_layout.addWidget(QLabel(), 4, 0)  # Empty label for spacing
        column_layout.addWidget(ct_info_label, 4, 1)
        
        # Set initial CT selection value
        if 'ct_selection' in config and config['ct_selection']:
            ct_index = ct_selection_combo.findData(config['ct_selection'])
            if ct_index >= 0:
                ct_selection_combo.setCurrentIndex(ct_index)
        
        # Refresh CT codelists immediately
        self.refresh_ct_codelists_for_config(ct_selection_combo, node, config_index)
        
        config_layout.addWidget(column_widget)
        
        # Mapping table section with improved spacing and auto-population
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setSpacing(5)  # Reduced spacing
        
        table_label = QLabel("Conditional Mappings:")
        table_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px; margin-bottom: 3px;")
        table_layout.addWidget(table_label)
        
        # Create mapping table with increased size
        mapping_table = QTableWidget()
        mapping_table.setColumnCount(2)
        mapping_table.setHorizontalHeaderLabels(["Condition (value)", "Result (output)"])
        mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mapping_table.setMinimumHeight(250)  # Increased to accommodate more rows
        mapping_table.setMaximumHeight(400)  # Allow more space for many unique values
        mapping_table.setAlternatingRowColors(True)  # Enable alternating colors for better readability
        mapping_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        mapping_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)  # Allow all edit triggers
        mapping_table.setShowGrid(True)  # Show table grid lines
        mapping_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                border: 1px solid #ccc;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 8px;
                background-color: white;
                color: black;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: white;
                color: black;
                border: none;
            }
            QTableWidget::item:focus {
                background-color: white;
                color: black;
                border: none;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
                color: #333;
            }
        """)
        
        # Auto-populate conditions if source column is selected
        self.populate_table_with_unique_values(mapping_table, config, available_columns)
        
        # Store mapping table reference in config for CT auto-mapping
        config['mapping_table'] = mapping_table
        
        # Connect CT selection change (now that mapping_table is defined)
        ct_selection_combo.currentTextChanged.connect(lambda text, idx=config_index, table=mapping_table: self.on_ct_selection_changed_for_config(node, idx, text, table))
        
        # Connect table changes
        mapping_table.itemChanged.connect(lambda item, idx=config_index: self.on_config_mapping_changed(node, idx, mapping_table))
        
        table_layout.addWidget(mapping_table)
        
        # Add/Remove mapping buttons (restored functionality)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # Reduced spacing
        
        add_mapping_btn = QPushButton("+ Add Mapping")
        add_mapping_btn.clicked.connect(lambda _, idx=config_index: self.add_config_mapping_row(node, idx, mapping_table))
        add_mapping_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        
        remove_mapping_btn = QPushButton("- Remove Selected")
        remove_mapping_btn.clicked.connect(lambda _, idx=config_index: self.remove_config_mapping_row(node, idx, mapping_table))
        remove_mapping_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #da190b;
            }
        """)
        
        refresh_values_btn = QPushButton("🔄 Refresh Unique Values")
        refresh_values_btn.clicked.connect(lambda _, idx=config_index: self.refresh_unique_values_for_config(node, idx, mapping_table, available_columns))
        refresh_values_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        
        button_layout.addWidget(add_mapping_btn)
        button_layout.addWidget(remove_mapping_btn)
        button_layout.addWidget(refresh_values_btn)
        button_layout.addStretch()
        
        table_layout.addLayout(button_layout)
        
        # Default value with reduced spacing
        default_widget = QWidget()
        default_layout = QHBoxLayout(default_widget)
        default_layout.setContentsMargins(0, 5, 0, 0)  # Reduced top margin
        
        default_label = QLabel("Default Value:")
        default_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        default_edit = QLineEdit()
        default_edit.setText(config.get('default_value', ''))
        default_edit.setPlaceholderText("Value when no conditions match...")
        default_edit.textEdited.connect(lambda text, idx=config_index: self.on_config_default_value_changed(node, idx, text))
        
        default_layout.addWidget(default_label)
        default_layout.addWidget(default_edit)
        
        table_layout.addWidget(default_widget)
        config_layout.addWidget(table_widget)
        
        self.content_layout.addWidget(config_group)
        
        # Store references for later use
        if not hasattr(self, 'config_widgets'):
            self.config_widgets = {}
        self.config_widgets[config_index] = {
            'group': config_group,
            'source_combo': source_combo,
            'target_edit': target_edit,
            'mode_combo': mode_combo,
            'mapping_table': mapping_table,
            'default_edit': default_edit
        }
    
    def on_config_source_column_changed(self, node, config_index, column_name):
        """Handle source column change for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            node.mapping_configs[config_index]['source_column'] = column_name
            
            # CRITICAL FIX: Update legacy properties for serialization
            if config_index == 0:  # Update legacy properties from first configuration
                node.source_column = column_name
                print(f"🔄 Updated legacy source_column: {column_name}")
            
            print(f"🗂️ Config {config_index + 1} source column changed to: {column_name}")
            
            # Auto-populate mapping table with unique values from the new source column
            # Clear existing values when source column changes
            if hasattr(self, 'config_widgets') and config_index in self.config_widgets:
                mapping_table = self.config_widgets[config_index]['mapping_table']
                config = node.mapping_configs[config_index]
                available_columns = self.get_available_columns_for_node(node)
                
                print(f"🔄 Auto-populating table with unique values from column: {column_name} (clearing previous values)")
                self.populate_table_with_unique_values(mapping_table, config, available_columns, clear_existing=True)
            
            if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                self._canvas_ref.flow_changed.emit()
    
    def on_config_target_column_changed(self, node, config_index, column_name):
        """Handle target column change for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            node.mapping_configs[config_index]['target_column'] = column_name
            
            # CRITICAL FIX: Update legacy properties for serialization
            if config_index == 0:  # Update legacy properties from first configuration
                node.target_column = column_name
                print(f"🔄 Updated legacy target_column: {column_name}")
            
            print(f"🗂️ Config {config_index + 1} target column changed to: {column_name}")
    
    def on_config_operation_mode_changed(self, node, config_index, mode, target_edit=None):
        """Handle operation mode change for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            node.mapping_configs[config_index]['operation_mode'] = mode
            
            # CRITICAL FIX: Update legacy properties for serialization
            if config_index == 0:  # Update legacy properties from first configuration
                node.operation_mode = mode
                print(f"🔄 Updated legacy operation_mode: {mode}")
            
            print(f"🗂️ Config {config_index + 1} operation mode changed to: {mode}")
            
            # Handle target column field based on operation mode
            if target_edit:
                if mode == "replace_column":
                    # For replace mode, clear and disable target column field
                    target_edit.setText("")
                    target_edit.setEnabled(False)
                    target_edit.setPlaceholderText("Source column will be replaced")
                    node.mapping_configs[config_index]['target_column'] = ""
                    print(f"🗂️ Config {config_index + 1}: Target column cleared for replace mode")
                else:  # add_column
                    # For add mode, enable target column field
                    target_edit.setEnabled(True)
                    target_edit.setPlaceholderText("Enter new column name...")
                    print(f"🗂️ Config {config_index + 1}: Target column enabled for add mode")
            
            if self._canvas_ref and hasattr(self._canvas_ref, 'flow_changed'):
                self._canvas_ref.flow_changed.emit()
    
    def refresh_ct_codelists_for_config(self, ct_combo, node=None, config_index=None):
        """Refresh CT codelists for a specific configuration's combo box."""
        if ct_combo is None:
            return
            
        # Store the previously selected value to restore it later
        saved_ct_selection = None
        if node and config_index is not None and 0 <= config_index < len(node.mapping_configs):
            saved_ct_selection = node.mapping_configs[config_index].get('ct_selection')
            
        ct_combo.clear()
        
        # Get main window to access SDTM specifications
        main_window = self.get_main_window()
        if not main_window:
            ct_combo.addItem("❌ No main window found", None)
            return
            
        # Check for SDTM specifications (could be in either attribute)
        spec_data = None
        if hasattr(main_window, 'sdtm_raw_data') and main_window.sdtm_raw_data:
            spec_data = main_window.sdtm_raw_data
        elif hasattr(main_window, 'sdtm_specifications') and main_window.sdtm_specifications:
            spec_data = main_window.sdtm_specifications
        
        if not spec_data:
            ct_combo.addItem("❌ No SDTM specifications loaded", None)
            return
        
        # Extract unique codelist names from Codelist Name column specifically - ONLY from 'Codelist' sheet
        codelist_names = set()
        
        # Store the codelist mapping for later use (Codelist Name -> Codelist Value)
        self.codelist_name_to_value_mapping = {}
        
        # Look specifically for the 'Codelist' sheet (case insensitive)
        codelist_sheet_found = False
        for sheet_name, df in spec_data.items():
            if sheet_name.lower() == 'codelist':
                codelist_sheet_found = True
                print(f"🎯 Processing '{sheet_name}' sheet for CT selection")
                
                if not hasattr(df, 'columns'):
                    continue
                    
                # Look specifically for Codelist Name and Codelist Value columns (case insensitive)
                codelist_name_col = None
                codelist_value_col = None
                
                for col in df.columns:
                    col_upper = col.upper()
                    if col_upper in ['CODELIST NAME', 'CODELIST_NAME', 'CODELISTNAME']:
                        codelist_name_col = col
                    elif col_upper in ['CODELIST VALUE', 'CODELIST_VALUE', 'CODELISTVALUE']:
                        codelist_value_col = col
                
                if codelist_name_col and codelist_value_col:
                    # Build mapping from Codelist Name to Codelist Value
                    for _, row in df.iterrows():
                        name_val = str(row[codelist_name_col]).strip()
                        value_val = str(row[codelist_value_col]).strip()
                        
                        # Only add if both values are clean strings (not processed/computed values)
                        if (name_val and value_val and 
                            name_val.lower() != 'nan' and value_val.lower() != 'nan' and
                            not any(func in name_val.lower() for func in ['strip(', 'upcase(', 'substr(', 'scan(', 'catx(', 'length(']) and
                            not any(func in value_val.lower() for func in ['strip(', 'upcase(', 'substr(', 'scan(', 'catx(', 'length(']) and
                            not name_val.startswith('_') and not value_val.startswith('_') and  # Avoid SAS variable names starting with _
                            len(name_val) > 1 and len(value_val) > 0):
                            
                            codelist_names.add(name_val)
                            self.codelist_name_to_value_mapping[name_val] = value_val
                            
                    print(f"🔍 Found {len(codelist_names)} unique codelist names with corresponding values from '{sheet_name}' sheet")
                    print(f"📋 Sample mappings: {dict(list(self.codelist_name_to_value_mapping.items())[:3])}")
                    break  # Only process the Codelist sheet
                else:
                    missing_cols = []
                    if not codelist_name_col:
                        missing_cols.append("'Codelist Name'")
                    if not codelist_value_col:
                        missing_cols.append("'Codelist Value'")
                    print(f"❌ Missing required columns: {', '.join(missing_cols)} in '{sheet_name}' sheet")
                    print(f"Available columns: {list(df.columns)}")
                    break
        
        if not codelist_sheet_found:
            ct_combo.addItem("❌ No 'Codelist' sheet found in specifications", None)
            print("⚠️ No 'Codelist' sheet found in specification file")
            return
        
        if not codelist_names:
            ct_combo.addItem("❌ No valid Codelist Name entries found in Codelist sheet", None)
            print("⚠️ No valid Codelist Name entries found in Codelist sheet")
            return
        
        ct_combo.addItem("🎯 Select a codelist for mapping...", None)
        for codelist_name in sorted(codelist_names):
            # Show only the codelist name, no arrow or value
            ct_combo.addItem(f"📋 {codelist_name}", codelist_name)
        
        # Restore the previously selected CT selection if it exists
        if saved_ct_selection:
            for i in range(ct_combo.count()):
                if ct_combo.itemData(i) == saved_ct_selection:
                    ct_combo.setCurrentIndex(i)
                    print(f"🔄 RESTORE CT: Config {config_index} restored selection '{saved_ct_selection}'")
                    break
        
        print(f"🔄 Loaded {len(codelist_names)} unique codelist values from 'Codelist Name' column: {sorted(list(codelist_names))}")

    def filter_ct_dropdown(self, ct_combo, search_text, config_index):
        """Filter CT dropdown based on search text."""
        if not hasattr(self, 'codelist_name_to_value_mapping'):
            return
        
        ct_combo.clear()
        
        # Always add the default option first
        ct_combo.addItem("🎯 Select a codelist for mapping...", None)
        
        # Filter codelist names based on search text
        search_lower = search_text.lower().strip()
        
        if not search_lower:
            # Show all items if search is empty
            for codelist_name in sorted(self.codelist_name_to_value_mapping.keys()):
                ct_combo.addItem(f"📋 {codelist_name}", codelist_name)
        else:
            # Show filtered items
            matched_items = []
            for codelist_name in self.codelist_name_to_value_mapping.keys():
                corresponding_value = self.codelist_name_to_value_mapping.get(codelist_name, "")
                
                # Search in both name and value
                if (search_lower in codelist_name.lower() or 
                    search_lower in corresponding_value.lower()):
                    matched_items.append(codelist_name)
            
            if matched_items:
                for codelist_name in sorted(matched_items):
                    ct_combo.addItem(f"📋 {codelist_name}", codelist_name)
                
                # Auto-select first match if there's only one
                if len(matched_items) == 1:
                    ct_combo.setCurrentIndex(1)  # Index 1 because 0 is the default option
                    # Trigger the selection change
                    self.on_ct_selection_changed_for_config_by_index(config_index, ct_combo.currentData())
            else:
                ct_combo.addItem("❌ No matches found", None)
        
        print(f"🔍 Filtered CT dropdown: {search_text} -> {ct_combo.count()-1} results")

    def on_ct_selection_changed_for_config_by_index(self, config_index, selected_codelist):
        """Handle CT selection change by config index (used by search auto-select)."""
        if not (0 <= config_index < len(self.current_node.mapping_configs)):
            return
        
        # Store the selection in the config
        self.current_node.mapping_configs[config_index]['ct_selection'] = selected_codelist
        
        # Find the mapping table for this config
        mapping_table = self.config_widgets[config_index]['mapping_table']
        
        # Auto-map values for this configuration
        self.auto_map_values_for_config(self.current_node, config_index, selected_codelist)

    def on_ct_selection_changed_for_config(self, node, config_index, text, mapping_table):
        """Handle CT selection change for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            ct_combo = self.findChild(QComboBox, f"ct_selection_combo_{config_index}")
            if ct_combo:
                selected_codelist = ct_combo.currentData()
                node.mapping_configs[config_index]['ct_selection'] = selected_codelist
                
                ct_info_label = self.findChild(QLabel, f"ct_info_label_{config_index}")
                if ct_info_label:
                    if not selected_codelist:
                        ct_info_label.setText("Select a controlled terminology codelist")
                        return
                        
                    # Check if SDTM specifications are loaded
                    main_window = self.get_main_window()
                    if not main_window or not hasattr(main_window, 'sdtm_raw_data'):
                        ct_info_label.setText("⚠️ Please upload SDTM specifications first")
                        return
                    
                    ct_info_label.setText(f"🔄 Loading values from codelist '{selected_codelist}'...")
                    
                    # Auto-map values for this configuration
                    self.auto_map_values_for_config(node, config_index, selected_codelist)

    def auto_map_values_for_config(self, node, config_index, selected_codelist):
        """Automatically map condition values to closest matches from the selected codelist."""
        if not (0 <= config_index < len(node.mapping_configs)):
            return
        
        # Import QColor at the beginning for use throughout the method
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QTableWidgetItem
            
        config = node.mapping_configs[config_index]
        
        # Find the mapping table for this configuration
        mapping_table = config.get('mapping_table')
        if not mapping_table:
            return
        
        ct_info_label = self.findChild(QLabel, f"ct_info_label_{config_index}")
        
        # Get main window to access SDTM specifications
        main_window = self.get_main_window()
        if not main_window or not hasattr(main_window, 'sdtm_raw_data'):
            if ct_info_label:
                ct_info_label.setText("⚠️ SDTM specifications not available. Please load specifications first.")
            return
        
        # Get current condition values from mapping table
        condition_values = []
        for row in range(mapping_table.rowCount()):
            condition_item = mapping_table.item(row, 0)
            if condition_item and condition_item.text().strip():
                condition_values.append(condition_item.text().strip())
        
        if not condition_values:
            if ct_info_label:
                ct_info_label.setText(f"📝 Add condition values first, then they will be auto-mapped with codelist '{selected_codelist}'")
            return
        
        # Find all entries for the selected codelist from the Codelist sheet
        spec_data = main_window.sdtm_raw_data
        codelist_entries = []
        
        for sheet_name, df in spec_data.items():
            if sheet_name.lower() == 'codelist':
                if not hasattr(df, 'columns'):
                    continue
                    
                # Find the columns
                codelist_name_col = None
                codelist_value_col = None
                decode_col = None  # For descriptive text
                
                for col in df.columns:
                    col_upper = col.upper()
                    if col_upper in ['CODELIST NAME', 'CODELIST_NAME', 'CODELISTNAME']:
                        codelist_name_col = col
                    elif col_upper in ['CODELIST VALUE', 'CODELIST_VALUE', 'CODELISTVALUE']:
                        codelist_value_col = col
                    elif col_upper in ['DECODE', 'CODELIST DECODE', 'DESCRIPTION', 'LABEL', 'MEANING']:
                        decode_col = col
                
                if codelist_name_col and codelist_value_col:
                    # Get all rows for the selected codelist
                    codelist_rows = df[df[codelist_name_col] == selected_codelist]
                    
                    for _, row in codelist_rows.iterrows():
                        value_val = str(row[codelist_value_col]).strip()
                        decode_val = str(row[decode_col]).strip() if decode_col else ""
                        
                        # Only add clean values
                        if (value_val and value_val.lower() != 'nan' and
                            not any(func in value_val.lower() for func in ['strip(', 'upcase(', 'substr(', 'scan(', 'catx(', 'length(']) and
                            not value_val.startswith('_')):
                            
                            codelist_entries.append({
                                'value': value_val,
                                'decode': decode_val,
                                'search_text': f"{value_val} {decode_val}".lower()
                            })
                    break
        
        if not codelist_entries:
            if ct_info_label:
                ct_info_label.setText(f"⚠️ No entries found for codelist '{selected_codelist}' in Codelist sheet")
            return
        
        print(f"🔍 Found {len(codelist_entries)} entries for codelist '{selected_codelist}'")
        
        # Perform closest match mapping for each condition value
        mappings_found = {}
        for condition_val in condition_values:
            best_match = None
            best_score = 0
            condition_lower = condition_val.lower()
            
            for entry in codelist_entries:
                # Calculate match score
                score = 0
                search_text = entry['search_text']
                value_lower = entry['value'].lower()
                decode_lower = entry['decode'].lower()
                
                # Exact match with value (highest priority)
                if condition_lower == value_lower:
                    score = 100
                # Exact match with decode text
                elif condition_lower == decode_lower:
                    score = 95
                # Value starts with condition or vice versa (but require minimum length)
                elif (len(condition_lower) >= 3 and len(value_lower) >= 3 and 
                      (value_lower.startswith(condition_lower) or condition_lower.startswith(value_lower))):
                    score = 85
                # Decode starts with condition or vice versa (but require minimum length)
                elif (len(condition_lower) >= 3 and len(decode_lower) >= 3 and 
                      (decode_lower.startswith(condition_lower) or condition_lower.startswith(decode_lower))):
                    score = 80
                # Value contains condition or vice versa (require meaningful length)
                elif (len(condition_lower) >= 4 and len(value_lower) >= 4 and 
                      (condition_lower in value_lower or value_lower in condition_lower)):
                    score = 70
                # Decode contains condition or vice versa (require meaningful length)
                elif (len(condition_lower) >= 4 and len(decode_lower) >= 4 and 
                      (condition_lower in decode_lower or decode_lower in condition_lower)):
                    score = 65
                # Any word matches (only for very specific meaningful matches)
                else:
                    # Check for significant word overlap (stricter criteria)
                    condition_words = [word for word in condition_lower.split() if len(word) > 4]  # Only longer words
                    if condition_words:
                        matching_words = []
                        for word in condition_words:
                            if word in value_lower or word in decode_lower:
                                matching_words.append(word)
                        
                        # Only score if majority of significant words match
                        if len(matching_words) >= len(condition_words) * 0.8:  # 80% of words must match
                            score = 30  # Much lower score for word matches
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        'condition': condition_val,
                        'result': entry['value'],
                        'decode': entry['decode'],
                        'score': score
                    }
            
            # Only map if there's a very strong match (increased threshold to 75 for stricter matching)
            if best_match and best_score >= 75:
                mappings_found[condition_val] = best_match
                print(f"🎯 Mapped '{condition_val}' → '{best_match['result']}' (score: {best_score})")
            else:
                # Log when no suitable match is found
                if best_match:
                    print(f"⚠️  '{condition_val}' has weak match '{best_match['result']}' (score: {best_score}) - skipping (threshold: 75)")
                else:
                    print(f"ℹ️  No match found for '{condition_val}' in codelist '{selected_codelist}'")
        
        # Apply mappings to the table
        mapped_count = 0
        if mappings_found:
            for row in range(mapping_table.rowCount()):
                condition_item = mapping_table.item(row, 0)
                if condition_item and condition_item.text().strip() in mappings_found:
                    mapping_data = mappings_found[condition_item.text().strip()]
                    
                    # Update result column
                    result_item = mapping_table.item(row, 1)
                    if not result_item:
                        result_item = QTableWidgetItem()
                        mapping_table.setItem(row, 1, result_item)
                    
                    result_item.setText(mapping_data['result'])
                    result_item.setToolTip(
                        f"Auto-mapped from codelist '{selected_codelist}':\n"
                        f"Best match: {mapping_data['decode']}\n"
                        f"Match score: {mapping_data['score']}%"
                    )
                    
                    # Color code based on match quality (updated for higher standards)
                    if mapping_data['score'] >= 90:
                        result_item.setBackground(QColor(220, 255, 220))  # Light green for excellent matches
                    elif mapping_data['score'] >= 75:
                        result_item.setBackground(QColor(255, 255, 200))  # Light yellow for good matches
                    else:
                        result_item.setBackground(QColor(255, 240, 220))  # Light orange for acceptable matches
                    
                    mapped_count += 1
        
        # Clear results for unmapped values to avoid showing unrelated mappings
        for row in range(mapping_table.rowCount()):
            condition_item = mapping_table.item(row, 0)
            if condition_item and condition_item.text().strip():
                condition_val = condition_item.text().strip()
                if condition_val not in mappings_found:
                    # Clear the result for unmapped values
                    result_item = mapping_table.item(row, 1)
                    if result_item:
                        result_item.setText("")  # Clear unrelated values
                        result_item.setBackground(QColor(255, 255, 255))  # Reset background
                        result_item.setToolTip("")  # Clear tooltip
                    else:
                        result_item = QTableWidgetItem("")
                        mapping_table.setItem(row, 1, result_item)
        
        # Update info label
        unmapped_count = len(condition_values) - mapped_count
        if ct_info_label:
            if mapped_count > 0:
                if unmapped_count > 0:
                    ct_info_label.setText(
                        f"✅ Auto-mapped {mapped_count}/{len(condition_values)} values from '{selected_codelist}'. "
                        f"⚠️ {unmapped_count} values need manual entry."
                    )
                else:
                    ct_info_label.setText(
                        f"✅ All {mapped_count} values successfully auto-mapped from '{selected_codelist}'"
                    )
            else:
                ct_info_label.setText(
                    f"⚠️ No suitable matches found in '{selected_codelist}'. Please map values manually."
                )
        
        # Update the configuration's mappings
        self.update_config_mappings_from_table(config, mapping_table)
        
        print(f"🔄 Auto-mapped {mapped_count}/{len(condition_values)} values using closest match from '{selected_codelist}'")

    def update_config_mappings_from_table(self, config, mapping_table):
        """Update a configuration's mappings from the mapping table."""
        if not (config and mapping_table):
            return
            
        mappings = []
        for row in range(mapping_table.rowCount()):
            condition_item = mapping_table.item(row, 0)
            result_item = mapping_table.item(row, 1)
            
            if condition_item and result_item:
                condition = condition_item.text().strip()
                result = result_item.text().strip()
                
                if condition and result:
                    mappings.append({
                        'condition': condition,
                        'result': result
                    })
        
        # Update the config's mappings
        config['mappings'] = mappings

    def on_config_default_value_changed(self, node, config_index, value):
        """Handle default value change for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            node.mapping_configs[config_index]['default_value'] = value
            
            # CRITICAL FIX: Update legacy properties for serialization
            if config_index == 0:  # Update legacy properties from first configuration
                node.default_value = value
                print(f"🔄 Updated legacy default_value: {value}")
            
            print(f"🗂️ Config {config_index + 1} default value changed to: {value}")
    
    def on_config_mapping_changed(self, node, config_index, mapping_table):
        """Handle mapping table changes for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            mappings = []
            for row in range(mapping_table.rowCount()):
                condition_item = mapping_table.item(row, 0)
                result_item = mapping_table.item(row, 1)
                
                condition = condition_item.text() if condition_item else ""
                result = result_item.text() if result_item else ""
                
                if condition and result:
                    mappings.append({"condition": condition, "result": result})
            
            node.mapping_configs[config_index]['mappings'] = mappings
            
            # CRITICAL FIX: Also update legacy properties for serialization
            if config_index == 0:  # Update legacy properties from first configuration
                node.mappings = mappings
                # Also update other legacy properties from this config
                config = node.mapping_configs[config_index]
                node.source_column = config.get('source_column', '')
                node.target_column = config.get('target_column', '')
                node.default_value = config.get('default_value', '')
                node.operation_mode = config.get('operation_mode', 'add_column')
                print(f"🔄 Updated legacy properties from config {config_index + 1}")
            
            print(f"🗂️ Config {config_index + 1} mappings updated: {len(mappings)} mappings")
    
    def populate_table_with_unique_values(self, mapping_table, config, available_columns, clear_existing=False):
        """Auto-populate mapping table with unique values from source column."""
        source_column = config.get('source_column', '')
        
        if not source_column or not hasattr(self, '_canvas_ref') or not self._canvas_ref:
            # Populate existing mappings or create one empty row
            existing_mappings = config.get('mappings', [])
            mapping_table.setRowCount(max(len(existing_mappings) + 1, 3))  # At least 3 rows
            
            for row, mapping in enumerate(existing_mappings):
                mapping_table.setItem(row, 0, QTableWidgetItem(mapping.get('condition', '')))
                mapping_table.setItem(row, 1, QTableWidgetItem(mapping.get('result', '')))
            return
        
        try:
            # Get unique values from the source column
            unique_values = self.get_unique_values_from_column(source_column)
            existing_mappings = config.get('mappings', [])
            
            # If clear_existing is True, ignore existing mappings
            if clear_existing:
                print(f"🧹 Clearing existing mappings for new source column: {source_column}")
                existing_mappings = []
                config['mappings'] = []  # Clear stored mappings too
            
            # Create a set of existing conditions to avoid duplicates
            existing_conditions = {mapping.get('condition', '') for mapping in existing_mappings}
            
            # Combine existing mappings with new unique values
            all_rows = []
            
            # Add existing mappings first (only if not clearing)
            if not clear_existing:
                for mapping in existing_mappings:
                    all_rows.append({
                        'condition': mapping.get('condition', ''),
                        'result': mapping.get('result', '')
                    })
            
            # Add unique values that aren't already mapped (up to 50 for reasonable UI)
            sdtm_suggestions = {}
            if self._main_window_ref and hasattr(self._main_window_ref, 'get_sdtm_suggestions'):
                # Get SDTM suggestions for all unique values
                sdtm_suggestions = self._main_window_ref.get_sdtm_suggestions(unique_values[:50])
                print(f"🎯 SDTM suggestions found: {len(sdtm_suggestions)} mappings")
            
            for value in unique_values[:50]:
                if str(value) not in existing_conditions and str(value).strip():
                    suggested_result = sdtm_suggestions.get(value, '')  # Use SDTM suggestion if available
                    all_rows.append({
                        'condition': str(value),
                        'result': suggested_result  # Auto-filled with SDTM suggestion or empty
                    })
                    if suggested_result:
                        print(f"📋 Auto-filled SDTM mapping: '{value}' → '{suggested_result}'")
            
            # Ensure at least 3 rows for user convenience
            while len(all_rows) < 3:
                all_rows.append({'condition': '', 'result': ''})
            
            # Populate the table
            mapping_table.setRowCount(len(all_rows))
            for row, data in enumerate(all_rows):
                condition_item = QTableWidgetItem(data['condition'])
                result_item = QTableWidgetItem(data['result'])
                
                # Highlight auto-filled SDTM suggestions with a light green background
                if data['result'] and data['condition'] in sdtm_suggestions:
                    from PyQt6.QtGui import QColor
                    result_item.setBackground(QColor(230, 255, 230))  # Light green
                    result_item.setToolTip(f"Auto-filled from SDTM specifications: {data['result']}")
                
                mapping_table.setItem(row, 0, condition_item)
                mapping_table.setItem(row, 1, result_item)
                
            suggestions_count = len([r for r in all_rows if r['result'] and r['condition'] in sdtm_suggestions])
            if suggestions_count > 0:
                print(f"✨ Applied {suggestions_count} SDTM auto-suggestions from specifications")
                
            print(f"📋 Populated table with {len(unique_values)} unique values from column: {source_column}")
            
        except Exception as e:
            print(f"⚠️ Could not populate unique values: {e}")
            # Fallback to existing mappings
            existing_mappings = config.get('mappings', [])
            mapping_table.setRowCount(max(len(existing_mappings) + 1, 3))
            
            for row, mapping in enumerate(existing_mappings):
                mapping_table.setItem(row, 0, QTableWidgetItem(mapping.get('condition', '')))
                mapping_table.setItem(row, 1, QTableWidgetItem(mapping.get('result', '')))
    
    def get_unique_values_from_column(self, column_name):
        """Get unique values from a column in the connected data."""
        try:
            # Get execution engine
            if hasattr(self._canvas_ref, 'execution_engine') and self._canvas_ref.execution_engine:
                execution_engine = self._canvas_ref.execution_engine
                
                # Get input data for the selected node
                current_node = self.current_node
                if current_node:
                    input_data = execution_engine.get_node_input_data(current_node)
                    
                    if input_data is not None and column_name in input_data.columns:
                        # Get unique values, excluding NaN/None values
                        unique_values = input_data[column_name].dropna().unique()
                        
                        # Convert to list and sort for consistency
                        unique_list = sorted([str(val) for val in unique_values if str(val).strip()])
                        # Return all unique values (up to 100 for performance)
                        return unique_list[:100]
                        
        except Exception as e:
            print(f"⚠️ Error getting unique values: {e}")
        
        return []
    
    def refresh_unique_values_for_config(self, node, config_index, mapping_table, available_columns):
        """Refresh the unique values for a specific configuration."""
        if 0 <= config_index < len(node.mapping_configs):
            config = node.mapping_configs[config_index]
            print(f"🔄 Refreshing unique values for config {config_index + 1}")
            
            # Clear existing mappings from the table
            mapping_table.clearContents()
            
            # Re-populate with fresh unique values
            self.populate_table_with_unique_values(mapping_table, config, available_columns)
    
    def add_config_mapping_row(self, node, config_index, mapping_table):
        """Add a new row to the mapping table for a specific configuration."""
        current_row_count = mapping_table.rowCount()
        mapping_table.setRowCount(current_row_count + 1)
        
        # Add empty items to the new row
        mapping_table.setItem(current_row_count, 0, QTableWidgetItem(""))
        mapping_table.setItem(current_row_count, 1, QTableWidgetItem(""))
        
        print(f"➕ Added new mapping row to config {config_index + 1}")
    
    def remove_config_mapping_row(self, node, config_index, mapping_table):
        """Remove selected row from the mapping table for a specific configuration."""
        current_row = mapping_table.currentRow()
        
        if current_row >= 0 and mapping_table.rowCount() > 1:  # Keep at least one row
            mapping_table.removeRow(current_row)
            print(f"🗑️ Removed mapping row {current_row + 1} from config {config_index + 1}")
            
            # Update the node's mappings
            self.on_config_mapping_changed(node, config_index, mapping_table)
        else:
            print("⚠️ Cannot remove the last row or no row selected")
    
    def refresh_all_ct_selections(self):
        """Refresh all CT selection dropdowns in all conditional mapping nodes."""
        print("🔄 Refreshing all CT selection dropdowns...")
        
        # Find all CT selection combo boxes
        ct_combos = self.findChildren(QComboBox)
        refreshed_count = 0
        
        for combo in ct_combos:
            # Check if this is a CT selection combo
            if combo.objectName() and "ct_selection_combo" in combo.objectName():
                print(f"🔄 Refreshing CT selection combo: {combo.objectName()}")
                
                # Extract config_index from the combo name (e.g., "ct_selection_combo_0" -> 0)
                try:
                    config_index = int(combo.objectName().split('_')[-1])
                    self.refresh_ct_codelists_for_config(combo, self.current_node, config_index)
                except (ValueError, IndexError):
                    # Fallback for combo boxes without proper naming
                    self.refresh_ct_codelists_for_config(combo)
                refreshed_count += 1
        
        print(f"✅ Refreshed {refreshed_count} CT selection dropdowns")
        
    def create_domain_properties(self, node):
        """Create properties for Domain nodes."""
        # Create main container (matching Column Keep/Drop pattern)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Debug: Check node state
        print(f"🏷️ PROPERTY DEBUG: Creating properties for {node.title}")
        print(f"🏷️ PROPERTY DEBUG: Node has selected_domain: {hasattr(node, 'selected_domain')}")
        if hasattr(node, 'selected_domain'):
            print(f"🏷️ PROPERTY DEBUG: selected_domain = '{node.selected_domain}'")
        else:
            print(f"🏷️ PROPERTY DEBUG: Adding selected_domain attribute")
            node.selected_domain = ""
        
        # Title
        title_label = QLabel("🏷️ SDTM Domain Assignment")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px 0px;")
        layout.addWidget(title_label)
        
        # Info
        info_label = QLabel("Select an SDTM domain code to add a 'DOMAIN' column with that value to all rows in the dataset.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; margin: 5px 0px;")
        layout.addWidget(info_label)
        
        # Connection Status (like other nodes)
        available_columns = self.get_available_columns_for_node(node)
        print(f"📊 Available columns for Domain node: {available_columns}")
        
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        if available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            status_icon = QLabel("🔗")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel(f"Connected - {len(available_columns)} columns available")
            status_text.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            status_icon = QLabel("⚠️")
            status_icon.setStyleSheet("font-size: 18px;")
            status_text = QLabel("No input connection detected")
            status_text.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 14px;")
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        status_widget.setStyleSheet("""
            QWidget {
                background: #f0f0f0;
                border: 1px solid #999;
            }
        """)
        layout.addWidget(status_widget)
        
        # Domain Selection Group
        domain_group = QGroupBox("Domain Selection")
        domain_layout = QVBoxLayout()
        
        domain_label = QLabel("Select SDTM Domain:")
        domain_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        domain_layout.addWidget(domain_label)
        
        self.domain_combo = QComboBox()
        self.domain_combo.addItem("🎯 Select Domain...", "")
        
        # Add domain codes with descriptions
        domain_descriptions = {
            "TA": "TA - Trial Arms",
            "TD": "TD - Trial Disease Assessments", 
            "TE": "TE - Trial Elements",
            "TI": "TI - Trial Inclusion/Exclusion Criteria",
            "TM": "TM - Trial Milestones",
            "TS": "TS - Trial Summary",
            "TV": "TV - Trial Visits",
            "DM": "DM - Demographics",
            "SV": "SV - Subject Visits",
            "SE": "SE - Subject Elements",
            "CO": "CO - Comments",
            "SM": "SM - Subject Milestones",
            "AG": "AG - Associated Groups/Pooled Groups",
            "CM": "CM - Concomitant Medications",
            "EC": "EC - Exposure as Collected",
            "EX": "EX - Exposure",
            "ML": "ML - Meal Data",
            "PR": "PR - Procedures",
            "SU": "SU - Substance Use",
            "AE": "AE - Adverse Events",
            "APMH": "APMH - Associated Persons Medical History",
            "CE": "CE - Clinical Events",
            "DS": "DS - Disposition",
            "DV": "DV - Device Properties",
            "HO": "HO - Healthcare Encounters",
            "MH": "MH - Medical History",
            "CV": "CV - Cardiovascular System Findings",
            "DA": "DA - Drug Accountability",
            "DD": "DD - Death Details",
            "EG": "EG - ECG Test Results",
            "FT": "FT - Fertility Testing",
            "IE": "IE - Inclusion/Exclusion Criteria Not Met",
            "IS": "IS - Immunogenicity Specimen Assessments",
            "LB": "LB - Laboratory Test Results",
            "LC": "LC - Laboratory Specimens",
            "MB": "MB - Microbiology Specimen",
            "MI": "MI - Microscopic Findings",
            "MK": "MK - Musculoskeletal System Findings",
            "MO": "MO - Morphology",
            "MS": "MS - Microbiology Susceptibility",
            "NV": "NV - Nervous System Findings",
            "OE": "OE - Ophthalmic Examinations",
            "PC": "PC - Pharmacokinetics Concentrations",
            "PE": "PE - Physical Examinations",
            "PP": "PP - Pharmacokinetics Parameters",
            "QS": "QS - Questionnaires",
            "RE": "RE - Reproductive System Findings",
            "RP": "RP - Reproductive System Procedures",
            "RS": "RS - Respiratory System Findings",
            "SC": "SC - Subject Characteristics",
            "SS": "SS - Skin System Findings",
            "TR": "TR - Tumor/Lesion Results",
            "TU": "TU - Tumor/Lesion Identification",
            "UR": "UR - Urinalysis Results",
            "VS": "VS - Vital Signs",
            "FA": "FA - Findings About Events or Interventions",
            "SR": "SR - Skin Response",
            "OI": "OI - Other Interventions"
        }
        
        for code in node.domain_codes:
            description = domain_descriptions.get(code, f"{code} - SDTM Domain")
            self.domain_combo.addItem(description, code)
        
        # Set current selection if node has one - check multiple sources
        node_domain = ""
        if hasattr(node, 'selected_domain') and node.selected_domain:
            node_domain = node.selected_domain
        elif hasattr(node, 'properties') and node.properties.get('selected_domain'):
            node_domain = node.properties['selected_domain']
            # Restore to node attribute
            node.selected_domain = node_domain
        
        print(f"🏷️ PROPERTY: Node domain to restore: '{node_domain}'")
        
        if node_domain:
            for i in range(self.domain_combo.count()):
                if self.domain_combo.itemData(i) == node_domain:
                    self.domain_combo.setCurrentIndex(i)
                    print(f"🏷️ PROPERTY: Restored combo selection to index {i} for domain '{node_domain}'")
                    break
        
        # Connect signal AFTER setting initial value to avoid false triggers
        self.domain_combo.currentTextChanged.connect(lambda: self.on_domain_changed(node))
        
        # Force synchronization between combo and node state
        # This ensures that if the combo shows a selection, the node has it too
        current_data = self.domain_combo.currentData()
        if current_data and current_data != node.selected_domain:
            print(f"🏷️ PROPERTY: Synchronizing node.selected_domain '{node.selected_domain}' with combo selection '{current_data}'")
            node.selected_domain = current_data
        elif node.selected_domain and not current_data:
            print(f"🏷️ PROPERTY: Node has selection '{node.selected_domain}' but combo shows none - fixing combo")
            for i in range(self.domain_combo.count()):
                if self.domain_combo.itemData(i) == node.selected_domain:
                    self.domain_combo.setCurrentIndex(i)
                    break
        domain_layout.addWidget(self.domain_combo)
        
        # Current selection display
        self.domain_status_label = QLabel()
        if hasattr(node, 'selected_domain') and node.selected_domain:
            self.domain_status_label.setText(f"🎯 Selected: {node.selected_domain}")
            self.domain_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.domain_status_label.setText("💡 No domain selected")
            self.domain_status_label.setStyleSheet("color: #666;")
        domain_layout.addWidget(self.domain_status_label)
        
        domain_group.setLayout(domain_layout)
        layout.addWidget(domain_group)
        
        # Apply Configuration Section (matching Conditional Mapping style)
        buttons_group = QGroupBox("🎯 Apply Configuration")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button (matching Conditional Mapping exactly)
        apply_execute_btn = QPushButton("✅ Apply and Execute")
        apply_execute_btn.setToolTip("Apply domain selection and execute transformation in one step")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_and_execute_domain(node))
        apply_execute_btn.setEnabled(hasattr(node, 'selected_domain') and bool(node.selected_domain))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button (matching Conditional Mapping exactly)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.cancel_domain_selection(node))
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_group)
        
        # Store button references for enabling/disabling
        self.apply_domain_button = apply_execute_btn
        self.cancel_domain_button = cancel_btn
        
        # Status/result info
        self.domain_result_label = QLabel("🔄 Ready to add DOMAIN column when domain is selected")
        self.domain_result_label.setWordWrap(True)
        self.domain_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
        layout.addWidget(self.domain_result_label)
        
        # Add domain results section (matching Expression node pattern exactly)
        self.add_domain_results_section(node, layout)
        
        # Spacer
        layout.addStretch()
        
        # Add all content to the main content layout
        self.content_layout.addWidget(container)
        
        # Store node reference
        self.current_node = node
        
    def add_domain_results_section(self, node, layout):
        """Add domain results section (matching Expression node pattern exactly)."""
        # Check if node has been executed and show result (same pattern as Expression)
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
            if output_data is not None:
                result_group = QGroupBox("🏷️ Domain Results")
                result_group.setStyleSheet("""
                    QGroupBox {
                        color: #27ae60;
                        border: 1px solid #999;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 2px;
                    }
                """)
                result_layout = QVBoxLayout(result_group)
                
                result_info = QLabel(f"✅ Domain added: {len(output_data)} rows processed")
                result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                result_layout.addWidget(result_info)
                
                # View transformed data button (matching Expression exactly)
                view_btn = QPushButton("👁️ View Transformed Data")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 5px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Domain Transformed Data"))
                result_layout.addWidget(view_btn)
                
                layout.addWidget(result_group)
        
    def on_domain_changed(self, node):
        """Handle domain selection change."""
        print(f"🏷️ DOMAIN CHANGE: on_domain_changed called for {node.title}")
        
        current_data = self.domain_combo.currentData()
        current_text = self.domain_combo.currentText()
        current_index = self.domain_combo.currentIndex()
        selected_domain = current_data if current_data else ""
        
        print(f"🏷️ DOMAIN CHANGE: Combo state - Index: {current_index}, Text: '{current_text}', Data: '{current_data}'")
        print(f"🏷️ DOMAIN CHANGE: Before update - node.selected_domain = '{getattr(node, 'selected_domain', 'MISSING')}'")
        
        # Update node IMMEDIATELY and make it stick
        node.selected_domain = selected_domain
        
        # FORCE save to node properties dict to ensure persistence
        if not hasattr(node, 'properties'):
            node.properties = {}
        node.properties['selected_domain'] = selected_domain
        
        print(f"🏷️ DOMAIN CHANGE: After update - node.selected_domain = '{node.selected_domain}'")
        print(f"🏷️ DOMAIN CHANGE: Saved to properties: '{node.properties.get('selected_domain', 'NOT_FOUND')}'")
        
        # Trigger workflow save to persist the domain selection
        if hasattr(node, 'canvas') and node.canvas and hasattr(node.canvas, 'flow_changed'):
            print(f"🏷️ DOMAIN CHANGE: Triggering workflow save to persist selection")
            node.canvas.flow_changed.emit()
        
        # Check connection status for better messaging
        available_columns = self.get_available_columns_for_node(node)
        has_connection = available_columns and available_columns[0] not in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]
        
        # Update UI
        if selected_domain:
            self.domain_status_label.setText(f"🎯 Selected: {selected_domain}")
            self.domain_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.apply_domain_button.setEnabled(True)
            
            if has_connection:
                self.domain_result_label.setText(f"✅ Ready to add DOMAIN='{selected_domain}' to {len(available_columns)} columns of data")
                self.domain_result_label.setStyleSheet("color: #27ae60; font-style: italic; padding: 10px; border: 1px solid #27ae60; border-radius: 4px; background-color: #d4edda;")
            else:
                self.domain_result_label.setText(f"🔄 Ready to add DOMAIN column with value '{selected_domain}' (connect data source)")
                self.domain_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
        else:
            self.domain_status_label.setText("💡 No domain selected")
            self.domain_status_label.setStyleSheet("color: #666;")
            self.apply_domain_button.setEnabled(False)
            
            if has_connection:
                self.domain_result_label.setText(f"🔄 Select a domain to add DOMAIN column to {len(available_columns)} columns of data")
                self.domain_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
            else:
                self.domain_result_label.setText("🔄 Ready to add DOMAIN column when domain is selected and data is connected")
                self.domain_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
            
        print(f"🏷️ DOMAIN: Selected domain changed to: {selected_domain}")
        
    def apply_and_execute_domain(self, node):
        """Apply the domain selection and execute the node."""
        if not hasattr(node, 'selected_domain') or not node.selected_domain:
            self.domain_result_label.setText("❌ Please select a domain first")
            return
            
        # Check for input data using the same method as connection detection
        available_columns = self.get_available_columns_for_node(node)
        
        # If we have available columns, we have input data
        if not available_columns or available_columns[0] in ["⚠️ Connect input data to see available columns", "❌ Error: Connect input data first"]:
            self.domain_result_label.setText("❌ No input data available. Connect a data source first.")
            return
            
        try:
            # Get the actual input data using the domain node's method
            input_data = node.get_input_data()
            if input_data is None:
                # Try alternative approach - check execution engine cache directly
                if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'execution_engine'):
                    execution_engine = self._canvas_ref.execution_engine
                    # Access cache directly (not via get_node_outputs method)
                    if hasattr(execution_engine, 'node_outputs'):
                        cache = execution_engine.node_outputs
                        print(f"🏷️ PROPERTY: Found {len(cache)} outputs in cache: {list(cache.keys())}")
                        
                        # Find input connections to this node
                        for connection in self._canvas_ref.connections:
                            if connection.end_port.parent_node == node:
                                input_node = connection.start_port.parent_node
                                print(f"🏷️ PROPERTY: Checking input node: {input_node.title}")
                                
                                # Method 1: Try by the actual node object (most direct)
                                if input_node in cache:
                                    input_data = cache[input_node]
                                    print(f"🏷️ PROPERTY: SUCCESS - Found by node object: {input_data.shape}")
                                    break
                                
                                # Method 2: Try by title match  
                                for cache_key, cache_value in cache.items():
                                    if hasattr(cache_key, 'title') and cache_key.title == input_node.title:
                                        input_data = cache_value
                                        print(f"🏷️ PROPERTY: SUCCESS - Found by title match: {input_data.shape}")
                                        break
                                
                                # Method 3: Try by node_id as fallback
                                if input_data is None and hasattr(input_node, 'node_id'):
                                    for cache_key, cache_value in cache.items():
                                        if hasattr(cache_key, 'node_id') and cache_key.node_id == input_node.node_id:
                                            input_data = cache_value
                                            print(f"🏷️ PROPERTY: SUCCESS - Found by node_id: {input_data.shape}")
                                            break
                                
                                # Method 4: Try direct output_data as last resort
                                if input_data is None and hasattr(input_node, 'output_data') and input_node.output_data is not None:
                                    input_data = input_node.output_data
                                    print(f"🏷️ PROPERTY: SUCCESS - Found by output_data: {input_data.shape}")
                                    break
            
            if input_data is None or (hasattr(input_data, 'empty') and input_data.empty):
                self.domain_result_label.setText("❌ Connected but no data available. Please execute upstream nodes first.")
                self.domain_result_label.setStyleSheet("color: #e67e22; font-style: italic; padding: 10px; border: 1px solid #e67e22; border-radius: 4px; background-color: #fdf2e9;")
                return
            
            # Update the result display immediately to show we're processing
            self.domain_result_label.setText(f"🔄 Processing {len(input_data)} rows with domain '{node.selected_domain}'...")
            self.domain_result_label.setStyleSheet("color: #2196F3; font-style: italic; padding: 10px; border: 1px solid #2196F3; border-radius: 4px; background-color: #e3f2fd;")
            
            # Execute the node to process the data
            print(f"🏷️ PROPERTY: Calling node.execute() for domain processing")
            success = node.execute()
            
            if success:
                # Get the output data to verify
                output_data = node.get_output_data()
                if output_data is not None:
                    # Update success message
                    self.domain_result_label.setText(
                        f"✅ Successfully added DOMAIN column with value '{node.selected_domain}' to {len(output_data)} rows"
                    )
                    self.domain_result_label.setStyleSheet("color: #27ae60; font-style: italic; padding: 10px; border: 1px solid #27ae60; border-radius: 4px; background-color: #d4edda;")
                    
                    # Trigger canvas update
                    if hasattr(node, 'canvas') and node.canvas and hasattr(node.canvas, 'flow_changed'):
                        node.canvas.flow_changed.emit()
                        print(f"🏷️ PROPERTY: Emitted flow_changed signal")
                        
                    # Auto-refresh data viewer
                    if hasattr(self, '_main_window_ref') and self._main_window_ref:
                        try:
                            self._main_window_ref.on_node_selected_for_data_view(node)
                            print(f"🏷️ PROPERTY: Triggered data viewer refresh")
                        except Exception as e:
                            print(f"🏷️ PROPERTY: Data viewer refresh error: {e}")
                else:
                    self.domain_result_label.setText("❌ Failed to generate output data")
                    self.domain_result_label.setStyleSheet("color: #dc3545; font-style: italic; padding: 10px; border: 1px solid #dc3545; border-radius: 4px; background-color: #f8d7da;")
            else:
                self.domain_result_label.setText("❌ Failed to execute domain assignment")
                self.domain_result_label.setStyleSheet("color: #dc3545; font-style: italic; padding: 10px; border: 1px solid #dc3545; border-radius: 4px; background-color: #f8d7da;")
                
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.domain_result_label.setText(error_msg)
            self.domain_result_label.setStyleSheet("color: #dc3545; font-style: italic; padding: 10px; border: 1px solid #dc3545; border-radius: 4px; background-color: #f8d7da;")
            print(f"❌ DOMAIN ERROR: {str(e)}")
    
    def cancel_domain_selection(self, node):
        """Cancel/clear domain selection."""
        try:
            # Clear node selection
            node.selected_domain = ""
            
            # Reset combo box to first item (usually empty or default)
            if hasattr(self, 'domain_combo'):
                self.domain_combo.setCurrentIndex(0)
            
            # Update status label
            if hasattr(self, 'domain_status_label'):
                self.domain_status_label.setText("💡 No domain selected")
                self.domain_status_label.setStyleSheet("color: #666;")
            
            # Update result label
            if hasattr(self, 'domain_result_label'):
                self.domain_result_label.setText("🔄 Ready to add DOMAIN column when domain is selected")
                self.domain_result_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;")
            
            # Disable apply button
            if hasattr(self, 'apply_domain_button'):
                self.apply_domain_button.setEnabled(False)
                
        except Exception as e:
            print(f"❌ Error canceling domain selection: {e}")


    def create_column_keep_drop_properties(self, node):
        """Create KNIME-style column filter properties with include/exclude interface."""
        print(f"📋 Creating KNIME-style column filter properties for: {node.title}")

        # Refresh available columns from connected inputs
        node.refresh_available_columns()

        # Create main container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Connection status header
        if node.available_columns:
            status_text = f"✅ Connected - {len(node.available_columns)} columns available"
            status_color = "#27ae60"
        else:
            status_text = "⚠️ No input connection detected"
            status_color = "#e67e22"

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(status_label)

        # Main content based on column availability
        if node.available_columns:
            # Initialize node state if needed - CHECK FOR SAVED STATE FIRST
            print(f"📋 LOAD CHECK: Node has included_columns={hasattr(node, 'included_columns')}, excluded_columns={hasattr(node, 'excluded_columns')}")
            if hasattr(node, 'included_columns'):
                print(f"📋 LOAD CHECK: included_columns = {node.included_columns}")
            if hasattr(node, 'excluded_columns'):
                print(f"📋 LOAD CHECK: excluded_columns = {node.excluded_columns}")
            
            # Check if we have saved data or need to initialize fresh
            has_saved_included = hasattr(node, 'included_columns') and node.included_columns is not None
            has_saved_excluded = hasattr(node, 'excluded_columns') and node.excluded_columns is not None
            
            if not has_saved_included and not has_saved_excluded:
                # Fresh initialization - no saved data
                print(f"📋 FRESH INIT: No saved column selections found")
                node.included_columns = []
                node.excluded_columns = node.available_columns.copy()
                print(f"📋 Fresh initialization - {len(node.excluded_columns)} columns in excluded")
            else:
                # Has saved data - validate it against available columns
                print(f"📋 LOAD: Found saved column selections")
                if not has_saved_included:
                    node.included_columns = []
                if not has_saved_excluded:
                    node.excluded_columns = []
                
                # Ensure all columns are accounted for
                all_selected = set(node.included_columns + node.excluded_columns)
                all_available = set(node.available_columns)
                
                # Add any new columns to excluded by default
                new_columns = all_available - all_selected
                if new_columns:
                    node.excluded_columns.extend(list(new_columns))
                    print(f"📋 LOAD: Added {len(new_columns)} new columns to excluded list")
                
                # Remove any columns that are no longer available
                node.included_columns = [col for col in node.included_columns if col in all_available]
                node.excluded_columns = [col for col in node.excluded_columns if col in all_available]
                
                print(f"📋 LOADED: {len(node.included_columns)} included, {len(node.excluded_columns)} excluded")

            # KNIME-style column filter interface
            filter_group = QGroupBox("🔍 Column Filter")
            filter_group.setStyleSheet("""
                QGroupBox {
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    background: white;
                    border-radius: 4px;
                }
            """)
            filter_layout = QVBoxLayout(filter_group)

            # Instructions
            instructions = QLabel("Select columns and choose to include or exclude them from the output:")
            instructions.setStyleSheet("color: #34495e; font-size: 12px; margin-bottom: 10px; font-weight: normal;")
            filter_layout.addWidget(instructions)

            # Main filter layout - two columns like KNIME
            main_filter_layout = QHBoxLayout()

            # Left side - Available columns list with search
            left_container = QWidget()
            left_layout = QVBoxLayout(left_container)
            left_layout.setContentsMargins(5, 5, 5, 5)

            # Search/filter box
            search_label = QLabel("Filter columns:")
            search_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            left_layout.addWidget(search_label)

            search_box = QLineEdit()
            search_box.setPlaceholderText("Type to filter columns...")
            search_box.setStyleSheet("""
                QLineEdit {
                    padding: 6px 8px;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border: 2px solid #3498db;
                }
            """)
            left_layout.addWidget(search_box)

            # Column list with checkboxes
            columns_label = QLabel(f"Available Columns ({len(node.available_columns)}):")
            columns_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px; margin-top: 10px;")
            left_layout.addWidget(columns_label)

            # Scrollable area for columns
            scroll_area = QScrollArea()
            scroll_area.setMaximumHeight(300)
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    background: white;
                }
            """)
            
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(2)
            scroll_layout.setContentsMargins(5, 5, 5, 5)

            # Store checkbox references
            self.column_checkboxes = {}

            # Create checkboxes for each column (maintain original dataframe order)
            for col in node.available_columns:
                checkbox = QCheckBox(col)
                checkbox.setChecked(col in node.included_columns)
                checkbox.stateChanged.connect(lambda state, column=col: self.toggle_column_selection_standard(node, column, state))
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font-family: 'Consolas', 'Monaco', monospace;
                        font-size: 11px;
                        padding: 4px;
                        color: #2c3e50;
                    }
                    QCheckBox:checked {
                        color: #27ae60;
                        font-weight: bold;
                    }
                    QCheckBox:unchecked {
                        color: #7f8c8d;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                    QCheckBox::indicator:unchecked {
                        border: 2px solid #bdc3c7;
                        border-radius: 3px;
                        background: white;
                    }
                    QCheckBox::indicator:checked {
                        border: 2px solid #27ae60;
                        border-radius: 3px;
                        background: #27ae60;
                        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik04LjUgMUwyLjc1IDYuNzVMMSA1IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                    }
                """)
                scroll_layout.addWidget(checkbox)
                self.column_checkboxes[col] = checkbox

            # Search functionality
            def filter_columns():
                search_text = search_box.text().lower()
                for col, checkbox in self.column_checkboxes.items():
                    checkbox.setVisible(search_text in col.lower())
                
            search_box.textChanged.connect(filter_columns)

            scroll_area.setWidget(scroll_widget)
            left_layout.addWidget(scroll_area)

            # Quick selection buttons (KNIME style)
            quick_buttons_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("Select All")
            select_all_btn.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
            select_all_btn.clicked.connect(lambda: self.keep_all_columns(node))
            quick_buttons_layout.addWidget(select_all_btn)

            deselect_all_btn = QPushButton("Deselect All")
            deselect_all_btn.setStyleSheet("""
                QPushButton {
                    background: #95a5a6;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #7f8c8d;
                }
            """)
            deselect_all_btn.clicked.connect(lambda: self.drop_all_columns(node))
            quick_buttons_layout.addWidget(deselect_all_btn)

            quick_buttons_layout.addStretch()
            left_layout.addLayout(quick_buttons_layout)

            main_filter_layout.addWidget(left_container)

            # Right side - Include/Exclude choice (KNIME style)
            right_container = QWidget()
            right_layout = QVBoxLayout(right_container)
            right_layout.setContentsMargins(15, 5, 5, 5)

            action_label = QLabel("Action for selected columns:")
            action_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            right_layout.addWidget(action_label)

            # Radio buttons for include/exclude
            self.include_radio = QRadioButton("Include selected columns")
            self.include_radio.setChecked(True)  # Default to include
            self.include_radio.setStyleSheet("""
                QRadioButton {
                    color: #27ae60;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 8px;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    background: white;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #27ae60;
                    border-radius: 8px;
                    background: #27ae60;
                }
            """)
            right_layout.addWidget(self.include_radio)

            self.exclude_radio = QRadioButton("Exclude selected columns")
            self.exclude_radio.setStyleSheet("""
                QRadioButton {
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 8px;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    background: white;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #e74c3c;
                    border-radius: 8px;
                    background: #e74c3c;
                }
            """)
            right_layout.addWidget(self.exclude_radio)

            # Connect radio button changes to update summary
            self.include_radio.toggled.connect(lambda: self.update_column_summary(node))
            self.exclude_radio.toggled.connect(lambda: self.update_column_summary(node))

            # Status summary
            self.status_summary = QLabel()
            self.update_column_summary(node)
            self.status_summary.setStyleSheet("""
                QLabel {
                    background: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 10px;
                    color: #2c3e50;
                    font-weight: bold;
                    font-size: 12px;
                    margin-top: 20px;
                }
            """)
            right_layout.addWidget(self.status_summary)

            right_layout.addStretch()
            main_filter_layout.addWidget(right_container)

            filter_layout.addLayout(main_filter_layout)
            layout.addWidget(filter_group)

            # Action buttons group (Expression style)
            buttons_group = QGroupBox("🚀 Actions")
            buttons_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    color: #2c3e50;
                    border: 2px solid #28a745;
                    border-radius: 3px;
                    margin-top: 5px;
                    padding-top: 5px;
                    background: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px 0 4px;
                    background: white;
                    border-radius: 2px;
                }
            """)
            buttons_layout = QVBoxLayout(buttons_group)

            # Apply and Execute button (Expression style)
            apply_execute_btn = QPushButton("🚀 Apply and Execute")
            apply_execute_btn.setToolTip("Apply column filter and execute transformation in one step")
            apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
            apply_execute_btn.clicked.connect(lambda: self.apply_and_execute_column_filter(node))
            buttons_layout.addWidget(apply_execute_btn)

            # Cancel button (Expression style)
            cancel_btn = QPushButton("❌ Cancel")
            cancel_btn.setToolTip("Cancel - Revert unsaved changes")
            cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
            cancel_btn.clicked.connect(lambda: self.cancel_column_keep_drop(node))
            buttons_layout.addWidget(cancel_btn)

            layout.addWidget(buttons_group)

            # Check if node has been executed and show result (Expression style)
            execution_engine = self.get_execution_engine(node)
            if execution_engine:
                output_data = execution_engine.get_node_output_data(node)
                if output_data is not None:
                    result_group = QGroupBox("✨ Filter Results")
                    result_group.setStyleSheet("""
                        QGroupBox {
                            color: #27ae60;
                            border: 1px solid #999;
                            margin-top: 5px;
                            padding-top: 5px;
                        }
                        QGroupBox::title {
                            subcontrol-origin: margin;
                            left: 5px;
                            padding: 0 2px;
                        }
                    """)
                    result_layout = QVBoxLayout(result_group)
                    
                    result_info = QLabel(f"✅ Column filter applied: {len(output_data.columns)} columns in result")
                    result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                    result_layout.addWidget(result_info)
                    
                    # View transformed data button (Expression style)
                    view_btn = QPushButton("👁️ View Transformed Data")
                    view_btn.setStyleSheet("""
                        QPushButton {
                            background: #17a2b8;
                            color: white;
                            padding: 5px 10px;
                            border: none;
                        }
                        QPushButton:hover {
                            background: #138496;
                        }
                    """)
                    view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Transformed Data"))
                    result_layout.addWidget(view_btn)
                    
                    layout.addWidget(result_group)

            print(f"✅ KNIME-STYLE: Created column filter interface with {len(node.available_columns)} columns")

        else:
            # No columns available - show connection message
            no_data_label = QLabel("⚠️ Connect an input node to see available columns")
            no_data_label.setStyleSheet("color: #e67e22; font-size: 14px; padding: 20px; text-align: center;")
            layout.addWidget(no_data_label)

        # Add container to main layout
        self.content_layout.addWidget(container)

    def apply_column_keep_drop(self, node):
        """Apply column keep/drop configuration."""
        try:
            print(f"✅ APPLY: Column selection applied - {len(node.included_columns)} included")
            self.show_notification(f"Column selection applied: {len(node.included_columns)} columns will be kept")
        except Exception as e:
            print(f"❌ APPLY ERROR: {e}")

    def execute_column_keep_drop(self, node):
        """Execute column keep/drop operation."""
        try:
            print(f"🚀 EXECUTE: Executing column keep/drop with {len(node.included_columns)} columns")
            # Apply and execute
            self.apply_column_keep_drop(node)
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.execute_single_node(node)
            self.show_notification(f"Executed successfully: {len(node.included_columns)} columns kept")
        except Exception as e:
            print(f"❌ EXECUTE ERROR: {e}")
    
    def cancel_column_keep_drop(self, node):
        """Cancel column selection changes."""
        try:
            node.included_columns = []
            node.excluded_columns = node.available_columns.copy()
            if hasattr(self, 'column_checkboxes'):
                for checkbox in self.column_checkboxes.values():
                    checkbox.setChecked(False)
            print("❌ CANCEL: Column selection reset")
        except Exception as e:
            print(f"❌ CANCEL ERROR: {e}")

    def simple_move_all_to_included(self, node, included_text, excluded_text):
        """Simple function to move all columns to included."""
        node.included_columns = node.available_columns.copy()
        node.excluded_columns = []
        
        # Update display
        included_display = ", ".join(node.included_columns)
        included_text.setText(included_display)
        excluded_text.setText("(No columns excluded)")
        
        print(f"📋 SIMPLE: Moved all {len(node.included_columns)} columns to included")
        
        # Update checkboxes if they exist
        if hasattr(self, 'column_checkboxes'):
            for col, checkbox in self.column_checkboxes.items():
                checkbox.setChecked(True)  # All columns included = checked
    
    def simple_move_all_to_excluded(self, node, included_text, excluded_text):
        """Simple function to move all columns to excluded."""
        node.excluded_columns = node.available_columns.copy()
        node.included_columns = []
        
        # Update display
        excluded_display = ", ".join(node.excluded_columns)
        excluded_text.setText(excluded_display)
        included_text.setText("(No columns included)")
        
        print(f"📋 SIMPLE: Moved all {len(node.excluded_columns)} columns to excluded")
        
        # Update checkboxes if they exist
        if hasattr(self, 'column_checkboxes'):
            for col, checkbox in self.column_checkboxes.items():
                checkbox.setChecked(False)  # All columns excluded = unchecked
        
    def toggle_column_selection(self, node, column, state, included_text, excluded_text):
        """Toggle individual column selection with checkbox."""
        try:
            print(f"🎯 TOGGLE: Column '{column}' state changed to {state}")
            
            if state == 2:  # Checked (included)
                if column not in node.included_columns:
                    node.included_columns.append(column)
                if column in node.excluded_columns:
                    node.excluded_columns.remove(column)
            else:  # Unchecked (excluded)
                if column in node.included_columns:
                    node.included_columns.remove(column)
                if column not in node.excluded_columns:
                    node.excluded_columns.append(column)
            
            # Update text displays
            if node.included_columns:
                included_text.setText(f"✅ Included Columns ({len(node.included_columns)}):\n" + 
                                    "\n".join([f"  • {col}" for col in node.included_columns]))
                included_text.setStyleSheet("""
                    background: #e8f5e8; 
                    padding: 10px; 
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 10px;
                """)
            else:
                included_text.setText("(No columns included)")
                included_text.setStyleSheet("color: #666; font-style: italic;")
            
            if node.excluded_columns:
                excluded_text.setText(f"❌ Excluded Columns ({len(node.excluded_columns)}):\n" + 
                                    "\n".join([f"  • {col}" for col in node.excluded_columns]))
                excluded_text.setStyleSheet("""
                    background: #ffe8e8; 
                    padding: 10px; 
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 10px;
                """)
            else:
                excluded_text.setText("(No columns excluded)")
                excluded_text.setStyleSheet("color: #666; font-style: italic;")
                
            print(f"🎯 TOGGLE: Updated - {len(node.included_columns)} included, {len(node.excluded_columns)} excluded")
            
        except Exception as e:
            print(f"❌ TOGGLE ERROR: {e}")
            self.show_notification(f"Error toggling column: {e}", True)
            
    def update_column_summary(self, node):
        """Update the status summary for KNIME-style column filter."""
        if not hasattr(self, 'status_summary'):
            return
            
        selected_count = len([col for col in node.available_columns if col in node.included_columns])
        total_count = len(node.available_columns)
        
        if self.include_radio.isChecked():
            action = "included"
            result_count = selected_count
        else:
            action = "excluded"
            result_count = total_count - selected_count
            
        summary_text = f"📊 {selected_count} of {total_count} columns selected\n"
        summary_text += f"🎯 Action: {action.title()}\n"
        summary_text += f"📤 Result: {result_count} columns in output"
        
        self.status_summary.setText(summary_text)

    def apply_and_execute_column_filter(self, node):
        """Apply and execute the KNIME-style column filter in one step."""
        try:
            print(f"🎯 KNIME-FILTER: Applying and executing column filter")
            
            # Determine which columns to include based on radio button selection
            selected_columns = [col for col in node.available_columns if col in node.included_columns]
            
            if self.include_radio.isChecked():
                # Include mode - keep selected columns
                final_columns = selected_columns
                action = "included"
            else:
                # Exclude mode - keep unselected columns
                final_columns = [col for col in node.available_columns if col not in selected_columns]
                action = "excluded"
            
            print(f"🎯 KNIME-FILTER: {action.title()} {len(selected_columns)} columns, result: {len(final_columns)} columns")
            
            # Update node configuration
            node.included_columns = final_columns
            node.excluded_columns = [col for col in node.available_columns if col not in final_columns]
            
            # Execute the transformation
            execution_engine = self.get_execution_engine(node)
            if execution_engine:
                success = execution_engine.execute_node(node)
                if success:
                    print(f"✅ KNIME-FILTER: Filter applied and executed successfully")
                    # Refresh the interface to show results
                    self.show_properties(node)
                    
                    # Ensure automatic data refresh happens  
                    print("🔄 KNIME-FILTER: Ensuring data viewer refresh")
                    self.data_refresh_requested.emit(node)
                    print("🔄 KNIME-FILTER: Data refresh signal emitted - viewer should update automatically")
                    
                    # Show success message
                    QMessageBox.information(self, "Column Filter Applied", 
                                          f"✅ Column filter executed successfully!\n\n"
                                          f"• {len(selected_columns)} columns {action}\n"
                                          f"• {len(final_columns)} columns in result")
                else:
                    QMessageBox.warning(self, "Execution Failed", "❌ Failed to execute column filter")
            else:
                QMessageBox.warning(self, "No Execution Engine", "❌ No execution engine available")
                
        except Exception as e:
            print(f"❌ KNIME-FILTER: Error in apply_and_execute_column_filter: {e}")
            QMessageBox.critical(self, "Error", f"❌ Error applying column filter: {str(e)}")

    def toggle_column_selection_standard(self, node, column, state):
        """Toggle individual column selection for KNIME-style interface."""
        try:
            print(f"🎯 KNIME TOGGLE: Column '{column}' state changed to {state}")
            
            if state == 2:  # Checked (included)
                if column not in node.included_columns:
                    node.included_columns.append(column)
                if column in node.excluded_columns:
                    node.excluded_columns.remove(column)
            else:  # Unchecked (excluded)
                if column in node.included_columns:
                    node.included_columns.remove(column)
                if column not in node.excluded_columns:
                    node.excluded_columns.append(column)
            
            # Update KNIME-style summary if available
            if hasattr(self, 'status_summary') and hasattr(self, 'include_radio'):
                self.update_column_summary(node)
            
            print(f"🎯 KNIME TOGGLE: Updated - {len(node.included_columns)} included, {len(node.excluded_columns)} excluded")
            
        except Exception as e:
            print(f"❌ KNIME TOGGLE ERROR: {e}")
            self.show_notification(f"Error toggling column: {e}", True)
            
    def keep_all_columns(self, node):
        """Keep all columns (check all checkboxes) - KNIME style."""
        try:
            node.included_columns = node.available_columns.copy()
            node.excluded_columns = []
            
            # Update all checkboxes
            if hasattr(self, 'column_checkboxes'):
                for col, checkbox in self.column_checkboxes.items():
                    checkbox.setChecked(True)
            
            # Update KNIME-style summary
            if hasattr(self, 'status_summary'):
                self.update_column_summary(node)
                
            print(f"📋 KNIME SELECT ALL: All {len(node.included_columns)} columns selected")
            self.show_notification(f"All {len(node.included_columns)} columns selected")
            
        except Exception as e:
            print(f"❌ SELECT ALL ERROR: {e}")
            self.show_notification(f"Error selecting all columns: {e}", True)
            
    def drop_all_columns(self, node):
        """Drop all columns (uncheck all checkboxes) - KNIME style."""
        try:
            node.excluded_columns = node.available_columns.copy()
            node.included_columns = []
            
            # Update all checkboxes
            if hasattr(self, 'column_checkboxes'):
                for col, checkbox in self.column_checkboxes.items():
                    checkbox.setChecked(False)
            
            # Update KNIME-style summary
            if hasattr(self, 'status_summary'):
                self.update_column_summary(node)
                
            print(f"📋 KNIME DESELECT ALL: All {len(node.excluded_columns)} columns deselected")
            self.show_notification(f"All {len(node.excluded_columns)} columns deselected")
            
        except Exception as e:
            print(f"❌ DESELECT ALL ERROR: {e}")
            self.show_notification(f"Error deselecting all columns: {e}", True)
            
    def update_column_status_display(self, node):
        """Update the status display showing included/excluded counts."""
        try:
            if hasattr(self, 'column_status_label'):
                included_count = len(node.included_columns)
                excluded_count = len(node.excluded_columns)
                
                status_text = f"✅ {included_count} columns to keep  |  ❌ {excluded_count} columns to drop"
                self.column_status_label.setText(status_text)
                self.column_status_label.setStyleSheet("""
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                """)
        except Exception as e:
            print(f"❌ STATUS UPDATE ERROR: {e}")
            
    def apply_column_keep_drop(self, node):
        """Apply column selection changes without executing."""
        try:
            print(f"📋 APPLY: Column selection applied - {len(node.included_columns)} included, {len(node.excluded_columns)} excluded")
            self.show_notification(f"Column selection applied: {len(node.included_columns)} columns to keep")
            
        except Exception as e:
            print(f"❌ APPLY ERROR: {e}")
            self.show_notification(f"Error applying column selection: {e}", True)
            
    def execute_column_keep_drop(self, node):
        """Execute the column keep/drop operation."""
        try:
            print(f"📋 EXECUTE: Starting column keep/drop execution...")
            
            # Apply and execute the column keep/drop
            self.apply_and_execute_column_keep_drop(node)
            
        except Exception as e:
            print(f"❌ EXECUTE ERROR: {e}")
            self.show_notification(f"Error executing column keep/drop: {e}", True)
            
    def cancel_column_keep_drop(self, node):
        """Cancel column selection changes."""
        try:
            # Reset to original state - put all columns back in excluded
            node.excluded_columns = node.available_columns.copy()
            node.included_columns = []
            
            # Update all checkboxes
            if hasattr(self, 'column_checkboxes'):
                for col, checkbox in self.column_checkboxes.items():
                    checkbox.setChecked(False)
            
            self.update_column_status_display(node)
            print(f"📋 CANCEL: Reset to original state - all columns excluded")
            self.show_notification("Column selection cancelled - reset to original state")
            
        except Exception as e:
            print(f"❌ CANCEL ERROR: {e}")
            self.show_notification(f"Error cancelling column selection: {e}", True)

    def create_column_keep_drop_panes(self, layout, node):
        """Create dual-pane column interface with proper CSS styling."""
        panes_group = QGroupBox("📊 Column Selection")
        panes_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                background: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        panes_layout = QVBoxLayout(panes_group)
        
        # Dual panes container
        panes_container = QHBoxLayout()
        
        # Included Columns Pane (Left)
        included_group = QGroupBox("✅ Included Columns (Will be kept)")
        included_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #27ae60;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background: #f8fff8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background: white;
                color: #27ae60;
                font-weight: bold;
            }
        """)
        included_layout = QVBoxLayout(included_group)
        
        # Included columns list - create without parent, add to layout properly
        self.included_list = QListWidget()
        print(f"📋 WIDGET CREATION: included_list created: {bool(self.included_list)}")
        self.included_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #27ae60;
                border-radius: 3px;
                background: white;
                selection-background-color: #27ae60;
                selection-color: white;
                color: black;
                min-height: 150px;
                max-height: 300px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #e0e0e0;
                color: black;
                min-height: 20px;
            }
            QListWidget::item:hover {
                background-color: #e8f5e9;
                color: black;
            }
            QListWidget::item:selected {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
            }
        """)
        # Set explicit size constraints - increased for better visibility
        self.included_list.setMinimumHeight(150)
        self.included_list.setMaximumHeight(300)
        self.included_list.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.included_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.included_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        # Connect selection change to save functionality with error handling
        def safe_save_included():
            try:
                self.save_column_selections(node)
            except Exception as e:
                print(f"❌ Error in included list selection save: {e}")
        self.included_list.itemSelectionChanged.connect(safe_save_included)
        included_layout.addWidget(self.included_list)
        
        # Included columns buttons
        included_buttons_layout = QHBoxLayout()
        
        select_all_included_btn = QPushButton("Select All")
        select_all_included_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 3px 8px;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        select_all_included_btn.clicked.connect(lambda: self.included_list.selectAll())
        included_buttons_layout.addWidget(select_all_included_btn)
        
        clear_selection_included_btn = QPushButton("Clear Selection")
        clear_selection_included_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 3px 8px;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        clear_selection_included_btn.clicked.connect(lambda: self.included_list.clearSelection())
        included_buttons_layout.addWidget(clear_selection_included_btn)
        
        included_layout.addLayout(included_buttons_layout)
        
        # Move to excluded button
        move_to_excluded_btn = QPushButton("➡️ Move Selected to Excluded")
        move_to_excluded_btn.setStyleSheet("""
            QPushButton {
                background: #ff5722;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e64a19;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        move_to_excluded_btn.clicked.connect(lambda: self.move_columns_to_excluded(node))
        included_layout.addWidget(move_to_excluded_btn)
        
        # Excluded Columns Pane (Right)
        excluded_group = QGroupBox("❌ Excluded Columns (Will be dropped)")
        excluded_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background: #fff8f8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background: white;
                color: #e74c3c;
                font-weight: bold;
            }
        """)
        excluded_layout = QVBoxLayout(excluded_group)
        
        # Excluded columns list - create without parent, add to layout properly
        self.excluded_list = QListWidget()
        print(f"📋 WIDGET CREATION: excluded_list created: {bool(self.excluded_list)}")
        self.excluded_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e74c3c;
                border-radius: 3px;
                background: white;
                selection-background-color: #e74c3c;
                selection-color: white;
                color: black;
                min-height: 150px;
                max-height: 300px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #e0e0e0;
                color: black;
                min-height: 20px;
            }
            QListWidget::item:hover {
                background-color: #ffebee;
                color: black;
            }
            QListWidget::item:selected {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
            }
        """)
        # Set explicit size constraints - increased for better visibility
        self.excluded_list.setMinimumHeight(150)
        self.excluded_list.setMaximumHeight(300)
        self.excluded_list.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.excluded_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.excluded_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        # Connect selection change to save functionality with error handling
        def safe_save_excluded():
            try:
                self.save_column_selections(node)
            except Exception as e:
                print(f"❌ Error in excluded list selection save: {e}")
        self.excluded_list.itemSelectionChanged.connect(safe_save_excluded)
        excluded_layout.addWidget(self.excluded_list)
        
        # Excluded columns buttons
        excluded_buttons_layout = QHBoxLayout()
        
        select_all_excluded_btn = QPushButton("Select All")
        select_all_excluded_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 3px 8px;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        select_all_excluded_btn.clicked.connect(lambda: self.excluded_list.selectAll())
        excluded_buttons_layout.addWidget(select_all_excluded_btn)
        
        clear_selection_excluded_btn = QPushButton("Clear Selection")
        clear_selection_excluded_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 3px 8px;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        clear_selection_excluded_btn.clicked.connect(lambda: self.excluded_list.clearSelection())
        excluded_buttons_layout.addWidget(clear_selection_excluded_btn)
        
        excluded_layout.addLayout(excluded_buttons_layout)
        
        # Move to included button
        move_to_included_btn = QPushButton("⬅️ Move Selected to Included")
        move_to_included_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        move_to_included_btn.clicked.connect(lambda: self.move_columns_to_included(node))
        excluded_layout.addWidget(move_to_included_btn)
        
        # Add panes to container with central controls
        panes_container.addWidget(included_group)
        
        # Central control buttons
        central_controls_widget = QWidget()
        central_controls_widget.setMaximumWidth(120)
        central_controls_layout = QVBoxLayout(central_controls_widget)
        central_controls_layout.setContentsMargins(10, 50, 10, 50)
        
        # Move all to excluded
        move_all_to_excluded_btn = QPushButton("Move All ➡️")
        move_all_to_excluded_btn.setToolTip("Move all columns to excluded section")
        move_all_to_excluded_btn.setStyleSheet("""
            QPushButton {
                background: #ff9800;
                color: white;
                padding: 8px 10px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: #f57c00;
            }
        """)
        move_all_to_excluded_btn.clicked.connect(lambda: self.move_all_columns_to_excluded(node))
        central_controls_layout.addWidget(move_all_to_excluded_btn)
        
        central_controls_layout.addSpacing(10)
        
        # Move all to included
        move_all_to_included_btn = QPushButton("⬅️ Move All")
        move_all_to_included_btn.setToolTip("Move all columns to included section")
        move_all_to_included_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                padding: 8px 10px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        move_all_to_included_btn.clicked.connect(lambda: self.move_all_columns_to_included(node))
        central_controls_layout.addWidget(move_all_to_included_btn)
        
        central_controls_layout.addStretch()
        
        panes_container.addWidget(central_controls_widget)
        panes_container.addWidget(excluded_group)
        panes_layout.addLayout(panes_container)
        layout.addWidget(panes_group)
        
        # Load saved properties from node.properties (similar to domain node pattern)
        # Only load if properties exist and are not empty (don't override fresh initialization)
        if hasattr(node, 'properties') and node.properties:
            if 'included_columns' in node.properties and node.properties['included_columns']:
                node.included_columns = node.properties['included_columns']
                print(f"📋 LOADED: {len(node.included_columns)} included columns from saved properties")
            if 'excluded_columns' in node.properties and node.properties['excluded_columns']:
                node.excluded_columns = node.properties['excluded_columns']
                print(f"📋 LOADED: {len(node.excluded_columns)} excluded columns from saved properties")
        
        # Apply Configuration Section
        buttons_group = QGroupBox("🎯 Apply Configuration")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #28a745;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background: white;
                border-radius: 2px;
            }
        """)
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Apply and Execute button
        apply_execute_btn = QPushButton("🚀 Apply and Execute")
        apply_execute_btn.setToolTip("Apply column selections and execute filtering in one step")
        apply_execute_btn.setStyleSheet(BUTTON_STYLE_PRIMARY)
        apply_execute_btn.clicked.connect(lambda: self.apply_and_execute_column_keep_drop(node))
        buttons_layout.addWidget(apply_execute_btn)
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setToolTip("Cancel - Revert unsaved changes")
        cancel_btn.setStyleSheet(BUTTON_STYLE_DANGER)
        cancel_btn.clicked.connect(lambda: self.cancel_column_keep_drop(node))
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_group)
        
        # Add column keep/drop results section
        self.add_column_keep_drop_results_section(node, layout)
        
        # Spacer
        layout.addStretch()
        
        # Add all content to the main content layout
        self.content_layout.addWidget(container)
        
        # Store node reference
        self.current_node = node
        
        # Populate immediately since widgets now have proper parents
        print(f"📋 IMMEDIATE POPULATE: Populating lists with proper parent hierarchy")
        self.populate_column_lists_immediate(node)
    
    def populate_column_lists_immediate(self, node):
        """Immediate population with proper error handling."""
        try:
            print(f"📋 IMMEDIATE: Starting population for {node.title}")
            
            # Check widget existence first
            print(f"📋 IMMEDIATE: Checking widget existence...")
            print(f"   - hasattr included_list: {hasattr(self, 'included_list')}")
            print(f"   - hasattr excluded_list: {hasattr(self, 'excluded_list')}")
            print(f"   - included_list exists: {bool(getattr(self, 'included_list', None))}")
            print(f"   - excluded_list exists: {bool(getattr(self, 'excluded_list', None))}")
            
            # Clear and populate included list
            if self.included_list:
                print(f"📋 IMMEDIATE: included_list exists, parent: {self.included_list.parent()}")
                print(f"   - Current count before clear: {self.included_list.count()}")
                self.included_list.clear()
                print(f"   - Count after clear: {self.included_list.count()}")
                
                if hasattr(node, 'included_columns') and node.included_columns:
                    print(f"   - Node has {len(node.included_columns)} included columns")
                    self.included_list.addItems(node.included_columns)
                    print(f"✅ IMMEDIATE: Added {len(node.included_columns)} included columns")
                else:
                    print(f"   - Node has no included columns")
                    
                final_inc = self.included_list.count()
                print(f"📋 IMMEDIATE: Included list final count: {final_inc}")
            else:
                print(f"❌ IMMEDIATE: included_list is None or invalid")
            
            # Clear and populate excluded list
            if self.excluded_list:
                print(f"📋 IMMEDIATE: excluded_list exists, parent: {self.excluded_list.parent()}")
                print(f"   - Current count before clear: {self.excluded_list.count()}")
                self.excluded_list.clear()
                print(f"   - Count after clear: {self.excluded_list.count()}")
                
                if hasattr(node, 'excluded_columns') and node.excluded_columns:
                    print(f"   - Node has {len(node.excluded_columns)} excluded columns")
                    print(f"   - First few: {node.excluded_columns[:5]}")
                    self.excluded_list.addItems(node.excluded_columns)
                    print(f"✅ IMMEDIATE: Added {len(node.excluded_columns)} excluded columns")
                else:
                    print(f"   - Node has no excluded columns")
                    
                final_exc = self.excluded_list.count()
                print(f"📋 IMMEDIATE: Excluded list final count: {final_exc}")
            else:
                print(f"❌ IMMEDIATE: excluded_list is None or invalid")
            
            print(f"✅ IMMEDIATE: Population completed successfully")
            
        except Exception as e:
            print(f"❌ IMMEDIATE: Error during population: {e}")
            import traceback
            traceback.print_exc()
    
    def delayed_populate_column_lists(self, node):
        """Delayed population to ensure widgets are fully initialized."""
        print(f"📋 DELAYED POPULATE: Starting delayed population for {node.title}")
        
        # Check if widgets still exist and are valid
        if not hasattr(self, 'included_list') or not hasattr(self, 'excluded_list'):
            print(f"❌ DELAYED POPULATE: Widget attributes missing - widgets were deleted")
            return
            
        if not self.included_list or not self.excluded_list:
            print(f"❌ DELAYED POPULATE: Widget references are None - widgets were deleted")
            return
            
        try:
            # Test if widgets are actually functional
            inc_test = self.included_list.count()
            exc_test = self.excluded_list.count()
            inc_parent = self.included_list.parent()
            exc_parent = self.excluded_list.parent()
            
            print(f"📋 DELAYED POPULATE: Widget validation passed")
            print(f"   - included_list count test: {inc_test}, parent: {inc_parent}")
            print(f"   - excluded_list count test: {exc_test}, parent: {exc_parent}")
            
            # Now safely populate
            self.included_list.clear()
            if hasattr(node, 'included_columns') and node.included_columns:
                self.included_list.addItems(node.included_columns)
                print(f"✅ DELAYED POPULATE: Added {len(node.included_columns)} included columns")
            
            self.excluded_list.clear()
            if hasattr(node, 'excluded_columns') and node.excluded_columns:
                self.excluded_list.addItems(node.excluded_columns)
                print(f"✅ DELAYED POPULATE: Added {len(node.excluded_columns)} excluded columns")
            
            final_inc = self.included_list.count()
            final_exc = self.excluded_list.count()
            print(f"✅ DELAYED POPULATE: Final counts - included: {final_inc}, excluded: {final_exc}")
            
        except Exception as e:
            print(f"❌ DELAYED POPULATE: Widgets are corrupted: {e}")
            print(f"❌ DELAYED POPULATE: Widget corruption confirmed - this is a Qt parent/child hierarchy issue")
        
    def populate_column_lists(self, node):
        """Populate the included and excluded column lists with better performance."""
        try:
            print(f"📋 POPULATE: Starting populate_column_lists for {node.title if hasattr(node, 'title') else 'Unknown'}")
            
            # Debug current state
            included_count = len(getattr(node, 'included_columns', []))
            excluded_count = len(getattr(node, 'excluded_columns', []))
            print(f"📋 POPULATE: Node state - Included: {included_count}, Excluded: {excluded_count}")
            if excluded_count > 0:
                print(f"📋 POPULATE: First few excluded columns: {getattr(node, 'excluded_columns', [])[:5]}")
            
            # Debug widget existence and state
            print(f"📋 POPULATE: Widget state check:")
            print(f"   - hasattr included_list: {hasattr(self, 'included_list')}")
            print(f"   - hasattr excluded_list: {hasattr(self, 'excluded_list')}")
            if hasattr(self, 'included_list'):
                print(f"   - included_list valid: {bool(self.included_list)}")
                try:
                    print(f"   - included_list count: {self.included_list.count()}")
                except:
                    print(f"   - included_list count: ERROR")
            if hasattr(self, 'excluded_list'):
                print(f"   - excluded_list valid: {bool(self.excluded_list)}")
                try:
                    print(f"   - excluded_list count: {self.excluded_list.count()}")
                except:
                    print(f"   - excluded_list count: ERROR")
            
            # Temporarily disconnect signals to prevent cascading updates
            try:
                if hasattr(self, 'included_list') and self.included_list:
                    self.included_list.itemSelectionChanged.disconnect()
            except (RuntimeError, TypeError):
                print("📋 POPULATE: included_list signals already disconnected or invalid")
                
            try:
                if hasattr(self, 'excluded_list') and self.excluded_list:
                    self.excluded_list.itemSelectionChanged.disconnect()
            except (RuntimeError, TypeError):
                print("📋 POPULATE: excluded_list signals already disconnected or invalid")
            
            # Clear and populate lists efficiently
            included_success = False
            excluded_success = False
            
            if hasattr(self, 'included_list') and self.included_list:
                try:
                    # Force widget validation before using
                    test_count = self.included_list.count()  # Test if widget is valid
                    if not self.included_list.isVisible():
                        print(f"📋 POPULATE: included_list not visible - making visible")
                        self.included_list.setVisible(True)
                    
                    self.included_list.clear()
                    if hasattr(node, 'included_columns') and node.included_columns:
                        self.included_list.addItems(node.included_columns)
                        print(f"📋 POPULATE: Added {len(node.included_columns)} items to included list")
                        included_success = True
                    else:
                        print(f"📋 POPULATE: No included columns to add")
                        included_success = True
                    print(f"📋 POPULATE: Included list final count: {self.included_list.count()}")
                except Exception as e:
                    print(f"❌ POPULATE: Error with included list: {e}")
                    print(f"📋 POPULATE: included_list widget is corrupted - clearing reference")
                    self.included_list = None
            else:
                print(f"📋 POPULATE: included_list not available or invalid")
            
            if hasattr(self, 'excluded_list') and self.excluded_list:
                try:
                    # Force widget validation before using
                    test_count = self.excluded_list.count()  # Test if widget is valid
                    if not self.excluded_list.isVisible():
                        print(f"📋 POPULATE: excluded_list not visible - making visible")
                        self.excluded_list.setVisible(True)
                    
                    self.excluded_list.clear()
                    if hasattr(node, 'excluded_columns') and node.excluded_columns:
                        self.excluded_list.addItems(node.excluded_columns)
                        print(f"📋 POPULATE: Added {len(node.excluded_columns)} items to excluded list")
                        excluded_success = True
                    else:
                        print(f"📋 POPULATE: No excluded columns to add")
                        excluded_success = True
                    print(f"📋 POPULATE: Excluded list final count: {self.excluded_list.count()}")
                except Exception as e:
                    print(f"❌ POPULATE: Error with excluded list: {e}")
                    print(f"📋 POPULATE: excluded_list widget is corrupted - clearing reference")
                    self.excluded_list = None
            else:
                print(f"📋 POPULATE: excluded_list not available or invalid")
            
            # Report final status
            if included_success and excluded_success:
                print(f"✅ POPULATE: Both lists populated successfully!")
            else:
                print(f"❌ POPULATE: Failed to populate lists - included: {included_success}, excluded: {excluded_success}")
                print(f"❌ POPULATE: This indicates a fundamental widget corruption issue")
            
            # Reconnect signals with error handling
            if hasattr(self, 'included_list') and self.included_list:
                def safe_save_included():
                    try:
                        self.save_column_selections(node)
                    except Exception as e:
                        print(f"❌ Error in included list selection save: {e}")
                self.included_list.itemSelectionChanged.connect(safe_save_included)
                
            if hasattr(self, 'excluded_list') and self.excluded_list:
                def safe_save_excluded():
                    try:
                        self.save_column_selections(node)
                    except Exception as e:
                        print(f"❌ Error in excluded list selection save: {e}")
                self.excluded_list.itemSelectionChanged.connect(safe_save_excluded)
            
            included_count = len(node.included_columns) if hasattr(node, 'included_columns') and node.included_columns else 0
            excluded_count = len(node.excluded_columns) if hasattr(node, 'excluded_columns') and node.excluded_columns else 0
            print(f"📋 POPULATE: Populated lists: {included_count} included, {excluded_count} excluded")
            
        except Exception as e:
            print(f"❌ POPULATE: Error in populate_column_lists: {e}")
            import traceback
            traceback.print_exc()
    
    def move_columns_to_excluded(self, node):
        """Move selected columns from included to excluded list with better performance."""
        try:
            selected_items = self.included_list.selectedItems()
            if not selected_items:
                return
            
            # Process in batch
            columns_to_move = []
            for item in selected_items:
                column_name = item.text()
                if column_name in node.included_columns:
                    columns_to_move.append(column_name)
            
            # Batch update node data
            for column_name in columns_to_move:
                node.included_columns.remove(column_name)
                if column_name not in node.excluded_columns:
                    node.excluded_columns.append(column_name)
            
            # Single refresh and save
            self.populate_column_lists(node)
            self.save_column_selections(node)
            print(f"📋 Moved {len(columns_to_move)} columns to excluded")
            
        except Exception as e:
            print(f"❌ Error moving columns to excluded: {e}")
    
    def move_columns_to_included(self, node):
        """Move selected columns from excluded to included list with better performance."""
        try:
            selected_items = self.excluded_list.selectedItems()
            if not selected_items:
                return
            
            # Process in batch
            columns_to_move = []
            for item in selected_items:
                column_name = item.text()
                if column_name in node.excluded_columns:
                    columns_to_move.append(column_name)
            
            # Batch update node data
            for column_name in columns_to_move:
                node.excluded_columns.remove(column_name)
                if column_name not in node.included_columns:
                    node.included_columns.append(column_name)
            
            # Single refresh and save
            self.populate_column_lists(node)
            self.save_column_selections(node)
            print(f"📋 Moved {len(columns_to_move)} columns to included")
            
        except Exception as e:
            print(f"❌ Error moving columns to included: {e}")
    
    def move_all_columns_to_excluded(self, node):
        """Move ALL columns from included to excluded section."""
        try:
            if not node.included_columns:
                return
                
            # Move all at once
            columns_to_move = node.included_columns.copy()
            node.excluded_columns.extend(columns_to_move)
            node.included_columns.clear()
            
            # Single refresh and save
            self.populate_column_lists(node)
            self.save_column_selections(node)
            print(f"📋 Moved ALL {len(columns_to_move)} columns to excluded")
            
        except Exception as e:
            print(f"❌ Error moving all columns to excluded: {e}")
    
    def move_all_columns_to_included(self, node):
        """Move ALL columns from excluded to included section."""
        try:
            if not node.excluded_columns:
                return
                
            # Move all at once  
            columns_to_move = node.excluded_columns.copy()
            node.included_columns.extend(columns_to_move)
            node.excluded_columns.clear()
            
            # Single refresh and save
            self.populate_column_lists(node)
            self.save_column_selections(node)
            print(f"📋 Moved ALL {len(columns_to_move)} columns to included")
            
        except Exception as e:
            print(f"❌ Error moving all columns to included: {e}")
    
    def apply_and_execute_column_keep_drop(self, node):
        """Apply column selections and execute the filtering with robust error handling."""
        try:
            print(f"📋 Applying column keep/drop configuration...")
            
            # Validate node state
            if not hasattr(node, 'included_columns') or not hasattr(node, 'excluded_columns'):
                error_msg = "Node missing required column attributes"
                print(f"❌ {error_msg}")
                QMessageBox.critical(self, "Configuration Error", error_msg)
                return
            
            # Validate selection
            if not node.included_columns:
                QMessageBox.warning(self, "Invalid Selection", 
                                   "At least one column must be included!\n\n"
                                   "Please move some columns to the 'Included Columns' list.")
                return
            
            # Validate canvas and execution engine connection
            if not hasattr(self, '_canvas_ref') or not self._canvas_ref:
                error_msg = "No canvas reference available"
                print(f"❌ {error_msg}")
                QMessageBox.critical(self, "System Error", f"Internal error: {error_msg}")
                return
                
            if not hasattr(self._canvas_ref, 'execution_engine') or not self._canvas_ref.execution_engine:
                error_msg = "No execution engine available"
                print(f"❌ {error_msg}")
                QMessageBox.warning(self, "No Execution Engine", "Cannot execute - no execution engine available")
                return
            
            # Ensure node has canvas reference
            if not hasattr(node, 'canvas') or not node.canvas:
                print(f"📋 Setting canvas reference on node")
                node.canvas = self._canvas_ref
            
            # Check if node has input data available
            engine = self._canvas_ref.execution_engine
            input_data = None
            
            try:
                input_data = engine.get_node_input_data(node)
            except Exception as e:
                error_msg = f"Failed to get input data: {str(e)}"
                print(f"❌ {error_msg}")
                QMessageBox.critical(self, "Data Error", f"Cannot get input data:\n{error_msg}")
                return
            
            if input_data is None:
                error_msg = "No input data available. Please connect a data source to this node and execute the upstream nodes first."
                print(f"❌ {error_msg}")
                QMessageBox.warning(self, "No Input Data", error_msg)
                return
            
            print(f"📋 Input data validated: {input_data.shape}")
            
            # Validate that included columns exist in input data
            input_columns = list(input_data.columns)
            missing_columns = [col for col in node.included_columns if col not in input_columns]
            
            if missing_columns:
                error_msg = f"Selected columns not found in input data: {missing_columns}"
                print(f"❌ {error_msg}")
                QMessageBox.warning(self, "Column Mismatch", 
                                   f"The following selected columns are not available in the input data:\n\n"
                                   f"{', '.join(missing_columns)}\n\n"
                                   f"Available columns: {', '.join(input_columns)}")
                return
            
            # Execute the node with comprehensive error handling
            try:
                success = engine.execute_column_keep_drop_node(node)
                if success:
                    print(f"✅ Column keep/drop applied successfully")
                    
                    # Refresh the property panel to show results by recreating it
                    try:
                        self.create_column_keep_drop_properties(node)
                    except Exception as e:
                        print(f"⚠️ Warning: Failed to refresh property panel: {e}")
                        # Don't fail the whole operation if UI refresh fails
                    
                    # Ensure automatic data refresh happens
                    try:
                        print("🔄 COLUMN-KEEP-DROP: Ensuring data viewer refresh")
                        self.data_refresh_requested.emit(node)
                        print("🔄 COLUMN-KEEP-DROP: Data refresh signal emitted - viewer should update automatically")
                    except Exception as e:
                        print(f"⚠️ Warning: Failed to emit data refresh signal: {e}")
                    
                    # Emit flow change for downstream updates
                    try:
                        if hasattr(self._canvas_ref, 'flow_changed'):
                            self._canvas_ref.flow_changed.emit()
                    except Exception as e:
                        print(f"⚠️ Warning: Failed to emit flow change signal: {e}")
                        # Don't fail the whole operation if signal fails
                        
                    # Show success message
                    QMessageBox.information(self, "Success", 
                                          f"Column filtering applied successfully!\n\n"
                                          f"Kept {len(node.included_columns)} columns: {', '.join(node.included_columns)}")
                else:
                    error_msg = "Column keep/drop execution failed"
                    print(f"❌ {error_msg}")
                    QMessageBox.critical(self, "Execution Failed", error_msg)
                    
            except Exception as e:
                error_msg = f"Error during column keep/drop execution: {str(e)}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Execution Error", f"Failed to apply column keep/drop:\n{str(e)}")
                
        except Exception as e:
            error_msg = f"Unexpected error in apply_and_execute_column_keep_drop: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Critical Error", f"An unexpected error occurred:\n{str(e)}")
    
    def cancel_column_keep_drop(self, node):
        """Cancel column keep/drop changes."""
        print(f"📋 Canceling column keep/drop changes...")
        
        # Reset to default: all columns included, none excluded
        if node.available_columns:
            node.included_columns = node.available_columns.copy()
            node.excluded_columns = []
            
            # Refresh the lists
            self.populate_column_lists(node)
            print(f"📋 Reset to default: all {len(node.included_columns)} columns included")
        
    def add_column_keep_drop_results_section(self, node, layout):
        """Add column keep/drop results section (matching Expression node pattern exactly)."""
        # Check if node has been executed and show result
        execution_engine = self.get_execution_engine(node)
        if execution_engine:
            output_data = execution_engine.get_node_output_data(node)
            if output_data is not None:
                result_group = QGroupBox("📋 Column Keep/Drop Results")
                result_group.setStyleSheet("""
                    QGroupBox {
                        color: #27ae60;
                        border: 1px solid #999;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 2px;
                    }
                """)
                result_layout = QVBoxLayout(result_group)
                
                result_info = QLabel(f"✅ Column filtering applied: {len(output_data.columns)} columns kept from {len(node.available_columns)} total")
                result_info.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px; font-size: 13px;")
                result_layout.addWidget(result_info)
                
                # View transformed data button
                view_btn = QPushButton("👁️ View Transformed Data")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #17a2b8;
                        color: white;
                        padding: 5px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #138496;
                    }
                """)
                view_btn.clicked.connect(lambda: self.view_node_data(node, output_data, "Column Keep/Drop Transformed Data"))
                result_layout.addWidget(view_btn)
                
                layout.addWidget(result_group)
    
    def save_column_selections(self, node):
        """Save the current column selections to node properties for persistence"""
        try:
            print(f"📋 SAVE: Starting save_column_selections for {node.title if hasattr(node, 'title') else 'Unknown Node'}")
            
            # Safety check: ensure node exists and has required attributes
            if not node:
                print("❌ SAVE: No node provided")
                return
                
            if not hasattr(node, 'included_columns'):
                print("📋 SAVE: Initializing included_columns")
                node.included_columns = []
                
            if not hasattr(node, 'excluded_columns'):
                print("📋 SAVE: Initializing excluded_columns") 
                node.excluded_columns = []
            
            # Get current selections from the lists with safety checks
            included_columns = []
            excluded_columns = []
            
            if hasattr(self, 'included_list') and self.included_list:
                try:
                    for i in range(self.included_list.count()):
                        item = self.included_list.item(i)
                        if item and item.text():
                            included_columns.append(item.text())
                except Exception as e:
                    print(f"⚠️ SAVE: Error reading included_list: {e}")
            
            if hasattr(self, 'excluded_list') and self.excluded_list:
                try:
                    for i in range(self.excluded_list.count()):
                        item = self.excluded_list.item(i)
                        if item and item.text():
                            excluded_columns.append(item.text())
                except Exception as e:
                    print(f"⚠️ SAVE: Error reading excluded_list: {e}")
            
            # Update node attributes
            node.included_columns = included_columns
            node.excluded_columns = excluded_columns
            
            # FORCE save to node properties dict to ensure persistence (same pattern as domain nodes)
            if not hasattr(node, 'properties'):
                node.properties = {}
            node.properties['included_columns'] = included_columns
            node.properties['excluded_columns'] = excluded_columns
            
            print(f"📋 COLUMN KEEP/DROP: Saved {len(included_columns)} included, {len(excluded_columns)} excluded columns")
            print(f"📋 INCLUDED: {included_columns}")
            print(f"📋 EXCLUDED: {excluded_columns}")
            
            # Trigger workflow save to persist the selections
            try:
                if hasattr(node, 'canvas') and node.canvas and hasattr(node.canvas, 'flow_changed'):
                    node.canvas.flow_changed.emit()
                    print("📋 SAVE: Flow change signal emitted")
            except Exception as e:
                print(f"⚠️ SAVE: Error emitting flow change signal: {e}")
                # Don't let signal errors crash the save operation
            
        except Exception as e:
            print(f"❌ SAVE: Critical error in save_column_selections: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise to prevent crashes