"""CSV Tools for MCP Server"""
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


class CSVTools:
    """Tools for reading and writing CSV files"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def read_csv(
        self,
        filename: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read data from a CSV file with optional filtering
        
        Args:
            filename: Name of the CSV file
            filters: Dictionary of column:value pairs to filter by
            columns: List of columns to return (None = all columns)
            limit: Maximum number of rows to return
            
        Returns:
            Dictionary with data and metadata
        """
        try:
            filepath = self.data_dir / filename
            
            if not filepath.exists():
                return {
                    "success": False,
                    "error": f"File {filename} not found",
                    "data": []
                }
            
            # Read CSV
            df = pd.read_csv(filepath)
            
            # Apply filters
            if filters:
                for column, value in filters.items():
                    if column in df.columns:
                        df = df[df[column] == value]
            
            # Select columns
            if columns:
                available_cols = [col for col in columns if col in df.columns]
                df = df[available_cols]
            
            # Apply limit
            if limit:
                df = df.head(limit)
            
            # Convert to dict
            data = df.to_dict(orient='records')
            
            return {
                "success": True,
                "filename": filename,
                "rows": len(data),
                "columns": list(df.columns),
                "data": data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    def write_csv(
        self,
        filename: str,
        data: List[Dict[str, Any]],
        mode: str = "overwrite"
    ) -> Dict[str, Any]:
        """
        Write data to a CSV file
        
        Args:
            filename: Name of the CSV file
            data: List of dictionaries to write
            mode: "overwrite", "append", or "update"
            
        Returns:
            Dictionary with operation result
        """
        try:
            filepath = self.data_dir / filename
            
            # Convert data to DataFrame
            new_df = pd.DataFrame(data)
            
            if mode == "append" and filepath.exists():
                # Append to existing file
                existing_df = pd.read_csv(filepath)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(filepath, index=False)
                rows_written = len(new_df)
                
            elif mode == "update" and filepath.exists():
                # Update existing rows (requires 'id' column)
                existing_df = pd.read_csv(filepath)
                if 'id' not in new_df.columns or 'id' not in existing_df.columns:
                    return {
                        "success": False,
                        "error": "Update mode requires 'id' column in data"
                    }
                
                # Update matching rows
                existing_df.set_index('id', inplace=True)
                new_df.set_index('id', inplace=True)
                existing_df.update(new_df)
                existing_df.reset_index(inplace=True)
                existing_df.to_csv(filepath, index=False)
                rows_written = len(new_df)
                
            else:
                # Overwrite or create new file
                new_df.to_csv(filepath, index=False)
                rows_written = len(new_df)
            
            return {
                "success": True,
                "filename": filename,
                "mode": mode,
                "rows_written": rows_written,
                "message": f"Successfully wrote {rows_written} rows to {filename}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_csv_files(self) -> Dict[str, Any]:
        """List all CSV files in the data directory"""
        try:
            csv_files = list(self.data_dir.glob("*.csv"))
            files_info = []
            
            for file in csv_files:
                df = pd.read_csv(file)
                files_info.append({
                    "filename": file.name,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "size_bytes": file.stat().st_size
                })
            
            return {
                "success": True,
                "files": files_info,
                "total_files": len(files_info)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": []
            }
