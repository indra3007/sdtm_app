# Join Node - KNIME-style data joiner with multiple join types
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                           QPushButton, QFrame, QListWidget, QListWidgetItem,
                           QSplitter, QGroupBox, QRadioButton, QButtonGroup,
                           QCheckBox, QSpinBox, QTabWidget, QWidget, QTableWidget,
                           QTableWidgetItem, QHeaderView)
from PyQt6.QtGui import QFont
import pandas as pd


class JoinNode(BaseNode):
    """KNIME-style Join node for combining datasets"""
    
    def __init__(self):
        super().__init__()
        self.title = "🔗 Join"
        self.content_label.setText("Join datasets on key columns")
        
        # Join configuration
        self.join_type = "inner"  # inner, left, right, outer
        self.left_columns = []    # Columns from left dataset for joining
        self.right_columns = []   # Columns from right dataset for joining
        self.duplicate_handling = "append"  # append, skip
        self.column_suffix_left = "_left"
        self.column_suffix_right = "_right"
        
        # Available columns from input datasets
        self.left_available_columns = []
        self.right_available_columns = []
        
        # Duplicate column configuration
        self.duplicate_columns = []
        self.duplicate_column_settings = {}  # {col_name: {"action": "use_left"/"use_right"/"suffix"}}
        
        self.setupUI()
        
    def setupUI(self):
        """Setup the Join node UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🔗 Dataset Join Configuration")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Status info
        self.status_label = QLabel("Select join columns and type")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(self.status_label)
        
        # Set node content
        container = self.get_content_widget()
        container.setLayout(layout)
        
    def execute(self, left_data, right_data):
        """Execute the join operation"""
        try:
            print(f"🔗 JOIN EXECUTE: Starting join operation for {self.title}")
            
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
            print(f"🔗 JOIN EXECUTE: Join completed successfully")
            
            return result_df
            
        except Exception as e:
            print(f"❌ JOIN EXECUTE ERROR: {str(e)}")
            raise e
    
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
            "right_available_columns": self.right_available_columns
        }
    
    def set_properties(self, properties):
        """Set join configuration from saved properties"""
        self.join_type = properties.get("join_type", "inner")
        self.left_columns = properties.get("left_columns", [])
        self.right_columns = properties.get("right_columns", [])
        self.duplicate_handling = properties.get("duplicate_handling", "append")
        self.column_suffix_left = properties.get("column_suffix_left", "_left")
        self.column_suffix_right = properties.get("column_suffix_right", "_right")
        self.left_available_columns = properties.get("left_available_columns", [])
        self.right_available_columns = properties.get("right_available_columns", [])
        
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
            "right_available_columns": self.right_available_columns
        })
        return data
    
    def deserialize(self, data):
        """Deserialize join configuration from saved data"""
        super().deserialize(data)
        self.set_properties(data)
        
    def update_status(self):
        """Update the status label based on current configuration"""
        if not self.left_columns or not self.right_columns:
            self.status_label.setText("Select join columns for both datasets")
            self.status_label.setStyleSheet("QLabel { color: #ff6b6b; font-style: italic; }")
        else:
            join_info = f"{self.join_type.upper()} join on "
            join_pairs = []
            for i, (left_col, right_col) in enumerate(zip(self.left_columns, self.right_columns)):
                join_pairs.append(f"L.{left_col} = R.{right_col}")
            
            self.status_label.setText(f"{join_info}{', '.join(join_pairs)}")
            self.status_label.setStyleSheet("QLabel { color: #4ecdc4; font-style: italic; }")