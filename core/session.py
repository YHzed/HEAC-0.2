
import streamlit as st
from core.data_processor import DataProcessor
from core.analysis import Analyzer
from core.models import ModelTrainer
from core.dataset_manager import DatasetManager
from core.hea_cermet import MaterialProcessor
from core.model_manager import ModelManager
from core.activity_logger import ActivityLogger

def initialize_session_state():
    """Initializes the Streamlit session state with required objects if they don't exist."""
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    
    if 'analyzer' not in st.session_state:
        # Analyzer depends on data_processor
        st.session_state.analyzer = Analyzer(st.session_state.data_processor)
        
    if 'model_trainer' not in st.session_state:
        st.session_state.model_trainer = ModelTrainer()
        
    if 'trained_model' not in st.session_state:
        st.session_state.trained_model = None
        
    if 'model_metrics' not in st.session_state:
        st.session_state.model_metrics = None
        
    if 'language' not in st.session_state:
        st.session_state.language = '简体中文' # Default
        
    if 'dataset_manager' not in st.session_state:
        st.session_state.dataset_manager = DatasetManager()
        
    if 'material_processor' not in st.session_state:
        st.session_state.material_processor = MaterialProcessor()
        
    if 'model_manager' not in st.session_state:
        st.session_state.model_manager = ModelManager()
        
    if 'activity_logger' not in st.session_state:
        st.session_state.activity_logger = ActivityLogger()
