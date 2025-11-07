"""
Project Manager - Handle saving/loading of SDTM workflow projects.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import shutil

class ProjectManager:
    """Manages SDTM workflow projects - saving, loading, and organization."""
    
    def __init__(self, base_projects_dir: str = None):
        """Initialize project manager with base directory for projects."""
        if base_projects_dir is None:
            # Create projects directory in app folder
            self.base_projects_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'projects')
        else:
            self.base_projects_dir = base_projects_dir
            
        # Ensure projects directory exists
        os.makedirs(self.base_projects_dir, exist_ok=True)
        
    def create_project(self, project_name: str, description: str = "") -> str:
        """Create a new project directory."""
        # Clean project name for filesystem
        safe_name = self._sanitize_filename(project_name)
        project_path = os.path.join(self.base_projects_dir, safe_name)
        
        # Create project directory structure
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, 'data'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'flows'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'outputs'), exist_ok=True)
        
        # Create project metadata
        metadata = {
            "name": project_name,
            "description": description,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "version": "1.0",
            "flows": []
        }
        
        self._save_project_metadata(project_path, metadata)
        return project_path
    
    def save_flow(self, project_path: str, flow_name: str, flow_data: Dict[str, Any]) -> str:
        """Save a workflow to the project."""
        flows_dir = os.path.join(project_path, 'flows')
        safe_flow_name = self._sanitize_filename(flow_name)
        flow_file = os.path.join(flows_dir, f"{safe_flow_name}.json")
        
        # Add metadata to flow
        flow_data_with_meta = {
            "metadata": {
                "name": flow_name,
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "version": "1.0"
            },
            "flow": flow_data
        }
        
        # Save flow file
        with open(flow_file, 'w', encoding='utf-8') as f:
            json.dump(flow_data_with_meta, f, indent=2, ensure_ascii=False)
        
        # Update project metadata
        self._update_project_flows(project_path, flow_name, safe_flow_name)
        
        return flow_file
    
    def load_flow(self, project_path: str, flow_name: str) -> Optional[Dict[str, Any]]:
        """Load a workflow from the project."""
        flows_dir = os.path.join(project_path, 'flows')
        safe_flow_name = self._sanitize_filename(flow_name)
        flow_file = os.path.join(flows_dir, f"{safe_flow_name}.json")
        
        print(f"🔍 PROJECT MANAGER: Loading flow '{flow_name}' from {flow_file}")
        
        if not os.path.exists(flow_file):
            print(f"❌ Flow file not found: {flow_file}")
            return None
            
        try:
            with open(flow_file, 'r', encoding='utf-8') as f:
                flow_data = json.load(f)
            
            print(f"📂 Loaded flow data keys: {list(flow_data.keys())}")
            
            # Handle both old and new formats
            result = flow_data.get('flow', flow_data)
            print(f"📊 Returning flow with {len(result.get('nodes', []))} nodes")
            return result
            
        except Exception as e:
            print(f"❌ Error loading flow: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all available projects."""
        projects = []
        
        if not os.path.exists(self.base_projects_dir):
            return projects
            
        for item in os.listdir(self.base_projects_dir):
            project_path = os.path.join(self.base_projects_dir, item)
            if os.path.isdir(project_path):
                metadata = self._load_project_metadata(project_path)
                if metadata:
                    metadata['path'] = project_path
                    projects.append(metadata)
                else:
                    # Fallback for projects without metadata
                    projects.append({
                        'name': item,
                        'description': 'Legacy project',
                        'path': project_path,
                        'created': 'Unknown',
                        'flows': []
                    })
        
        return sorted(projects, key=lambda x: x.get('modified', x.get('created', '')), reverse=True)
    
    def list_flows(self, project_path: str) -> List[Dict[str, Any]]:
        """List all flows in a project."""
        flows_dir = os.path.join(project_path, 'flows')
        flows = []
        
        if not os.path.exists(flows_dir):
            return flows
            
        for file in os.listdir(flows_dir):
            if file.endswith('.json'):
                flow_file = os.path.join(flows_dir, file)
                try:
                    with open(flow_file, 'r', encoding='utf-8') as f:
                        flow_data = json.load(f)
                    
                    metadata = flow_data.get('metadata', {
                        'name': file[:-5],  # Remove .json extension
                        'created': 'Unknown'
                    })
                    metadata['filename'] = file
                    flows.append(metadata)
                except Exception as e:
                    print(f"Error reading flow {file}: {e}")
        
        return sorted(flows, key=lambda x: x.get('modified', x.get('created', '')), reverse=True)
    
    def delete_project(self, project_path: str) -> bool:
        """Delete a project and all its contents."""
        try:
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False
    
    def delete_flow(self, project_path: str, flow_name: str) -> bool:
        """Delete a flow from a project."""
        try:
            flows_dir = os.path.join(project_path, 'flows')
            safe_flow_name = self._sanitize_filename(flow_name)
            flow_file = os.path.join(flows_dir, f"{safe_flow_name}.json")
            
            if os.path.exists(flow_file):
                os.remove(flow_file)
                self._remove_flow_from_project_metadata(project_path, flow_name)
                return True
            return False
        except Exception as e:
            print(f"Error deleting flow: {e}")
            return False
    
    def copy_data_to_project(self, project_path: str, source_files: List[str]) -> List[str]:
        """Copy data files to project data directory."""
        data_dir = os.path.join(project_path, 'data')
        copied_files = []
        
        for source_file in source_files:
            if os.path.exists(source_file):
                filename = os.path.basename(source_file)
                dest_file = os.path.join(data_dir, filename)
                try:
                    shutil.copy2(source_file, dest_file)
                    copied_files.append(dest_file)
                except Exception as e:
                    print(f"Error copying {source_file}: {e}")
        
        return copied_files
    
    def get_project_data_files(self, project_path: str) -> List[str]:
        """Get list of data files in project."""
        data_dir = os.path.join(project_path, 'data')
        data_files = []
        
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                file_path = os.path.join(data_dir, file)
                if os.path.isfile(file_path):
                    data_files.append(file_path)
        
        return sorted(data_files)
    
    def export_project(self, project_path: str, export_path: str) -> bool:
        """Export project to a zip file."""
        try:
            import zipfile
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, project_path)
                        zipf.write(file_path, arc_path)
            
            return True
        except Exception as e:
            print(f"Error exporting project: {e}")
            return False
    
    def import_project(self, import_path: str, project_name: str = None) -> Optional[str]:
        """Import project from a zip file."""
        try:
            import zipfile
            
            # Extract project name from zip if not provided
            if project_name is None:
                project_name = os.path.splitext(os.path.basename(import_path))[0]
            
            # Create project directory
            project_path = self.create_project(project_name, "Imported project")
            
            # Extract zip contents
            with zipfile.ZipFile(import_path, 'r') as zipf:
                zipf.extractall(project_path)
            
            return project_path
        except Exception as e:
            print(f"Error importing project: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for filesystem compatibility."""
        import re
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Limit length
        return filename[:100] if filename else 'unnamed'
    
    def _save_project_metadata(self, project_path: str, metadata: Dict[str, Any]):
        """Save project metadata file."""
        metadata_file = os.path.join(project_path, 'project.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _load_project_metadata(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Load project metadata file."""
        metadata_file = os.path.join(project_path, 'project.json')
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
        return None
    
    def _update_project_flows(self, project_path: str, flow_name: str, safe_flow_name: str):
        """Update project metadata with new flow."""
        metadata = self._load_project_metadata(project_path)
        if metadata:
            metadata['modified'] = datetime.now().isoformat()
            
            # Update or add flow to list
            flow_entry = {
                'name': flow_name,
                'filename': f"{safe_flow_name}.json",
                'modified': datetime.now().isoformat()
            }
            
            # Remove existing entry if it exists
            metadata['flows'] = [f for f in metadata['flows'] if f.get('name') != flow_name]
            metadata['flows'].append(flow_entry)
            
            self._save_project_metadata(project_path, metadata)
    
    def _remove_flow_from_project_metadata(self, project_path: str, flow_name: str):
        """Remove flow from project metadata."""
        metadata = self._load_project_metadata(project_path)
        if metadata:
            metadata['modified'] = datetime.now().isoformat()
            metadata['flows'] = [f for f in metadata['flows'] if f.get('name') != flow_name]
            self._save_project_metadata(project_path, metadata)