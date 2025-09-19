from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd

app = Flask(__name__)
CORS(app)
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

try:
    df = pd.read_csv('../../public/Artisans.csv')
    print(f"Successfully loaded {len(df)} records")
except Exception as e:
    print(f"Error loading CSV: {e}")
    df = pd.DataFrame()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400

        display_cols = ['name', 'craft_type', 'state', 'district', 'age', 'gender']
        context = f"Artisan Database Information:\n{df[display_cols].to_string()}\n\n"
        
        prompt = f"""Based on the following artisan database, please answer this question: {query}
        {context}
        Please provide a clear and concise answer based only on the data provided."""

        response = model.generate_content(prompt)
        print(f"Query: {query}")
        print(f"Response: {response.text}")
        
        return jsonify({
            'response': response.text,
            'status': 'success'
        })

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)