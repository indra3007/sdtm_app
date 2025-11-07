"""
SDTM Specifications Viewer with AG-Grid
Displays loaded SDTM specifications in a user-friendly AG-Grid interface with full column expansion.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QComboBox, QLineEdit,
    QSplitter, QTextEdit, QGroupBox, QHeaderView, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import pandas as pd
import json


class SDTMSpecsViewer(QDialog):
    """Dialog for viewing SDTM specifications with AG-Grid interface."""
    
    def __init__(self, sdtm_raw_data, parent=None):
        super().__init__(parent)
        self.sdtm_raw_data = sdtm_raw_data  # Raw pandas DataFrames
        self.grid_cache = {}  # Cache for AG-Grid HTML content
        
        self.setWindowTitle("📋 SDTM Specifications Viewer")
        self.setModal(False)  # Allow interaction with main window
        
        # Enable maximize/minimize buttons and make window resizable
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.resize(1200, 800)  # Larger default size
        
        self.setup_ui()
        self.populate_specifications()
        
    def refresh_data(self, new_sdtm_raw_data):
        """Refresh the viewer with new data without recreating everything."""
        self.sdtm_raw_data = new_sdtm_raw_data
        self.grid_cache.clear()  # Clear cache for new data
        self.populate_specifications()
        
        # Update window title to show it's refreshed
        current_title = self.windowTitle()
        if "📋" not in current_title:
            self.setWindowTitle("📋 SDTM Specifications Viewer")
        
        self.log_refresh()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Header with summary
        header_layout = QHBoxLayout()
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        header_layout.addWidget(self.summary_label)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.populate_specifications)
        refresh_btn.setMaximumWidth(100)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main specifications tabs (removed codelist manager)
        self.specs_tabs = QTabWidget()
        layout.addWidget(self.specs_tabs)
        
        # Footer with actions  
        footer_layout = QHBoxLayout()
        
        footer_layout.addStretch()
        
        close_btn = QPushButton("✖️ Close")
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
        self.setLayout(layout)
        
        
    def log_refresh(self):
        """Log refresh activity."""
        try:
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'log_message'):
                self.parent().log_message(f"🔄 SDTM Specifications Viewer refreshed with {len(self.sdtm_raw_data)} sheets")
        except:
            pass
            
    def populate_specifications(self):
        """Populate the specifications viewer with loaded raw data using AG-Grid."""
        # Clear existing tabs
        self.specs_tabs.clear()
        
        if not self.sdtm_raw_data or len(self.sdtm_raw_data) == 0:
            self.summary_label.setText("❌ No SDTM specifications loaded")
            return
        
        # Show loading status
        self.summary_label.setText("🔄 Loading SDTM specifications...")
        
        total_rows = 0
        total_columns = 0
        
        # Process each DataFrame with progress indication
        for i, (sheet_name, df) in enumerate(self.sdtm_raw_data.items()):
            total_rows += len(df)
            total_columns += len(df.columns)
            
            # Update loading progress
            progress_text = f"🔄 Loading sheet {i+1}/{len(self.sdtm_raw_data)}: {sheet_name}"
            self.summary_label.setText(progress_text)
            
            # Create AG-Grid view for this sheet (with caching)
            ag_grid_view = self.create_aggrid_view(df, sheet_name)
            
            # Add tab
            self.specs_tabs.addTab(ag_grid_view, sheet_name)
        
        # Update final summary with success status
        summary_text = f"✅ Successfully loaded {total_rows:,} total rows across {len(self.sdtm_raw_data)} sheets"
        summary_text += f" | 📋 {total_columns} total columns"
        self.summary_label.setText(summary_text)
    
    def create_aggrid_view(self, df, sheet_name):
        """Create AG-Grid view for a DataFrame with auto-sizing columns and caching."""
        
        # Create cache key based on sheet name and data shape
        cache_key = f"{sheet_name}_{len(df)}_{len(df.columns)}_{hash(str(df.columns.tolist()))}"
        
        # Check cache first to improve performance
        if cache_key in self.grid_cache:
            web_view = QWebEngineView()
            web_view.setHtml(self.grid_cache[cache_key])
            return web_view
            
        web_view = QWebEngineView()
        
        # Prepare data for AG-Grid (limit to first 1000 rows for performance)
        max_rows = min(1000, len(df))  # Limit initial load for performance
        df_display = df.head(max_rows)
        
        grid_data = []
        for _, row in df_display.iterrows():
            row_dict = {}
            for col in df.columns:
                cell_value = row[col]
                if pd.isna(cell_value):
                    row_dict[col] = ""
                else:
                    # Truncate very long values for performance
                    str_value = str(cell_value)
                    if len(str_value) > 500:
                        str_value = str_value[:500] + "..."
                    row_dict[col] = str_value
            grid_data.append(row_dict)
        
        # Create column definitions with improved sizing and text wrapping
        column_defs = []
        for col in df.columns:
            column_defs.append({
                'headerName': col,
                'field': col,
                'sortable': True,
                'filter': True,
                'resizable': True,
                'minWidth': 80,  # Smaller minimum width
                'maxWidth': 300,  # Reasonable maximum width
                'wrapText': True,  # Enable text wrapping
                'autoHeight': True,  # Auto height for wrapped text
                'floatingFilter': True,  # Enable floating filters
                'cellStyle': {
                    'fontSize': '11px', 
                    'fontFamily': 'Arial, sans-serif',
                    'lineHeight': '1.2',
                    'padding': '4px',
                    'whiteSpace': 'normal',
                    'wordWrap': 'break-word'
                }
            })
        
        # Create HTML with AG-Grid
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/ag-grid-community.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 8px;
            font-family: Arial, sans-serif;
            background-color: #fafafa;
        }}
        .ag-theme-alpine {{
            --ag-grid-size: 6px;
            --ag-list-size: 6px;
            --ag-row-height: 28px;
            --ag-header-height: 32px;
            --ag-font-size: 11px;
            height: calc(100vh - 60px);
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .ag-header-cell-label {{
            font-weight: bold;
            font-size: 11px;
            color: #333;
        }}
        .ag-cell {{
            display: flex;
            align-items: flex-start;
            font-size: 11px;
            line-height: 1.2;
            padding: 4px 6px !important;
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }}
        .ag-cell-wrapper {{
            white-space: normal !important;
            word-wrap: break-word !important;
        }}
        .ag-row {{
            border-bottom: 1px solid #e0e0e0;
        }}
        .ag-row:hover {{
            background-color: #f5f5f5 !important;
        }}
        .sheet-title {{
            background: linear-gradient(135deg, #2196f3, #1976d2);
            color: white;
            padding: 10px 12px;
            border-radius: 4px 4px 0 0;
            font-weight: bold;
            font-size: 13px;
            margin-bottom: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .ag-floating-filter-input {{
            font-size: 10px !important;
            height: 24px !important;
        }}
    </style>
</head>
<body>
    <div class="sheet-title">
        📋 {sheet_name} - {len(df_display):,} of {len(df):,} rows × {len(df.columns)} columns
        {' (First 1000 rows shown for performance)' if len(df) > max_rows else ''}
    </div>
    <div id="myGrid" class="ag-theme-alpine"></div>
    
    <script type="text/javascript">
        const gridOptions = {{
            columnDefs: {json.dumps(column_defs)},
            rowData: {json.dumps(grid_data)},
            defaultColDef: {{
                sortable: true,
                filter: true,
                resizable: true,
                floatingFilter: true,
                wrapText: true,
                autoHeight: true,
                cellClass: 'text-wrap-cell'
            }},
            rowHeight: null, // Auto height based on content
            suppressRowHoverHighlight: false,
            rowSelection: 'single',
            animateRows: true,
            onGridReady: function(params) {{
                console.log('AG-Grid ready for {sheet_name}');
                
                // Auto-size columns to fit content but with reasonable limits
                setTimeout(() => {{
                    const allColumnIds = [];
                    params.api.getColumns().forEach(function(column) {{
                        allColumnIds.push(column.getId());
                    }});
                    
                    // Auto-size columns with skip header to get better content-based sizing
                    params.api.autoSizeColumns(allColumnIds, true);
                    
                    // Ensure no column is too narrow or too wide
                    params.api.getColumns().forEach(function(column) {{
                        const currentWidth = column.getActualWidth();
                        if (currentWidth < 80) {{
                            params.api.setColumnWidth(column, 80);
                        }} else if (currentWidth > 300) {{
                            params.api.setColumnWidth(column, 300);
                        }}
                    }});
                    
                    console.log('✅ {sheet_name}: Columns sized for optimal viewing');
                }}, 200);
            }},
            onFirstDataRendered: function(params) {{
                // Refresh row heights after data is rendered
                params.api.onRowHeightChanged();
            }},
            onColumnResized: function(params) {{
                if (params.finished) {{
                    // Recalculate row heights when columns are resized
                    params.api.onRowHeightChanged();
                }}
            }}
        }};
        
        const gridDiv = document.querySelector('#myGrid');
        agGrid.createGrid(gridDiv, gridOptions);
    </script>
</body>
</html>'''
        
        # Cache the HTML content for faster subsequent loads
        self.grid_cache[cache_key] = html_content
        
        # Add performance info for large datasets
        if len(df) > max_rows:
            # Add note about truncated data
            truncation_notice = f'''
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; margin: 5px; border-radius: 3px; font-size: 11px;">
                <strong>⚡ Performance Notice:</strong> Showing first {max_rows:,} rows of {len(df):,} total rows for optimal performance.
            </div>'''
            html_content = html_content.replace('<div id="myGrid"', truncation_notice + '<div id="myGrid"')
        
        web_view.setHtml(html_content)
        return web_view

