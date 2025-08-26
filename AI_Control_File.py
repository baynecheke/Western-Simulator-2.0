from httpx import stream
import ollama, json
from textwrap import dedent



class AI_Control:
    def __init__(self,):
        self.action = None

    def parse_YN(self, choice: str, player_text):
        prompt = dedent(f"""
    You are the action parser for a text RPG.
    The player may only yes or no to this choice {choice}.
    Convert the player's input into JSON with yes or no.
    Return ONLY JSON. Do not invent other actions.
    Return ONLY JSON in the form:
    {{"choice": "yes or no", "args": {"an argument"}}}
    You may include arguments in the "args" field if needed.
    Arguments are optional.
    Example output: {{"choice": "yes", "args": {{"target": "bison"}}}}
    Second example: {{"choice": "no", "args": {{"leave location": "cave"}}}}
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
            self.action = {"action": "help", "args": {}}
            return {"action": "help", "args": {}}

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
            self.action = {"action": "help", "args": {}}
            return {"action": "help", "args": {}}

    def parse_action(self, player_text: str, available_actions: list):
        prompt = dedent(f"""
    You are the action parser for a text RPG.
    The player may only perform these actions now: {available_actions}.
    Convert the player's input into JSON with one of these actions.
    Return ONLY JSON. Do not invent other actions.
    Return ONLY JSON in the form:
    {{"action": "one of the actions", "args": {"an argument"}}}
    You may include arguments in the "args" field if needed.
    Arguments are optional.
    Example output: {{"action": "gunsmith's shop", "args": {{"purchase": "gun"}}}}
    Second example: {{"action": "town jail", "args": {{"target": "sheriff"}}}}
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
            self.action = {"action": "help", "args": {}}
            return {"action": "help", "args": {}}

    def parse_example(self):
        actions_in_city = ["move", "look", "talk", "inventory"]
        player_input = str(input("What do you want to do:"))
        parsed = self.parse_action(player_input, actions_in_city)
        print(parsed)

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
    
    def narrate_dialogue(self, game_state, event, NPC):
        # Create a dynamic prompt

        base_prompt = [{"role": "system", "content": dedent(f"""
        You are an NPC for a western text RPG.
        The world state is: {game_state}.
        Your tone should
        Event: {event}.
        You are {NPC}.
        Stay in character, answer briefly in dialogue style.
    """)}
]
        dialogue_history = []
        leave = False
        while leave == False:
            leave = False
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
            if player_input.lower() in ["bye", "leave", "exit", "quit"]:
                print(f"{NPC}: Safe travels, stranger.")
                break
            dialogue_history.append({"role": "user", "content": player_input})
            
            
            



#AI = AI_Control()
#AI.parse_example()
#AI.narrate_action()