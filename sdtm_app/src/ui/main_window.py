"""
Main Window for SDTM Flow Builder Application
Provides the primary user interface with toolbars, canvas, and property panels.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QMenuBar, QStatusBar, QDockWidget, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QApplication, QMenu
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDir, QMimeData, QThread
from PyQt6.QtGui import QAction, QIcon, QPixmap, QDrag
import os
import time
import psutil
import pandas as pd
from pathlib import Path


class SDTMProcessingThread(QThread):
    """Background thread for SDTM processing operations to keep UI responsive."""
    
    progress_updated = pyqtSignal(int, str)  # percentage, message
    processing_completed = pyqtSignal(object, str)  # result, operation_type
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, operation_type, target_function, *args, **kwargs):
        super().__init__()
        self.operation_type = operation_type
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        self.should_cancel = False
        
    def run(self):
        """Execute the processing operation in background."""
        try:
            self.progress_updated.emit(0, f"Starting {self.operation_type}...")
            
            # Execute the target function
            result = self.target_function(*self.args, **self.kwargs)
            
            if not self.should_cancel:
                self.progress_updated.emit(100, f"{self.operation_type} completed")
                self.processing_completed.emit(result, self.operation_type)
            
        except Exception as e:
            self.error_occurred.emit(f"Error in {self.operation_type}: {str(e)}")
            
    def cancel(self):
        """Cancel the current operation."""
        self.should_cancel = True


class MemoryMonitor:
    """Monitor application memory usage for performance optimization."""
    
    def __init__(self):
        try:
            self.process = psutil.Process()
        except:
            self.process = None
            
    def get_memory_usage_mb(self):
        """Get current memory usage in MB."""
        if self.process:
            try:
                return self.process.memory_info().rss / 1024 / 1024
            except:
                return 0
        return 0
        
    def get_memory_info_text(self):
        """Get formatted memory usage text."""
        memory_mb = self.get_memory_usage_mb()
        if memory_mb > 0:
            if memory_mb > 1000:
                return f"Memory: {memory_mb/1024:.1f} GB"
            else:
                return f"Memory: {memory_mb:.0f} MB"
        return "Memory: N/A"


class DraggableTreeWidget(QTreeWidget):
    """Custom tree widget that supports proper drag and drop."""
    
    def startDrag(self, supportedActions):
        """Start drag operation with proper mime data."""
        item = self.currentItem()
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(item.data(0, Qt.ItemDataRole.UserRole))
            drag.setMimeData(mimeData)
            drag.exec(Qt.DropAction.CopyAction)

from .flow_canvas import FlowCanvas
from .property_panel import PropertyPanel
from .data_viewer import DataPreviewTab
from .project_dialog import ProjectDialog
from data.data_manager import DataManager
from data.project_manager import ProjectManager


class MainWindow(QMainWindow):
    """Main application window with modern UI layout."""
    
    # Signals
    data_loaded = pyqtSignal(str, object, str)  # filename, dataframe, file_path
    
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.project_manager = ProjectManager()
        self.current_project_path = None
        self.current_flow = None
        
        # SDTM Specifications storage
        self.sdtm_specifications = {}  # Will store controlled terminology mappings
        
        # Track current workflow for smart saving
        self.current_workflow_name = None
        self.current_workflow_file = None
        self.workflow_modified = False
        
        # Performance monitoring and optimization
        self.memory_monitor = MemoryMonitor()
        self.processing_thread = None
        
        self.init_ui()
        self.create_menus()
        self.create_toolbars()
        self.create_dock_widgets()
        self.setup_status_bar()
        
        # Set canvas reference on property panel for connection checking
        self.property_panel.set_canvas_reference(self.flow_canvas)
        
        # Connect signals
        self.data_loaded.connect(self.on_data_loaded)
        self.connect_signals()
        
    def connect_signals(self):
        """Connect UI signals after all components are created."""
        # Connect initial flow canvas signals
        self.connect_canvas_signals(self.flow_canvas)
        
        # Connect property panel data refresh requests (works for all canvases)
        self.property_panel.data_refresh_requested.connect(self.on_node_selected_for_data_view)
        
    def connect_canvas_signals(self, canvas):
        """Connect signals for a specific canvas."""
        # Connect flow canvas node selection to property panel
        canvas.node_selected.connect(self.property_panel.show_properties)
        # Connect flow canvas node selection to data viewer
        canvas.node_selected.connect(self.on_node_selected_for_data_view)
        # Connect flow changes to refresh property panel for current node
        canvas.flow_changed.connect(self.on_flow_changed)
    
    def initialize_execution_engine(self, canvas=None):
        """Initialize the execution engine for the specified flow canvas or current active one."""
        try:
            from data.execution_engine import FlowExecutionEngine
            
            # Use provided canvas or get current active canvas
            target_canvas = canvas if canvas else self.get_current_canvas()
            if not target_canvas:
                print("❌ MAIN WINDOW: No canvas available for execution engine initialization")
                return
            
            # Create execution engine and store it on the canvas
            target_canvas.execution_engine = FlowExecutionEngine(target_canvas)
            print(f"🚀 MAIN WINDOW: Execution engine initialized for canvas: {target_canvas}")
            
        except Exception as e:
            print(f"❌ MAIN WINDOW: Failed to initialize execution engine: {e}")

    def get_current_canvas(self):
        """Get the currently active workflow canvas."""
        current_widget = self.workflow_tabs.currentWidget()
        if isinstance(current_widget, FlowCanvas):
            return current_widget
        return None
    
    def get_current_workflow_name(self):
        """Get the name of the currently active workflow."""
        current_index = self.workflow_tabs.currentIndex()
        if current_index >= 0 and current_index in self.workflow_metadata:
            return self.workflow_metadata[current_index]['name']
        return "Unknown Workflow"
    
    def add_custom_close_button(self, tab_index):
        """Add a custom close button to a specific tab."""
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtCore import Qt
        
        # Create close button
        close_button = QPushButton("×")
        close_button.setFixedSize(16, 16)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #cccccc;
                font-weight: bold;
                font-size: 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #ff4444;
                color: white;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
        """)
        
        # Connect to close function
        close_button.clicked.connect(lambda: self.close_workflow_tab(tab_index))
        
        # Add button to tab bar
        self.workflow_tabs.tabBar().setTabButton(tab_index, self.workflow_tabs.tabBar().ButtonPosition.RightSide, close_button)
    
    def close_workflow_tab(self, index):
        """Close a workflow tab with confirmation if modified."""
        if index < 0 or index >= self.workflow_tabs.count():
            return
        
        workflow_meta = self.workflow_metadata.get(index, {})
        workflow_name = workflow_meta.get('name', f'Workflow {index + 1}')
        
        # Check if workflow has unsaved changes
        if workflow_meta.get('modified', False):
            reply = QMessageBox.question(
                self, 
                'Close Workflow',
                f'Workflow "{workflow_name}" has unsaved changes.\n\nDo you want to save before closing?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_workflow(index):
                    return  # Cancel close if save failed
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # Cancel close
        
        # Don't close the last tab
        if self.workflow_tabs.count() <= 1:
            QMessageBox.information(self, 'Cannot Close', 'Cannot close the last workflow tab.')
            return
        
        # Remove the tab and clean up metadata
        self.workflow_tabs.removeTab(index)
        if index in self.workflow_metadata:
            del self.workflow_metadata[index]
        
        # Renumber remaining tabs in metadata
        new_metadata = {}
        for i in range(self.workflow_tabs.count()):
            old_key = next((k for k in self.workflow_metadata.keys() if k > index), None)
            if old_key:
                new_metadata[i] = self.workflow_metadata[old_key]
            else:
                # Find the correct metadata by canvas widget
                for old_index, meta in self.workflow_metadata.items():
                    if old_index >= i:
                        new_metadata[i] = meta
                        break
        
        self.workflow_metadata = new_metadata
        print(f"✅ WORKFLOW: Closed workflow tab '{workflow_name}'")
    
    def on_workflow_tab_changed(self, index):
        """Handle switching between workflow tabs."""
        if index < 0:
            return
        
        current_canvas = self.get_current_canvas()
        if current_canvas:
            # Update property panel to show properties for current canvas
            if hasattr(self, 'property_panel'):
                self.property_panel.set_canvas_reference(current_canvas)
                # Property panel will be updated when user selects a node
            
            workflow_name = self.get_current_workflow_name()
            print(f"🔄 WORKFLOW: Switched to '{workflow_name}' (Tab {index + 1})")
    
    def save_workflow(self, tab_index=None):
        """Save the workflow in the specified tab."""
        if tab_index is None:
            tab_index = self.workflow_tabs.currentIndex()
        
        workflow_meta = self.workflow_metadata.get(tab_index, {})
        workflow_name = workflow_meta.get('name', f'Workflow {tab_index + 1}')
        
        try:
            # Get the canvas for this tab
            canvas_widget = self.workflow_tabs.widget(tab_index)
            if not isinstance(canvas_widget, FlowCanvas):
                QMessageBox.warning(self, 'Save Error', f'Invalid workflow canvas for "{workflow_name}"')
                return False
            
            # Use existing file path or prompt for new one
            file_path = workflow_meta.get('file_path')
            if not file_path:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    f'Save Workflow "{workflow_name}"',
                    f'{workflow_name.lower().replace(" ", "_")}.json',
                    'JSON Files (*.json)'
                )
                if not file_path:
                    return False
            
            # Save the workflow
            workflow_data = canvas_widget.serialize_flow()
            
            # Add summary information
            workflow_data['summary'] = {
                'node_count': len(canvas_widget.nodes),
                'connection_count': len(canvas_widget.connections),
                'node_types': [node.__class__.__name__ for node in canvas_widget.nodes],
                'custom_names': [getattr(node, 'custom_name', '') for node in canvas_widget.nodes if getattr(node, 'custom_name', '')]
            }
            
            # Save using project manager
            self.project_manager.save_flow(
                self.current_project_path,
                workflow_name,
                workflow_data
            )
            
            # Update metadata
            self.workflow_metadata[tab_index]['file_path'] = file_path
            self.workflow_metadata[tab_index]['modified'] = False
            
            # Update tab title to remove modified indicator
            tab_title = self.workflow_tabs.tabText(tab_index)
            if tab_title.endswith('*'):
                self.workflow_tabs.setTabText(tab_index, tab_title[:-1])
            
            QMessageBox.information(self, 'Save Successful', f'Workflow "{workflow_name}" saved successfully!')
            print(f"💾 WORKFLOW: Saved '{workflow_name}' to {file_path}")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, 'Save Error', f'Failed to save workflow "{workflow_name}":\n{str(e)}')
            print(f"❌ WORKFLOW: Save failed for '{workflow_name}': {e}")
            return False
    
    def mark_workflow_modified(self, tab_index):
        """Mark a workflow as modified."""
        if tab_index in self.workflow_metadata:
            self.workflow_metadata[tab_index]['modified'] = True
            
            # Add asterisk to tab title if not already present
            tab_title = self.workflow_tabs.tabText(tab_index)
            if not tab_title.endswith('*'):
                self.workflow_tabs.setTabText(tab_index, tab_title + '*')
    
    def create_new_workflow(self):
        """Create a new workflow tab."""
        from PyQt6.QtWidgets import QInputDialog
        
        # Prompt for workflow name
        workflow_name, ok = QInputDialog.getText(
            self,
            'New Workflow',
            'Enter name for the new workflow:\n(e.g., "AE Analysis", "Demographics", "Vital Signs")',
            text=f'Workflow {self.workflow_tabs.count() + 1}'
        )
        
        if ok and workflow_name.strip():
            workflow_name = workflow_name.strip()
            
            # Create new canvas
            new_canvas = FlowCanvas()
            
            # Add tab with appropriate icon
            domain_icons = {
                'AE': '⚡', 'ADVERSE': '⚡',
                'DM': '👤', 'DEMOGRAPHICS': '👤', 'DEMO': '👤',
                'VS': '💓', 'VITAL': '💓', 'VITALS': '💓',
                'LB': '🧪', 'LAB': '🧪', 'LABORATORY': '🧪',
                'CM': '💊', 'CONMED': '💊', 'MEDICATION': '💊',
                'MH': '📋', 'MEDICAL': '📋', 'HISTORY': '📋',
                'EX': '💉', 'EXPOSURE': '💉',
                'DS': '📊', 'DISPOSITION': '📊',
                'QS': '❓', 'QUESTIONNAIRE': '❓'
            }
            
            icon = '📊'  # Default icon
            for key, emoji in domain_icons.items():
                if key in workflow_name.upper():
                    icon = emoji
                    break
            
            tab_index = self.workflow_tabs.addTab(new_canvas, f"{icon} {workflow_name}")
            self.workflow_tabs.setTabToolTip(tab_index, f"Workflow: {workflow_name}")
            
            # Add custom close button to this tab
            self.add_custom_close_button(tab_index)
            
            # Store metadata
            self.workflow_metadata[tab_index] = {
                'name': workflow_name,
                'file_path': None,
                'modified': False,
                'domain': self.extract_domain_from_name(workflow_name)
            }
            
            # Initialize execution engine for new canvas
            self.initialize_execution_engine(new_canvas)
            
            # Connect signals for new canvas
            self.connect_canvas_signals(new_canvas)
            
            # Switch to the new tab
            self.workflow_tabs.setCurrentIndex(tab_index)
            
            print(f"✅ WORKFLOW: Created new workflow '{workflow_name}' (Tab {tab_index + 1})")
    
    def extract_domain_from_name(self, workflow_name):
        """Extract SDTM domain from workflow name."""
        name_upper = workflow_name.upper()
        domain_mappings = {
            'AE': 'AE', 'ADVERSE': 'AE',
            'DM': 'DM', 'DEMOGRAPHICS': 'DM', 'DEMO': 'DM',
            'VS': 'VS', 'VITAL': 'VS', 'VITALS': 'VS',
            'LB': 'LB', 'LAB': 'LB', 'LABORATORY': 'LB',
            'CM': 'CM', 'CONMED': 'CM', 'MEDICATION': 'CM',
            'MH': 'MH', 'MEDICAL': 'MH', 'HISTORY': 'MH',
            'EX': 'EX', 'EXPOSURE': 'EX',
            'DS': 'DS', 'DISPOSITION': 'DS',
            'QS': 'QS', 'QUESTIONNAIRE': 'QS'
        }
        
        for key, domain in domain_mappings.items():
            if key in name_upper:
                return domain
        return 'GENERAL'
    
    def duplicate_current_workflow(self):
        """Duplicate the current workflow with all its nodes and connections."""
        current_index = self.workflow_tabs.currentIndex()
        if current_index < 0:
            return
        
        current_canvas = self.get_current_canvas()
        current_meta = self.workflow_metadata.get(current_index, {})
        current_name = current_meta.get('name', f'Workflow {current_index + 1}')
        
        from PyQt6.QtWidgets import QInputDialog
        
        # Prompt for new workflow name
        new_name, ok = QInputDialog.getText(
            self,
            'Duplicate Workflow',
            f'Enter name for the duplicated workflow:\n(Original: "{current_name}")',
            text=f'{current_name} Copy'
        )
        
        if ok and new_name.strip():
            new_name = new_name.strip()
            
            # Create new canvas and copy flow
            new_canvas = FlowCanvas()
            
            # Copy the flow data
            try:
                # Save current flow to temporary data
                flow_data = current_canvas.get_flow_data()
                
                # Load the data into new canvas
                new_canvas.load_flow_data(flow_data)
                
                # Add tab
                icon = self.get_icon_for_domain(self.extract_domain_from_name(new_name))
                tab_index = self.workflow_tabs.addTab(new_canvas, f"{icon} {new_name}")
                self.workflow_tabs.setTabToolTip(tab_index, f"Workflow: {new_name} (Duplicated from {current_name})")
                
                # Add custom close button to duplicated workflow tab
                self.add_custom_close_button(tab_index)
                
                # Store metadata
                self.workflow_metadata[tab_index] = {
                    'name': new_name,
                    'file_path': None,
                    'modified': True,  # Mark as modified since it's a copy
                    'domain': self.extract_domain_from_name(new_name)
                }
                
                # Initialize execution engine
                self.initialize_execution_engine(new_canvas)
                
                # Connect signals for new canvas
                self.connect_canvas_signals(new_canvas)
                
                # Switch to new tab
                self.workflow_tabs.setCurrentIndex(tab_index)
                
                # Mark tab as modified
                self.workflow_tabs.setTabText(tab_index, f"{icon} {new_name}*")
                
                print(f"✅ WORKFLOW: Duplicated '{current_name}' as '{new_name}'")
                
            except Exception as e:
                QMessageBox.critical(self, 'Duplication Error', f'Failed to duplicate workflow:\n{str(e)}')
                print(f"❌ WORKFLOW: Duplication failed: {e}")
    
    def get_icon_for_domain(self, domain):
        """Get appropriate icon for domain."""
        icons = {
            'AE': '⚡', 'DM': '👤', 'VS': '💓', 'LB': '🧪', 
            'CM': '💊', 'MH': '📋', 'EX': '💉', 'DS': '📊', 'QS': '❓'
        }
        return icons.get(domain, '📊')
    
    def rename_current_workflow(self):
        """Rename the current workflow."""
        current_index = self.workflow_tabs.currentIndex()
        if current_index < 0:
            return
        
        current_meta = self.workflow_metadata.get(current_index, {})
        current_name = current_meta.get('name', f'Workflow {current_index + 1}')
        
        from PyQt6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self,
            'Rename Workflow',
            'Enter new name for the workflow:',
            text=current_name
        )
        
        if ok and new_name.strip() and new_name.strip() != current_name:
            new_name = new_name.strip()
            
            # Update metadata
            self.workflow_metadata[current_index]['name'] = new_name
            domain = self.extract_domain_from_name(new_name)
            self.workflow_metadata[current_index]['domain'] = domain
            
            # Update tab title
            icon = self.get_icon_for_domain(domain)
            modified_indicator = '*' if self.workflow_metadata[current_index].get('modified', False) else ''
            self.workflow_tabs.setTabText(current_index, f"{icon} {new_name}{modified_indicator}")
            self.workflow_tabs.setTabToolTip(current_index, f"Workflow: {new_name}")
            
            print(f"✅ WORKFLOW: Renamed '{current_name}' to '{new_name}'")
    
    def close_current_workflow(self):
        """Close the current workflow tab."""
        current_index = self.workflow_tabs.currentIndex()
        if current_index >= 0:
            self.close_workflow_tab(current_index)
    
    def save_all_workflows(self):
        """Save all workflow tabs."""
        saved_count = 0
        failed_count = 0
        
        for i in range(self.workflow_tabs.count()):
            if self.save_workflow(i):
                saved_count += 1
            else:
                failed_count += 1
        
        if failed_count == 0:
            QMessageBox.information(self, 'Save All Complete', f'Successfully saved all {saved_count} workflows!')
        else:
            QMessageBox.warning(self, 'Save All Partial', f'Saved {saved_count} workflows, {failed_count} failed to save.')
        
        print(f"💾 WORKFLOW: Save all completed - {saved_count} saved, {failed_count} failed")
    
    def mark_current_workflow_modified(self):
        """Mark the current workflow as modified."""
        current_index = self.workflow_tabs.currentIndex()
        if current_index >= 0 and current_index in self.workflow_metadata:
            if not self.workflow_metadata[current_index].get('modified', False):
                self.workflow_metadata[current_index]['modified'] = True
                
                # Add asterisk to tab title
                current_title = self.workflow_tabs.tabText(current_index)
                if not current_title.endswith('*'):
                    self.workflow_tabs.setTabText(current_index, current_title + '*')
                
                workflow_name = self.workflow_metadata[current_index].get('name', f'Workflow {current_index + 1}')
                print(f"📝 WORKFLOW: '{workflow_name}' marked as modified")

    def init_ui(self):
        """Initialize the main UI layout with fancy styling."""
        self.setWindowTitle("✨ SDTM Flow Builder - Advanced Data Processing Studio")
        self.setGeometry(100, 100, 1600, 1000)  # Larger default size
        
        # Apply modern dark theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-bottom: 2px solid #555555;
                padding: 4px;
                font-weight: 500;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenuBar::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a4a4a, stop:1 #2e2e2e);
                border: none;
                spacing: 2px;
                padding: 4px;
            }
            QToolBar::separator {
                background-color: #555555;
                width: 1px;
                margin: 4px 2px;
            }
            QDockWidget {
                background-color: #353535;
                color: #ffffff;
                titlebar-close-icon: url(none);
                titlebar-normal-icon: url(none);
                font-weight: 600;
            }
            QDockWidget::title {
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a9eff, stop:1 #357abd);
                color: #ffffff;
                padding: 8px;
                border-radius: 4px 4px 0px 0px;
                font-weight: bold;
                font-size: 11px;
            }
            QStatusBar {
                background-color: #2e2e2e;
                color: #cccccc;
                border-top: 1px solid #555555;
                font-size: 10px;
            }
        """)
        
        # Central widget - tabbed workflow interface
        self.workflow_tabs = QTabWidget()
        # Don't use setTabsClosable, we'll add custom close buttons
        self.workflow_tabs.setMovable(True)
        self.workflow_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #4a9eff;
                color: #ffffff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
        """)
        
        # Create initial workflow tab
        self.flow_canvas = FlowCanvas()
        initial_tab_index = self.workflow_tabs.addTab(self.flow_canvas, "📊 Workflow 1")
        self.workflow_tabs.setTabToolTip(initial_tab_index, "Main workflow - drag nodes here to build your data flow")
        
        # Add custom close button to initial tab
        self.add_custom_close_button(initial_tab_index)
        
        # Store workflow metadata
        self.workflow_metadata = {
            0: {
                'name': 'Workflow 1',
                'file_path': None,
                'modified': False,
                'domain': 'GENERAL'
            }
        }
        
        self.setCentralWidget(self.workflow_tabs)
        
        # Connect tab signals
        self.workflow_tabs.currentChanged.connect(self.on_workflow_tab_changed)
        
        # We'll add custom close buttons to each tab instead of using built-in ones
        
        # Initialize execution engine for the initial canvas
        self.initialize_execution_engine()
        
    def create_menus(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Workflow submenu
        workflow_menu = file_menu.addMenu("🔄 &Workflows")
        
        new_workflow_action = QAction("📊 &New Workflow", self)
        new_workflow_action.setShortcut("Ctrl+T")
        new_workflow_action.setToolTip("Create a new workflow tab (e.g., for AE, DM, VS domains)")
        new_workflow_action.triggered.connect(self.create_new_workflow)
        workflow_menu.addAction(new_workflow_action)
        
        duplicate_workflow_action = QAction("📋 &Duplicate Current Workflow", self)
        duplicate_workflow_action.setShortcut("Ctrl+Shift+D")
        duplicate_workflow_action.triggered.connect(self.duplicate_current_workflow)
        workflow_menu.addAction(duplicate_workflow_action)
        
        workflow_menu.addSeparator()
        
        rename_workflow_action = QAction("✏️ &Rename Current Workflow...", self)
        rename_workflow_action.triggered.connect(self.rename_current_workflow)
        workflow_menu.addAction(rename_workflow_action)
        
        close_workflow_action = QAction("❌ &Close Current Workflow", self)
        close_workflow_action.setShortcut("Ctrl+W")
        close_workflow_action.triggered.connect(self.close_current_workflow)
        workflow_menu.addAction(close_workflow_action)
        
        workflow_menu.addSeparator()
        
        save_all_workflows_action = QAction("💾 &Save All Workflows", self)
        save_all_workflows_action.setShortcut("Ctrl+Shift+A")
        save_all_workflows_action.triggered.connect(self.save_all_workflows)
        workflow_menu.addAction(save_all_workflows_action)
        
        file_menu.addSeparator()
        
        # Project submenu
        project_menu = file_menu.addMenu("📁 &Project")
        
        new_project_action = QAction("&New Project...", self)
        new_project_action.setShortcut("Ctrl+Shift+N")
        new_project_action.triggered.connect(self.new_project)
        project_menu.addAction(new_project_action)
        
        open_project_action = QAction("&Open Project...", self)
        open_project_action.setShortcut("Ctrl+Shift+O")
        open_project_action.triggered.connect(self.open_project)
        project_menu.addAction(open_project_action)
        
        project_menu.addSeparator()
        
        save_project_action = QAction("&Save Complete Workflow...", self)
        save_project_action.setShortcut("Ctrl+Shift+S")
        save_project_action.triggered.connect(self.save_current_flow)
        project_menu.addAction(save_project_action)
        
        project_menu.addSeparator()
        
        project_manager_action = QAction("📊 &Project Manager...", self)
        project_manager_action.triggered.connect(self.show_project_manager)
        project_menu.addAction(project_manager_action)
        
        view_flows_action = QAction("📋 &View Saved Workflows", self)
        view_flows_action.triggered.connect(self.view_current_project_flows)
        project_menu.addAction(view_flows_action)
        
        file_menu.addSeparator()
        
        open_action = QAction("&Load Data...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.smart_load_data)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Complete Workflow", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_flow)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_flow_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)
        
        # Data menu
        data_menu = menubar.addMenu("&Data")
        
        # Auto SDTM Processing toggle
        self.auto_sdtm_action = QAction("&Auto SDTM Processing", self)
        self.auto_sdtm_action.setCheckable(True)
        self.auto_sdtm_action.setChecked(False)  # Disabled by default to show raw data
        self.auto_sdtm_action.setToolTip("Automatically create USUBJID from X_USUBJID column and apply SDTM transformations")
        self.auto_sdtm_action.triggered.connect(self.toggle_auto_sdtm_processing)
        data_menu.addAction(self.auto_sdtm_action)
        
        data_menu.addSeparator()
        
        refresh_action = QAction("&Refresh Data", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        data_menu.addAction(refresh_action)
        
        # Flow menu
        flow_menu = menubar.addMenu("&Flow")
        
        execute_action = QAction("&Execute Flow", self)
        execute_action.setShortcut("Ctrl+F5")
        execute_action.triggered.connect(self.execute_flow)
        flow_menu.addAction(execute_action)
        
        validate_action = QAction("&Validate SDTM", self)
        validate_action.setShortcut("F6")
        validate_action.triggered.connect(self.validate_sdtm)
        flow_menu.addAction(validate_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Properties panel toggle
        props_action = QAction("&Properties Panel", self)
        props_action.setShortcut("F4")
        props_action.setCheckable(True)
        props_action.setChecked(True)  # Initially visible
        props_action.triggered.connect(self.toggle_properties_panel)
        view_menu.addAction(props_action)
        
        # Node palette toggle
        nodes_action = QAction("&Node Palette", self)
        nodes_action.setShortcut("F3")
        nodes_action.setCheckable(True)
        nodes_action.setChecked(True)  # Initially visible
        nodes_action.triggered.connect(self.toggle_node_palette)
        view_menu.addAction(nodes_action)
        
        view_menu.addSeparator()
        
        # Reset layout action
        reset_layout_action = QAction("&Reset Layout", self)
        reset_layout_action.setShortcut("Ctrl+Shift+R")
        reset_layout_action.triggered.connect(self.reset_dock_layout)
        view_menu.addAction(reset_layout_action)
        
    def create_toolbars(self):
        """Create enhanced application toolbars with modern styling."""
        # Main toolbar with fancy styling
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setIconSize(QSize(32, 32))  # Larger icons
        main_toolbar.setMovable(False)  # Fixed position
        
        # Enhanced button styling
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a9fd4, stop:1 #306998);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
                margin: 2px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6bb6ff, stop:1 #4a9eff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #306998, stop:1 #1e4a73);
                padding-top: 9px;
                padding-left: 17px;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """
        
        # File operations with enhanced styling
        self.load_data_btn = QPushButton("📁 Load Data")
        self.load_data_btn.setToolTip("Load SAS Dataset(s) - Right-click for options")
        self.load_data_btn.clicked.connect(self.smart_load_data)
        self.load_data_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.load_data_btn.customContextMenuRequested.connect(self.show_load_menu)
        self.load_data_btn.setStyleSheet(button_style)
        main_toolbar.addWidget(self.load_data_btn)
        
        # Separator
        main_toolbar.addSeparator()
        
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save Flow")
        save_btn.clicked.connect(self.save_flow)
        save_btn.setStyleSheet(button_style)
        main_toolbar.addWidget(save_btn)
        
        save_as_btn = QPushButton("� Save As")
        save_as_btn.setToolTip("Save Flow As...")
        save_as_btn.clicked.connect(self.save_flow_as)
        save_as_btn.setStyleSheet(button_style)
        main_toolbar.addWidget(save_as_btn)
        
        # Project management separator
        main_toolbar.addSeparator()
        
        # Project management buttons
        project_btn = QPushButton("� Projects")
        project_btn.setToolTip("Manage Projects & Load Workflows")
        project_btn.clicked.connect(self.open_project_dialog)
        project_btn.setStyleSheet(button_style.replace('#5a9fd4', '#ff6b35').replace('#306998', '#d84315'))
        main_toolbar.addWidget(project_btn)
        
        # Workflow management button
        new_workflow_btn = QPushButton("📊 New Workflow")
        new_workflow_btn.setToolTip("Create a new workflow tab (Ctrl+T)")
        new_workflow_btn.clicked.connect(self.create_new_workflow)
        new_workflow_btn.setStyleSheet(button_style.replace('#5a9fd4', '#00bcd4').replace('#306998', '#0097a7'))
        main_toolbar.addWidget(new_workflow_btn)
        
        # Execution separator
        main_toolbar.addSeparator()
        
        # Flow execution buttons
        execute_btn = QPushButton("▶️ Execute")
        execute_btn.setToolTip("Execute Flow")
        execute_btn.clicked.connect(self.execute_flow)
        execute_btn.setStyleSheet(button_style.replace('#5a9fd4', '#4caf50').replace('#306998', '#2e7d32'))
        main_toolbar.addWidget(execute_btn)
        
        validate_btn = QPushButton("✅ Validate")
        validate_btn.setToolTip("Validate SDTM")
        validate_btn.clicked.connect(self.validate_sdtm)
        validate_btn.setStyleSheet(button_style.replace('#5a9fd4', '#ff9800').replace('#306998', '#f57c00'))
        main_toolbar.addWidget(validate_btn)
        
        # SDTM Specifications button
        sdtm_specs_btn = QPushButton("📋 SDTM Specs")
        sdtm_specs_btn.setToolTip("Load SDTM Mapping Specifications for Auto-Population")
        sdtm_specs_btn.clicked.connect(self.load_sdtm_specifications)
        sdtm_specs_btn.setStyleSheet(button_style.replace('#5a9fd4', '#673ab7').replace('#306998', '#4527a0'))
        sdtm_specs_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        sdtm_specs_btn.customContextMenuRequested.connect(self.show_sdtm_specs_menu)
        main_toolbar.addWidget(sdtm_specs_btn)
        
        # View operations separator
        main_toolbar.addSeparator()
        
        # Auto-connect button for easier connections
        auto_connect_btn = QPushButton("🔗 Auto-Connect")
        auto_connect_btn.setToolTip("Automatically connect compatible nodes")
        auto_connect_btn.clicked.connect(self.auto_connect_nodes)
        auto_connect_btn.setStyleSheet(button_style.replace('#5a9fd4', '#9c27b0').replace('#306998', '#6a1b9a'))
        main_toolbar.addWidget(auto_connect_btn)
        
        # Properties panel toggle
        props_btn = QPushButton("🔧 Properties")
        props_btn.setToolTip("Toggle Properties Panel (F4)")
        props_btn.setCheckable(True)
        props_btn.setChecked(True)
        props_btn.clicked.connect(self.toggle_properties_panel)
        props_btn.setStyleSheet(button_style.replace('#5a9fd4', '#607d8b').replace('#306998', '#37474f'))
        main_toolbar.addWidget(props_btn)
        
        # Store reference for menu sync
        self.props_toolbar_btn = props_btn
        
        # Add delete connections button
        delete_connections_btn = QPushButton("🗑️ Clear Connections")
        delete_connections_btn.setToolTip("Delete all connections")
        delete_connections_btn.clicked.connect(self.delete_all_connections)
        main_toolbar.addWidget(delete_connections_btn)

        validate_btn = QPushButton("✅ Validate")
        validate_btn.setToolTip("Validate SDTM Compliance")
        validate_btn.clicked.connect(self.validate_sdtm)
        main_toolbar.addWidget(validate_btn)
        
        main_toolbar.addSeparator()
        
        # View operations
        zoom_in_btn = QPushButton("🔍➕ Zoom In")
        zoom_in_btn.clicked.connect(lambda: self.get_current_canvas().zoom_in() if self.get_current_canvas() else None)
        main_toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("🔍➖ Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self.get_current_canvas().zoom_out() if self.get_current_canvas() else None)
        main_toolbar.addWidget(zoom_out_btn)
        
        # Reset zoom button
        reset_zoom_btn = QPushButton("🎯 100%")
        reset_zoom_btn.setToolTip("Reset zoom to 100%")
        reset_zoom_btn.clicked.connect(lambda: self.get_current_canvas().reset_zoom() if self.get_current_canvas() else None)
        main_toolbar.addWidget(reset_zoom_btn)
        
        # Optimal zoom button
        optimal_zoom_btn = QPushButton("⚡ Optimal")
        optimal_zoom_btn.setToolTip("Set optimal zoom for current workflow")
        optimal_zoom_btn.clicked.connect(lambda: self.get_current_canvas().set_optimal_zoom() if self.get_current_canvas() else None)
        main_toolbar.addWidget(optimal_zoom_btn)
        
        fit_btn = QPushButton("📐 Fit to Window")
        fit_btn.setToolTip("Fit all nodes to window (may zoom out significantly)")
        fit_btn.clicked.connect(lambda: self.get_current_canvas().fit_to_window() if self.get_current_canvas() else None)
        main_toolbar.addWidget(fit_btn)
        
    def create_dock_widgets(self):
        """Create dockable panels."""
        # Transformation nodes palette
        self.create_nodes_palette()
        
        # Property panel
        self.create_property_panel()
        
        # Data viewer
        self.create_data_viewer()
        
        # Log panel
        self.create_log_panel()
        
    def create_nodes_palette(self):
        """Create the enhanced transformation nodes palette."""
        self.nodes_dock = QDockWidget("🧰 Transformation Nodes", self)
        self.nodes_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                       Qt.DockWidgetArea.RightDockWidgetArea)
        
        nodes_widget = QWidget()
        layout = QVBoxLayout(nodes_widget)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Create tree widget for categorized nodes with enhanced styling
        self.nodes_tree = DraggableTreeWidget()
        self.nodes_tree.setHeaderLabel("Available Nodes")
        self.nodes_tree.setDragEnabled(True)
        self.nodes_tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        self.nodes_tree.setDefaultDropAction(Qt.DropAction.CopyAction)
        
        # Enhanced tree widget styling
        self.nodes_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                selection-background-color: #4a9eff;
                selection-color: #ffffff;
                font-size: 11px;
                font-weight: 500;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #404040;
                min-height: 20px;
            }
            QTreeWidget::item:hover {
                background-color: #404040;
                border-radius: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #4a9eff;
                border-radius: 2px;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
            QTreeWidget::branch:has-children:closed {
                image: url(none);
                border-image: none;
            }
            QTreeWidget::branch:has-children:open {
                image: url(none);
                border-image: none;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Data Input/Output with enhanced icons
        io_item = QTreeWidgetItem(["📁 Data Input/Output"])
        io_item.setExpanded(True)
        load_item = QTreeWidgetItem(["📥 Load Dataset"])
        load_item.setData(0, Qt.ItemDataRole.UserRole, "Load Dataset")
        io_item.addChild(load_item)
        export_item = QTreeWidgetItem(["📤 Export Dataset"])
        export_item.setData(0, Qt.ItemDataRole.UserRole, "Export Dataset")
        io_item.addChild(export_item)
        self.nodes_tree.addTopLevelItem(io_item)
        
        # Data Transformation
        transform_item = QTreeWidgetItem(["Data Transformation"])
        
        rename_item = QTreeWidgetItem(["🏷️ Column Renamer"])
        rename_item.setData(0, Qt.ItemDataRole.UserRole, "Column Renamer")
        transform_item.addChild(rename_item)
        
        expr_item = QTreeWidgetItem(["📝 Expression Builder"])
        expr_item.setData(0, Qt.ItemDataRole.UserRole, "Expression Builder")
        transform_item.addChild(expr_item)
        
        constant_item = QTreeWidgetItem(["🔢 Constant Value Column"])
        constant_item.setData(0, Qt.ItemDataRole.UserRole, "Constant Value Column")
        transform_item.addChild(constant_item)
        
        merge_item = QTreeWidgetItem(["🔗 Merge/Join"])
        merge_item.setData(0, Qt.ItemDataRole.UserRole, "Merge/Join")
        transform_item.addChild(merge_item)
        
        set_item = QTreeWidgetItem(["📊 Set Operations"])
        set_item.setData(0, Qt.ItemDataRole.UserRole, "Set Operations")
        transform_item.addChild(set_item)
        
        transpose_item = QTreeWidgetItem(["🔄 Transpose"])
        transpose_item.setData(0, Qt.ItemDataRole.UserRole, "Transpose")
        transform_item.addChild(transpose_item)
        
        self.nodes_tree.addTopLevelItem(transform_item)
        
        # String & Number Operations
        string_item = QTreeWidgetItem(["String & Number Operations"])
        
        str_manip_item = QTreeWidgetItem(["✂️ String Manipulation"])
        str_manip_item.setData(0, Qt.ItemDataRole.UserRole, "String Manipulation")
        string_item.addChild(str_manip_item)
        
        num_str_item = QTreeWidgetItem(["🔢 Number to String"])
        num_str_item.setData(0, Qt.ItemDataRole.UserRole, "Number to String")
        string_item.addChild(num_str_item)
        
        str_num_item = QTreeWidgetItem(["📊 String to Number"])
        str_num_item.setData(0, Qt.ItemDataRole.UserRole, "String to Number")
        string_item.addChild(str_num_item)
        
        self.nodes_tree.addTopLevelItem(string_item)
        
        # Logic & Rules
        logic_item = QTreeWidgetItem(["Logic & Rules"])
        
        rule_item = QTreeWidgetItem(["⚙️ Rule Engine"])
        rule_item.setData(0, Qt.ItemDataRole.UserRole, "Rule Engine")
        logic_item.addChild(rule_item)
        
        if_item = QTreeWidgetItem(["🔀 If-Then-Else"])
        if_item.setData(0, Qt.ItemDataRole.UserRole, "If-Then-Else")
        logic_item.addChild(if_item)
        
        conditional_mapping_item = QTreeWidgetItem(["🗂️ Conditional Mapping"])
        conditional_mapping_item.setData(0, Qt.ItemDataRole.UserRole, "Conditional Mapping")
        logic_item.addChild(conditional_mapping_item)
        
        self.nodes_tree.addTopLevelItem(logic_item)
        
        # Data Management
        mgmt_item = QTreeWidgetItem(["Data Management"])
        
        filter_item = QTreeWidgetItem(["🔍 Row Filter"])
        filter_item.setData(0, Qt.ItemDataRole.UserRole, "Row Filter")
        mgmt_item.addChild(filter_item)
        
        keep_drop_item = QTreeWidgetItem(["📋 Column Keep/Drop"])
        keep_drop_item.setData(0, Qt.ItemDataRole.UserRole, "Column Keep/Drop")
        mgmt_item.addChild(keep_drop_item)
        
        join_item = QTreeWidgetItem(["🔗 Join"])
        join_item.setData(0, Qt.ItemDataRole.UserRole, "Join")
        mgmt_item.addChild(join_item)
        
        group_item = QTreeWidgetItem(["📈 GroupBy"])
        group_item.setData(0, Qt.ItemDataRole.UserRole, "GroupBy")
        mgmt_item.addChild(group_item)
        
        sort_item = QTreeWidgetItem(["🔤 Sorter"])
        sort_item.setData(0, Qt.ItemDataRole.UserRole, "Sorter")
        mgmt_item.addChild(sort_item)
        
        domain_item = QTreeWidgetItem(["🏷️ Domain"])
        domain_item.setData(0, Qt.ItemDataRole.UserRole, "Domain")
        mgmt_item.addChild(domain_item)
        
        self.nodes_tree.addTopLevelItem(mgmt_item)
        
        # Expand all categories
        self.nodes_tree.expandAll()
        
        # Connect double-click to add node
        self.nodes_tree.itemDoubleClicked.connect(self.on_node_double_clicked)
        
        layout.addWidget(self.nodes_tree)
        self.nodes_dock.setWidget(nodes_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.nodes_dock)
        
    def create_property_panel(self):
        """Create the enhanced property configuration panel."""
        self.props_dock = QDockWidget("⚙️ Properties", self)
        self.props_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                       Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Enhanced property panel styling
        self.props_dock.setStyleSheet("""
            QDockWidget::title {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b35, stop:1 #d84315);
                color: #ffffff;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        self.property_panel = PropertyPanel()
        self.property_panel.set_main_window_reference(self)  # Pass reference for SDTM suggestions
        # Set wider minimum width for better button and control display, especially for Column Keep/Drop
        self.props_dock.setMinimumWidth(520)  # Increased from 420 for dual-pane Column Keep/Drop
        self.props_dock.setWidget(self.property_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.props_dock)
        
    def create_data_viewer(self):
        """Create the enhanced data preview panel with optimal height."""
        self.data_dock = QDockWidget("📊 Data Viewer", self)
        self.data_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | 
                                  Qt.DockWidgetArea.TopDockWidgetArea)
        
        # Enhanced dock widget styling
        self.data_dock.setStyleSheet("""
            QDockWidget::title {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a9eff, stop:1 #357abd);
                color: #ffffff;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        self.data_viewer = DataPreviewTab()
        
        # Increased height to accommodate larger control widgets (28px controls + 24px header)
        # Plus space for 5-6 data rows = ~260px total
        self.data_viewer.setMinimumHeight(220)  # Increased from 180
        self.data_viewer.setMaximumHeight(280)  # Increased from 220
        
        self.data_dock.setWidget(self.data_viewer)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.data_dock)
        
        # Set initial size hint for better layout with larger controls
        self.data_dock.setMinimumHeight(240)  # Increased from 200
        self.data_dock.setMaximumHeight(300)  # Increased from 240
        
    def create_log_panel(self):
        """Create the enhanced execution log panel."""
        log_dock = QDockWidget("📋 Execution Log", self)
        log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | 
                                 Qt.DockWidgetArea.TopDockWidgetArea)
        
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumHeight(180)  # Slightly taller for better readability
        
        # Enhanced log panel styling
        self.log_panel.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10px;
                padding: 4px;
                line-height: 1.2;
            }
        """)
        
        log_dock.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, log_dock)
        
        # Tabify log with data viewer
        self.tabifyDockWidget(self.data_dock, log_dock)
        
        # Make data viewer the active tab initially
        self.data_dock.raise_()
        
        # Configure dock widget sizes for better property panel display
        # Give properties panel more space and reduce nodes palette - especially for Column Keep/Drop dual panes
        self.resizeDocks([self.nodes_dock, self.props_dock], [250, 520], Qt.Orientation.Horizontal)
        
    def on_node_double_clicked(self, item, column):
        """Handle double-click on tree item to add node."""
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if node_type:
            current_canvas = self.get_current_canvas()
            if current_canvas:
                # Add node to center of current canvas
                center_pos = current_canvas.mapToScene(
                    current_canvas.viewport().rect().center()
                )
                current_canvas.add_transformation_node(node_type, center_pos)
        
    def setup_status_bar(self):
        """Setup the enhanced status bar with performance monitoring."""
        self.status_bar = self.statusBar()
        
        # Memory usage label
        self.memory_label = QLabel(self.memory_monitor.get_memory_info_text())
        self.memory_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                padding: 2px 6px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #2e2e2e;
            }
        """)
        self.status_bar.addPermanentWidget(self.memory_label)
        
        # Progress bar for long operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                font-size: 10px;
                color: #ffffff;
                background-color: #2e2e2e;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 2px;
            }
        """)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Update memory usage every 5 seconds
        from PyQt6.QtCore import QTimer
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_display)
        self.memory_timer.start(5000)  # Update every 5 seconds
        
    def smart_load_data(self):
        """Smart data loader that automatically detects what user wants to load."""
        # Check if raw folder exists and has SAS files
        raw_folder = os.path.abspath("../raw")
        has_raw_folder = os.path.exists(raw_folder)
        
        if has_raw_folder:
            sas_files = list(Path(raw_folder).glob("*.sas7bdat"))
            if len(sas_files) > 1:
                # Multiple files in raw folder - offer to load all
                reply = QMessageBox.question(
                    self,
                    "Load Data",
                    f"Found {len(sas_files)} SAS files in raw/ folder:\n" + 
                    "\n".join([f.name for f in sas_files[:5]]) +
                    ("\n..." if len(sas_files) > 5 else "") +
                    "\n\nWhat would you like to do?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )
                reply.setButtonText(QMessageBox.StandardButton.Yes, "Load All Files")
                reply.setButtonText(QMessageBox.StandardButton.No, "Choose Specific Files")
                reply.setButtonText(QMessageBox.StandardButton.Cancel, "Cancel")
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Load all files from raw folder
                    for file_path in sas_files:
                        self.load_dataset(str(file_path))
                    return
                elif reply == QMessageBox.StandardButton.No:
                    # Let user choose specific files
                    self.open_multiple_datasets(raw_folder)
                    return
                else:
                    return
            elif len(sas_files) == 1:
                # Single file in raw folder - load it
                self.load_dataset(str(sas_files[0]))
                return
        
        # No raw folder or no files - show file picker
        self.show_load_menu_dialog()
        
    def show_load_menu(self, position):
        """Show context menu for load options."""
        menu = QMenu(self)
        
        single_action = menu.addAction("📄 Load Single File")
        single_action.triggered.connect(self.open_dataset)
        
        multiple_action = menu.addAction("📄📄 Load Multiple Files")
        multiple_action.triggered.connect(lambda: self.open_multiple_datasets())
        
        folder_action = menu.addAction("📂 Load Folder")
        folder_action.triggered.connect(self.open_folder)
        
        menu.exec(self.load_data_btn.mapToGlobal(position))
        
    def show_load_menu_dialog(self):
        """Show dialog for choosing load method."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Load Data")
        msg.setText("How would you like to load your SAS data?")
        
        single_btn = msg.addButton("📄 Single File", QMessageBox.ButtonRole.ActionRole)
        multiple_btn = msg.addButton("📄📄 Multiple Files", QMessageBox.ButtonRole.ActionRole)
        folder_btn = msg.addButton("📂 Entire Folder", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == single_btn:
            self.open_dataset()
        elif msg.clickedButton() == multiple_btn:
            self.open_multiple_datasets()
        elif msg.clickedButton() == folder_btn:
            self.open_folder()
            
    def open_dataset(self):
        """Open a single SAS dataset file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SAS Dataset",
            "../raw",
            "SAS Files (*.sas7bdat);;All Files (*)"
        )
        
        if file_path:
            self.load_dataset(file_path)
            
    def open_multiple_datasets(self, start_dir="../raw"):
        """Open multiple SAS dataset files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Multiple SAS Datasets",
            start_dir,
            "SAS Files (*.sas7bdat);;All Files (*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                self.load_dataset(file_path)
                
    def open_folder(self):
        """Open all SAS files in a folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing SAS Datasets",
            "../raw"
        )
        
        if folder_path:
            # Find all .sas7bdat files in the folder
            sas_files = []
            for file_path in Path(folder_path).glob("*.sas7bdat"):
                sas_files.append(str(file_path))
                
            if sas_files:
                for file_path in sas_files:
                    self.load_dataset(file_path)
                self.log_message(f"Loaded {len(sas_files)} datasets from folder: {folder_path}")
            else:
                QMessageBox.information(
                    self, 
                    "No SAS Files", 
                    f"No .sas7bdat files found in folder:\n{folder_path}"
                )
                
    def load_dataset(self, file_path):
        """Load a single dataset file."""
        try:
            self.status_label.setText(f"Loading {os.path.basename(file_path)}...")
            self.progress_bar.setVisible(True)
            QApplication.processEvents()  # Update UI
            
            # Load data using data manager
            df = self.data_manager.load_sas_dataset(file_path)
            filename = os.path.basename(file_path)
            
            # Pass both filename and full path
            self.data_loaded.emit(filename, df, file_path)
            self.log_message(f"Successfully loaded {filename} ({len(df)} rows, {len(df.columns)} columns)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load dataset {os.path.basename(file_path)}:\n{str(e)}")
            self.log_message(f"Error loading {os.path.basename(file_path)}: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.status_label.setText("Ready")
    
    def load_sdtm_specifications(self):
        """Load SDTM mapping specifications for auto-population of controlled terminology."""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self,
                "Load SDTM Mapping Specifications",
                "",
                "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Create progress dialog
            from PyQt6.QtWidgets import QProgressDialog
            from PyQt6.QtCore import Qt
            
            progress = QProgressDialog("Loading SDTM specifications...", "Cancel", 0, 100, self)
            progress.setWindowTitle("SDTM Specifications Loader")
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            self.status_label.setText("Loading SDTM specifications...")
            self.progress_bar.setVisible(True)
            QApplication.processEvents()
            
            # Load the specifications file
            if file_path.lower().endswith(('.xlsx', '.xls')):
                progress.setLabelText("Reading Excel file...")
                progress.setValue(10)
                QApplication.processEvents()
                
                # Load Excel file - try to find controlled terminology sheets
                xl_file = pd.ExcelFile(file_path)
                sheet_names = xl_file.sheet_names
                
                progress.setLabelText("Loading all Excel sheets...")
                progress.setValue(20)
                QApplication.processEvents()
                
                # Load ALL sheets for comprehensive access
                all_sheets = sheet_names
                
                # Initialize storage for raw data (preserve original structure)
                if not hasattr(self, 'sdtm_raw_data'):
                    self.sdtm_raw_data = {}
                
                loaded_sheets = 0
                
                total_sheets = len(all_sheets)
                for i, sheet_name in enumerate(all_sheets):
                    progress.setLabelText(f"Loading sheet: {sheet_name}")
                    progress.setValue(20 + int(60 * i / total_sheets))
                    QApplication.processEvents()
                    
                    if progress.wasCanceled():
                        progress.close()
                        return
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        
                        # Store the raw DataFrame AS-IS with all columns and rows
                        self.sdtm_raw_data[sheet_name] = df
                        loaded_sheets += 1
                        
                        self.log_message(f"📊 Loaded sheet '{sheet_name}': {len(df)} rows × {len(df.columns)} columns")
                        
                    except Exception as e:
                        print(f"⚠️ Could not process sheet '{sheet_name}': {e}")
                        continue
                
            else:  # CSV file
                progress.setLabelText("Reading CSV file...")
                progress.setValue(40)
                QApplication.processEvents()
                
                df = pd.read_csv(file_path)
                
                # Store the raw DataFrame AS-IS with all columns and rows
                filename = os.path.basename(file_path)
                if not hasattr(self, 'sdtm_raw_data'):
                    self.sdtm_raw_data = {}
                self.sdtm_raw_data[filename] = df
                
                progress.setLabelText("CSV file loaded successfully...")
                progress.setValue(80)
                QApplication.processEvents()
                
                self.log_message(f"📊 Loaded CSV '{filename}': {len(df)} rows × {len(df.columns)} columns")
                loaded_sheets = 1
            
            # Finalize loading
            progress.setLabelText("Finalizing specifications...")
            progress.setValue(90)
            QApplication.processEvents()
            
            if self.sdtm_raw_data:
                msg = "✅ SDTM Specifications Successfully Loaded!\n\n"
                msg += "� How to View Your Specifications:\n\n"
                # Removed old msg lines with undefined total_rows variable
                # Old msg construction removed
                
                # Removed problematic lines that referenced undefined total_rows
                # Removed all old msg references
                
                progress.setValue(100)
                progress.close()
                
                # Use the correct final message without total_rows reference
                msg_final = "✅ SDTM Specifications Successfully Loaded!\n\n"
                msg_final += "📋 How to View Your Specifications:\n\n"
                msg_final += "🎯 Option 1: Quick Summary\n"
                msg_final += "   • Go to: SDTM Specifications → View Loaded Specs\n"
                msg_final += "   • Shows: Overview with row/column counts\n\n"
                msg_final += "🎯 Option 2: Full Data Viewer (Recommended)\n" 
                msg_final += "   • Go to: SDTM Specifications → Open Specifications UI\n"
                msg_final += "   • Shows: Complete data in AG-Grid with auto-sizing columns\n"
                msg_final += "   • Features: Sorting, filtering, column expansion\n\n"
                msg_final += "💡 Tip: Use the Full Data Viewer to explore all your SDTM\n"
                msg_final += "specifications with enhanced viewing capabilities!"
                
                QMessageBox.information(self, "SDTM Specifications Loaded", msg_final)
                self.log_message(f"Loaded SDTM specifications: {len(self.sdtm_raw_data)} sheets with original structure preserved")
                
                # Refresh all CT selection dropdowns after loading specifications
                if hasattr(self, 'property_panel') and self.property_panel:
                    self.property_panel.refresh_all_ct_selections()
                    self.log_message("🔄 Refreshed all CT selection dropdowns with new specifications")
            else:
                progress.close()
                QMessageBox.warning(
                    self, 
                    "No Data Found", 
                    "Could not load any data from the specifications file.\n\n"
                    "Please check if the file contains valid data."
                )
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(self, "Error", f"Failed to load SDTM specifications:\n{str(e)}")
            self.log_message(f"Error loading SDTM specifications: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.status_label.setText("Ready")
    
    def identify_mapping_columns(self, df):
        """Identify potential source/target mapping columns in a dataframe."""
        columns = df.columns.tolist()
        mapping_pairs = []
        
        # Common mapping column patterns
        source_patterns = ['source', 'original', 'value', 'raw', 'crf', 'input', 'from']
        target_patterns = ['target', 'sdtm', 'standard', 'code', 'mapped', 'output', 'to']
        
        # Try to find explicit pairs
        for i, col1 in enumerate(columns):
            col1_lower = col1.lower()
            for j, col2 in enumerate(columns):
                if i >= j:  # Avoid duplicates and self-pairing
                    continue
                    
                col2_lower = col2.lower()
                
                # Check if one looks like source and other like target
                col1_is_source = any(pattern in col1_lower for pattern in source_patterns)
                col1_is_target = any(pattern in col1_lower for pattern in target_patterns)
                col2_is_source = any(pattern in col2_lower for pattern in source_patterns)
                col2_is_target = any(pattern in col2_lower for pattern in target_patterns)
                
                if col1_is_source and col2_is_target:
                    mapping_pairs.append((col1, col2))
                elif col1_is_target and col2_is_source:
                    mapping_pairs.append((col2, col1))
        
        # If no explicit patterns found, try first two columns
        if not mapping_pairs and len(columns) >= 2:
            mapping_pairs.append((columns[0], columns[1]))
        
        return mapping_pairs
    
    def get_sdtm_suggestions(self, source_values):
        """Get SDTM mapping suggestions for a list of source values by searching raw data."""
        suggestions = {}
        
        if not hasattr(self, 'sdtm_raw_data') or not self.sdtm_raw_data:
            return suggestions
        
        for value in source_values:
            value_str = str(value).strip()
            if not value_str or value_str.lower() == 'nan':
                continue
                
            # Search across all loaded data sheets/files
            for sheet_name, df in self.sdtm_raw_data.items():
                
                # Look for potential mapping columns
                # Check if this looks like a codelist structure
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
                
                # If we have codelist structure, search for matches
                if decode_col and value_col:
                    for _, row in df.iterrows():
                        decode_val = str(row[decode_col]).strip()
                        code_val = str(row[value_col]).strip()
                        
                        # Check for exact or partial matches
                        if (decode_val.lower() == value_str.lower() or 
                            value_str.lower() in decode_val.lower() or
                            decode_val.lower() in value_str.lower()):
                            
                            if code_val and code_val.lower() != 'nan':
                                suggestions[value] = code_val
                                break
                
                # If we found a suggestion, don't search other sheets
                if value in suggestions:
                    break
        
        return suggestions
    
    def show_sdtm_specs_menu(self, position):
        """Show context menu for SDTM specifications button."""
        menu = QMenu()
        
        load_action = menu.addAction("📁 Load SDTM Specifications")
        load_action.triggered.connect(self.load_sdtm_specifications)
        
        # Load sample CSV action
        load_sample_action = menu.addAction("📂 Load Sample CSV (Fix SDTMCT issue)")
        load_sample_action.triggered.connect(self.load_sample_csv_specs)
        
        create_sample_action = menu.addAction("📝 Create Sample Specifications")
        create_sample_action.triggered.connect(self.create_sample_sdtm_specs)
        
        menu.addSeparator()
        
        # Always show view options, even when no specs are loaded
        if self.sdtm_specifications:
            view_action = menu.addAction(f"�️ View Loaded Specs ({len(self.sdtm_specifications)} sheets)")
            specs_ui_action = menu.addAction("🖥️ Open Specifications UI")
            
            # Clear specs action (only when specs exist)
            clear_action = menu.addAction("�️ Clear All Specifications")
            clear_action.triggered.connect(self.clear_sdtm_specifications)
        else:
            view_action = menu.addAction("👁️ View Loaded Specs (None loaded)")
            specs_ui_action = menu.addAction("🖥️ Open Specifications UI (None loaded)")
        
        view_action.triggered.connect(self.view_sdtm_specifications)
        specs_ui_action.triggered.connect(self.open_sdtm_specs_ui)
        
        # Get the button that triggered the menu
        button = self.sender()
        menu.exec(button.mapToGlobal(position))
    
    def load_sample_csv_specs(self):
        """Load the sample CSV specifications to fix SDTMCT-20240329 issue."""
        try:
            sample_file = "sample_sdtm_codelists.csv"
            if not os.path.exists(sample_file):
                QMessageBox.warning(self, "Sample File Missing", 
                    f"Sample file '{sample_file}' not found.\nPlease create it first using 'Create Sample Specifications'.")
                return
                
            # Clear existing specifications first
            self.clear_sdtm_specifications()
            
            # Load the sample CSV
            self.load_specific_sdtm_file([sample_file])
            
            QMessageBox.information(self, "Sample Loaded", 
                f"✅ Sample CSV loaded successfully!\n\nNow your mappings will show:\n• Yes → Y\n• No → N\n• Unknown → U\n\nInstead of SDTMCT-20240329 values.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample CSV:\n{str(e)}")
    
    def clear_sdtm_specifications(self):
        """Clear all loaded SDTM specifications."""
        self.sdtm_specifications.clear()
        if hasattr(self, 'sdtm_raw_data'):
            self.sdtm_raw_data.clear()
        
        self.log_message("🗑️ Cleared all SDTM specifications")
    
    def load_specific_sdtm_file(self, file_paths):
        """Load specific SDTM specification files."""
        try:
            for file_path in file_paths:
                if file_path.lower().endswith('.csv'):
                    # Load CSV file
                    df = pd.read_csv(file_path)
                    
                    # Use enhanced column detection for CODELIST structure
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
                    
                    # Use codelist structure if available
                    if codelist_col and decode_col and value_col:
                        csv_mappings = {}
                        for _, row in df.iterrows():
                            decode_val = str(row[decode_col]).strip()
                            code_val = str(row[value_col]).strip()
                            
                            if decode_val and code_val and decode_val != 'nan' and code_val != 'nan':
                                csv_mappings[decode_val.lower()] = code_val
                        
                        if csv_mappings:
                            filename = os.path.basename(file_path)
                            self.sdtm_specifications[filename] = csv_mappings
                            self.log_message(f"✅ Loaded {len(csv_mappings)} mappings from {filename}")
                    
        except Exception as e:
            self.log_message(f"❌ Error loading specific SDTM file: {str(e)}")
            raise
    
    def create_sample_sdtm_specs(self):
        """Create a sample SDTM specifications file for testing."""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self,
                "Save Sample SDTM Specifications",
                "sample_sdtm_specifications.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # Create sample controlled terminology data
            sample_data = {
                'Yes_No_Mappings': pd.DataFrame({
                    'Source_Value': ['Yes', 'Y', 'YES', 'No', 'N', 'NO', 'Unknown', 'UNK', 'Missing', ''],
                    'SDTM_Value': ['Y', 'Y', 'Y', 'N', 'N', 'N', 'U', 'U', 'U', 'U']
                }),
                'Severity_Mappings': pd.DataFrame({
                    'Original_Term': ['Mild', 'MILD', 'Minor', 'Moderate', 'MODERATE', 'Severe', 'SEVERE', 'Life-threatening'],
                    'Standard_Code': ['MILD', 'MILD', 'MILD', 'MODERATE', 'MODERATE', 'SEVERE', 'SEVERE', 'LIFE THREATENING']
                }),
                'Action_Taken_Mappings': pd.DataFrame({
                    'Raw_Value': ['No action taken', 'NONE', 'Drug withdrawn', 'WITHDRAWN', 'Dose reduced', 'REDUCED', 'Dose increased'],
                    'SDTM_Term': ['NONE', 'NONE', 'DRUG WITHDRAWN', 'DRUG WITHDRAWN', 'DOSE REDUCED', 'DOSE REDUCED', 'DOSE INCREASED']
                })
            }
            
            # Write to Excel file
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in sample_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            msg = f"✅ Sample SDTM Specifications Created!\n\n"
            msg += f"📁 File: {file_path}\n\n"
            msg += f"📋 Contains {len(sample_data)} sheets with common SDTM mappings:\n"
            for sheet_name, df in sample_data.items():
                msg += f"• {sheet_name}: {len(df)} mappings\n"
            msg += "\n🎯 You can now load this file to test auto-population!"
            
            QMessageBox.information(self, "Sample File Created", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create sample specifications:\n{str(e)}")
    
    def view_sdtm_specifications(self):
        """View currently loaded SDTM specifications."""
        if not self.sdtm_specifications:
            QMessageBox.information(self, "No Specifications", "No SDTM specifications are currently loaded.")
            return
        
        msg = "📋 Loaded SDTM Specifications:\n\n"
        total_mappings = 0
        
        for sheet_name, mappings in self.sdtm_specifications.items():
            msg += f"🗂️ {sheet_name} ({len(mappings)} mappings):\n"
            # Show first few mappings as examples
            count = 0
            for source, target in mappings.items():
                if count < 3:  # Show first 3 mappings
                    msg += f"   • {source} → {target}\n"
                    count += 1
                else:
                    remaining = len(mappings) - 3
                    if remaining > 0:
                        msg += f"   ... and {remaining} more\n"
                    break
            msg += "\n"
            total_mappings += len(mappings)
        
    def view_sdtm_specifications(self):
        """Display the loaded SDTM specifications in AG-Grid format."""
        if not self.sdtm_specifications:
            # Show helpful message when no specs are loaded
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("No Specifications Loaded")
            msg.setText("No SDTM specifications are currently loaded.")
            msg.setInformativeText("Would you like to load some specifications first?")
            
            load_btn = msg.addButton("📁 Load Specifications", QMessageBox.ButtonRole.AcceptRole)
            sample_btn = msg.addButton("📝 Create Sample", QMessageBox.ButtonRole.ActionRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg.exec()
            
            if msg.clickedButton() == load_btn:
                self.load_sdtm_specifications()
            elif msg.clickedButton() == sample_btn:
                self.create_sample_sdtm_specs()
            return
        
    def view_sdtm_specifications(self):
        """Display the loaded SDTM specifications summary."""
        if not hasattr(self, 'sdtm_raw_data') or not self.sdtm_raw_data:
            # Show helpful message when no specs are loaded
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("No Specifications Loaded")
            msg.setText("No SDTM specifications are currently loaded.")
            msg.setInformativeText("Would you like to load some specifications first?")
            
            load_btn = msg.addButton("📁 Load Specifications", QMessageBox.ButtonRole.AcceptRole)
            sample_btn = msg.addButton("� Create Sample", QMessageBox.ButtonRole.ActionRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg.exec()
            
            if msg.clickedButton() == load_btn:
                self.load_sdtm_specifications()
            elif msg.clickedButton() == sample_btn:
                self.create_sample_sdtm_specs()
            return
        
        # Show summary of all loaded data with original structure
        msg = "📋 Loaded SDTM Specifications:\n\n"
        total_rows = 0
        total_columns = 0
        
        for sheet_name, df in self.sdtm_raw_data.items():
            msg += f"🗂️ {sheet_name}:\n"
            msg += f"   📊 {len(df)} rows × {len(df.columns)} columns\n"
            msg += f"   📝 Columns: {', '.join(df.columns[:5])}"
            if len(df.columns) > 5:
                msg += f"... (+{len(df.columns) - 5} more)"
            msg += "\n\n"
            
            total_rows += len(df)
            total_columns += len(df.columns)
        
        msg += f"📊 Total: {total_rows} rows across {len(self.sdtm_raw_data)} sheets\n"
        msg += f"📋 All data preserved with original structure!\n\n"
        msg += "💡 For detailed view, use 'Open Specifications UI' option."
        
        # Show the summary dialog
        QMessageBox.information(self, "SDTM Specifications Summary", msg)
    
    def open_sdtm_specs_ui(self):
        """Open the SDTM specifications viewer UI."""
        try:
            # Check if specs are actually loaded with data
            if not hasattr(self, 'sdtm_raw_data') or not self.sdtm_raw_data or len(self.sdtm_raw_data) == 0:
                # Show helpful message when no specs are loaded
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("No Specifications Loaded")
                msg.setText("No SDTM specifications are currently loaded.")
                msg.setInformativeText("Would you like to load some specifications first?")
                
                load_btn = msg.addButton("📁 Load Specifications", QMessageBox.ButtonRole.AcceptRole)
                sample_btn = msg.addButton("📝 Create Sample", QMessageBox.ButtonRole.ActionRole)
                cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg.exec()
                
                if msg.clickedButton() == load_btn:
                    self.load_sdtm_specifications()
                    return
                elif msg.clickedButton() == sample_btn:
                    self.create_sample_sdtm_specs()
                    return
                else:
                    return
            
            from .sdtm_specs_viewer import SDTMSpecsViewer
            
            # Reuse existing viewer if it exists and is visible, otherwise create new one
            if hasattr(self, 'specs_viewer') and self.specs_viewer is not None:
                try:
                    # Check if the viewer is still valid
                    if self.specs_viewer.isVisible():
                        # Just bring it to front and refresh data
                        self.specs_viewer.raise_()
                        self.specs_viewer.activateWindow()
                        self.specs_viewer.refresh_data(self.sdtm_raw_data)
                        return
                    else:
                        # Viewer exists but is closed, refresh it with new data
                        self.specs_viewer.refresh_data(self.sdtm_raw_data)
                        self.specs_viewer.show()
                        return
                except:
                    # Viewer is invalid, create new one
                    pass
            
            # Create new viewer
            self.specs_viewer = SDTMSpecsViewer(self.sdtm_raw_data, self)
            self.specs_viewer.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open specifications UI:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def clear_sdtm_specifications(self):
        """Clear all loaded SDTM specifications."""
        self.sdtm_specifications = {}
        QMessageBox.information(self, "Specifications Cleared", "All SDTM specifications have been cleared.")
        self.log_message("SDTM specifications cleared")
                
    def on_data_loaded(self, filename, dataframe, file_path):
        """Handle data loaded event."""
        # Update data viewer
        self.data_viewer.set_dataframe(dataframe, filename, "Data Load", [])
        
        # Add to current active canvas as input node with file path
        current_canvas = self.get_current_canvas()
        if current_canvas:
            current_canvas.add_input_node(filename, dataframe, file_path)
        
    def on_flow_changed(self):
        """Handle flow structure changes (connections, etc.)."""
        print(f"🔄 FLOW CHANGED: Signal received")
        
        # Mark current workflow as modified
        self.mark_current_workflow_modified()
        
        # Mark workflow as modified
        if self.current_workflow_name:
            if not self.workflow_modified:
                self.workflow_modified = True
                self.update_window_title()
                print(f"📝 Workflow '{self.current_workflow_name}' marked as modified")
        
        # Refresh property panel for the currently selected node
        if hasattr(self.property_panel, 'current_node') and self.property_panel.current_node:
            print(f"🔄 Flow changed - refreshing properties for {self.property_panel.current_node.title}")
            print(f"📊 Canvas has {len(self.flow_canvas.connections)} connections")
            
            # Refresh the property panel
            self.property_panel.set_node(self.property_panel.current_node)
        else:
            print(f"🔄 Flow changed but no current node selected in property panel")
        
    def on_node_selected_for_data_view(self, node):
        """Handle node selection for data viewer updates - AUTOMATIC REFRESH AFTER EXECUTE."""
        try:
            print(f"🔄 AUTO REFRESH: Updating data viewer for {node.title}")
            
            # Get current workflow canvas
            current_canvas = self.workflow_tabs.currentWidget()
            if not current_canvas:
                print("⚠️ No current workflow canvas available")
                return
            
            # Get execution engine if available
            execution_engine = getattr(current_canvas, 'execution_engine', None)
            print(f"🔄 AUTO REFRESH: Execution engine available: {execution_engine is not None}")
            
            # CRITICAL FIX: Check for execution errors FIRST before showing any data
            if execution_engine:
                last_error = execution_engine.get_last_error()
                if last_error:
                    print(f"🔄 AUTO REFRESH: Execution error detected: {last_error}")
                    # Show error message in data viewer
                    error_df = pd.DataFrame({
                        'ERROR': [f"❌ Execution Failed"],
                        'NODE': [node.title],
                        'MESSAGE': [last_error],
                        'SOLUTION': ['Fix upstream node errors and re-execute the flow']
                    })
                    source_info = f"❌ Execution Error in {node.title}"
                    self.data_viewer.set_dataframe(error_df, node.title, source_info, ['ERROR'])
                    self.log_message(f"🔄 AUTO REFRESH: Displaying error for {node.title}")
                    return
                
                # Check if this node has valid connections and dependencies
                has_valid_inputs = True
                if hasattr(node, 'node_type') and node.node_type not in ['input', 'constant']:
                    # Non-input nodes need upstream connections
                    input_connections = [
                        conn for conn in self.flow_canvas.connections 
                        if conn.end_port.parent_node == node
                    ]
                    
                    if not input_connections:
                        print(f"🔄 AUTO REFRESH: Node {node.title} has no input connections")
                        has_valid_inputs = False
                    else:
                        # Check if upstream nodes have valid data
                        for conn in input_connections:
                            upstream_node = conn.start_port.parent_node
                            upstream_data = execution_engine.get_node_output_data(upstream_node)
                            if upstream_data is None:
                                print(f"🔄 AUTO REFRESH: Upstream node {upstream_node.title} has no data")
                                has_valid_inputs = False
                                break
                
                if not has_valid_inputs:
                    error_df = pd.DataFrame({
                        'STATUS': [f"⚠️ Invalid Pipeline"],
                        'NODE': [node.title],
                        'REASON': ['Missing or invalid upstream connections/data'],
                        'SOLUTION': ['Check connections and re-execute the flow']
                    })
                    source_info = f"⚠️ Invalid Pipeline for {node.title}"
                    self.data_viewer.set_dataframe(error_df, node.title, source_info, ['STATUS'])
                    self.log_message(f"🔄 AUTO REFRESH: Invalid pipeline for {node.title}")
                    return
                
                # Try to get executed data
                executed_data = execution_engine.get_node_output_data(node)
                print(f"🔄 AUTO REFRESH: Executed data available: {executed_data is not None}")
                
                if executed_data is not None:
                    print(f"🔄 AUTO REFRESH: Data shape: {executed_data.shape}")
                else:
                    # Debug cache information
                    print(f"🔄 AUTO REFRESH: Getting cache info for debugging...")
                    cache_info = execution_engine.get_cache_info()
                    print(f"🔄 AUTO REFRESH: Node object id: {id(node)}")
                    print(f"🔄 AUTO REFRESH: Node title: '{node.title}'")
                    print(f"🔄 AUTO REFRESH: Node type: {type(node)}")
                    
                    # Check if title exists in cache with different formatting
                    for cache_key in execution_engine.node_outputs.keys():
                        if str(cache_key) == str(node.title):
                            print(f"🔄 AUTO REFRESH: Found matching title key: '{cache_key}' (type: {type(cache_key)})")
                            cached_data = execution_engine.node_outputs[cache_key]
                            if hasattr(cached_data, 'shape'):
                                print(f"🔄 AUTO REFRESH: Found data with shape: {cached_data.shape}")
                                executed_data = cached_data
                                break
                
                # Check if this node has no cached data (might be due to upstream failure)
                if executed_data is None:
                    print(f"🔄 AUTO REFRESH: No cached data for {node.title} - checking if upstream failed")
                    error_df = pd.DataFrame({
                        'STATUS': [f"⚠️ No Data Available"],
                        'NODE': [node.title],
                        'REASON': ['No cached data - upstream nodes may have failed'],
                        'SOLUTION': ['Check upstream nodes and re-execute the flow']
                    })
                    source_info = f"⚠️ No Data for {node.title}"
                    self.data_viewer.set_dataframe(error_df, node.title, source_info, ['STATUS'])
                    self.log_message(f"🔄 AUTO REFRESH: No data available for {node.title}")
                    return
                
                if executed_data is not None:
                    print(f"🔄 AUTO REFRESH: Displaying executed data ({len(executed_data)} rows, {len(executed_data.columns)} cols)")
                    print(f"🔄 AUTO REFRESH: Data columns preview: {list(executed_data.columns)[:5]}...")
                    
                    # Determine changed columns based on node type
                    changed_columns = []
                    if hasattr(node, 'rename_mappings') and node.rename_mappings:
                        # For rename nodes, highlight the new column names (values in the mapping)
                        changed_columns = list(node.rename_mappings.values())
                        print(f"🔄 CHANGED COLUMNS: Rename node changed columns: {changed_columns}")
                    elif hasattr(node, 'transformed_columns') and node.transformed_columns:
                        # For transformation nodes that set transformed_columns (ConditionalMapping, etc.)
                        changed_columns = list(node.transformed_columns)
                        print(f"🔄 CHANGED COLUMNS: Transformation node changed columns: {changed_columns}")
                    elif hasattr(node, 'columns') and node.columns:
                        # For multiple constant value columns, highlight all new columns
                        changed_columns = [col.get('column_name', '').strip() 
                                        for col in node.columns 
                                        if col.get('column_name', '').strip()]
                        print(f"🔄 CHANGED COLUMNS: Multiple constant value columns added: {changed_columns}")
                    elif hasattr(node, 'column_name') and hasattr(node, 'constant_value') and node.column_name.strip():
                        # For backward compatibility - single constant value column
                        changed_columns = [node.column_name.strip()]
                        print(f"🔄 CHANGED COLUMNS: Single constant value node added column: {changed_columns}")
                    elif hasattr(node, 'new_column_name') and node.new_column_name.strip():
                        # For expression builder nodes, highlight the new expression column
                        changed_columns = [node.new_column_name.strip()]
                        print(f"🔄 CHANGED COLUMNS: Expression node added column: {changed_columns}")
                    elif hasattr(node, 'filter_conditions') and node.filter_conditions:
                        # For filter nodes, no columns are changed, just filtered
                        changed_columns = []
                        print(f"🔄 CHANGED COLUMNS: Filter node - no columns changed")
                    else:
                        # For unknown transformation nodes, try to detect new columns by comparison
                        changed_columns = []
                        try:
                            # Get input data to compare
                            if execution_engine:
                                input_data = execution_engine.get_node_input_data(node)
                                if input_data is not None and executed_data is not None:
                                    input_columns = set(input_data.columns)
                                    output_columns = set(executed_data.columns)
                                    new_columns = output_columns - input_columns
                                    if new_columns:
                                        changed_columns = list(new_columns)
                                        print(f"🔄 CHANGED COLUMNS: Auto-detected new columns: {changed_columns}")
                                    else:
                                        print(f"🔄 CHANGED COLUMNS: No new columns detected")
                                else:
                                    print(f"🔄 CHANGED COLUMNS: Cannot compare - missing input or output data")
                            else:
                                print(f"🔄 CHANGED COLUMNS: Cannot compare - no execution engine")
                        except Exception as e:
                            print(f"🔄 CHANGED COLUMNS: Error in auto-detection: {e}")
                            changed_columns = []
                    
                    # Show executed data with changed columns highlighting
                    source_info = f"✅ Executed Output from {node.title} (AUTO REFRESHED)"
                    print(f"🔄 AUTO REFRESH: About to call set_dataframe with {len(executed_data)} rows")
                    self.data_viewer.set_dataframe(executed_data, node.title, source_info, changed_columns)
                    print(f"🔄 AUTO REFRESH: set_dataframe call completed")
                    self.log_message(f"🔄 AUTO REFRESH: Displaying executed data from {node.title} ({len(executed_data)} rows)")
                    
                    # Force multiple update attempts to ensure visibility
                    if hasattr(self.data_viewer, 'update'):
                        self.data_viewer.update()
                    if hasattr(self.data_viewer, 'refresh'):
                        self.data_viewer.refresh()
                    if hasattr(self.data_viewer, 'repaint'):
                        self.data_viewer.repaint()
                    
                    # Force the application to process events
                    from PyQt6.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    print("🔄 AUTO REFRESH: Forced data viewer refresh complete")
                    return
            
            # Fallback to original data for input nodes (no changed columns)
            if hasattr(node, 'dataframe') and node.dataframe is not None:
                source_info = f"Original Data from {node.title}"
                self.data_viewer.set_dataframe(node.dataframe, node.title, source_info, [])
                self.log_message(f"Displaying original data from {node.title} ({len(node.dataframe)} rows)")
                return
            
            # No data available
            self.data_viewer.set_dataframe(None, "", "No Data Available", [])
            self.log_message(f"No data available for {node.title} - execute flow to see results")
            
        except Exception as e:
            self.log_message(f"Error displaying data for {node.title}: {str(e)}")
            self.data_viewer.set_dataframe(None, "", "Error Loading Data", [])
        
    def save_flow(self):
        """Save the current flow configuration - smart save to existing file or new if first save."""
        return self.save_workflow()  # Use the new workflow-aware save method

    def save_flow_original(self):
        """Original save flow method for backwards compatibility."""
        try:
            # If we already have a workflow file, save to it directly
            if self.current_workflow_name and self.current_workflow_file:
                print(f"💾 SMART SAVE: Saving to existing workflow '{self.current_workflow_name}'")
                
                # Serialize the complete current workflow
                current_canvas = self.get_current_canvas()
                if current_canvas:
                    workflow_data = current_canvas.serialize_flow()
                    
                    # Add summary information
                    workflow_data['summary'] = {
                        'node_count': len(current_canvas.nodes),
                        'connection_count': len(current_canvas.connections),
                        'node_types': [node.__class__.__name__ for node in current_canvas.nodes],
                        'custom_names': [getattr(node, 'custom_name', '') for node in current_canvas.nodes if getattr(node, 'custom_name', '')]
                    }
                    
                    # Save to existing file
                    workflow_file = self.project_manager.save_flow(
                        self.current_project_path, 
                        self.current_workflow_name,
                        workflow_data
                    )
                    
                    self.workflow_modified = False
                    self.status_label.setText(f"✅ Saved: {self.current_workflow_name}")
                    self.log_message(f"💾 Workflow '{self.current_workflow_name}' saved successfully")
                    
                    # Update window title to remove modified indicator
                    self.update_window_title()
                
            else:
                # First save or no current workflow - use save as
                print("💾 SMART SAVE: First save - asking for workflow name")
                self.save_current_flow()
                
        except Exception as e:
            self.log_message(f"❌ Error saving workflow: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Failed to save workflow:\n{str(e)}")
    
    def save_flow_original(self):
        """Save the current flow configuration - redirect to project system."""
        # Redirect to the project-based save system
        self.save_current_flow()
        
    def save_flow_as(self):
        """Save As - always ask for new workflow name regardless of current state."""
        try:
            if not self.current_project_path:
                QMessageBox.warning(self, "No Project", 
                                   "Please create or open a project first.")
                return
            
            # Get current workflow canvas
            current_canvas = self.workflow_tabs.currentWidget()
            if not current_canvas or not current_canvas.nodes:
                QMessageBox.information(self, "Empty Flow", 
                                       "No nodes to save. Create some nodes first.")
                return
            
            # Always ask for new name in Save As
            from PyQt6.QtWidgets import QInputDialog
            
            # Default to current name with "_copy" suffix if exists
            current_workflow_name = self.get_current_workflow_name()
            if current_workflow_name and current_workflow_name != "Unknown Workflow":
                default_name = f"{current_workflow_name}_copy"
            else:
                node_count = len(current_canvas.nodes)
                connection_count = len(current_canvas.connections)
                default_name = f"Workflow_{node_count}nodes_{connection_count}connections"
            
            name, ok = QInputDialog.getText(
                self, 
                'Save Workflow As', 
                'Enter new workflow name:',
                text=default_name
            )
            
            if ok and name.strip():
                name = name.strip()
                
                # Serialize the complete current workflow
                workflow_data = current_canvas.serialize_flow()
                
                # Add summary information
                workflow_data['summary'] = {
                    'node_count': len(current_canvas.nodes),
                    'connection_count': len(current_canvas.connections),
                    'node_types': [node.__class__.__name__ for node in current_canvas.nodes],
                    'custom_names': [getattr(node, 'custom_name', '') for node in current_canvas.nodes if getattr(node, 'custom_name', '')]
                }
                
                # Save the workflow and get the file path
                workflow_file = self.project_manager.save_flow(
                    self.current_project_path, 
                    name, 
                    workflow_data
                )
                
                # Update tracking variables to the new workflow
                self.current_workflow_name = name
                self.current_workflow_file = workflow_file
                self.workflow_modified = False
                
                # Update UI
                self.status_label.setText(f"✅ Saved As: {name}")
                self.log_message(f"💾 Workflow saved as '{name}' to: {workflow_file}")
                self.update_workflow_list()
                self.update_window_title()
                
                QMessageBox.information(
                    self, "✅ Workflow Saved As", 
                    f"Workflow saved as '{name}'!\n\n"
                    f"📁 Location: {workflow_file}\n\n"
                    f"💡 Future saves (Ctrl+S) will save to this new workflow."
                )
                
        except Exception as e:
            self.log_message(f"❌ Error saving workflow as: {str(e)}")
            QMessageBox.critical(self, "Save As Error", f"Failed to save workflow as:\n{str(e)}")
        
    def load_flow(self):
        """Load a flow configuration - redirect to project system."""
        # Redirect to the project dialog for loading flows
        self.open_project_dialog()
                
    def execute_flow(self):
        """Execute the current data flow for the active workflow tab."""
        try:
            # Get the currently active workflow canvas
            current_canvas = self.workflow_tabs.currentWidget()
            if not current_canvas:
                QMessageBox.warning(self, "No Workflow", "No workflow is currently active.")
                return
            
            # Get workflow name for logging
            current_index = self.workflow_tabs.currentIndex()
            workflow_name = self.get_current_workflow_name()
            
            self.status_label.setText(f"Executing workflow: {workflow_name}...")
            self.progress_bar.setVisible(True)
            self.log_message(f"🚀 Flow execution started for workflow: {workflow_name}")
            
            # Import and use the execution engine
            from data.execution_engine import FlowExecutionEngine
            
            # CRITICAL FIX: Reuse existing execution engine if available to preserve cache
            existing_engine = getattr(current_canvas, 'execution_engine', None)
            if existing_engine:
                print(f"🔄 REUSING existing execution engine with {len(existing_engine.node_outputs)} cached outputs")
                engine = existing_engine
            else:
                print(f"🔄 CREATING new execution engine for workflow: {workflow_name}")
                # Create and run execution engine for current canvas
                engine = FlowExecutionEngine(current_canvas)
            
            # Set up logging callback to display messages in execution log
            engine.set_log_callback(self.log_message)
            success = engine.execute_flow()
            
            if success:
                self.log_message(f"✅ Flow execution completed successfully for workflow: {workflow_name}!")
                QMessageBox.information(self, "🎉 Execution Complete", 
                                      f"Workflow '{workflow_name}' executed successfully!\n\n"
                                      f"📊 Processed {len(current_canvas.nodes)} nodes\n"
                                      f"🔗 Through {len(current_canvas.connections)} connections\n\n"
                                      f"💡 Click on nodes to view their output data!")
                
                # Store engine reference for data viewing
                current_canvas.execution_engine = engine
                
                # Mark workflow as modified after execution
                self.mark_workflow_modified(current_index)
                
            else:
                self.log_message(f"❌ Flow execution failed for workflow: {workflow_name}!")
                QMessageBox.warning(self, "⚠️ Execution Failed", 
                                  f"Workflow '{workflow_name}' execution encountered errors.\n\n"
                                  "Please check:\n"
                                  "• All nodes are properly connected\n"
                                  "• Data sources are loaded\n"
                                  "• Node configurations are valid\n\n"
                                  "Check the log panel for details.")
                
                # Store engine reference even for failed execution (to access successful nodes)
                current_canvas.execution_engine = engine
            
        except Exception as e:
            self.log_message(f"❌ Flow execution error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to execute flow:\n{str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.status_label.setText("Ready")
            
    def auto_connect_nodes(self):
        """Automatically connect compatible nodes."""
        try:
            self.status_label.setText("Auto-connecting nodes...")
            
            # Find data input nodes and transformation nodes
            data_nodes = []
            transform_nodes = []
            
            for node in self.flow_canvas.nodes:
                if hasattr(node, 'filename'):  # Data input node
                    data_nodes.append(node)
                elif hasattr(node, 'rename_mappings') or hasattr(node, 'expression'):  # Transformation node
                    transform_nodes.append(node)
            
            connections_made = 0
            
            # Connect data nodes to transformation nodes
            for data_node in data_nodes:
                for transform_node in transform_nodes:
                    # Check if already connected
                    already_connected = any(
                        conn.start_port.parent_node == data_node and 
                        conn.end_port.parent_node == transform_node
                        for conn in self.flow_canvas.connections
                    )
                    
                    if not already_connected and len(data_node.output_ports) > 0 and len(transform_node.input_ports) > 0:
                        # Create connection
                        from ui.flow_canvas import NodeConnection
                        output_port = data_node.output_ports[0]
                        input_port = transform_node.input_ports[0]
                        
                        connection = NodeConnection(output_port, input_port)
                        connection.set_canvas(self.flow_canvas)  # Set canvas reference for deletion
                        self.flow_canvas.scene.addItem(connection)
                        self.flow_canvas.connections.append(connection)
                        connections_made += 1
                        
                        self.log_message(f"Connected {data_node.title} → {transform_node.title}")
            
            if connections_made > 0:
                QMessageBox.information(self, "✅ Auto-Connect Success", 
                                      f"🔗 Created {connections_made} connection(s)!\n\n"
                                      f"Now you can:\n"
                                      f"1. Click nodes to configure properties\n"
                                      f"2. Add column mappings\n"
                                      f"3. Execute the flow")
                self.log_message(f"Auto-connected {connections_made} node pairs")
            else:
                QMessageBox.information(self, "ℹ️ Auto-Connect", 
                                      "No compatible nodes found to connect.\n\n"
                                      "Make sure you have:\n"
                                      "• Data input nodes (from loaded files)\n" 
                                      "• Transformation nodes (Column Renamer, etc.)")
                                      
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto-connect failed:\n{str(e)}")
            self.log_message(f"Auto-connect error: {str(e)}")
        finally:
            self.status_label.setText("Ready")
            
    def delete_all_connections(self):
        """Delete all connections in the flow canvas."""
        try:
            self.status_label.setText("Deleting connections...")
            self.flow_canvas.delete_all_connections()
            self.log_message("All connections deleted")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete connections:\n{str(e)}")
            self.log_message(f"Connection deletion error: {str(e)}")
        finally:
            self.status_label.setText("Ready")
    
    def toggle_auto_sdtm_processing(self, enabled):
        """Toggle automatic SDTM processing."""
        self.data_manager.set_auto_sdtm_processing(enabled)
        
        msg = QMessageBox()
        msg.setWindowTitle("SDTM Processing Setting")
        
        if enabled:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("✅ Auto SDTM Processing Enabled")
            msg.setInformativeText("New datasets will automatically get:\n"
                                 "• USUBJID columns created from X_USUBJID (or SUBJID as fallback)\n"
                                 "• Date columns standardized\n"
                                 "• SDTM domain-specific transformations")
        else:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("🔧 Auto SDTM Processing Disabled")
            msg.setInformativeText("New datasets will show raw data:\n"
                                 "• No automatic USUBJID creation\n"
                                 "• Original column names preserved\n"
                                 "• No automatic transformations")
        
        msg.setDetailedText("Note: This affects newly loaded datasets. "
                          "Already loaded datasets are not changed. "
                          "Use 'Data > Refresh Data' to reload with new settings.")
        msg.exec()
    
    def refresh_data(self):
        """Refresh all loaded datasets with current settings."""
        try:
            self.status_label.setText("Refreshing datasets...")
            
            if not self.data_manager.datasets:
                QMessageBox.information(self, "No Data", "No datasets are currently loaded.")
                return
            
            # Get list of current datasets
            dataset_files = {}
            for name, (df, metadata) in self.data_manager.datasets.items():
                if 'file_path' in metadata:
                    dataset_files[name] = metadata['file_path']
            
            # Clear current flow canvas nodes
            self.flow_canvas.scene.clear()
            self.flow_canvas.nodes.clear()
            self.flow_canvas.connections.clear()
            
            # Clear and reload datasets
            self.data_manager.datasets.clear()
            
            reloaded_count = 0
            for name, file_path in dataset_files.items():
                try:
                    df = self.data_manager.load_sas_dataset(file_path)
                    filename = os.path.basename(file_path)
                    self.add_data_input_node(filename, df)
                    reloaded_count += 1
                except Exception as e:
                    print(f"❌ Failed to reload {name}: {e}")
            
            QMessageBox.information(self, "Refresh Complete", 
                                  f"Refreshed {reloaded_count} datasets with current SDTM settings.")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh datasets:\n{str(e)}")
        finally:
            self.status_label.setText("Ready")
            
    def validate_sdtm(self):
        """Validate SDTM compliance."""
        try:
            self.status_label.setText("Validating SDTM compliance...")
            
            # TODO: Implement SDTM validation
            self.log_message("SDTM validation started...")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to validate SDTM:\n{str(e)}")
        finally:
            self.status_label.setText("Ready")
            
    def log_message(self, message):
        """Add a message to the execution log."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_panel.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        """Handle application close event."""
        reply = QMessageBox.question(
            self, 
            "Confirm Exit",
            "Are you sure you want to exit?\nUnsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
    
    def toggle_properties_panel(self, checked):
        """Toggle the properties panel visibility."""
        if hasattr(self, 'props_dock'):
            self.props_dock.setVisible(checked)
            if checked:
                print("🔧 Properties panel opened")
            else:
                print("🔧 Properties panel closed")
    
    def toggle_node_palette(self, checked):
        """Toggle the node palette visibility."""
        if hasattr(self, 'nodes_dock'):
            self.nodes_dock.setVisible(checked)
            if checked:
                print("🎨 Node palette opened")
            else:
                print("🎨 Node palette closed")
    
    def reset_dock_layout(self):
        """Reset dock widgets to default layout."""
        try:
            # Show all dock widgets
            if hasattr(self, 'props_dock'):
                self.props_dock.setVisible(True)
            if hasattr(self, 'nodes_dock'):
                self.nodes_dock.setVisible(True)
            
            # Reset to default positions
            if hasattr(self, 'nodes_dock'):
                self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.nodes_dock)
            if hasattr(self, 'props_dock'):
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.props_dock)
            
            print("🔄 Dock layout reset to default")
            
        except Exception as e:
            print(f"❌ Error resetting layout: {e}")
    
    # === PROJECT MANAGEMENT METHODS ===
    
    def new_project(self):
        """Create a new project."""
        try:
            from PyQt6.QtWidgets import QInputDialog
            
            # Get project name
            name, ok = QInputDialog.getText(
                self, "New Project", "Project name:"
            )
            
            if ok and name.strip():
                # Get description
                description, ok = QInputDialog.getMultiLineText(
                    self, "New Project", "Project description (optional):"
                )
                
                if ok:
                    # Create project
                    project_path = self.project_manager.create_project(name.strip(), description.strip())
                    self.current_project_path = project_path
                    
                    # Clear current flow
                    self.flow_canvas.clear_flow()
                    
                    self.status_label.setText(f"Created project: {name}")
                    QMessageBox.information(self, "Success", f"Project '{name}' created successfully!")
                    self.update_window_title()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project:\n{str(e)}")
    
    def open_project(self):
        """Open the project manager to select a project."""
        try:
            dialog = ProjectDialog(self, self.current_project_path)
            dialog.project_selected.connect(self.load_project)
            dialog.flow_selected.connect(self.load_project_flow)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project manager:\n{str(e)}")
    
    def show_project_manager(self):
        """Show the full project manager dialog."""
        self.open_project()
    
    def open_project_dialog(self):
        """Alias for open_project - used by toolbar button."""
        self.open_project()
    
    def view_current_project_flows(self):
        """Show complete workflows in the current project."""
        if not self.current_project_path:
            QMessageBox.information(
                self, "No Project", 
                "No project is currently loaded.\n\n"
                "Create a new project with:\nFile → Project → New Project"
            )
            return
            
        try:
            # Get project info
            project_name = os.path.basename(self.current_project_path)
            flows = self.project_manager.list_flows(self.current_project_path)
            
            if not flows:
                QMessageBox.information(
                    self, "No Workflows", 
                    f"Project '{project_name}' has no saved workflows.\n\n"
                    f"Save your current workflow with:\nFile → Project → Save Complete Workflow"
                )
                return
            
            # Create workflow list display with more details
            flow_list = []
            for i, flow in enumerate(flows, 1):
                modified = flow.get('modified', 'Unknown')
                if modified != 'Unknown':
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                        modified = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                flow_list.append(f"{i}. {flow['name']} (Modified: {modified})")
            
            flows_text = "\n".join(flow_list)
            flows_folder = os.path.join(self.current_project_path, 'flows')
            
            QMessageBox.information(
                self, f"📋 Complete Workflows in '{project_name}'", 
                f"Found {len(flows)} saved workflow(s):\n\n"
                f"{flows_text}\n\n"
                f"📂 Location: {flows_folder}\n\n"
                f"💡 Each workflow contains:\n"
                f"   • All nodes and connections\n"
                f"   • Node settings and transformations\n"
                f"   • Custom names and descriptions\n\n"
                f"To load a workflow:\nFile → Project → Project Manager"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to view flows:\n{str(e)}")
    
    def load_project(self, project_path):
        """Load a project (clears current flow)."""
        try:
            self.current_project_path = project_path
            
            # Clear current flow
            self.flow_canvas.clear_flow()
            
            project_name = os.path.basename(project_path)
            self.status_label.setText(f"Loaded project: {project_name}")
            self.update_window_title()
            
            # Show available flows in project
            flows = self.project_manager.list_flows(project_path)
            if flows:
                flow_names = [f['name'] for f in flows]
                QMessageBox.information(
                    self, "Project Loaded", 
                    f"Project '{project_name}' loaded.\n\n"
                    f"Available flows:\n" + "\n".join(f"• {name}" for name in flow_names) +
                    "\n\nUse File → Project → Project Manager to load a specific flow."
                )
            else:
                QMessageBox.information(
                    self, "Project Loaded", 
                    f"Project '{project_name}' loaded.\n\nNo flows found in this project."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{str(e)}")
    
    def load_project_flow(self, project_path, flow_name):
        """Load a specific flow from a project into a new tab."""
        try:
            flow_data = self.project_manager.load_flow(project_path, flow_name)
            
            if flow_data:
                self.current_project_path = project_path
                
                # Create a new workflow tab for the loaded flow
                new_canvas = FlowCanvas()
                
                # Load the flow into the new canvas
                success = new_canvas.load_flow(flow_data)
                
                if success:
                    # Add the new tab with the flow name
                    domain = self.extract_domain_from_name(flow_name)
                    icon = self.get_icon_for_domain(domain)
                    tab_index = self.workflow_tabs.addTab(new_canvas, f"{icon} {flow_name}")
                    self.workflow_tabs.setTabToolTip(tab_index, f"Workflow: {flow_name} (Loaded from project)")
                    
                    # Add custom close button to loaded workflow tab
                    self.add_custom_close_button(tab_index)
                    
                    # Store metadata for the new tab
                    self.workflow_metadata[tab_index] = {
                        'name': flow_name,
                        'file_path': os.path.join(project_path, 'flows', f'{flow_name}.json'),
                        'modified': False,  # Just loaded, so not modified yet
                        'domain': domain
                    }
                    
                    # Initialize execution engine for new canvas
                    self.initialize_execution_engine(new_canvas)
                    
                    # Connect signals for new canvas
                    self.connect_canvas_signals(new_canvas)
                    
                    # Switch to the new tab
                    self.workflow_tabs.setCurrentIndex(tab_index)
                    
                    project_name = os.path.basename(project_path)
                    self.status_label.setText(f"Loaded flow: {flow_name} from {project_name}")
                    
                    print(f"📂 Loaded workflow '{flow_name}' in new tab {tab_index + 1}")
                    
                    QMessageBox.information(
                        self, "Flow Loaded", 
                        f"Flow '{flow_name}' loaded successfully in a new tab!"
                    )
                else:
                    QMessageBox.warning(self, "Error", f"Failed to load flow '{flow_name}' - invalid flow data")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load flow '{flow_name}' - flow not found")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load flow:\n{str(e)}")
            print(f"❌ Exception loading flow: {e}")
            import traceback
            traceback.print_exc()
    
    def save_current_flow(self):
        """Save the complete current workflow as one file."""
        try:
            if not self.current_project_path:
                # No project selected, ask user to create one or select one
                reply = QMessageBox.question(
                    self, "No Project", 
                    "No project is currently loaded. Would you like to create a new project?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.new_project()
                    if not self.current_project_path:
                        return  # User cancelled project creation
                else:
                    return
            
            # Get current workflow canvas
            current_canvas = self.workflow_tabs.currentWidget()
            if not current_canvas:
                QMessageBox.warning(self, "No Workflow", "No workflow is currently active.")
                return
            
            # Check if there are any nodes to save
            if not current_canvas.nodes:
                QMessageBox.warning(
                    self, "No Workflow", 
                    "There are no nodes in the current workflow to save.\n\n"
                    "Please add some nodes first."
                )
                return
            
            # Get workflow name
            from PyQt6.QtWidgets import QInputDialog
            
            # Use current workflow name if exists, otherwise default name
            current_workflow_name = self.get_current_workflow_name()
            if current_workflow_name and current_workflow_name != "Unknown Workflow":
                default_name = current_workflow_name
            else:
                node_count = len(current_canvas.nodes)
                connection_count = len(current_canvas.connections)
                default_name = f"Workflow_{node_count}nodes_{connection_count}connections"
            
            workflow_name, ok = QInputDialog.getText(
                self, "Save Complete Workflow", 
                f"Save entire workflow ({len(current_canvas.nodes)} nodes, {len(current_canvas.connections)} connections):\n\nWorkflow name:",
                text=default_name
            )
            
            if ok and workflow_name.strip():
                # Serialize the complete current workflow
                workflow_data = current_canvas.serialize_flow()
                
                # Add summary information to the workflow
                workflow_data['summary'] = {
                    'node_count': len(current_canvas.nodes),
                    'connection_count': len(current_canvas.connections),
                    'node_types': [node.__class__.__name__ for node in current_canvas.nodes],
                    'custom_names': [getattr(node, 'custom_name', '') for node in current_canvas.nodes if getattr(node, 'custom_name', '')]
                }
                
                # Save the complete workflow to project
                workflow_file = self.project_manager.save_flow(
                    self.current_project_path, 
                    workflow_name.strip(), 
                    workflow_data
                )
                
                # Update tracking variables for smart save
                self.current_workflow_name = workflow_name.strip()
                self.current_workflow_file = workflow_file
                self.workflow_modified = False
                
                # Get project info for display
                project_name = os.path.basename(self.current_project_path)
                flows_folder = os.path.join(self.current_project_path, 'flows')
                
                self.status_label.setText(f"Saved complete workflow: {workflow_name}")
                self.log_message(f"✅ Complete workflow '{workflow_name}' saved to project '{project_name}'")
                self.log_message(f"📁 Location: {workflow_file}")
                self.log_message(f"📊 Saved: {len(self.flow_canvas.nodes)} nodes, {len(self.flow_canvas.connections)} connections")
                
                # Update UI
                self.update_workflow_list()
                self.update_window_title()
                
                # Show detailed success message
                QMessageBox.information(
                    self, "✅ Complete Workflow Saved", 
                    f"Complete workflow '{workflow_name}' has been saved!\n\n"
                    f"📊 Contents:\n"
                    f"   • {len(self.flow_canvas.nodes)} nodes\n"
                    f"   • {len(self.flow_canvas.connections)} connections\n"
                    f"   • All transformations and settings\n\n"
                    f"📁 Project: {project_name}\n"
                    f"📂 Location: {flows_folder}\n\n"
                    f"💡 To reload this complete workflow:\n"
                    f"File → Project → Project Manager → Load Flow"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save flow:\n{str(e)}")
    
    def update_window_title(self):
        """Update window title with current project info."""
        base_title = "SDTM Flow Builder"
        
        if self.current_project_path:
            project_name = os.path.basename(self.current_project_path)
            
            # Add workflow name if available
            if self.current_workflow_name:
                # Add modified indicator if workflow has been modified
                modified_indicator = " *" if self.workflow_modified else ""
                title = f"{base_title} - {project_name} - {self.current_workflow_name}{modified_indicator}"
            else:
                title = f"{base_title} - {project_name}"
                
            self.setWindowTitle(title)
        else:
            self.setWindowTitle(base_title)
    
    def update_memory_display(self):
        """Update the memory usage display in status bar."""
        try:
            memory_text = self.memory_monitor.get_memory_info_text()
            self.memory_label.setText(memory_text)
            
            # Warn if memory usage is very high (>2GB)
            memory_mb = self.memory_monitor.get_memory_usage_mb()
            if memory_mb > 2048:
                self.memory_label.setStyleSheet("""
                    QLabel {
                        color: #ffffff;
                        font-size: 10px;
                        padding: 2px 6px;
                        border: 1px solid #f44336;
                        border-radius: 3px;
                        background-color: #f44336;
                    }
                """)
                if not hasattr(self, '_high_memory_warned'):
                    self.log_message(f"⚠️ High memory usage: {memory_mb:.0f} MB")
                    self._high_memory_warned = True
            else:
                self.memory_label.setStyleSheet("""
                    QLabel {
                        color: #888888;
                        font-size: 10px;
                        padding: 2px 6px;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        background-color: #2e2e2e;
                    }
                """)
                self._high_memory_warned = False
                
        except Exception as e:
            print(f"Error updating memory display: {e}")
    
    def start_background_operation(self, operation_name, target_function, *args, **kwargs):
        """Start a background operation with progress tracking."""
        try:
            # Stop any existing operation
            if self.processing_thread and self.processing_thread.isRunning():
                self.processing_thread.cancel()
                self.processing_thread.wait(1000)  # Wait up to 1 second
                
            # Create new processing thread
            self.processing_thread = SDTMProcessingThread(
                operation_name, target_function, *args, **kwargs
            )
            
            # Connect signals
            self.processing_thread.progress_updated.connect(self.on_progress_updated)
            self.processing_thread.processing_completed.connect(self.on_processing_completed)
            self.processing_thread.error_occurred.connect(self.on_processing_error)
            
            # Show progress bar and start
            self.progress_bar.setVisible(True)
            self.status_label.setText(f"Starting {operation_name}...")
            self.processing_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start {operation_name}:\n{str(e)}")
    
    def on_progress_updated(self, percentage, message):
        """Handle progress updates from background thread."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        
    def on_processing_completed(self, result, operation_type):
        """Handle completion of background processing."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"{operation_type} completed successfully")
        self.log_message(f"✅ {operation_type} completed")
        
    def on_processing_error(self, error_message):
        """Handle errors from background processing."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Operation failed")
        self.log_message(f"❌ {error_message}")
        QMessageBox.critical(self, "Processing Error", error_message)