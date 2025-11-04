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

    def parse_choice(self, available_choices, player_prompt ,use_ollama):
        player_text = input(player_prompt)
        safe_fallback = "none"
        if "leave" in available_choices:
            safe_fallback = "leave"
        if use_ollama:
            prompt = dedent(f"""
        You are the choice parser for a text RPG.
        The player may only choose from these choices now: {", ".join(available_choices)}.
        Convert the player's input into JSON with one of these actions.
        Return ONLY JSON. Do not invent other actions.
        Return ONLY JSON in the form:
        {{"choice": "<one of the choices>"}}
        """)    
            
            # --- START FIX ---
            # Define a smart, safe fallback action.
            # If "leave" is a valid choice, use it. Otherwise, use "none".
            safe_fallback = "none"
            if "leave" in available_choices:
                safe_fallback = "leave"
            # --- END FIX ---

            try:
                response = ollama.chat(
                    model="phi3",
                    format="json",
                    options={"temperature": 0},   # deterministic & faster
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": player_text}
                    ]
                )
                
                # This is your original try/except, now nested
                try:
                    parsed = json.loads(response['message']['content'])
                    answer = parsed.get("choice", safe_fallback).lower() # Use safe_fallback
                    if answer not in (available_choices):
                        answer = safe_fallback  # Enforce valid fallback
                    return answer.strip().lower()
                except json.JSONDecodeError:
                    return safe_fallback # Return the safe string
                    
            except Exception as e: # This catches network errors
                print(f"[AI_Control Error in parse_choice]: {e}")
                print(f"[AI_Control]: Falling back to default '{safe_fallback}' action.")
                return safe_fallback # Return the safe string
        else:
            print("\nChoose an option:")
            for i, choice_text in enumerate(available_choices, 1):
                print(f"{i}. {choice_text.capitalize()}")

            # The 'player_text' variable holds the user's raw input (which should be a number here)
            player_text = input(player_prompt)
            choice_input = player_text # Use the input directly

            try:
                choice_num = int(choice_input)
                if 1 <= choice_num <= len(available_choices):
                    # Adjust index (user enters 1, list index is 0)
                    return available_choices[choice_num - 1].lower()
                else:
                    print("Invalid number.")
                    return safe_fallback
            except ValueError:
                # Still allow direct name match as a fallback if they typed text
                if choice_input.lower() in available_choices:
                    return choice_input.lower()
                print("Please enter a valid number corresponding to the choice.")
                return safe_fallback

    def parse_YN(self, player_prompt) -> str:
        player_text = input(player_prompt)
        """
        Parse yes/no answers robustly without using LLMs.
        Always returns 'yes' or 'no'.
        """
        yes_words = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "affirmative", "of course", "certainly"}
        no_words  = {"no", "n", "nope", "nah", "negative", "never"}

        text_lower = player_text.strip().lower()

        # Direct check first (most common)
        if text_lower in yes_words:
            return "yes"
        if text_lower in no_words:
            return "no"

        # Split input into words and check
        words_in_text = set(text_lower.split())

        # Check if any word from the input is in our 'yes' set
        if not words_in_text.isdisjoint(yes_words):
            return "yes"

        # Check if any word from the input is in our 'no' set
        if not words_in_text.isdisjoint(no_words):
            return "no"

        # Fallback default
        return "no"

    def parse_purchase(self, items: list, player_prompt, use_ollama):
        player_text = input(player_prompt)
        if use_ollama:
            # --- START FIX ---
            # The 'items' list passed from store.py NOW CONTAINS 'inventory' and 'leave'
            # So we don't need to add "leave" again.
            shop_items = items 
            
            prompt = dedent(f"""
        You are the action parser for a text RPG.
        The player is trying to purchase an item. The available items are: {", ".join(shop_items)}.
        Convert the player's input into JSON **with exactly two keys**:
        1. "choice" -> must be exactly one of the items (case-insensitive).
        2. "quantity" -> must always be present as a string representing an integer.
        - If the player does not specify a number, use "1" as the default.
        - If the player's choice is "leave", use "0" as the quantity.
        - If the player's choice is "inventory", use "0" as the quantity.
        Return ONLY JSON. No explanations or extra text.

        Example outputs:
        {{"choice": "rifle", "quantity": "1"}}
        {{"choice": "pistol_ammo", "quantity": "3"}}
        {{"choice": "inventory", "quantity": "0"}}
        {{"choice": "leave", "quantity": "0"}}
        """)
            # --- END FIX ---

            response = ollama.chat(
                model="phi3",
                format="json",
                options={"temperature": 0},   # deterministic & faster
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": player_text}
                ]
            )
            
            try:
                # 1. Try to parse the LLM's response
                parsed_data = json.loads(response['message']['content'])

                # 2. Basic structure check
                if not isinstance(parsed_data, dict):
                    raise ValueError("LLM did not return a dictionary.")

                # 3. Get 'choice', with a fallback
                choice = parsed_data.get("choice", "leave").lower()

                # 4. Get 'quantity' raw value, with a "1" default if key is missing
                quantity_raw = parsed_data.get("quantity", "1")

                # 5. Validate 'choice'
                valid_choices = [item.lower() for item in shop_items]
                if choice not in valid_choices:
                    choice = "leave" # Fallback to "leave" if choice is invalid

                # 6. Handle the "leave" and "inventory" cases explicitly
                if choice == "leave" or choice == "inventory":
                    quantity_final = "0"
                else:
                    # 7. VALIDATION PATCH: Validate 'quantity' for non-action choices
                    
                    # Convert if it's an int (e.g., 1 -> "1")
                    if isinstance(quantity_raw, int):
                        quantity_raw = str(quantity_raw)
                        
                    # Check if it's a string AND is a positive digit
                    if isinstance(quantity_raw, str) and quantity_raw.isdigit() and int(quantity_raw) > 0:
                        quantity_final = quantity_raw
                    else:
                        # This is a "weird" value (e.g., "two", "0", "", "-5", "a bunch")
                        # Default to "1" as requested
                        quantity_final = "1" 

                # 8. Success: create and return the clean action
                self.action = {"choice": choice, "quantity": quantity_final}
                return self.action

            except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                # 9. Catch-all fallback for bad JSON or validation errors
                # Return a consistent, safe default that matches the expected format
                self.action = {"choice": "leave", "quantity": "0"} 
                return self.action
        else:
            # --- Numerical Fallback Logic ---
            safe_fallback = {"choice": "leave", "quantity": "0"}
            
            # The 'player_text' variable holds the user's raw input
            # E.g., "1" or "1 10" or "bread 5"
            choice_input = player_text.strip().lower()

            if not choice_input:
                # User just hit enter
                return safe_fallback

            # --- START NEW PARSING LOGIC ---
            parts = choice_input.split()
            item_identifier = parts[0]  # This is "1" or "bread"
            quantity_str = "1"          # Default quantity

            if len(parts) > 1:
                # User provided a quantity, e.g., "1 10"
                if parts[1].isdigit() and int(parts[1]) > 0:
                    quantity_str = parts[1]
                # (If it's not a valid number, we just ignore it and use the default "1")
            
            # --- END NEW PARSING LOGIC ---

            try:
                # --- Try parsing the identifier as a NUMBER ---
                choice_num = int(item_identifier)

                if 1 <= choice_num <= len(items):
                    selected_item_name = items[choice_num - 1].lower() # Get 'item1', 'inventory', or 'leave'

                    if selected_item_name == "leave":
                        return safe_fallback
                    
                    if selected_item_name == "inventory":
                        return {"choice": "inventory", "quantity": "0"}
                    
                    # It's an item. Return it with the parsed quantity.
                    self.action = {"choice": selected_item_name, "quantity": quantity_str}
                    return self.action
                else:
                    # This handles numbers outside the printed range
                    print("Invalid number.")
                    return safe_fallback

            except ValueError:
                # --- Identifier was NOT a number, try it as a NAME ---
                
                # Check if they typed an item name directly
                if item_identifier in items:
                    selected_item_name = item_identifier
                    
                    # Double-check it's not an action
                    if selected_item_name == "leave":
                        return safe_fallback
                    if selected_item_name == "inventory":
                        return {"choice": "inventory", "quantity": "0"}
                        
                    # It's an item. Return it with the parsed quantity.
                    self.action = {"choice": selected_item_name, "quantity": quantity_str}
                    return self.action
                
                # Handle 'leave' or 'inventory' by name
                if item_identifier == "leave":
                    return safe_fallback
                if item_identifier == "inventory":
                    return {"choice": "inventory", "quantity": "0"}

                # If input is neither a valid number nor item name
                print("Please enter the number or name of your choice.")
                return safe_fallback
            # --- End Numerical Fallback Logic ---

    def parse_action(self, player_prompt, available_actions: list, use_ollama):
        player_text = input(player_prompt)
        if use_ollama:
            # --- START FIX ---
            # Give the AI a "help" option and better instructions
            ai_choices = available_actions + ["help"]
            
            prompt = dedent(f"""
            You are an action parser for a text RPG.
            The player's input is: "{player_text}"
            
            You must choose the **closest match** from this list of actions: {ai_choices}
            - If the player's input is "travel", the closest match is "travel road".
            - If the player's input is unclear, or you cannot find a good match, default to "help".

            Return ONLY JSON in this format:
            {{"action": "<one_of_the_choices_from_the_list>"}}
            """)
            # --- END FIX ---

            response = ollama.chat(
                model="phi3",
                format="json",
                options={"temperature": 0},   # deterministic & faster
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

