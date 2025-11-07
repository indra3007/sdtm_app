"""
Clean version of create_column_renamer_properties method to fix widget repetition issue.
This replaces the corrupted method that has duplicate sections.
"""

# Clean method implementation - replace lines 317-876 in property_panel.py
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
    
    # Table for rename mappings - Enhanced to fit 10-15 rows
    self.rename_table = QTableWidget(0, 3)
    self.rename_table.setHorizontalHeaderLabels(["Original Column", "New Column Name", "Action"])
    self.rename_table.horizontalHeader().setStretchLastSection(False)
    self.rename_table.setColumnWidth(0, 150)
    self.rename_table.setColumnWidth(1, 150)
    self.rename_table.setColumnWidth(2, 80)
    
    # Set minimum height to fit 10-15 rows comfortably
    row_height = 30  # Approximate row height including padding
    header_height = 25  # Header height
    min_rows = 10
    max_rows = 15
    min_height = header_height + (row_height * min_rows)
    max_height = header_height + (row_height * max_rows)
    
    self.rename_table.setMinimumHeight(min_height)  # ~325px for 10 rows
    self.rename_table.setMaximumHeight(max_height)  # ~475px for 15 rows
    
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
    
    # Set the layout (NEW standardized pattern)
    widget = QWidget()
    widget.setLayout(layout)
    self.setWidget(widget)
    
    # Store node reference
    self.current_node = node