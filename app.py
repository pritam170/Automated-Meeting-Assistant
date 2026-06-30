import os
import json
import werkzeug
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from analyzer import LocalAnalyzer
from transcriber import LocalTranscriber
from mailer import Mailer

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configuration files paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BACKEND_DIR, 'config.json')
TEAM_FILE = os.path.join(BACKEND_DIR, 'team.json')
UPLOAD_FOLDER = os.path.join(BACKEND_DIR, 'temp_uploads')

# Create temporary upload folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to read/write config
def read_json_file(file_path, default_data):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return default_data

def write_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Load / Save configurations and team
def get_config():
    default_config = {
        "smtp": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "",
            "password": "",
            "use_ssl": False,
            "use_tls": True,
            "sender_email": ""
        },
        "whisper_model": "tiny"
    }
    return read_json_file(CONFIG_FILE, default_config)

def get_team():
    default_team = [
        {"name": "Alice", "email": "alice@example.com", "role": "Product Manager"},
        {"name": "Bob", "email": "bob@example.com", "role": "Lead Engineer"},
        {"name": "Charlie", "email": "charlie@example.com", "role": "Frontend Designer"},
        {"name": "Dave", "email": "dave@example.com", "role": "Backend Developer"}
    ]
    return read_json_file(TEAM_FILE, default_team)


@app.route('/')
def index():
    # Serves the index.html from static folder
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'GET':
        cfg = get_config()
        # Hide password in response for security
        cfg_copy = json.loads(json.dumps(cfg))
        if cfg_copy["smtp"]["password"]:
            cfg_copy["smtp"]["password"] = "••••••••••••"
        return jsonify(cfg_copy)
    
    else:
        new_cfg = request.json
        current_cfg = get_config()
        
        # If password is sent as mask, preserve old password
        if new_cfg.get("smtp", {}).get("password") == "••••••••••••":
            new_cfg["smtp"]["password"] = current_cfg["smtp"]["password"]
            
        write_json_file(CONFIG_FILE, new_cfg)
        return jsonify({"status": "success", "message": "Configuration saved!"})


@app.route('/api/smtp/test', methods=['POST'])
def test_smtp():
    data = request.json
    smtp_data = data.get("smtp", {})
    current_cfg = get_config()
    
    # Resolve password if masked
    pwd = smtp_data.get("password")
    if pwd == "••••••••••••":
        pwd = current_cfg["smtp"]["password"]
        
    success, msg = Mailer.test_connection(
        host=smtp_data.get("host"),
        port=int(smtp_data.get("port", 587)),
        username=smtp_data.get("username"),
        password=pwd,
        use_ssl=smtp_data.get("use_ssl", False),
        use_tls=smtp_data.get("use_tls", True)
    )
    
    if success:
        return jsonify({"status": "success", "message": msg})
    else:
        return jsonify({"status": "error", "message": msg}), 400


@app.route('/api/team', methods=['GET', 'POST'])
def handle_team():
    if request.method == 'GET':
        return jsonify(get_team())
    else:
        new_team = request.json
        write_json_file(TEAM_FILE, new_team)
        return jsonify({"status": "success", "message": "Team directory updated!"})


@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get("text", "")
    num_summary_sentences = int(data.get("summary_sentences", 4))
    
    team = get_team()
    team_names = [member["name"] for member in team]
    
    analyzer = LocalAnalyzer(team_members=team_names)
    
    summary = analyzer.summarize_extractive(text, num_sentences=num_summary_sentences)
    action_items = analyzer.extract_action_items(text)
    
    return jsonify({
        "summary": summary,
        "action_items": action_items
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    config = get_config()
    model_name = config.get("whisper_model", "tiny")
    
    try:
        # Transcribe audio file using local Whisper (or fallback)
        transcriber = LocalTranscriber(model_name=model_name)
        transcript = transcriber.transcribe(file_path)
        
        # Analyze transcription
        team = get_team()
        team_names = [member["name"] for member in team]
        analyzer = LocalAnalyzer(team_members=team_names)
        
        summary = analyzer.summarize_extractive(transcript, num_sentences=4)
        action_items = analyzer.extract_action_items(transcript)
        
        # Clean up temporary uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return jsonify({
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items
        })
        
    except Exception as e:
        # Clean up file in case of error
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    data = request.json
    meeting_title = data.get("meeting_title", "Meeting Action Items")
    meeting_summary = data.get("meeting_summary", "")
    tasks = data.get("tasks", [])
    
    if not tasks:
        return jsonify({"status": "error", "message": "No action items provided"}), 400
        
    config = get_config()
    smtp_config = config.get("smtp", {})
    
    if not smtp_config.get("host") or not smtp_config.get("username"):
        return jsonify({"status": "error", "message": "SMTP is not configured in settings"}), 400
        
    team = get_team()
    # Create name to email lookup mapping
    team_emails = {member["name"].lower(): member["email"] for member in team}
    
    # Group tasks by assignee
    grouped_tasks = {}
    for task in tasks:
        assignee = task.get("assignee", "Unassigned").lower()
        if assignee not in grouped_tasks:
            grouped_tasks[assignee] = []
        grouped_tasks[assignee].append(task)
        
    sent_details = []
    
    for assignee, user_tasks in grouped_tasks.items():
        if assignee == "unassigned":
            continue
            
        # Get assignee email
        recipient_email = team_emails.get(assignee)
        # Try finding key in names if exact match lower didn't match (partial match)
        if not recipient_email:
            for member in team:
                if member["name"].lower() in assignee or assignee in member["name"].lower():
                    recipient_email = member["email"]
                    assignee = member["name"].lower()
                    break
                    
        if not recipient_email:
            sent_details.append({
                "assignee": assignee.capitalize(),
                "status": "failed",
                "message": "Email address not found in Team Directory"
            })
            continue
            
        # Capitalize recipient name
        recipient_name = next((member["name"] for member in team if member["name"].lower() == assignee), assignee.capitalize())
        
        try:
            Mailer.send_task_email(
                smtp_config=smtp_config,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                meeting_title=meeting_title,
                meeting_summary=meeting_summary,
                all_tasks=tasks,
                recipient_tasks=user_tasks
            )
            sent_details.append({
                "assignee": recipient_name,
                "email": recipient_email,
                "status": "success"
            })
        except Exception as e:
            sent_details.append({
                "assignee": recipient_name,
                "email": recipient_email,
                "status": "failed",
                "message": str(e)
            })
            
    return jsonify({
        "status": "completed",
        "results": sent_details
    })

if __name__ == '__main__':
    # Default Flask local execution
    app.run(host='127.0.0.1', port=5000, debug=True)
