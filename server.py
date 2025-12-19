import os
import threading
import queue
import builtins 
import time     
from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv() 

# --- Import Your Game Logic ---
from AI_Control_File import AI_Control
from Western_Sim import Player 
import game_html 

# --- Global Game Objects ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-fallback-secret-key-12345')

# --- MULTIPLAYER SESSION REGISTRY ---
# Maps session_id -> dictionary containing queues and player object
sessions = {} 

# Maps thread_id -> AI_Control object
# This allows 'print' to know WHICH player to send text to based on the running thread
thread_registry = {}

# Save original built-ins before we patch them so the server can still log to console
original_print = builtins.print
original_input = builtins.input

# --- SMART PATCHING FUNCTIONS ---

def smart_print(*args, **kwargs):
    """
    Replaces builtins.print. 
    Checks which thread is calling it.
    If it's a game thread, send to that player's browser via their AI_Control.
    If it's the server (main thread), print to terminal.
    """
    current_thread_id = threading.get_ident()
    
    # Check if this thread belongs to a game session
    if current_thread_id in thread_registry:
        ai_controller = thread_registry[current_thread_id]
        message = " ".join(map(str, args))
        ai_controller.print_to_client(message)
    else:
        # Default to terminal for system/server messages
        original_print(*args, **kwargs)

def smart_input(prompt=""):
    """
    Replaces builtins.input.
    Finds the correct player AI controller for this thread and asks them for input.
    """
    current_thread_id = threading.get_ident()
    
    if current_thread_id in thread_registry:
        ai_controller = thread_registry[current_thread_id]
        # Use the existing AI logic to send the prompt and wait for a response
        return ai_controller.patched_input(prompt)
    else:
        # Default to terminal input (shouldn't happen in game context)
        return original_input(prompt)

# --- APPLY PATCHES GLOBALLY ---
builtins.print = smart_print
builtins.input = smart_input


# --- The Main Game Loop Function (Per Session) ---
def run_game_session(session_id, ai_file):
    """ 
    Wrapper to run the game in a unique thread for a specific session.
    """
    # 1. Register this thread ID so smart_print knows where to send text
    thread_id = threading.get_ident()
    thread_registry[thread_id] = ai_file
    
    try:
        # 2. Create the Player
        # Note: We do NOT set Western_Sim.USE_OLLAMA globally here because 
        # it might affect other threads. However, your Player class likely 
        # reads from ai_file.use_ai, which is thread-safe.
        player = Player(ai_file_arg=ai_file) 
        
        # 3. Save player object to session so /get_update can poll stats
        if session_id in sessions:
            sessions[session_id]['player'] = player

        # 4. Run the game logic
        player.main_game_loop()
        
    except Exception as e:
        original_print(f"[Error in Session {session_id}]: {e}")
        import traceback
        original_print(traceback.format_exc())
        
        ai_file.print_to_client(f"CRITICAL ERROR: {e}. Please refresh.")
    
    finally:
        # 5. Cleanup when game ends or crashes
        # Unregister the thread so memory is freed
        if thread_id in thread_registry:
            del thread_registry[thread_id]
        
        # We don't delete the session immediately from 'sessions' dict 
        # so the user can still see the Game Over message.
        ai_file.print_to_client("--- GAME OVER ---")


# --- Web Server Routes ---

@app.route('/')
def index():
    return render_template_string(game_html.HTML_CONTENT)

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400

    original_print(f"[SERVER] Starting game for Session: {session_id}")

    # Create queues specifically for THIS player
    server_outbox = queue.Queue()
    player_inbox = queue.Queue()
    
    # Create AI Controller for this session
    ai_file = AI_Control(server_outbox, player_inbox) 
    
    # Store everything in the global registry keyed by session_id
    sessions[session_id] = {
        'outbox': server_outbox,
        'inbox': player_inbox,
        'player': None, # Will be filled by the thread once it starts
        'ai': ai_file
    }

    # Start the dedicated thread for this player
    game_thread = threading.Thread(target=run_game_session, args=(session_id, ai_file))
    game_thread.start()
    
    return jsonify({"status": "Game started"})

@app.route('/get_update')
def get_update():
    # Browser sends session_id as a query parameter
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({"messages": []}) # No active session found

    session_data = sessions[session_id]
    outbox = session_data['outbox']
    player_object = session_data['player']
    
    messages = []
    
    # --- Proactive Stat Update (Specific to this Player) ---
    if player_object is not None:
        try:
            stat_payload = {
                'type': 'update_stats',
                'payload': {
                    'health': player_object.Health,
                    'max_health': player_object.MaxHealth,
                    # Safely get Heat stats (default to 100 if not set)
                    'heat': getattr(player_object, 'Heat', 100), 
                    'max_heat': getattr(player_object, 'MaxHeat', 100),
                    'hunger': player_object.Hunger,
                    'gold': player_object.gold,
                    'day': player_object.Day,
                    'time': f"{player_object.Time}:00",
                    'location': player_object.current_town_name if player_object.invillage else "On the Trail",
                    'difficulty': player_object.difficulty.capitalize()
                }
            }
            messages.append(stat_payload)
        except Exception:
            # If player object is in middle of init, just skip stats this tick
            pass

    # Drain specific user's outbox
    while not outbox.empty():
        msg = outbox.get()
        # Prevent duplicate stat updates if we just added one manually
        if msg.get("type") == "update_stats" and any(m.get("type") == "update_stats" for m in messages):
            continue
        messages.append(msg)
        # If we hit an input request, stop draining so the browser handles it
        if msg.get("type") in ["ask_for_choice", "ask_for_text"]:
            break
            
    return jsonify({"messages": messages})

@app.route('/send_response', methods=['POST'])
def send_response():
    data = request.json
    session_id = data.get('session_id')
    choice = data.get('choice')

    if session_id in sessions:
        # Put the answer in THAT specific player's inbox
        sessions[session_id]['inbox'].put(choice)
        return jsonify({"status": "Response received"})
    
    return jsonify({"error": "Session not found"}), 404

if __name__ == '__main__':
    print("Starting Multi-Session Flask server on http://localhost:5001")
    # Debug=False is safer for threads
    app.run(host="0.0.0.0", port=5001, debug=False)