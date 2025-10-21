from httpx import stream
import ollama, json
from textwrap import dedent



class AI_Control:
    def __init__(self,):
        self.action = None

# In AI_Control_File.py

    def parse_choice(self, available_choices, player_text):
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

    def parse_purchase(self, items: list, player_text):
            # Add "leave" as a valid item for the prompt
            shop_items = items + ["leave"]
            
            prompt = dedent(f"""
        You are the action parser for a text RPG.
        The player is trying to purchase an item. The available items are: {", ".join(shop_items)}.
        Convert the player's input into JSON **with exactly two keys**:
        1. "choice" -> must be exactly one of the items (case-insensitive).
        2. "quantity" -> must always be present as a string representing an integer.
        - If the player does not specify a number, use "1" as the default.
        - If the player's choice is "leave", use "0" as the quantity.
        Return ONLY JSON. No explanations or extra text.

        Example outputs:
        {{"choice": "rifle", "quantity": "1"}}
        {{"choice": "pistol_ammo", "quantity": "3"}}
        {{"choice": "leave", "quantity": "0"}}
        """) # NOTE: Changed the "leave" example from "" to "0" for consistency

            response = ollama.chat(
                model="phi3",
                format="json",
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

                # 6. Handle the "leave" case explicitly
                if choice == "leave":
                    quantity_final = "0"
                else:
                    # 7. VALIDATION PATCH: Validate 'quantity' for non-leave choices
                    
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


# In AI_Control_File.py
    def parse_action(self, player_text: str, available_actions: list):
        
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
   

    def parse_dialogue_player(self, player_dialogue, choices: list):
        prompt = dedent(f"""
    You are a dialogue parser for a game.  
    The player is speaking to an NPC.  
    You must choose one of the following actions: {", ".join(choices)}.  

    Return ONLY valid JSON in this format:
    {{"action": "<one_of_choices>"}}

    If the player is not clear, default to:
    {{"action": "talk"}}
    """)
        
        response = ollama.chat(
            model="phi3",
            format="json",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": player_dialogue}
            ]
        )
        try:
            
            self.action = json.loads(response['message']['content'])         # convert to dict

            return self.action
        except json.JSONDecodeError:
            # fallback to a safe default
            self.action = {"action": "talk"}
            return {"action": "talk", }

    # def narrate_action(self, game_state, possible_actions, past_actions):
    #     action = self.action.get("action")
    #     args = self.action.get("args", {})

    #     # Create a dynamic prompt
    #     prompt = dedent(f"""
    # You are the narrator for a western text RPG.
    # The world state is: {game_state}.
    # Past actions: {past_actions}.
    # The player has chosen the action: {action} with arguments {args}.
    # Write a short narration (1-2 sentences max) describing what happens next.
    # Keep it immersive and consistent with the world state.
    # Suggest a few possible actions, consistent with {possible_actions} and include them in the narration subtly.
    # """)
        
    #     response_stream = ollama.chat(
    #         model="llama3:8b",
    #         messages=[
    #             {"role": "system", "content": prompt}
    #         ],
    #         stream=True
    #     )
        
    #     narration = ""
    #     for chunk in response_stream:
    #         # Ollama yields dicts with incremental content
    #         token = chunk["message"]["content"]
    #         print(token, end="", flush=True)   # print as it arrives
    #         narration += token
    #     print()
    #     return narration


    def narrate_shop(self, game_state, event, NPC):
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
        leave = False
        while leave == False:
            prompt = [base_prompt[0]]
            prompt.extend(dialogue_history[-3:])
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
            

            dialogue_history.append({"role": "assistant", "content": narration})

                
            player_input = input("You: ").strip()
            if player_input.lower() in ["bye"]:
                print(f"{NPC}: Safe travels, stranger.")
                break
            dialogue_history.append({"role": "user", "content": player_input})
            list_options = ["buy", "talk", "leave"]
            choice = self.parse_dialogue_player(player_input, list_options)
            if choice.get("action", 'talk') == "leave":
                print(f"{NPC}: Safe travels, stranger.")
                leave = True
                return 'leave'
            if choice.get("action", 'talk') == "buy":
                leave = True
                print("Here is what I've got:")
                return 'buy'
            
    def narrate_dialogue_once(self, game_state, event, NPC):
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
           



#AI = AI_Control()
#AI.parse_example()
#AI.narrate_action()