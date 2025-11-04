import json
import os
import time
from textwrap import dedent
from groq import Groq

# This is the new "bridge" to the web server
# It's given these objects by server.py when it's created
class AI_Control:
    def __init__(self, socketio, input_event, get_player_response_func):
        self.action = None
        self.socketio = socketio
        self.input_event = input_event
        self.get_player_response = get_player_response_func
        self.use_ai = False # Default to False
        
        # Initialize the Groq client
        # It will automatically find the API key from the environment variables
        try:
            self.groq_api_key = os.environ.get("GROQ_API_KEY")
            if not self.groq_api_key:
                print("[WARNING] GROQ_API_KEY not found in .env file. AI features will be disabled.")
            else:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.use_ai = True
                print("[Groq client initialized. AI features enabled.]")
        except Exception as e:
            print(f"Failed to initialize Groq client: {e}")
            print("Falling back to numerical-only mode.")

    # --- CORE I/O FUNCTIONS ---

    def print_to_client(self, *args, **kwargs):
        """
        Replaces 'print()'. 
        Converts all arguments to a single string and sends it.
        """
        # This mimics the behavior of the built-in print()
        message = " ".join(map(str, args))
        self.socketio.emit('game_message', {'text': message})

    def play_sound(self, filename, loop=False):
        """Tells the client's browser to play a sound file."""
        self.socketio.emit('play_sound', {
            'file': f'static/audio/{filename}',
            'loop': loop
        })

    def change_music(self, filename, loop=-1):
        """Tells the client's browser to change the background music."""
        self.socketio.emit('change_music', {
            'file': f'static/audio/{filename}',
            'loop': True if loop == -1 else False
        })
        
    def update_stats_display(self, player_obj):
        """Sends a complete player stat block to the UI."""
        self.socketio.emit('update_stats', {
            'health': player_obj.Health,
            'max_health': player_obj.MaxHealth,
            'hunger': player_obj.Hunger,
            'gold': player_obj.gold,
            'day': player_obj.Day,
            'time': f"{player_obj.Time}:00",
            'location': player_obj.current_town_name if player_obj.invillage else "On the Trail",
            'difficulty': player_obj.difficulty.capitalize()
        })

    def _get_web_input(self, prompt, choices=None, input_type='choice'):
        """
        This is the new "master input" function.
        It tells the web UI to ask the user for something,
        then it PAUSES the game thread until the UI sends a response.
        """
        # 1. Clear the "event" flag
        self.input_event.clear()
        
        # 2. Emit the correct event to the web UI
        if input_type == 'choice':
            self.socketio.emit('ask_for_choice', {'prompt': prompt, 'choices': choices})
        elif input_type == 'text':
            self.socketio.emit('ask_for_text', {'prompt': prompt})
        
        # 3. PAUSE this (the game) thread and wait...
        self.input_event.wait() 
        
        # 4. Once we are 'woken up', get the response
        response = self.get_player_response()
        return response

    # --- "ask_..." FUNCTIONS (Your game will call these) ---
    # You MUST have refactored your game to use these functions!

    def ask_yes_no(self, prompt):
        """Asks a 'yes' or 'no' question and returns 'yes' or 'no'."""
        raw_text = self._get_web_input(prompt, choices=["Yes", "No"], input_type='choice')
        # The web buttons are reliable, so we just parse the response
        return "yes" if raw_text.lower() == "yes" else "no"

    def ask_choice(self, available_choices, prompt, use_ollama):
        """Asks the player to make a choice from a list."""
        # This function *no longer* needs the 'use_ollama' flag,
        # but we keep it to match your refactored code.
        raw_text = self.get_web_input(prompt, choices=available_choices, input_type='choice')
        
        # The web UI sends back the *exact* choice (e.g., "leave town")
        # So we just need to find it in the list.
        if raw_text in available_choices:
            return raw_text
        else:
            return "leave" # Safe fallback

    def ask_free_text(self, prompt):
        """Gets free text input (for save names, etc.)"""
        return self._get_web_input(prompt, input_type='text')
        
    def ask_purchase(self, items: list, prompt, use_ollama):
        """
        Asks the player what they want to buy.
        This is a simplified version. For quantity, you'd need a multi-step process.
        """
        # This will just show a button for each item
        raw_text = self._get_web_input(prompt, choices=items, input_type='choice')

        # The raw_text is the item name (e.g., "bread")
        # We return it in the format your 'parse_purchase' expects
        if raw_text in items and raw_text not in ["leave", "inventory"]:
             # TODO: This version doesn't ask for quantity!
             # You will need to add a second step that calls
             # ask_free_text("How many?") to get the quantity.
            return {"choice": raw_text, "quantity": "1"}
        elif raw_text == "inventory":
            return {"choice": "inventory", "quantity": "0"}
        else:
            return {"choice": "leave", "quantity": "0"}
            
    def ask_action(self, prompt, available_actions: list, use_ollama):
        """Asks for the main game action."""
        raw_text = self._get_web_input(prompt, choices=available_actions, input_type='choice')
        
        if raw_text in available_actions:
            return {"action": raw_text}
        else:
            return {"action": "leave"} # Safe fallback

    # --- ORIGINAL PARSERS (Refactored for Groq) ---
    # We keep these in case you want to use them for AI-driven text input later.
    # Your *current* code (ask_choice, ask_action) doesn't use these,
    # as it relies on simple button clicks, which is more reliable.

    def _call_groq(self, system_prompt, user_prompt, is_json=True):
        """Helper function to call the Groq API."""
        if not self.use_ai:
            return None 
        
        format_props = {}
        if is_json:
            # Llama 3 on Groq supports JSON mode
            format_props = {"type": "json_object"}
            
        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192", # Fast, reliable model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=format_props,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            self.print_to_client(f"[Groq API Error: {e}]")
            return None

    def parse_choice(self, available_choices, player_text, use_ollama):
        # This function is now just a wrapper.
        # The real logic is in 'ask_choice' which gets a direct button click.
        # We just format the button click to match what the old parser returned.
        if player_text in available_choices:
            return player_text
        return "leave" # fallback

    def parse_YN(self, player_prompt):
        # This function is now just a wrapper.
        # The real logic is in 'ask_yes_no'.
        return self.ask_yes_no(player_prompt)

    def parse_purchase(self, items: list, player_prompt, use_ollama):
        # This is now a wrapper.
        return self.ask_purchase(items, player_prompt, use_ollama)

    def parse_action(self, player_prompt, available_actions: list, use_ollama):
        # This is now a wrapper.
        return self.ask_action(player_prompt, available_actions, use_ollama)

    def narrate_shop(self, game_state, event, NPC, use_ollama):
        if self.use_ai:
            prompt = dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}. Event: {event}. You are {NPC}.
            Stay in character, answer very briefly in dialogue style (1-2 sentences).
            """)
            
            narration = self._call_groq(prompt, "The player enters your shop.", is_json=False)
            if narration:
                self.print_to_client(f"{NPC}: {narration}")
            return 'buy' # Always proceed to buy
        else:
            self.print_to_client(f"\n{NPC}: Welcome to the shop. Take a look.")
            return 'buy'
            
    def narrate_dialogue_once(self, game_state, event, NPC, use_ollama):
        if self.use_ai:
            prompt = dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}. Event: {event}. You are {NPC}.
            Stay in character. Ask the player a simple yes/no question based on the event.
            1-2 sentences max.
            """)
            question = self._call_groq(prompt, "Ask the player the question.", is_json=False)
            if question:
                self.print_to_client(f"{NPC}: {question}")
            else:
                self.print_to_client(f"{NPC}: {event} (yes/no?)") # Fallback
        else:
            self.print_to_client(f"\n{NPC}: {event} (yes/no?)")
            
        # The 'ask_yes_no' function will be called *after* this by your main code
        # This function's only job is to print the dialogue.
        # Your Western_Sim.py code MUST call `AI_File.ask_yes_no()` AFTER this.
        
        # We need to return what your *old* function returned.
        # This is a bit of a hack. Your refactored code should
        # just call `ask_yes_no` directly.
        
        # Let's assume your refactored code is:
        # choice = AI_File.narrate_dialogue_once(...)
        # if choice == "yes":
        #
        # Then we MUST call ask_yes_no here.
        return self.ask_yes_no("") # Prompt is already printed
            
    def generate_diary_entry(self, game_state, player_health, max_health, day_memory, tone):
        """
        Uses Groq to generate a creative diary entry based on the day's events.
        """
        fallback_entry = "Another day done. The trail is long." 
        
        if not self.use_ai:
            self.print_to_client(fallback_entry)
            return fallback_entry

        encounter_desc = day_memory.get('encounter') or "nothing special"
        loot_desc = day_memory.get('loot') or "nothing of note"

        prompt_content = dedent(f"""
        You are the personal diary of a western adventurer.
        Write a 2-3 sentence diary entry in a {tone} tone.
        Do NOT use "Dear Diary" or sign off.
        Context:
        Health: {player_health} / {max_health}
        Encounter: {encounter_desc}
        Loot: {loot_desc}
        """)

        full_entry = self._call_groq(prompt_content, "Write the diary entry.", is_json=False)

        if not full_entry:
            full_entry = fallback_entry
            
        self.print_to_client("\n— Your diary entry —")
        self.print_to_client(full_entry)
        
        return full_entry.strip()

