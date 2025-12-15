import pandas as pd
import numpy as np
import io
from sklearn.model_selection import train_test_split, LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.ensemble import IsolationForest

class DataProcessor:
    def __init__(self):
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.columns = None
        self.target_column = None
        self.encoders = {}
        self.scaler = None

    def load_data(self, file_buffer, file_type='csv'):
        """Load data from a file buffer."""
        try:
            if file_type == 'csv':
                self.data = pd.read_csv(file_buffer)
            elif file_type == 'excel':
                self.data = pd.read_excel(file_buffer)
            elif file_type == 'parquet':
                self.data = pd.read_parquet(file_buffer)
            else:
                raise ValueError("Unsupported file type")
            
            self.columns = self.data.columns.tolist()
            return True, "Data loaded successfully."
        except Exception as e:
            return False, str(e)

    def get_preview(self, rows=5):
        """Get a preview of the data."""
        if self.data is not None:
            return self.data.head(rows)
        return None

    def get_info(self):
        """Get information about data columns and types."""
        if self.data is not None:
            buffer = io.StringIO()
            self.data.info(buf=buffer)
            return buffer.getvalue()
        return None
    
    def get_statistics(self):
        """Get descriptive statistics."""
        if self.data is not None:
            return self.data.describe()
        return None

    def handle_missing_values(self, method='drop'):
        """Handle missing values in the dataframe."""
        if self.data is not None:
            if method == 'drop':
                self.data = self.data.dropna()
            elif method == 'mean':
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                self.data[numeric_cols] = self.data[numeric_cols].fillna(self.data[numeric_cols].mean())
            elif method == 'median':
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                self.data[numeric_cols] = self.data[numeric_cols].fillna(self.data[numeric_cols].median())
            elif method == 'mode':
                self.data = self.data.fillna(self.data.mode().iloc[0])
            return True
        return False

    def prepare_data(self, target_col=None, feature_columns=None, test_size=0.2, random_state=42, use_scaling=True, scaling_method='standard'):
        """Prepare data for training (Encoding, Splitting, Scaling)."""
        if self.data is None:
            return False, "No data loaded."
        
        if target_col and target_col not in self.data.columns:
            return False, f"Target column '{target_col}' not found."

        self.target_column = target_col
        df = self.data.copy()

        # Separate Features and Target
        if target_col:
            X = df.drop(columns=[target_col])
            y = df[target_col]
        else:
            X = df
            y = None
            
        # Filter features if specified
        if feature_columns:
            # maintain order and validity
            valid_stats = [c for c in feature_columns if c in X.columns]
            if not valid_stats:
                 return False, "No valid feature columns selected."
            X = X[valid_stats]

        # Encoding Categorical Variables
        # For Features
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.encoders[col] = le
        
        # For Target (if categorical)
        if y is not None and (y.dtype == 'object' or y.dtype.name == 'category'):
            le_target = LabelEncoder()
            y = le_target.fit_transform(y.astype(str))
            self.encoders[target_col] = le_target

        # Train Test Split
        if y is not None:
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
        else:
            self.X_train, self.X_test = train_test_split(
                X, test_size=test_size, random_state=random_state
            )
            self.y_train, self.y_test = None, None

        # Scaling
        if use_scaling:
            if scaling_method == 'standard':
                self.scaler = StandardScaler()
            elif scaling_method == 'minmax':
                self.scaler = MinMaxScaler()
            
            self.X_train = pd.DataFrame(self.scaler.fit_transform(self.X_train), columns=X.columns)
            self.X_test = pd.DataFrame(self.scaler.transform(self.X_test), columns=X.columns)

        return True, "Data prepared successfully."

    def detect_outliers(self, method='isolation_forest', contamination=0.05, feature_columns=None):
        """
        Detects outliers in the loaded data.
        Returns a boolean mask (True = Inlier, False = Outlier) and the outlier scores.
        """
        if self.data is None:
            return None, None
            
        df_for_outlier = self.data.copy()
        if feature_columns:
             # Use only selected columns for detection
             valid_cols = [c for c in feature_columns if c in df_for_outlier.columns]
             if valid_cols:
                 df_for_outlier = df_for_outlier[valid_cols]
        
        # Select numeric columns only
        numeric_data = df_for_outlier.select_dtypes(include=[np.number]).dropna()
        
        if numeric_data.empty:
            return None, None
            
        if method == 'isolation_forest':
            iso = IsolationForest(contamination=contamination, random_state=42)
            # fit_predict returns 1 for inlier, -1 for outlier
            preds = iso.fit_predict(numeric_data)
            mask = preds == 1
            # scores: lower is more abnormal
            scores = iso.decision_function(numeric_data)
            
            # Align mask with original index if drops happened
            # (Though validation should happen on clean data usually)
            full_mask = pd.Series(True, index=self.data.index)
            full_mask.loc[numeric_data.index] = mask
            
            return full_mask, scores
            
        return None, None

    def remove_outliers(self, mask):
        """Removes data points where mask is False."""
        if self.data is not None and mask is not None:
            initial_count = len(self.data)
            self.data = self.data[mask]
            final_count = len(self.data)
            return True, f"Removed {initial_count - final_count} outliers."
        return False, "Failed to remove outliers."

    def get_group_cv_splitter(self, group_col):
        """Returns a generator for Leave-One-Group-Out CV if group_col exists."""
        if self.data is not None and group_col in self.data.columns:
            groups = self.data[group_col]
            logo = LeaveOneGroupOut()
            return logo.split(self.data, groups=groups)
        return None
