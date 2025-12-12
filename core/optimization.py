import optuna
from sklearn.model_selection import cross_val_score
from .models import ModelFactory

class Optimizer:
    def __init__(self, X_train, y_train, task_type):
        self.X_train = X_train
        self.y_train = y_train
        self.task_type = task_type
        self.best_params = None
        self.best_model = None
        self.study = None

    def optimize(self, model_name, n_trials=20, progress_callback=None):
        
        def objective(trial):
            params = {}
            if model_name == 'Random Forest':
                params['n_estimators'] = trial.suggest_int('n_estimators', 10, 200)
                params['max_depth'] = trial.suggest_int('max_depth', 2, 32, log=True)
                params['min_samples_split'] = trial.suggest_int('min_samples_split', 2, 10)
                params['min_samples_leaf'] = trial.suggest_int('min_samples_leaf', 1, 10)
            elif model_name == 'XGBoost':
                params['n_estimators'] = trial.suggest_int('n_estimators', 50, 300)
                params['learning_rate'] = trial.suggest_float('learning_rate', 0.01, 0.3)
                params['max_depth'] = trial.suggest_int('max_depth', 3, 10)
                params['subsample'] = trial.suggest_float('subsample', 0.5, 1.0)
            elif model_name == 'SVC' or model_name == 'SVR':
                params['C'] = trial.suggest_float('C', 1e-3, 1e2, log=True)
                params['C'] = trial.suggest_float('C', 1e-3, 1e2, log=True)
                params['gamma'] = trial.suggest_categorical('gamma', ['scale', 'auto'])
            elif model_name == 'Stacking':
                # Tuning final estimator and passthrough
                final_est_name = trial.suggest_categorical('final_estimator', ['Ridge', 'Linear Regression', 'Random Forest'])
                params['final_estimator'] = final_est_name
                
                if final_est_name == 'Ridge':
                    params['final_estimator_alpha'] = trial.suggest_float('final_estimator_alpha', 0.1, 10.0, log=True)
                elif final_est_name == 'Random Forest':
                    params['final_estimator_n_estimators'] = trial.suggest_int('final_estimator_n_estimators', 10, 100)
                
                params['passthrough'] = trial.suggest_categorical('passthrough', [True, False])
            
            model = ModelFactory.get_model(self.task_type, model_name, params)
            
            # Using Cross Validation for robust evaluation
            if self.task_type == 'regression':
                score = cross_val_score(model, self.X_train, self.y_train, n_jobs=-1, cv=3, scoring='neg_mean_squared_error')
                return score.mean()
            else:
                score = cross_val_score(model, self.X_train, self.y_train, n_jobs=-1, cv=3, scoring='accuracy')
                return score.mean()

        direction = 'maximize' if self.task_type == 'classification' else 'maximize' # neg_mse is maximized (closer to 0)
        
        callbacks = []
        if progress_callback:
            def optuna_cb(study, trial):
                progress = len(study.trials) / n_trials
                progress_callback(min(progress, 1.0))
            callbacks.append(optuna_cb)

        self.study = optuna.create_study(direction=direction)
        self.study.optimize(objective, n_trials=n_trials, callbacks=callbacks)
        
        self.best_params = self.study.best_params
        return self.study.best_params
