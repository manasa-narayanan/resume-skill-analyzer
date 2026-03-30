from flask import Flask, request, jsonify, render_template_string
import os
import PyPDF2
import pdfplumber
import io

app = Flask(__name__)

# HTML Template with PDF Upload Support
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Resume Skill Analyzer - PDF Support</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: bold;
            color: #666;
        }
        .tab.active {
            color: #667eea;
            border-bottom: 3px solid #667eea;
        }
        .panel { display: none; }
        .panel.active { display: block; }
        
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #fafbfc;
        }
        .upload-area:hover { background: #f0f0f0; border-color: #5a67d8; }
        .upload-icon { font-size: 48px; margin-bottom: 10px; }
        
        textarea {
            width: 100%;
            height: 200px;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
        }
        textarea:focus { outline: none; border-color: #667eea; }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            margin-top: 15px;
            font-weight: bold;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .skill {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            margin: 5px;
            font-size: 13px;
        }
        .role-card {
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stats {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .stat {
            background: white;
            padding: 10px;
            text-align: center;
            flex: 1;
            border-radius: 8px;
            font-weight: bold;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        .file-info {
            margin-top: 10px;
            padding: 8px;
            background: #e8f0fe;
            border-radius: 5px;
            text-align: center;
            display: none;
        }
        .example-btn {
            background: #e0e0e0;
            color: #333;
            font-size: 12px;
            padding: 5px 10px;
            width: auto;
            display: inline-block;
            margin-right: 10px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>📄 Resume Skill Analyzer</h1>
            <p style="text-align: center;">Upload PDF or paste text to analyze skills</p>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('upload')">📁 Upload PDF</button>
                <button class="tab" onclick="switchTab('paste')">📝 Paste Text</button>
            </div>
            
            <!-- Upload Panel -->
            <div id="upload-panel" class="panel active">
                <div class="upload-area" id="dropZone">
                    <div class="upload-icon">📄</div>
                    <div>Drag & Drop PDF here</div>
                    <div style="font-size: 12px; margin-top: 5px;">or click to browse</div>
                    <input type="file" id="fileInput" accept=".pdf" style="display: none;">
                </div>
                <div id="fileInfo" class="file-info"></div>
                <button id="uploadAnalyzeBtn" onclick="analyzeFile()" disabled>Analyze PDF</button>
            </div>
            
            <!-- Paste Panel -->
            <div id="paste-panel" class="panel">
                <textarea id="resumeText" placeholder="Paste your resume text here..."></textarea>
                <div>
                    <button class="example-btn" onclick="loadExample()">📝 Load Example</button>
                    <button class="example-btn" onclick="clearText()">🗑️ Clear</button>
                </div>
                <button onclick="analyzeText()">🔍 Analyze Text</button>
            </div>
            
            <div id="result" class="result">
                <h3>📊 Analysis Results</h3>
                <div id="content"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            
            if (tab === 'upload') {
                document.querySelector('.tab:first-child').classList.add('active');
                document.getElementById('upload-panel').classList.add('active');
            } else {
                document.querySelector('.tab:last-child').classList.add('active');
                document.getElementById('paste-panel').classList.add('active');
            }
        }
        
        // File upload handling
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        let selectedFile = null;
        
        dropZone.onclick = () => fileInput.click();
        
        dropZone.ondragover = (e) => {
            e.preventDefault();
            dropZone.style.background = '#eef2ff';
        };
        
        dropZone.ondragleave = () => {
            dropZone.style.background = '#fafbfc';
        };
        
        dropZone.ondrop = (e) => {
            e.preventDefault();
            dropZone.style.background = '#fafbfc';
            const files = e.dataTransfer.files;
            if (files.length > 0) handleFile(files[0]);
        };
        
        fileInput.onchange = (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        };
        
        function handleFile(file) {
            if (file.type === 'application/pdf') {
                selectedFile = file;
                fileInfo.innerHTML = `✅ Selected: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
                fileInfo.style.display = 'block';
                document.getElementById('uploadAnalyzeBtn').disabled = false;
            } else {
                alert('Please upload a PDF file');
            }
        }
        
        function loadExample() {
            document.getElementById('resumeText').value = "Experienced Python developer with 5 years in machine learning, AWS cloud, and team leadership. Skilled in TensorFlow, PyTorch, SQL databases, and project management.";
        }
        
        function clearText() {
            document.getElementById('resumeText').value = '';
        }
        
        async function analyzeFile() {
            if (!selectedFile) return;
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            showLoading();
            const btn = document.getElementById('uploadAnalyzeBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Analyzing PDF...';
            
            try {
                const response = await fetch('/analyze_pdf', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showError(error.message);
            }
            
            btn.disabled = false;
            btn.textContent = 'Analyze PDF';
        }
        
        async function analyzeText() {
            const text = document.getElementById('resumeText').value;
            if (!text.trim()) {
                alert('Please paste some text or click "Load Example"');
                return;
            }
            
            showLoading();
            
            try {
                const response = await fetch('/analyze_text', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({resume_text: text})
                });
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                showError(error.message);
            }
        }
        
        function showLoading() {
            const resultDiv = document.getElementById('result');
            const contentDiv = document.getElementById('content');
            resultDiv.style.display = 'block';
            contentDiv.innerHTML = '<div class="loading">🔍 Analyzing your resume...</div>';
        }
        
        function showError(message) {
            const contentDiv = document.getElementById('content');
            contentDiv.innerHTML = `<p style="color: red;">❌ Error: ${message}</p>`;
        }
        
        function displayResults(data) {
            const contentDiv = document.getElementById('content');
            
            if (!data.success) {
                contentDiv.innerHTML = `<p style="color: red;">❌ Error: ${data.error}</p>`;
                return;
            }
            
            let html = '<h4>🔧 Skills Found (' + data.skill_count + '):</h4><div>';
            data.skills.forEach(skill => {
                html += `<span class="skill">${skill}</span>`;
            });
            html += '</div>';
            
            html += '<h4>💼 Suggested Career Paths:</h4>';
            data.roles.forEach(role => {
                html += `<div class="role-card">${role}</div>`;
            });
            
            html += `<h4>⭐ Resume Strength: ${data.strength}</h4>`;
            html += `<p>${data.message}</p>`;
            
            html += `<div class="stats">`;
            html += `<div class="stat">📝 Words: ${data.words}</div>`;
            html += `<div class="stat">🎯 Skills: ${data.skill_count}</div>`;
            html += `<div class="stat">⭐ Score: ${data.score}</div>`;
            html += `</div>`;
            
            contentDiv.innerHTML = html;
        }
    </script>
</body>
</html>
'''

def extract_text_from_pdf(file_data):
    """Extract text from PDF file"""
    text = ""
    
    # Try PyPDF2 first
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"PyPDF2 error: {e}")
    
    # If PyPDF2 didn't get enough text, try pdfplumber
    if len(text.strip()) < 100:
        try:
            with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber error: {e}")
    
    return text

def analyze_resume_text(text):
    """Analyze resume text and return results"""
    if len(text.strip()) < 30:
        return {"error": "Text too short", "success": False}
    
    text_lower = text.lower()
    
    # Skill detection
    skill_dict = {
        'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript',
        'sql': 'SQL', 'machine learning': 'Machine Learning',
        'aws': 'AWS', 'docker': 'Docker', 'react': 'React',
        'node.js': 'Node.js', 'leadership': 'Leadership',
        'communication': 'Communication', 'tensorflow': 'TensorFlow',
        'pytorch': 'PyTorch', 'git': 'Git', 'agile': 'Agile',
        'scrum': 'Scrum', 'mongodb': 'MongoDB', 'postgresql': 'PostgreSQL'
    }
    
    skills = []
    for key, name in skill_dict.items():
        if key in text_lower:
            skills.append(name)
    skills = list(dict.fromkeys(skills))
    
    # Role suggestions
    roles = []
    if any(w in text_lower for w in ['python', 'machine learning', 'tensorflow', 'pytorch']):
        roles.append('🤖 Data Scientist / Machine Learning Engineer')
    if any(w in text_lower for w in ['react', 'javascript', 'node.js', 'angular']):
        roles.append('💻 Frontend / Full Stack Developer')
    if any(w in text_lower for w in ['aws', 'docker', 'kubernetes', 'azure']):
        roles.append('☁️ Cloud Engineer / DevOps')
    if any(w in text_lower for w in ['sql', 'database', 'tableau', 'power bi']):
        roles.append('📊 Data Analyst / Business Intelligence')
    if any(w in text_lower for w in ['java', 'spring', 'c++', 'c#']):
        roles.append('⚙️ Backend Developer')
    
    if not roles:
        roles.append('💻 Software Developer')
    
    # Strength
    count = len(skills)
    if count >= 8:
        strength = "Excellent! 🌟"
        message = "Outstanding! Your resume shows exceptional skill diversity. You're highly competitive!"
    elif count >= 5:
        strength = "Strong! 👍"
        message = "Great skill set! You're well-prepared for job applications."
    elif count >= 3:
        strength = "Good 📈"
        message = "Good foundation. Add more in-demand skills to stand out."
    else:
        strength = "Needs Improvement 📝"
        message = "Add more technical skills. List programming languages, frameworks, and tools."
    
    return {
        "success": True,
        "skills": skills,
        "roles": roles,
        "skill_count": count,
        "score": min(100, count * 10),
        "strength": strength,
        "message": message,
        "words": len(text.split())
    }

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('resume_text', '')
        result = analyze_resume_text(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "success": False})

@app.route('/analyze_pdf', methods=['POST'])
def analyze_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded", "success": False})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected", "success": False})
        
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "Please upload a PDF file", "success": False})
        
        # Read PDF file
        file_data = file.read()
        text = extract_text_from_pdf(file_data)
        
        if not text or len(text.strip()) < 30:
            return jsonify({"error": "Could not extract text from PDF. Make sure it's not scanned/image-based.", "success": False})
        
        result = analyze_resume_text(text)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Resume Skill Analyzer with PDF Support")
    print("=" * 50)
    print("✅ Server running at: http://localhost:8080")
    print("📄 Upload PDF or paste text to analyze")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=True)