
import os
import logging
from typing import Dict, List, Optional, Any, Tuple

# Optional imports for mat2vec
try:
    from mat2vec.processing import MaterialsTextProcessor
    MAT2VEC_AVAILABLE = True
except ImportError:
    MAT2VEC_AVAILABLE = False
    MaterialsTextProcessor = None

try:
    from gensim.models import Word2Vec
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False

# ChemDataExtractor imports
try:
    from chemdataextractor import Document
    from chemdataextractor.model import Compound, MeltingPoint, Density
    from chemdataextractor.doc import Paragraph, Heading
    CDE_AVAILABLE = True
except ImportError:
    CDE_AVAILABLE = False

class LiteratureAnalyzer:
    def __init__(self, model_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        if MAT2VEC_AVAILABLE:
            self.processor = MaterialsTextProcessor()
        else:
            self.processor = None
            self.logger.warning("mat2vec not installed. Text normalization will be limited.")

        self.w2v_model = None
        if model_path and GENSIM_AVAILABLE:
            try:
                self.w2v_model = Word2Vec.load(model_path)
            except Exception as e:
                self.logger.error(f"Failed to load Word2Vec model from {model_path}: {e}")

    def normalize_text(self, text: str) -> str:
        """
        Normalizes text using mat2vec processor if available.
        """
        if self.processor:
            # mat2vec process returns (list_of_words, list_of_tuples)
            # We just want the normalized text for now or keep it as is?
            # actually process() returns a tuple.
            processed, _ = self.processor.process(text)
            return " ".join(processed)
        return text

    def extract_properties(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts material properties (Density, MeltingPoint) using ChemDataExtractor.
        """
        if not CDE_AVAILABLE:
            self.logger.error("ChemDataExtractor not available.")
            return []

        doc = Document(text)
        # We can add models to the document
        # doc.models = [Compound, Density] # This might be auto-detected or need configuration
        
        extracted_data = []
        
        # This is a simplified usage. CDE is complex.
        # We will iterate over records.
        for record in doc.records.serialize():
            extracted_data.append(record)
            
        return extracted_data

    def find_similar_materials(self, formula: str, topn: int = 5) -> List[Tuple[str, float]]:
        """
        Finds materials similar to the given formula using the loaded Word2Vec model.
        """
        if not self.w2v_model:
            return []
        
        normalized_formula = formula
        if self.processor:
            normalized_formula = self.processor.normalized_formula(formula)
            
        try:
            return self.w2v_model.wv.most_similar(normalized_formula, topn=topn)
        except KeyError:
            self.logger.warning(f"Word {normalized_formula} not in vocabulary.")
            return []

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of text.
        """
        raw_text = text
        normalized_text = self.normalize_text(text)
        properties = self.extract_properties(raw_text) # CDE works better on raw text usually
        
        return {
            "normalized_text": normalized_text,
            "extracted_properties": properties
        }
