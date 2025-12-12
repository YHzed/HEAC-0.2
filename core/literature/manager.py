
import os
import json
import logging
from typing import Dict, List, Any
from .pdf_reader import extract_text_from_pdf
from .analyzer import LiteratureAnalyzer
from ..material_database import db

class LibraryManager:
    def __init__(self, data_file: str = "extracted_data.json"):
        self.analyzer = LiteratureAnalyzer()
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(current_dir, 'data', data_file)
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.extracted_data = json.load(f)
        else:
            self.extracted_data = []

    def save_data(self):
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, indent=4)

    def process_file(self, filepath: str) -> Dict[str, Any]:
        """
        Process a single file (PDF or Text).
        """
        if filepath.lower().endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        
        analysis_result = self.analyzer.analyze_text(text)
        
        # Prepare a record
        record = {
            "source": os.path.basename(filepath),
            "text_preview": text[:200],
            "analysis": analysis_result,
            "status": "pending" # pending user approval
        }
        
        return record

    def add_to_library(self, record: Dict[str, Any]):
        """
        Adds a validated record to the local extracted database.
        """
        self.extracted_data.append(record)
        self.save_data()
        
    def get_pending_records(self) -> List[Dict[str, Any]]:
        return [r for r in self.extracted_data if r.get('status') == 'pending']

    def approve_record(self, index: int):
        """
        Approves a record and potentially updates the main material database 
        (Implementation of main DB update depends on DB structure).
        """
        if 0 <= index < len(self.extracted_data):
            self.extracted_data[index]['status'] = 'approved'
            self.save_data()
            # TODO: Logic to update core/data/enthalpy.json or compounds.json
            # This requires parsing the specific CDE output structure to get clear Property: Value pairs.
