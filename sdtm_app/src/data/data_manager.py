"""
Data Manager - Core data handling and SAS dataset loading
Manages data loading, caching, and basic transformations.
"""

import pandas as pd
import pyreadstat
import numpy as np
from typing import Dict, List, Optional, Any
import os
from pathlib import Path


class DataManager:
    """Central data management class for SDTM application."""
    
    def __init__(self, auto_sdtm_processing=False):
        self.datasets = {}  # Cache loaded datasets
        self.metadata = {}  # Store dataset metadata
        self.auto_sdtm_processing = auto_sdtm_processing  # Control automatic SDTM transformations
        
    def load_sas_dataset(self, file_path: str) -> pd.DataFrame:
        """
        Load a SAS7BDAT dataset using pyreadstat.
        
        Args:
            file_path: Path to the SAS dataset file
            
        Returns:
            pandas DataFrame with the loaded data
        """
        try:
            # Use pyreadstat to read SAS file
            df, meta = pyreadstat.read_sas7bdat(file_path)
            
            # Store metadata
            filename = os.path.basename(file_path)
            self.metadata[filename] = {
                "file_path": file_path,
                "column_names": meta.column_names,
                "column_labels": meta.column_labels,
                "number_rows": meta.number_rows,
                "number_columns": meta.number_columns,
                "file_encoding": meta.file_encoding,
                "creation_time": getattr(meta, 'creation_time', None),
                "modified_time": getattr(meta, 'modified_time', None)
            }
            
            # Cache the dataset
            self.datasets[filename] = df
            
            # Clean and prepare data
            df = self.prepare_dataset(df, filename)
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to load SAS dataset {file_path}: {str(e)}")
            
    def prepare_dataset(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """
        Prepare dataset for SDTM processing.
        
        Args:
            df: Raw DataFrame
            filename: Dataset filename
            
        Returns:
            Cleaned DataFrame
        """
        # Make a copy to avoid modifying original
        prepared_df = df.copy()
        
        # Convert column names to uppercase (SDTM standard)
        prepared_df.columns = prepared_df.columns.str.upper()
        
        # Handle missing values appropriately
        # Convert SAS missing values to pandas NaN
        prepared_df = prepared_df.replace(['.', ''], np.nan).infer_objects(copy=False)
        
        # SDTM-specific preparations based on domain (optional)
        if self.auto_sdtm_processing:
            domain = filename.split('.')[0].upper()
            
            try:
                if domain == 'DM':
                    prepared_df = self.prepare_dm_domain(prepared_df)
                elif domain == 'AE':
                    prepared_df = self.prepare_ae_domain(prepared_df)
                elif domain == 'AES':
                    prepared_df = self.prepare_aes_domain(prepared_df)
                print(f"✅ Applied SDTM transformations for {domain} domain")
            except Exception as e:
                # If domain-specific preparation fails, just log and continue
                print(f"Warning: Domain-specific preparation for {domain} failed: {str(e)}")
                # Continue with generic preparation
        else:
            print(f"ℹ️ Skipped automatic SDTM transformations (raw data preserved)")
            
        return prepared_df
    
    def set_auto_sdtm_processing(self, enabled: bool):
        """Enable or disable automatic SDTM transformations."""
        self.auto_sdtm_processing = enabled
        status = "enabled" if enabled else "disabled"
        print(f"🔧 Automatic SDTM processing {status}")
        
    def prepare_dm_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare Demographics domain."""
        # Only rename X_USUBJID to USUBJID if it exists
        if 'USUBJID' not in df.columns and 'X_USUBJID' in df.columns:
            df['USUBJID'] = df['X_USUBJID'].astype(str)
            print(f"✅ Renamed X_USUBJID to USUBJID column")
                
        # Standardize date columns
        date_columns = [col for col in df.columns if col.endswith('DTC')]
        for col in date_columns:
            if col in df.columns:
                df[col] = self.standardize_datetime(df[col])
                
        return df
        
    def prepare_ae_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare Adverse Events domain."""
        # Only rename X_USUBJID to USUBJID if it exists
        if 'USUBJID' not in df.columns and 'X_USUBJID' in df.columns:
            df['USUBJID'] = df['X_USUBJID'].astype(str)
            print(f"✅ Renamed X_USUBJID to USUBJID column")
                
        # Standardize date columns
        date_columns = [col for col in df.columns if col.endswith('DTC')]
        for col in date_columns:
            if col in df.columns:
                df[col] = self.standardize_datetime(df[col])
                
        return df
        
    def prepare_aes_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare Adverse Events Supplemental domain."""
        # Make required columns optional - just log warnings if missing
        required_cols = ['USUBJID', 'QNAM', 'QVAL']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"Warning: AES domain missing recommended columns: {missing_cols}")
            
        # Only rename X_USUBJID to USUBJID if it exists
        if 'USUBJID' not in df.columns and 'X_USUBJID' in df.columns:
            df['USUBJID'] = df['X_USUBJID'].astype(str)
            print(f"✅ Renamed X_USUBJID to USUBJID column")
                
        return df
        
    def standardize_datetime(self, series: pd.Series) -> pd.Series:
        """
        Standardize datetime values to ISO 8601 format.
        
        Args:
            series: Pandas Series with datetime values
            
        Returns:
            Series with standardized datetime strings
        """
        try:
            # Try to parse existing datetime values with multiple formats
            dt_series = pd.to_datetime(series, errors='coerce')
            
            # Format as ISO 8601 strings
            # Use different formats based on precision
            formatted = dt_series.apply(lambda x: 
                x.strftime('%Y-%m-%dT%H:%M:%S') if pd.notna(x) and (x.hour != 0 or x.minute != 0 or x.second != 0)
                else x.strftime('%Y-%m-%d') if pd.notna(x)
                else np.nan
            )
            
            return formatted
            
        except Exception:
            # If conversion fails, return original series
            return series
            
    def get_dataset(self, filename: str) -> Optional[pd.DataFrame]:
        """Get a cached dataset."""
        return self.datasets.get(filename)
        
    def get_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get dataset metadata."""
        return self.metadata.get(filename)
        
    def list_datasets(self) -> List[str]:
        """List all loaded datasets."""
        return list(self.datasets.keys())
        
    def export_dataset(self, df: pd.DataFrame, file_path: str, format: str = 'sas') -> None:
        """
        Export dataset to various formats.
        
        Args:
            df: DataFrame to export
            file_path: Output file path
            format: Export format ('sas', 'csv', 'excel')
        """
        try:
            if format.lower() == 'sas':
                # Export to SAS7BDAT using pyreadstat
                pyreadstat.write_sas7bdat(df, file_path)
            elif format.lower() == 'csv':
                df.to_csv(file_path, index=False)
            elif format.lower() in ['excel', 'xlsx']:
                df.to_excel(file_path, index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            raise Exception(f"Failed to export dataset to {file_path}: {str(e)}")
            
    def validate_usubjid_consistency(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Validate USUBJID consistency across datasets.
        
        Args:
            datasets: Dictionary of dataset name -> DataFrame
            
        Returns:
            Validation results
        """
        results = {
            "consistent": True,
            "issues": [],
            "usubjid_counts": {}
        }
        
        all_usubjids = set()
        
        # Collect all USUBJIDs
        for name, df in datasets.items():
            if 'USUBJID' in df.columns:
                dataset_usubjids = set(df['USUBJID'].dropna().unique())
                results["usubjid_counts"][name] = len(dataset_usubjids)
                all_usubjids.update(dataset_usubjids)
            else:
                results["issues"].append(f"Dataset {name} missing USUBJID column")
                results["consistent"] = False
                
        # Check for orphan records
        for name, df in datasets.items():
            if 'USUBJID' in df.columns:
                dataset_usubjids = set(df['USUBJID'].dropna().unique())
                orphans = dataset_usubjids - all_usubjids
                if orphans:
                    results["issues"].append(f"Dataset {name} has orphan USUBJIDs: {len(orphans)}")
                    results["consistent"] = False
                    
        return results
        
    def merge_datasets(self, 
                      left_df: pd.DataFrame, 
                      right_df: pd.DataFrame,
                      on: str = 'USUBJID',
                      how: str = 'inner') -> pd.DataFrame:
        """
        Merge two datasets on specified key.
        
        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            on: Column to merge on
            how: Type of merge ('inner', 'left', 'right', 'outer')
            
        Returns:
            Merged DataFrame
        """
        try:
            # Check if merge key exists in both datasets
            if on not in left_df.columns:
                raise ValueError(f"Merge key '{on}' not found in left dataset")
            if on not in right_df.columns:
                raise ValueError(f"Merge key '{on}' not found in right dataset")
                
            # Perform merge
            merged_df = pd.merge(left_df, right_df, on=on, how=how, suffixes=('', '_right'))
            
            return merged_df
            
        except Exception as e:
            raise Exception(f"Failed to merge datasets: {str(e)}")
            
    def apply_column_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Apply column renaming mapping.
        
        Args:
            df: DataFrame to rename columns
            mapping: Dictionary of old_name -> new_name
            
        Returns:
            DataFrame with renamed columns
        """
        try:
            # Check if all source columns exist
            missing_cols = [col for col in mapping.keys() if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Source columns not found: {missing_cols}")
                
            # Apply renaming
            renamed_df = df.rename(columns=mapping)
            
            return renamed_df
            
        except Exception as e:
            raise Exception(f"Failed to apply column mapping: {str(e)}")