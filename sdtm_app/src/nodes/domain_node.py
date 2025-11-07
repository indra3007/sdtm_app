# Domain Node - Adds SDTM Domain column with selected value
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame
from PyQt6.QtGui import QFont
from .base_node import BaseNode
import pandas as pd

class DomainNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.title = "🏷️ Domain"
        self.content_label.setText("Adds SDTM Domain column")
        
        # Store selected domain value
        self.selected_domain = ""
        
        # SDTM Domain codes list
        self.domain_codes = [
            "TA", "TD", "TE", "TI", "TM", "TS", "TV",  # Trial Design
            "DM", "SV", "SE", "CO", "SM",              # Special Purpose
            "AG", "CM", "EC", "EX", "ML", "PR", "SU",  # Interventions
            "AE", "APMH", "CE", "DS",                  # Events
            "DV", "HO", "MH", "CV", "DA", "DD",        # Findings
            "EG", "FT", "IE", "IS", "LB", "LC",        # Findings (continued)
            "MB", "MI", "MK", "MO", "MS", "NV",        # Findings (continued)
            "OE", "PC", "PE", "PP", "QS", "RE",        # Findings (continued)
            "RP", "RS", "SC", "SS", "TR", "TU",        # Findings (continued)
            "UR", "VS", "FA", "SR", "OI"               # Findings (continued)
        ]
        
        self.setupUI()
        
    def setupUI(self):
        """Setup the Domain node UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🏷️ SDTM Domain Assignment")
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
        
        # Domain Selection
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
        
        for code in self.domain_codes:
            description = domain_descriptions.get(code, f"{code} - SDTM Domain")
            self.domain_combo.addItem(description, code)
        
        self.domain_combo.currentTextChanged.connect(self.on_domain_changed)
        domain_layout.addWidget(self.domain_combo)
        
        layout.addLayout(domain_layout)
        
        # Info label
        self.info_label = QLabel("💡 Select a domain code to add 'DOMAIN' column to the data")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(self.info_label)
        
        # Apply button
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("✅ Apply Domain")
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.apply_button.clicked.connect(self.apply_domain)
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)
        layout.addLayout(button_layout)
        
        # Set the layout
        self.content_widget.setLayout(layout)
        
    def on_domain_changed(self):
        """Handle domain selection change"""
        current_data = self.domain_combo.currentData()
        self.selected_domain = current_data if current_data else ""
        
        if self.selected_domain:
            self.info_label.setText(f"🎯 Ready to add DOMAIN column with value: '{self.selected_domain}'")
            self.apply_button.setEnabled(True)
            self.apply_button.setText(f"✅ Apply Domain: {self.selected_domain}")
        else:
            self.info_label.setText("💡 Select a domain code to add 'DOMAIN' column to the data")
            self.apply_button.setEnabled(False)
            self.apply_button.setText("✅ Apply Domain")
            
    def apply_domain(self):
        """Apply the selected domain to create/update DOMAIN column"""
        if not self.selected_domain:
            self.info_label.setText("❌ Please select a domain first")
            return
            
        # Get input data
        input_data = self.get_input_data()
        if input_data is None or input_data.empty:
            self.info_label.setText("❌ No input data available")
            return
            
        try:
            # Create a copy of the input data
            output_data = input_data.copy()
            
            # Add or update the DOMAIN column
            output_data['DOMAIN'] = self.selected_domain
            
            # Store the output data
            self.output_data = output_data
            
            # Update info label
            self.info_label.setText(
                f"✅ Successfully added DOMAIN column with value '{self.selected_domain}' "
                f"to {len(output_data)} rows"
            )
            
            # Emit data changed signal
            if hasattr(self, 'data_changed'):
                self.data_changed.emit()
                
            print(f"🏷️ DOMAIN: Added DOMAIN column with value '{self.selected_domain}' to {len(output_data)} rows")
            
        except Exception as e:
            self.info_label.setText(f"❌ Error applying domain: {str(e)}")
            print(f"❌ DOMAIN ERROR: {str(e)}")
            
    def get_input_data(self):
        """Get input data from connected nodes"""
        if not hasattr(self, 'canvas') or not self.canvas:
            return None
            
        # Find input connections
        for connection in self.canvas.connections:
            if connection.output_node == self:
                input_node = connection.input_node
                if hasattr(input_node, 'output_data') and input_node.output_data is not None:
                    return input_node.output_data
                    
        return None
        
    def execute(self):
        """Execute the domain assignment"""
        return self.apply_domain()
        
    def get_output_data(self):
        """Get the output data with domain column added"""
        return getattr(self, 'output_data', None)
        
    def serialize(self):
        """Serialize the domain node state"""
        return {
            'type': 'DomainNode',
            'selected_domain': self.selected_domain,
            'position': {'x': self.pos().x(), 'y': self.pos().y()}
        }
        
    def deserialize(self, data):
        """Deserialize the domain node state"""
        if 'selected_domain' in data:
            self.selected_domain = data['selected_domain']
            
            # Update UI to reflect loaded state
            if self.selected_domain:
                for i in range(self.domain_combo.count()):
                    if self.domain_combo.itemData(i) == self.selected_domain:
                        self.domain_combo.setCurrentIndex(i)
                        break
                        
                self.info_label.setText(f"🎯 Ready to add DOMAIN column with value: '{self.selected_domain}'")
                self.apply_button.setEnabled(True)
                self.apply_button.setText(f"✅ Apply Domain: {self.selected_domain}")