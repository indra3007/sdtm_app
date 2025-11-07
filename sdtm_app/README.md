# 🧬 SDTM Flow Builder - Visual Clinical Data Transformation

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6.1-green?logo=qt)](https://www.qt.io/)
[![SDTM](https://img.shields.io/badge/CDISC-SDTM-orange)](https://www.cdisc.org/standards/foundational/sdtm)

**A modern, no-code GUI application for transforming clinical trial data into SDTM-compliant formats using visual flow-based programming.**

## 🚀 **Answer to Your Question: Using the Column Renamer Node**

### **Complete Workflow Example**

**"How do I use the rename node after dragging and dropping it?"**

#### **Step 1: Create the Node**
1. **Drag** the "🏷️ Column Renamer" from the left toolbar
2. **Drop** it anywhere on the central canvas
3. You'll see a node with blue (input) and orange (output) connection ports

#### **Step 2: Connect Your Data**
1. **Look for data source nodes** (auto-created when you load SAS files)
2. **Click and drag** from the **orange port** of your data source
3. **Connect to the blue port** of the Column Renamer
4. **See the blue connection line** indicating active data flow

#### **Step 3: Configure Column Mappings**
1. **Click** on the Column Renamer node to select it
2. **Property Panel opens** on the right side
3. **Available columns** from your data appear in dropdowns
4. **Add mappings** using the intuitive interface:

```
┌─────────────────────────────────────────────────────────┐
│ 🏷️ Column Rename Mappings                               │
├─────────────────────────────────────────────────────────│
│ Original Column    │ New Column Name │ Action          │
│ ▼ subject_id       │ USUBJID         │ 🗑️             │
│ ▼ age             │ AGE             │ 🗑️             │
│ ▼ sex             │ SEX             │ 🗑️             │
│                   │                 │                 │
│ [+ Add Mapping]   [💡 Suggest SDTM Names]              │
└─────────────────────────────────────────────────────────┘
```

5. **Click "💡 Suggest SDTM Names"** for automatic mapping suggestions
6. **Use "+Add Mapping"** to add more column transformations
7. **Select from dropdowns** or type new SDTM names

#### **Step 4: Execute and Review**
1. **Right-click the node** → "Execute Flow" (coming soon)
2. **Or use toolbar** "▶️ Run Flow" button  
3. **View results** in the Data Viewer panel (bottom)
4. **See transformed columns** with new SDTM names

---

## 🌟 Enhanced Features

## Features

### 🎯 Visual Flow Interface
- **Drag-and-drop** transformation nodes
- **Visual connections** between data operations
- **Real-time preview** of transformations
- **Modern dark theme** with professional styling

### 📊 Data Operations
- **Column Renamer**: Rename variables to SDTM standards
- **Expression Builder**: Create derived variables with formula editor
- **Merge/Join**: Combine datasets on USUBJID or other keys
- **Set Operations**: Union, intersect, subtract datasets
- **Transpose**: Pivot wide/long format transformations

### 🔧 Data Management
- **String Manipulation**: Concatenate, substring, case conversion
- **Type Conversion**: Number ↔ String with validation
- **Rule Engine**: Complex business logic with if-then-else chains
- **Row Filter**: Filter records based on conditions
- **Column Keep/Drop**: Select relevant variables
- **GroupBy**: Aggregate data by categories
- **Sorter**: Multi-column sorting with SDTM ordering

### ✅ SDTM Compliance
- **Domain Standards**: Built-in DM, AE, AES validation
- **USUBJID Consistency**: Automatic cross-domain linking validation
- **Date Format Validation**: ISO 8601 compliance for DTC variables
- **Controlled Terminology**: Built-in CDISC CT validation
- **Data Lineage**: Full transformation history tracking

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### Setup
1. **Clone or download** this repository
2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
cd src
python main.py
```

## Quick Start

1. **Open SAS Dataset**: Click "📁 Open" to load `.sas7bdat` files from the `raw/` directory
2. **Add Transformation Nodes**: Drag nodes from the left panel to the canvas
3. **Connect Nodes**: Create data flow by connecting output ports to input ports
4. **Configure Properties**: Select nodes to edit their properties in the right panel
5. **Execute Flow**: Click "▶️ Execute" to run your data transformation pipeline
6. **Validate SDTM**: Click "✅ Validate" to check regulatory compliance

## Data Requirements

### Input Data
- Place SAS7BDAT files in the `raw/` directory
- Supported domains: DM (Demographics), AE (Adverse Events), AES (AE Supplemental)
- Files should follow basic SDTM structure with USUBJID as subject identifier

### SDTM Standards
- **Demographics (DM)**: USUBJID, SUBJID, demographic variables (AGE, SEX, RACE, etc.)
- **Adverse Events (AE)**: USUBJID, AETERM, AESTDTC, AEENDTC, AESEV, AEREL, etc.
- **AE Supplemental (AES)**: Additional qualifiers for AE domain (QNAM, QVAL, QORIG)

## Project Structure

```
sdtm_app/
├── src/
│   ├── main.py                 # Application entry point
│   ├── ui/                     # PyQt6 UI components
│   │   ├── main_window.py      # Main application window
│   │   ├── flow_canvas.py      # Visual flow interface
│   │   ├── property_panel.py   # Node configuration panel
│   │   └── data_viewer.py      # Data preview and profiling
│   ├── data/
│   │   └── data_manager.py     # SAS data loading and management
│   ├── components/             # Transformation node implementations
│   └── utils/                  # Helper functions and validators
├── raw/                        # Source SAS7BDAT files
│   ├── dm.sas7bdat            # Demographics data
│   ├── ae.sas7bdat            # Adverse events data
│   └── aes.sas7bdat           # AE supplemental data
└── requirements.txt           # Python dependencies
```

## Development

### Technology Stack
- **GUI Framework**: PyQt6 with modern styling
- **Data Processing**: pandas + pyreadstat for SAS7BDAT handling
- **Flow Engine**: Custom visual node-based pipeline
- **SDTM Compliance**: Built-in validation rules and controlled terminology

### Adding New Transformation Nodes
1. Create node class in `src/components/`
2. Inherit from `BaseNode` in `flow_canvas.py`
3. Implement `get_properties()` method
4. Add to nodes palette in `main_window.py`
5. Add property panel support in `property_panel.py`

### Key Design Principles
- **Regulatory First**: SDTM compliance takes priority over performance
- **Data Integrity**: Never modify original raw data files
- **User Experience**: Intuitive drag-drop interface with real-time feedback
- **Extensibility**: Modular architecture for easy addition of new features

## Troubleshooting

### Common Issues
- **Import Error**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **SAS File Loading**: Verify pyreadstat is properly installed for SAS7BDAT support
- **Display Issues**: Application uses high DPI scaling; try different display scale settings

### Support
- Check the execution log panel for detailed error messages
- Verify your SAS files contain the expected SDTM structure
- Ensure USUBJID is present in all datasets for proper linking

## License

This project is for educational and research purposes in clinical data processing and SDTM compliance.