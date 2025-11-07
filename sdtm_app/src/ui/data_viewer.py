"""
Data Viewer Component with Working ag-Grid Floating Filters
Enhanced PyQt6 component for displaying SDTM data with advanced filtering
"""

import os
import sys
import tempfile
import json
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QFrame,
    QFileDialog, QMessageBox, QSplitter, QDockWidget, QApplication
)
from PyQt6.QtCore import Qt, QUrl, QRect
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView

class DataPreviewTab(QWidget):
    """Enhanced data preview widget with ag-Grid floating filters."""
    
    def __init__(self):
        super().__init__()
        self.dataframe = None
        self.full_dataframe = None  # Store complete dataframe
        self.filename = ""
        self.temp_html_file = None
        self.use_webengine = True
        self.table = None
        self.web_view = None
        self._is_maximizing = False  # Flag to prevent interference during maximize operations
        
        # Data limiting settings
        self.show_limited_data = True
        self.current_row_limit = 1000
        self.max_safe_rows = 10000  # Warn user above this threshold
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the enhanced user interface for optimal data viewing."""
        layout = QVBoxLayout(self)
        layout.setSpacing(1)  # Minimal spacing for maximum data area
        layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        
        # Enhanced info bar - increased size for better visibility
        self.info_bar = QLabel("🔍 No data loaded")
        self.info_bar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #357abd);
                color: #ffffff;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                border: none;
                margin: 0px;
            }
        """)
        self.info_bar.setMaximumHeight(24)  # Increased from 16px
        self.info_bar.setMinimumHeight(24)
        layout.addWidget(self.info_bar)
        
        # Enhanced control bar for filters and actions - increased size
        control_layout = QHBoxLayout()
        control_layout.setSpacing(6)  # Increased spacing
        control_layout.setContentsMargins(4, 2, 4, 2)  # More padding
        
        # Filter controls with larger size for better visibility
        filter_label = QLabel("🔎")
        filter_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 2px;
                background-color: transparent;
            }
        """)
        filter_label.setMaximumHeight(28)  # Increased from 16px
        filter_label.setMinimumHeight(28)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter...")
        self.filter_input.setStyleSheet("""
            QLineEdit {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
                max-height: 28px;
                min-height: 28px;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
                background-color: #1e1e1e;
            }
        """)
        self.filter_input.textChanged.connect(self.apply_quick_filter)
        
        # Export button with enhanced styling - larger size
        self.export_btn = QPushButton("📤")
        self.export_btn.setToolTip("Export visible data")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                max-height: 28px;
                min-height: 28px;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: #6bb6ff;
            }
            QPushButton:pressed {
                background-color: #357abd;
            }
        """)
        
        # Refresh button - larger size
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh data view")
        self.refresh_btn.clicked.connect(self.refresh_view)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                max-height: 28px;
                min-height: 28px;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: #ffb74d;
            }
            QPushButton:pressed {
                background-color: #f57c00;
            }
        """)
        
        # Maximize button - larger size
        self.maximize_btn = QPushButton("⛶")
        self.maximize_btn.setToolTip("Maximize data viewer")
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                max-height: 28px;
                min-height: 28px;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: #ba68c8;
            }
            QPushButton:pressed {
                background-color: #7b1fa2;
            }
        """)
        
        # Data limiting controls - larger size
        self.limit_dropdown = QComboBox()
        self.limit_dropdown.addItems(["1K rows", "5K rows", "10K rows", "All rows"])
        self.limit_dropdown.setCurrentText("1K rows")  # Default to 1000 rows
        self.limit_dropdown.setToolTip("Select number of rows to display")
        self.limit_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
                max-height: 28px;
                min-height: 28px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
            }
        """)
        self.limit_dropdown.currentTextChanged.connect(self.on_limit_changed)
        
        self.view_all_btn = QPushButton("👁")
        self.view_all_btn.setToolTip("View all data (may be slow for large datasets)")
        self.view_all_btn.clicked.connect(self.view_all_data)
        self.view_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                max-height: 28px;
                min-height: 28px;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: #ef5350;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
        """)
        
        control_layout.addWidget(filter_label)
        control_layout.addWidget(self.filter_input, 1)
        control_layout.addWidget(self.limit_dropdown)
        control_layout.addWidget(self.view_all_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.maximize_btn)
        
        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        control_widget.setMaximumHeight(32)  # Increased from 18px
        control_widget.setMinimumHeight(32)
        layout.addWidget(control_widget)
        
        # Main data display area - this is where the web view or table will go
        self.data_container = QWidget()
        self.data_container.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.data_container, 1)  # Take remaining space
        
        # Set overall widget styling for dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #6bb6ff;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        
        # Initialize data display components
        self.initialize_data_display()
        
        # Set initial button states
        self.export_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        # maximize button is always enabled
        
    def initialize_data_display(self):
        """Initialize the data display components with proper scrolling."""
        # Create container layout for data display with minimal margins
        container_layout = QVBoxLayout(self.data_container)
        container_layout.setContentsMargins(1, 1, 1, 1)  # Minimal margins
        container_layout.setSpacing(0)  # No spacing between components
        
        # Try to create WebEngine view for ag-Grid
        try:
            self.web_view = QWebEngineView()
            # Ensure web view can scroll and show data properly
            self.web_view.setMinimumHeight(100)  # Ensure minimum space for data rows
            # Enable proper scrolling for web content
            self.web_view.settings().setAttribute(
                self.web_view.settings().WebAttribute.ScrollAnimatorEnabled, True
            )
            self.web_view.settings().setAttribute(
                self.web_view.settings().WebAttribute.TouchIconsEnabled, True
            )
            self.use_webengine = True
            container_layout.addWidget(self.web_view)
            print("✅ WebEngine initialized for ag-Grid with enhanced scrolling")
        except Exception as e:
            print(f"⚠️ WebEngine not available: {e}")
            self.use_webengine = False
        
        # Create fallback table widget with proper scrolling
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Enable comprehensive scrolling and ensure data rows are visible
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setMinimumHeight(100)  # Ensure minimum space for data rows
        
        # Enable horizontal scrolling behavior
        self.table.horizontalHeader().setStretchLastSection(False)  # Allow horizontal scrolling
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)  # Smooth scrolling
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)  # Smooth scrolling
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #404040;
                selection-background-color: #4a9eff;
                alternate-background-color: #2a2a2a;
                font-size: 9px;
                border: none;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 2px 4px;
                border: 1px solid #555555;
                font-weight: bold;
                font-size: 9px;
                max-height: 20px;
                min-height: 20px;
            }
            QScrollBar:vertical {
                background-color: #2e2e2e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar:horizontal {
                background-color: #2e2e2e;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                border: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        if not self.use_webengine:
            container_layout.addWidget(self.table)
        else:
            # Hide table initially if WebEngine is available
            self.table.hide()
            
        self.show_empty_state()
        
    def apply_quick_filter(self, text):
        """Apply quick filter to the displayed data."""
        if not self.dataframe is None and hasattr(self, 'table') and self.table.isVisible():
            # Simple table filtering for fallback mode
            for row in range(self.table.rowCount()):
                match = False
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text.lower() in item.text().lower():
                        match = True
                        break
                self.table.setRowHidden(row, not match)
        # For WebEngine/ag-Grid mode, filtering is handled by JavaScript
    
    def show_empty_state(self):
        """Show empty state in web view."""
        if not self.web_view:
            return
            
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Empty State</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 40px; background: #f8f9fa; text-align: center;
        }
        .empty-state {
            background: white; padding: 60px 40px; border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto;
        }
        .icon { font-size: 64px; margin-bottom: 20px; }
        .title { font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; }
        .subtitle { font-size: 16px; color: #7f8c8d; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="empty-state">
        <div class="icon">📊</div>
        <div class="title">No Data Loaded</div>
        <div class="subtitle">
            Execute a flow or load data to view it here.<br>
            ag-Grid with floating filters will appear when data is available.
        </div>
    </div>
</body>
</html>
"""
        self.web_view.setHtml(html_content)
    
    def show_empty_state_table(self):
        """Show empty state in table widget."""
        if not self.table:
            return
        
        self.table.clear()
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["No Data"])
        
        empty_item = QTableWidgetItem("📊 No data to display\nSelect a node and execute flow to view data")
        empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_item.setForeground(QColor('#999999'))
        
        self.table.setItem(0, 0, empty_item)
        self.table.resizeRowToContents(0)
        self.table.resizeColumnToContents(0)
        
    def set_dataframe(self, dataframe, filename="", source="Unknown", changed_columns=None):
        """Set the dataframe to preview with smart row limiting for performance.
        
        Args:
            dataframe: pandas DataFrame to display
            filename: name of the file/node
            source: source description
            changed_columns: list of column names that were changed/added in this transformation
        """
        print(f"📊 DATA VIEWER: set_dataframe called")
        print(f"📊 DATA VIEWER: filename='{filename}', source='{source}'")
        if dataframe is not None:
            print(f"📊 DATA VIEWER: dataframe shape: {dataframe.shape}")
            print(f"📊 DATA VIEWER: dataframe columns preview: {list(dataframe.columns)[:5]}...")
        else:
            print(f"📊 DATA VIEWER: dataframe is None")
        print(f"📊 DATA VIEWER: changed_columns: {changed_columns}")
        
        # Store the full dataframe
        self.full_dataframe = dataframe
        self.filename = filename
        self.changed_columns = changed_columns or []  # Store changed columns for highlighting
        
        # Get the display dataframe based on current limit settings
        self.dataframe = self.get_display_dataframe()
        print(f"📊 DATA VIEWER: display dataframe shape: {self.dataframe.shape if self.dataframe is not None else 'None'}")
        
        if self.full_dataframe is not None and not self.full_dataframe.empty:
            print(f"📊 DATA VIEWER: Dataframe is valid, setting up display...")
            # Try ag-Grid first if WebEngine is available
            if self.use_webengine and self.web_view:
                print(f"📊 DATA VIEWER: Using WebEngine ag-Grid display")
                try:
                    self.create_aggrid_view()
                    print(f"📊 DATA VIEWER: ag-Grid view created successfully")
                    # Hide table and show web view when ag-Grid loads successfully
                    self.web_view.show()
                    if self.table:
                        self.table.hide()
                    print(f"📊 DATA VIEWER: ag-Grid display completed")
                except Exception as e:
                    print(f"📊 DATA VIEWER: ag-Grid failed, using table fallback: {e}")
                    # If ag-Grid fails, show table and hide web view
                    if self.table:
                        self.populate_table()
                        self.table.show()
                    if self.web_view:
                        self.web_view.hide()
            else:
                # Use table fallback when WebEngine not available
                if self.table:
                    self.populate_table()
                    self.table.show()
                if self.web_view:
                    self.web_view.hide()
                        
            self.update_info_bar(source)
            self.export_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.limit_dropdown.setEnabled(True)
            self.view_all_btn.setEnabled(True)
            
            # Ensure data viewer is visible when data is loaded
            self.show_data_viewer()
        else:
            if self.use_webengine and self.web_view:
                self.show_empty_state()
                self.web_view.show()
                if self.table:
                    self.table.hide()
            else:
                self.show_empty_state_table()
                if self.web_view:
                    self.web_view.hide()
                    
            self.export_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.limit_dropdown.setEnabled(False)
            self.view_all_btn.setEnabled(False)
            self.info_bar.setText("No data loaded")
    
    def populate_table(self):
        """Populate the fallback table widget."""
        if self.dataframe is None or self.dataframe.empty:
            self.show_empty_state_table()
            return
        
        # Set table dimensions
        rows, cols = self.dataframe.shape
        self.table.setRowCount(min(rows, 1000))  # Limit rows for performance
        self.table.setColumnCount(cols)
        
        # Set compact row height for docked mode (like KNIME)
        self.table.verticalHeader().setDefaultSectionSize(20)  # Compact row height
        self.table.verticalHeader().hide()  # Hide row numbers to save space
        
        # Set headers
        self.table.setHorizontalHeaderLabels([str(col) for col in self.dataframe.columns])
        
        # Populate data
        for row_idx in range(min(rows, 1000)):
            for col_idx in range(cols):
                value = self.dataframe.iloc[row_idx, col_idx]
                
                # Handle different data types
                if pd.isna(value):
                    item = QTableWidgetItem("—")
                elif isinstance(value, (int, float)):
                    item = QTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem(str(value))
                
                # Make cells read-only
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Color coding for data types
                if pd.isna(self.dataframe.iloc[row_idx, col_idx]):
                    item.setForeground(QColor('#999999'))
                    font = QFont('Arial', 9)
                    font.setItalic(True)
                    item.setFont(font)  # Italic for NaN
                elif isinstance(self.dataframe.iloc[row_idx, col_idx], (int, float)):
                    item.setForeground(QColor('#1565c0'))  # Blue for numbers
                
                self.table.setItem(row_idx, col_idx, item)
        
        # Auto-resize columns to content (with limits)
        for col in range(self.table.columnCount()):
            self.table.resizeColumnToContents(col)
            # Limit column width
            if self.table.columnWidth(col) > 200:
                self.table.setColumnWidth(col, 200)
            elif self.table.columnWidth(col) < 80:
                self.table.setColumnWidth(col, 80)
    
    def create_aggrid_view(self):
        """Create ag-Grid view with working floating filters."""
        if self.dataframe is None:
            return
        
        # Prepare data - limit for performance
        sample_size = min(1000, len(self.dataframe))
        sample_df = self.dataframe.head(sample_size)
        
        # Convert to JSON
        data_json = sample_df.fillna("").to_json(orient='records', date_format='iso')
        
        # Create column definitions with automatic sizing
        column_defs = []
        for col in self.dataframe.columns:
            col_def = {
                'headerName': col,
                'field': col,
                'sortable': True,
                'filter': True,
                'floatingFilter': True,  # Enable floating filter
                'resizable': True,
                'suppressSizeToFit': False,  # Allow auto-sizing
                'filterParams': {
                    'buttons': ['reset', 'apply'],
                    'closeOnApply': True
                }
            }
            
            # Set filter type based on data type
            dtype = str(self.dataframe[col].dtype)
            if 'int' in dtype or 'float' in dtype:
                col_def['filter'] = 'agNumberColumnFilter'
                col_def['filterParams'].update({
                    'allowedCharPattern': '\\\\d\\\\-\\\\.',
                    'numberParser': 'parseFloat'
                })
            elif 'datetime' in dtype or 'date' in col.lower():
                col_def['filter'] = 'agDateColumnFilter'
                col_def['filterParams'].update({
                    'comparator': 'date',
                    'browserDatePicker': True
                })
            else:
                col_def['filter'] = 'agTextColumnFilter'
                col_def['filterParams'].update({
                    'filterOptions': ['contains', 'equals', 'startsWith', 'endsWith'],
                    'defaultOption': 'contains',
                    'caseSensitive': False
                })
                
            # Highlight changed/transformed columns instead of SDTM columns
            if hasattr(self, 'changed_columns') and self.changed_columns and col in self.changed_columns:
                col_def['headerClass'] = 'changed-header'
                col_def['cellClass'] = 'changed-cell'
            
            column_defs.append(col_def)

        # Create HTML with working ag-Grid
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Preview: {self.filename}</title>
    <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/ag-grid-community.min.js"></script>
    <style>
        body {{
            margin: 0; padding: 2px;  /* Even less padding */
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #ffffff;
            height: 100vh;
            overflow: hidden;
        }}
        
        #myGrid {{
            height: calc(100vh - 4px);  /* Maximize height for data visibility */
            width: 100%;
            min-height: 150px;          /* Ensure minimum height for data rows */
        }}
        
        .ag-theme-alpine {{
            --ag-row-height: 36px;        /* Standard row height */
            --ag-header-height: 44px;     /* Standard header height */
            --ag-floating-filter-height: 36px;  /* Standard floating filter */
            
            --ag-header-background-color: #f8f9fa;
            --ag-header-foreground-color: #2c3e50;
            --ag-border-color: #e9ecef;
            --ag-row-hover-color: #f5f7fa;
            --ag-selected-row-background-color: #e3f2fd;
            --ag-font-size: 12px;  /* Slightly smaller font for more data */
        }}
        
        .ag-header-cell-text {{
            font-weight: bold !important;
            color: #1976d2 !important;
        }}
        
        /* FINAL APPROACH: Make the outer container look exactly like the input */
        .ag-theme-alpine .ag-floating-filter,
        .ag-theme-alpine .ag-floating-filter-body,
        .ag-theme-alpine .ag-floating-filter-full-body,
        .ag-theme-alpine .ag-header-cell.ag-floating-filter {{
            background: #ffffff !important;         /* Same as input */
            background-color: #ffffff !important;   /* Same as input */
            border: 1px solid #d0d0d0 !important;   /* Same as input */
            border-radius: 3px !important;          /* Same as input */
            padding: 0px !important;                /* No padding */
            margin: 0px !important;                 /* No margin */
            box-shadow: none !important;
            outline: none !important;
        }}
        
        /* Make input borderless since container has the border */
        .ag-theme-alpine .ag-floating-filter-input,
        .ag-theme-alpine .ag-input-field-input {{
            border: none !important;                /* Remove input border */
            border-radius: 0px !important;          /* Remove input radius */
            padding: 4px 8px !important;
            font-size: 12px !important;
            background: transparent !important;     /* Transparent background */
            background-color: transparent !important;
            margin: 0px !important;
            width: 100% !important;
            height: auto !important;
            box-sizing: border-box !important;
            outline: none !important;
            box-shadow: none !important;
        }}
        
        /* Focus state - apply to container instead of input */
        .ag-theme-alpine .ag-floating-filter:focus-within,
        .ag-theme-alpine .ag-header-cell.ag-floating-filter:focus-within {{
            border-color: #2196f3 !important;
            box-shadow: 0 0 2px rgba(33, 150, 243, 0.3) !important;
        }}
        
        /* Remove any extra container styling */
        .ag-theme-alpine .ag-header-row-floating-filter,
        .ag-theme-alpine .ag-floating-filter-wrapper,
        .ag-theme-alpine .ag-input-wrapper {{
            background: transparent !important;
            border: none !important;
            padding: 0px !important;
            margin: 0px !important;
        }}
        
        .ag-theme-alpine .ag-floating-filter-input:focus,
        .ag-theme-alpine .ag-input-field-input:focus {{
            border-color: #2196f3 !important;
            box-shadow: 0 0 2px rgba(33, 150, 243, 0.3) !important;
            outline: none !important;
        }}
        
        .ag-theme-alpine .ag-floating-filter-input::placeholder,
        .ag-theme-alpine .ag-input-field-input::placeholder {{
            color: #999 !important;
            font-style: italic !important;
        }}
        
        /* Force remove any container styling */
        .ag-theme-alpine .ag-header-cell-filter-button {{
            display: none !important;  /* Hide filter button if it exists */
        }}
        
        /* Remove any possible wrapper backgrounds */
        .ag-theme-alpine .ag-header-viewport,
        .ag-theme-alpine .ag-header-container {{
            background: transparent !important;
        }}
        
        .changed-header {{
            background-color: #fff3e0 !important;
            font-weight: bold !important;
            color: #f57c00 !important;
            border-left: 3px solid #ff9800 !important;
        }}
        
        .changed-cell {{
            background-color: #fef7e4 !important;
        }}
        
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #666;
            z-index: 1000;
        }}
        
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="loading" class="loading">
        <div class="spinner"></div>
        <div>Loading data grid...</div>
    </div>
    
    <div id="myGrid" class="ag-theme-alpine" style="opacity: 0;"></div>

    <script>
        const columnDefs = {json.dumps(column_defs)};
        const rowData = {data_json};

        const gridOptions = {{
            columnDefs: columnDefs,
            rowData: rowData,
            
            // Default column settings - Enable auto-sizing but maintain filters
            defaultColDef: {{
                sortable: true,
                filter: true,
                floatingFilter: true,  // Enable floating filters
                resizable: true,
                cellStyle: {{ 'font-size': '13px' }},
                filterParams: {{
                    buttons: ['reset', 'apply'],
                    closeOnApply: true
                }},
                // Auto-sizing properties
                autoHeaderHeight: true,
                wrapHeaderText: true,
                suppressSizeToFit: false
            }},
            
            // Floating filter configuration - compact for docked mode
            floatingFiltersHeight: 25,  // Reduced from 40 for docked view
            headerHeight: 25,           // Reduced from 40 for docked view
            rowHeight: 22,              // Compact row height for more data visibility
            
            // Auto-sizing configuration
            columnTypes: {{
                'auto': {{
                    resizable: true,
                    sortable: true,
                    filter: true,
                    floatingFilter: true,
                    minWidth: 80,           // Minimum column width
                    maxWidth: 300           // Maximum column width
                }}
            }},
            
            // Grid options - optimized for docked view with horizontal scrolling
            animateRows: false,         // Disable animation for better performance in small space
            rowSelection: 'multiple',
            enableBrowserTooltips: true,
            enableCellTextSelection: true,
            suppressColumnVirtualisation: false,
            suppressHorizontalScroll: false,  // Ensure horizontal scrolling is enabled
            alwaysShowHorizontalScroll: false, // Show scroll only when needed
            
            // NO pagination for docked view - show all data with scrolling
            pagination: false,          // Disabled to show continuous data like KNIME
            
            // Enable virtual scrolling for performance
            rowBuffer: 10,
            maxBlocksInCache: 5,
            
            // Callbacks
            onGridReady: function(params) {{
                // Hide loading and show grid
                document.getElementById('loading').style.display = 'none';
                document.getElementById('myGrid').style.opacity = '1';
                
                // Store grid API
                window.gridApi = params.api;
                window.gridColumnApi = params.columnApi;
                
                // Auto-size columns to fit content, not container
                setTimeout(() => {{
                    params.api.autoSizeAllColumns(false);  // Don't skip header
                    console.log('✅ MAIN APP: Columns auto-sized to fit content with horizontal scroll');
                }}, 100);
                
                console.log('✅ MAIN APP: ag-Grid ready with auto-sized columns and floating filters!');
                console.log('🔍 MAIN APP: Look for search boxes below column headers!');
                console.log('📊 MAIN APP: Grid has', params.api.getDisplayedRowCount(), 'rows');
            }},
            
            onFirstDataRendered: function(params) {{
                // Auto-size columns when data is first rendered
                setTimeout(() => {{
                    params.api.autoSizeAllColumns(false);  // Don't skip header
                    console.log('🔄 MAIN APP: Columns auto-sized after data render with horizontal scroll');
                }}, 200);
            }},
            
            onGridSizeChanged: function(params) {{
                // Don't auto-size on resize to preserve horizontal scrolling
                console.log('📐 MAIN APP: Grid resized - maintaining column widths for horizontal scroll');
            }},
            
            onFilterChanged: function(params) {{
                const filterModel = params.api.getFilterModel();
                const filteredCount = params.api.getDisplayedRowCount();
                console.log(`🔍 MAIN APP: Filter changed - ${{filteredCount}} of {len(self.dataframe)} rows displayed`);
            }}
        }};

        // Initialize grid
        document.addEventListener('DOMContentLoaded', function() {{
            const gridDiv = document.querySelector('#myGrid');
            new agGrid.Grid(gridDiv, gridOptions);
        }});
    </script>
</body>
</html>
"""
        
        # Set HTML content
        self.web_view.setHtml(html_content)
        print(f"✅ MAIN APP: ag-Grid view created with {len(self.dataframe)} rows and floating filters enabled")
    
    def update_info_bar(self, source=""):
        """Update the info bar with minimal data info including row limiting status."""
        if self.full_dataframe is not None and not self.full_dataframe.empty:
            total_rows, cols = self.full_dataframe.shape
            row_info = self.get_row_info_text()
            # Very concise info with row limiting status
            text = f"{self.filename} • {row_info} × {cols} cols"
            if source:
                text += f" • {source}"
        else:
            text = "No data"
        
        self.info_bar.setText(text)
    
    def _clear_all_size_constraints(self):
        """Clear all size constraints for maximized mode - aggressive approach."""
        print("🔥 AGGRESSIVE size constraint clearing for maximize mode...")
        
        # Clear main widget constraints
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        
        # Clear data container constraints
        if hasattr(self, 'data_container') and self.data_container:
            self.data_container.setMinimumHeight(0)
            self.data_container.setMaximumHeight(16777215)
            self.data_container.setMinimumWidth(0)
            self.data_container.setMaximumWidth(16777215)
            print("📦 Data container: ALL size constraints cleared")
        
        # Clear data display component constraints with aggressive settings
        if hasattr(self, 'table') and self.table:
            self.table.setMinimumHeight(0)
            self.table.setMaximumHeight(16777215)
            self.table.setMinimumWidth(0)
            self.table.setMaximumWidth(16777215)
            # Set size policy to expanding
            from PyQt6.QtWidgets import QSizePolicy
            self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            print("📊 Table: ALL size constraints cleared + expanding policy set")
        
        if hasattr(self, 'web_view') and self.web_view:
            self.web_view.setMinimumHeight(0)
            self.web_view.setMaximumHeight(16777215)
            self.web_view.setMinimumWidth(0)
            self.web_view.setMaximumWidth(16777215)
            # Set size policy to expanding
            from PyQt6.QtWidgets import QSizePolicy
            self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            print("🌐 Web view: ALL size constraints cleared + expanding policy set")
        
        # Force layout updates
        self.updateGeometry()
        if hasattr(self, 'data_container'):
            self.data_container.updateGeometry()
        QApplication.processEvents()
    
    def _set_docked_size_constraints(self):
        """Set size constraints for docked mode - optimized for data visibility like KNIME."""
        print("🔒 Setting docked size constraints...")
        
        # Set main widget constraints for docked mode - slightly taller for data visibility
        self.setMinimumHeight(200)  # Increased from 180
        self.setMaximumHeight(250)  # Increased from 220
        
        # Set data container constraints for docked mode - more space for actual data
        if hasattr(self, 'data_container') and self.data_container:
            self.data_container.setMinimumHeight(170)  # Increased from 150
            self.data_container.setMaximumHeight(210)  # Increased from 190
            print("📦 Data container: Docked size constraints applied (increased for data visibility)")
        
        # Set data display component constraints for docked mode - optimized for KNIME-like view
        if hasattr(self, 'table') and self.table:
            self.table.setMinimumHeight(140)  # Increased from 120  
            self.table.setMaximumHeight(180)  # Same as before
            # Reset size policy to preferred for docked mode
            from PyQt6.QtWidgets import QSizePolicy
            self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            print("📊 Table: Docked size constraints applied + preferred policy set (optimized for data cells)")
        
        if hasattr(self, 'web_view') and self.web_view:
            self.web_view.setMinimumHeight(140)  # Increased from 120
            self.web_view.setMaximumHeight(180)  # Same as before
            # Reset size policy to preferred for docked mode
            from PyQt6.QtWidgets import QSizePolicy
            self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            print("🌐 Web view: Docked size constraints applied + preferred policy set (optimized for data cells)")
        
        # Force layout updates
        self.updateGeometry()
        if hasattr(self, 'data_container'):
            self.data_container.updateGeometry()
        QApplication.processEvents()

    def toggle_maximize(self):
        """Toggle maximize/restore state of the data viewer."""
        try:
            # Set flag to prevent visibility change interference
            self._is_maximizing = True
            
            # Find the dock widget parent
            dock_widget = self.parent()
            while dock_widget and not isinstance(dock_widget, QDockWidget):
                dock_widget = dock_widget.parent()
            
            if dock_widget:
                # If dock is hidden, show it first
                if not dock_widget.isVisible():
                    dock_widget.setVisible(True)
                    dock_widget.raise_()
                    self._is_maximizing = False
                    return
                
                # Use button text to determine current state (more reliable than isFloating)
                is_currently_maximized = self.maximize_btn.text() == "⬇ Restore"
                
                print(f"🔍 Dock widget found - Button shows: {self.maximize_btn.text()}, Currently maximized: {is_currently_maximized}")
                print(f"🔍 Dock state - Floating: {dock_widget.isFloating()}, Visible: {dock_widget.isVisible()}")
                
                if is_currently_maximized:
                    # Currently maximized, restore to docked mode
                    print("🔽 Restoring from maximized state...")
                    
                    # First set dock widget back to normal
                    dock_widget.showNormal()
                    dock_widget.setFloating(False)
                    
                    # Find the main window to properly re-dock
                    main_window = dock_widget.parent()
                    while main_window and not hasattr(main_window, 'addDockWidget'):
                        main_window = main_window.parent()
                    
                    # If we found the main window, explicitly re-add the dock widget
                    if main_window:
                        # Remove and re-add to ensure proper docking
                        main_window.removeDockWidget(dock_widget)
                        main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_widget)
                        print("📍 Re-docked to main window bottom area")
                    
                    # Set dock widget constraints for docked mode - taller for KNIME-like data visibility
                    dock_widget.setMinimumHeight(220)  # Increased from 200
                    dock_widget.setMaximumHeight(270)  # Increased from 240
                    
                    # Apply docked size constraints to all components
                    self._set_docked_size_constraints()
                    
                    # Ensure it's visible and raised
                    dock_widget.setVisible(True)
                    dock_widget.raise_()
                    
                    # Update button state
                    self.maximize_btn.setText("⛶ Maximize")
                    self.maximize_btn.setToolTip("Maximize data viewer to full screen")
                    print("✅ Data viewer restored to docked mode with size constraints")
                    
                else:
                    # Currently docked, maximize it
                    print("🔼 Maximizing to floating state...")
                    
                    # Clear ALL size constraints FIRST
                    dock_widget.setMinimumHeight(0)
                    dock_widget.setMaximumHeight(16777215)
                    self._clear_all_size_constraints()
                    
                    # Then make it floating
                    dock_widget.setFloating(True)
                    dock_widget.setVisible(True)
                    
                    # Give it a moment to process the floating state
                    QApplication.processEvents()
                    
                    # Get screen geometry for true maximization
                    screen = QApplication.primaryScreen()
                    screen_geometry = screen.availableGeometry()
                    
                    # Set the floating dock to cover the entire available screen (no margins)
                    new_geometry = QRect(
                        screen_geometry.x(),
                        screen_geometry.y(), 
                        screen_geometry.width(),
                        screen_geometry.height()
                    )
                    
                    print(f"🖥️ Setting geometry to: {new_geometry}")
                    dock_widget.setGeometry(new_geometry)
                    
                    # Ensure it's on top and active
                    dock_widget.raise_()
                    dock_widget.activateWindow()
                    dock_widget.setFocus()
                    
                    # Try to maximize the dock widget itself
                    dock_widget.showMaximized()
                    
                    # Force layout update and resize
                    QApplication.processEvents()
                    
                    # Force a second geometry setting after processEvents
                    dock_widget.setGeometry(new_geometry)
                    
                    # Force the internal components to resize to match the dock
                    if hasattr(self, 'data_container') and self.data_container:
                        container_geometry = QRect(0, 0, new_geometry.width(), new_geometry.height() - 80)  # Account for controls
                        self.data_container.setGeometry(container_geometry)
                        print(f"📦 Force-resized data container to: {container_geometry}")
                    
                    # One more process events to ensure everything is laid out
                    QApplication.processEvents()
                    
                    # Update button state
                    self.maximize_btn.setText("⬇ Restore")
                    self.maximize_btn.setToolTip("Restore data viewer to dock")
                    print("✅ Data viewer maximized - full screen mode with unrestricted data view")
                    
                    # Connect to visibility changed signal to reset button when closed
                    if not hasattr(self, '_visibility_connected'):
                        dock_widget.visibilityChanged.connect(self._on_dock_visibility_changed)
                        self._visibility_connected = True
                    
        except Exception as e:
            print(f"❌ Error toggling maximize state: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always clear the flag
            self._is_maximizing = False
    
    def _on_dock_visibility_changed(self, visible):
        """Handle dock widget visibility changes."""
        # Don't interfere if we're in the middle of a maximize operation
        if hasattr(self, '_is_maximizing') and self._is_maximizing:
            print("🚫 Ignoring visibility change during maximize operation")
            return
            
        if not visible:
            # Dock was closed/hidden, reset button state and restore size constraints
            dock_widget = self.parent()
            while dock_widget and not isinstance(dock_widget, QDockWidget):
                dock_widget = dock_widget.parent()
            
            if dock_widget:
                # Restore original dock widget size constraints - updated for better data visibility
                dock_widget.setMinimumHeight(220)  # Increased from 200
                dock_widget.setMaximumHeight(270)  # Increased from 240
                
                # Apply docked size constraints to all components
                self._set_docked_size_constraints()
            
            # Always reset button to maximize state when dock is closed
            self.maximize_btn.setText("⛶ Maximize")
            self.maximize_btn.setToolTip("Maximize data viewer to full screen")
    
    def on_limit_changed(self, limit_text):
        """Handle row limit dropdown change."""
        try:
            if limit_text == "All rows":
                self.show_limited_data = False
            else:
                self.show_limited_data = True
                # Extract number from text (e.g., "1K rows" -> 1000)
                if "1K" in limit_text:
                    self.current_row_limit = 1000
                elif "5K" in limit_text:
                    self.current_row_limit = 5000
                elif "10K" in limit_text:
                    self.current_row_limit = 10000
                    
            # Refresh the view with new limit
            self.refresh_view()
            
        except Exception as e:
            print(f"❌ Error changing row limit: {e}")
            
    def view_all_data(self):
        """Show all data with warning for large datasets."""
        try:
            if self.full_dataframe is not None and len(self.full_dataframe) > self.max_safe_rows:
                # Show warning for large datasets
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "View All Data",
                    f"This dataset has {len(self.full_dataframe):,} rows.\n"
                    f"Displaying all data may slow down the interface.\n\n"
                    f"Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
                    
            # Set to show all data
            self.limit_dropdown.setCurrentText("All rows")
            self.show_limited_data = False
            self.refresh_view()
            
        except Exception as e:
            print(f"❌ Error viewing all data: {e}")
            
    def get_display_dataframe(self):
        """Get the dataframe to display based on current limit settings."""
        if self.full_dataframe is None:
            return None
            
        if not self.show_limited_data:
            return self.full_dataframe
            
        # Return limited dataframe
        if len(self.full_dataframe) > self.current_row_limit:
            return self.full_dataframe.head(self.current_row_limit)
        else:
            return self.full_dataframe
            
    def get_row_info_text(self):
        """Get information text about displayed vs total rows."""
        if self.full_dataframe is None:
            return "No data"
            
        total_rows = len(self.full_dataframe)
        
        if not self.show_limited_data:
            return f"Showing all {total_rows:,} rows"
        else:
            displayed_rows = min(self.current_row_limit, total_rows)
            if displayed_rows < total_rows:
                return f"Showing {displayed_rows:,} of {total_rows:,} rows"
            else:
                return f"Showing all {total_rows:,} rows"
            print("🔽 Data viewer closed - button state reset to maximize")
    
    def show_data_viewer(self):
        """Ensure the data viewer is visible."""
        try:
            # Find the dock widget parent
            dock_widget = self.parent()
            while dock_widget and not isinstance(dock_widget, QDockWidget):
                dock_widget = dock_widget.parent()
            
            if dock_widget:
                dock_widget.setVisible(True)
                dock_widget.raise_()
                
                # If it's tabified with other docks, make sure it's the active tab
                if hasattr(dock_widget, 'raise_'):
                    dock_widget.raise_()
                    
        except Exception as e:
            print(f"Error showing data viewer: {e}")
    
    def export_data(self):
        """Export current dataframe to CSV."""
        if self.dataframe is None:
            return
            
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Data", 
                f"{self.filename.replace('.sas7bdat', '')}_export.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if filename:
                self.dataframe.to_csv(filename, index=False)
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Data exported to: {filename}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Error", 
                f"Failed to export data: {str(e)}"
            )
    
    def refresh_view(self):
        """Refresh the current view with updated row limiting."""
        if self.full_dataframe is not None:
            # Update the display dataframe based on current limit settings
            self.dataframe = self.get_display_dataframe()
            
            # Refresh the display
            if self.use_webengine and self.web_view:
                try:
                    self.create_aggrid_view()
                    self.web_view.show()
                    if self.table:
                        self.table.hide()
                except Exception as e:
                    print(f"ag-Grid refresh failed: {e}")
                    if self.table:
                        self.populate_table()
                        self.table.show()
                    if self.web_view:
                        self.web_view.hide()
            else:
                if self.table:
                    self.populate_table()
                    self.table.show()
                if self.web_view:
                    self.web_view.hide()
                    
            self.update_info_bar("Refreshed")
    
    def __del__(self):
        """Clean up temporary files."""
        if self.temp_html_file:
            try:
                os.unlink(self.temp_html_file)
            except:
                pass