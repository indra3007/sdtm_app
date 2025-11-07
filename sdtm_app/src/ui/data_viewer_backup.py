"""
Data Viewer - Tabular data display with filtering and analysis
Enhanced with ag-Grid for superior data viewing experience.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QLineEdit, QComboBox,
    QSpinBox, QTextEdit, QGroupBox, QFormLayout, QProgressBar,
    QHeaderView, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QColor
import pandas as pd
import numpy as np
import json
import tempfile
import os

# Try to import WebEngine, fall back to table if not available
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None


class DataViewer(QTabWidget):
    """Multi-tab data viewer with preview and profiling."""
    
    def __init__(self):
        super().__init__()
        self.current_dataframe = None
        self.current_filename = ""
        
        self.setup_tabs()
        
    def setup_tabs(self):
        """Setup viewer tabs."""
        # Data preview tab
        self.preview_tab = DataPreviewTab()
        self.addTab(self.preview_tab, "📊 Data Preview")
        
        # Data profile tab
        self.profile_tab = DataProfileTab()
        self.addTab(self.profile_tab, "📈 Data Profile")
        
        # Data quality tab
        self.quality_tab = DataQualityTab()
        self.addTab(self.quality_tab, "✅ Data Quality")
        
    def set_dataframe(self, dataframe, filename="", source="Unknown"):
        """Set the dataframe to display."""
        self.current_dataframe = dataframe
        self.current_filename = filename
        
        # Update all tabs
        self.preview_tab.set_dataframe(dataframe, filename, source)
        self.profile_tab.set_dataframe(dataframe, filename)
        self.quality_tab.set_dataframe(dataframe, filename)


class DataPreviewTab(QWidget):
    """Enhanced data preview with ag-Grid or fallback table for superior data viewing."""
    
    def __init__(self):
        super().__init__()
        self.dataframe = None
        self.filename = ""
        self.temp_html_file = None
        self.use_webengine = WEBENGINE_AVAILABLE
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup preview tab UI with ag-Grid or fallback table."""
        layout = QVBoxLayout(self)
        
        # Info bar
        self.info_bar = QLabel("No data loaded - Select a node or load data to view")
        self.info_bar.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
                color: #1565c0;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.info_bar)
        
        # ag-Grid Filter Help
        help_panel = QLabel("""
        🔍 <b>ag-Grid Advanced Filtering:</b> • Use floating filters below headers for quick search • Click filter icons in headers for advanced options • Use sidebar (right panel) for complex filtering • Right-click columns for more options
        """)
        help_panel.setStyleSheet("""
            QLabel {
                background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                color: #1565c0;
                border-left: 4px solid #2196f3;
                margin: 4px 0;
            }
        """)
        help_panel.setWordWrap(True)
        layout.addWidget(help_panel)
        
        # Controls (simplified - ag-Grid handles filtering)
        controls_layout = QHBoxLayout()
        
        # Export button
        self.export_btn = QPushButton("� Export Filtered Data")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        controls_layout.addWidget(self.export_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setEnabled(False)
        controls_layout.addWidget(self.refresh_btn)
        
        # View mode indicator
        if not self.use_webengine:
            mode_label = QLabel("📊 Table Mode")
            mode_label.setStyleSheet("color: #ff6b35; font-weight: bold; padding: 5px;")
            mode_label.setToolTip("WebEngine not available - using fallback table view")
            controls_layout.addWidget(mode_label)
        
        controls_layout.addStretch()
        
        # Data source indicator
        self.source_label = QLabel("Source: None")
        self.source_label.setStyleSheet("color: #666; font-style: italic;")
        controls_layout.addWidget(self.source_label)
        
        layout.addLayout(controls_layout)
        
        # Choose display method based on availability
        if self.use_webengine and QWebEngineView:
            # Web view for ag-Grid
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(400)
            layout.addWidget(self.web_view)
            self.table = None
        else:
            # Fallback to enhanced table widget
            self.web_view = None
            self.table = QTableWidget()
            self.setup_table_widget()
            layout.addWidget(self.table)
        
        # Load empty state
        self.show_empty_state()
    
    def setup_table_widget(self):
        """Setup the fallback table widget with enhanced features."""
        if not self.table:
            return
            
        # Enhanced table styling
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        
        # Header styling
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        
        # Styling
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                selection-background-color: #e3f2fd;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
        """)
        
    def show_empty_state(self):
        """Show empty state when no data is loaded."""
        empty_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f8f9fa;
            color: #6c757d;
            text-align: center;
        }
        .empty-state {
            max-width: 400px;
        }
        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        .empty-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #495057;
        }
        .empty-message {
            font-size: 14px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="empty-state">
        <div class="empty-icon">📊</div>
        <div class="empty-title">No Data to Display</div>
        <div class="empty-message">
            Load data or execute a flow to see results here.<br>
            Click on nodes after execution to view their transformed data.
        </div>
    </div>
</body>
</html>
        """
        if self.web_view:
            self.web_view.setHtml(empty_html)
    
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
        
    def set_dataframe(self, dataframe, filename="", source="Unknown"):
        """Set the dataframe to preview."""
        self.dataframe = dataframe
        self.filename = filename
        
        if dataframe is not None and not dataframe.empty:
            # Always try table first since ag-Grid CDN might fail
            if self.table:
                self.populate_table()
                self.table.show()
            
            # Try ag-Grid as enhancement if WebEngine is available
            if self.use_webengine and self.web_view:
                try:
                    self.create_aggrid_view()
                    # Don't hide table immediately - let ag-Grid load and then switch
                except Exception as e:
                    print(f"ag-Grid failed, using table fallback: {e}")
                    if self.web_view:
                        self.web_view.hide()
                        
            self.update_info_bar(source)
            self.export_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
        else:
            if self.use_webengine and self.web_view:
                self.show_empty_state()
                self.web_view.show()
                if self.table:
                    self.table.hide()
            else:
                self.show_empty_state_table()
                if self.table:
                    self.table.show()
                if self.web_view:
                    self.web_view.hide()
            self.export_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            
    def update_info_bar(self, source="Unknown"):
        """Update the info bar with current data information."""
        if self.dataframe is not None:
            row_count = len(self.dataframe)
            col_count = len(self.dataframe.columns)
            self.info_bar.setText(f"📊 {self.filename} | {row_count:,} rows × {col_count} columns | Source: {source}")
            self.source_label.setText(f"Source: {source}")
        else:
            self.info_bar.setText("No data loaded")
            self.source_label.setText("Source: None")
    
    def populate_table(self):
        """Populate the table widget with dataframe data."""
        if not self.table or self.dataframe is None or self.dataframe.empty:
            return
        
        # Clear table
        self.table.clear()
        
        # Set dimensions
        self.table.setRowCount(len(self.dataframe))
        self.table.setColumnCount(len(self.dataframe.columns))
        
        # Set column headers
        self.table.setHorizontalHeaderLabels(list(self.dataframe.columns))
        
        # Populate data
        for row_idx, (_, row) in enumerate(self.dataframe.iterrows()):
            for col_idx, value in enumerate(row):
                # Convert value to string and handle special cases
                if pd.isna(value):
                    display_value = ""
                elif isinstance(value, (int, float)):
                    if pd.isna(value):
                        display_value = ""
                    else:
                        display_value = str(value)
                else:
                    display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                
                # Make cells read-only
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Color coding for data types
                if pd.isna(row.iloc[col_idx]):
                    item.setForeground(QColor('#999999'))
                    font = QFont('Arial', 9)
                    font.setItalic(True)
                    item.setFont(font)  # Italic for NaN
                elif isinstance(row.iloc[col_idx], (int, float)):
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
        """Create ag-Grid HTML view for the current dataframe."""
        if self.dataframe is None or self.dataframe.empty:
            self.show_empty_state()
            return
            
        # Prepare data for ag-Grid - limit initial load for performance
        sample_size = min(1000, len(self.dataframe))
        sample_df = self.dataframe.head(sample_size)
        
        # Convert to JSON, handling NaN and datetime values
        data_json = sample_df.fillna("").to_json(orient='records', date_format='iso')
        
        # Create column definitions with enhanced ag-Grid filters
        column_defs = []
        for col in self.dataframe.columns:
            col_def = {
                'headerName': col,
                'field': col,
                'sortable': True,
                'filter': True,
                'resizable': True,
                'minWidth': 120,
                'floatingFilter': True,  # Enable floating filter row
                'filterParams': {
                    'buttons': ['reset', 'apply'],
                    'closeOnApply': True
                }
            }
            
            # Set appropriate filter type based on data type
            dtype = str(self.dataframe[col].dtype)
            if 'int' in dtype or 'float' in dtype:
                col_def['filter'] = 'agNumberColumnFilter'
                col_def['filterParams'].update({
                    'allowedCharPattern': '\\d\\-\\.',
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
                
            # Highlight SDTM columns
            if col.upper() in ['USUBJID', 'SUBJID', 'STUDYID', 'DOMAIN', 'AETERM', 'AESEV', 'AESTDTC', 'RFSTDTC', 'SITEID']:
                col_def['headerClass'] = 'sdtm-header'
                col_def['cellClass'] = 'sdtm-cell'
            
            column_defs.append(col_def)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Preview: {self.filename}</title>
    <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/ag-grid-community.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #ffffff;
        }}
        #myGrid {{
            height: calc(100vh - 60px);
            width: 100%;
        }}
        .ag-theme-alpine {{
            --ag-grid-size: 6px;
            --ag-list-item-height: 30px;
            --ag-row-height: 40px;
            --ag-header-height: 50px;
            --ag-floating-filter-height: 40px;
            
            --ag-header-background-color: #f8f9fa;
            --ag-header-foreground-color: #2c3e50;
            --ag-border-color: #e9ecef;
            --ag-row-hover-color: #f5f7fa;
            --ag-selected-row-background-color: #e3f2fd;
            --ag-font-size: 13px;
            
            /* Floating filter styling */
            --ag-input-border-color: #ced4da;
            --ag-input-border-color-invalid: #dc3545;
            --ag-input-focus-border-color: #007bff;
            
            /* Side panel styling */
            --ag-side-panel-background-color: #ffffff;
            --ag-panel-background-color: #f8f9fa;
        }}
        
        .ag-header-cell-text {{
            font-weight: bold !important;
            color: #1976d2 !important;
        }}
        
        .ag-floating-filter-input {{
            border: 2px solid #e0e0e0 !important;
            border-radius: 4px !important;
            padding: 6px 10px !important;
            font-size: 13px !important;
            background: #ffffff !important;
        }}
        
        .ag-floating-filter-input:focus {{
            border-color: #2196f3 !important;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2) !important;
            outline: none !important;
        }}
        
        .ag-floating-filter-input::placeholder {{
            color: #999 !important;
            font-style: italic !important;
        }}
        
        .ag-floating-filter {{
            background: #f9f9f9 !important;
            border-top: 1px solid #e0e0e0 !important;
        }}
        
        .ag-header-row-floating-filter {{
            background: linear-gradient(135deg, #f9f9f9 0%, #f0f0f0 100%) !important;
            border-bottom: 2px solid #e0e0e0 !important;
        }}
        
        .sdtm-header {{
            background-color: #e8f5e8 !important;
            font-weight: bold !important;
            color: #2e7d32 !important;
            border-left: 3px solid #4caf50 !important;
        }}
        
        .sdtm-cell {{
            background-color: #f1f8e9 !important;
                width: 100%; 
                border-collapse: collapse; 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
            `;
            
            // Create header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            headerRow.style.backgroundColor = '#f8f9fa';
            
            columnDefs.forEach(col => {{
                const th = document.createElement('th');
                th.textContent = col.headerName;
                th.style.cssText = `
                    padding: 12px 8px; 
                    text-align: left; 
                    font-weight: 600;
                    border-bottom: 2px solid #dee2e6;
                    cursor: pointer;
                    user-select: none;
                `;
                th.onclick = () => sortTable(table, col.field);
                headerRow.appendChild(th);
            }});
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            // Create body with pagination
            const tbody = document.createElement('tbody');
            const pageSize = 50;
            let currentPage = 0;
            
            function renderPage() {{
                tbody.innerHTML = '';
                const start = currentPage * pageSize;
                const end = Math.min(start + pageSize, rowData.length);
                
                for (let i = start; i < end; i++) {{
                    const row = rowData[i];
                    const tr = document.createElement('tr');
                    tr.style.cssText = `
                        border-bottom: 1px solid #e9ecef;
                        transition: background-color 0.15s;
                    `;
                    tr.onmouseover = () => tr.style.backgroundColor = '#f8f9fa';
                    tr.onmouseout = () => tr.style.backgroundColor = i % 2 ? '#ffffff' : '#f8f9fa';
                    tr.style.backgroundColor = i % 2 ? '#ffffff' : '#f8f9fa';
                    
                    columnDefs.forEach(col => {{
                        const td = document.createElement('td');
                        const value = row[col.field];
                        td.textContent = value === null || value === undefined ? '' : value;
                        td.style.cssText = `
                            padding: 8px; 
                            border-right: 1px solid #e9ecef;
                            max-width: 200px;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                        `;
                        
                        // Color coding based on data type
                        if (typeof value === 'number') {{
                            td.style.color = '#1565c0';
                            td.style.textAlign = 'right';
                        }} else if (value === null || value === undefined || value === '') {{
                            td.style.color = '#999999';
                            td.style.fontStyle = 'italic';
                            td.textContent = '—';
                        }}
                        
                        tr.appendChild(td);
                    }});
                    tbody.appendChild(tr);
                }}
            }}
            
            table.appendChild(tbody);
            gridDiv.appendChild(table);
            
            // Add pagination controls
            const pagination = document.createElement('div');
            pagination.style.cssText = `
                margin-top: 16px; 
                text-align: center; 
                padding: 12px;
                background: #f8f9fa;
                border-radius: 6px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;
            
            const pageInfo = document.createElement('span');
            const prevBtn = document.createElement('button');
            const nextBtn = document.createElement('button');
            
            prevBtn.textContent = '← Previous';
            nextBtn.textContent = 'Next →';
            
            [prevBtn, nextBtn].forEach(btn => {{
                btn.style.cssText = `
                    padding: 8px 16px;
                    border: 1px solid #007bff;
                    background: #007bff;
                    color: white;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                `;
                btn.onmouseover = () => btn.style.backgroundColor = '#0056b3';
                btn.onmouseout = () => btn.style.backgroundColor = '#007bff';
            }});
            
            prevBtn.onclick = () => {{
                if (currentPage > 0) {{
                    currentPage--;
                    renderPage();
                    updatePagination();
                }}
            }};
            
            nextBtn.onclick = () => {{
                if ((currentPage + 1) * pageSize < rowData.length) {{
                    currentPage++;
                    renderPage();
                    updatePagination();
                }}
            }};
            
            function updatePagination() {{
                const totalPages = Math.ceil(rowData.length / pageSize);
                pageInfo.textContent = `Page ${{currentPage + 1}} of ${{totalPages}} (Showing ${{currentPage * pageSize + 1}}-${{Math.min((currentPage + 1) * pageSize, rowData.length)}} of ${{rowData.length}} rows)`;
                prevBtn.disabled = currentPage === 0;
                nextBtn.disabled = (currentPage + 1) * pageSize >= rowData.length;
                
                if (prevBtn.disabled) {{
                    prevBtn.style.backgroundColor = '#6c757d';
                    prevBtn.style.borderColor = '#6c757d';
                    prevBtn.style.cursor = 'not-allowed';
                }}
                if (nextBtn.disabled) {{
                    nextBtn.style.backgroundColor = '#6c757d';
                    nextBtn.style.borderColor = '#6c757d';
                    nextBtn.style.cursor = 'not-allowed';
                }}
            }}
            
            pagination.appendChild(prevBtn);
            pagination.appendChild(pageInfo);
            pagination.appendChild(nextBtn);
            
            gridDiv.appendChild(pagination);
            
            // Initial render
            renderPage();
            updatePagination();
            
            console.log('Lightweight grid created successfully');
        }}
        
        // Simple sorting function
        function sortTable(table, field) {{
            console.log('Sorting by:', field);
            // Sort rowData and re-render
            rowData.sort((a, b) => {{
                const aVal = a[field];
                const bVal = b[field];
                if (aVal === bVal) return 0;
                if (aVal === null || aVal === undefined) return 1;
                if (bVal === null || bVal === undefined) return -1;
                return aVal > bVal ? 1 : -1;
            }});
            
            // Re-render current page
            const tbody = table.querySelector('tbody');
            const pageSize = 50;
            const currentPage = 0; // Reset to first page after sort
            
            tbody.innerHTML = '';
            const start = currentPage * pageSize;
            const end = Math.min(start + pageSize, rowData.length);
            
            for (let i = start; i < end; i++) {{
                const row = rowData[i];
                const tr = document.createElement('tr');
                tr.style.cssText = `border-bottom: 1px solid #e9ecef;`;
                tr.style.backgroundColor = i % 2 ? '#ffffff' : '#f8f9fa';
                
                columnDefs.forEach(col => {{
                    const td = document.createElement('td');
                    const value = row[col.field];
                    td.textContent = value === null || value === undefined ? '—' : value;
                    td.style.cssText = `padding: 8px; border-right: 1px solid #e9ecef; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`;
                    
                    if (typeof value === 'number') {{
                        td.style.color = '#1565c0';
                        td.style.textAlign = 'right';
                    }} else if (value === null || value === undefined || value === '') {{
                        td.style.color = '#999999';
                        td.style.fontStyle = 'italic';
                    }}
                    
                    tr.appendChild(td);
                }});
                tbody.appendChild(tr);
            }}
        }}
    </script>
    <style>
        body {{
            margin: 0;
            padding: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #ffffff;
        }}
        #myGrid {{
            height: calc(100vh - 60px);
            width: 100%;
        }}
        .ag-theme-alpine {{
            --ag-header-background-color: #f8f9fa;
            --ag-header-foreground-color: #2c3e50;
            --ag-border-color: #e9ecef;
            --ag-row-hover-color: #f5f7fa;
            --ag-selected-row-background-color: #e3f2fd;
            --ag-font-size: 13px;
            --ag-header-height: 45px;
            --ag-row-height: 35px;
            
            /* Floating filter styling */
            --ag-input-border-color: #ced4da;
            --ag-input-border-color-invalid: #dc3545;
            --ag-input-focus-border-color: #007bff;
            --ag-floating-filter-height: 40px;
            
            /* Side panel styling */
            --ag-side-panel-background-color: #ffffff;
            --ag-panel-background-color: #f8f9fa;
        }}
        
        /* Enhanced floating filter styling */
        .ag-floating-filter-input {{
            border: 2px solid #e0e0e0 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            font-size: 13px !important;
            background: #ffffff !important;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1) !important;
        }}
        
        .ag-floating-filter-input:focus {{
            border-color: #2196f3 !important;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2) !important;
            outline: none !important;
        }}
        
        .ag-floating-filter-input::placeholder {{
            color: #999 !important;
            font-style: italic !important;
        }}
        
        .ag-floating-filter {{
            background: #f9f9f9 !important;
            border-top: 1px solid #e0e0e0 !important;
        }}
        
        .ag-header-row-floating-filter {{
            background: linear-gradient(135deg, #f9f9f9 0%, #f0f0f0 100%) !important;
            border-bottom: 2px solid #e0e0e0 !important;
        }}
        
        .sdtm-header {{
            background-color: #e8f5e8 !important;
            font-weight: bold !important;
            color: #2e7d32 !important;
            border-left: 3px solid #4caf50 !important;
        }}
        
        .sdtm-cell {{
            background-color: #f1f8e9 !important;
            font-weight: 500 !important;
        }}
        
        /* Custom styling for floating filters */
        .ag-floating-filter-input {{
            border-radius: 4px !important;
            border: 1px solid #ced4da !important;
            padding: 4px 8px !important;
        }}
        
        .ag-floating-filter-input:focus {{
            border-color: #007bff !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
        }}
        
        /* Side panel styling */
        .ag-side-panel {{
            border-left: 2px solid #e9ecef !important;
        }}
        
        .ag-tool-panel-wrapper {{
            background-color: #ffffff !important;
        }}
        
        /* Filter tool panel */
        .ag-filter-toolpanel-header {{
            background-color: #f8f9fa !important;
            font-weight: bold !important;
            color: #495057 !important;
            padding: 8px 12px !important;
        }}
        
        /* Advanced filter builder button */
        .ag-filter-apply-panel-button {{
            background-color: #007bff !important;
            border-color: #007bff !important;
            color: white !important;
            border-radius: 4px !important;
            padding: 6px 12px !important;
            font-weight: 500 !important;
        }}
        
        .ag-filter-apply-panel-button:hover {{
            background-color: #0056b3 !important;
        }}
        .info-panel {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    <div class="info-panel">
        📊 <strong>{self.filename}</strong> • Showing {sample_size:,} of {len(self.dataframe):,} rows × {len(self.dataframe.columns)} columns • Interactive filtering and sorting enabled
    </div>
    
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
            
            // Default column settings - simplified like working test
            defaultColDef: {{
                flex: 1,
                minWidth: 120,
                sortable: true,
                filter: true,
                floatingFilter: true,  // Key: explicitly enable floating filters
                resizable: true,
                cellStyle: {{ 'font-size': '13px' }},
                filterParams: {{
                    buttons: ['reset', 'apply'],
                    closeOnApply: true
                }}
            }},
            
            // Floating filter configuration
            floatingFiltersHeight: 40,
            
            // Basic grid options
            animateRows: true,
            rowSelection: 'multiple',
            
            // Enable tooltips
            enableBrowserTooltips: true,
            
            // Pagination
            pagination: true,
            paginationPageSize: 100,
            paginationPageSizeSelector: [25, 50, 100, 200, 500],
            
            // Grid ready callback
            onGridReady: function(params) {{
                // Hide loading indicator and show grid
                document.getElementById('loading').style.display = 'none';
                document.getElementById('myGrid').style.opacity = '1';
                
                // Auto-size columns to fit content
                params.api.sizeColumnsToFit();
                
                // Store grid API for potential use
                window.gridApi = params.api;
                window.gridColumnApi = params.columnApi;
                
                console.log('✅ ag-Grid ready with floating filters!');
                console.log('🔍 Look for search boxes below column headers!');
            }},
            
            // First data rendered callback
            onFirstDataRendered: function(params) {{
                // Auto-size columns after data is rendered
                params.api.sizeColumnsToFit();
            }},
            
            // Filter change callback
            onFilterChanged: function(params) {{
                const filterModel = params.api.getFilterModel();
                console.log('🔍 Filter changed:', filterModel);
                
                const filteredRowCount = params.api.getDisplayedRowCount();
                console.log('Filtered rows:', filteredRowCount, 'of', {len(self.dataframe)});
            }}
        }};

        // Create the grid - simplified like working test
        document.addEventListener('DOMContentLoaded', function() {{
            const gridDiv = document.querySelector('#myGrid');
            new agGrid.Grid(gridDiv, gridOptions);
        }});
    </script>
</body>
</html>
        
        # Set HTML content
        self.web_view.setHtml(html_content)
        print(f"✅ ag-Grid view created with {len(self.dataframe)} rows and floating filters enabled")
    
    def export_data(self):
        """Export current dataframe to CSV."""
        if self.dataframe is None:
            return
            
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            
            suggested_name = f"{self.filename.replace('.sas7bdat', '')}_exported.csv" if self.filename else "data_export.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Data to CSV",
                suggested_name,
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                self.dataframe.to_csv(file_path, index=False)
                QMessageBox.information(self, "✅ Export Complete", 
                                      f"Data exported successfully!\n\n"
                                      f"File: {os.path.basename(file_path)}\n"
                                      f"Rows: {len(self.dataframe):,}\n"
                                      f"Columns: {len(self.dataframe.columns)}")
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "❌ Export Error", f"Failed to export data:\n{str(e)}")
    
    def refresh_data(self):
        """Refresh the data view."""
        if self.dataframe is not None:
            self.apply_all_filters()
            
    def toggle_column_filters(self):
        """Toggle the visibility of column-specific filters."""
        if self.filters_visible:
            self.filters_panel.hide()
            self.toggle_filters_btn.setText("🔽 Show Column Filters")
            self.filters_visible = False
        else:
            self.setup_column_filters()
            self.filters_panel.show()
            self.toggle_filters_btn.setText("🔼 Hide Column Filters")
            self.filters_visible = True
            
    def setup_column_filters(self):
        """Setup individual column filter widgets."""
        # Clear existing filters
        for i in reversed(range(self.filters_layout.count())):
            child = self.filters_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        self.column_filter_widgets = {}
        
        if self.dataframe is None:
            return
        
        # Add filters for each column
        for column in self.dataframe.columns:
            filter_group = QWidget()
            filter_layout = QVBoxLayout(filter_group)
            filter_layout.setContentsMargins(8, 8, 8, 8)
            
            # Column label
            col_label = QLabel(column)
            col_label.setStyleSheet("font-weight: bold; color: #333; font-size: 11px;")
            filter_layout.addWidget(col_label)
            
            # Filter input
            if self.dataframe[column].dtype in ['object', 'string']:
                # Text filter for string columns
                filter_input = QLineEdit()
                filter_input.setPlaceholderText(f"Filter {column}...")
                filter_input.textChanged.connect(lambda text, col=column: self.update_column_filter(col, text))
            else:
                # Numeric filter for numeric columns
                filter_input = QLineEdit()
                filter_input.setPlaceholderText("e.g., >50, <100, 25-75")
                filter_input.textChanged.connect(lambda text, col=column: self.update_numeric_filter(col, text))
            
            filter_input.setStyleSheet("""
                QLineEdit {
                    padding: 4px 6px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    font-size: 11px;
                    background: white;
                }
                QLineEdit:focus {
                    border-color: #2196f3;
                }
            """)
            
            filter_layout.addWidget(filter_input)
            self.column_filter_widgets[column] = filter_input
            
            # Add unique values preview for string columns (limit to 5)
            if self.dataframe[column].dtype in ['object', 'string']:
                unique_vals = self.dataframe[column].dropna().unique()[:5]
                if len(unique_vals) > 0:
                    preview_text = "Values: " + ", ".join([str(v)[:15] + ("..." if len(str(v)) > 15 else "") for v in unique_vals])
                    if len(self.dataframe[column].dropna().unique()) > 5:
                        preview_text += f" (+{len(self.dataframe[column].dropna().unique()) - 5} more)"
                    
                    preview_label = QLabel(preview_text)
                    preview_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
                    preview_label.setWordWrap(True)
                    filter_layout.addWidget(preview_label)
            
            filter_group.setFixedWidth(180)
            filter_group.setStyleSheet("""
                QWidget {
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    margin: 2px;
                }
            """)
            
            self.filters_layout.addWidget(filter_group)
        
        # Add stretch to push filters to left
        self.filters_layout.addStretch()
        
    def update_column_filter(self, column, text):
        """Update text filter for a column."""
        if text.strip():
            self.column_filters[column] = text.strip().lower()
        else:
            self.column_filters.pop(column, None)
        
        self.apply_all_filters()
        
    def update_numeric_filter(self, column, text):
        """Update numeric filter for a column."""
        if text.strip():
            self.column_filters[column] = text.strip()
        else:
            self.column_filters.pop(column, None)
        
        self.apply_all_filters()
        
    def apply_global_filter(self, search_text):
        """Apply global search filter across all columns."""
        self.global_search_text = search_text.lower().strip()
        self.apply_all_filters()
        
    def apply_column_filter(self, column_name):
        """Apply filter to show only specific column."""
        # This updates the column dropdown selection
        self.apply_all_filters()
        
    def clear_search(self):
        """Clear all search and filters."""
        self.global_search.clear()
        self.column_filter.setCurrentText("All Columns")
        
        # Clear column-specific filters
        for widget in self.column_filter_widgets.values():
            widget.clear()
        self.column_filters.clear()
        
        self.apply_all_filters()
        
    def apply_all_filters(self):
        """Apply all active filters and refresh display."""
        if self.dataframe is None:
            return
        
        df = self.dataframe.copy()
        
        # Apply global search filter
        if hasattr(self, 'global_search_text') and self.global_search_text:
            mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(self.global_search_text, na=False)).any(axis=1)
            df = df[mask]
        
        # Apply column-specific filters
        for column, filter_value in self.column_filters.items():
            if column not in df.columns:
                continue
                
            if df[column].dtype in ['object', 'string']:
                # Text filter - partial match
                mask = df[column].astype(str).str.lower().str.contains(filter_value, na=False)
                df = df[mask]
            else:
                # Numeric filter - support various formats
                try:
                    df = self.apply_numeric_filter(df, column, filter_value)
                except:
                    pass  # Skip invalid numeric filters
        
        # Apply column selection filter
        selected_column = self.column_filter.currentText()
        if selected_column != "All Columns" and selected_column in df.columns:
            df = df[[selected_column]]
        
        self.filtered_dataframe = df
        
        # Update display with filtered data
        if self.table and not self.use_webengine:
            self.populate_table_with_data(df)
        elif self.use_webengine and self.web_view:
            self.create_aggrid_with_data(df)
        
        # Update info
        total_rows = len(self.dataframe) if self.dataframe is not None else 0
        filtered_rows = len(df)
        filter_info = f" (filtered from {total_rows:,})" if filtered_rows != total_rows else ""
        
        self.info_bar.setText(f"📊 {self.filename} | {filtered_rows:,} rows × {len(df.columns)} columns{filter_info}")
        
    def apply_numeric_filter(self, df, column, filter_text):
        """Apply numeric filter with various operators."""
        filter_text = filter_text.strip()
        
        if '-' in filter_text and not filter_text.startswith('-'):
            # Range filter: e.g., "25-75"
            try:
                parts = filter_text.split('-')
                min_val = float(parts[0])
                max_val = float(parts[1])
                return df[(df[column] >= min_val) & (df[column] <= max_val)]
            except:
                return df
                
        elif filter_text.startswith('>='):
            # Greater than or equal
            try:
                val = float(filter_text[2:])
                return df[df[column] >= val]
            except:
                return df
                
        elif filter_text.startswith('<='):
            # Less than or equal
            try:
                val = float(filter_text[2:])
                return df[df[column] <= val]
            except:
                return df
                
        elif filter_text.startswith('>'):
            # Greater than
            try:
                val = float(filter_text[1:])
                return df[df[column] > val]
            except:
                return df
                
        elif filter_text.startswith('<'):
            # Less than
            try:
                val = float(filter_text[1:])
                return df[df[column] < val]
            except:
                return df
                
        elif filter_text.startswith('!='):
            # Not equal
            try:
                val = float(filter_text[2:])
                return df[df[column] != val]
            except:
                return df
                
        else:
            # Exact match or contains
            try:
                val = float(filter_text)
                return df[df[column] == val]
            except:
                # Treat as string contains
                return df[df[column].astype(str).str.contains(filter_text, na=False)]
        
    def populate_table_with_data(self, df):
        """Populate table widget with specific dataframe."""
        if not self.table or df is None or df.empty:
            return
        
        # Clear table
        self.table.clear()
        
        # Set dimensions
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        
        # Set column headers
        self.table.setHorizontalHeaderLabels(list(df.columns))
        
        # Populate data
        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, value in enumerate(row):
                # Convert value to string and handle special cases
                if pd.isna(value):
                    display_value = ""
                else:
                    display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Color coding for data types
                if pd.isna(row.iloc[col_idx]):
                    item.setForeground(QColor('#999999'))
                    font = QFont('Arial', 9)
                    font.setItalic(True)
                    item.setFont(font)
                elif isinstance(row.iloc[col_idx], (int, float)):
                    item.setForeground(QColor('#1565c0'))
                
                self.table.setItem(row_idx, col_idx, item)
        
        # Auto-resize columns
        for col in range(self.table.columnCount()):
            self.table.resizeColumnToContents(col)
            if self.table.columnWidth(col) > 200:
                self.table.setColumnWidth(col, 200)
            elif self.table.columnWidth(col) < 80:
                self.table.setColumnWidth(col, 80)
                
    def create_aggrid_with_data(self, df):
        """Create ag-Grid with specific dataframe."""
        # Store current data and call existing method
        original_df = self.dataframe
        self.dataframe = df
        self.create_aggrid_view()
        self.dataframe = original_df  # Restore original
            
    def __del__(self):
        """Clean up temp files."""
        if self.temp_html_file:
            try:
                os.unlink(self.temp_html_file)
            except:
                pass


class DataProfileTab(QWidget):
    """Data profiling and statistics."""
    
    def __init__(self):
        super().__init__()
        self.dataframe = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup profile tab UI."""
        layout = QVBoxLayout(self)
        
        # Summary statistics
        summary_group = QGroupBox("Summary Statistics")
        summary_layout = QFormLayout(summary_group)
        
        self.summary_labels = {}
        for stat in ["Shape", "Memory Usage", "Missing Values", "Duplicates"]:
            label = QLabel("N/A")
            self.summary_labels[stat] = label
            summary_layout.addRow(f"{stat}:", label)
            
        layout.addWidget(summary_group)
        
        # Column statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setHorizontalHeaderLabels([
            "Column", "Type", "Count", "Missing", "Unique", "Mean", "Std", "Min", "Max"
        ])
        layout.addWidget(self.stats_table)
        
    def set_dataframe(self, dataframe, filename=""):
        """Set dataframe and calculate profile."""
        self.dataframe = dataframe
        self.calculate_profile()
        
    def calculate_profile(self):
        """Calculate data profile statistics."""
        if self.dataframe is None:
            return
            
        df = self.dataframe
        
        # Summary statistics
        shape = f"{df.shape[0]} rows × {df.shape[1]} columns"
        memory = f"{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
        missing = f"{df.isnull().sum().sum()} ({df.isnull().sum().sum() / df.size * 100:.1f}%)"
        duplicates = f"{df.duplicated().sum()}"
        
        self.summary_labels["Shape"].setText(shape)
        self.summary_labels["Memory Usage"].setText(memory)
        self.summary_labels["Missing Values"].setText(missing)
        self.summary_labels["Duplicates"].setText(duplicates)
        
        # Column statistics
        stats_data = []
        for col in df.columns:
            series = df[col]
            stats = {
                "Column": col,
                "Type": str(series.dtype),
                "Count": len(series.dropna()),
                "Missing": series.isnull().sum(),
                "Unique": series.nunique()
            }
            
            # Numeric statistics
            if pd.api.types.is_numeric_dtype(series):
                stats.update({
                    "Mean": f"{series.mean():.2f}" if not series.isnull().all() else "N/A",
                    "Std": f"{series.std():.2f}" if not series.isnull().all() else "N/A",
                    "Min": f"{series.min()}" if not series.isnull().all() else "N/A",
                    "Max": f"{series.max()}" if not series.isnull().all() else "N/A"
                })
            else:
                stats.update({"Mean": "N/A", "Std": "N/A", "Min": "N/A", "Max": "N/A"})
                
            stats_data.append(stats)
            
        # Populate table
        self.stats_table.setRowCount(len(stats_data))
        for row, stats in enumerate(stats_data):
            for col, key in enumerate(["Column", "Type", "Count", "Missing", "Unique", "Mean", "Std", "Min", "Max"]):
                item = QTableWidgetItem(str(stats[key]))
                if key == "Missing" and stats[key] > 0:
                    item.setBackground(Qt.GlobalColor.yellow)
                self.stats_table.setItem(row, col, item)
                
        self.stats_table.resizeColumnsToContents()


class DataQualityTab(QWidget):
    """Data quality assessment for SDTM compliance."""
    
    def __init__(self):
        super().__init__()
        self.dataframe = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup quality tab UI."""
        layout = QVBoxLayout(self)
        
        # Quality checks
        checks_group = QGroupBox("SDTM Quality Checks")
        checks_layout = QVBoxLayout(checks_group)
        
        self.checks_text = QTextEdit()
        self.checks_text.setReadOnly(True)
        self.checks_text.setMaximumHeight(200)
        checks_layout.addWidget(self.checks_text)
        
        layout.addWidget(checks_group)
        
        # Issues table
        issues_group = QGroupBox("Issues Found")
        issues_layout = QVBoxLayout(issues_group)
        
        self.issues_table = QTableWidget()
        self.issues_table.setHorizontalHeaderLabels([
            "Severity", "Rule", "Column", "Description", "Count"
        ])
        issues_layout.addWidget(self.issues_table)
        
        layout.addWidget(issues_group)
        
    def set_dataframe(self, dataframe, filename=""):
        """Set dataframe and run quality checks."""
        self.dataframe = dataframe
        self.run_quality_checks(filename)
        
    def run_quality_checks(self, filename=""):
        """Run SDTM quality checks."""
        if self.dataframe is None:
            return
            
        df = self.dataframe
        issues = []
        
        # Determine domain from filename
        domain = filename.split('.')[0].upper() if filename else "UNKNOWN"
        
        # SDTM-specific checks
        if domain == "DM":
            issues.extend(self.check_dm_domain(df))
        elif domain == "AE":
            issues.extend(self.check_ae_domain(df))
        elif domain == "AES":
            issues.extend(self.check_aes_domain(df))
            
        # General SDTM checks
        issues.extend(self.check_general_sdtm(df))
        
        # Display results
        self.display_quality_results(issues)
        
    def check_dm_domain(self, df):
        """Check DM domain specific rules."""
        issues = []
        
        # Required variables
        required_vars = ["USUBJID", "SUBJID", "RFSTDTC", "RFENDTC"]
        for var in required_vars:
            if var not in df.columns:
                issues.append({
                    "Severity": "Error",
                    "Rule": "Required Variable",
                    "Column": var,
                    "Description": f"Required DM variable {var} is missing",
                    "Count": 1
                })
                
        # Date format checks
        date_vars = [col for col in df.columns if col.endswith("DTC")]
        for var in date_vars:
            if var in df.columns:
                invalid_dates = df[var].dropna().apply(self.is_invalid_iso_date).sum()
                if invalid_dates > 0:
                    issues.append({
                        "Severity": "Warning",
                        "Rule": "Date Format",
                        "Column": var,
                        "Description": f"Invalid ISO 8601 date format",
                        "Count": invalid_dates
                    })
                    
        return issues
        
    def check_ae_domain(self, df):
        """Check AE domain specific rules."""
        issues = []
        
        # Required variables
        required_vars = ["USUBJID", "AETERM", "AESTDTC"]
        for var in required_vars:
            if var not in df.columns:
                issues.append({
                    "Severity": "Error",
                    "Rule": "Required Variable",
                    "Column": var,
                    "Description": f"Required AE variable {var} is missing",
                    "Count": 1
                })
                
        return issues
        
    def check_aes_domain(self, df):
        """Check AES domain specific rules."""
        issues = []
        
        # Required variables for supplemental
        required_vars = ["USUBJID", "QNAM", "QVAL"]
        for var in required_vars:
            if var not in df.columns:
                issues.append({
                    "Severity": "Error",
                    "Rule": "Required Variable",
                    "Column": var,
                    "Description": f"Required AES variable {var} is missing",
                    "Count": 1
                })
                
        return issues
        
    def check_general_sdtm(self, df):
        """Check general SDTM rules."""
        issues = []
        
        # USUBJID consistency
        if "USUBJID" in df.columns:
            missing_usubjid = df["USUBJID"].isnull().sum()
            if missing_usubjid > 0:
                issues.append({
                    "Severity": "Error",
                    "Rule": "Missing Key",
                    "Column": "USUBJID",
                    "Description": "Missing USUBJID values",
                    "Count": missing_usubjid
                })
                
        return issues
        
    def is_invalid_iso_date(self, date_str):
        """Check if date string is valid ISO 8601 format."""
        try:
            pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S')
            return False
        except:
            try:
                pd.to_datetime(date_str, format='%Y-%m-%d')
                return False
            except:
                return True
                
    def display_quality_results(self, issues):
        """Display quality check results."""
        # Summary text
        total_issues = len(issues)
        errors = len([i for i in issues if i["Severity"] == "Error"])
        warnings = len([i for i in issues if i["Severity"] == "Warning"])
        
        summary = f"""Quality Check Summary:
Total Issues: {total_issues}
Errors: {errors}
Warnings: {warnings}

Status: {'❌ Failed' if errors > 0 else '⚠️ Warnings' if warnings > 0 else '✅ Passed'}
"""
        self.checks_text.setText(summary)
        
        # Issues table
        self.issues_table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            for col, key in enumerate(["Severity", "Rule", "Column", "Description", "Count"]):
                item = QTableWidgetItem(str(issue[key]))
                if issue["Severity"] == "Error":
                    item.setBackground(Qt.GlobalColor.red)
                elif issue["Severity"] == "Warning":
                    item.setBackground(Qt.GlobalColor.yellow)
                self.issues_table.setItem(row, col, item)
                
        self.issues_table.resizeColumnsToContents()