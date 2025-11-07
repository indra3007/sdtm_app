"""
Project Management Dialog - UI for managing SDTM workflow projects.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QPushButton, QLabel, QLineEdit, 
                           QTextEdit, QMessageBox, QSplitter, QGroupBox,
                           QFileDialog, QInputDialog, QMenu, QHeaderView,
                           QWidget, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction
import os
from datetime import datetime
from data.project_manager import ProjectManager

class ProjectDialog(QDialog):
    """Dialog for managing SDTM workflow projects."""
    
    project_selected = pyqtSignal(str)  # Emitted when project is selected for loading
    flow_selected = pyqtSignal(str, str)  # project_path, flow_name
    
    def __init__(self, parent=None, current_project_path=None):
        super().__init__(parent)
        self.setWindowTitle("SDTM Project Manager")
        self.setModal(True)
        self.resize(900, 600)
        
        self.project_manager = ProjectManager()
        self.current_project_path = current_project_path
        self.selected_project_path = None
        self.selected_flow_name = None
        
        self.init_ui()
        self.load_projects()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("SDTM Project Manager")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Projects
        self.create_projects_panel(splitter)
        
        # Right panel - Flows and details
        self.create_details_panel(splitter)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Action buttons
        self.new_project_btn = QPushButton("📁 New Project")
        self.new_project_btn.clicked.connect(self.new_project)
        
        self.load_project_btn = QPushButton("📂 Load Project")
        self.load_project_btn.clicked.connect(self.load_project)
        self.load_project_btn.setEnabled(False)
        
        self.load_flow_btn = QPushButton("🔄 Load Complete Workflow")
        self.load_flow_btn.clicked.connect(self.load_flow)
        self.load_flow_btn.setEnabled(False)
        
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_project)
        self.export_btn.setEnabled(False)
        
        self.import_btn = QPushButton("📥 Import")
        self.import_btn.clicked.connect(self.import_project)
        
        button_layout.addWidget(self.new_project_btn)
        button_layout.addWidget(self.load_project_btn)
        button_layout.addWidget(self.load_flow_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.import_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def create_projects_panel(self, parent):
        """Create the projects panel."""
        projects_widget = QWidget()
        layout = QVBoxLayout(projects_widget)
        
        # Projects group
        projects_group = QGroupBox("Projects")
        projects_layout = QVBoxLayout(projects_group)
        
        self.projects_tree = QTreeWidget()
        self.projects_tree.setHeaderLabels(["Name", "Modified", "Flows"])
        self.projects_tree.itemSelectionChanged.connect(self.on_project_selected)
        self.projects_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.projects_tree.customContextMenuRequested.connect(self.show_project_context_menu)
        
        projects_layout.addWidget(self.projects_tree)
        layout.addWidget(projects_group)
        
        parent.addWidget(projects_widget)
        
    def create_details_panel(self, parent):
        """Create the details panel."""
        details_widget = QWidget()
        layout = QVBoxLayout(details_widget)
        
        # Project info group
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)
        
        self.project_name_label = QLabel("-")
        self.project_path_label = QLabel("-")
        self.project_created_label = QLabel("-")
        self.project_description = QTextEdit()
        self.project_description.setMaximumHeight(60)
        self.project_description.setReadOnly(True)
        
        info_layout.addRow("Name:", self.project_name_label)
        info_layout.addRow("Path:", self.project_path_label)
        info_layout.addRow("Created:", self.project_created_label)
        info_layout.addRow("Description:", self.project_description)
        
        layout.addWidget(info_group)
        
        # Flows group
        flows_group = QGroupBox("Complete Workflows")
        flows_layout = QVBoxLayout(flows_group)
        
        self.flows_tree = QTreeWidget()
        self.flows_tree.setHeaderLabels(["Workflow Name", "Modified"])
        self.flows_tree.itemSelectionChanged.connect(self.on_flow_selected)
        self.flows_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.flows_tree.customContextMenuRequested.connect(self.show_flow_context_menu)
        
        flows_layout.addWidget(self.flows_tree)
        layout.addWidget(flows_group)
        
        parent.addWidget(details_widget)
        
    def load_projects(self):
        """Load and display all projects."""
        self.projects_tree.clear()
        projects = self.project_manager.list_projects()
        
        for project in projects:
            item = QTreeWidgetItem(self.projects_tree)
            item.setText(0, project['name'])
            item.setText(1, self.format_date(project.get('modified', project.get('created', ''))))
            item.setText(2, str(len(project.get('flows', []))))
            item.setData(0, Qt.ItemDataRole.UserRole, project['path'])
            
            # Highlight current project
            if project['path'] == self.current_project_path:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setFont(1, font)
                item.setFont(2, font)
        
        # Auto-resize columns
        header = self.projects_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
    def on_project_selected(self):
        """Handle project selection."""
        items = self.projects_tree.selectedItems()
        if items:
            item = items[0]
            project_path = item.data(0, Qt.ItemDataRole.UserRole)
            self.selected_project_path = project_path
            
            # Update project info
            self.update_project_info(project_path)
            
            # Load flows
            self.load_flows(project_path)
            
            # Enable buttons
            self.load_project_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
        else:
            self.selected_project_path = None
            self.clear_project_info()
            self.flows_tree.clear()
            self.load_project_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.load_flow_btn.setEnabled(False)
            
    def update_project_info(self, project_path):
        """Update project information display."""
        metadata = self.project_manager._load_project_metadata(project_path)
        if metadata:
            self.project_name_label.setText(metadata.get('name', 'Unknown'))
            self.project_path_label.setText(project_path)
            self.project_created_label.setText(self.format_date(metadata.get('created', '')))
            self.project_description.setPlainText(metadata.get('description', ''))
        else:
            self.project_name_label.setText(os.path.basename(project_path))
            self.project_path_label.setText(project_path)
            self.project_created_label.setText('Unknown')
            self.project_description.setPlainText('Legacy project')
            
    def clear_project_info(self):
        """Clear project information display."""
        self.project_name_label.setText("-")
        self.project_path_label.setText("-")
        self.project_created_label.setText("-")
        self.project_description.setPlainText("")
        
    def load_flows(self, project_path):
        """Load and display flows for selected project."""
        self.flows_tree.clear()
        flows = self.project_manager.list_flows(project_path)
        
        for flow in flows:
            item = QTreeWidgetItem(self.flows_tree)
            item.setText(0, flow.get('name', 'Unknown'))
            item.setText(1, self.format_date(flow.get('modified', flow.get('created', ''))))
            item.setData(0, Qt.ItemDataRole.UserRole, flow.get('name'))
            
        # Auto-resize columns
        header = self.flows_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
    def on_flow_selected(self):
        """Handle flow selection."""
        items = self.flows_tree.selectedItems()
        if items and self.selected_project_path:
            item = items[0]
            flow_name = item.data(0, Qt.ItemDataRole.UserRole)
            self.selected_flow_name = flow_name
            self.load_flow_btn.setEnabled(True)
        else:
            self.selected_flow_name = None
            self.load_flow_btn.setEnabled(False)
            
    def new_project(self):
        """Create a new project."""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_edit.text().strip()
            description = dialog.description_edit.toPlainText().strip()
            
            try:
                project_path = self.project_manager.create_project(name, description)
                QMessageBox.information(self, "Success", f"Project '{name}' created successfully!")
                self.load_projects()
                
                # Select the new project
                for i in range(self.projects_tree.topLevelItemCount()):
                    item = self.projects_tree.topLevelItem(i)
                    if item.data(0, Qt.ItemDataRole.UserRole) == project_path:
                        self.projects_tree.setCurrentItem(item)
                        break
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")
                
    def load_project(self):
        """Load the selected project."""
        if self.selected_project_path:
            self.project_selected.emit(self.selected_project_path)
            self.accept()
            
    def load_flow(self):
        """Load the selected flow."""
        if self.selected_project_path and self.selected_flow_name:
            self.flow_selected.emit(self.selected_project_path, self.selected_flow_name)
            self.accept()
            
    def export_project(self):
        """Export the selected project."""
        if not self.selected_project_path:
            return
            
        project_name = os.path.basename(self.selected_project_path)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Project", f"{project_name}.zip", 
            "Zip files (*.zip);;All files (*.*)"
        )
        
        if file_path:
            try:
                success = self.project_manager.export_project(self.selected_project_path, file_path)
                if success:
                    QMessageBox.information(self, "Success", f"Project exported to {file_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export project")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                
    def import_project(self):
        """Import a project from zip file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Project", "", 
            "Zip files (*.zip);;All files (*.*)"
        )
        
        if file_path:
            # Get project name
            default_name = os.path.splitext(os.path.basename(file_path))[0]
            name, ok = QInputDialog.getText(
                self, "Import Project", "Project name:", text=default_name
            )
            
            if ok and name.strip():
                try:
                    project_path = self.project_manager.import_project(file_path, name.strip())
                    if project_path:
                        QMessageBox.information(self, "Success", f"Project '{name}' imported successfully!")
                        self.load_projects()
                    else:
                        QMessageBox.critical(self, "Error", "Failed to import project")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
                    
    def show_project_context_menu(self, position):
        """Show context menu for projects."""
        item = self.projects_tree.itemAt(position)
        if item:
            menu = QMenu(self)
            
            load_action = QAction("Load Project", self)
            load_action.triggered.connect(self.load_project)
            menu.addAction(load_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete Project", self)
            delete_action.triggered.connect(lambda: self.delete_project(item))
            menu.addAction(delete_action)
            
            menu.exec(self.projects_tree.mapToGlobal(position))
            
    def show_flow_context_menu(self, position):
        """Show context menu for flows."""
        item = self.flows_tree.itemAt(position)
        if item and self.selected_project_path:
            menu = QMenu(self)
            
            load_action = QAction("Load Flow", self)
            load_action.triggered.connect(self.load_flow)
            menu.addAction(load_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete Flow", self)
            delete_action.triggered.connect(lambda: self.delete_flow(item))
            menu.addAction(delete_action)
            
            menu.exec(self.flows_tree.mapToGlobal(position))
            
    def delete_project(self, item):
        """Delete a project."""
        project_path = item.data(0, Qt.ItemDataRole.UserRole)
        project_name = item.text(0)
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete project '{project_name}'?\n\n"
            f"This will permanently delete all flows and data in the project.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.project_manager.delete_project(project_path)
                if success:
                    QMessageBox.information(self, "Success", f"Project '{project_name}' deleted.")
                    self.load_projects()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete project")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed: {str(e)}")
                
    def delete_flow(self, item):
        """Delete a flow."""
        flow_name = item.data(0, Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete flow '{flow_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.project_manager.delete_flow(self.selected_project_path, flow_name)
                if success:
                    QMessageBox.information(self, "Success", f"Flow '{flow_name}' deleted.")
                    self.load_flows(self.selected_project_path)
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete flow")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed: {str(e)}")
                
    def format_date(self, date_str):
        """Format date string for display."""
        if not date_str or date_str == 'Unknown':
            return 'Unknown'
            
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str


class NewProjectDialog(QDialog):
    """Dialog for creating a new project."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New SDTM Project")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter project description (optional)...")
        self.description_edit.setMaximumHeight(100)
        
        form_layout.addRow("Project Name:", self.name_edit)
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        create_btn.setDefault(True)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Enable create button only when name is entered
        self.name_edit.textChanged.connect(
            lambda text: create_btn.setEnabled(bool(text.strip()))
        )
        create_btn.setEnabled(False)
        
    def accept(self):
        """Accept dialog if name is valid."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a project name.")
            return
            
        super().accept()