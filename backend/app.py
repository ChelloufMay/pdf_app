import os              
from flask import Flask, jsonify, request, send_from_directory  
from sqlalchemy import create_engine, text
from dotenv import load_dotenv 
from werkzeug.utils import secure_filename

print(">>> app.py is executing")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 1) Load environment variables from the .env file into os.environ
load_dotenv()                                     

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 2) Initialize Flask application
app = Flask(__name__)                             # __name__ tells Flask where to look for templates/static files

# 3) Configure upload folder and max request size
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')  
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH'))

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 4) Build database connection URI from environment variables
user = os.getenv('MYSQL_USER') 
pwd  = os.getenv('MYSQL_PASS') 
host = os.getenv('MYSQL_HOST') 
db   = os.getenv('MYSQL_DB')  
uri  = f"mysql+pymysql://{user}:{pwd}@{host}/{db}"# Full SQLAlchemy URI string
engine = create_engine(uri)                       # Create a connection pool / engine

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 5) Health-check endpoint — confirms the app is running
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok'})              

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 6) DB-test endpoint — verifies DB connectivity and table presence
@app.route('/db_test', methods=['GET'])
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) AS cnt FROM pdf_files"))
        row = result.fetchone()
        # row could be None (no rows) — default to 0
        cnt = row[0] if row is not None else 0
    return jsonify({'pdf_files_count': int(cnt)})     # Return JSON 

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 7) File-upload endpoint — accepts a PDF and stores metadata in the DB
@app.route('/upload', methods=['POST'])
def upload_pdf():
    file = request.files.get('file')              # Pull the file object from the form-data key 'file'
    if not file:
        return jsonify({'error': 'No file provided'}), 400  # 400 Bad Request if missing

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDFs allowed'}), 400 # Reject non-PDF uploads

    fn = secure_filename(file.filename)            # Sanitize the filename (prevent ../ etc.)

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], fn)  # Build the full path to save the file

    file.save(save_path)                           # Write the file to disk

    size_kb = os.path.getsize(save_path) // 1024   # Compute file size in KB

    # Insert file metadata into the database
    with engine.connect() as conn:
        stmt = text(
            "INSERT INTO pdf_files (filename, url, size_kb) "
            "VALUES (:fn, :url, :sz)"
        )# Prepare parameterized SQL

        conn.execute(stmt, {
            'fn': fn,
            'url': f'/files/{fn}',
            'sz': size_kb
        })# Execute with actual values

    return jsonify({'message': 'Uploaded', 'filename': fn}), 201  # 201 Created response

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 8) List-files endpoint — returns all uploaded PDFs (most recent first)
@app.route('/list', methods=['GET'])
def list_files():
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT filename, url, size_kb, upload_time "
            "FROM pdf_files ORDER BY upload_time DESC"
        )).fetchall() # Fetch all rows into a list
    files = [dict(r) for r in rows] # Convert each row to a Python dict
    return jsonify(files) # Return JSON array of file metadata

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 9) Serve-file endpoint — streams the PDF back to the client
@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], filename
    )  # Look in UPLOAD_FOLDER and send that file

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────>:(
# 10) Run the app if this file is executed directly
if __name__ == '__main__':
    print(">>> reaching app.run()")
    app.run(host='0.0.0.0', port=5000, debug=True)


