import os
import threading
import builtins
from flask import Flask, render_template_string
from flask_socketio import SocketIO
from dotenv import load_dotenv

# --- Load Environment Variables ---
# This loads your GROQ_API_KEY from the .env file
load_dotenv() 

# --- Import Your Game Logic ---
from AI_Control_File import AI_Control
from Western_Sim import Player 
from store import ShopItem, ShopSession
import game_html # This is our new HTML file

# --- Global Game Objects ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-fallback-secret-key-12345')
socketio = SocketIO(app)

# --- Thread-Safe Communication ---
input_event = threading.Event()
player_response = None

def get_player_response_from_global():
    """A function to safely get the response."""
    global player_response
    return player_response

# --- Instantiate Game Objects ---
# 1. Create the AI Controller Bridge
ai_file = AI_Control(socketio, input_event, get_player_response_from_global) 

# 2. Create the Player and "inject" the ai_file
# --- THIS IS THE FIX ---
player = Player(ai_file_arg=ai_file) 
# --- END OF FIX ---

# --- MONKEY-PATCH 'print()' ---
builtins.print = ai_file.print_to_client
# ---

# --- Web Server Routes ---
@app.route('/')
def index():
    """Serves the main HTML game page."""
    return render_template_string(game_html.HTML_CONTENT)

# --- Socket.IO Event Handlers (The "Waiter") ---
@socketio.on('connect')
def handle_connect():
    """A new player connected. Start the game loop in a new thread."""
    socketio.emit('game_message', {'text': 'Client connected!'})
    
    # This check prevents the game from restarting on a simple refresh
    if player.Health > 0 and player.Day == 1 and player.Time == 9:
         threading.Thread(target=run_game_loop).start()

@socketio.on('player_response')
def handle_player_response(data):
    """ We received an answer from the web client. """
    global player_response, input_event
    player_response = data['choice']
    input_event.set() # Wake up the game thread

@socketio.on('request_save')
def handle_request_save():
    """ Browser is asking to save. (Not fully implemented) """
    print("Save request received... (logic not fully implemented)")

@socketio.on('load_game')
def handle_load_game(data):
    """ Browser is sending us a save file to load. (Not fully implemented) """
    print("Load request received... (logic not fully implemented)")
    # Here you would parse data['save_data']
    # and use it to set up the player object
    # player.load_from_json_string(data['save_data'])


# --- The Main Game Loop Function ---
def run_game_loop():
    """ This function runs the actual game logic in a separate thread. """
    try:
        # This global variable is set at the top of Western_Sim.py
        # We must update it here so the game knows to use AI
        import Western_Sim
        Western_Sim.USE_OLLAMA = ai_file.use_ai # Use Groq status
        
        # Now, call the main loop on our *global* player object
        player.main_game_loop() 
        
    except Exception as e:
        # Send a fatal error to the client
        print(f"--- A CRITICAL ERROR OCCURRED ---")
        print(f"ERROR: {e}")
        print("The game must restart. Please refresh the page.")
        # Also print to the server console for debugging
        import traceback
        traceback.print_exc()
    
    print("--- GAME OVER ---")
    print("Refresh the page to play again.")

# --- Start The Server ---
if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)