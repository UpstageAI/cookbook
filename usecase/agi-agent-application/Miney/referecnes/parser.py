import os
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

class MultiPDFOCRProcessor:
    def __init__(self, api_key, max_workers=3):
        self.api_key = api_key
        self.api_url = "https://api.upstage.ai/v1/document-digitization"
        self.output_dir = Path("ocr_outputs")
        self.max_workers = max_workers
        self._setup_directories()

    def _setup_directories(self):
        """Create output directory structure"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _process_single_pdf(self, pdf_path):
        """Process individual PDF file using Upstage Document Parsing API"""
        try:
            with open(pdf_path, "rb") as f:
                files = {"document": f}
                data = {
                    "model": "document-parse",  # Use document parsing model
                    "ocr": "force",  # Force OCR processing
                    "base64_encoding": "['table']"  # Include table data in base64 format
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}

                response = requests.post(
                    self.api_url,
                    headers=headers,
                    files=files,
                    data=data
                )
                response.raise_for_status()

                result = response.json()
                output_data = self._format_output(pdf_path, result)
                output_path = self._save_output(pdf_path, output_data)
                
                return output_path

        except Exception as e:
            self._save_error(pdf_path, str(e))
            return None

    def _format_output(self, pdf_path, api_result):
        """Structure the document parsing results"""
        return {
            "metadata": {
                "document_name": Path(pdf_path).name,
                "processed_at": str(Path(pdf_path).stat().st_mtime),
                "status": "success"
            },
            "content": api_result  # Save the full API response for detailed parsing results
        }

    def _save_output(self, pdf_path, data):
        """Save successful document parsing results as JSON"""
        output_path = self.output_dir / f"{Path(pdf_path).stem}_parsed.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return output_path

    def _save_error(self, pdf_path, error):
        """Save error information as JSON"""
        error_path = self.output_dir / f"{Path(pdf_path).stem}_error.json"
        with open(error_path, "w", encoding="utf-8") as f:
            json.dump({
                "error": error,
                "document": Path(pdf_path).name,
                "timestamp": str(Path(pdf_path).stat().st_mtime)
            }, f, indent=2)

    def process_pdfs(self, pdf_paths):
        """
        Process multiple PDFs with parallel execution
        :param pdf_paths: List of PDF file paths
        :return: Dictionary of processing results
        """
        results = {"success": [], "errors": []}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._process_single_pdf, path): path for path in pdf_paths}
            
            for future in futures:
                path = futures[future]
                try:
                    result = future.result()
                    if result:
                        results["success"].append(result)
                    else:
                        results["errors"].append(str(path))
                except Exception as e:
                    results["errors"].append(f"{path}: {str(e)}")

        return results

    def get_all_results(self):
        """Retrieve all processed JSON files"""
        return list(self.output_dir.glob("*.json"))

if __name__ == "__main__":
    # Replace 'your_api_key_here' with your actual Upstage API key
    processor = MultiPDFOCRProcessor(api_key="up_t3QYrS83Q83MvEc78SoS84NEU47FF")
    
    # List of PDF files to process
    for i in range(10):
        pdf_file = ["./files/ih_"+str(i+1)+".pdf"]
    
        # Process the PDFs and print results summary
        processing_results = processor.process_pdfs(pdf_file)
        
        print(f"Processed {len(processing_results['success'])} files successfully")
        print(f"Encountered {len(processing_results['errors'])} errors")
        
        # List all generated JSON results
        all_results = processor.get_all_results()
        print("\nAvailable parsing results:")
        for result_file in all_results:
            print(f"- {result_file.name}")