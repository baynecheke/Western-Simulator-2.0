from httpx import stream
import ollama, json
from textwrap import dedent



class AI_Control:
    def __init__(self):
        self.action = None

    def parse_action(self, player_text: str, available_actions: list):
        prompt = dedent(f"""
    You are the action parser for a text RPG.
    The player may only perform these actions now: {available_actions}.
    Convert the player's input into JSON with one of these actions.
    Return ONLY JSON. Do not invent other actions.
    You may include arguments in the "args" field if needed.
    Arguments are optional.
    Example output: {{"action": "move", "args": {{"direction": "north"}}}}
    Second example: {{"action": "attack_guard", "args": {{"combatant": "guard"}}}}
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
            response_text = response['message']['content']  # this is still a string
            response_text = response_text.strip()            # remove leading/trailing whitespace
            self.action = json.loads(response_text)         # convert to dict

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

    def narrate_action(self):
        from Western_Sim import Player
        player = Player()
        game_state = "Player is in a town with guards at the walls and townsfolk milling about."
        tool = self.action.get("action")
        args = self.action.get("args", {})

        # Create a dynamic prompt
        prompt = dedent(f"""
    You are the narrator for a text RPG.
    The world state is: {game_state}.
    The player has chosen the action: {tool} with arguments {args}.
    Write a short narration (2-3 sentences max) describing what happens next.
    Keep it immersive and consistent with the world state.
    Suggest a few possible actions, and include them in the narration subtly.
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


#AI = AI_Control()
#AI.parse_example()
#AI.narrate_action()