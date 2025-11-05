import json
import os
import time
from textwrap import dedent
from groq import Groq # We can safely import this at the top now

class AI_Control:
    def __init__(self, outbox_queue, inbox_queue):
        self.action = None
        self.outbox = outbox_queue # The "mailbox" to send commands TO the browser
        self.inbox = inbox_queue   # The "mailbox" to receive answers FROM the browser
        self.use_ai = False
        
        # We can safely initialize the Groq client here.
        # The library conflicts are gone.
        try:
            self.groq_api_key = os.environ.get("GROQ_API_KEY")
            if not self.groq_api_key:
                print("[WARNING] GROQ_API_KEY not found in .env file. AI features will be disabled.")
                self.groq_client = None
            else:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.use_ai = True
                print("[Groq client initialized. AI features enabled.]")
        except Exception as e:
            print(f"Failed to initialize Groq client: {e}")
            print("Falling back to numerical-only mode.")
            self.groq_client = None

    # --- CORE I/O (Output) FUNCTIONS ---

    def print_to_client(self, *args, **kwargs):
        """ Replaces 'print()'. Puts a 'game_message' command in the outbox. """
        message = " ".join(map(str, args))
        self.outbox.put({'type': 'game_message', 'text': message})

    def play_sound(self, filename, loop=False):
        """ Puts a 'play_sound' command in the outbox. """
        self.outbox.put({
            'type': 'play_sound',
            'file': f'static/audio/{filename}',
            'loop': loop
        })

    def change_music(self, filename, loop=-1):
        """ Puts a 'change_music' command in the outbox. """
        self.outbox.put({
            'type': 'change_music',
            'file': f'static/audio/{filename}',
            'loop': True if loop == -1 else False
        })
        
    def weapon_sound(self, weapon):
        """ Tells the client to play a weapon sound. """
        if "rifle" in weapon: self.play_sound("rifle_shot.mp3")
        elif "revolver" in weapon or "pistol" in weapon: self.play_sound("revolver_shot.mp3")
        elif "shotgun" in weapon: self.play_sound("shotgun.mp3")
        elif "knife" in weapon or "saber" in weapon: self.play_sound("knife.mp3")
        elif "tomahawk" in weapon: self.play_sound("tomahawk.mp3")
        else: self.play_sound("punch.mp3")

    def enemy_sound(self, name):
        """ Tells the client to play an enemy sound. """
        if "wolf" in name: self.play_sound("wolf_howl.mp3")
        elif "snake" in name or "viper" in name or "cobra" in name: self.play_sound("rattle_snake.mp3")
        
    def update_stats_display(self, player_obj):
        """ Puts an 'update_stats' command in the outbox. """
        try:
            self.outbox.put({
                'type': 'update_stats',
                'payload': {
                    'health': player_obj.Health,
                    'max_health': player_obj.MaxHealth,
                    'hunger': player_obj.Hunger,
                    'gold': player_obj.gold,
                    'day': player_obj.Day,
                    'time': f"{player_obj.Time}:00",
                    'location': player_obj.current_town_name if player_obj.invillage else "On the Trail",
                    'difficulty': player_obj.difficulty.capitalize()
                }
            })
        except Exception as e:
            print(f"[Stat Update Error]: {e}") 

    # --- CORE I/O (Input) FUNCTIONS ---

    def patched_input(self, prompt=""):
        """
        This replaces builtins.input.
        It sends the prompt to the client (via the print patch)
        and then requests text input.
        """
        # The prompt is automatically sent by the print() patch
        # that 'input()' triggers.
        # We just need to ask the browser for a text box.
        return self._get_web_input(prompt, input_type='text')

    def _get_web_input(self, prompt, choices=None, input_type='choice'):
        """
        This is the new "master input" function.
        1. It puts a question (e.g., 'ask_for_choice') in the outbox.
        2. It PAUSES and waits for a response to appear in the inbox.
        3. It returns the response.
        """
        if input_type == 'choice':
            self.outbox.put({
                'type': 'ask_for_choice', 
                'prompt': prompt, 
                'choices': choices
            })
        elif input_type == 'text':
            # Ask the browser to show a text box.
            self.outbox.put({
                'type': 'ask_for_text', 
                'prompt': prompt
            })
        
        # This is the magic:
        # The game thread will sleep here until the /send_response route
        # puts an item in the inbox.
        response = self.inbox.get() 
        
        return response

    def _call_groq(self, system_prompt, user_prompt, is_json=True):
        """ Helper function to call the Groq API. """
        if not self.use_ai or self.groq_client is None:
            return None 
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"} if is_json else None,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            self.print_to_client(f"[Groq API Error: {e}]")
            return None

    # --- PARSER FUNCTIONS (These are identical to your file) ---

    def parse_choice(self, available_choices, player_prompt):
        raw_text = self._get_web_input(player_prompt, choices=available_choices, input_type='choice')
        if raw_text in available_choices: return raw_text.lower()
        else: return "leave" if "leave" in available_choices else "none"

    def parse_YN(self, player_prompt) -> str:
        raw_text = self._get_web_input(player_prompt, choices=["Yes", "No"], input_type='choice')
        return "yes" if raw_text.lower() == "yes" else "no"

    def parse_purchase(self, items: list, player_prompt):
        item_choice = self._get_web_input(player_prompt, choices=items, input_type='choice')
        if item_choice == "leave": return {"choice": "leave", "quantity": "0"}
        if item_choice == "inventory": return {"choice": "inventory", "quantity": "0"}
        quantity_str = self._get_web_input(f"How many {item_choice}?", input_type='text')
        if quantity_str.isdigit() and int(quantity_str) > 0: final_quantity = quantity_str
        else:
            self.print_to_client(f"Invalid quantity '{quantity_str}'. Defaulting to 1.")
            final_quantity = "1"
        return {"choice": item_choice, "quantity": final_quantity}

    def parse_action(self, player_prompt, available_actions: list):
        raw_text = self._get_web_input(player_prompt, choices=available_actions, input_type='choice')
        if raw_text in available_actions: return {"action": raw_text}
        else: return {"action": "help"}

    def narrate_shop(self, game_state, event, NPC):
        if self.use_ai:
            prompt = dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}. Event: {event}. You are {NPC}.
            Stay in character, answer very briefly in dialogue style (1-2 sentences).
            Make sure you respond with the correct hostility.
            """)
            narration = self._call_groq(prompt, "The player enters your shop.", is_json=False)
            if narration: self.print_to_client(f"{NPC}: {narration}")
            else: self.print_to_client(f"\n{NPC}: Welcome to the shop. Take a look.")
            return 'buy'
        else:
            self.print_to_client(f"\n{NPC}: Welcome to the shop. Take a look.")
            return 'buy'

    def narrate_dialogue_once(self, game_state, event, NPC):
        if self.use_ai:
            prompt = dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}. Event: {event}. You are {NPC}.
            Stay in character. Ask the player a simple yes/no question based on the event.
            1-2 sentences max.
            """)
            question = self._call_groq(prompt, "Ask the player the question.", is_json=False)
            if question: self.print_to_client(f"{NPC}: {question}")
            else: self.print_to_client(f"{NPC}: {event} (yes/no?)")
        else:
            self.print_to_client(f"\n{NPC}: {event} (yes/no?)")
        return self.parse_YN("")
            
    def generate_diary_entry(self, game_state, player_health, max_health, day_memory, tone):
        fallback_entry = "Another day done. The trail is long." 
        if not self.use_ai: return fallback_entry
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
        if not full_entry: full_entry = fallback_entry
        return full_entry.strip()