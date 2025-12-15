from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.svm import SVR, SVC
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, StackingRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report, confusion_matrix, silhouette_score

class ModelFactory:
    @staticmethod
    def get_model(task_type, model_name, params=None):
        """
        Factory method to get a model instance.
        task_type: 'regression', 'classification', or 'clustering'
        model_name: Name of the model (e.g., 'Linear Regression')
        params: Dictionary of hyperparameters
        """
        if params is None:
            params = {}

        if task_type == 'regression':
            if model_name == 'Linear Regression':
                return LinearRegression(**params)
            elif model_name == 'Ridge':
                return Ridge(**params)
            elif model_name == 'Lasso':
                return Lasso(**params)
            elif model_name == 'SVR':
                return SVR(**params)
            elif model_name == 'Decision Tree':
                return DecisionTreeRegressor(**params)
            elif model_name == 'Random Forest':
                return RandomForestRegressor(**params)
            elif model_name == 'XGBoost':
                try:
                    from xgboost import XGBRegressor
                    return XGBRegressor(**params)
                except ImportError:
                    raise ImportError("XGBoost is not installed. Please install it to use this model.")
            elif model_name == 'LightGBM':
                try:
                    from lightgbm import LGBMRegressor
                    return LGBMRegressor(**params)
                except ImportError:
                    raise ImportError("LightGBM is not installed. Please install it to use this model.")
            elif model_name == 'CatBoost':
                try:
                    from catboost import CatBoostRegressor
                    return CatBoostRegressor(verbose=0, **params)
                except ImportError:
                    raise ImportError("CatBoost is not installed. Please install it to use this model.")
            elif model_name == 'Stacking':
                # Default Stacking Configuration for HEA Cermets
                # Base: XGB, RF, SVR, Ridge
                # Meta: Ridge
                estimators = [
                    ('rf', RandomForestRegressor(n_estimators=100, random_state=42)),
                    ('svr', SVR(kernel='rbf')),
                    ('ridge', Ridge()),
                ]
                
                # Add XGBoost if available
                try:
                    from xgboost import XGBRegressor
                    estimators.append(('xgb', XGBRegressor(n_estimators=100, random_state=42, verbosity=0)))
                except ImportError:
                    pass
                    
                # Setup Stacking
                # Note: StackingRegressor takes 'estimators' and 'final_estimator'.
                
                # Handle final_estimator if it's a string (from optimization or UI)
                final_est_param = params.pop('final_estimator', 'Ridge')
                
                if isinstance(final_est_param, str):
                    if final_est_param == 'Ridge':
                        # Extract Ridge params if any, otherwise default
                        alpha = params.pop('final_estimator_alpha', 1.0) 
                        final_est = Ridge(alpha=alpha)
                    elif final_est_param == 'Linear Regression':
                        final_est = LinearRegression()
                    elif final_est_param == 'Random Forest':
                        n_est = params.pop('final_estimator_n_estimators', 100)
                        final_est = RandomForestRegressor(n_estimators=n_est, random_state=42)
                    else:
                        final_est = Ridge() # Default fallback
                else:
                    final_est = final_est_param
                
                return StackingRegressor(estimators=estimators, final_estimator=final_est, **params)
        
        elif task_type == 'classification':
            if model_name == 'Logistic Regression':
                return LogisticRegression(**params)
            elif model_name == 'SVC':
                return SVC(**params)
            elif model_name == 'Decision Tree':
                return DecisionTreeClassifier(**params)
            elif model_name == 'Random Forest':
                return RandomForestClassifier(**params)
            elif model_name == 'XGBoost':
                try:
                    from xgboost import XGBClassifier
                    return XGBClassifier(**params)
                except ImportError:
                    raise ImportError("XGBoost is not installed. Please install it to use this model.")
            elif model_name == 'LightGBM':
                try:
                    from lightgbm import LGBMClassifier
                    return LGBMClassifier(**params)
                except ImportError:
                    raise ImportError("LightGBM is not installed. Please install it to use this model.")
            elif model_name == 'CatBoost':
                try:
                    from catboost import CatBoostClassifier
                    return CatBoostClassifier(verbose=0, **params)
                except ImportError:
                    raise ImportError("CatBoost is not installed. Please install it to use this model.")

        elif task_type == 'clustering':
            if model_name == 'K-Means':
                return KMeans(**params)
        
        raise ValueError(f"Unknown model: {model_name} for task {task_type}")

class ModelTrainer:
    def __init__(self):
        self.model = None
        self.metrics = {}

    def train(self, model, X_train, y_train):
        self.model = model
        self.model.fit(X_train, y_train)

    def evaluate(self, X_test, y_test, task_type):
        if self.model is None:
            return None
        
        y_pred = self.model.predict(X_test)
        
        if task_type == 'regression':
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            self.metrics = {'MSE': mse, 'R2 Score': r2}
            return self.metrics, y_pred
            
        elif task_type == 'classification':
            acc = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            cm = confusion_matrix(y_test, y_pred)
            self.metrics = {'Accuracy': acc, 'Report': report, 'Confusion Matrix': cm}
            return self.metrics, y_pred

        elif task_type == 'clustering':
            # For clustering, y_test might be None or ignored if unsupervised, 
            # but we usually evaluate on the same set we predicted or a held-out set.
            # Here we assume X_test is what we predicted on.
            if len(set(y_pred)) > 1:
                sil = silhouette_score(X_test, y_pred)
            else:
                sil = -1 # Invalid silhouette for single cluster
            self.metrics = {'Silhouette Score': sil}
            return self.metrics, y_pred
