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
from AI_Control_File import AI_Control
from Western_Sim import Player 
import game_html 

# --- Global Game Objects ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key')

server_outbox = queue.Queue()
player_inbox = queue.Queue()

ai_file = AI_Control(server_outbox, player_inbox) 
player_thread = None
player_object = None 

# --- The Main Game Loop Function ---
def run_game_loop(ai_file):
    global player_object
    
    # --- Store original built-in functions ---
    original_print = builtins.print
    original_input = builtins.input
    original_sleep = time.sleep

    try:
        # --- PATCH BUILT-IN FUNCTIONS ---
        builtins.print = ai_file.print_to_client
        builtins.input = ai_file.patched_input
        # We don't patch time.sleep globally to avoid breaking server timing, 
        # but the AI class has a reference if needed.
        
        # 1. Create the Player *inside the thread*
        player_object = Player(ai_file_arg=ai_file) 

        # 2. Set the AI flag
        # We import here to ensure we are modifying the module that Player uses
        import Western_Sim
        Western_Sim.USE_OLLAMA = ai_file.use_ai

        # 3. Run the game
        player_object.main_game_loop()
        
    except Exception as e:
        # Use the *original* print to log to the terminal
        original_print(f"--- A CRITICAL ERROR OCCURRED ---")
        original_print(traceback.format_exc())
        
        # Send a fatal error to the client
        server_outbox.put({
            "type": "game_message",
            "text": f"--- A CRITICAL ERROR OCCURRED: {e} ---<br>The game must restart. Please refresh the page."
        })
    
    finally:
        # --- CRITICAL: Restore original functions ---
        builtins.print = original_print
        builtins.input = original_input
        time.sleep = original_sleep
    
    server_outbox.put({"type": "game_over", "text": "--- GAME OVER ---<br>Refresh the page to play again."})

# --- Web Server Routes ---
@app.route('/')
def index():
    return render_template_string(game_html.HTML_CONTENT)

@app.route('/start_game', methods=['POST'])
def start_game():
    global player_thread, server_outbox, player_inbox, ai_file, player_object

    # 1. Log if an old thread is being orphaned
    if player_thread is not None and player_thread.is_alive():
        print("[SERVER] WARNING: Old game thread was still alive. It is now orphaned.")
            
    # 2. Create NEW queues for this new game session
    server_outbox = queue.Queue()
    player_inbox = queue.Queue()
    
    # 3. Create a NEW AI_Control object using the NEW queues
    ai_file = AI_Control(server_outbox, player_inbox) 
    
    # 4. Reset the player object reference
    player_object = None 

    # 5. Start the new game thread
    player_thread = threading.Thread(target=run_game_loop, args=(ai_file,))
    player_thread.start()
    return jsonify({"status": "Game started"})

@app.route('/get_update')
def get_update():
    messages = []
    
    # --- Proactive Stat Update ---
    if player_object is not None:
        try:
            # Use getattr to safely get values, defaulting to reasonable numbers if not set yet
            current_heat = getattr(player_object, 'Heat', 100)
            max_heat = getattr(player_object, 'MaxHeat', 100)
            
            stat_payload = {
                'type': 'update_stats',
                'payload': {
                    'health': player_object.Health,
                    'max_health': player_object.MaxHealth,
                    'heat': current_heat, 
                    'max_heat': max_heat,
                    'hunger': player_object.Hunger,
                    'gold': player_object.gold,
                    'day': player_object.Day,
                    'time': f"{player_object.Time}:00",
                    'location': player_object.current_town_name if player_object.invillage else "On the Trail",
                    'difficulty': player_object.difficulty.capitalize()
                }
            }
            messages.append(stat_payload)
        except Exception as e:
            print(f"[Stat Poll Error]: {e}")
    
    while not server_outbox.empty():
        msg = server_outbox.get()
        
        # Prevent duplicate stat messages to save bandwidth
        if msg.get("type") == "update_stats" and any(m.get("type") == "update_stats" for m in messages):
            continue
        
        messages.append(msg)
        if msg.get("type") in ["ask_for_choice", "ask_for_text"]:
            break
            
    return jsonify({"messages": messages})

@app.route('/send_response', methods=['POST'])
def send_response():
    data = request.json
    player_inbox.put(data['choice'])
    return jsonify({"status": "Response received"})

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)