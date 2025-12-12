import pandas as pd
import os

class FormatConverter:
    """
    A class to handle conversion of various data file formats to Parquet.
    """

    @staticmethod
    def convert_to_parquet(source_path, output_path=None):
        """
        Convert a CSV or Excel file to Parquet format.

        Args:
            source_path (str): Path to the source file.
            output_path (str, optional): Path to save the parquet file.
                                         If None, uses source filename with .parquet extension.

        Returns:
            tuple: (bool, str) - (Success status, Message or Error)
        """
        if not os.path.exists(source_path):
            return False, f"Source file not found: {source_path}"

        try:
            # Determine file type and read data
            if source_path.lower().endswith('.csv'):
                df = pd.read_csv(source_path)
            elif source_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(source_path)
            else:
                return False, "Unsupported source file format. Only CSV and Excel are supported."

            # Determine output path
            if output_path is None:
                base_name = os.path.splitext(source_path)[0]
                output_path = base_name + ".parquet"
            elif not output_path.lower().endswith('.parquet'):
                output_path += ".parquet"

            # Save as Parquet
            df.to_parquet(output_path, index=False)
            
            return True, f"Successfully converted to {output_path}"

        except Exception as e:
            return False, f"Conversion failed: {str(e)}"
