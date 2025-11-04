import json
import os
import time
from textwrap import dedent
from groq import Groq

class AI_Control:
    def __init__(self, socketio, input_event, get_player_response_func):
        self.action = None
        self.socketio = socketio
        self.input_event = input_event
        self.get_player_response = get_player_response_func
        self.use_ai = False # Default to False
        
        try:
            self.groq_api_key = os.environ.get("GROQ_API_KEY")
            if not self.groq_api_key:
                # This will now print to the web console
                print("[WARNING] GROQ_API_KEY not found in .env file. AI features will be disabled.")
            else:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.use_ai = True
                print("[Groq client initialized. AI features enabled.]")
        except Exception as e:
            print(f"Failed to initialize Groq client: {e}")
            print("Falling back to numerical-only mode.")

    # --- CORE I/O (Output) FUNCTIONS ---

    def print_to_client(self, *args, **kwargs):
        """ Replaces 'print()'. Converts all arguments to a single string and sends it. """
        message = " ".join(map(str, args))
        self.socketio.emit('game_message', {'text': message})

    def play_sound(self, filename, loop=False):
        """ Tells the client's browser to play a sound file. """
        self.socketio.emit('play_sound', {
            'file': f'static/audio/{filename}',
            'loop': loop
        })

    def change_music(self, filename, loop=-1):
        """ Tells the client's browser to change the background music. """
        self.socketio.emit('change_music', {
            'file': f'static/audio/{filename}',
            'loop': True if loop == -1 else False
        })
        
    def update_stats_display(self, player_obj):
        """ Sends a complete player stat block to the UI. """
        try:
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
        except Exception as e:
            print(f"[Stat Update Error]: {e}")

    # --- CORE I/O (Input) FUNCTIONS ---

    def _get_web_input(self, prompt, choices=None, input_type='choice'):
        """
        This is the new "master input" function.
        It tells the web UI to ask the user for something,
        then it PAUSES the game thread until the UI sends a response.
        """
        self.input_event.clear()
        
        if input_type == 'choice':
            self.socketio.emit('ask_for_choice', {'prompt': prompt, 'choices': choices})
        elif input_type == 'text':
            self.socketio.emit('ask_for_text', {'prompt': prompt})
        
        self.input_event.wait() 
        response = self.get_player_response()
        return response

    def _call_groq(self, system_prompt, user_prompt, is_json=True):
        """ Helper function to call the Groq API. """
        if not self.use_ai:
            return None 
        
        format_props = {}
        if is_json:
            format_props = {"type": "json_object"}
            
        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192", 
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

    # --- NEW PARSER FUNCTIONS (Replaces your old file) ---
    # These functions now get input from the web UI
    # instead of the console `input()`.

    def parse_choice(self, available_choices, player_prompt, use_ollama):
        # We always use the web buttons, which is the 'numerical' (safe) path.
        # The 'use_ollama' flag (now 'use_ai') is only for AI *narration*.
        
        # 1. Get input from the web UI by showing buttons
        # 'player_prompt' is used as the title for the button list
        raw_text = self._get_web_input(player_prompt, choices=available_choices, input_type='choice')

        # 2. Since the UI sends the *exact* choice (e.g., "leave town"),
        # we can just validate and return it.
        if raw_text in available_choices:
            return raw_text.lower()
        else:
            # Safe fallback
            if "leave" in available_choices:
                return "leave"
            else:
                return "none"

    def parse_YN(self, player_prompt) -> str:
        # 1. Get input from the web UI. We show two buttons: "Yes" and "No".
        raw_text = self._get_web_input(player_prompt, choices=["Yes", "No"], input_type='choice')
        
        # 2. The UI sends back "Yes" or "No". We convert it to your game's format.
        if raw_text.lower() == "yes":
            return "yes"
        else:
            return "no"

    def parse_purchase(self, items: list, player_prompt, use_ollama):
        # This is now a multi-step process
        
        # 1. Ask *what* item to buy
        # 'items' list already contains 'inventory' and 'leave'
        item_choice = self._get_web_input(player_prompt, choices=items, input_type='choice')
        
        # 2. Handle non-item choices
        if item_choice == "leave":
            return {"choice": "leave", "quantity": "0"}
        if item_choice == "inventory":
            return {"choice": "inventory", "quantity": "0"}

        # 3. It's an item. Now ask *how many*.
        quantity_str = self._get_web_input(f"How many {item_choice}?", input_type='text')
        
        # 4. Validate quantity
        if quantity_str.isdigit() and int(quantity_str) > 0:
            final_quantity = quantity_str
        else:
            # If they type "one" or "a bunch" or "0", default to 1
            print(f"Invalid quantity '{quantity_str}'. Defaulting to 1.")
            final_quantity = "1"
            
        # 5. Return the full dictionary your store.py expects
        return {"choice": item_choice, "quantity": final_quantity}


    def parse_action(self, player_prompt, available_actions: list, use_ollama):
        # 1. Get input from the web UI
        raw_text = self._get_web_input(player_prompt, choices=available_actions, input_type='choice')

        # 2. The UI sends the exact action.
        if raw_text in available_actions:
            return {"action": raw_text}
        else:
            # Safe fallback
            return {"action": "help"}

    def parse_dialogue_player(self, player_dialogue_prompt, choices: list, use_ollama):
        # This is now identical to parse_choice
        raw_text = self._get_web_input(player_dialogue_prompt, choices=choices, input_type='choice')
        
        if raw_text in choices:
            return {"action": raw_text}
        else:
            return {"action": "talk"} # Default fallback for dialogue

    # --- AI NARRATION FUNCTIONS (Using Groq) ---

    def narrate_shop(self, game_state, event, NPC, use_ollama):
        # We use the 'use_ollama' flag (which is now self.use_ai)
        if self.use_ai:
            prompt = dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}. Event: {event}. You are {NPC}.
            Stay in character, answer very briefly in dialogue style (1-2 sentences).
            Make sure you respond with the correct hostility.
            """)
            
            narration = self._call_groq(prompt, "The player enters your shop.", is_json=False)
            if narration:
                print(f"{NPC}: {narration}")
            else:
                print(f"\n{NPC}: Welcome to the shop. Take a look.") # Groq fallback
            
            # This function no longer needs to handle input.
            # Your store.py loop will continue and call 'parse_purchase' next.
            return 'buy' # Always proceed
        else:
            print(f"\n{NPC}: Welcome to the shop. Take a look.")
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
                print(f"{NPC}: {question}")
            else:
                print(f"{NPC}: {event} (yes/no?)") # Groq fallback
        else:
            print(f"\n{NPC}: {event} (yes/no?)")
            
        # Your Western_Sim.py code MUST call 'AI_File.parse_YN()' *after*
        # this function. This function's only job is to print the dialogue.
        # We return 'yes' or 'no' based on the player's *next* input.
        return self.parse_YN("") # Ask the Y/N question
            
    def generate_diary_entry(self, game_state, player_health, max_health, day_memory, tone):
        """ Uses Groq to generate a creative diary entry. """
        fallback_entry = "Another day done. The trail is long." 
        
        if not self.use_ai:
            print(fallback_entry)
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
            
        print("\n— Your diary entry —")
        print(full_entry)
        
        return full_entry.strip()