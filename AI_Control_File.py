from httpx import stream
import ollama, json
from textwrap import dedent



class AI_Control:
    def __init__(self,):
        self.action = None

    def parse_choice(self, available_choices, player_text):
        prompt = dedent(f"""
    You are the choice parser for a text RPG.
    The player may only choose from these choices now: {", ".join(available_choices)}.
    Convert the player's input into JSON with one of these actions.
    Return ONLY JSON. Do not invent other actions.
    Return ONLY JSON in the form:
    {{"choice": "<one of the choices>"}}
    """)    
        
        response = ollama.chat(
            model="phi3",
            format="json",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": player_text}
            ]
        )
        try:
            
            parsed = json.loads(response['message']['content'])
            print(parsed.get("choice", "no").lower())
            answer = parsed.get("choice", "none").lower()
            if answer not in (available_choices):
                answer = "none"  # enforce valid fallback
            return answer
        except json.JSONDecodeError:
            # fallback to a safe default
            self.action = {"choice": "None", }
            return self.action
 
    def parse_YN(self, player_text: str) -> str:
        """
        Parse yes/no answers robustly without using LLMs.
        Always returns 'yes' or 'no'.
        """
        yes_words = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "affirmative", "of course", "certainly"}
        no_words  = {"no", "n", "nope", "nah", "negative", "never"}

        text = player_text.strip().lower()

        # Direct checks
        if text in yes_words:
            return "yes"
        if text in no_words:
            return "no"

        # Partial matching (covers phrases like "yes please", "sure thing")
        for word in yes_words:
            if word in text:
                return "yes"
        for word in no_words:
            if word in text:
                return "no"

        # Fallback default
        return "no"

    
    def parse_purchase(self, items: list, player_text):
        prompt = dedent(f"""
You are the action parser for a text RPG.
The player is trying to purchase an item. The available items are: {", ".join(items)}.
Convert the player's input into JSON **with exactly two keys**:
1. "choice" → must be exactly one of the items (case-insensitive).
2. "quantity" → must always be present as a string representing an integer. 
   If the player does not specify a number, use "1" as the default.
Return ONLY JSON. No explanations or extra text.

Example outputs:
{{"choice": "rifle", "quantity": "1"}}
{{"choice": "pistol_ammo", "quantity": "3"}}
{{"choice": "leave", "quantity": ""}}
""")
        response = ollama.chat(
            model="phi3",
            format="json",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": player_text}
            ]
        )
        try:
            
            self.action = json.loads(response['message']['content'])         # convert to dict

            return self.action
        except json.JSONDecodeError:
            # fallback to a safe default
            self.action = {"choice": "leave", "args": {}}
            return self.action

    def parse_action(self, player_text: str, available_actions: list):
        prompt = dedent(f"""
        You are an action parser for a text RPG.
        The player may only perform one of these actions: {available_actions}

        Return ONLY JSON in this format:
        {{"action": "one of the available actions"}}
        """)

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
            parsed = json.loads(response['message']['content'])
            action = parsed.get("action", "").lower()
            if action not in available_actions:
                action = "help"  # fallback
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

    def narrate_action(self, game_state, possible_actions, past_actions):
        action = self.action.get("action")
        args = self.action.get("args", {})

        # Create a dynamic prompt
        prompt = dedent(f"""
    You are the narrator for a western text RPG.
    The world state is: {game_state}.
    Past actions: {past_actions}.
    The player has chosen the action: {action} with arguments {args}.
    Write a short narration (1-2 sentences max) describing what happens next.
    Keep it immersive and consistent with the world state.
    Suggest a few possible actions, consistent with {possible_actions} and include them in the narration subtly.
    """)
        
        response_stream = ollama.chat(
            model="llama3:8b",
            messages=[
                {"role": "system", "content": prompt}
            ],
            stream=True
        )
        
        narration = ""
        for chunk in response_stream:
            # Ollama yields dicts with incremental content
            token = chunk["message"]["content"]
            print(token, end="", flush=True)   # print as it arrives
            narration += token
        print()
        return narration

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