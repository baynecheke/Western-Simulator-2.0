import os
import threading
import queue
import builtins 
import time     
import traceback
from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv() 

# --- Import Your Game Logic ---
# Ensure these files are in the same directory
from AI_Control_File import AI_Control
from Western_Sim import Player 
import game_html 

# --- Global Server Objects ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key')

# --- REGISTRIES ---
# sessions: Maps session_id (str) -> { 'outbox': Queue, 'inbox': Queue, 'player': PlayerObj }
sessions = {} 

# thread_registry: Maps thread_id (int) -> AI_Control object
# This allows 'print' to know WHICH player to send text to based on the running thread.
thread_registry = {}

# Save original built-ins immediately so we can use them for server logs
original_print = builtins.print
original_input = builtins.input

# --- SMART PATCHING FUNCTIONS ---

def smart_print(*args, **kwargs):
    """
    Replaces builtins.print. 
    1. Gets the current thread ID.
    2. Checks if that thread belongs to a player (in thread_registry).
    3. If yes, routes the text to that player's browser.
    4. If no (it's the server), prints to the system terminal.
    """
    current_thread_id = threading.get_ident()
    
    if current_thread_id in thread_registry:
        ai_controller = thread_registry[current_thread_id]
        # Convert all args to a single string, similar to how print works
        message = " ".join(map(str, args))
        ai_controller.print_to_client(message)
    else:
        # It's a server log, use the real terminal
        original_print(*args, **kwargs)

def smart_input(prompt=""):
    """
    Replaces builtins.input.
    1. Gets the current thread ID.
    2. Finds the correct AI Controller.
    3. Asks that specific browser for input.
    """
    current_thread_id = threading.get_ident()
    
    if current_thread_id in thread_registry:
        ai_controller = thread_registry[current_thread_id]
        return ai_controller.patched_input(prompt)
    else:
        # Fallback for server-side inputs (rarely used)
        return original_input(prompt)

# --- APPLY PATCHES GLOBALLY ---
# This affects ALL modules imported after this point
builtins.print = smart_print
builtins.input = smart_input


# --- GAME THREAD WORKER ---
def run_game_session(session_id, ai_file):
    """ 
    This function runs inside a unique thread for EACH player.
    """
    thread_id = threading.get_ident()
    
    # 1. Register thread so smart_print finds us
    thread_registry[thread_id] = ai_file
    
    try:
        # 2. Initialize Player
        # We pass the ai_file directly so the player object interacts with THIS session
        player = Player(ai_file_arg=ai_file) 
        
        # 3. Store player object for stat polling
        if session_id in sessions:
            sessions[session_id]['player'] = player

        # 4. Run the Game Loop
        player.main_game_loop()
        
    except Exception as e:
        # Log to server console
        original_print(f"[Session {session_id} Error]: {e}")
        original_print(traceback.format_exc())
        # Tell the user
        ai_file.print_to_client(f"<span style='color:red'>CRITICAL ERROR: {e}</span>")
    
    finally:
        # 5. Cleanup
        if thread_id in thread_registry:
            del thread_registry[thread_id]
        
        ai_file.print_to_client("--- GAME OVER ---")


# --- FLASK ROUTES ---

@app.route('/')
def index():
    return render_template_string(game_html.HTML_CONTENT)

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "No session ID"}), 400

    original_print(f"[SERVER] New Game Request from: {session_id}")

    # 1. Create dedicated queues
    server_outbox = queue.Queue()
    player_inbox = queue.Queue()
    
    # 2. Create dedicated AI Controller
    ai_file = AI_Control(server_outbox, player_inbox) 
    
    # 3. Register Session
    sessions[session_id] = {
        'outbox': server_outbox,
        'inbox': player_inbox,
        'player': None, 
        'ai': ai_file
    }

    # 4. Launch Thread
    game_thread = threading.Thread(target=run_game_session, args=(session_id, ai_file))
    game_thread.daemon = True # Kills thread if server stops
    game_thread.start()
    
    return jsonify({"status": "Game started"})

@app.route('/get_update')
def get_update():
    # Retrieve the unique ID associated with the browser tab
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({"messages": []}) 

    session_data = sessions[session_id]
    outbox = session_data['outbox']
    player_object = session_data['player']
    
    messages = []
    
    # --- Stat Payload (Safe Lookup) ---
    if player_object:
        try:
            stat_payload = {
                'type': 'update_stats',
                'payload': {
                    'health': getattr(player_object, 'Health', 100),
                    'max_health': getattr(player_object, 'MaxHealth', 100),
                    'heat': getattr(player_object, 'Heat', 100),       # Winter Stat
                    'max_heat': getattr(player_object, 'MaxHeat', 100),
                    'hunger': getattr(player_object, 'Hunger', 0),
                    'gold': getattr(player_object, 'gold', 0),
                    'day': getattr(player_object, 'Day', 1),
                    'time': f"{getattr(player_object, 'Time', 9)}:00",
                    'location': player_object.current_town_name if getattr(player_object, 'invillage', True) else "On the Trail",
                    'difficulty': getattr(player_object, 'difficulty', 'frontier').capitalize()
                }
            }
            messages.append(stat_payload)
        except Exception as e:
            original_print(f"Stat Error: {e}")

    # --- Drain Message Queue ---
    while not outbox.empty():
        msg = outbox.get()
        # Filter duplicates for cleaner UI
        if msg.get("type") == "update_stats" and any(m.get("type") == "update_stats" for m in messages):
            continue
        messages.append(msg)
        # Don't buffer too many questions at once
        if msg.get("type") in ["ask_for_choice", "ask_for_text"]:
            break
            
    return jsonify({"messages": messages})

@app.route('/send_response', methods=['POST'])
def send_response():
    data = request.json
    session_id = data.get('session_id')
    choice = data.get('choice')

    if session_id in sessions:
        # Drop the answer into the specific player's inbox
        sessions[session_id]['inbox'].put(choice)
        return jsonify({"status": "OK"})
    
    return jsonify({"error": "Session invalid"}), 404

if __name__ == '__main__':
    original_print(">>> Multiplayer Server Active on http://localhost:5001 <<<")
    app.run(host="0.0.0.0", port=5001, debug=False)