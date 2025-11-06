import os
import threading
import queue
import builtins # Need this for patching
import time     # Need this for patching
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

server_outbox = queue.Queue()
player_inbox = queue.Queue()

ai_file = AI_Control(server_outbox, player_inbox) 
player_thread = None
player_object = None 

# --- The Main Game Loop Function ---
def run_game_loop(ai_file):
    """ 
    This function runs the actual game logic in a separate thread.
    It will start, run until it needs input, and then pause, waiting 
    for the player_inbox to have an item.
    """
    global player_object
    
    # --- Store original built-in functions ---
    original_print = builtins.print
    original_input = builtins.input
    original_sleep = time.sleep

    try:
        # --- PATCH BUILT-IN FUNCTIONS ---
        # All calls to 'print()' in the game thread will now go to the web.
        builtins.print = ai_file.print_to_client
        # All calls to 'input()' in the game thread will now ask the web.
        builtins.input = ai_file.patched_input
        # Speed up the game by patching 'time.sleep'
        
        # 1. Create the Player *inside the thread*
        player_object = Player(ai_file_arg=ai_file) 

        # 2. Set the AI flag
        import Western_Sim
        Western_Sim.USE_OLLAMA = ai_file.use_ai

        # 3. Run the game
        player_object.main_game_loop()
        
    except Exception as e:
        # Use the *original* print to log to the terminal
        original_print(f"--- A CRITICAL ERROR OCCURRED ---")
        import traceback
        original_print(traceback.format_exc())
        
        # Send a fatal error to the client
        server_outbox.put({
            "type": "game_message",
            "text": f"--- A CRITICAL ERROR OCCURRED: {e} ---<br>The game must restart. Please refresh the page."
        })
    
    finally:
        # --- CRITICAL: Restore original functions ---
        # This ensures that if the thread dies, the server
        # itself can still print to the terminal.
        builtins.print = original_print
        builtins.input = original_input
        time.sleep = original_sleep
    
    server_outbox.put({"type": "game_over", "text": "--- GAME OVER ---<br>Refresh the page to play again."})

# --- Web Server Routes ---
@app.route('/')
def index():
    """Serves the main HTML game page."""
    return render_template_string(game_html.HTML_CONTENT)

@app.route('/start_game', methods=['POST'])
def start_game():
    """
    Browser calls this *once* on page load to start the game thread.
    This function now RE-INITIALIZES the game every time.
    """
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

    # 5. Start the new game thread, passing it the NEW ai_file
    player_thread = threading.Thread(target=run_game_loop, args=(ai_file,))
    player_thread.start()
    return jsonify({"status": "Game started"})

@app.route('/get_update')
def get_update():
    """
    This is the "polling" endpoint. The browser calls this every second.
    It drains all pending messages from the outbox and sends them as a list.
    """
    messages = []
    
    # --- NEW: Proactive Stat Update ---
    # On every poll, check if the player object exists and send its current state.
    # This is non-blocking and doesn't lag the game thread.
    if player_object is not None:
        try:
            # Manually create a stat update message
            stat_payload = {
                'type': 'update_stats',
                'payload': {
                    'health': player_object.Health,
                    'max_health': player_object.MaxHealth,
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
            # This might fail if the player object is in a weird state during init
            # It's not critical, so we just log it and move on
            print(f"[Stat Poll Error]: {e}")
    # --- END NEW ---

    while not server_outbox.empty():
        msg = server_outbox.get()
        
        # --- MODIFICATION: Prevent duplicate stat messages ---
        # If we just added a stat update, and the queue also has one,
        # skip the one from the queue to avoid sending two.
        if msg.get("type") == "update_stats" and any(m.get("type") == "update_stats" for m in messages):
            continue
        # --- END MODIFICATION ---
        
        messages.append(msg)
        # If the message is a question, stop sending more messages.
        # This ensures the browser only gets one question at a time.
        if msg.get("type") in ["ask_for_choice", "ask_for_text"]:
            break
            
    return jsonify({"messages": messages})

@app.route('/send_response', methods=['POST'])
def send_response():
    """
    This is where the browser sends the player's answer (from a button click
    or text input) back to the server.
    """
    
    data = request.json
    player_inbox.put(data['choice']) # Put the answer in the inbox
    return jsonify({"status": "Response received"})

# --- Start The Server ---
if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5001")
    # We use a standard Flask server. No eventlet, no socketio.
    app.run(host="0.0.0.0", port=5001, debug=False)