import os

import threading
from gevent import monkey
monkey.patch_all()
import queue
import builtins 
import time     
import traceback
import uuid
import json
from dataclasses import dataclass, field
from typing import Optional
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv
load_dotenv() 
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
dynamodb = None
table = None

if aws_access_key and aws_secret_key:
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=os.environ.get('AWS_REGION', 'us-east-1'),
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        table = dynamodb.Table('WesternSim')
        table.load()
        print("[SERVER] AWS DynamoDB connection initialized.")
    except Exception as e:
        print(f"[SERVER] Warning: AWS DynamoDB setup failed. Saving disabled. Error: {e}")
else:
    print("[SERVER] Warning: AWS credentials missing from environment. DynamoDB disabled.")

# --- Load Environment Variables ---


# --- Import Your Game Logic ---
from AI_Control_File import AI_Control, SessionEnded
from Western_Sim import Player 
import game_html 

# --- Global Game Objects ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key')
socketio = SocketIO(app, cors_allowed_origins="*")
@dataclass
class GameSession:
    session_id: str
    server_outbox: queue.Queue
    player_inbox: queue.Queue
    ai_file: AI_Control
    player_thread: Optional[threading.Thread] = None
    player_object: Optional[Player] = None
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    stop_requested: bool = False
    stop_reason: str = ""

sessions = {}
sessions_lock = threading.Lock()
SESSION_TIMEOUT_SECONDS = 120

thread_local = threading.local()
original_print = builtins.print
original_input = builtins.input

def thread_print(*args, **kwargs):
    handler = getattr(thread_local, "print_fn", None)
    if handler:
        return handler(*args, **kwargs)
    return original_print(*args, **kwargs)

def thread_input(prompt=""):
    handler = getattr(thread_local, "input_fn", None)
    if handler:
        return handler(prompt)
    return original_input(prompt)

builtins.print = thread_print
builtins.input = thread_input

def create_session():
    session_id = uuid.uuid4().hex
    server_outbox = queue.Queue()
    player_inbox = queue.Queue()
    ai_file = AI_Control(server_outbox, player_inbox)
    session = GameSession(
        session_id=session_id,
        server_outbox=server_outbox,
        player_inbox=player_inbox,
        ai_file=ai_file
    )
    with sessions_lock:
        sessions[session_id] = session
    return session

def get_session(session_id):
    if not session_id:
        return None
    with sessions_lock:
        session = sessions.get(session_id)
    if session:
        session.last_seen = time.time()
    return session

def request_session_stop(session, reason=""):
    if session.stop_requested:
        return
    session.stop_requested = True
    session.stop_reason = reason
    try:
        session.player_inbox.put({"_session_end": True})
    except Exception:
        pass
    try:
        session.server_outbox.put({
            "type": "game_message",
            "text": "Session ended. Refresh to start a new game."
        })
    except Exception:
        pass

def cleanup_sessions_loop():
    while True:
        time.sleep(10)
        now = time.time()
        with sessions_lock:
            session_ids = list(sessions.keys())
        for session_id in session_ids:
            with sessions_lock:
                session = sessions.get(session_id)
            if not session:
                continue
            if not session.stop_requested and (now - session.last_seen) > SESSION_TIMEOUT_SECONDS:
                request_session_stop(session, reason="timeout")
            if session.stop_requested and session.player_thread and not session.player_thread.is_alive():
                with sessions_lock:
                    sessions.pop(session_id, None)

cleanup_thread = threading.Thread(target=cleanup_sessions_loop, daemon=True)
cleanup_thread.start()

def start_session_game(session):
    if session.player_thread is not None and session.player_thread.is_alive():
        return
    session.player_thread = threading.Thread(target=run_game_loop, args=(session,))
    session.player_thread.start()

# --- The Main Game Loop Function ---
def run_game_loop(session):
    try:
        thread_local.print_fn = session.ai_file.print_to_client
        thread_local.input_fn = session.ai_file.patched_input
        
        # 1. Create the Player *inside the thread*
        session.player_object = Player(ai_file_arg=session.ai_file) 

        # 2. Set the AI flag
        # We import here to ensure we are modifying the module that Player uses
        import Western_Sim
        Western_Sim.USE_OLLAMA = session.ai_file.use_ai

        # 3. Run the game
        session.player_object.main_game_loop()
        
    except SessionEnded:
        pass
    except Exception as e:
        original_print(f"--- A CRITICAL ERROR OCCURRED ---")
        original_print(traceback.format_exc())
        
        # Send a fatal error to the client
        session.server_outbox.put({
            "type": "game_message",
            "text": f"--- A CRITICAL ERROR OCCURRED: {e} ---<br>The game must restart. Please refresh the page."
        })
    
    finally:
        thread_local.print_fn = None
        thread_local.input_fn = None
    
    if not session.stop_requested:
        session.server_outbox.put({"type": "game_over", "text": "--- GAME OVER ---<br>Refresh the page to play again."})

# --- Web Server Routes ---
@app.route('/')
def index():
    return render_template_string(game_html.HTML_CONTENT)

@socketio.on('start_game')
def handle_start_game():
    session = create_session()
    join_room(session.session_id) # Put the player in a private socket room
    start_session_game(session)
    
    # Start the message pump for this specific session
    socketio.start_background_task(message_pump, session)
    
    emit('game_started', {"session_id": session.session_id})

@socketio.on('send_response')
def handle_send_response(data):
    if not data: return
    session_id = data.get("session_id")
    choice = data.get("choice")
    
    session = get_session(session_id)
    if session and choice is not None:
        session.player_inbox.put(choice)

@app.route('/end_session', methods=['POST'])
def end_session():
    data = request.get_json(silent=True) or {}
    if not data and request.data:
        try:
            data = json.loads(request.data.decode("utf-8"))
        except Exception:
            data = {}
    session_id = data.get("session_id")
    session = get_session(session_id)
    if not session:
        return jsonify({"status": "Session not found."})
    request_session_stop(session, reason="client_closed")
    return jsonify({"status": "Session ended."})
@app.route('/save_game', methods=['POST'])
def save_game():
    global table
    data = request.json
    
    # Add this guard
    if not data:
        return jsonify({"status": "Error: Invalid request data."}), 400
        
    session_id = data.get("session_id")
    session = get_session(session_id)
    if not table or not session or not session.player_object:
        return jsonify({"status": "Error: Database not connected or game not running."})
    
    username = data.get("username", "default_player").strip()
    if not username: return jsonify({"status": "Error: Invalid name."})
    
    # 1. Get the raw data
    raw_data = session.player_object.to_dict()
    raw_data['username'] = username 
    
    # 2. HELPER FUNCTION: Convert all floats to Decimals recursively
    # DynamoDB crashes if it sees a float, so we must sanitize the data.
    def convert_floats_to_decimal(obj):
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats_to_decimal(i) for i in obj]
        return obj

    # 3. Apply the conversion
    final_save_data = convert_floats_to_decimal(raw_data)
    
    try:
        table.put_item(Item=final_save_data)
        return jsonify({"status": f"Game saved successfully for {username}!"})
    except ClientError as e:
        return jsonify({"status": f"Save failed: {e.response['Error']['Message']}"})
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj


@app.route('/load_game', methods=['POST'])
def load_game():
    global table
    if not table:
        return jsonify({"status": "Error: Database not connected."})
        
    data = request.json
    
    # Add this guard
    if not data:
        return jsonify({"status": "Error: Invalid request data."}), 400
        
    session_id = data.get("session_id")
    session = get_session(session_id)
    if not session:
        return jsonify({"status": "Error: Session not found. Start a new game first."})
    username = data.get("username", "default_player").strip()
    
    try:
        response = table.get_item(Key={'username': username})
        if 'Item' in response:
            # Start a new game thread if one isn't running
            if session.player_object is None:
                start_session_game(session)
                time.sleep(1.0) # Wait a second for the thread to create the object
            
            if session.player_object:
                session.player_object.load_from_dict(convert_decimals(response['Item']))
                # Force an update to the client
                session.ai_file.update_stats_display(session.player_object)
                while not session.player_inbox.empty():
                    try:
                        session.player_inbox.get_nowait()
                    except queue.Empty:
                        break
                
                # --- ADD THIS LINE TO BREAK THE GAME OUT OF ITS WAITING STATE ---
                session.player_inbox.put("_LOAD_GAME_")
                
                return jsonify({"status": f"Welcome back, {username}. Game loaded!"})
        else:
            return jsonify({"status": "No save file found for that name."})
    except ClientError as e:
        return jsonify({"status": f"Load failed: {e.response['Error']['Message']}"})

def message_pump(session):
    """Constantly checks the outbox and pushes messages to the client."""
    while not session.stop_requested:
        try:
            # Wait up to 1 second for a message
            msg = session.server_outbox.get(timeout=1)
            
            # Send the message directly to THIS specific player's room
            socketio.emit('game_update', msg, room=session.session_id)
            
            # If the game is asking for input, push a fresh stat update right before it
            if msg.get("type") in ["ask_for_choice", "ask_for_text"]:
                if session.player_object:
                    current_heat = getattr(session.player_object, 'Heat', 100)
                    max_heat = getattr(session.player_object, 'MaxHeat', 100)
                    stat_payload = {
                        'type': 'update_stats',
                        'payload': {
                            'health': session.player_object.Health,
                            'max_health': session.player_object.MaxHealth,
                            'heat': current_heat, 
                            'max_heat': max_heat,
                            'hunger': session.player_object.Hunger,
                            'gold': session.player_object.gold,
                            'day': session.player_object.Day,
                            'time': f"{session.player_object.Time}:00",
                            'location': session.player_object.current_town_name if session.player_object.invillage else "On the Trail",
                            'difficulty': session.player_object.difficulty.capitalize()
                        }
                    }
                    socketio.emit('game_update', stat_payload, room=session.session_id)

        except queue.Empty:
            continue # Nothing in the outbox, keep waiting
        except Exception as e:
            print(f"[Pump Error]: {e}")
            break


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting Flask-SocketIO server on http://0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
