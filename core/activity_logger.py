import json
import os
from datetime import datetime

class ActivityLogger:
    def __init__(self, log_file="activity_logs.json"):
        # Store logs in the data directory if it exists, otherwise root
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        if os.path.exists(data_dir):
            self.log_file = os.path.join(data_dir, log_file)
        else:
            self.log_file = log_file
        
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, "w", encoding='utf-8') as f:
                    json.dump([], f)
            except OSError:
                # Fallback to local directory if permission issues or path issues
                self.log_file = "activity_logs.json"
                with open(self.log_file, "w", encoding='utf-8') as f:
                    json.dump([], f)

    def log_activity(self, activity_type, details, status, error=None):
        """
        Logs an activity.
        
        Args:
            activity_type (str): Type of activity (e.g., "Model Training", "Data Processing").
            details (str): Description or parameters of the activity.
            status (str): Status of the activity ("Success", "Failed", "Started").
            error (str, optional): Error message if failed.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "activity_type": activity_type,
            "details": details,
            "status": status,
            "error_message": str(error) if error else None
        }
        
        logs = self.get_logs()
        logs.append(entry)
        
        # Keep only the last 20 entries
        if len(logs) > 20:
            logs = logs[-20:]
            
        self._save_logs(logs)

    def get_logs(self):
        """Returns the list of logs."""
        try:
            with open(self.log_file, "r", encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_logs(self, logs):
        try:
            with open(self.log_file, "w", encoding='utf-8') as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        except OSError as e:
            print(f"Error saving logs: {e}")
