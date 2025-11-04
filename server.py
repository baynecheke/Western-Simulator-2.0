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
# Make sure these files are in the same folder
from AI_Control_File import AI_Control
from Western_Sim import Player 
from store import ShopItem, ShopSession
import game_html # This is our new HTML file

# --- Global Game Objects ---
app = Flask(__name__)
# We get the secret key from environment variables for security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-fallback-secret-key-12345')
socketio = SocketIO(app)

# --- Thread-Safe Communication ---
# This Event will pause the game thread while we wait for web input
input_event = threading.Event()
player_response = None

def get_player_response_from_global():
    """A function to safely get the response."""
    global player_response
    return player_response

# --- Instantiate Game Objects ---
# 1. Create the AI Controller Bridge, passing it the server tools
ai_file = AI_Control(socketio, input_event, get_player_response_from_global) 

# 2. Create the Player. (Your Player __init__ should NOT take any arguments)
player = Player() 

# 3. Link the player to the AI controller
# (Your Western_Sim.py already has 'self.AI_File = AI_File' in __init__)
# We just need to make sure the global AI_File is our new one.
# NOTE: This line is critical and replaces the `AI_File = AI_Control()` in Western_Sim.py
player.AI_File = ai_file

# --- MONKEY-PATCH 'print()' ---
# This is your clever idea!
# We tell Python's built-in 'print' to
# actually call our 'print_to_client' function.
builtins.print = ai_file.print_to_client
# ---

# --- Web Server Routes ---
@app.route('/')
def index():
    """Serves the main HTML game page."""
    # Renders the HTML string from our game_html.py file
    return render_template_string(game_html.HTML_CONTENT)

# --- Socket.IO Event Handlers (The "Waiter") ---
@socketio.on('connect')
def handle_connect():
    """A new player connected. Start the game loop in a new thread."""
    # We use emit() directly here because print() hasn't been patched
    # for this specific connection thread yet.
    socketio.emit('game_message', {'text': 'Client connected!'})
    
    # Start the game loop in a background thread
    # This check prevents the game from restarting on a simple refresh
    if player.Health > 0 and player.Day == 1 and player.Time == 9:
         threading.Thread(target=run_game_loop).start()

@socketio.on('player_response')
def handle_player_response(data):
    """
    We received an answer from the web client.
    This is the replacement for 'input()'.
    """
    global player_response, input_event
    
    # 1. Store the response
    player_response = data['choice']
    
    # 2. Tell the game thread (which is waiting) to wake up
    input_event.set()

@socketio.on('request_save')
def handle_request_save():
    """Browser is asking to save. Tell the game to save."""
    # This is a simple example. You'd need a way
    # to trigger the save logic in your player class.
    # For now, we just acknowledge.
    print("Save request received... (logic not fully implemented)")
    # In a full app, you'd call player.save_game()
    # and that function would emit the save data back.

@socketio.on('load_game')
def handle_load_game(data):
    """Browser is sending us a save file to load."""
    print("Load request received... (logic not fully implemented)")
    # Here you would parse data['save_data']
    # and use it to set up the player object
    # player.load_from_json_string(data['save_data'])


# --- The Main Game Loop Function ---
def run_game_loop():
    """
    This function runs the actual game logic in a separate thread.
    """
    try:
        # This will now call the 'print()' statements at the
        # bottom of Western_Sim.py, which are now patched
        # and will send messages to the client.
        
        # --- CRITICAL ---
        # You must REMOVE the `player = Player()` and `player.main_game_loop()`
        # lines from the *bottom* of your Western_Sim.py file.
        # We call it from here now.
        
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
    # allow_unsafe_werkzeug=True is needed for the simple reloader
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)

