# SDTM Application - AI Assistant Instructions

## Project Overview
This is a **no-code PyQt6 GUI application** for SDTM (Study Data Tabulation Model) clinical data processing. The application provides a visual flow-based interface for transforming and validating clinical trial data according to FDA regulatory standards.

## Application Architecture

### Technology Stack
- **GUI Framework**: PyQt6 with modern styling and custom widgets
- **Data Processing**: pandas + pyreadstat for SAS7BDAT file handling
- **Flow Engine**: Visual node-based data transformation pipeline
- **SDTM Compliance**: Built-in validation rules and controlled terminology

### Project Structure
```
src/
├── main.py                 # Application entry point
├── ui/                    # PyQt6 UI components
├── components/            # Reusable transformation nodes
├── data/                  # Data models and pipeline engine
└── utils/                 # Helper functions and validators
raw/                       # Source SAS7BDAT files (dm, ae, aes)
```

### Data Flow Paradigm
The application uses a **visual node-based flow** where users:
1. Load SAS datasets from `raw/` directory using pyreadstat
2. Drag transformation nodes onto canvas
3. Connect nodes to create data processing pipelines
4. Execute flows to generate SDTM-compliant outputs

## Core Transformation Nodes

### Data Operations
- **Column Renamer**: Rename variables to SDTM standards
- **Expression Builder**: Create derived variables with formula editor
- **Merge/Join**: Combine datasets on USUBJID or other keys
- **Set Operations**: Union, intersect, subtract datasets
- **Transpose**: Pivot wide/long format transformations

### Data Type & String Operations
- **String Manipulation**: Concatenate, substring, case conversion
- **Type Conversion**: Number ↔ String with validation
- **Rule Engine**: Complex business logic with if-then-else chains
- **Conditional Logic**: Multi-condition transformations

### Data Management
- **Row Filter**: Filter records based on conditions
- **Column Keep/Drop**: Select relevant variables
- **GroupBy**: Aggregate data by categories
- **Sorter**: Multi-column sorting with SDTM ordering

## SDTM-Specific Features

### Domain Standards Integration
- **DM (Demographics)**: USUBJID, AGE, SEX, RACE validation
- **AE (Adverse Events)**: AETERM, AESTDTC, AEREL terminology checks
- **AES (Supplemental)**: QNAM/QVAL pair validation

### Regulatory Compliance
- **USUBJID Consistency**: Automatic cross-domain linking validation
- **Date Format Validation**: ISO 8601 compliance for DTC variables
- **Controlled Terminology**: Built-in CDISC CT validation
- **Data Lineage**: Full transformation history tracking

## Development Guidelines

### UI/UX Patterns
- Use **drag-and-drop** for intuitive flow building
- Implement **property panels** for node configuration
- Provide **real-time preview** of transformations
- Include **data profiling** widgets for quality assessment

### Code Organization
- Separate **UI logic** from **data processing logic**
- Create **reusable node base classes** for consistency
- Implement **undo/redo** functionality for flow editing
- Use **threading** for long-running data operations

### SDTM Compliance Priority
- Validate **required variables** exist in each domain
- Check **referential integrity** across linked domains
- Ensure **controlled terminology** compliance
- Maintain **audit trail** for regulatory submissions

When implementing features, prioritize SDTM regulatory requirements and user experience over technical complexity.