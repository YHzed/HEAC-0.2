import os
import pandas as pd
from datetime import datetime

class DatasetManager:
    def __init__(self, base_dir='datasets'):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save_dataset(self, data, name, file_type='csv'):
        """Save a dataframe to a file (csv, xlsx, parquet)."""
        if not name:
            return False, "Filename cannot be empty."
        
        # Sanitize filename (basic)
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
        if not safe_name:
             return False, "Invalid filename."

        if not safe_name.lower().endswith(f".{file_type}"):
            safe_name += f".{file_type}"
            
        file_path = os.path.join(self.base_dir, safe_name)
        
        try:
            if file_type == 'csv':
                data.to_csv(file_path, index=False)
            elif file_type == 'xlsx' or file_type == 'excel':
                 # Ensure xlsx extension if we say excel
                 if not file_path.endswith('.xlsx'):
                     file_path = file_path.rsplit('.', 1)[0] + '.xlsx'
                 data.to_excel(file_path, index=False)
            elif file_type == 'parquet':
                if not file_path.endswith('.parquet'):
                    file_path = file_path.rsplit('.', 1)[0] + '.parquet'
                data.to_parquet(file_path, index=False)
            else:
                return False, "Unsupported file type for saving (csv/xlsx/parquet only)."
            
            return True, "Dataset saved successfully."
        except Exception as e:
            return False, f"Error saving dataset: {str(e)}"

    def list_datasets(self):
        """List all saved datasets with metadata."""
        datasets = []
        if not os.path.exists(self.base_dir):
            return datasets
            
        for f in os.listdir(self.base_dir):
            if f.endswith('.csv') or f.endswith('.xlsx') or f.endswith('.parquet'):
                file_path = os.path.join(self.base_dir, f)
                stats = os.stat(file_path)
                datasets.append({
                    'name': f,
                    'size': f"{stats.st_size / 1024:.2f} KB",
                    'date': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'path': file_path
                })
        # Sort by latest
        datasets.sort(key=lambda x: x['date'], reverse=True)
        return datasets

    def load_dataset(self, filename):
        """Load a saved dataset."""
        file_path = os.path.join(self.base_dir, filename)
        if not os.path.exists(file_path):
            return None, "File not found."
            
        try:
            if filename.endswith('.csv'):
                data = pd.read_csv(file_path)
            elif filename.endswith('.xlsx'):
                data = pd.read_excel(file_path)
            elif filename.endswith('.parquet'):
                data = pd.read_parquet(file_path)
            else:
                 return None, "Unsupported file format."
            return data, "Loaded successfully."
        except Exception as e:
            return None, str(e)

    def delete_dataset(self, filename):
        """Delete a saved dataset."""
        file_path = os.path.join(self.base_dir, filename)
        if not os.path.exists(file_path):
            return False, "File not found."
        
        try:
            os.remove(file_path)
            return True, "Deleted successfully."
        except Exception as e:
            return False, str(e)
