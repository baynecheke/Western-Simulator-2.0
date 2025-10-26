from httpx import stream
import ollama, json
from textwrap import dedent



class AI_Control:
    def __init__(self,):
        self.action = None

    def parse_choice(self, available_choices, player_text, use_ollama):
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

    def parse_YN(self, player_text: str) -> str:
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

    def parse_purchase(self, items: list, player_text, use_ollama):
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

    def parse_action(self, player_text: str, available_actions: list, use_ollama):
        
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
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": player_text} # The AI will now see the input twice, reinforcing it
                ]
            )

            try:
                parsed = json.loads(response['message']['content'])
                action = parsed.get("action", "").lower()
                
                # --- START FIX ---
                # Check against the list the AI was given
                if action not in ai_choices:
                    action = "help"  # fallback
                # --- END FIX ---

                self.action = {"action": action}
            except (json.JSONDecodeError, KeyError, TypeError):
                self.action = {"action": "help"}

            return self.action
        else:
            # --- Numerical Fallback Logic ---
            # This function NO LONGER prints the list.
            # Printing is now handled by TakeActionsChose in Western_Sim.py
            safe_fallback = {"action": "help"} # 'help' will cause TakeActionsChose to reprint the list

            # The 'player_text' variable holds the user's raw input (which should be a number here)
            choice_input = player_text # Use the input directly

            try:
                choice_num = int(choice_input)
                # Map numbers to actions (adjust index)
                if 1 <= choice_num <= len(available_actions):
                    action = available_actions[choice_num - 1].lower()
                    self.action = {"action": action}
                    return self.action
                elif choice_num == len(available_actions) + 1: # Check for Help number
                    self.action = {"action": "help"}
                    return self.action
                else:
                    print("Invalid number.") # Keep error message
                    return safe_fallback # Return 'help' to trigger a list reprint
            except ValueError:
                # Still allow direct name match as a fallback if they typed text
                if choice_input.lower() in available_actions:
                    self.action = {"action": choice_input.lower()}
                    return self.action
                elif choice_input.lower() == "help":
                    self.action = {"action": "help"}
                    return self.action
                
                # Only print error if it's not an empty string (e.g., just pressing Enter)
                if choice_input: 
                    print("Please enter a valid number or 'help'.") 
                return safe_fallback # Return 'help' to trigger a list reprint
            # --- End Numerical Fallback Logic ---

    def parse_dialogue_player(self, player_dialogue, choices: list, use_ollama):
        """
        Parses player dialogue input against a list of specific dialogue actions.
        Uses Ollama if use_ollama is True, otherwise uses numerical input.
        Defaults to 'talk' if unclear or on error.
        Returns a dictionary like {"action": "chosen_action"}.
        """
        safe_fallback_action = "talk" # Define the fallback action

        if use_ollama:
            # --- Ollama Logic ---
            prompt = dedent(f"""
            You are a dialogue parser for a game.
            The player is speaking to an NPC.
            You must choose one of the following actions based on the player's input: {", ".join(choices)}.

            Return ONLY valid JSON in this format:
            {{"action": "<one_of_choices>"}}

            If the player is not clear which action they want, default to:
            {{"action": "{safe_fallback_action}"}}
            """)

            try:
                response = ollama.chat(
                    model="phi3",
                    format="json",
                    options={"temperature": 0},   # deterministic & faster
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": player_dialogue}
                    ]
                )
                try:
                    parsed_action = json.loads(response['message']['content'])
                    # Validate the action returned by the AI
                    if parsed_action.get("action") not in choices:
                        print(f"[AI Warning: AI returned invalid action '{parsed_action.get('action')}'. Falling back.]")
                        self.action = {"action": safe_fallback_action}
                    else:
                        self.action = parsed_action # Use the valid AI response

                    return self.action
                except json.JSONDecodeError:
                    print("[AI Error: Could not parse dialogue response. Falling back.]")
                    self.action = {"action": safe_fallback_action}
                    return self.action # Use the safe fallback

            except Exception as e:
                print(f"[AI_Control Error in parse_dialogue_player]: {e}")
                print(f"[AI_Control]: Ollama call failed. Falling back to '{safe_fallback_action}'.")
                self.action = {"action": safe_fallback_action}
                return self.action
            # --- End Ollama Logic ---

        else:
            # --- Numerical Fallback Logic ---
            print("\nChoose a dialogue option:")
            for i, choice_text in enumerate(choices, 1):
                print(f"{i}. {choice_text.capitalize()}")

            # The 'player_dialogue' variable holds the user's raw input (number expected)
            choice_input = player_dialogue

            try:
                choice_num = int(choice_input)
                if 1 <= choice_num <= len(choices):
                    # Adjust index
                    chosen_action = choices[choice_num - 1].lower()
                    self.action = {"action": chosen_action}
                    return self.action
                else:
                    print("Invalid number.")
                    self.action = {"action": safe_fallback_action}
                    return self.action
            except ValueError:
                # Allow direct name match as fallback
                if choice_input.lower() in choices:
                    self.action = {"action": choice_input.lower()}
                    return self.action
                print("Please enter a valid number corresponding to the dialogue choice.")
                self.action = {"action": safe_fallback_action}
                return self.action
            # --- End Numerical Fallback Logic ---

    def narrate_shop(self, game_state, event, NPC, use_ollama):
        if use_ollama:
            # Create a dynamic prompt

            base_prompt = [{"role": "system", "content": dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}.
            Event: {event}.
            You are {NPC}.
            Stay in character, answer very briefly in dialogue style.
            1-2 sentences max.
            Make sure you respond with the correct hostility.
        """)}
    ]
            dialogue_history = []
            
            # --- START FIX ---
            # Define keywords that trigger actions
            leave_words = {"bye", "leave", "exit", "goodbye", "farewell", "see ya"}
            buy_words = {"buy", "shop", "wares", "see wares", "trade", "show me", "what do you have", "see what you have", "purchase"}
            # --- END FIX ---

            leave = False
            count = 0
            while leave == False:
                prompt = [base_prompt[0]]
                prompt.extend(dialogue_history[-3:])
                
                # --- Add outer try/except for network errors ---
                try:
                    response_stream = ollama.chat(
                        model="llama3:8b",
                        messages=prompt,
                        stream=True)
                except Exception as e:
                    print(f"[AI_Control Error in narrate_shop]: {e}")
                    print(f"{NPC}: Sorry, lost my train of thought. What was I sayin'?")
                    # Safely exit the conversation on AI failure
                    return 'leave' 
                # --- End outer try/except ---
                
                narration = ""

                for chunk in response_stream:
                    # Ollama yields dicts with incremental content
                    token = chunk["message"]["content"]
                    print(token, end="", flush=True)   # print as it arrives
                    narration += token
                

                dialogue_history.append({"role": "assistant", "content": narration})

                    
                player_input = input("You: ").strip()
                player_lower = player_input.lower() # Get a lowercase version

                # --- START FIX ---
                # 1. Check for LEAVE intent
                # We use 'any' to check if any of the player's words are in our leave_words set
                if any(word in player_lower.split() for word in leave_words) or player_lower in leave_words:
                    print(f"{NPC}: Safe travels, stranger.")
                    return 'leave' # Correctly return 'leave'

                # 2. Check for BUY intent
                # We use 'any' to check if the player's input contains any of our buy_words
                if any(phrase in player_lower for phrase in buy_words):
                    print(f"{NPC}: Here is what I've got:")
                    return 'buy' # Correctly return 'buy'
                # --- END FIX ---

                # 3. If not leaving or buying, it's just talk.
                dialogue_history.append({"role": "user", "content": player_input})
                
                # The loop will now repeat, and the AI will respond to the player's last statement.
                count = count + 1    
                if count > 3:
                    print(f"{NPC}: Well, if you're not buying, I gotta get back to work.")
                if count > 4:
                    print(f"{NPC}: Safe travels, stranger.")
                    leave = True
                    return 'leave'   
        else:
            # --- Numerical Fallback Logic ---
            # Simple, direct approach for non-AI mode
            print(f"\n{NPC}: Welcome to the shop. Take a look.")
            # Automatically proceed to showing wares in numerical mode.
            # The ShopSession loop will handle buying/leaving from there.
            return 'buy'
            # --- End Numerical Fallback Logic ---

    def narrate_dialogue_once(self, game_state, event, NPC, use_ollama):
        if use_ollama:
            # Create a dynamic prompt

            prompt = [{"role": "system", "content": dedent(f"""
            You are an NPC for a western text RPG.
            The world state is: {game_state}.
            Event: {event}.
            You are {NPC}.
            Stay in character, answer very briefly in dialogue style.
            1-2 sentences max.
            Make sure you respond with the correct hostility.
        """)}
    ]


            response_stream = ollama.chat(
                model="llama3:8b",
                messages=prompt,
                stream=True)
                
                
            narration = ""

            for chunk in response_stream:
                # Ollama yields dicts with incremental content
                token = chunk["message"]["content"]
                print(token, end="", flush=True)   # print as it arrives
                narration += token
            player_input = input("You: ").strip()
            choice = self.parse_YN(player_input)
            if choice == 'yes':
                return 'yes'
            else:
                return 'no'
        else:
            # --- Numerical Fallback Logic ---
            # Print a direct question based on the event context
            print(f"\n{NPC}: {event} (yes/no?)")
            player_input = input("You: ").strip()
            choice = self.parse_YN(player_input) # Use reliable Y/N parser
            return choice # Return 'yes' or 'no'
            # --- End Numerical Fallback Logic ---
            

