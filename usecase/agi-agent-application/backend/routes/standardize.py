from flask import Blueprint, request, jsonify
from services.extractor import extraction_and_mapping

standardize_bp = Blueprint('standardize', __name__)

@standardize_bp.route('/api/standardize', methods=['POST'])
def extract():
    try:
        data = request.get_json()
        print(data)
        clinical_note = data.get('note', '')

        if not clinical_note:
            return jsonify({"error": "No input note provided"}), 400

        df = extraction_and_mapping(clinical_note)
        return jsonify(df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
