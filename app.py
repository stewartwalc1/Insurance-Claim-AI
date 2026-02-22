import os
import boto3
import json
from flask import Flask, render_template, request
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from bedrock_logic import ClaimProcessor
from pypdf import PdfReader
from concurrent.futures import ThreadPoolExecutor
import io


processor = ClaimProcessor()

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

s3_client = boto3.client('s3')

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'claim_pdf' not in request.files:
        return "No file uploaded"

    file = request.files['claim_pdf']
    if file.filename == '':
        return "No file selected"

    if file:
        filename = secure_filename(file.filename)
        folder = os.getenv('S3_FOLDER', 'claims')
        s3_key = f"{folder}/{filename}"

        file_bytes = file.read()
        file_buffer = io.BytesIO(file_bytes)
        
        reader = PdfReader(file_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        file_buffer.seek(0)
 
        with ThreadPoolExecutor() as executor:
            upload_task = executor.submit(s3_client.upload_fileobj, file_buffer, BUCKET_NAME, s3_key)
            extract_task = executor.submit(processor.extract_info, text)

            upload_task.result() 
            raw_json = extract_task.result()

            if "Content blocked" in raw_json:
                return render_template('results.html', 
                           summary="SENSITIVE DATA ALERT: This document contains prohibited PII (Social Security Numbers or private info).", 
                           data={}, 
                           decision="BLOCKED BY SECURITY POLICY",
                           flagged=True)

        print(f"DEBUG: Raw AI Response: {raw_json}")


        try:
    
            clean_str = raw_json.replace("```json", "").replace("```", "").strip()
            start = clean_str.find('{')
            end = clean_str.rfind('}') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")
                
            json_snippet = clean_str[start:end]
            extracted_data = json.loads(json_snippet)

            cause = extracted_data.get('incident', {}).get('cause_of_loss', '').strip().lower()

            if "flood" in cause:
                # Stop the chain here and return the flagged template
                return render_template('results.html', 
                                       summary="Automated processing is disabled for flood-related events. This claim has been routed for manual adjustment.", 
                                       data=json.dumps(extracted_data, indent=4), 
                                       decision="MANUAL REVIEW REQUIRED (FLOOD)",
                                       flagged=True)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Parsing Error: {e}")
            return f"Error parsing AI JSON output. Raw response was: {raw_json}"

        policy_facts = processor.retrieve_policy(raw_json)
        decision = processor.analyze_coverage(raw_json, policy_facts)
        final_summary = processor.generate_summary(decision)

        return render_template('results.html', 
                               summary=final_summary, 
                               data=raw_json, 
                               decision=decision,
                               flagged=False)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)