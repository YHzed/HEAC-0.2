import os
import joblib
import datetime
from pathlib import Path

class ModelManager:
    def __init__(self, save_dir="saved_models"):
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def save_model(self, model, metrics, task_type, model_name, feature_columns=None):
        """
        Save the model and its metadata.
        """
        # Ensure name doesn't have extension
        if model_name.endswith('.joblib'):
            model_name = model_name[:-7]
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            'model': model,
            'metrics': metrics,
            'task_type': task_type,
            'feature_columns': feature_columns,
            'timestamp': timestamp,
            'name': model_name
        }
        
        file_path = os.path.join(self.save_dir, f"{model_name}.joblib")
        try:
            joblib.dump(data, file_path)
            return True, f"Model saved successfully to {file_path}"
        except Exception as e:
            return False, str(e)

    def load_model(self, model_name):
        """
        Load a model by name (with or without extension).
        """
        if not model_name.endswith('.joblib'):
            model_name += '.joblib'
            
        file_path = os.path.join(self.save_dir, model_name)
        
        if not os.path.exists(file_path):
            return None, "File not found."
            
        try:
            data = joblib.load(file_path)
            return data, "Loaded successfully"
        except Exception as e:
            return None, str(e)

    def list_models(self):
        """
        List all saved models with metadata.
        """
        models = []
        if not os.path.exists(self.save_dir):
            return models
            
        for f in os.listdir(self.save_dir):
            if f.endswith('.joblib'):
                file_path = os.path.join(self.save_dir, f)
                try:
                    # We load the whole object to get metadata, might be slow if models are huge
                    # Optimization: Store metadata in separate json or just rely on file stats
                    # For now, let's just inspect file stat + maybe load if needed, 
                    # but loading everything just to list is bad practice if files are large.
                    # Let's just return file info for now and rely on naming/loading when selected.
                    # OR: we can trust the user knows what they saved. 
                    # Improved: let's try to load just to get 'metrics' if strictly needed, 
                    # but for speed, let's just use file creation time/size.
                    
                    stats = os.stat(file_path)
                    size_mb = round(stats.st_size / (1024 * 1024), 2)
                    mod_time = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    models.append({
                        'name': f, # filename
                        'display_name': f[:-7], # name without extension
                        'size': f"{size_mb} MB",
                        'date': mod_time
                    })
                except Exception:
                    continue
        return models

    def delete_model(self, model_name):
        if not model_name.endswith('.joblib'):
            model_name += '.joblib'
        
        file_path = os.path.join(self.save_dir, model_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True, "Model deleted."
            except Exception as e:
                return False, str(e)
        return False, "File not found."

    def save_uploaded_model(self, file_obj, name_override=None):
        """
        Save a model uploaded via Streamlit.
        """
        try:
            name = name_override if name_override else file_obj.name
            if not name.endswith('.joblib'):
                name += '.joblib'
                
            file_path = os.path.join(self.save_dir, name)
            
            with open(file_path, "wb") as f:
                f.write(file_obj.getbuffer())
                
            return True, "Model uploaded successfully."
        except Exception as e:
            return False, str(e)
