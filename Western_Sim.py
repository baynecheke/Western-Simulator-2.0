import random

import time
import json
import os

from store import ShopItem, ShopSession
global USE_OLLAMA
USE_OLLAMA = True
import builtins
import sys








class Player:
    def __init__(self, ai_file_arg):
        #Basic player stuff
        self.AI_File = ai_file_arg

        self.player_name = "default"
        self.rumors = {}
        self.Day = 1
        import yaml
        global weapons_data
        global loot_data
        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS # type: ignore
            except AttributeError: # <-- This is more specific
                # AttributeError is raised when _MEIPASS doesn't exist
                base_path = os.path.abspath(".")

            return os.path.join(base_path, relative_path)
        base_dir = resource_path(".")
        with open(os.path.join(base_dir, "weapons"), "r") as file:
            weapons_data = yaml.safe_load(file)


        with open(os.path.join(base_dir, "loot.yaml"), "r") as file:
            loot_data = yaml.safe_load(file)
        

        self.skip_freeze = False
        self.Time = 9
        self.Speed = 3
        self.counter = 0
        self.Hunger = 0
        self.Health = 100
        self.MaxHealth = 100
        self.itemsinventory = {}
        self.gold = 50  # Starting gold
        self.distancenext = 0
        self.event = []
        self.number_of_towns_visited = 0
        self.town_event_occurred = False
        self.town_encounter_available = False
        self.quest_flags = {
            "iron_tracks": {"stage": 0, "bonus": 0},
            "earp_vendetta": {"stage": 0, "bonus": 0},
            "defend_town": {"outcome": None, "aftermath": None, "final": None, "bonus": 0}
        }
        self.Heat = 100
        self.MaxHeat = 100
        self.cold_penalty = 0
        
        self.EmptyTown = False
        self.Speed = 3
        self.Hostility = 0
        self.invillage = True
        self.save_name = ""
        self.rumors_collected = 0
        self.rumors_heard = []
        self.rebirth = False
        self.tent_used_today = False

        #stuff
        self.score = 0
        self.poisoned = 0
        self.difficulty = 'frontier'  # Default
        # --- WINTER UPDATE: INIT FLAG ---
        self.winter_mode = False
        #boosts
        self.Armor_Boost = 1
        self.travel_bonus = 0
        self.trade_bonus = 0
        self.dmg_modifier_multiply = 1
        self.damage_modifier = 0
        self.shadow_skill = 3
        self.trail_skill = 3
        self.strength_skill = 3
        self.travelspeed = 3 + (self.trail_skill - 3) // 2
        self.Temporaryspdboost = 0
        self.Temporarytravelboost = 0
        self.enemy_effects = {}
        self.player_effects = {}
        self.TownUpgrades = {
            "general store": {'level':1},
            "gunsmith": {'level':1},
            "town jail":{'level':1},
            "doctor":{'level':1},
            "trading post":{'level':1},
            "blacksmith":{'level':1},
        }

        #classifications
        self.weapons = {
            "melee": [
                "knife",
                "tomahawk",
                "cavalry saber"
            ],
            "revolver": [
                "revolver",
                "colt pistol",
                "derringer pistol",
                "colt navy revolver",
                "remington pistol"
            ],
            "rifle": [
                "rifle",
                "winchester rifle",
                "henry rifle",
                "carbine rifle",
                "sharps rifle",
                "lever-action rifle"
            ],
            "shotgun": [
                "shotgun",
                "double barrel shotgun",
                "sawed-off shotgun"
            ]
        }

        self.QUEST_DATABASE = [
            # --- IRON TRACKS ---
            {
                "id": "iron_intro",
                "theme": "railroad",
                "trigger": "saloon",  # This appears as a button in the Saloon
                "description": "Talk to Railroad Men (Start Quest)",
                "condition": lambda p: "iron_tracks" not in p.quests_done and p.Tquest == "None" and p.rumors.get("railroad_job", 0) == 1,
                "function": "encounter_iron_intro"
            },
            {
                "id": "iron_missing_wagon",
                "theme": "railroad",
                "trigger": "arrive_town", # Happens automatically on arrival
                "description": "The Railroad Foreman looks furious and is asking for help.",
                "condition": lambda p: p.Tquest == "iron_tracks" and p.get_flag("iron_tracks", "stage") == 1,
                "function": "encounter_iron_stage1"
            },
            {
                "id": "iron_depot_night",
                "theme": "railroad",
                "trigger": "leave_town", # Happens when you try to leave
                "description": "You hear shouting coming from the train depot.",
                "condition": lambda p: p.Tquest == "iron_tracks" and p.get_flag("iron_tracks", "stage") == 2,
                "function": "encounter_iron_stage2"
            },
            {
                "id": "iron_train_defense",
                "theme": "railroad",
                "trigger": "leave_town", # Happens during daily update
                "description": "The first train is arriving. The Foreman needs guards.",
                "condition": lambda p: p.Tquest == "iron_tracks" and p.get_flag("iron_tracks", "stage") == 3,
                "function": "encounter_iron_stage3"
            },
            {
                "id": "iron_bridge",
                "theme": "railroad",
                "trigger": "leave_town",
                "description": "The Foreman runs up to you with urgent news about the bridge.",
                "condition": lambda p: p.Tquest == "iron_tracks" and p.get_flag("iron_tracks", "stage") == 4,
                "function": "encounter_iron_stage4"
            },
            {
                "id": "iron_dynamite_boss",
                "theme": "railroad",
                "trigger": "leave_town",
                "description": "The notorious Dynamite Kid has ridden into town.",
                "condition": lambda p: p.Tquest == "iron_tracks" and p.get_flag("iron_tracks", "stage") == 5,
                "function": "encounter_iron_stage5"
            },

            # --- TOWN DEFENSE ---
            {
                "id": "town_def_1",
                "theme": "town_defense",
                "trigger": "arrive_town",
                "description": "The Sheriff looks frantic and is asking for volunteers.",
                "condition": lambda p: p.Tquest == "defend_town" and p.get_flag("defend_town", "outcome") is None,
                "function": "encounter_town_part1"
            },
            {
                "id": "town_def_2",
                "theme": "town_defense",
                "trigger": "arrive_town",
                "description": "The town is scarred from the raid. They are rebuilding.",
                "condition": lambda p: p.Tquest == "defend_town" and p.get_flag("defend_town", "outcome") is not None and p.get_flag("defend_town", "aftermath") is None,
                "function": "encounter_town_part2"
            },
            {
                "id": "town_def_3",
                "theme": "town_defense",
                "trigger": "leave_town",
                "description": "Rumors say the bandits are returning for revenge tonight.",
                "condition": lambda p: p.Tquest == "defend_town" and p.get_flag("defend_town", "aftermath") is not None and p.get_flag("defend_town", "final") is None,
                "function": "encounter_town_part3"
            },
            {
                "id": "earp_meet_saloon",
                "theme": "earp",
                "trigger": "saloon",
                "description": "Approach the table where Wyatt Earp sits.",
                # Condition: Tquest is Earp, but stage is 0 (Waiting)
                "condition": lambda p: p.Tquest == "earp_vendetta" and p.get_flag("earp_vendetta", "stage") == 0,
                "function": "encounter_earp_intro" 
            },
            
            # 2. Stage 1: Pete Spence's Camp
            {
                "id": "earp_stage_1",
                "theme": "earp",
                "trigger": "town_event",
                "description": "The Posse rides to Pete Spence's wood camp.",
                "condition": lambda p: "earp_vendetta" not in p.quests_done and p.Tquest == "None" and p.rumors.get("earp_rumor", 0) == 1,
                "function": "encounter_earp_stage1"
            },

            # 3. Stage 2: Florentino Cruz
            {
                "id": "earp_stage_2",
                "theme": "earp",
                "trigger": "on_the_trail",
                "description": "Word comes that Florentino Cruz is near the San Pedro River.",
                "condition": lambda p: p.Tquest == "earp_vendetta" and p.get_flag("earp_vendetta", "stage") == 2,
                "function": "encounter_earp_stage2"
            },

            # 4. Stage 3: The Clanton Brothers
            {
                "id": "earp_stage_3",
                "theme": "earp",
                "trigger": "town_event",
                "description": "The Clanton brothers have been spotted nearby.",
                "condition": lambda p: p.Tquest == "earp_vendetta" and p.get_flag("earp_vendetta", "stage") == 3,
                "function": "encounter_earp_stage3"
            },

            # 5. Stage 4: Curly Bill Showdown
            {
                "id": "earp_stage_4",
                "theme": "earp",
                "trigger": "saloon",
                "description": "The final showdown with Curly Bill Brocius at Iron Springs.",
                "condition": lambda p: p.Tquest == "earp_vendetta" and p.get_flag("earp_vendetta", "stage") == 4,
                "function": "encounter_earp_stage4"
            },
            {
                "id": "warlord_finale",
                "theme": "finale",
                "trigger": "arrive_town",  # Triggers when you enter a town
                "description": "A US Marshal approaches you with an urgent mission.",
                # Condition: You must have survived at least 20 days and have no active quest
                "condition": lambda p: (
                    p.Day >= 20
                    and p.Tquest == "None"
                    and any(q in p.quests_done for q in ("iron_tracks", "earp_vendetta", "defend_town"))
                ),

                "function": "run_final_mission"
            }
            ]




    #loots
        self.common_loot = loot_data['common']
        
        self.uncommon_loot = loot_data['uncommon']
        
        self.rare_loot = loot_data['rare']
        
        self.ultra_rare_loot = loot_data['ultra_rare']
        
        self.medical_loot = [
                            "bandage", 
                            "bandage"]


        self.day_memory = {
            "encounter": None,   # e.g. "bandit", "rattlesnake"
            "loot": None,        # e.g. "Winchester rifle"
            "town_event": None   # e.g. "rebuilding Dust Camp"
        }
        self.music = True

        self.caravan = []
        self.world_events = [
        "A sandstorm rolls in, making travel harder.",
        "You hear whispers about gold in the hills.",
        "A traveling preacher offers a cryptic warning."
        ]



        self.Tquest = "None"  
        self.quest_today = False
        self.quest = []
        self.quests_done = []
        self.boots_used = False
        self.town_defense_outcome   = None
        self.town_aftermath_outcome = None
        self.town_final_outcome     = None
        self.town_defense_bonus = 0
        self.diary_bonuses = []
        self.diary_entries = []
        

        self.town_actions = [
            "town jail", "doctor's office", "general store", "gunsmith's shop", 
            "bank", "saloon", "talk townspeople", "trading post", 
            "blacksmith shop", "leave town"
        ]
        
        # Actions only available WHILE traveling
        self.travel_actions = ["travel road", "make camp"] 
        
        # Actions available in BOTH states
        self.universal_actions = ["use item", "inventory"]
        
        # This list will be built dynamically
        self.possibleactions = []

        self.TownNames1 = ["Gray", "Dust", "Buffalo", "Coyote", "Gold", "Post", "North"]
        self.TownNames2 = ["Town", "Ridge", "Camp", "Fort", "Settlement"]
        self.current_town_name = "Dustbowl"
        self.update_actions()

    @classmethod

    def load_game(cls):
        global player
        print("\n--- Load Game ---")
        save_folder = 'saves'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # 1. Get existing save files on the server
        save_files = [f for f in os.listdir(save_folder) if f.endswith('.json')]
        save_names = [f.replace('save_', '').replace('.json', '') for f in save_files]

        # 2. Add the "Upload" option
        upload_option = "Upload Save File (Paste Data)"
        menu_choices = save_names + [upload_option]

        if not menu_choices:
            # If no files and no menu generated (unlikely with upload option), just start new
            print("No save files found. Starting a new game.")
            return player 

        # 3. Ask the user
        choice = player.AI_File.parse_choice(
            menu_choices,
            "Choose a save slot or Upload a file:"
        )

        save_data = None

        # --- PATH A: UPLOAD (PASTE) LOGIC ---
        if choice == upload_option.lower():
            print("\n--- Upload Save ---")
            print("Open the .json save file on your computer with Notepad.")
            print("Copy ALL the text inside and paste it here.")
            
            # Use patched_input to get the raw string
            try:
                # We check if ask_free_text exists (it should if you added it previously)
                if hasattr(player.AI_File, 'ask_free_text'):
                    save_string = player.AI_File.ask_free_text("Paste JSON data here:")
                else:
                    save_string = player.AI_File.patched_input("Paste JSON data here:")

                # convert string to dictionary
                save_data = json.loads(save_string)
                print("Save data recognized!")
                
                # Save it to the server temp disk so it persists for this session
                # This prevents you from having to re-upload if you reload within the same session
                temp_name = save_data.get("save_name", "uploaded")
                with open(os.path.join(save_folder, f"save_{temp_name}.json"), 'w') as f:
                    json.dump(save_data, f)

            except json.JSONDecodeError:
                print("Error: The text you pasted is not valid JSON. Starting new game.")
                return player
            except Exception as e:
                print(f"Error reading upload: {e}")
                return player

        # --- PATH B: LOAD LOCAL FILE LOGIC ---
        else:
            # Find the original case-sensitive name
            original_cased_name = None
            for name in save_names:
                if name.lower() == choice:
                    original_cased_name = name
                    break
            
            if original_cased_name is None:
                print("Invalid choice. Starting a new game.")
                return player 

            save_file = f"save_{original_cased_name}.json"
            filepath = os.path.join(save_folder, save_file)
            
            try:
                with open(filepath, 'r') as f:
                    save_data = json.load(f)
            except Exception as e:
                print(f"Error loading file: {e}")
                return player

        # --- APPLY DATA TO PLAYER (Runs for both paths) ---
        if save_data:
            player.rebirth = save_data.get("rebirth", False)
            player.gold = save_data.get("gold", 0)
            player.itemsinventory = save_data.get("itemsinventory", {})
            player.distancenext = save_data.get("distancenext", 0)
            player.Day = save_data.get("Day", 1)
            player.Time = save_data.get("Time", 9)
            player.Health = save_data.get("Health", 100)
            player.Hunger = save_data.get("Hunger", 0)
            player.Hostility = save_data.get("Hostility", 0)
            player.score = save_data.get("score", 0)
            player.invillage = save_data.get("invillage", True)
            player.travel_bonus = save_data.get("travel_bonus", 0)
            player.trade_bonus = save_data.get("trade_bonus", 0)
            player.caravan = save_data.get("caravan", [])
            player.town_defense_outcome = save_data.get("defense_outcome", None)
            player.town_aftermath_outcome = save_data.get("aftermath_outcome", None)
            player.town_final_outcome = save_data.get("final_outcome", None)
            player.boots_used = save_data.get("boots", False)
            player.diary_entries = save_data.get("diary_entries", [])
            player.difficulty = save_data.get("difficulty", "frontier")
            player.MaxHealth = save_data.get("MaxHealth", 100)
            player.TownUpgrades = save_data.get("TownUpgrades", {})
            player.Tquest = save_data.get("Tquest", "None")
            player.quest = save_data.get("quest", [])
            player.rumors = save_data.get("rumors", {})
            player.diary_bonuses = save_data.get("diary_bonuses", [])
            player.rumors_heard = save_data.get("rumors_heard", [])
            player.enemy_effects = save_data.get("enemy_effects", [])
            player.player_effects = save_data.get("player_effects", [])
            player.shadow_skill = save_data.get("shadow_skill", 3)
            player.trail_skill = save_data.get("trail_skill", 3)
            player.strength_skill = save_data.get("strength_skill", 3)
            player.quests_done = save_data.get("quests_done", [])
            player.event = save_data.get("event", [])
            player.number_of_towns_visited = save_data.get("number_of_towns_visited", 0)
            player.quest_flags = save_data.get("quest_flags", {})
            player.Heat = save_data.get("Heat", 100)
            player.MaxHeat = save_data.get("MaxHeat", 100)
            player.cold_penalty = save_data.get("cold_penalty", 0)
            player.winter_mode = save_data.get("winter_mode", False)

            # Compatibility Check
            if "iron_tracks" not in player.quest_flags:
                player.quest_flags["iron_tracks"] = {
                    "stage": save_data.get("iron_stage", 0),
                    "bonus": save_data.get("iron_bonus", 0)
                }
            if "defend_town" not in player.quest_flags:
                player.quest_flags["defend_town"] = {
                    "outcome": player.town_defense_outcome,
                    "aftermath": player.town_aftermath_outcome,
                    "final": player.town_final_outcome,
                    "bonus": 0
                }
            player.normalize_effects()

            # Metadata
            player.player_name = save_data.get("player_name", "default")
            player.current_town_name = save_data.get("current_town_name", "Dustbowl")
            player.save_name = save_data.get("save_name", "uploaded")

            print(f"Game loaded successfully!")
            player.update_actions()
            return player

        return player

    def save_game(self):
        if not self.save_name:
            self.save_name = input("Enter a name for your save file: ").strip().replace(" ", "_")
        save_folder = 'saves'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        save_path = os.path.join(save_folder, f"save_{self.save_name}.json")
        with open(save_path, "w") as file:
            json.dump({
                "gold": self.gold,
                "itemsinventory": self.itemsinventory,
                "distancenext": self.distancenext,
                "Day": self.Day,
                "Time": self.Time,
                "Health": self.Health,
                "Hunger": self.Hunger,
                "Hostility": self.Hostility,
                "score": self.score,
                "invillage": self.invillage,
                "travel_bonus": self.travel_bonus,
                "trade_bonus": self.trade_bonus,
                "caravan": self.caravan,
                "defense_outcome": self.town_defense_outcome,
                "aftermath_outcome": self.town_aftermath_outcome,
                "final_outcome": self.town_final_outcome,
                "boots": self.boots_used,
                "diary_entries": self.diary_entries,
                "difficulty": self.difficulty,
                "MaxHealth": self.MaxHealth,
                "save_name": self.save_name,
                "TownUpgrades": self.TownUpgrades,
                "Tquest": self.Tquest,
                "quest": self.quest,
                "rumors": self.rumors,
                "diary_bonuses": self.diary_bonuses,
                "rumors_heard": self.rumors_heard,
                "enemy_effects": self.enemy_effects,
                "player_effects": self.player_effects,
                "rebirth": self.rebirth,
                "shadow_skill": self.shadow_skill,
                "trail_skill": self.trail_skill,
                "strength_skill": self.strength_skill,
                "quests_done": self.quests_done,
                "event": self.event,
                "number_of_towns_visited": self.number_of_towns_visited,
                "player_name": self.player_name,
                "current_town_name": self.current_town_name,
                "quest_flags": self.quest_flags,
                "Heat": self.Heat,
                "MaxHeat": self.MaxHeat,
                "cold_penalty": self.cold_penalty,
                "winter_mode": self.winter_mode,
            }, file)
        print(f"Game saved successfully to 'save_{self.save_name}.json'.")
# In Western_Sim.py
    def export_save(self):
            """Prints the raw save data so the user can copy-paste it to their PC."""
            if not self.save_name:
                print("You haven't saved the game yet.")
                return

            save_file = f"save_{self.save_name}.json"
            save_path = os.path.join('saves', save_file)
            
            if not os.path.exists(save_path):
                print(f"No save file found for '{self.save_name}'.")
                return

            print("\n--- SAVE DATA EXPORT ---")
            print("INSTRUCTIONS: Copy everything between the START and END lines below.")
            print("Create a new text file on your computer, paste the text in, and name it 'save_YourName.json'.")
            print("-" * 20)
            print("--- START SAVE DATA ---")
            
            with open(save_path, 'r') as f:
                # Read the file and print it raw
                print(f.read())
                
            print("--- END SAVE DATA ---")
            print("-" * 20)
            # Pause so the user can copy it
            self.AI_File.parse_choice(["Done"], "Press 'Done' once you have copied the text.")
            
    def main_game_loop(self):
        global player # <-- FIX 1: Add this line
        
        # --- NEW CODE ---
        prompt = "Would you like to Start a New Game or Load a Save?"
        choices = ["Start New Game", "Load a Save"]
        
        # This will show two buttons
        choice_str = self.AI_File.parse_choice(choices, prompt)
        # --- END NEW ---
        if choice_str == "load a save": # Note: parse_choice returns lowercase
            player = self # <-- FIX 2: Add this line
            player = Player.load_game() # This will still use text boxes (for now)
        else:
            print("\nSelect a Season:")
            print("1. Standard (Normal)")
            print("2. The Long Winter (Hard Mode + Winter Events)")
                
            # This parses "1", "2", "standard", or "winter"
            season_choice = self.AI_File.parse_choice(["standard", "winter"], "Choose season:")
                
            if season_choice == "winter":
                self.winter_mode = True
                print("You have chosen The Long Winter. Bundle up...")
                # Optional: Force difficult setting if you want
                # self.difficulty = 'survivalist' 
            else:
                self.winter_mode = False
            player = self # <-- FIX 3: Add this line
            # "Start New Game" path
            print("Would you like the instructions (Yes/No)?")
            Choice = self.AI_File.parse_YN(": ")
            if Choice == "yes":
                print("Welcome to Western Simulator!")
                time.sleep(2,)
                print("In this game you will try and survive the western life and complete quests.")
                time.sleep(2,)
                print("The rules are simple. You chose options that you would like to do. I tell you what happens. If you run out of health, you die.")
                time.sleep(2,)
                
                # --- MODIFICATION START ---
                available_choices = ["adventure", "frontier", "savage"]
                prompt = "Choose a difficulty:"
                

                choice = self.AI_File.parse_choice(available_choices, prompt)
                # 'choice' will be "adventure", "frontier", or "savage"
                
                if choice == "adventure": # <-- Changed from "1"
                    self.difficulty = 'adventure'
                elif choice == "savage": # <-- Changed from "3"
                    self.difficulty = 'savage'
                else: # <-- This now correctly defaults to "frontier"
                    self.difficulty = 'frontier'
                time.sleep(2,)
                print("Certain items are a single use like bread, antivenom, and boots, and provide a one time bonus.")
                time.sleep(2,)
                print("Others like the knife and armor have unlimited uses.")
                time.sleep(2,)
                print("Now let's start your journey.")
                print("(I would recommend going to the gunsmith first, maybe get a revolver and some ammo.)")
                time.sleep(1,)
                Location = ["Dustbowl, a tough town in the South Dakota territory.", 
                            "Rust Ridge, a thriving town in the eastern half of Colorado.", 
                            "Quarry Town, a large mining town on the banks of the Missouri River."]
                print("You wake up in the town of " + Location[random.randint(0,2)])
                print("The people greet you with nods as you walk down the mainstreet.")
                time.sleep(4,)
                self.change_music("Town.mp3", -1)
                self.add_item("diary")
                
            else:
                self.change_music("Town.mp3", -1)
                self.add_item("diary")
                available_choices = ["adventure", "frontier", "savage"]
                prompt = "Choose a difficulty:"
                
                choice = self.AI_File.parse_choice(available_choices, prompt)
                # 'choice' will be "adventure", "frontier", or "savage"
                
                if choice == "adventure": # <-- Changed from "1"
                    self.difficulty = 'adventure'
                elif choice == "savage": # <-- Changed from "3"
                    self.difficulty = 'savage'
                else: # <-- This now correctly defaults to "frontier"
                    self.difficulty = 'frontier'


        while not player.Health <= 0:
            self.tent_used_today = False
            if player.invillage == True:
                player.HostilityFunc()
                player.change_music("Town.mp3", -1)
            else:
                player.change_music("game_theme.mp3", -1)
            player.RunDay()
            if self.has_effect("drunk"):
                print("You suffer from the effects of alcohol, but it slowly wears off.")
                self.Health -= 5
                self.Speed += 1
            self.tick_effects()
            player.counter = 0
            player.Day += 1
            if player.Temporaryspdboost > 0:
                player.Speed -= player.Temporaryspdboost
                player.Temporaryspdboost = 0
            if player.Health <= 0:
                time.sleep(2,)
                player.Death("You have succumbed to your injuries and the harsh conditions of the wild west.")
            player.Hunger = player.Hunger + 2
            print("You feel hungrier...")
            time.sleep(2,)
            if player.Hunger >= 10: 
                print("You are starving! Your body is consuming itself.")
                player.Hunger = 10
                player.Health -= 20
            elif player.Hunger >= 7:
                print("You are very hungry. Find some food soon.")
                player.Health -= 10
                
            if player.poisoned > 0:
                print("You remain poisoned, feeling weak and faint.")
                time.sleep(2,)

            print(f"Your health is: {player.Health}.")
            if player.Health <= 0:
                break
            player.save_game()
            print("Game Saved.")
            prompt = "What would you like to do?"
            choices = ["Continue Playing", "Export Save Data", "Quit"]
            decision = player.AI_File.parse_choice(choices, prompt)
            if decision == "export save data":
                player.export_save()
                print("Continuing your adventure...")
                time.sleep(2)
                
            elif decision == "quit":
                print("Thanks for playing! See you next time.")
                exit()
            else:
                print("Continuing your adventure...")
                time.sleep(4)

    def update_actions(self):
        """
        Builds the self.possibleactions list based on
        whether the player is in a village or not.
        This keeps all action-switching logic in one place.
        """
        if self.invillage:
            # In town: Show town actions + universal actions
            actions = list(self.town_actions)
            if self.town_encounter_available:
                actions.insert(0, "town encounter")
            self.possibleactions = actions + self.universal_actions
        else:
            # Traveling: Show travel actions + universal actions
            self.possibleactions = self.travel_actions + self.universal_actions


    def lose_random_item(self, amount):
        if not self.itemsinventory:
            print("You have no items to lose.")
            return

        item = random.choice(list(self.itemsinventory.keys()))
        self.itemsinventory[item] -= amount
        if self.itemsinventory[item] <= 0:
            del self.itemsinventory[item]
        print(f"You lost 1 {item} from your inventory.")

    def add_item(self, item_name):
        self.itemsinventory[item_name] = self.itemsinventory.get(item_name, 0) + 1
        print(f"You found a {item_name}!")

    def loot_drop(self, item):
        loot = item
        if item in ["winchester barrel", "winchester stock"]:
            print("You found a part for a Winchester rifle!")
            print("You can take it to a blacksmith to assemble it once you get all the parts.")
        if item in ["pistol_ammo", "rifle_ammo", "shotgun_ammo"]:
            self.itemsinventory[item] = self.itemsinventory.get(item, 0) + 3
            print(f"You found 3 x {item}!")
        else:
            self.add_item(loot)
            if self.difficulty == 'adventure' and loot in self.common_loot:
                print(f"You found extra {loot} due to adventure mode!")
                self.add_item(loot)
        self.day_memory["loot"] = item

    def perform_stat_check(self, stat_value, base_target=10):
            """ 
            Performs a stat check against a target, adjusted by game difficulty.
            Returns True for success, False for failure.

            - stat_value: The player's skill (e.g., self.strength_skill).
            - base_target: The inherent difficulty of the task (e.g., 10 for medium).
            """
            roll = random.randint(1, 20)

            # 1. Handle criticals (guarantees a "never 0%" chance)
            if roll == 20:
                return True  # Critical Success (5% chance, always wins)
            if roll == 1:
                return False # Critical Failure (5% chance, always fails)
            
            # 2. Adjust target based on game difficulty
            adjusted_target = base_target
            if self.difficulty == 'adventure':
                adjusted_target -= 2  # Make it easier
            elif self.difficulty == 'savage':
                adjusted_target += 2  # Make it harder
            # 'frontier' uses the base_target as-is

            # 3. Calculate the final score and check
            # We use (stat_value - 3) as the bonus.
            # This makes your starting skill of 3 a "+0" (average) bonus.
            # A skill of 4 is +1. A skill of 2 is -1.
            stat_bonus = stat_value - 3 
            if self.winter_mode:
                roll -= self.cold_penalty
            final_score = roll + stat_bonus
            
            # You can uncomment this for testing:
            # print(f"[Debug: Rolled {roll} + Bonus {stat_bonus} = {final_score} vs Target {adjusted_target}]")
            
            return final_score >= adjusted_target

    def TakeActionsChose(self):
        # This function will now ONLY print the list if USE_OLLAMA is false.
        # If USE_OLLAMA is true, it prints the simple list.
        # Initial prompt
        # Print the numbered list for the first time
        print("\nAvailable Actions:")
        print("\n--- Available Actions ---")
        for action_text in self.possibleactions:
            print(f"{action_text.capitalize()}")
        print(f"Help")
        

        while True:

            parsed = self.AI_File.parse_action(f"Enter a number (1-{len(self.possibleactions) + 1}): ", self.possibleactions)
            action_result = parsed.get('action', 'none')

            # 2. Manual 'help' check (for Ollama mode, or if user types 'help' in numerical)

            # 3. Parse the action
            # AI_File.parse_action will now handle the number-to-action conversion
            # or the text-to-action conversion.
            

            # 4. Handle result
            if action_result in self.possibleactions:
                # if USE_OLLAMA: # We don't need this feedback line anymore
                #     print(f"[{action_result.capitalize()}]") 
                return action_result # Success!
            

            
            else:
                # In Ollama mode, print a generic error
                # if USE_OLLAMA: # We don't need this branch
                #     print("Invalid or unavailable choice. Try again.")
                # In Numerical mode, parse_action already printed the error.
                # We just loop to re-prompt.
                pass

    def generate_game_state(self):
        if self.invillage == True:
            village_part = "Player is in a western village"
        else:
            village_part = "Player is in the western prairy."
        if self.Hostility == 1:
            hostility = f"You are somewhat hostile to the player."
        elif self.Hostility == 2:
            hostility = f"You are very hostile to the player for what they have done in town."
        elif self.Hostility >= 3: 
            hostility = f"You are extremely hostile to the player for what they have done in town."
        else:
            hostility = "You are not hostile to the player."
        game_state = village_part + hostility
        return game_state
    
    def ActionFunction(self, choice):
        match choice:
            case "town jail": 
                self.TownJail()
            case "doctor's office": 
                self.DoctorOffice()
            case "general store": 
                self.GeneralStore()
            case "gunsmith's shop": 
                self.Gunsmiths()
            case "bank": 
                self.Bank()
            case "saloon": 
                self.Saloon()
            case "talk townspeople":
                self.Townspeople()
            case "trading post":
                self.TradingPost()
            case "blacksmith shop":
                self.Blacksmith()
            case "town encounter":
                self.town_encounter()
            case "leave town":
                self.LeaveTown()
            case "use item":
                self.use_item1()
            case "inventory":
                self.Statcheck()
            case "travel road":
                self.Explore()
            case "make camp":
                self.MakeCamp()

            case _:
                print("That action is not currently available.")

    def DoAction(self):
        index = self.TakeActionsChose()
        self.ActionFunction(index)
    
    def use_item1(self):
        self.use_item(combat=False, enemy_name=None, enemy_combatant=None)

    def use_item(self, combat, enemy_name, enemy_combatant):
        if not self.itemsinventory:
            print("Your inventory is empty.")
            return
        use_continue = True
        while use_continue == True:
            print("\nYour Inventory:")
            item_descriptions = {
                "bread": f"Restores 5 health or reduces 1 hunger if you are hungry. Can be used whenever. {self.hunger_check()}",
                "antivenom": "Cures poison if poisoned. Only usable outside of combat.",
                "lantern": "Gives you 1 extra hour of time. Only usable outside of combat.",
                "boots": "Increases travel speed by 1. Only usable outside of combat.",
                "leather armor": "Reduces combat damage taken (90%). Only usable in combat.",
                "chain mail": "Greatly reduces combat damage taken (70%). Only usable in combat.",
                "rope": "Halves the health of animal-type enemies. Only usable in combat.",
                "fire cracker": "Halves health of pack-type enemies and stuns them. Only usable in combat.",
                "rope": "Could be used during events. Only usable outside of combat.",
                "ammo cartridge": "Gives 5 of a given ammo. Usable whenever.",
                "tobacco pouch": "Boosts morale: +5 to your next attack. Only usable in combat.",
                "gun oil":       "Apply to weapon: +5 damage on next attack. Only usable in combat.",
                "coffee tin":    "Drink for a speed boost: +1 travel speed in next combat. Only usable outside of combat.",
                "gold nugget":   "A heavy nugget. Sell for a high price. Only usable outside of combat.",
                "bandit's map":  "Study to reveal a hidden stash. Only usable outside of combat.",
                "diary": "Open your journal and read past entries. Only usable outside of combat.",
                "flashbang": "Can be thrown at enemies. Stuns them for one turn. Only usable in combat.",
                "bandage": f"Heals 25 health. Usable only outside of combat. Health = {self.Health}/{self.MaxHealth}.",
                "field dressing kit": "prevents 50% of next damage. Only usable in combat.",
                "vendetta badge": "A one-time call for help. Summons an echo of the Earp posse for a devastating attack. Only usable in combat.",
                "pendant of recognition": "A memorandom of the vendetta ride. Grants +20 score at the end of the game.",
                "winchester barrel": "Bring it to the blacksmith with a winchester stock to make a winchester rifle.",
                "winchester stock": "Bring it to the blacksmith with a winchester barrel to make a winchester rifle.",
                "whiskey": "Liquid courage. +15 HP, +5 Damage buff. Don't drink too much.",
                "steak": "A large, fire-cooked steak. Huge meal. -5 Hunger, +30 Health.",
                "bourbon roast": "Meat slow-cooked in whiskey. A king's meal. Fully Restores Health & Hunger.",
                "salted pork sandwich": "A hearty sandwich made with salted pork and bread. -2 Hunger, +15 Health.",
            }

            for item, qty in self.itemsinventory.items():
                description = item_descriptions.get(item, "This item can't be used.")
                print(f"{item.capitalize()} (x{qty}) - {description}")
            # --- MODIFICATION START ---
            # Define the list of choices for the parser
            item_list = list(self.itemsinventory.keys())
            choices_for_parser = item_list + ["leave"] # Add "leave" as an explicit choice


            choice = self.AI_File.parse_choice(
                choices_for_parser, 
                "Choose an item to use:"
            )
            # 'choice' is now the item *name* (e.g., "bread") or "leave"

            if choice == "leave": # <-- Changed from "q"
                print("You decided not to use anything.")
                use_continue = False
                break

            # We no longer need the isdigit() check or the index conversion.
            # 'choice' is already the item name.
            selected_item = choice
            if combat == False:
                
                if selected_item == "bread":
                    self.Hunger = self.Hunger - 2
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    print(f"You eat some bread and reduce {2} hunger.")
                
                elif selected_item == "salted pork":
                    self.Hunger = self.Hunger - 4
                    self.Health = min(self.Health + 5, self.MaxHealth)
                    print("The salty meat is tough, but filling. -4 Hunger, +5 Health.")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                
                elif selected_item == "salted pork sandwich":
                    self.Hunger = self.Hunger - 4
                    self.Health = min(self.Health + 15, self.MaxHealth)
                    print("The sandwich is hearty. -4 Hunger, +15 Health.")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "pemmican":
                    self.Hunger = 0 # Fully cures hunger
                    self.Health = min(self.Health + 20, self.MaxHealth)
                    print("You eat the nutrient-dense pemmican. You feel completely full. Hunger cleared.")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                
                elif selected_item == "coffee tin":
                    print("You slam the coffee—your reflexes sharpen!")
                    self.Speed += 1
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    self.Temporaryspdboost = 1

                elif selected_item == "antivenom":
                    if self.poisoned > 0:
                        print(f"You use the antivenom.")
                        self.itemsinventory[selected_item] -= 1
                        if self.itemsinventory[selected_item] <= 0:
                            del self.itemsinventory[selected_item]
                        self.poisoned -=1
                        if self.poisoned > 0:
                            print(f"Your poison level has decreased to {self.poisoned}.")
                        else:
                            print(f"You are no longer poisoned.")
                    else:
                        print("You are not poisoned, and cannot use this.")
            
                elif selected_item == "diary":
                    self.read_diary_day()

                elif selected_item == "ammo cartridge":
                    # --- MODIFICATION START ---
                    # Let player choose which ammo to receive
                    prompt = "Which ammo type would you like?"
                    available_choices = ["Pistol Ammo", "Rifle Ammo", "Shotgun Ammo"]
                    
                    choice = self.AI_File.parse_choice(available_choices, prompt)
                    # 'choice' will be "pistol ammo", "rifle ammo", or "shotgun ammo"
                    
                    if choice == "pistol ammo":
                        ammo = "pistol_ammo"
                    elif choice == "rifle ammo":
                        ammo = "rifle_ammo"
                    elif choice == "shotgun ammo":
                        ammo = "shotgun_ammo"
                    else:
                        print("Invalid selection. No ammo granted.")
                        return
                    # Grant 5 of the chosen ammo
                    self.itemsinventory[ammo] = self.itemsinventory.get(ammo, 0) + 5
                    # Consume the cartridge
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                    print(f"You open the ammo cartridge and receive 5 x {ammo}.")

                elif selected_item == "lantern":
                    print("You decide to use your lantern, and it allows you an extra hour to work with.")
                    self.Time = self.Time - 2
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "boots":
                    if self.boots_used == False:
                        print("You put on you boots, you feel faster. +1 speed")
                        self.Speed += 1
                        self.itemsinventory[selected_item] -= 1
                        if self.itemsinventory[selected_item] <= 0:
                            del self.itemsinventory[selected_item]
                        self.boots_used = True
                    else:
                        print("You are already wearing boots, another pair won't help.")

                elif selected_item == "bandage":
                    heal_amount = 25
                    self.Health = min(self.Health + heal_amount, self.MaxHealth)
                    print(f"You apply the bandage. You regain {heal_amount} health.")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]


                elif selected_item == "whiskey":
                    print("You take a long swig of the burning liquid.")
                    self.Health = min(self.Health + 15, self.MaxHealth)
                    self.damage_modifier += 5 # "Liquid Courage" buff for next fight
                    self.add_effect("drunk", duration=1)
                    
                    # Small chance to get "drunk" (slow)
                    if random.randint(1, 10) == 1:
                        print("You feel a bit woozy... -1 Speed.")
                        self.Speed = max(1, self.Speed - 1)
                    else:
                        print("You feel warm and ready for a fight. (+15 HP, +5 Dmg)")

                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0: del self.itemsinventory[selected_item]

                elif selected_item == "steak":
                    self.Hunger = max(0, self.Hunger - 5)
                    self.Health = min(self.Health + 30, self.MaxHealth)
                    print("You devour the steak. It is delicious. (-5 Hunger, +30 Health)")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0: del self.itemsinventory[selected_item]

                elif selected_item == "bourbon roast":
                    self.Hunger = 0
                    self.Health = self.MaxHealth
                    self.damage_modifier += 10 
                    print("The flavor is incredible. You feel invincible! (Full Restore + Damage Buff)")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0: del self.itemsinventory[selected_item]
                else:
                    print(f"You can't use {selected_item} right now.")
    
            else:
                if selected_item == "bread":
                    heal_amount = 5
                    self.Health = min(self.Health + heal_amount, self.MaxHealth)
                    print(f"You eat some bread and restore {heal_amount} health.")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "gun oil":
                    print("You carefully oil your firearm.")
                    print("Your next attack will deal extra damage.")
                    self.dmg_modifier_multiply = 1.25
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "whetstone":
                    print("You run the whetstone along your melee weapon, sharpening it to a razor edge.")
                    print("Your next melee attack will deal extra damage.")
                    self.add_effect("sharpened_blade")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "tobacco pouch":
                    print("You puff on the tobacco pouch and feel emboldened.")
                    print("You will be faster and stronger in the fight to come. +1 damage, +1 speed")
                    self.damage_modifier += 5
                    self.Temporaryspdboost += 1
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "rope":
                    if combat and enemy_combatant:
                        old_hp = enemy_combatant["health"]
                        enemy_combatant["health"] = max(1, enemy_combatant["health"] // 2)
                        print(f"You used the rope! The {enemy_name}'s health is halved from {old_hp} to {enemy_combatant['health']}!")
                        self.itemsinventory[selected_item] -= 1
                        if self.itemsinventory[selected_item] <= 0:
                            del self.itemsinventory[selected_item]
                    else:
                        print("You can only use the rope during combat.")

                elif selected_item == "fire cracker":
                    if combat and enemy_combatant and enemy_combatant.get("type") == "pack":
                        print(f"You used the fire cracker! The {enemy_name}'s health is halved!")
                        print(f"They are much more disorganized.")
                        self.add_effect("stun", target="enemy")
                        self.add_effect("hphalf", target="enemy")
                        time.sleep(2,)
                        self.itemsinventory[selected_item] -= 1
                        if self.itemsinventory[selected_item] <= 0:
                            del self.itemsinventory[selected_item]
                    else:
                        print("The fire cracker has no effect on this enemy.")

                elif selected_item == "leather armor":
                    print("Your durability has increased.")
                    self.Armor_Boost = 0.9

                elif selected_item == "chain mail":
                    print("Your durability has increased significantly.")
                    self.Armor_Boost = 0.7

                elif selected_item == "ammo cartridge":
                    # --- MODIFICATION START ---
                    # Let player choose which ammo to receive
                    prompt = "Which ammo type would you like?"
                    available_choices = ["Pistol Ammo", "Rifle Ammo", "Shotgun Ammo"]
                    
                    choice = self.AI_File.parse_choice(available_choices, prompt)
                    # 'choice' will be "pistol ammo", "rifle ammo", or "shotgun ammo"
                    
                    if choice == "pistol ammo":
                        ammo = "pistol_ammo"
                    elif choice == "rifle ammo":
                        ammo = "rifle_ammo"
                    elif choice == "shotgun ammo":
                        ammo = "shotgun_ammo"
                    else:
                        print("Invalid selection. No ammo granted.")
                        return
                    # Grant 5 of the chosen ammo
                    self.itemsinventory[ammo] = self.itemsinventory.get(ammo, 0) + 5
                    # Consume the cartridge
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                    print(f"You open the ammo cartridge and receive 5 x {ammo}.")

                elif selected_item == "flashbang":
                    print("You throw the stun bomb! It explodes in a flash and bang!")
                    self.add_effect("stun", target="enemy")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    print(f"The {enemy_name} is stunned!")

                elif selected_item == "field dressing kit":
                    print("You quickly apply a field dressing, bracing for the next attack.")
                    self.add_effect("half_incoming_damage")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                elif selected_item == "vendetta badge":
                    print("\nYou hold the badge high. You hear the thunder of hooves and a volley of gunfire rings out!")
                    self.add_effect("posse_help")
                else:
                    print(f"You can't use {selected_item} right now.")
                    time.sleep(2,)
                                
            time.sleep(2,)

    def Statcheck(self):
        print(f"You are on day {self.Day}.")
        print(f"Shadow skill: {self.shadow_skill}.")
        print(f"Strength skill: {self.strength_skill}.")
        print(f"Trail skill: {self.trail_skill}.")
        print(f"Max health: {self.MaxHealth}")
        if "surveyor's kit" in self.itemsinventory:
            print(f"[Surveyor's Kit] {self.distancenext} miles to next town.")
        print(f"It is {self.Time}:00 o'clock.")
        print(f"You have {self.gold} gold in your pouch.")
        print("Your inventory contains:")
        if self.itemsinventory:
            for item, count in self.itemsinventory.items():
                print(f" - {item}: {count}")
        else:
            print(" - (empty)")
        #print(f"Your role is {self.active_role.name.capitalize()} (XP: {self.active_role.xp}).")
        print(self.hunger_check())
        print(f"Your health is {self.Health}.")
        self.AI_File.parse_choice(["Continue"], "Press Enter to continue:")

    def hunger_check(self):
            if self.Hunger >= 9:
                return "You are starving to death."
            elif self.Hunger >= 7:
                return "You are ravenously hungry. You feel weak."
            elif self.Hunger >= 4:
                return "Your stomach is growling."
            elif self.Hunger > 0:
                return "You could eat."
            else:
                return "You are well fed."

    def TownJail(self):
        print("You walk into the town jail.")
        print("The sheriff greets you.")
        print("Would you like to: ")
        print("Pay a fine to reduce hostility.")
        print("Return a criminal or loot to the sheriff.")
        print("Ask the sheriff about rumors.")
        print("Ask the sheriff to teach you some skills.")
        print("Leave the jail.")
        available_choices = ["pay fine", "return criminal", "ask rumors", "teach skills", "leave"]
        choice = self.AI_File.parse_choice(available_choices, "Enter your choice: ")
        if choice == "pay fine":
            if self.Hostility > 0:
                fine = self.Hostility * 5
                print(f"The sheriff says, 'Your current hostility level is {self.Hostility}.")
                print(f"To reduce it, you need to pay a fine of ${fine}.")
                if self.gold >= fine:
                    self.gold -= fine
                    self.Hostility = 0
                    print(f"You paid the fine. Your hostility is now reduced to {self.Hostility}.")
                else:
                    print("You don't have enough gold to pay the fine.")
            else:
                print("You have no hostility towards the town.")
        elif choice == "return criminal":
            if "outlaw" in self.caravan:
                print("You turn in the outlaw you captured.")
                print("The sheriff approaches you.")
                prompt = "How can we reward you for bringing in this outlaw?"
                available_choices = ["Gold", "Supplies"]
                
                choice = self.AI_File.parse_choice(available_choices, prompt)
                if choice == "gold": # <-- Changed from "1"
                    reward = random.randint(20, 40)
                    self.gold += reward
                    print(f"The sheriff thanks you and gives you {reward} gold as a reward.")
                else: # <-- This now handles "supplies"
                    supply = random.choice(self.rare_loot)
                    self.add_item(supply)
                    print(f"The sheriff thanks you and gives you some supplies: {supply}.")
            else:
                print("You have no criminals to turn in.")
        elif choice == "ask rumors":
            if "sheriff_rumor" not in self.rumors_heard:
                self.rumors_heard.append("sheriff_rumor")
                rumor_topics = {
                "bandits_coyote_camp": "People have been being robbed by coyote pass, somethings not right there.",
                "old_mine_lights": "Nobody goes near the old mine anymore.",
                "earp_vendetta": "I don't tell anybody this, but go to the saloon, Wyatt Earp is looking for help in the saloon.",
                }
                topic, rumor = random.choice(list(rumor_topics.items()))
                print(f"The sheriff murmurs: \"{rumor}\"")
                self.rumors[topic] = self.rumors.get(topic, 0) + 1
                print(f"[Rumor about '{topic.replace('_',' ').capitalize()}' added! Heard {self.rumors[topic]} times.]")
                # Example: trigger a quest after hearing a rumor 2 times
                if self.rumors[topic] == 2:
                    if topic == "earp_vendetta":
                        self.rumors["earp_rumor"] = 1 # Set the flag
                        print("\n[Quest Update] You can now approach Wyatt Earp in the Saloon.")
                    print(f"A new quest is now available: {topic.replace('_',' ').capitalize()}!")
                    print("Would you like to accept this quest? (will replace your current town quest if any) (yes/no)")
                    if self.AI_File.parse_YN(": ") == "yes":
                        self.Tquest = topic
                        print(f"You have accepted the quest: {topic.replace('_',' ').capitalize()}!")
                    else:
                        print("You declined the quest for now.")
            time.sleep(2)

        elif choice == "teach skills":
            print("The sheriff can teach you some skills.")
            print("Choose a skill to learn:")
            print(f"Shadow Skill - Improves stealth and tracking. Current: {self.shadow_skill}")
            print(f"Strength Skill - Improves combat effectiveness. Current: {self.strength_skill}")
            print(f"Trail Skill - Improves navigation and survival. Current: {self.trail_skill}")
            print(f"Durability Skill - Improves max Health. Current: {self.MaxHealth}")
            available_choices = ['durability', 'trail', 'strength', 'shadow']
            skill_choice = self.AI_File.parse_choice(available_choices, "Enter your choice: ")
            if skill_choice == "shadow":
                gold = (self.shadow_skill - 2) * 5
                if gold > self.gold:
                    print("You don't have enough gold.")
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    self.shadow_skill += 1
                    print("Your shadow skill has improved! +1 shadow skill.")
                    self.gold -= gold
                else:
                    print("You decided not to pay for the lesson.")
            elif skill_choice == "trail":
                gold = self.trail_skill * 5
                if gold > self.gold:
                    print("You don't have enough gold.")
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    self.trail_skill += 1
                    print("Your trail skill has improved! +1 trail skill.")
                    self.gold -= gold
                else:
                    print("You decided not to pay for the lesson.")
            elif skill_choice == "strength":
                gold = (self.strength_skill - 2) * 5
                if gold > self.gold:
                    print("You don't have enough gold.")
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    self.strength_skill += 1
                    print("Your strength skill has improved! +1 strength skill.")
                    self.gold -= gold
                else:
                    print("You decided not to pay for the lesson.")
            elif skill_choice == "durability":
                gold = (self.MaxHealth-95)/5 * 5
                if gold > self.gold:
                    print("You don't have enough gold.")
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    self.MaxHealth += 5
                    print("Your durability skill has improved! +5 max Health.")
                    self.gold -= gold
                else:
                    print("You decided not to pay for the lesson.")
            else:
                print("Invalid choice.")
            
        elif choice == "leave":
            print("You leave the jail.")

    def TradingPost(self):
        if not self.itemsinventory:
            print("You don't have any items to trade or sell.")
            return

        # Define the data here, but pass the logic to the session
        sell_prices = {
            "small hide": 12, "medium hide": 20, "large hide": 40,
            "small meat": 12, "medium meat": 20, "large meat": 40,
            "horn": 45, "bread": 2, "knife": 5,
            "revolver": 15, "colt pistol": 20, "sharps rifle": 40,
            "rifle": 15, "shotgun": 25,
            "pistol_ammo": 1, "rifle_ammo": 2, "shotgun_ammo": 3,
            "winchester rifle": 50, "carved horn": 40,
            "gold nugget": random.randint(15, 45),
            "silver watch": random.randint(10, 20),
            "silver bar": random.randint(40, 60),
            "gold bar": random.randint(45, 100)
        }

        trade_offers = [
            {"give": "winchester barrel", "get": "winchester stock"},
            {"give": "winchester stock", "get": "winchester barrel"},
            {"give": "gold nugget", "get": "field dressing kit"},
            {"give": "medium hide", "get": "bandage"},
            {"give": "shotgun_ammo", "get": "rifle_ammo"},
        ]
        price_mult = 1.25 if self.winter_mode else 1.0
        if self.winter_mode: 
            print("Trader: 'I pay extra for furs in this cold.'")
            sell_prices = {
                "small hide": int(12 * price_mult), 
                "medium hide": int(20 * price_mult), 
                "large hide": int(40 * price_mult),
                "small meat": 12, "medium meat": 20, "large meat": 40,
                "horn": 45, "bread": 2, "knife": 5,
                "revolver": 15, "colt pistol": 20, "sharps rifle": 40,
                "rifle": 15, "shotgun": 25,
                "pistol_ammo": 1, "rifle_ammo": 2, "shotgun_ammo": 3,
                "winchester rifle": 50, "carved horn": 40,
                "gold nugget": random.randint(15, 45),
                "silver watch": random.randint(10, 20),
                "silver bar": random.randint(40, 60),
                "gold bar": random.randint(45, 100)
            }
        # We don't need a buy inventory, so we pass an empty dict {}
        trader_session = ShopSession(self, self.AI_File, "Trading Post", {}, "Trader")

        # Call our new, specialized method!
        trader_session.run_trade_session(sell_prices, trade_offers)

    def Blacksmith(self):
        self.play_sound("store_bell.mp3")
        print("You walk into the blacksmith.")
        print("The smith gives you a nod.")
        base_level = self.TownUpgrades["blacksmith"]["level"]
        effective_level = base_level
        if "Fort" in self.current_town_name or "Ridge" in self.current_town_name:
            effective_level += 1
            print("The blacksmith's shop is more advanced due to the town's fortifications.")
        print(f"The blacksmith's current upgrade level is {effective_level}.")
        if "winchester barrel" in self.itemsinventory and "winchester stock" in self.itemsinventory:
            print("You have the parts to assemble a Winchester rifle.")
            print("Would you like to assemble it now? (yes/no)")
            choice = self.AI_File.parse_YN(": ")
            if choice == "yes":
                self.itemsinventory.pop("winchester barrel")
                self.itemsinventory.pop("winchester stock")
                self.add_item("winchester rifle")
                print("You have assembled a Winchester rifle!")
        time.sleep(2,)


        item_prices = {
            'boots': 15,
            'leather armor': 35,
            'chain mail': 75,
            'whetstone': 20,  # Our new item
            'gun oil': 7,
        }

        # Build the list of available items based on the effective level
        available_items = ['boots']
        if effective_level >= 1:
            available_items.append('leather armor')
            available_items.append('gun oil')
        if effective_level >= 2:
            available_items.append('chain mail')
        if effective_level >= 3:
            available_items.append('whetstone') # Whetstone is a level 3+ item

        # Create the final inventory dict for the ShopSession
        shop_inventory = {}
        for name in available_items:
            # Use a default quantity of 5 for this example
            shop_inventory[name] = ShopItem(name, item_prices[name], 5)
        BlacksmithShop = ShopSession(self, self.AI_File, "Blacksmith Shop", shop_inventory, "Blacksmith")
        BlacksmithShop.run_buy_session()

    def DoctorOffice(self):
        self.play_sound("store_bell.mp3")
        print("You enter the doctor's office. The doctor greets you with a friendly smile.")
        time.sleep(2,)
        print("The doctor takes your physical.")
        if self.Health >= 100:
            print(f"'You are in great health!' the doctor exclaims.")
            print(f"'Your health is {self.Health}.")
        elif self.Health >= 75:
            print(f"'You are in good health.' the doctor announces.")
            print(f"'Your health is {self.Health}.")
        elif self.Health >= 50:
            print(f"'You are slightly injured.' the doctor says.")
            print(f"'Your health is {self.Health}.")
        elif self.Health >= 25:
            print(f"'You are very injured.' the doctor worries.")
            print(f"'Your health is {self.Health}.")
        elif self.Health > 0:
            print(f"'You are extremely injured and need immediate medical attention.' the doctor worries.")
            print(f"'Your health is {self.Health}.")
        Heal = self.MaxHealth - self.Health
        cost = (Heal)/4
        if cost > 75:
            cost = 75
        cost = round(cost)
        print("'Would you like me to heal you?' Yes/No")
        print(f"It will cost you {cost}.")
        Choice = self.AI_File.parse_YN(": ")
        if Choice == "yes":
            if self.gold >= cost:
                self.gold -= cost
                print(f"You were healed {Heal}")
                self.Health = self.MaxHealth
            else:
                print("You do not have enough gold.")
            time.sleep(2,)
        doctor_inventory = {
            # Use ShopItem('name', base_price, quantity)
            'bandage': ShopItem('bandage', 10, 5),
            'field dressing kit': ShopItem('field dressing kit', 20, 5),
            'antivenom': ShopItem('antivenom', 10, 5),
        }

        doc_shop = ShopSession(self, self.AI_File, "Doctor's Supply Store", doctor_inventory, "Doctor")
        doc_shop.run_buy_session() # Call the new method
        print("You leave the Doctor's Office.")

    def Gunsmiths(self):
        self.play_sound("store_bell.mp3")
        print("You enter the gunsmith.")
        print("The gunsmith greets you with a nod. Guns line the walls.")
        time.sleep(2,)

        available_weapons = ["revolver", "rifle", "shotgun", "knife"]
        if self.TownUpgrades["gunsmith"]["level"] >= 2:
            available_weapons.append("sawed-off shotgun")
            available_weapons.append("lever-action rifle")
        if self.TownUpgrades["gunsmith"]["level"] >= 3:
            available_weapons.append("henry rifle")
            available_weapons.append("remington pistol")
        if self.TownUpgrades["gunsmith"]["level"] >= 4:
            available_weapons.append("winchester rifle")
            available_weapons.append("double barrel shotgun")

        # Create inventory using ShopItem
        inventory = {}
        for name in available_weapons:
            if name in weapons_data:
                info = weapons_data[name]
                inventory[name] = ShopItem(name, info['price'], 3) # default quantity 3

        # Add ammo separately:
        inventory.update({
            'pistol_ammo': ShopItem('pistol_ammo', 2, 50),
            'rifle_ammo': ShopItem('rifle_ammo', 3, 30),
            'shotgun_ammo': ShopItem('shotgun_ammo', 5, 10),
        })

        GunsmithStore = ShopSession(self, self.AI_File, "Gunsmith", inventory, "Gunsmith")
        GunsmithStore.run_buy_session()

    def Bank(self):
            print("You walk into the Bank. The air smells of leather and dust.")
            print("What town building would you like to invest in?")

            # 1. Define buildings and their upgrade prices in a dictionary
            buildings_to_upgrade = {
                "general store": self.TownUpgrades["general store"]["level"] * 10,
                "blacksmith": self.TownUpgrades["blacksmith"]["level"] * 10,
                "gunsmith": self.TownUpgrades["gunsmith"]["level"] * 10,
            }

            # 2. Create the list of valid choices for the parser
            # We add "leave" so the parser knows it's a valid option.
            available_choices = list(buildings_to_upgrade.keys()) + ["leave"]

            # 3. Display the options to the user
            # The parse_choice function will handle numbering if USE_OLLAMA is False
            print("\n--- Town Investments ---")
            for building, price in buildings_to_upgrade.items():
                current_level = self.TownUpgrades[building]['level']
                # This text will be shown in both modes
                print(f"{building.capitalize()} (Level {current_level}) - Price to upgrade: {price} gold.")
            

            # Pass the full list, including "leave", to the parser
            choice = self.AI_File.parse_choice(available_choices, "Choice: ")

            # Pass the full list, including "leave", to the parser
            choice = self.AI_File.parse_choice(available_choices, "Choice: ")

            # 5. Handle the parsed choice
            if choice == "leave":
                print("You decide not to invest right now and leave the bank.")
                return

            # Check if the choice is a valid building (it should be, if not 'leave')
            if choice in buildings_to_upgrade:
                price_to_pay = buildings_to_upgrade[choice]

                # Check affordability
                if self.gold < price_to_pay:
                    print("You check your coin purse. You cannot afford that investment.")
                    return
                
                # Process the upgrade
                self.gold -= price_to_pay
                self.TownUpgrades[choice]["level"] += 1
                
                # Get new level for confirmation message
                new_level = self.TownUpgrades[choice]["level"]
                new_price = new_level * 10 # Calculate the *next* price
                
                print(f"\nYou paid {price_to_pay} gold.")
                print(f"The {choice.capitalize()} has been upgraded to Level {new_level}!")
                print(f"(The next upgrade will cost {new_price} gold.)")
            
            else:
                # This case should rarely happen if parse_choice is working, but it's safe
                print(f"Invalid choice '{choice}'. Leaving the bank.")
                return

    def Armory(self):
        print("You enter the Armory, a shattered house on the edge of town.")
        print("A gruff soldier nods at you as you step inside.")
        time.sleep(2)
        print("You may choose two actions before the coming fight.")

        for i in range(2):
            print(f"\n--- Choice {i+1}/2 ---")
            
            # --- MODIFICATION START ---
            prompt = f"What would you like to do? (Choice {i+1}/2)"
            available_choices = ["Heal to full health", "Buy ammo", "Get supplies"]
            
            choice = self.AI_File.parse_choice(available_choices, prompt)
            # 'choice' will be the lowercase string of the selected option
            
            if choice == "heal to full health":
                self.Health = self.MaxHealth
                print(f"You are fully healed. Health is now {self.Health}.")
            elif choice == "buy ammo":
                ammo_inventory = {
                    'pistol_ammo': ShopItem('pistol_ammo', 2, 10),
                    'rifle_ammo': ShopItem('rifle_ammo', 3, 10),
                    'shotgun_ammo': ShopItem('shotgun_ammo', 5, 10)
                }
                print("The quartermaster unlocks an ammo crate for you.")
                # Note: Updated to use USE_OLLAMA to match your current Store class
                ammo_shop = ShopSession(self, self.AI_File, "Armory Ammo Shop", ammo_inventory, "Quartermaster")
                ammo_shop.run_buy_session()
            elif choice == "get supplies":
                print("The armory clerk hands you a crate of supplies...")
                loot = random.choice(["colt pistol", "revolver", "bandage", "ammo cartridge", "bread", "rope"])
                self.loot_drop(loot)
                time.sleep(1)
            else:
                print("You decided to do nothing.")
            # --- MODIFICATION END ---
            
            time.sleep(1)

        print("\nYou step out of the Armory, ready for what comes next.")

    def Saloon(self):
        self.play_sound("saloon door.mp3")
        print("You push open the swinging saloon doors.")
        print("The saloon is alive with music and conversation.")
        self.change_music("Saloon_music.mp3", -1)
        time.sleep(1)
        
        # Random flavor event (Brawls, cards, etc.)
        self.saloon_entry_event()

        # Allow multiple interactions
        for i in range(max(3-self.counter, 0)):
            self.counter += 1
            
            # --- 1. Base Menu Options ---
            available_choices = [
                "Talk to the barkeeper",
                "Sing a drinking song", 
                "Talk to the patrons",
                "Leave the bar"
            ]
            quest_options = None
            if not self.quest_today:
                quest_options = self.process_quest_triggers("saloon", is_menu_option=True)
            # --- 2. Dynamic Quest Wiring ---
            # Ask the database: "Are there any buttons for the Saloon right now?"
            if not self.quest_today:
                quest_options = self.process_quest_triggers("saloon", is_menu_option=True)
            quest_map = {}
            
            # If we got a list of quests back, add them as buttons
            if isinstance(quest_options, list):
                for q in quest_options:
                    btn_text = q['description']
                    # Add to the top of the list so they are seen first
                    available_choices.insert(0, btn_text)
                    # Map the lowercase text to the quest object for lookup
                    quest_map[btn_text.lower()] = q
            
            # --- 3. Get User Choice ---
            prompt = "\nWhat would you like to do?"
            # parse_choice typically returns the choice as a lowercase string
            choice = self.AI_File.parse_choice(available_choices, prompt)

            # --- 4. Handle Quest Buttons ---
            if choice in quest_map:
                selected_quest = quest_map[choice]
                # Run the specific function (e.g., encounter_iron_intro)
                method_to_call = getattr(self, selected_quest["function"])
                method_to_call()
                
                # If the quest state changed (e.g. you accepted a quest), 
                # break the loop to refresh the game state/menu
                if self.Tquest != "None": 
                    break 
                continue

            # --- 5. Handle Standard Options ---
            if choice == "talk to the barkeeper":
                self.saloon_barkeeper()
            elif choice == "sing a drinking song":
                self.saloon_song()
            elif choice == "talk to the patrons":
                self.saloon_patrons()
            else: # Leave the bar
                print("You decide to just watch the crowd for a while.")
                break
            
            time.sleep(1)
            
        print("You have gathered all new information.")
        self.change_music("Town.mp3", -1)

    def saloon_entry_event(self):
        roll = random.randint(1,7)
        if roll == 1:
            print("A brawl erupts in the corner—chairs fly as punches land.")
            combat = Combat(self)
            combat.FindAttacker("brawler")
            combat.Attack()
            
        elif roll == 2:
            if "coin" in self.event:
                print("The saloon is lively, but nothing new catches your attention.")
                return
            print("A heated card game ends abruptly; someone storms out in a rage.")
            print("A coin rolls toward you and you pick it up. +5 gold.")
            self.gold += 5
            self.event.append("coin")
        elif roll == 3:
            print("A piano player strikes up a ragtime tune; toes tap in time.")
        elif roll == 4:
            if "drink" in self.event:
                print("The saloon is lively, but nothing new catches your attention.")
                return
            print("A drunk cowboy staggers over and offers you a swig of whiskey. (yes/no)")
            ans = self.AI_File.parse_YN(": ")
            if ans == "yes":
                if random.randint(1,10) >= 9:
                    print("The whiskey was spoiled! You feel ill.")
                    self.poisoned = 1
                else:
                    print("You feel a warm buzz. +5 health.")
                    print("You feel faster. +1 speed.")
                    self.Temporaryspdboost += 1
                    self.Health = min(self.Health + 5, self.MaxHealth)

        elif roll == 5 or roll == 6: # Add a new chance for the quest intro
            if self.Tquest == "None" and "earp_vendetta" not in self.quests_done:
                self.encounter_earp_intro()
            else:
                # Just flavor text if you already did it or have another quest
                print("The saloon is rowdy tonight.")

        elif roll == 7:
            if self.Tquest == "None" and "iron_tracks" not in self.quests_done:
                self.encounter_iron_intro()

        else:
            print("Lot's of people gather around the saloon's door and inside.")

    def saloon_barkeeper(self):
            print("\nThe barkeeper polishes a glass and nods.")
            
            # --- MODIFICATION START ---
            # Define the choices for the buttons
            # I included the cost in the button text so the player knows before clicking
            available_choices = ["Ask about rumors", "Buy a drink (5 gold)"]
            
            choice = self.AI_File.parse_choice(available_choices, "What would you like to do?")
            # choice will be the lowercase string of the button clicked

            if choice == "ask about rumors": # <-- Changed from "1"
                if "barkeeper_rumor" not in self.rumors_heard:
                    self.rumors_heard.append("barkeeper_rumor")
                    rumor_topics = {
                    "bandits_coyote_camp": "People have been being robbed by coyote pass, somethings not right there.",
                    "old_mine_lights": "Nobody goes near the old mine anymore.",
                    "railroad_job": "The Railroad Foreman is in the back. He's looking for hired guns.",
                    }
                    # Fix: Initialize topic and rumor properly before use
                    topic, rumor = random.choice(list(rumor_topics.items()))
                    
                    print(f"The barkeeper murmurs: \"{rumor}\"")
                    self.rumors[topic] = self.rumors.get(topic, 0) + 1
                    print(f"[Rumor about '{topic.replace('_',' ').capitalize()}' added! Heard {self.rumors[topic]} times.]")
                    
                    # Example: trigger a quest after hearing a rumor 2 times
                    if self.rumors[topic] == 2:
                        print(f"A new quest is now available: {topic.replace('_',' ').capitalize()}!")
                        self.quest.append(topic)
                else:
                    print("Unfortunately, the barkeeper has no new rumors for you.")
                
                # Ensure this flag is added (it was in your original code, seemingly outside the 'if' but logic suggests it marks the interaction)
                if "barkeeper_rumor" not in self.rumors_heard:
                    self.rumors_heard.append("barkeeper_rumor")
                time.sleep(2)

            elif choice == "buy a drink (5 gold)": # <-- Changed from "2"
                if self.gold >= 5:
                    self.gold -= 5
                    print("You pay 5 gold and down a shot. +5 health.")
                    print("You feel a warm buzz, and faster. +1 speed.")
                    self.Health = min(self.Health + 5, self.MaxHealth)
                    self.Temporaryspdboost += 1
                else:
                    print("You check your pouch—you don't have enough gold.")

            else:
                print("He shrugs: \"Suit yourself.\"")
            # --- MODIFICATION END ---

    def saloon_song(self):
        print("\nYou stand and clear your throat to sing...")
        time.sleep(1)
        self.Time += 1
        print("Your voice rings out over the crowd; they cheer!")
        # decrease town hostility
        if self.Hostility > 0:
            self.Hostility -= 1
            print("The townsfolk warm to you. -1 Hostility.")
        # chance of free drink
        if random.randint(1,10) <= 3:
            print("The barkeeper is impressed and slides you a free drink. +5 health.")
            print("You feel a warm buzz, and faster. +1 speed.")
            self.Health = min(self.Health + 5, self.MaxHealth)
            self.Temporaryspdboost += 1
        # small chance of brawl
        elif random.randint(1,10) <= 2:
            print("A drunk patron doesn't like your song and swings at you!")
            combat = Combat(self)
            combat.FindAttacker("brawler")
            combat.Attack()
        self.saloon_steal_attempt()
    
    def saloon_steal_attempt(self):
        print("\nYou notice the crowd is enthralled by the music... could be your chance to steal something.")
        choice = self.AI_File.parse_YN("Would you like to attempt to steal? (yes/no): ")
        if choice == "yes":
            # Determine success based on shadow skill

            print("You try and sneak something from the townspeople.")
            if self.perform_stat_check(self.shadow_skill, base_target=12):
                loot = random.choice(["pouch of gold", "silver watch", "pistol_ammo", "bread"])
                if loot == "pouch of gold":
                    gold_stolen = random.randint(5, 15)
                    self.gold += gold_stolen
                    print(f"You slip a pouch of gold from an unwatched belt. +{gold_stolen} gold.")
                else:
                    self.add_item(loot)
                    print(f"You sneak a {loot} from an unsuspecting patron.")
            else:
                print("'What you doin in his belt?' the sheriff asks raising an eyebrow.")
                self.Hostility += 1
                print("'We can do this the easy way, or the hard way.'")
                print("'Surrender, or I make you.'")
                print("Will you surrender? (yes/no)")
                Choice = self.AI_File.parse_YN(": ")
                if Choice == "yes":
                    print("You surrender to the sheriff, and he takes you to the Town Jail.")
                    self.jail_penalty()

                else:
                    combat = Combat(self)
                    combat.FindAttacker("sheriff")
                    combat.Attack()
                    if self.Health <= 0:
                        print("The sheriff revives you.")
                        self.Health += 50
                        self.Hostility += 1
                        self.jail_penalty()
                    print("The sheriff falls, the entire town glares at you.")
                    self.Hostility += 2
                
        else:
            print("You decide against the risk and keep singing.")

    def saloon_patrons(self):
            print("\nYou join a group of patrons at a table.")
            
            # --- MODIFICATION START ---
            available_choices = [
                "Gather gossip", 
                "Play cards (gamble)", 
                "Arm-wrestling contest"
            ]
            
            choice = self.AI_File.parse_choice(available_choices, "What would you like to do?")
            # choice is now a lowercase string

            if choice == "gather gossip": # <-- Changed from "1"
                if "patron_rumor" not in self.rumors_heard:

                    self.rumors_heard.append("patron_rumor")
                    rumor_topics = {
                    "bandits_coyote_camp": "People have been being robbed by coyote pass, somethings not right there.",
                    "old_mine_lights": "Nobody goes near the old mine anymore.",
                    }
                    # Ensure topic/rumor variables are defined inside the scope or earlier
                    topic, rumor = random.choice(list(rumor_topics.items()))
                    print(f"A patron murmurs: \"{rumor}\"")
                    self.rumors[topic] = self.rumors.get(topic, 0) + 1
                    print(f"[Rumor about '{topic.replace('_',' ').capitalize()}' added! Heard {self.rumors[topic]} times.]")
                    # Example: trigger a quest after hearing a rumor 2 times
                    if self.rumors[topic] == 2:
                        print(f"A new quest is now available: {topic.replace('_',' ').capitalize()}!")
                        self.quest.append(topic)
                else:
                    print("They shrug: \"We'll let you know if something happens.\"")
                time.sleep(2)

            elif choice == "play cards (gamble)": # <-- Changed from "2"

                bet = input("Enter bet amount: ").strip()
                
                if bet.isdigit() and int(bet) > 0 and int(bet) <= self.gold:
                    bet = int(bet)
                    self.gold -= bet

                    if self.perform_stat_check(self.shadow_skill, base_target=16):
                        winnings = bet + 10 + bet//2
                        self.gold += winnings
                        print(f"You win! You gain {winnings} gold.")
                    else:
                        print("You lose the hand and your bet.")
                        print("If you had been more stealthy, you might have won.")
                else:
                    print("Invalid bet.")

            elif choice == "arm-wrestling contest": # <-- Changed from "3"
                print("You grip a burly patron's hand and push...")
                if self.perform_stat_check(self.strength_skill, base_target=13) == True:
                    prize = 5
                    print(f"You win the arm-wrestle! +{prize} gold.")
                    self.gold += prize
                else:
                    print("You lose and take a punch. -5 health.")
                    print("If you had been stronger, you might have won.")
                    self.Health -= 5
            
            else:
                print("No one notices your hesitation.")
            # --- MODIFICATION END ---
                
            time.sleep(2)

    def Townspeople(self):
        if self.Hostility >= 3:
            print("The townspeople are hostile and refuse to talk to you.")
        print(f"You chat with a few townsfolk.")
        time.sleep(1)
        self.counter += 1
        if self.counter >= 4:
            print("You've chatted for a while; there are no new conversations right now.")
            return

        roll = random.randint(1, 100)

        if roll <= 15:
            # Basic job
            print("A merchant walks up to you.")
            NpC = "merchant"
            event = "A merchant asks if the player will help load wagons at the stable."
            choice = self.AI_File.narrate_dialogue_once(self.generate_game_state(), event, NpC)
            if choice.strip().lower() == "yes":
                earned = random.randint(20, 40)
                self.gold += earned
                self.Time += 2
                print(f"You work and earn {earned} gold.")
            else:
                print("You politely decline.")
            time.sleep(2,)

        elif roll <= 30:
            NpC = "farmer"
            print("A farmer waves you over.")
            event = "A farmer waves the player over. 'My plow's busted—can you help fix it?'"
            choice = self.AI_File.narrate_dialogue_once(self.generate_game_state(), event, NpC)
            if choice == "yes":
                if "rope" in self.itemsinventory:
                    print("You tie it back together with your rope.")
                    self.itemsinventory["rope"] -= 1
                    if self.itemsinventory["rope"] <= 0:
                        del self.itemsinventory["rope"]
                    self.gold += 30
                    print("You fix the plow. +10 gold.")
                elif self.perform_stat_check(self.trail_skill, base_target=12) == True:
                    print("You heave the plow upright and wedge it in tight.")
                    self.gold += 30
                    print("The farmer gives you 20 gold for your help.")
                else:
                    print("You try to help, but it's beyond your skill. The farmer thanks you anyway.")
                    print("If only you were more skilled in trail skills.")
            else:
                print("You decline to help the farmer.")
            
            time.sleep(2)


        elif roll <= 45:
            print("A schoolteacher walks over.")
            NpC = "schoolteacher"
            event = "A schoolteacher asks if the player will speak to the children about survival."
            choice = self.AI_File.narrate_dialogue_once(self.generate_game_state(), event, NpC)
            if choice == "yes":
                self.Time += 2
                self.shadow_skill += 1
                print("You tell them stories and teach a few tricks. +1 Shadow Skill.")
                self.Time += 1
            else:
                print("You shake your head and move on.")
            
            time.sleep(2)
        elif roll <= 60:
            # Help the blacksmith
            print("The blacksmith grunts, 'Hand me that hammer, would ya?'")
            if self.perform_stat_check(self.strength_skill, base_target=14) == True:
                self.strength_skill += 1
                print("He's impressed with your help. +1 Strength Skill.")
            else:
                print("You fumble a bit, but he pays you for your time.")
                self.gold += 5
            self.Time += 1

        elif roll <= 75:
            # Rare: town alert
            print("A kid runs by shouting, 'Bandits near the ridge!'")
            print("The sheriff is calling for help. Do you join him? (yes/no)")
            choice = self.AI_File.parse_YN(": ")
            if choice == "yes":
                print("You ride with the sheriff to confront the bandits!")
                self.Speed += 1
                print("The sheriff tosses you a revolver and some ammo.")
                item_name = "revolver"
                self.itemsinventory[item_name] = self.itemsinventory.get(item_name, 0) + 1
                item_name = "pistol_ammo"
                self.itemsinventory[item_name] = self.itemsinventory.get(item_name, 0) + 3
                combat = Combat(self)
                combat.FindAttacker("bandit")
                combat.Attack()
                
                self.Speed -= 1
                if self.Health > 0:
                    loot = random.choice(["ammo cartridge", "bread", "tobacco pouch", "gold nugget"])
                    self.loot_drop(loot)
                    print("As the final bandit falls under you and the sheriff's fury, you breath a sigh of relief.")
                    print("The sheriff slaps your back and thanks you.")
                    print("You return his revolver, and he gives you a pouch of gold.")
                    self.gold += 35
                    self.Health = self.MaxHealth
                    print("You feel rejuvenated. Health fully restored.")
                    selected_item = "revolver"
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                time.sleep(2)
                    

            else:
                print("You stay back, watching from a safe distance.")
                time.sleep(2,)

        elif roll <= 90:
            # Crafting bonus (if tools owned)
            if self.perform_stat_check(self.trail_skill, base_target=12) == True:
                print("A merchant sees your intelligence and teaches you a couple haggling tricks.")
                print("You feel more confident with your skills.")
                self.trail_skill += 1
            else:
                print("You chat with a merchant, but nothing comes of it.")

        else:
            # Gift
            item = random.choice(["bandage", "bread", "antivenom", "coffee tin"])
            print(f"A town elder says, 'You look like you could use this.' He hands you a {item}.")
            self.add_item(item)

    def LeaveTown(self):
        # 1. Run standard triggers (like Iron Tracks Stage 2)
        # We assume these don't block leaving, they just play a scene.
        if not self.quest_today:
            self.process_quest_triggers("leave_town", is_menu_option=False)

        # 2. Earp Vendetta Interception
        # Check if we are on Stage 4 OR if we deferred the fight earlier
        on_finale_stage = (self.Tquest == "earp_vendetta" and self.get_flag("earp_vendetta", "stage") == 4)


        if on_finale_stage:
            print("\nAs you head for the edge of town, Wyatt Earp steps into the road, blocking your path.")
            print("'We have business to finish with Curly Bill,' he says sternly.")
            print("'You aren't riding out on us now, are you?'")
            
            # Ask the player what to do
            choice = self.AI_File.parse_YN("Do you stay and fight? (yes/no): ")
            
            if choice == "yes":
                print("'Good. Meet me at the Saloon. We ride out soon.'")
                # Ensure the deferred flag is set so the button appears in the Saloon
                if "final_earp_confrontation" not in self.event:
                    self.event.append("final_earp_confrontation")
                return # Cancel leaving, go back to town menu
            
            else:
                print("You shake your head and push past him.")
                print("You turn your back, leaving the vendetta behind.")
                time.sleep(1)
                print("Suddenly, gunshots ring out from the shadows!")
                print("The Earp posse ambushes you for your cowardice! -20 health.")
                self.Health -= 20
                
                # FAIL THE QUEST (Clean up flags)
                self.Tquest = "None"
                if "final_earp_confrontation" in self.event:
                    self.event.remove("final_earp_confrontation")
                # Optional: Add to completed so it doesn't trigger again
                self.quests_done.append("earp_vendetta") 

        # 3. Cleanup Event Flags
        if "coin" in self.event:
            self.event.remove("coin")
        if "drink" in self.event:
            self.event.remove("drink")

        # 4. Actual Leaving Logic
        self.counter = 0
        self.current_town_name = "none"
        self.distancenext = random.randint(15, 20) + self.number_of_towns_visited * 3
        
        print("\nYou leave the town and head down the road.")
        if "surveyor's kit" in self.itemsinventory:
            print(f"[Surveyor's Kit] {self.distancenext} miles to next town.")
            
        self.play_sound("rolling_wheels.mp3")
        self.change_music("game_theme.mp3", -1)
        self.invillage = False
        self.Hostility = 0
        self.update_actions()
        time.sleep(2)

    def Interaction(self):
        Random = random.randint(1,50)
        if Random <= 5:
            print("You find some gold on the path! +10 gold.")
            self.gold += 10
        elif Random <= 25:
            combat = Combat(self)
            combat.FindAttacker("random")
            combat.Attack()
        elif Random <= 50:
            self.PossibleQuest()

    def Explore(self):
        print("You travel down the road...")
        self.play_sound("rolling_wheels.mp3")
        time.sleep(2,)
        travel = self.travelspeed + self.travel_bonus
        if self.distancenext <= travel:
            self.ArriveTown()
            
        else:
            self.distancenext -= travel
            Random = random.randint(1,5)
            if Random == 1:
                pass
            else:
                self.Interaction()

    def town_encounter(self):
        """
        Handles daily events in town.
        Prioritizes active quest progression over random new quests.
        """
        self.town_encounter_available = False
        self.update_actions()
        if self.Tquest == "None":
            roll = random.randint(1, 10)
            
            # 30% chance to start the Town Defense quest (Force Start)
            if roll <= 2 and "defend_town" not in self.quests_done:
                print("\nSomething is happening in town...")
                self.Tquest = "defend_town" # Set as active
                self.encounter_town_part1() # Start it immediately
                
            # 30% chance to hear the Iron Tracks rumor (Hint)
            elif roll <= 4 and "iron_tracks" not in self.quests_done:
                print("\n[Rumor] You see a new poster: 'Railroad Hiring - See Foreman at Saloon'.")
                # CHANGE THESE LINES:
                # Instead of starting the quest, we just give the "Key" to unlock the button
                self.rumors["railroad_job"] = 1
            elif roll <= 6:
                print("\nYou hear whispers of a vendetta. Wyatt Earp is looking for brave souls in the Saloon.")
                self.rumors["earp_rumor"] = 1 # Set the flag

            else:
                # Fallback: Just a quiet day
                print("The town is relatively quiet today.")

    def ArriveTown(self):
        name = f"{random.choice(self.TownNames1)} {random.choice(self.TownNames2)}"
        self.play_sound("rolling_wheels.mp3")
        self.play_sound("horse_neigh.mp3")
        print(f"You arrive in the town of {name}!")
        self.change_music("Town.mp3", -1)
        self.number_of_towns_visited += 1
        self.current_town_name = name
        self.town_event_occurred = False
        if "family" in self.caravan:
            self.travel_bonus += 1
            print("The family thanks you sincerely for allowing them to travel with you, and gives you a handsome reward. +20 gold.")
            self.gold += 20
            self.caravan.remove("family")
        self.gold += 10
        print("You feel a sense of relief as you enter the town.")
        print("You gain 10 gold from your travels.")
        self.invillage = True
        self.update_actions()
        self.score = self.score + 5
        time.sleep(2)
        if self.Tquest == "earp_vendetta" and self.get_flag("earp_vendetta", "stage") == 4:
            print("Wyatt Earp nods at you as you enter town.")
            print("'Ready to finish this?' he asks.")
            print("'I will be at the saloon when you are ready.'")
        if not self.quest_today:
            self.process_quest_triggers("arrive_town", is_menu_option=False)

        self.town_encounter_available = (self.Tquest == "None")
        self.update_actions()

    def GeneralStore(self):
        self.play_sound("store_bell.mp3")
        print("You walk into the general store. A friendly shopkeeper greets you.")
        time.sleep(2,)
        general_inventory = {            
            'lantern': ShopItem('lantern', 3, 10),
            'bread': ShopItem('bread', 5, 30),
            'rope': ShopItem('rope', 5, 20),
            'fire cracker': ShopItem('fire cracker', 5, 10),
            'antivenom': ShopItem('antivenom', 5, 10),
            'tobacco pouch': ShopItem('tobacco pouch', 7, 7),
            'coffee tin': ShopItem('coffee tin', 5, 5),
            'diary': ShopItem('diary', 5, 5),
            'salted pork': ShopItem('salted pork', 10, 10), # -2 Hunger
            'pemmican': ShopItem('pemmican', 20, 5),        # -3 Hunger (Full)
            'flint and steel': ShopItem('flint and steel', 15, 1), # Reusable fire starter
            'firewood': ShopItem('firewood', 2, 20),        # Fuel
            'wool blanket': ShopItem('wool blanket', 25, 1), # Passive heat drain reduction
            'bedroll': ShopItem('bedroll', 15, 1), 
            'small tent': ShopItem('small tent', 40, 1),
            'wall tent': ShopItem('wall tent', 100, 1),      
            'wool blanket': ShopItem('wool blanket', 25, 2),
        }
        if self.winter_mode:
            general_inventory['heavy coat'] = ShopItem('heavy coat', 50, 5)
            general_inventory['firewood'].base_price = 5
        gen_shop = ShopSession(self, self.AI_File, "General Store", general_inventory, "store owner")
        gen_shop.run_buy_session()

    def HostilityFunc(self):
        if self.Hostility < 1:
            print("The people pass by your wagon happily.")
            time.sleep(1,)
        if self.Hostility == 1:
            print("The people are suspicious that you were unharmed during the attack.")
            if self.gold >= 3:
                print("It appears that someone snuck a couple gold coins from your purse. -3 gold")
                self.gold = self.gold - 3
            else:
                return
        elif self.Hostility == 2:
            print("The people are sure you have some correlation with the bandits.")
            print("A burly fellow shoves you into a water trough.")
            self.Health = self.Health - 15
            time.sleep(2,)
        elif self.Hostility >= 3:
            print("The sheriff throws you into the musty jail, not believing your pleas of innocence.")
            self.jail_penalty()

    def Death(self, death_cause):
        self.change_music("stop", 0)
        self.play_sound("death.mp3")
        print("You fall to the ground, your vision fading...")
        
        time.sleep(2,)
        print(death_cause)
        if self.rebirth == True:
            print("You have already respawned once.")
            print("You feel your life slipping away, and you know this is the end.")
            self.score = 0
        else:
            print("Your stats:")
            print(f"Days survived: {self.Day}")
            print(f"Score: {self.score}")
            

            self.AI_File.parse_choice(["Continue"], "Press Enter to continue...")
            
            self.Statcheck()
            
            # 2. Replace the yes/no prompt
            prompt = "You have come so far, would you like to respawn at your current position?"
            print("You will no longer track score.")
            choice = self.AI_File.parse_YN(prompt)
            if choice == "yes":
                self.lose_random_item(2)
                self.gold -= self.gold/2
                print("You feel a strange sensation, as if you are being pulled back to life...")
                self.Health = self.MaxHealth
                self.rebirth = True
                self.score = 0
                return
 

        print("Credits: Bayne Cheke, Designer and Programmer.")
        time.sleep(1,)
        print("Music/audio effects: Freesound.com")
        time.sleep(1,)
        print("Playtesters: Deric R Cheke, Dax Cheke, Jessica Cheke, Silas Cheke, Shai Mckerley, Carson Templeton")
        time.sleep(1,)
        print("Other contributors: ChatGPT, Gemini AI, Ollama AI")
        time.sleep(1,)

        print("Thank you for playing!")
        print("Until next time...")
        time.sleep(2,)
        exit()

    def MakeCamp(self):
        print("\nYou pull your wagon off the road to set up a temporary camp.")
        print("This will cost 1 hour of daylight.")
        
        # 1. Define Camp Options
        print("1. Build a Fire (Requires Firewood + Flint)")
        print("2. Rest in Tent (Better if you have a Tent)")
        print("3. Cook Food (requires Firewood + Flint + Meat)")
        print("4. Pack up and leave")
        
        choice = self.AI_File.parse_choice(["build fire", "rest", "cook", "leave"], "Camp Action:")
        
        if choice == "build fire":
            self.skip_freeze = True
            if "flint and steel" in self.itemsinventory and "firewood" in self.itemsinventory:
                print("You strike the flint and light a roaring fire.")
                self.itemsinventory["firewood"] -= 1
                if self.itemsinventory["firewood"] <= 0: del self.itemsinventory["firewood"]
                
                # Restore Heat
                if self.winter_mode:
                    print("The warmth thaws your frozen limbs. Heat fully restored.")
                    self.Heat = self.MaxHeat
                    self.cold_penalty = 0
                
                # Small morale/health boost
                self.Health = min(self.Health + 5, self.MaxHealth)
                self.Time += 1
            elif "firewood" in self.itemsinventory:
                if random.randint(1, 2) == 1:
                    print("You light a small fire with the wood.")
                    self.itemsinventory["firewood"] -= 1
                    if self.itemsinventory["firewood"] <= 0: del self.itemsinventory["firewood"]
                    if self.winter_mode:
                        print("The warmth thaws your frozen limbs. Heat fully restored.")
                        self.Heat = self.MaxHeat
                        self.cold_penalty = 0
                    # Small morale/health boost
                    self.Health = min(self.Health + 5, self.MaxHealth)

                    self.Time += 1
                else:
                    print("You try to light the fire, but it fails. -5 health.")
            else:
                print("You need 'Flint and Steel' AND 'Firewood' to build a fire.")
        
        elif choice == "rest":
            self.skip_freeze = True
            sleep_options = ["sleep in wagon"] # Always available
            
            if "bedroll" in self.itemsinventory:
                sleep_options.append("use bedroll")
            if "small tent" in self.itemsinventory:
                sleep_options.append("use small tent")
            if "wall tent" in self.itemsinventory:
                sleep_options.append("use wall tent")
            sleep_choice = self.AI_File.parse_choice(sleep_options, "How do you want to sleep?")
            # --- TIER CHECK ---
            # Check from Best -> Worst
            if sleep_choice == "use wall tent":
                print("It takes some time to set up your Wall Tent. +2 Hours.")
                self.Time += 2
                print("You enter your spacious Wall Tent. It feels like a home away from home.")
                heal = 20
                heat = 50
                print(f"You sleep deeply. +{heal} Health. +{heat} Heat.")

                
            elif sleep_choice == "use small tent":
                print("It takes some time to set up your Small Tent. +1 Hour.")
                self.Time += 1
                print("You crawl into your Small Tent. It blocks the wind effectively.")
                heal = 10
                heat = 30
                print(f"You rest well. +{heal} Health. +{heat} Heat.")

                
            elif sleep_choice == "use bedroll":
                print("You unroll your Bedroll near the fire. It's better than the ground.")
                heal = 5
                heat = 15
                print(f"You catch some sleep. +{heal} Health. +{heat} Heat.")

                
            else:
                print("You curl up in your wagon.")
                self.Health = min(self.Health + 5, self.MaxHealth)
                print("You feel a bit better. +5 Health.")
                if self.winter_mode:
                    self.Heat = min(self.Heat + 15, self.MaxHeat)
                    print("You warm up slightly. +15 Heat.")
                    self.cold_penalty = 0
                    self.skip_freeze = True
            
            # Apply Blanket Bonus (Stacks with anything)
            if "wool blanket" in self.itemsinventory:
                print("Your Wool Blanket provides extra warmth. (+5 Heat)")
                if self.winter_mode: self.Heat = min(self.Heat + 5, self.MaxHeat)
            
            if not self.tent_used_today: 
                self.Health = min(self.Health + heal, self.MaxHealth)
            else:
                print("You cannot heal twice with a tent today. (You can still regain heat if in winter)")
            if self.winter_mode: self.Heat = min(self.Heat + heat, self.MaxHeat)
            self.cold_penalty = 0
            self.Time += 1
            self.tent_used_today = True
            

        elif choice == "cook":
            self.skip_freeze = True
            
            # Check for fire tools
            if "flint and steel" in self.itemsinventory and "firewood" in self.itemsinventory:
                print("\nYou light a fire. The flames crackle warmly.")
                
                # Consume 1 firewood for the cooking session
                self.itemsinventory["firewood"] -= 1
                if self.itemsinventory["firewood"] <= 0: del self.itemsinventory["firewood"]
                
                # --- INTERACTIVE COOKING LOOP ---
                cooking_session = True
                while cooking_session:
                    recipes = []
                    
                    # 1. Basic Recipes
                    if "small meat" in self.itemsinventory: recipes.append("Grill Small Meat (-> Salted Pork)")
                    if "medium meat" in self.itemsinventory: recipes.append("Grill Medium Meat (-> Salted Pork)")
                    if "large meat" in self.itemsinventory: recipes.append("Seer Large Meat (-> Steak)")
                    
                    # 2. Combo Recipes
                    if "large meat" in self.itemsinventory and "whiskey" in self.itemsinventory:
                        recipes.append("Cook Bourbon Roast (Large Meat + Whiskey)")
                    if "bread" in self.itemsinventory and "salted pork" in self.itemsinventory:
                        recipes.append("Cook Salted Pork Sandwich (Bread + Salted Pork)")
                    
                    recipes.append("Stop Cooking")
                    
                    # Ask player
                    print(f"\n--- Campfire Cooking (Firewood remaining: {self.itemsinventory.get('firewood', 0)}) ---")
                    cook_choice = self.AI_File.parse_choice(recipes, "Select a recipe:")
                    
                    if cook_choice == "stop cooking":
                        cooking_session = False
                        print("You put out the fire.")
                    
                    # --- RECIPE LOGIC ---
                    elif "small meat" in cook_choice:
                        self.itemsinventory["small meat"] -= 1
                        if self.itemsinventory["small meat"] <= 0: del self.itemsinventory["small meat"]
                        self.add_item("salted pork")
                        print("You grilled the small meat into a decent meal.")
                        
                    elif "medium meat" in cook_choice:
                        self.itemsinventory["medium meat"] -= 1
                        if self.itemsinventory["medium meat"] <= 0: del self.itemsinventory["medium meat"]
                        self.add_item("salted pork")
                        self.add_item("salted pork")
                        print("You grilled the medium meat into two rations.")

                    elif "seer large meat" in cook_choice: # Matches the button text
                        self.itemsinventory["large meat"] -= 1
                        if self.itemsinventory["large meat"] <= 0: del self.itemsinventory["large meat"]
                        self.add_item("steak")
                        print("You sear the large meat into a juicy Steak.")

                    elif "bourbon roast" in cook_choice:
                        # Consume Meat
                        self.itemsinventory["large meat"] -= 1
                        if self.itemsinventory["large meat"] <= 0: del self.itemsinventory["large meat"]
                        # Consume Whiskey
                        self.itemsinventory["whiskey"] -= 1
                        if self.itemsinventory["whiskey"] <= 0: del self.itemsinventory["whiskey"]
                        
                        self.add_item("bourbon roast")
                        print("You slow-cook the meat in whiskey glaze. It smells heavenly.")
                    
                    elif "salted pork sandwich" in cook_choice:
                        # Consume Ingredients
                        self.itemsinventory["bread"] -= 1
                        if self.itemsinventory["bread"] <= 0: del self.itemsinventory["bread"]
                        self.itemsinventory["salted pork"] -= 1
                        if self.itemsinventory["salted pork"] <= 0: del self.itemsinventory["salted pork"]
                        
                        self.add_item("salted pork sandwich")
                        print("You prepare a hearty Salted Pork Sandwich. It's filling.")
                    
                self.Time += 1
            else:
                print("You need 'Flint and Steel' AND 'Firewood' to start a cooking fire.")

        else:
            print("You pack up and head back to the road.")
        time.sleep(3,)


    #RunDay
    def RunDay(self):
        
        print("You step out of your wagon and stretch.")
        time.sleep(2,)
        while self.Time < 21:
            if self.Hunger >= 7:
                print("You feel weak from hunger.")
                if random.randint(1, 4) == 1: # Reduced chance to 25%
                    print("You stumble from exhaustion.")
                    self.Time += 0.5
                    self.Health -= 5
                    if self.Health <= 0:
                        self.Death("You have succumbed to exhaustion.")
                    continue
            self.DoAction()
            time.sleep(1,)
            print()
            if self.Hunger < 0:
                Heal_bonus = self.Hunger
                Heal_bonus = Heal_bonus*2
                self.Health -= Heal_bonus
                self.Hunger = 0
            self.Time += 1
            if self.Time % 2 == 0:
                if self.poisoned > 0:
                    dmg = self.poisoned*2
                    self.Health -= dmg
                    print(f"You feel light headed, the poison is taking effect. -{dmg} health.")
                    if self.Health <= 0:
                        self.Death("You have succumbed to the poison.")
            if self.Health > self.MaxHealth:
                self.Health = self.MaxHealth
            if self.Health <= 0:
                self.Death("You have succumbed to your injuries during the day.")
            if self.winter_mode:
                if self.skip_freeze:
                    self.skip_freeze = False
                    continue
                if self.invillage:
                    # Towns restore heat automatically
                    self.Heat = min(self.Heat + 30, self.MaxHeat)
                    self.cold_penalty = 0
                else:
                    # 1. Calculate Drain Amount

                    heat_drain = 10 # You lose 15 Heat per hour by default
                    
                    if "heavy coat" in self.itemsinventory:
                        heat_drain = 5 # Coat slows it down significantly
                        
                    # 2. Apply Drain
                    self.Heat -= heat_drain
                    
                    # 3. Check Thresholds (The Danger Zone)
                    if self.Heat <= 0:
                        self.Heat = 0
                        print(f"(!) HYPOTHERMIA. You are freezing to death. Heat: 0/{self.MaxHeat}")
                        self.Health -= 5
                        self.cold_penalty = 5 # Massive stat reduction
                        self.Hunger += 0.25 # Shivering burns calories (Lowers food stat)
                        
                    elif self.Heat < 30:
                        print(f"(!) You are shivering violently. Heat: {self.Heat}/{self.MaxHeat}")
                        self.Health -= 2 # Chip damage
                        self.Hunger += 0.1
                        self.cold_penalty = 2 # Moderate stat reduction
                    
                    else:
                        # Just getting cold, no damage yet
                        print(f"The cold gnaws at you. Heat: {self.Heat}/{self.MaxHeat}")

        self.quest_today = False
        time.sleep(1)
        if self.Health <= 0:
            self.Death("You have succumbed to your injuries during the day.")

        self.change_music("night_sounds.mp3", -1)
        if self.invillage == True:
            print("Night falls over the town.")
            Day = 3
            Day = Day - self.Day
            if Day <= 0:
                Day = 1
            if random.randint(0, Day) == 1:
                print("Gunshots ring out in the night! The town was attacked!")
                self.play_sound("gunfire.mp3")
                time.sleep(2,)
                print("You roll out of bed, but the bandits have already left.")
                print("You return to you wagon, concerned at what the next day will bring.")
                self.Hostility += 1
                time.sleep(2,)
                self.write_diary_entry()
            else:
                print("You sleep peacefully in your wagon.")
                time.sleep(4,)
                self.write_diary_entry()
        else:
            warmth_bonus = 0
            
            if "canvas tent" in self.itemsinventory:
                print("You sleep soundly in your Canvas Tent. (+10 Health)")
                self.Health = min(self.Health + 10, self.MaxHealth)
                warmth_bonus += 1
            
            if "wool blanket" in self.itemsinventory:
                print("Your Wool Blanket keeps the chill away.")
                warmth_bonus += 1

            if self.winter_mode:
                if warmth_bonus == 0:
                    print("It is freezing tonight! You shiver uncontrollably. -10 Health.")
                    self.Health -= 10
                elif warmth_bonus == 1:
                    print("It's cold, but your gear helps. -5 Health.")
                    self.Health -= 5
                else:
                    print("Your tent and blanket make the winter night comfortable. No Health lost.")

            print("You make camp under the stars.")
            self.write_diary_entry()
            print("You sleep through the night")
            time.sleep(4,)
        self.Time = 9

    #Quests
    def PossibleQuest(self):
        Random = random.randint(1,40)
        Random = Random + self.Day*5-5


        # --- On-the-trail quest handler (random chance) ---
        if not self.quest_today and random.randint(1, 4) == 1:
            if self.process_quest_triggers("on_the_trail", is_menu_option=False):
                self.quest_today = True
                return

        # --- Rumor quest handler ---
        if self.quest_today == False:
            if self.quest and random.randint(1,2) == 1:
                print("You remember a rumor you heard in town.")
                quest_topic = self.quest.pop(0)  # Remove and get the oldest quest
                self.quest_today = True
                print(f"\nYou follow up on a rumor: {quest_topic.replace('_',' ').capitalize()}!")
                # Trigger a special event based on the quest topic
                if quest_topic == "bandits_coyote_camp" and not self.quests_done.__contains__("bandits_coyote_camp"):
                    self.coyote_camp_quest()
                    self.quests_done.append("bandits_coyote_camp")
                elif quest_topic == "old_mine_lights" and not self.quests_done.__contains__("old_mine_lights"):
                    self.encounter_haunted_mine()
                    self.quests_done.append("old_mine_lights")
                else:
                    print("You follow the rumor, but nothing comes of it this time.")
                return  # Only do one quest per call
        
        if Random <= 5:
            self.encounter_abandoned_wagon()
        elif Random <= 10:
            self.encounter_dry_river_bed()
        elif Random <= 15:
            self.encounter_stage_coach()
        elif Random <= 20:
            self.encounter_caravan()
        elif Random <= 25:
            self.encounter_abandoned_house()
        elif Random <= 30:
            self.wandering_trader()
        elif Random <= 35:
            self.encounter_wounded_bandit()
        elif Random <= 40:
            self.encounter_caravan_attack()
        elif Random <= 45:
            self.encounter_wild_stallion()
        elif Random <= 50:
            self.encounter_burned_outpost()
        elif Random <= 55:
            self.encounter_haunted_house()
        elif Random <= 60:
            self.encounter_hermit_challenge()
        else:
            random_event = random.choice(["haunted_house", "cave_of_shadows", "hermit challenge"])
            if random_event == "haunted_house":
                self.encounter_haunted_house()
            elif random_event == "cave_of_shadows":
                self.encounter_cave_of_shadows()
            elif random_event == "hermit challenge":
                self.encounter_hermit_challenge()

    def encounter_caravan(self):
        rand = random.randint(1,2)
        if "outlaw" not in self.caravan and rand == 2:
            print("A outlaw appears on the road.")
            print("Will you try and capture him? (yes/no)")
            choice = self.AI_File.parse_YN(": ")
            time.sleep(2,)
            if choice == "yes":
                print("You attempt to capture the outlaw.")
                if self.perform_stat_check(self.strength_skill, base_target=14) == True:
                    print("You successfully capture the outlaw.")
                    print("Go to the next town's jail to turn him in.")
                else: 
                    print("The outlaw overpowers you and escapes.")
                    print("If only you were stronger...")
                    self.Health -= 10
                    self.Hostility += 1
                    print("You are injured in the scuffle. -10 health.")
                    print("The townsfolk are suspicious that you 'let' him go. +1 Hostility.")
                time.sleep(2,)
            else:
                print("You decide to ignore him.")
                print("The townsfolk are suspicious that you let him go. +1 Hostility.")
                self.Hostility += 1
                time.sleep(2,)
        elif "family" not in self.caravan and rand == 1:
            print("A family is travelling in their wagon, but it appears that they have a broken wheel.")
            print("Would you like to help, or pass them by? (yes/no)")
            choice = self.AI_File.parse_YN(": ")
            if choice == "yes":
                print("You tow the other wagon behind yours.")
                print("The family thanks you for allowing them to travel with them")
                print("It takes some extra time, but you feel it was worth it.")
                self.caravan.append("family")
                time.sleep(2,)
                print("The family plans to unhook the wagons at the next town.")
                self.travel_bonus -= 1
                time.sleep(2,)
        else:
            print("You decide to pass them by.")
            time.sleep(2,)

    def encounter_abandoned_house(self):
            print("You see an abandoned house by the side of the road.")
            print("It could have some valuable loot, but you have no idea what is inside.")
            
            # --- MODIFICATION 1: Main Entry Menu ---
            available_choices = ["Leave it", "Enter door", "Enter cellar", "Loot garden"]
            prompt = "What do you want to do?"
            
            choice = self.AI_File.parse_choice(available_choices, prompt)
            
            if choice == "leave it":
                print("You decide it is wisest to leave it alone.")
                time.sleep(2,)
                
            elif choice == "enter door":
                print("You enter the door.")
                print("It makes a creaking sound as you walk in.")
                time.sleep(2,)
                
                # --- MODIFICATION 2: Inside the House Menu ---
                print("You see three things of interest:")
                print("1. A dusty rifle on the wall.")
                print("2. A bundle on the table.")
                print("3. A painting on the far wall.")
                
                choices_inside = ["Dusty Rifle", "Bundle", "Painting"]
                choice_inside = self.AI_File.parse_choice(choices_inside, "What do you inspect?")

                if choice_inside == "dusty rifle":
                    Random = random.randint(1,2)
                    if Random == 1:
                        print("As you head over to the table you hear a noise.")
                        time.sleep(2,)
                        print("Out of the darkness a blade hits you.")
                        print("You stumble out of the building.")
                        print("There must be a way to disable the traps...")
                        self.Health -= 20
                        time.sleep(2,)
                    else:
                        print("You grab the rifle")
                        self.loot_drop("rifle")
                        time.sleep(2,)
                
                elif choice_inside == "bundle":
                    Random = random.randint(1,3)
                    if Random == 1:
                        print("As you head over to the table you hear a noise.")
                        time.sleep(2,)
                        print("Out of the darkness a blade hits you.")
                        print("You stumble out of the building.")
                        print("There must be a way to disable the traps...")
                        self.Health -= 10
                        time.sleep(2,)
                    else:
                        print("You rummage around through the table")
                        self.loot_drop(random.choice(self.common_loot))
                
                elif choice_inside == "painting":
                    print("You examine the picture...")
                    time.sleep(2,)
                    if self.perform_stat_check(self.shadow_skill, base_target=15) == True:
                        print("You accidentally trigger the trap attached to the painting!")
                        print("Out of the darkness a blade hits you.")
                        print("You stumble out of the building.")
                        print("You were close. If your shadow skill was higher you might have disarmed it.")
                        time.sleep(4,)
                    else:
                        print("You notice the elaborate trap around the painting, stretching around the room.")
                        print("You carefully disarm the trap, glad your shadow skills have served you.")
                        time.sleep(2,)
                        print("You find a crate behind the painting.")
                        print("Now that the trap is disarmed, you can loot the room safely.")
                        
                        # --- MODIFICATION 3: Behind Painting Menu ---
                        choices_loot = ["Dusty Rifle", "Bundle", "Crate"]
                        choice_loot = self.AI_File.parse_choice(choices_loot, "What do you want to take?")
                        
                        if choice_loot == "dusty rifle":
                            print("You grab the rifle")
                            self.loot_drop("rifle")
                        elif choice_loot == "bundle":
                            print("You rummage around through the table")
                            self.loot_drop(random.choice(self.common_loot))
                        elif choice_loot == "crate":
                            print("You find a wealth of supplies")
                            self.gold += 20
                            self.loot_drop(random.choice(self.uncommon_loot))
                            self.loot_drop(random.choice(self.rare_loot))
                
                else:
                    print("Invalid choice.")
                    return

            elif choice == "enter cellar":
                print("You enter the cellar, it is damp and dirty.")
                if "lantern" in self.itemsinventory:
                    print("You use your lantern to light the way.")
                    time.sleep(1,)
                    print("You found a rare item!")
                    rare = random.choice(["winchester stock", "winchester barrel"])
                    self.loot_drop(rare)
                    for i in range(3):
                        self.loot_drop("rifle_ammo")
                else:
                    print("It is too dark to explore so you leave.")
                    time.sleep(1,)
            
            elif choice == "loot garden":
                print("You loot the garden.")
                self.loot_drop(random.choice(self.common_loot))
                time.sleep(2,)
            
            else:
                print("Invalid choice.")
                return

            print("Suddenly, you hear someone approaching the house.")
            print("You quickly exit the house and get back on the road.")
            time.sleep(2,)

    def encounter_stage_coach(self):
            print("You come upon a stagecoach dangling over a ravine. The driver pleads for help.")
            
            # --- MODIFICATION START ---
            available_choices = [
                "Secure with rope", 
                "Push it back", 
                "Leave it"
            ]
            
            choice = self.AI_File.parse_choice(available_choices, "What do you do?")

            if choice == "secure with rope": # <-- Changed from "1"
                if "rope" in self.itemsinventory:
                    print("You tie off your rope and carefully secure the stagecoach...")
                    
                    # Logic Fix: 1 is failure (25%), Else is success (75%)
                    if random.randint(1, 4) == 1: 
                        print("The rope frays! The coach lurches but you can't hold it.")
                        print("Your rope isn't strong enough. The coach slips over the edge.")
                        self.Health -= 5
                        print("-5 health from the strain.")
                    else:
                        print("With effort, you pull it back to safety! The driver rewards you.")
                        reward = random.randint(10, 30)
                        self.gold += reward
                        self.itemsinventory["rope"] -= 1
                        if self.itemsinventory["rope"] <= 0:
                            del self.itemsinventory["rope"]
                        print(f"+{reward} gold")
                else:
                    print("You rummage through your bag, but realize you have no rope!")
                    print("You try to pull the coach back but you are too late and it slips over the edge.")
                    self.Time += 1

            elif choice == "push it back": # <-- Changed from "2"
                print("You brace yourself and try to push the stagecoach back...")
                if self.perform_stat_check(self.strength_skill, base_target=14) == True:
                    print("Your strength prevails! You save the stagecoach and earn a reward.")
                    reward = random.randint(10, 30)
                    self.gold += reward
                    print(f"+{reward} gold")
                else:
                    print("Your strength isn't enough. The coach slips over the edge.")
                    self.Health -= 5
                    print("-5 health from the effort.")

            else: # Covers "leave it"
                print("You decide it's too dangerous and ride on, losing some daylight.")
                self.Time += 1
            # --- MODIFICATION END ---

            time.sleep(2,)

    def encounter_dry_river_bed(self):
        print("A dry river bed lies in your path.")
        time.sleep(1,)
        print("A storm is brewing in the West, and this location could flood easily.")
        print("You could either cross here, and risk the storm, or travel around.")
        time.sleep(2,)
        available_choices = ["Cross the river", "Go around"]
        prompt = "What will you do?"
        choice = self.AI_File.parse_choice(available_choices, prompt)
        
        if choice == "cross the river": 
            print("You take the chance and cross the river bank.")
            if "weather cloak" in self.itemsinventory:
                print("Your weather cloak shields you from the flooding; you cross safely.")
                self.itemsinventory["weather cloak"] -= 1
                if self.itemsinventory["weather cloak"] <= 0:
                    del self.itemsinventory["weather cloak"]
            else:

                Random = random.randint(1,10)
                if Random < 6:
                    print("You cross safely, and the rain starts only after you get across.")
                else:
                    print("The torrent of water that appears carries you and your wagon down stream.")
                    time.sleep(2,)
                    print("After the water, you realize that one of your items is missing.")
                    self.lose_random_item(1)
                    time.sleep(2,)
                    print("You get back on the trail, but a lot of time has been wasted.")
                    self.Time += 2
        else: 
            print("You travel around the creek, but are glad you didn't take the risk")
            self.Time += 1

    def encounter_abandoned_wagon(self):
            print("You notice an abandoned wagon a little ways off the trail.")
            
            choice = self.AI_File.parse_choice(["Search it", "Leave it"], "You could either search the wagon or leave and save time.")

            if choice == "search it":
                print("You take the time to search the wagon.")
                Random1 = random.randint(1,2)
                if Random1 == 1:
                    print("As you rummage through the bags and boxes you uncover a rattlesnake.")
                    if "rope" in self.itemsinventory:
                        print("You use your rope to whack the snakes head away, and it flees through the grass.")
                        self.itemsinventory["rope"] -= 1
                        if self.itemsinventory["rope"] <= 0:
                            del self.itemsinventory["rope"]
                    elif self.Speed >= 5:
                        print("You dodge the snakes attack, then strangle it")
                    else:
                        print("The snake bites you, then retreats.")
                        self.poisoned = 1
                    time.sleep(2,)
                print("Inside the wagon you find many useful items.")
                rare = random.choice(["colt pistol", "bowie knife", "bread", "rope"])
                self.loot_drop(rare)
                time.sleep(2,)
            else:
                print("You leave the wagon alone and proceed down the trail.")

    def encounter_wounded_bandit(self):
            Random = random.randint(1, 100)
            print("\nYou spot a wounded bandit slumped against a rock. His pistol lies beside him.")
            
            choice = self.AI_File.parse_choice(["Help him", "Loot him", "Leave him be"], "What do you do?")
            
            if choice == "help him":
                print("You tend his wounds and give him water.")
                gold = random.randint(5, 15)
                self.gold += gold
                print(f"He thanks you and staggers off. +{gold} gold.")
                if Random <= 50:
                    print("The bandit robbed you while you weren't looking!")
                    self.lose_random_item(1)
            elif choice == "loot him":
                print("You search him and take what he has.")
                gold = 5
                self.gold += gold
                if "revolver" not in self.itemsinventory:
                    self.itemsinventory["revolver"] = 1
                    print("You also pick up his revolver.")
                print(f"+{gold} gold.")
                if Random <= 50:
                    print("The bandit fights through his wounds and punches you!")
                    self.Health -= 10
            else:
                print("You decide not to get involved. You lose an hour of daylight.")
                self.Time += 1
            time.sleep(2)

    def encounter_caravan_attack(self):
            print("\nYou hear gunshots up ahead—a merchant caravan is under attack!")
            
            choice = self.AI_File.parse_choice(["Join the fight", "Stay hidden", "Loot after"], "What will you do?")

            if choice == "join the fight":
                print("You rush in to defend them!")
                combat = Combat(self)
                combat.FindAttacker("bandit")
                escape = combat.Attack()
                if escape == True:
                    return
                else:
                    if self.Health > 0:
                        reward = random.randint(15, 30)
                        self.gold += reward
                        print(f"The grateful merchants reward you with {reward} gold.")
                        print("They also give you some supplies.")
                        self.loot_drop("bandage")
            elif choice == "stay hidden":
                print("You stay hidden until it's over. No one notices you.")
            else:
                print("You wait for the dust to settle, then loot the fallen.")
                loot = random.choice(["bread", "pistol_ammo", "rope"])
                self.loot_drop(loot)
            time.sleep(2)

    def encounter_wild_stallion(self):
        print("\nA wild stallion rears up in a clearing—untamed and swift.")
        
        choice = self.AI_File.parse_choice(["Try to catch it", "Leave it be"], "What will you do?")

        if choice == "try to catch it":
            if "rope" in self.itemsinventory:
                print("You manage to rope the stallion! Your travels feel faster now. +1 travel speed.")
                self.travelspeed += 1
            else:
                print("It throws you off with a vicious kick!")
                self.Health -= 10
                print("-10 health.")
        else:
            print("You admire it for a moment, then move on.")
        time.sleep(2)

    def encounter_burned_outpost(self):
        print("\nYou find the charred remains of an old outpost. Supplies lie scattered.")
        print("1) Search the ruins")
        print("2) Move on quickly")
        Choice = input(": ").strip()
        if Choice == "1":
            if random.randint(1, 3) == 1:
                print("Ambush! Enemies burst from the shadows!")
                combat = Combat(self)
                combat.FindAttacker("brawler")
                combat.Attack()
            if self.Health > 0:
                loot = random.choice(self.rare_loot)
                self.loot_drop(loot)

        else:
            print("You decide it's too risky and press on.")
        time.sleep(2)

    def encounter_town_part1(self):
        print("\nA frantic sheriff begs: 'Bandits will raid this town tonight. Will you stay?'")
        print("1) Stay and defend")
        print("2) Offer supplies")
        print("3) Refuse")
        Choice = input(": ").strip()
        if Choice == "1":
            print("You take up arms alongside the sheriff.")
            self.Armory()
            combat = Combat(self)
            combat.FindAttacker("bandit")
            combat.Attack()
            if self.Health > 0:
                reward = random.randint(20, 30)
                self.gold += reward
                print(f"You defended the town! They award you {reward} gold.")
            self.town_defense_outcome = "fought"
        elif Choice == "2":
            cost = min(self.gold, random.randint(5, 10))
            self.gold -= cost
            print(f"You donate supplies worth {cost} gold and some supplies.")
            self.donate_supplies()
            self.town_defense_outcome = "helped"
        else:
            print("You tip your hat and leave before nightfall.")
            self.town_defense_outcome = "refused"
        self.set_flag("defend_town", "outcome", self.town_defense_outcome)
        time.sleep(2)
        self.Tquest = "defend_town"
        self.quest_today = True

    def encounter_town_part2(self):
        if self.town_defense_outcome is None:
            return  # don't run if Part 1 never happened

        print("\nDays later you return. The town is scarred by the last raid.")
        print("1) Help rebuild")
        print("2) Buy supplies")
        print("3) Threaten the sheriff for payment owed")
        Choice = input(": ").strip()

        if Choice == "1":
            self.town_aftermath_outcome = "repaired"
            if self.town_defense_outcome == "fought":
                print("Repairs go swiftly. The townsfolk gift you some bread and other supplies.")
                self.loot_drop("bread")
                self.loot_drop(random.choice(self.uncommon_loot))
            elif self.town_defense_outcome == "helped":
                print("Repairs lag but they appreciate you. You receive a small meal and some ammo.")
                self.loot_drop("bread")
                self.loot_drop("ammo cartridge")
                self.Time += 2
            else:
                print("They stare warily but accept your help. No reward.")
                self.Time += 3

        elif Choice == "2":
            self.town_aftermath_outcome = "bought"
            self.donate_supplies()
        else:
            self.town_aftermath_outcome = "threatened"
            print("You demand payment. The sheriff draws his pistol!")
            combat = Combat(self)
            combat.FindAttacker("sheriff")
            combat.Attack()
            print("You collect your reward from the dead sheriff...")
            print("The townspeople fear and hate you.")
            self.gold += 25
            self.Hostility += 2
        self.set_flag("defend_town", "aftermath", self.town_aftermath_outcome)
        self.quest_today = True
        time.sleep(2)

    def encounter_town_part3(self):
        if self.town_aftermath_outcome is None:
            return  # don't run if Part 2 never happened

        print("\nRumors: bandits return tonight for revenge. The sheriff implores you again.")
        print("1) Defend the town")
        print("2) Negotiate with the bandits")
        print("3) Leave them to fate")
        Choice = input(": ").strip()

        if Choice == "1":
            self.town_final_outcome = "defended"
            self.Armory()
            print("You stand firm. Battle commences!")
            # bonus if earlier you aided them
            if (self.town_defense_outcome in ["fought"]
                and self.town_aftermath_outcome in ["repaired", "bought"]):
                print("Your previous deeds bolster the townsfolk morale.")
                self.dmg_modifier_multiply = 1.25
            if (self.town_defense_outcome in ["helped"]
                and self.town_aftermath_outcome in ["repaired", "bought"]):
                print("Your previous deeds bolster the townsfolk morale.")
                if getattr(self, "town_defense_bonus", 0) > 0:
                    bonus = self.town_defense_bonus
                    bonus = bonus*3
                    print(f"Your supplies bolster the defenders! +{bonus} damage this battle for the first turn.")
                    self.dmg_modifier_multiply += bonus
            combat = Combat(self)
            combat.FindAttacker("bandit leader")
            combat.Attack()
            if self.Health > 0:
                reward = random.randint(20, 40)
                self.gold += reward
                print(f"Town survives! They reward you {reward} gold.")

        elif Choice == "2":
            self.town_final_outcome = "negotiated"
            fee = min(self.gold, random.randint(20, 40))
            if random.choice([True, False]):
                if self.gold >= fee:
                    self.gold -= fee
                    print(f"You pay the bandits {fee} gold. They depart peacefully.")
                else:
                    print("You don't have enought money so the bandits open fire.")
                    combat = Combat(self)
                    combat.FindAttacker("bandit leader")
                    combat.Attack()
            else:
                print("They feign agreement... then open fire!")
                combat = Combat(self)
                combat.FindAttacker("bandit leader")
                combat.Attack()

        else:
            self.town_final_outcome = "abandoned"
            print("You ride away, leaving the town to its fate.")
        self.set_flag("defend_town", "final", self.town_final_outcome)
        self.Tquest = "None"
        self.quests_done.append("defend_town")
        self.quest_today = True
        time.sleep(2)

    def wandering_trader(self):
        print("\nYou encounter a wandering trader on the trail.")
        time.sleep(1)
        print("The trader tips his hat. 'Got some fine goods, if you’ve got the coin.'")
        time.sleep(1)

        # --- Trader's curated pool of possible goods ---
        trader_pool = [
            # Common weapons
            "colt pistol", "revolver", "derringer pistol", "carbine rifle",
            "shotgun", "sawed-off shotgun", "tomahawk", "knife",
            # Rare / high-tier weapons
            "henry rifle", "lever-action rifle", "sharps rifle",
            "double barrel shotgun", "winchester rifle",
            # Supplies
            "bread", "bandage", "antivenom", "gun oil",
            "field dressing kit", "ammo cartridge",
            # Misc valuable or unique items
            "gold nugget", "silver watch", "boots"
        ]

        # --- Randomly choose up to 5 unique items ---
        trader_selection = random.sample(trader_pool, min(5, len(trader_pool)))

        # --- Build inventory dynamically ---
        wandering_trader_inventory = {}
        for name in trader_selection:
            # Look up price from weapons_data if available
            if name in weapons_data:
                base_price = weapons_data[name].get("price", random.randint(10, 50))
            else:
                # Fallback prices for non-weapon items
                fallback_prices = {
                    "bread": 4, "bandage": 10, "antivenom": 12,
                    "gun oil": 15, "field dressing kit": 20,
                    "ammo cartridge": 10, "gold nugget": 35,
                    "silver watch": 15, "boots": 10
                }
                base_price = fallback_prices.get(name, random.randint(5, 25))

            # Add slight random markup/discount (10%–20% variance)
            price = round(base_price * random.uniform(0.9, 1.2))
            quantity = random.randint(2, 6)

            wandering_trader_inventory[name] = ShopItem(name, price, quantity)

        # --- Open shop session ---
        trader_shop = ShopSession(self, self.AI_File, "Wandering Trader", wandering_trader_inventory, "Wandering Trader")
        trader_shop.run_buy_session()

        print("You thank the trader and continue down the dusty trail.")
        time.sleep(1)
        
    def encounter_hermit_challenge(self):
        print("\nWhile traveling, you stumble upon an old hermit sitting by a fire.")
        time.sleep(1)
        print("He eyes you carefully and says, 'Prove yourself in my three trials, and I'll reward you handsomely.'")
        print("Do you accept the Hermit's Challenge? (yes/no)")
        choice = input(": ").strip().lower()
        
        if choice != "yes":
            print("You nod politely and continue your journey.")
            return
        
        time.sleep(1)
        print("\nFirst Trial: The Bison Hunt.")
        combat = Combat(self)
        combat.FindAttacker("rattlesnake")
        combat.Attack()
        if self.Health <= 0:
            print("The rattlesnake was too much for you. The challenge ends.")
            print("The hermit heals you just enough to continue on your journey.")
            self.Health += 50
            return
        print("You successfully made it through the first trial, 2 more continue.")
        time.sleep(2,)

        print("\nSecond Trial: The Canyon Crossing.")
        print("You arrive at a deep canyon with a narrow ledge.")
        time.sleep(1)
        print("1) Use your rope to secure a path") 
        print("2) Carefully edge across without rope")
        choice = input("Choice: ").strip()
        if choice not in ["1", "2"]:
            print("Invalid choice. You hesitate and fall into the canyon!")
            self.Health -= 20
            print("-20 health.")
            if self.Health <= 0:
                print("You succumb to your injuries.")
                print("The hermit heals you just enough to continue on your journey.")
                self.Health += 50
                return
        time.sleep(1)
        print("You approach the canyon's edge, the wind howling around you.")
        time.sleep(1)
        # Handle the rope choice
        if choice == "1":
            if "rope" in self.itemsinventory:
                print("You use your rope to secure your path and cross safely.")
                self.itemsinventory["rope"] -= 1
                if self.itemsinventory["rope"] <= 0:
                    del self.itemsinventory["rope"]
            else:
                print("You do not have a rope, so you must cross carefully.")
                print("Without rope, you carefully edge across...")
                time.sleep(2)
                if random.randint(1, 3) == 1:
                    print("A rock gives way—you slip and fall into the canyon!")
                    self.Health -= 30
                    print("-30 health.")
                    if self.Health <= 0:
                        print("You succumb to your injuries.")
                        print("The hermit heals you just enough to continue on your journey.")
                        self.Health += 50
                        return
                else:
                    print("You manage to cross safely.")
        if choice == "2":
            print("You carefully edge across the narrow ledge...")
            time.sleep(2)
            if random.randint(1, 3) == 1:
                print("A gust of wind nearly knocks you off balance!")
                self.Health -= 10
                print("-10 health.")
                if self.Health <= 0:
                    print("You succumb to your injuries.")
                    print("The hermit heals you just enough to continue on your journey.")
                    self.Health += 50
                    return
            else:
                print("You manage to cross safely.")
        
        print("You successfully made it through the first trial, 2 more continue.")
        time.sleep(2,)

        print("\nFinal Trial: The Night of Wild Beasts.")
        print("The hermit leads you to a clearing and sets up camp.")
        print("He warns you that wild beasts may attack during the night.")
        time.sleep(1)
        print("1) Stay alert and ready")
        print("2) Sleep soundly, hoping the wild animals will miss you.")
        choice = input("Choice: ").strip()
        if choice not in ["1", "2"]:
            print("Invalid choice. You hesitate and are caught off guard!")
            combat = Combat(self)
            self.add_effect("+20HP", target="enemy")
            combat.FindAttacker("pack of wolves")
            combat.Attack()
            if self.Health <= 0:
                print("You succumb to your injuries.")
                print("The hermit heals you just enough to continue on your journey.")
                self.Health += 50
                return
        if choice == "1":
            print("You stay alert, ready for any danger.")
            time.sleep(1)
            print("Suddenly, a pack of wolves emerges from the shadows!")
            time.sleep(1)
            self.add_effect("stun", target="enemy")
            print("You ready your weapon and prepare to fight.")
            print("The wolves are surprised by your readiness.")
            combat = Combat(self)
            combat.FindAttacker("pack of wolves")
            combat.Attack()
            if self.Health <= 0:
                print("The wolves overwhelmed you. The challenge ends.")
                print("The hermit heals you just enough to continue on your journey.")
                self.Health += 50
                return
            else:
                print("You survive the wolves onslaught.")
        if choice == "2":
            print("You sleep soundly, hoping the wild animals will miss you.")
            Random = random.randint(1,3)
            if Random != 1:
                print("You are attacked by wolves during the night!")
                combat = Combat(self)
                combat.FindAttacker("pack of wolves")
                combat.Attack()
                if self.Health <= 0:
                    print("The wolves overwhelmed you. The challenge ends.")
                    print("The hermit heals you just enough to continue on your journey.")
                    self.Health += 50
                    return
            else:
                print("You wake up to find the wolves have passed by without noticing you.")
                print("You pass the night in peace under the stars.")
                time.sleep(1)

        time.sleep(1)
        # Reward phase
        print("\nThe hermit nods approvingly. 'You have proven yourself.'")
        time.sleep(2,)
        gold_reward = 25
        self.gold += gold_reward
        self.Speed += 1
        loot_item = random.choice(["carved horn", "ammo belt", "gold nugget", "winchester barrel"])
        self.loot_drop(loot_item)
        print(f"You gain {gold_reward} gold and the hermit gives you a {loot_item}.")
        print("You have learned from this adventure, you become more agile. +1 speed.")
        print("You may choose either a strength, shadow, or trail skill increase.")
        skill_choice = self.AI_File.parse_choice(["strength", "shadow", "trail"], "Which skill do you choose to improve? (strength/shadow/trail): ").strip().lower()
        if choice == "strength":
            self.strength_skill += 2
            print("Your strength skill increases by 2.")
        elif choice == "shadow":
            self.shadow_skill += 2
            print("Your shadow skill increases by 2.")
        elif choice == "trail":
            self.trail_skill += 2
            print("Your trail skill increases by 2.")
        time.sleep(2,)

    def encounter_haunted_house(self):
        print("\nYou approach a dilapidated house on the hill as dusk settles.")
        print("Locals whisper it's haunted—and that a fortune lies within.")
        print("1) Enter cautiously")
        print("2) Walk away")
        choice = input("Choice: ").strip()
        if choice == "2":
            print("You decide it's not worth the trouble. You lose an hour.")
            self.Time += 1
            return
        print("Your lantern's glow slips through broken windows as you step inside.")
        time.sleep(2)

        # Phase 2: Entry hall
        print("\nIn the entry hall you see:")
        print("1) A creaking staircase upward")
        print("2) A dark hallway to your left")
        print("3) A door on your right")
        path = input("Choose a path (1/2/3): ").strip()

        # Phase 3: Branching hazards
        if path == "1":
            print("\nHalfway up the staircase, a loose board snaps!")
            if "lantern" in self.itemsinventory:
                print("From the light of your lantern you notice a couple possible booby traps.")
                print("You avoid them carefully.")
            else:
                if self.perform_stat_check(self.strength_skill, base_target=15) == True:
                    print("You leap back just in time. No harm done.")
                else:
                    print("An old rifle mounted on the wall fires—you're hit!")
                    dmg = random.randint(1,15)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            time.sleep(2)
            print("At the top you find an empty, dusty bedroom. Nothing of value.")
            time.sleep(2)

        elif path == "2":
            print("\nYou follow the hallway, but the floor gives way!")
            if "rope" in self.itemsinventory:
                print("You use the rope to loop around the closest door knob and pull yourself up.")
            else:
                if self.perform_stat_check(self.strength_skill, base_target=12) == True:
                    print("You grab the railing and swing back to safety.")
                else:
                    print("You crash into the cellar below—painfully bruised.")
                    self.Health -= 5
                    print("-5 health.")
            print("You find something in the gloom:")
            self.loot_drop(random.choice(self.uncommon_loot))
            time.sleep(2)

        elif path == "3":
            print("\nYou open the door into a study filled with scattered papers.")
            print("1) Search the papers")
            print("2) Pocket a silver locket on the desk")
            sub = input("Choice (1/2): ").strip()
            if sub == "1":
                print("You sift through musty documents—nothing of value now, but who knows what secrets they held.")
                # could flag for future quest
            else:
                print("You slip the silver locket into your pocket. It's worth at least 10 gold.")
                self.loot_drop("silver watch")
            time.sleep(2)

        else:
            print("You hesitate too long and fall through a rotten floorboard!")
            self.Health -= 5
            print("-5 health.")
            time.sleep(2)

        # Phase 4: The Finale
        print("\nA sudden crash upstairs scares you.")
        print("1) Flee immediately")
        print("2) Search one last room")
        final = input("Choice (1/2): ").strip()
        if final == "1":
            print("You dash out into the night, empty-handed but alive.")
            return

        # search finale
        print("You steel yourself and push on into the final room...")
        if random.randint(1, 2) == 1:
            print("You finally find the final room")
            combat = Combat(self)
            combat.FindAttacker("looter")
            combat.Attack()
            combat = Combat(self)
            combat.FindAttacker("looter")
            combat.Attack()
            print("You found a hidden cache!")
            self.loot_drop(random.choice(self.rare_loot))
            self.loot_drop(random.choice(self.uncommon_loot))
        else:
            print("You steel yourself and push on into the final room...")
            print("An unearthly light seeps from the entire room, collecting in front of you.")
            combat = Combat(self)
            combat.FindAttacker("phantom gunslinger")
            escape = combat.Attack()
            if escape == True:
                print("You manage to escape the Phantom Gunslinger, fleeing the building.")
            else:
                print("You defeated the Phantom Gunslinger! You claim his ghostly treasure.")
                self.gold += 75
                self.loot_drop("winchester rifle")
                self.loot_drop(random.choice(self.ultra_rare_loot))
                self.loot_drop(random.choice(self.uncommon_loot))
                self.loot_drop(random.choice(self.common_loot))
        time.sleep(2)

    def encounter_cave_of_shadows(self):
        print("\nAs you travel, you discover a yawning cave entrance hidden behind a thicket.")
        time.sleep(1)
        print("Locals spoke of a 'Cave of Shadows' said to contain riches... and danger.")
        print("Do you dare enter? (yes/no)")
        choice = input(": ").strip().lower()

        if choice != "yes":
            print("You decide not to risk it and move on.")
            return

        time.sleep(1)
        print("\nYou step cautiously into the darkness.")
        if "lantern" in self.itemsinventory:
            print("Your lantern lights the way, revealing the treacherous path.")
            self.itemsinventory["lantern"] -= 1
            if self.itemsinventory["lantern"] <= 0:
                del self.itemsinventory["lantern"]
        else:
            print("Without a lantern, it's hard to see. Every step is a gamble.")
            if random.randint(1, 4) != 1:
                print("You trip on a rock and fall hard.")
                self.Health -= 10
                print("-10 health.")
                if self.Health <= 0:
                    self.Death("You succumbed to your injuries in the dark cave.")

        time.sleep(1)
        print("\nDeeper inside, you find a split: (1) Left tunnel (2) Right tunnel")
        path = input(": ").strip()
        if path == "1":
            print("You take the left tunnel...")
            if random.randint(1, 3) == 1:
                print("A loose rock falls from above, striking you!")
                self.Health -= 10
                print("-10 health.")
                if self.Health <= 0:
                    print("You collapse, never to leave the cave.")
                    self.Death("You succumbed to your injuries in the dark cave.")
            print("A bear emerges from the shadows!")
            combat = Combat(self)
            combat.FindAttacker("bear")
            escape = combat.Attack()
            if self.Health <= 0:
                self.Death("The bear has defeated you in the cave.")
        else:
            print("You take the right tunnel...")
            print("A pack of wolves lurks here!")
            combat = Combat(self)
            combat.FindAttacker("pack of wolves")
            escape = combat.Attack()
            if self.Health <= 0:
                self.Death("The wolves have defeated you in the cave.")

        time.sleep(1)
        if escape == True:
            print("You leave the cave battered, without any treasure...")
            return
        print("\nAt last, you find a hidden chamber filled with glinting treasures!")
        gold_found = random.randint(40, 70)
        self.gold += gold_found
        rare_loot = random.choice(["winchester barrel", "winchester stock", "sharps rifle", "silver bar"])
        self.loot_drop(rare_loot)
        print(f"You gain {gold_found} gold and discover a {rare_loot}!")

        # Optional skill boost
        self.shadow_skill += 1
        print("Navigating the cave improved your shadow skill! +1 shadow_skill.")

    def encounter_haunted_mine(self):
        print("\nYou have followed the rumors to the old mine.")
        print("They say it was abandoned after a tragic accident, but treasure might still lie within.")
        print("1) Enter the mine cautiously")
        print("2) Walk away")
        choice = input("Choice: ").strip()
        if choice == "2":
            print("You decide it's not worth the risk. You lose an hour.")
            self.Time += 1
            return

        print("You step into the mine. The air is cold and heavy with dust.")
        time.sleep(2)
        print("\nYou see two tunnels branching ahead:")
        print("1) The left tunnel, with old tracks")
        print("2) The center tunnel, faintly lit by a lantern")
        path = input("Choose a tunnel (1/2): ").strip()

        # Stage 1: Tunnel choice
        if path == "1":
            print("\nYou follow the tracks deeper into the mine.")
            print("You inspect an abandoned minecart on the side of the tracks.")
            loot = random.choice(["gold nugget", "lantern", "rope", "rifle"])
            self.loot_drop(loot)
            print("Suddenly, you hear the rumble of a minecart approaching!")
            print("A minecart is barreling down the tracks straight at you!")
            print("You have only a split second to react!")
            time.sleep(2)
            
            print("What do you do?")
            options = ["1) Try to stop the minecart with your strength",
                    "2) Dodge out of the way",
                    "3) Use your rope to snag the cart"]
            while True:
                for o in options:
                    print(o)
                action = input("Choose (1/2/3): ").strip()
                if action == "3" and "rope" not in self.itemsinventory:
                    print("You reach for your rope, but realize you don't have one!")
                    options = [o for o in options if not o.startswith("3)")]
                    continue
                break

            # Minecart outcome
            if action == "1":
                if self.perform_stat_check(self.strength_skill, base_target=16) == True:
                    print("You brace yourself and stop the minecart just in time! Your strength saves you.")
                    self.strength_skill += 1
                    print("+1 Strength Skill.")
                else:
                    print("You try to stop the minecart, but it's too heavy! It knocks you aside.")
                    dmg = random.randint(10, 20)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "2":
                if self.perform_stat_check(self.Speed, base_target=14) == True:
                    print("You leap aside with quick reflexes, narrowly avoiding the cart.")
                    self.shadow_skill += 1
                    print("+1 Shadow Skill.")
                else:
                    print("You try to dodge, but the cart clips you as it passes.")
                    dmg = random.randint(15, 25)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "3":
                print("You expertly rope the minecart, slowing it enough to avoid harm.")
                self.itemsinventory["rope"] -= 1
                if self.itemsinventory["rope"] <= 0:
                    del self.itemsinventory["rope"]
                print("Your rope is lost in the process.")

            time.sleep(2)
            print("You get up, shaken. The burning lantern and pickaxe make you suspicious—someone else is here.")
        elif path == "2":
            print("\nYou follow the faint light. The tunnel twists and you find a lantern and a pickaxe, both recently used.")
            print("Suddenly, a minecart comes flying out of the darkness!")
            print("Because you noticed the clues, you have a better chance to avoid the minecart.")
            options = ["1) Try to stop the minecart with your strength",
                    "2) Dodge out of the way",
                    "3) Use your rope to snag the cart"]
            while True:
                for o in options:
                    print(o)
                action = input("Choose (1/2/3): ").strip()
                if action == "3" and "rope" not in self.itemsinventory:
                    print("You reach for your rope, but realize you don't have one!")
                    options = [o for o in options if not o.startswith("3)")]
                    continue
                break

            # Minecart outcome with bonus
            if action == "1":
                if self.perform_stat_check(self.strength_skill, base_target=12) == True:
                    print("You brace yourself and stop the minecart just in time! Your strength saves you.")
                    self.strength_skill += 1
                    print("+1 Strength Skill.")
                else:
                    print("You try to stop the minecart, but it's too heavy! It knocks you aside.")
                    dmg = random.randint(5, 12)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "2":
                if self.perform_stat_check(self.Speed, base_target=14) == True:
                    print("You leap aside with quick reflexes, narrowly avoiding the cart.")
                    self.shadow_skill += 1
                    print("+1 Shadow Skill.")
                else:
                    print("You try to dodge, but the cart clips you as it passes.")
                    dmg = random.randint(5, 10)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "3":
                print("You expertly rope the minecart, slowing it enough to avoid harm.")
                self.itemsinventory["rope"] -= 1
                if self.itemsinventory["rope"] <= 0:
                    del self.itemsinventory["rope"]
                print("Your rope is lost in the process.")

            time.sleep(2)
            print("You get up, shaken. The burning lantern and pickaxe make you suspicious—someone else is here.")
        else:
            print("\nYou squeeze through the collapsed tunnel. It's slow going, but you avoid any immediate danger.")
            print("You find a side passage and hear faint footsteps echoing deeper in the mine.")
            time.sleep(2)

        # Stage 2: Suspicion and final event
        print("\nYou press on, more cautious now. The tunnel opens into a large chamber.")
        print("You spot a shadowy figure digging at the far wall. He turns, startled by your presence.")
        print("1) Call out to him")
        print("2) Sneak closer")
        print("3) Leave quietly")
        final = input("What do you do? (1/2/3): ").strip()
        if final == "1":
            print("You call out. The figure panics and drops a small sack as he flees into the darkness.")
            self.loot_drop("gold nugget")
            print("You pick up the sack and find a gold nugget inside!")
        elif final == "2":
            if self.perform_stat_check(self.shadow_skill, base_target=15) == True:
                print("You sneak closer and see the figure uncovering a hidden stash.")
                print("He flees, leaving the loot behind. You claim it for yourself!")
                self.loot_drop("gold nugget")
                self.loot_drop("silver bar")
            else:
                print("You try to sneak, but stumble on loose gravel.")
                print("The figure hears you and throws a lighted match on some barrels nearby.")
                print("You realize he is about to blow up the entire mine!")
                print("You run for your life, with only seconds to spare.")
                time.sleep(2)
                dmg = random.randint(10, 20)
                self.Health -= dmg
                print(f"You barely escape the blast, but some shrapnel hits your back. -{dmg} health.")
                time.sleep(2)
                print("Running quickly, you find the manage to catch the looter outside the mine.")
                print("He surrenders, begging for mercy.")
                print("Do you take him with you? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    self.caravan.append("outlaw")
                    print("You take the outlaw with you, hoping to turn him in for a reward.")
                if choice == "no":
                    print("In gratitude, he gives you a small pouch of gold before running off.")
                    self.gold += 20
                
        else:
            print("You decide not to risk it and leave the mine quietly, but you feel you missed out on something valuable.")
            self.Time += 1
            return

        print("You leave the haunted mine, feeling both richer and a little uneasy about what you found.")
        time.sleep(2)

    def encounter_earp_intro(self):
        print("At the Oriental Saloon, a hush falls. Morgan Earp has been murdered in cold blood.")
        print("Wyatt Earp leans on the bar, eyes cold. 'The law won't act. I'm forming a posse.'")
        choice = input("Do you ride with Wyatt Earp for vengeance? (yes/no): ").strip().lower()
        if choice == "yes":
            print("You swear loyalty to the Vendetta Ride.")
            self.Tquest = "earp_vendetta"
            self.set_flag("earp_vendetta", "stage", 1)
            print("Wyatt gives you a box of shells and a share of collected funds. +15 gold.")
            self.gold += 15
            self.loot_drop("ammo cartridge")
            current_bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
            self.set_flag("earp_vendetta", "bonus", current_bonus + 1)
        else:
            print("You refuse. Wyatt nods curtly, 'Then stay out of our way.'")
            self.Tquest = "None"
        self.quest_today = True

    def encounter_earp_stage1(self):
        if self.Health < 90:
            print("The posse tends to your wounds.")
            self.Health = 90
            print("You are healed to 90 health.")
        print("The Vendetta Posse rides to Pete Spence's wood camp.")
        print("A known outlaw is holed up there, armed and waiting.")
        print("Options:")
        print("1) Ride in with the posse guns blazing.")
        print("2) Flank around through the brush.")
        print("3) Refuse to fight.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("outlaw gunman")
            combat.Attack()
            if self.Health > 0:
                print("You help cut down the outlaw. The posse pushes forward.")
                self.gold += 10
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 1)
            else:
                print("You fall in the shootout. The posse drags you away as they move on.")
                self.Tquest = "None"
        elif choice == "2":
            if self.perform_stat_check(self.shadow_skill, base_target=15) == True:
                print("You flank the outlaw's position, forcing him into Wyatt's fire. Success!")
                self.gold += 15
                self.loot_drop("revolver")
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 2)
            else:
                print("You trip in the brush — shots ring out! You're hit. -12hp")
                self.Health -= 12
        else:
            print("You hang back. The posse fights without you.")
            bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
            self.set_flag("earp_vendetta", "bonus", bonus - 1)

        self.set_flag("earp_vendetta", "stage", 2)
        self.quest_today = True

    def encounter_earp_stage2(self):
        if self.Health < 90:
            print("The posse tends to your wounds.")
            self.Health = 90
            print("You are healed to 90 health.")
        print("At dawn, word comes: Florentino Cruz, a Cowboy, is spotted near the San Pedro River.")
        print("Wyatt growls, 'He helped ambush Morgan.'")
        print("Options:")
        print("1) Ride hard to catch him.")
        print("2) Stay behind in camp.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("cowboy scout")
            combat.Attack()
            if self.Health > 0:
                print("You gun down Florentino Cruz. Wyatt is grim but satisfied.")
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 1)
                self.gold += 20
            else:
                print("You're shot from ambush and collapse.")
                self.Tquest = "None"
        else:
            print("You refuse. Wyatt mutters about weak resolve.")
            bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
            self.set_flag("earp_vendetta", "bonus", bonus - 1)

        self.set_flag("earp_vendetta", "stage", 3)
        self.quest_today = True

    def encounter_earp_stage3(self):
        print("The posse learns the Clanton brothers are nearby.")
        print("Wyatt declares: 'They won't escape justice.'")
        print("Wyatt comes up to you. 'We have limited recources, but do you need extra round or extra healing?")
        choice = input("1 'ammo' or 2 'healing': ").strip().lower()
        if choice ==  "1":
            self.loot_drop("ammo cartridge")
            print("You receive an extra ammo cartridge.")
        else:
            if self.Health <= 90:
                self.Health = 90
                print(f"You receive extra healing. You are at {self.Health} health now.")
            else:
                print("Your health is already full. No healing needed.")
                self.loot_drop("ammo cartridge")
        print("Options:")
        print("1) Confront the Clantons openly.")
        print("2) Set an ambush at the river crossing.")
        print("3) Abandon the vendetta.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("clanton gunfighter")
            combat.Attack()
            if self.Health > 0:
                print("In a fierce shootout, one Clanton falls dead in the dust.")
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 2)
                self.gold += 35
                self.loot_drop("lever-action rifle")
            else:
                print("A Clanton bullet strikes you down. The Vendetta falters.")
                self.Tquest = "None"
        elif choice == "2":
            if self.perform_stat_check(self.trail_skill, base_target=12) == True:
                print("Your ambush works! You take the Clantons by surprise, killing one instantly.")
                self.gold += 25
                self.loot_drop("lever-action rifle")
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 2)
            else:
                print("The Clantons sense danger. They escape into the hills.")
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus - 1)
        else:
            print("You abandon the vendetta. The posse brands you a coward.")
            self.Hostility += 1
            self.Tquest = "None"
        self.quest_today = True
        self.set_flag("earp_vendetta", "stage", 4)

    def encounter_earp_stage4(self):
        print("\nAs you enter town, you spot Wyatt Earp waiting grimly.")
        print("'Word is Curly Bill is holed up here in town. This ends now.'")
        time.sleep(2)
            
        ready = self.AI_File.parse_YN("Are you ready for the final confrontation? (yes/no): ")
        if ready == "yes":
            print("You nod to Wyatt, ready to face Curly Bill.")
        else:
            print("You tell Wyatt you need a moment to prepare.")
            print("Find him at the Saloon when you're ready.")
            return
        print("The Vendetta Posse closes in on Curly Bill Brocius at Iron Springs.")
        print("This is the showdown that will decide everything.")
        print("Options:")
        print("1) Charge in alongside Wyatt.")
        print("2) Find a vantage point and snipe.")
        print("3) Hesitate.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("curly bill")
            combat.Attack()
            if self.Health > 0:
                print("Curly Bill is gunned down in a storm of lead. The Vendetta is triumphant!")
                self.gold += 75
                self.loot_drop("sawed-off shotgun")
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 3)
            else:
                print("Curly Bill's scattergun blast drops you. The Vendetta staggers on without you.")
                self.Tquest = "None"
        elif choice == "2":
            if self.perform_stat_check(self.trail_skill, base_target=18) == True:
                print("Your shot finds its mark! Curly Bill falls, Wyatt tipping his hat to you.")
                self.gold += 30
                bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
                self.set_flag("earp_vendetta", "bonus", bonus + 2)
            else:
                print("Your shot misses! Curly Bill fires back, grazing you. -10hp")
                print("If only you had better trail skills...")
                self.Health -= 10
                print("Curly Bill charges your position!")
                combat = Combat(self)
                combat.FindAttacker("curly bill")
                combat.Attack()
        else:
            print("You freeze. The others charge ahead without you.")
            bonus = int(self.get_flag("earp_vendetta", "bonus", 0) or 0)
            self.set_flag("earp_vendetta", "bonus", bonus - 2)

        # Quest complete
        print("The Vendetta Ride is over. The Cowboys are broken, scattered to the winds.")
        self.Tquest = "None"
        self.set_flag("earp_vendetta", "stage", -1)
        rewards = 20 + (int(self.get_flag("earp_vendetta", "bonus", 0) or 0) * 10)
        print(f"You receive {rewards} gold for your efforts.")
        if int(self.get_flag("earp_vendetta", "bonus", 0) or 0) <= 0:
            print("Your neutral actions earned you no bonus or penalty.")
        elif int(self.get_flag("earp_vendetta", "bonus", 0) or 0) == 1:
            print("Your efforts were noted.")
            self.loot_drop("pendant of recognition")
        elif int(self.get_flag("earp_vendetta", "bonus", 0) or 0) >= 3:
            print("Your valor stood out! You are hailed as a hero of the Vendetta.")
            self.loot_drop("vendetta badge")
            print("'You have done well today,' Wyatt says with a grin.")
            print("'Use this badge and the posse will help you once more if needed.'")
        self.quests_done.append("earp_vendetta")
        self.quest_today = True

    def encounter_iron_intro(self):
        if "iron_tracks" in self.quests_done:
            print("You have already completed the Iron Tracks quest.")
            return
        print("At the saloon, you overhear a group of railroad men talking.")
        print("'Tracks are coming through this territory... but bandits don't like progress.'")
        choice = self.AI_File.parse_YN("Do you agree to help the railroad? (yes/no): ")
        if choice == "yes":
            print("You agree to aid the foreman in keeping the line safe.")
            self.Tquest = "iron_tracks"
            self.set_flag("iron_tracks", "stage", 1)
            print("They give you a reward of 10 gold and a box of ammo cartridges.")
            self.gold += 10
            self.loot_drop("ammo cartridge")
            current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
            self.set_flag("iron_tracks", "bonus", current_bonus + 2)
        else:
            print("You shake your head. The railroad men mutter that you're missing an opportunity.")
            self.Tquest = "None"
        time.sleep(2,)
        self.quest_today = True

    def encounter_iron_stage1(self):
        print("The railroad foreman storms into town.")
        print("'A wagon full of steel rails and tools never arrived. Bandits must've taken it!'")
        print("Options:")
        print("1) Track the missing wagon.")
        print("2) Refuse to help.")
        choice = input(": ").strip()

        if choice == "1":
            if self.Health < 90:
                print("The foreman sees your wounds and tends to them.")
                self.Health = 90
                print("You are healed to 90 health.")
            print("You ride out and find the wagon under bandit guard!")
            if self.perform_stat_check(self.trail_skill, base_target=14) == True:
                print("You sneak up and catch the bandits off guard, taking them down silently.")
                self.gold += 15
                self.loot_drop("ammo cartridge")
                current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                self.set_flag("iron_tracks", "bonus", current_bonus + 2)
                self.trail_skill += 1
            else:
                print("The bandits spot you! A fight breaks out.")
                combat = Combat(self)
                combat.FindAttacker("bandit")
                escape = combat.Attack()
                if escape == False:
                    print("You defeat the bandits and recover the supplies.")
                    self.gold += 20
                    self.loot_drop("ammo cartridge")
                    current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                    self.set_flag("iron_tracks", "bonus", current_bonus + 1)
                else:
                    print("You retreat to save yourself.")
                    self.Tquest = "None"
                    current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                    self.set_flag("iron_tracks", "bonus", current_bonus - 1)
        else:
            print("The foreman scowls. 'Fine, I'll find someone else.'")
            current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
            self.set_flag("iron_tracks", "bonus", current_bonus - 2)
        self.set_flag("iron_tracks", "stage", 2)
        time.sleep(2,)
        self.quest_today = True

    def encounter_iron_stage2(self):
        print("Night falls. You hear shouting at the new train depot!")
        print("Options:")
        print("1) Investigate the depot.")
        print("2) Stay away.")
        choice = input(": ").strip()

        if choice == "1":
            print("You sneak into the depot and spot saboteurs planting dynamite.")
            if self.perform_stat_check(self.shadow_skill, base_target=16) == True:
                print("You catch one saboteur alive. He blurts out about a coming train heist.")
                self.set_flag("iron_tracks", "stage", 3)
            else:
                print("The saboteurs notice you! A fight breaks out.")
                combat = Combat(self)
                combat.FindAttacker("saboteur")
                escape = combat.Attack()
                if escape == False:
                    if self.Health > 0:
                        print("You stop the sabotage, but the plot deepens.")
                        self.set_flag("iron_tracks", "stage", 3)
                    else:
                        print("You fall at the depot. The railroad effort is doomed.")
                        self.Tquest = "None"
                else:
                    print("You flee, unable to stop the saboteurs.")
                    current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                    self.set_flag("iron_tracks", "bonus", current_bonus - 1)
        else:
            print("You ignore the commotion. In the morning, the depot lies in ruins.")
            self.Hostility += 1
            self.Tquest = "None"
        time.sleep(2,)
        self.quest_today = True

    def encounter_iron_stage3(self):
        bonus_used = False
        if self.Health < 90:
            print("The foreman sees your wounds and tends to them.")
            self.Health = 90
            print("You are healed to 90 health.")
        print("Word spreads: the first train is rolling in with gold and passengers.")
        print("Bandits plan a heist! The foreman begs for your help.")
        print("Options:")
        print("1) Defend the train.")
        print("2) Let the bandits have it.")
        choice = input(": ").strip()

        if choice == "1":
            print("You climb aboard as the train whistles into the valley...")
            print("The supply carriage holds a wealth of ammo, you won't be short of it this fight!")
            time.sleep(2,)
            print("As the train chugs along, 7 mounted bandits ride up, firing their pistols at the train!")
            if int(self.get_flag("iron_tracks", "bonus", 0) or 0) >= 2:
                print("You may spend two bonus points you have gained to gain a temporary boost!")
                print("Will you spend them now?")
                choice = input(": ").strip()
                if choice.lower() == "yes":
                    current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                    self.set_flag("iron_tracks", "bonus", current_bonus - 2)
                    self.MaxHealth += 20
                    self.Health += 20
                    bonus_used = True
                    
                    print("You feel invigorated!")
                else:
                    print("You choose to save your bonus points.")
            mounted_bandits = 5   # riders outside
            bandits_in_car = 2    # already onboard
            car_health = 100
            turns_elapsed = 0
            while car_health > 0 and turns_elapsed < 7:
                print(f"\nMounted bandits outside: {mounted_bandits}")
                print(f"Bandits in passenger cars: {bandits_in_car}")
                print(f"Your Health: {self.Health}")
                print(f"Train car health: {car_health}")
                print(f"If the train loses all health, it will be derailed!")
                print(f"Turns until escape: {8 - turns_elapsed}")
                input("Press Enter to continue...")

                print("\nChoose your action:")
                print("1) Climb onto the roof and shoot at mounted bandits.")
                print("2) Defend with your melee in the passenger cars.")
                print("3) Take cover and heal behind crates.")
                print("4) Rush forward and fight with your fists.")

                choice = input(": ").strip()

                # --- Option 1: Shoot from roof ---
                if choice == "1":
                    if mounted_bandits <= 0:
                        print("No mounted bandits left to shoot at!")
                        continue
                    print("Which weapon would you like to use?")
                    print("1) Rifle")
                    print("2) Shotgun")
                    print("3) Revolver")
                    weapon_choice = input(": ").strip()
                    if weapon_choice not in ["1", "2", "3"]:
                        print("Invalid choice. You lose your chance to shoot!")
                        continue
                    if weapon_choice == "1" and any(item in self.weapons["rifle"] for item in self.itemsinventory):
                        print("You fire your rifle from the rooftop!")
                        if self.perform_stat_check(self.trail_skill, base_target=12) == True:
                            print("A rider drops, his horse veering off!")
                            mounted_bandits -= 1
                        else:
                            if any(item in self.weapons["rifle"] for item in self.itemsinventory) == False:
                                print("You have no rifle!")
                                print("A shot grazes you. -8hp")
                                self.Health -= 8
                                continue
                            print("You miss! A shot grazes you. -8hp")
                            self.Health -= 8
                    elif weapon_choice == "2" and any(item in self.weapons["shotgun"] for item in self.itemsinventory):
                        print("You blast your shotgun downward at the riders!")
                        if self.perform_stat_check(self.trail_skill, base_target=12) == True:
                            print("A rider is blown clean off his saddle!")
                            mounted_bandits -= 1
                        else:
                            if any(item in self.weapons["shotgun"] for item in self.itemsinventory) == False:
                                print("You have no shotgun!")
                                print("A shot grazes your arm. -6hp")
                                self.Health -= 6
                                continue
                            print("Pellets scatter wide. A return shot hits your arm! -6hp")
                            self.Health -= 6
                    elif weapon_choice == "3" and any(item in self.weapons["revolver"] for item in self.itemsinventory):
                        print("You fire your revolver rapidly!")
                        if self.perform_stat_check(self.trail_skill, base_target=12) == True:
                            print("One rider tumbles off his horse!")
                            mounted_bandits -= 1
                        else:
                            if any(item in self.weapons["revolver"] for item in self.itemsinventory) == False:
                                print("You have no revolver!")
                                print("A rider's bullet clips you. -5hp")
                                self.Health -= 5
                                continue
                            else:
                                print("You miss under pressure. A rider's bullet clips you! -5hp")
                                self.Health -= 5
                    else:
                        print("You have no gun! The riders fire at you mercilessly. -10 hp")
                        self.Health -= 10
                    time.sleep(2)

                # --- Option 2: Defend inside cars ---
                elif choice == "2":
                    if bandits_in_car <= 0:
                        print("No bandits are inside the cars right now.")
                        continue

                    print("You rush into the passenger car where bandits terrorize civilians!")
                    if any(item in self.weapons["melee"] for item in self.itemsinventory):
                        if self.perform_stat_check(self.Speed, base_target=11) == True:
                            print("You slash a bandit and throw him out the window!")
                            bandits_in_car -= 1
                        else:
                            print("The bandit shoots first, grazing your shoulder! -8hp")
                            self.Health -= 8
                    else:
                        if self.perform_stat_check(self.strength_skill, base_target=15) == True:
                            print("You wrestle a bandit to the ground and knock him cold!")
                            bandits_in_car -= 1
                        else:
                            print("He clubs you with his revolver butt! -6hp")
                            self.Health -= 6

                # --- Option 3: Take cover ---
                elif choice == "3":
                    print("You duck behind heavy crates in the cargo car.")
                    print("You tend to your wounds. +15hp")
                    self.Health += 15
                    if self.perform_stat_check(self.shadow_skill, base_target=12) == True:
                        print("Bullets ping off the steel — you stay safe for now.")
                    else:
                        print("A stray shot punches through, grazing you! -4hp")
                        self.Health -= 4

                # --- Option 4: Melee rush ---
                elif choice == "4":
                    print("You charge forward, fists swinging!")
                    if bandits_in_car > 0:
                        if self.perform_stat_check(self.strength_skill, base_target=14) == True:
                            print("You knock a bandit out cold in brutal close combat!")
                            bandits_in_car -= 1
                        else:
                            print("He smashes you with the butt of his gun! -7hp")
                            self.Health -= 7
                    else:
                        print("There's nobody nearby to fight in melee!")
                elif choice == "5":
                    print("You take a moment to catch your breath and tend to your wounds. +15hp")
                    self.Health += 15
                else:
                    print("Invalid choice.")
                    turns_elapsed -= 1
                    continue
                turns_elapsed += 1

                # --- Bandit boarding mechanic ---
                Random = random.randint(1, 4)
                if  Random <= 2:
                    print("A rider leaps onto the train roof and drops into a car!")
                    if mounted_bandits > 2:
                        mounted_bandits -= 1
                        bandits_in_car += 1
                elif Random == 3:
                    if mounted_bandits > 0:
                        print("The bandits attempt to shoot you while riding.")
                        if random.randint(1, 10) <= self.shadow_skill:
                            print("You dodge the bullets!")
                        else:
                            self.Health -= 15
                            print("You lost 15 health.")
                    else:
                        print("No bandits are mounted.")
                else:
                    print("You gain a moment of respite.")

                if bandits_in_car > 0:
                    print("Bandits are still looting the car!")
                    car_health -= bandits_in_car * 10

                # --- Check for defeat ---
                if self.Health <= 0 or car_health <= 0:
                    if self.Health <= 0:
                        print("You collapse on the train floor. The bandits overrun it.")
                        print("A passenger revives you, but the bandits have already left with the loot.")
                        self.Health = 20
                        current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                        self.set_flag("iron_tracks", "bonus", current_bonus - 2)
                    else:
                        current_bonus = int(self.get_flag("iron_tracks", "bonus", 0) or 0)
                        self.set_flag("iron_tracks", "bonus", current_bonus - 1)
                        print("The car burns around you.")
                        print("The bandits have already taken everything of value.")
                    if bonus_used == True:
                        self.MaxHealth -= 20
                    return

                # --- Check for victory ---
                if mounted_bandits <= 0 and bandits_in_car <= 0:
                    print("\nThe last bandit falls! The train passengers cheer your bravery!")
                    break

            else:
                print("\nThe train arrives safely at the next station.")
                print("You helped save the railroad! The foreman rewards you handsomely. +35 gold")
                self.gold += 35
                self.loot_drop(random.choice(self.rare_loot))
                self.set_flag("iron_tracks", "stage", 4)
            if bonus_used == True:
                self.MaxHealth -= 20

        else:
            print("You stay behind. The train arrives looted, passengers shaken.")
            self.Hostility += 2
            self.Tquest = "None"
        time.sleep(2,)
        self.quest_today = True

    def encounter_iron_stage4(self):
        if self.Health < 90:
            print("The foreman sees your wounds and tends to them.")
            self.Health = 90
            print("You are healed to 90 health.")
        print("The railroad foreman rushes to you. 'They're going to blow the bridge!'")
        print("Options:")
        print("1) Race ahead with guards to stop the dynamite gang.")
        print("2) Ignore it.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("saboteur chief")
            combat.Attack()
            if self.Health > 0:
                print("You save the bridge! The train can continue.")
                self.set_flag("iron_tracks", "stage", 5)
            else:
                print("You fall. The bridge collapses. The railroad halts here forever.")
                self.Tquest = "None"
        else:
            print("You turn away. Hours later, the bridge collapses with a thunderous roar.")
            self.Hostility += 2
            self.Tquest = "None"
        time.sleep(2,)
        self.quest_today = True

    def encounter_iron_stage5(self):
        if self.Health < 90:
            print("The foreman sees your wounds and tends to them.")
            self.Health = 90
            print("You are healed to 90 health.")
        print("A notorious outlaw, the Dynamite Kid, rides into town with crates of explosives.")
        print("He plans to stop the railroad once and for all.")
        print("Options:")
        print("1) Confront him in the streets.")
        print("2) Try to ambush him.")
        print("3) Walk away.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("dynamite dave")
            combat.Attack()
            if self.Health > 0:
                print("You defeat Dynamite Dave in a blazing showdown!")
                if int(self.get_flag("iron_tracks", "bonus", 0) or 0) <= 0:
                    print("")
                self.gold += 70
                self.loot_drop("winchester rifle")
                print("The railroad is saved. The railroad has been added to the towns!")
            else:
                print("The Dynamite Dave plants his bombs. The town burns.")
                self.Hostility += 3
        elif choice == "2":
            if random.randint(1,10) <= self.shadow_skill:
                print("You ambush him successfully, taking his explosives.")
                self.loot_drop("ammo belt")
                self.gold += 75
            else:
                print("The ambush fails. You're caught in a blast!")
                self.Health -= 30
        else:
            print("You walk away. By dusk, explosions echo across the prairie.")
            self.Hostility += 2

        # Quest complete
        self.Tquest = "None"
        self.set_flag("iron_tracks", "stage", 0)
        self.quests_done.append("iron_tracks")
        self.quest_today = True

    def coyote_camp_quest(self):
        print("You arrive at Coyote Camp and find a group of bandits plotting a robbery!")
        combat = Combat(self)
        combat.FindAttacker("bandit")
        combat.Attack()
        if self.Health > 0:
            print("You defeat the bandits and find some loot.")
            self.loot_drop("gold nugget")
            self.loot_drop("pistol_ammo")

    def run_final_mission(self):
        print("\nYou arrive at Devil's Canyon. The river roars below.")
        print("The US Marshal points. 'He's barricaded at the far end. We need to clear the pass!'")
        input("Press Enter to begin the assault...")

        # --- Part 1: The Canyon Battle ---
        print("\nThe Marshal's men give you covering fire. You move up to take out the warlord's lieutenants.")
        self.damage_modifier += 15
        self.add_effect("Steel Wall")
        combat = Combat(self)
        combat.FindAttacker("warlord_lieutenant")
        combat.Attack()
        self.damage_modifier = 0 # Clear the bonus
        if self.Health <= 0:
            self.Death("You fall in the canyon. The assault fails...")

        print("\nThe lieutenant falls! But a deafening horn echoes from the river.")
        print("An iron-plated gunboat rounds the bend, the 'Coffee Grinder' repeating gun blazing!")
        print("The Marshal yells, 'It's a trap! He's going to shred us! Get to that boat and take control of that gun!'")
        print("'We will cover for you.'")
        time.sleep(3)

        # --- Part 2: Seize the Gun (Skill Challenge) ---
        print("\nYou spot it on the deck: a 'Coffee Mill' rapid-fire gun. You have to take it!")
        print("How will you board the ship?")
        print("Swim across under fire (Strength Check)")
        print("Use your rope to swing from the cliff (Trail Skill Check)")
        print("Sneak along the riverbank to get closer (Shadow Skill Check)")
        
        boarded = False
        choice =  self.AI_File.parse_choice((["swim", "rope", "sneak"]), "Choice (swim, rope, or sneak: ")
        if choice == "swim":
            if self.perform_stat_check(self.strength_skill, base_target=15):
                print("You dive into the churning water and power through the current, climbing aboard!")
                boarded = True
            else:
                print("The current is too strong! You're washed downstream but manage to grab the anchor line.")
                print("You climb aboard, exhausted. -15 health.")
                self.Health -= 15
                boarded = True

        elif choice == "rope":
            if "rope" in self.itemsinventory and self.perform_stat_check(self.trail_skill, base_target=12):
                print("You swing across like a hawk, landing hard on the deck!")
                self.itemsinventory["rope"] -= 1 # Use the rope
                boarded = True
            else:
                print("You misjudge the swing! You slam into the iron hull and fall to the deck.")
                print("-20 health.")
                self.Health -= 20
                boarded = True

        elif choice == "sneak":
            if self.perform_stat_check(self.shadow_skill, base_target=14):
                print("You slip through the shadows and climb onto the back of the boat unnoticed!")
                boarded = True
            else:
                print("You're spotted! A sniper pegs you as you climb! -25 health.")
                self.Health -= 25
                boarded = True

        if self.Health <= 0:
            print("Your wounds are too great. You collapse on the deck...")
            self.Death("You have died while trying to get to the Coffee Mill gun.")
            
        if boarded:
            print("\nYou're on the deck! The gunner and his crew turn to face you!")
            
            # Add "gunboat_crew" to your Enemies dict
            # "gunboat_crew": {"health": 90, "damage": 15, "speed": 3, "loot": "common", "type": "human", "behavior": "desperate", "bound": True}
            if self.Health < 50:
                print("You steel yourself for the fight ahead. +30 health.")
                self.Health += 30
            combat = Combat(self)
            combat.FindAttacker("gunboat_crew")
            combat.Attack()

            if self.Health <= 0:
                print("The crew cuts you down before you can reach the gun...")
                self.Death("You have died trying to seize the Coffee Mill gun.")

            print("\nYou take down the crew and seize the Coffee Mill gun!")
            print("The Warlord himself kicks open the cabin door, leveling a rifle at you.")
            print("'You've been a thorn in my side for too long!'")
            
            # --- Part 3: The Final Minigame ---
            self.coffee_mill_showdown() # Call the final minigame function

    def coffee_mill_showdown(self):
        self.change_music("The Last Stand.mp3", -1)
        boss_health = 150
        ship_integrity = 100
        gun_overheated = False
        gun_overheat_ever = True
        boss_behind_cover = True
        extra_damage = 0
        ammo = 50
        print("You finally grab the Coffee Mill gun and prepare for the final showdown!")
        print("The cold steel feels good in your hands as you figure out how the gun works.")
        if self.perform_stat_check(self.trail_skill, base_target=15):
            print("You quickly get the hang of the Coffee Mill's firing mechanism.")
            extra_damage += 5
        if self.perform_stat_check(self.shadow_skill, base_target=15):
            print("You search the deck and find some extra ammo for the Coffee Mill!")
            ammo += 20
        if self.perform_stat_check(self.strength_skill, base_target=15):
            print("You manage to jury-rig a cooling system to prevent overheating!")
            gun_overheat_ever = False

        print("\n--- FINAL SHOWDOWN ---")
        turn = "player"
        while boss_health > 0 and self.Health > 0 and ship_integrity > 0:
            if turn == "player":
                print("\n--- YOUR TURN ---")
                print(f"Your Health: {self.Health} | Warlord: {boss_health} | Ship Integrity: {ship_integrity}")
                print(f"Coffee Mill Ammo: {ammo}")
                if ammo < 1:
                    self.play_sound("no_ammo_coffee")
                    print("You're out of ammo! You must reload.")
                    ammo += 50
                    print(f"Coffee Mill Ammo: {ammo}")
                    time.sleep(4,)
                    continue
                if gun_overheated:
                    print("The gun is overheated! You must let it cool or take cover!")
                    print("1) Take cover and tend wounds (Use Bandage)")
                    print("2) Let it cool (Skip turn)")
                    choice = input("Action: ").strip()
                    if choice == "1" and "bandage" in self.itemsinventory:
                        self.Health = min(self.MaxHealth, self.Health + 25)
                        self.itemsinventory["bandage"] -= 1
                        print("You duck and apply a bandage. +25 Health.")
                    else:
                        print("You wait for the gun to cool...")
                    gun_overheated = False # It cools after one turn
                    turn = 'enemy'
                    time.sleep(4,)
                    continue
                else:
                    print("1) Fire a long burst at the Warlord (High Damage, risks overheat)")
                    print("2) Fire a short, accurate burst (Low Damage, safe)")
                    print("3) Spray the deck to clear out his guards (Damages ship)")
                
                choice = input("Action: ").strip()

                # --- Player Action ---
                
                if choice == "1":
                    dmg = random.randint(30, 45)
                    boss_health -= dmg
                    ammo -= 25
                    print(f"You spray the cabin! The Warlord is hit for {dmg} damage!")
                    self.play_sound("coffee_mill_gun_fire.mp3")
                    if gun_overheat_ever:
                        if random.randint(1, 3) == 1: # 33% chance to overheat
                            print("The gun barrel is glowing red! It's overheated!")
                            self.play_sound("overheat.mp3")
                            gun_overheated = True
                    else: 
                        print("Your cooling system keeps the gun from overheating.")
                    turn = 'enemy'
                    time.sleep(4,)
                    continue
                
                elif choice == "2":
                    dmg = random.randint(15, 20)
                    ammo -= 10
                    boss_health -= dmg
                    print(f"You land an accurate burst! The Warlord is hit for {dmg} damage.")
                    self.play_sound("coffee_mill_gun_fire.mp3")
                    turn = 'enemy'
                    time.sleep(4,)
                    continue
                
                elif choice == "3":
                    ship_dmg = random.randint(10, 15)
                    ship_integrity -= ship_dmg
                    print(f"You clear the deck, but damage the ship! -{ship_dmg} Integrity.")
                    print("The Warlord has fewer men to command next turn.")
                    self.play_sound("coffee_mill_gun_fire.mp3")
                    turn = 'enemy'
                    time.sleep(4,)
                    continue

            else:
                
                # --- Boss Turn ---
                if boss_health <= 0:
                    break # Player wins

                print("\n--- WARLORD'S TURN ---")
                boss_action = random.randint(1, 3)
                
                if boss_action == 1:
                    dmg = random.randint(15, 20)
                    self.Health -= dmg
                    print(f"The Warlord snipes you from the cabin! -{dmg} Health.")
                    turn = 'player'
                    time.sleep(2,)

                
                elif boss_action == 2:
                    print("The Warlord orders his men to fire a cannon at the cliff!")
                    print("The Marshal and his men are forced to take cover!")
                    turn = 'player'
                    time.sleep(2,)

                    
                elif boss_action == 3:
                    print("The Warlord yells, 'Scuttle the ship! Blow it all to hell!'")
                    ship_integrity -= 20
                    print("Explosions rock the boat! -20 Ship Integrity.")
                    turn = 'player'
                    time.sleep(2,)



            # --- Check Lose Conditions ---
            if self.Health <= 0:
                print("The Warlord's shot finds its mark. You fall over the gun...")
                self.Death("Killed by the Warlord in the final showdown.")
                return
                
            if ship_integrity <= 0:
                print("The ship is breaking apart! The explosions consume you!")
                self.Death("Lost at sea after the gunboat was scuttled.")
                return

        # --- Victory ---
        print("\nWith a final scream, the Warlord collapses. The battle is won.")
        print("You steer the burning gunboat to the shore, where the Marshal greets you as a hero.")
        print("The territory is finally safe, thanks to you.")
        
        self.score += 500 # A massive score bonus
        
        # Call the end game/credits (by borrowing from your Death() function)
        print(f"\nYour final score: {self.score}")
        print(f"Days survived: {self.Day}")
        self.Statcheck()
        
        print("\nCredits: Bayne Cheke, Designer and Programmer.")
        print("Music/audio effects: Freesound.com")
        print("Playtesters: Deric R Cheke, Dax Cheke, Jessica Cheke, Silas Cheke, Shai Mckerley, Carson Templeton")
        print("Other contributors: ChatGPT, Gemini AI, Ollama AI")
        print("\n--- THANKS FOR PLAYING! ---")
        exit()

    def change_music(self, filename, loop):
        self.AI_File.change_music(filename, loop)

    def play_sound(self, filename):
        self.AI_File.play_sound(filename)

    def weapon_sound(self, weapon):
        self.AI_File.weapon_sound(weapon)

    def enemy_sound(self, name):
        if name == "rattlesnake":
            self.AI_File.play_sound("rattle_snake.mp3")

    def weapon_ability(self, weapon):
        # Get the weapon's data from the loaded weapons_data
        weapon_info = weapons_data.get(weapon)

        # Exit if the weapon doesn't exist or has no defined ability
        if not weapon_info:
            return
        
        ability = weapon_info.get('ability', 'none')
        
        if ability == 'none':
            return

        # Use a match statement to handle the different abilities
        match ability:
            case "dual wield":
                # Logic for revolver, colt pistol
                if self.itemsinventory[weapon] >= 2:
                    if self.itemsinventory.get("pistol_ammo", 0) > 1:
                        print(f"You pull out both {weapon}s and fire!")
                        self.itemsinventory["pistol_ammo"] -= 1 # Only consumes 1 extra ammo for the 2nd gun
                        self.dmg_modifier_multiply = 2
                        self.play_sound("revolver_shot.mp3")
                        time.sleep(1,)

            case "steady aim":
                # Logic for winchester rifle, henry rifle
                print("You steady your aim...")
                if random.randint(1, 4) == 1:
                    print("A solid hit!")
                    self.dmg_modifier_multiply = 1.5

            case "multi-shot":
                # Logic for remington pistol, derringer pistol
                print("Would you like to fire multiple shots? yes/no")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    print("You fire multiple shots")
                    # Note: The main combat loop already consumed 1 ammo. This consumes 2 *additional* ammo.
                    if self.itemsinventory.get("pistol_ammo", 0) >= 2:
                        Random = random.randint(0, 2)
                        self.itemsinventory["pistol_ammo"] -= 2
                        for i in range(Random):
                            self.play_sound("revolver_shot.mp3")
                            self.damage_modifier += 15
                            time.sleep(1,)
                    else:
                        print("You do not have enough ammo.")
                        time.sleep(2,)

            case "double barrel":
                # Logic for double barrel shotgun
                print("Double Barrel! Fire both barrels? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                # Note: The main combat loop already consumed 1 ammo. This consumes 1 *additional* ammo.
                if choice == "yes" and self.itemsinventory.get("shotgun_ammo", 0) >= 1:
                    self.itemsinventory["shotgun_ammo"] -= 1 # Consume the second barrel's shell
                    print("You fire both barrels in a devastating volley!")
                    self.dmg_modifier_multiply = 2
                    self.play_sound("shotgun.mp3")
                    time.sleep(1,)
                    print("The kickback bruises your arm.")
                    self.Health -= 5
                else:
                    if choice == "yes":
                        print("You don't have enough ammo for a double shot.")
                    else:
                        print("You decide not to use the double shot.")

            case "throw":
                # Logic for tomahawk
                print("Throw your tomahawk for extra damage? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    if self.itemsinventory.get("tomahawk", 0) > 0:
                        self.itemsinventory["tomahawk"] -= 1
                        if self.itemsinventory["tomahawk"] <= 0:
                            del self.itemsinventory["tomahawk"]
                        print("You hurl your tomahawk—deadly accuracy!")
                        self.play_sound("tomahawk.mp3")
                        self.dmg_modifier_multiply = 2
                    else:
                        print("No tomahawks left!")
                else:
                    print("You keep your tomahawk ready for melee.")
            case "quick draw":
                print("Would you like to attempt a quick draw follow-up shot? (yes/no)")
                choice = self.AI_File.parse_YN(": ")
                if choice == "yes":
                    if self.itemsinventory.get("rifle_ammo", 0) >= 1:
                        if random.randint(1, 2) == 1: # 50% chance for a bonus hit
                            self.dmg_modifier_multiply += 0.75 
                            self.play_sound("rifle_shot.mp3")
                            print("The quick draw is successful! The follow-up shot hit for 75% damage.")
                        else:
                            print("The follow-up shot misses!")
                        self.itemsinventory["rifle_ammo"] -= 1 # Consume extra ammo
                        if self.itemsinventory["rifle_ammo"] <= 0:
                            del self.itemsinventory["rifle_ammo"]
                    else:
                        print("You don't have enough rifle ammo for a quick draw.")
                return

            case "precision shot":
                # Logic for sharps rifle
                print("You take a steady breath for a precision shot…")
                if random.randint(1, 4) == 1:
                    print("Bullseye! Your shot hits extra savage.")
                    self.dmg_modifier_multiply = 2

            case "precise strike":
                # Logic for cavalry saber
                print("You slash with your saber, aiming for weak points.")
                self.dmg_modifier_multiply = 1.5
            
            case _:
                # Fallback for any other defined ability
                pass

    def donate_supplies(self):
        
        if not self.itemsinventory:
            print("You have nothing to donate.")
            return

        while True:
            print("\nChoose an item to donate (or 'Done donating'):")
            
            # Create the list of choices for the UI
            item_list = list(self.itemsinventory.keys())
            display_choices = []
            
            # Print the list to the console (like you did before)
            for item, qty in self.itemsinventory.items():
                print(f"{item} x{qty}")
                display_choices.append(item) # Add the item name
            
            print("Done donating")
            display_choices.append("Done donating") # Add the exit option

            # --- FIX 1: Replaced input() with parse_choice ---
            # This will show buttons for each item and "Done donating"
            choice = self.AI_File.parse_choice(display_choices, "Choose item:")
            
            if choice == "done donating":
                break

            # 'choice' is now the item *name* (e.g., "bread")
            item = choice
            max_q = self.itemsinventory[item]
            
            # --- FIX 2: Replaced input() with ask_free_text ---
            num_str = input(f"How many {item}? (1-{max_q}): ")
            
            if not num_str.isdigit() or not (1 <= int(num_str) <= max_q):
                print("Invalid quantity.")
                continue
            
            num = int(num_str)

            # determine bonus per unit
            if item in self.common_loot:      bonus = 0.5
            elif item in self.uncommon_loot:  bonus = 1
            elif item in self.rare_loot:      bonus = 3
            elif item in self.ultra_rare_loot: bonus = 6
            else:                           bonus = 0.5

            self.town_defense_bonus += bonus * num
            self.itemsinventory[item] -= num
            if self.itemsinventory[item] <= 0:
                del self.itemsinventory[item]
            print(f"Donated {num}×{item}: +{bonus*num} defense bonus.")

        print(f"Total town defense bonus: {self.town_defense_bonus}")     

    def write_diary_entry(self):
        # 1) Ask for tone once
        print("\n Night falls. Time to write your diary.")
        tone = self.select_tone()
        
        # --- Calculate Activity Score ---
        activity_score = 1 
        
        if self.day_memory["encounter"]:
            activity_score += 1
        
        if self.day_memory["loot"]:
            activity_score += 1
        
        # --- AI Generation Logic ---
        if self.AI_File.use_ai:
            game_state = self.generate_game_state()
            generated_entry = self.AI_File.generate_diary_entry(
                game_state, 
                self.Health, 
                self.MaxHealth, 
                self.day_memory, 
                tone
            )
            
            lines = [generated_entry]
            activity_score += 1 

        else:
            # --- Template Logic ---
            lines = []
            lines.append(f"I only have {self.Health} health left, {self.health_tone_phrase(tone)}.")

            if self.day_memory["encounter"]:
                lines.append(f"I fought {self.day_memory['encounter']} today, {self.combat_tone_phrase(tone)}.")

            if self.day_memory["loot"]:
                lines.append(f"Found {self.day_memory['loot']} on the way, {self.loot_tone_phrase(tone)} could be useful sometime.")

            lines = lines[:4]


        print("\n— Your diary entry —")
        for l in lines:
            print("  " + l)


        # Save the entry
        self.diary_entries.append({
            "Day": self.Day,
            "Tone": tone,
            "Entry": lines,
            "Activity": activity_score 
        })

        # Check Bonuses (Rest of code remains the same)
        diary_milestones = {
            10:  ("Hopeful Spirit", "Max health +5"),
            20:  ("Sharpened Mind", "Shadow skill +1"),
            35:  ("Strong Constitution", "Hunger reduced by 2."),
            50: ("Frontier Wisdom", "Travel speed +1"),
            75: ("Iron Will", "Max health increased by 10."),
        }

        self.day_memory = {k: None for k in self.day_memory}
        
        entry_count = sum(entry.get("Activity", 1) for entry in self.diary_entries)
        
        for milestone, (title, bonus) in diary_milestones.items():
            if entry_count >= milestone and title not in self.diary_bonuses:
                print(f"\nAs you close your journal, you feel a change within you…")
                print(f"[Diary Bonus] {title}: {bonus}")
                self.diary_bonuses.append(title)

                if title == "Hopeful Spirit": self.MaxHealth += 5
                elif title == "Sharpened Mind": self.shadow_skill += 1
                elif title == "Strong Constitution": self.Hunger -= 2
                elif title == "Frontier Wisdom": self.travelspeed += 1
                elif title == "Iron Will": self.MaxHealth += 10

    def select_tone(self):
        tones = ["witty", "serious", "nervous", "hopeful"]
        prompt = "Choose a tone for tonight's diary:"
        selected_tone = self.AI_File.parse_choice(
            available_choices=tones,
            player_prompt=prompt,
        )

        return selected_tone

    def health_tone_phrase(self, tone):
        options = {
            "witty": [
                "been roughed up good",
                "could've been worse",
                "but still standing"
            ],
            "serious": [
                "I must rest before moving on",
                "I have to be cautious",
                "I can't afford another blow"
            ],
            "nervous": [
                "my heart won't stop racing",
                "I fear this won't hold up",
                "each breath sends pain through me"
            ],
            "hopeful": [
                "but tomorrow's a new day",
                "I feel I can recover",
                "I sense better luck ahead"
            ]
        }
        return random.choice(options.get(tone, [""]))
    
    def combat_tone_phrase(self, tone):
        options = {
            "witty": [
                "poor thing though it could win",
                "it won't forget this lesson",
                "I gave it quite the schooling"
            ],
            "serious": [
                "and I held my ground",
                "it tested me and I prevailed",
                "I showed no mercy"
            ],
            "nervous": [
                "and I barely made it out",
                "it nearly did me in",
                "I won't forget that fight"
            ],
            "hopeful": [
                "but I know I'll be stronger soon",
                "I look forward to the next challenge",
                "and I feel ready for more"
            ]
        }
        return random.choice(options.get(tone, [""]))
    
    def loot_tone_phrase(self, tone):
        options = {
            "witty": [
                "about time my luck turned,",
                "don't ask how I got it,",
                "one way or another it's mine,"
            ],
            "serious": [
                "surely this will serve me well,",
                "a sensible find,",
                "I'll keep it close,"
            ],
            "nervous": [
                "I hope it keeps me safe,",
                "I'm not sure I can hold onto it,",
                "don't know if it'll last,"
            ],
            "hopeful": [
                "a sign my fortune's changing,",
                "feels like a blessing,",
                "tomorrow looks brighter,"
            ]
        }
        return random.choice(options.get(tone, [""]))

    def read_diary_day(self):
        """Let the player pick a day and display that entry."""
        if not self.diary_entries:
            print("\nYour diary is empty.")
            return

        # show all available days
        days = [entry["Day"] for entry in self.diary_entries]
        print("\nYour diary contains entries for days:", ", ".join(map(str, days)))
        choice = input("Which day would you like to read? ").strip()
        if not choice.isdigit():
            print("Invalid input.")
            return
        day = int(choice)
        entry = next((e for e in self.diary_entries if e["Day"] == day), None)
        if not entry:
            print(f"No entry found for Day {day}.")
            return

        print(f"\n— Diary Day {day} (Tone: {entry['Tone']}) —")
        for line in entry["Entry"]:
            print("  " + line)

    def jail_penalty(self):
        """Apply jail penalties scaled by Hostility level."""
        print("\nThe sheriff slams the cell door shut. 'Think about your choices.'")

        # Define base penalties
        jail_hours = self.Hostility * random.randint(1, 3)  # 1-3 hours per hostility point
        fine = self.Hostility * random.randint(3, 10)  # Fine scales with hostility
        lose_item_chance = self.Hostility * 10  # % chance to lose a random item

        # Advance time
        self.Time += jail_hours
        if self.Time >= 21:
            self.Day += 1
            self.Time = 9
            print("You spent the night in jail. A new day dawns.")
        else:
            print(f"You spend {jail_hours} hours in the cell before release.")

        # Apply fine
        fine_paid = min(self.gold, fine)
        self.gold -= fine_paid
        print(f"The sheriff fines you {fine_paid} gold for your trouble.")

        # Chance to lose an item
        if self.itemsinventory and random.randint(1, 100) <= lose_item_chance:
            item = random.choice(list(self.itemsinventory.keys()))
            self.itemsinventory[item] -= 1
            if self.itemsinventory[item] <= 0:
                del self.itemsinventory[item]
            print(f"While in jail, you lose 1 {item}—stolen or confiscated.")

        # Penalty: reduce hostility slightly
        self.Hostility = max(0, self.Hostility - 2)
        print("Your hostility cools a bit after jail time.")

        # Health penalty
        health_loss = self.Hostility * 3
        self.Health = max(1, self.Health - health_loss)
        print(f"You lose {health_loss} health from poor conditions in the cell.")

        time.sleep(2)

    def process_quest_triggers(self, trigger_location, is_menu_option=False):
        """
        The Master Quest Handler.
        trigger_location: "arrive_town", "leave_town", "saloon", "sheriff", etc.
        is_menu_option: 
            - False: Runs the quest immediately (Auto-trigger). 
            - True: Returns the quest details so you can add it as a button.
        """
        
        # 1. Identify valid quests based on Trigger + Condition
        valid_quests = []
        for quest in self.QUEST_DATABASE:
            if quest["trigger"] == trigger_location:
                # Check the specific condition lambda defined in database
                if quest["condition"](self):
                    valid_quests.append(quest)

        # If no quests match, return appropriately
        if not valid_quests:
            return None if is_menu_option else False

        # 2. Handle "Auto" Triggers (Arrival / Leave)
        if not is_menu_option:
            # Check double-dip prevention for town arrival events
            if trigger_location == "arrive_town" and self.town_event_occurred:
                return False 

            # Execute the first valid quest found
            active_quest = valid_quests[0]
            print(f"\n[!] {active_quest['description']}") # Optional flavor text
            
            # Dynamically call the function
            method_to_call = getattr(self, active_quest["function"])
            method_to_call()
            
            # Mark that an event happened in this town
            self.town_event_occurred = True 
            return True

        # 3. Handle "Menu" Triggers (Saloon / Sheriff)
        else:
            # Return the list of valid quests so the Menu can create buttons
            return valid_quests

    def get_flag(self, quest_id, key, default=None):
            """Safely gets a value from quest_flags."""
            if quest_id not in self.quest_flags:
                return default
            return self.quest_flags[quest_id].get(key, default)

    def set_flag(self, quest_id, key, value):
        """Safely sets a value in quest_flags."""
        if quest_id not in self.quest_flags:
            self.quest_flags[quest_id] = {}
        self.quest_flags[quest_id][key] = value

    def _normalize_effect_store(self, store):
        if isinstance(store, dict):
            normalized = {}
            for name, value in store.items():
                if isinstance(value, dict):
                    stacks = int(value.get("stacks", 1) or 1)
                    duration = value.get("duration", None)
                    meta = value.get("meta", {})
                    if not isinstance(meta, dict):
                        meta = {}
                    normalized[name] = {"stacks": stacks, "duration": duration, "meta": meta}
                elif isinstance(value, int):
                    normalized[name] = {"stacks": value, "duration": None, "meta": {}}
                else:
                    normalized[name] = {"stacks": 1, "duration": None, "meta": {}}
            return normalized
        if isinstance(store, list):
            normalized = {}
            for name in store:
                if not isinstance(name, str):
                    continue
                entry = normalized.get(name, {"stacks": 0, "duration": None, "meta": {}})
                entry["stacks"] += 1
                normalized[name] = entry
            return normalized
        return {}

    def normalize_effects(self):
        self.player_effects = self._normalize_effect_store(self.player_effects)
        self.enemy_effects = self._normalize_effect_store(self.enemy_effects)

    def _get_effect_store(self, target):
        if target == "enemy":
            return self.enemy_effects
        return self.player_effects

    def _set_effect_store(self, target, store):
        if target == "enemy":
            self.enemy_effects = store
        else:
            self.player_effects = store

    def add_effect(self, name, target="player", stacks=1, duration=None, meta=None):
        store = self._get_effect_store(target)
        if not isinstance(store, dict):
            store = self._normalize_effect_store(store)
            self._set_effect_store(target, store)
        entry = store.get(name, {"stacks": 0, "duration": duration, "meta": {}})
        entry["stacks"] += stacks
        if duration is not None:
            if entry["duration"] is None:
                entry["duration"] = duration
            else:
                entry["duration"] = max(entry["duration"], duration)
        if meta:
            meta_store = entry.get("meta")
            if not isinstance(meta_store, dict):
                meta_store = {}
            meta_store.update(meta)
            entry["meta"] = meta_store
        store[name] = entry

    def has_effect(self, name, target="player"):
        store = self._get_effect_store(target)
        if not isinstance(store, dict):
            store = self._normalize_effect_store(store)
            self._set_effect_store(target, store)
        entry = store.get(name)
        return bool(entry) and entry.get("stacks", 0) > 0

    def consume_effect(self, name, target="player", stacks=1):
        store = self._get_effect_store(target)
        if not isinstance(store, dict):
            store = self._normalize_effect_store(store)
            self._set_effect_store(target, store)
        entry = store.get(name)
        if not entry:
            return False
        entry["stacks"] -= stacks
        if entry["stacks"] <= 0:
            del store[name]
        else:
            store[name] = entry
        return True

    def remove_effect(self, name, target="player"):
        store = self._get_effect_store(target)
        if not isinstance(store, dict):
            store = self._normalize_effect_store(store)
            self._set_effect_store(target, store)
        if name in store:
            del store[name]

    def tick_effects(self, target="player", ticks=1):
        store = self._get_effect_store(target)
        if not isinstance(store, dict):
            store = self._normalize_effect_store(store)
            self._set_effect_store(target, store)
        expired = []
        for name, entry in store.items():
            duration = entry.get("duration", None)
            if duration is None:
                continue
            entry["duration"] = duration - ticks
            if entry["duration"] <= 0:
                expired.append(name)
            else:
                store[name] = entry
        for name in expired:
            del store[name]
        
class Combat:
    def __init__(self, player):
        self.player = player
        if self.player.Day <= 0:
            self.enemies = ["viper", "cobra"]
        elif self.player.Day == 1:
            self.enemies = ["viper", "rattlesnake", "cobra", "wolf", "bison"] 
        elif self.player.Day == 2:
            self.enemies = ["pack of wolves", "cobra", "wolf", "bison"] 
        elif self.player.Day == 3:
            self.enemies = ["pack of wolves", "cobra", "wolf", "rattlesnake"] 
        elif self.player.Day >= 4 and self.player.Day <= 6:
            self.enemies = ["bandit", "pack of wolves", "wolf", "bison", "rattlesnake", "looter"] 
        else:
            self.enemies = ["bandit", "bear", "pack of wolves", "mounted bandit", "bison"] 

        self.Enemy = random.choice(self.enemies)
        self.EnemyCombatant = None
        self.Enemies = {
            "rattlesnake": {"health": 20, "damage": 7, "speed": 4, "loot": "small","type": "animal", "special": "venomous","behavior": "aggressive",}, 
            "viper": {"health": 10, "damage": 5, "speed": 5, "loot": "small", "type": "animal","behavior": "fearful",},
            "cobra": {"health": 15, "damage": 10, "speed": 2, "loot": "small",  "type": "animal","behavior": "cautious",},
            "wolf": {"health": 50, "damage": 10, "speed": 4, "loot": "medium", "type": "animal","behavior": random.choice(["reckless", "none", "none"]),},
            "bison": {"health": 100, "damage": 15, "speed": 2, "loot": "large", "passive": True,  "type": "animal","behavior": "cautious",},
            "pack of wolves": {"health": 70, "damage": 15, "speed": 4, "loot": "medium", "type": "pack","behavior": random.choice(["reckless", "cautious", "none"]),},
            "bear": {"health": 125, "damage": 15, "speed": 3, "loot": "medium",  "type": "animal","behavior": "reckless",},
            "bandit": {"health": 60, "damage": 10, "speed": 4, "loot": "bandit",  "type": "human","behavior": random.choice(["intelligent", "cautious"]),},
            "mounted bandit": {"health": 110, "damage": 15, "speed": 7, "loot": "bandit",  "type": "human","behavior": "intelligent",},
            "brawler": {"health": 60, "damage": 5, "speed": 2, "loot": "townsperson",  "type": "human","behavior": random.choice(["reckless", "none"]),},
            "sheriff": {"health": 65, "damage": 10, "speed": 2, "loot": "townsperson",  "type": "human","behavior": random.choice(["cautious", "desperate", "none"]),},
            "looter": {"health": 60, "damage": 10, "speed": 5, "loot": "rare",  "type": "human","behavior": random.choice(["fearful", "cautious"]),},
            "bandit leader": {"health": 120, "damage": 25, "speed": 3, "loot": "ultra_rare",  "type": "human", "special": "alert", "bound": True,"behavior": "boss"},
            "tester": {"health": 100, "damage": 5, "speed": 3, "loot": "ultra_rare",  "type": "human", "armored": True, "bound": True,"behavior": "boss"},
            "phantom gunslinger": {"health": 75, "damage": 15, "speed": 3, "loot": "ultra_rare", "type": "ghost", "special": "ghostly_form","behavior": "boss"},
            "outlaw gunman": {"health": 70, "damage": 12, "speed": 4, "loot": "bandit", "type": "human", "behavior": "aggressive"},
            "cowboy scout": {"health": 60, "damage": 10, "speed": 5, "loot": "common", "type": "human", "behavior": random.choice(["cautious", "desperate"])},
            "clanton gunfighter": {"health": 85, "damage": 15, "speed": 3, "loot": "rare", "type": "human", "behavior": "reckless"},
            "curly bill": {"health": 120, "damage": 20, "speed": 4, "loot": "ultra_rare", "type": "human", "behavior": "boss", "special": "alert", "bound": True},
            "saboteur": {"health": 65, "damage": 10, "speed": 4, "loot": "bandit",  "type": "human","behavior": random.choice(["intelligent", "cautious", "fearful"]),},
            "saboteur chief": {"health": 80, "damage": 15, "speed": 4, "loot": "bandit",  "type": "human","behavior": random.choice(["intelligent", "cautious", "fearful"]),},
            "dynamite dave": {"health": 110, "damage": 20, "speed": 3, "loot": "bandit",  "type": "human","behavior": "dynamite dave","bound": True,},
            "warlord_lieutenant": {"health": 120, "damage": 20, "speed": 2, "loot": "ultra_rare", "type": "human", "behavior": "boss", "bound": True},
            "gunboat_crew": {"health": 75, "damage": 15, "speed": 3, "loot": "common", "type": "human", "behavior": "desperate", "bound": True},
            }
        self.loots = {
            "small": ["small hide", "small meat"],
            "medium": ["medium hide", "medium meat"],
            "large": ["large hide", "large meat", "horn"],
            "bandit": ["revolver", "pistol_ammo", "bread", "rifle"],
            "townsperson": ["whiskey", "knife", "antivenom"],
            "common": [random.choice(player.common_loot)],
            "uncommon": [random.choice(player.uncommon_loot)],
            "rare": [random.choice(player.rare_loot)],
            "ultra_rare": [random.choice(player.ultra_rare_loot)],
        }

    def FindAttacker(self, RandomT):
        # If a specific enemy was requested and exists in the dictionary, use it
        if RandomT and RandomT.lower() in self.Enemies:
            self.Enemy = RandomT.lower()
        else:
            # Otherwise pick a random one from today's possible list
            self.Enemy = random.choice(self.enemies)
        self.EnemyCombatant = self.Enemies[self.Enemy]
        print(f"Along the path, you spot a {self.Enemy}.")

    def Attack(self):
        escape = False
        player.change_music("combat.mp3", -1)
        self.player.day_memory["encounter"] = f"a {self.Enemy}"
        if "ammo belt" in self.player.itemsinventory:
            ability_auto_ammo_belt = True
        else: 
            ability_auto_ammo_belt = False
        if not self.EnemyCombatant:
            print("There is no enemy to fight.")
            return
        base_enemy_health = self.EnemyCombatant["health"]
        base_enemy_damage = self.EnemyCombatant["damage"]
        base_enemy_speed = self.EnemyCombatant["speed"]

        enemy_damage = self.EnemyCombatant["damage"]
        enemy_speed = self.EnemyCombatant["speed"]
        enemy_loot = self.EnemyCombatant["loot"]
        enemy_health = self.EnemyCombatant["health"]
        # After setting up the enemy combatant

        if self.player.difficulty == 'adventure':
            enemy_health = int(self.EnemyCombatant["health"] * 0.75)
            enemy_damage = int(self.EnemyCombatant["damage"] * 0.75)
        elif self.player.difficulty == 'savage':
            enemy_health = int(self.EnemyCombatant["health"] * 1.25)
            enemy_damage = int(self.EnemyCombatant["damage"] * 1.1)
        if self.player.Day >= 5:
                enemy_health = int(self.EnemyCombatant["health"] + (self.player.Day))
                enemy_damage = int(self.EnemyCombatant["damage"] + (self.player.Day//2))

        print(f"\nYou face off against a {self.Enemy.capitalize()}!")
        print(f"Enemy stats — Health: {enemy_health}, Damage: {enemy_damage}, Speed: {enemy_speed}")
        player.enemy_sound(self.Enemy)
        if self.EnemyCombatant.get("passive") == True:
            print(f"The {self.Enemy} appears to be passive.")
            print("You have the option to leave it alone, will you? Yes/No")
            Choice = input(": ").capitalize().strip()
            if Choice.lower() == "yes":
                if player.invillage == True:
                    player.change_music("Town.mp3", -1)
                else:
                    player.change_music("game_theme.mp3", -1)
                    print(f"You slowly back away from the {self.Enemy}.")
                return
            else:
                print(f"You boldly approach the {self.Enemy}.")
        
        if self.player.Speed > self.EnemyCombatant["speed"]:
            TurnOrder = ["player", "enemy"]
        elif self.player.Speed < self.EnemyCombatant["speed"]:
            TurnOrder = ["enemy", "player"]
        else:
            TurnOrder = random.choice([["player", "enemy"], ["enemy", "player"]])
        stunned = False
        escape_boost = 0

        
        while enemy_health > 0 and self.player.Health > 0:
            for turn in TurnOrder:
                if turn == "player":
                    player_turn_complete = False
                    while not player_turn_complete:
                        if self.player.has_effect("posse_help"):
                            print("The Earp posse comes in, guns blazing!")
                            posse_damage = random.randint(70, 90)
                            print(f"They deal {posse_damage} damage to the {self.Enemy}!")
                            enemy_health -= posse_damage
                            self.player.consume_effect("posse_help")
                        print("\n--- Your Turn ---")
                        available_choices = ["Attack", "Use Item", "Retreat"]
                        prompt = "What will you do?"

                        choice = self.player.AI_File.parse_choice(available_choices, prompt)


                        if choice == "attack":
                            player_turn_complete = True
                            # Get list of owned weapons (weapons with known names)
                            owned_weapons = [w for w in weapons_data if w in self.player.itemsinventory]
                            if not owned_weapons:
                                print("You don't have any weapons, so you fight with your fists!")
                                player_attack = random.randint(2, 5)
                                player.play_sound("punch.mp3")
                            else:
                                while True:
                                    print("Choose a weapon:")
                                    for weapon in owned_weapons:
                                        info = weapons_data[weapon]
                                        dmg = info['damage']
                                        ammo_type = info['ammo']
                                        ammo_info = ""
                                        if ammo_type != 'none':
                                            if ability_auto_ammo_belt:
                                                self.player.itemsinventory[ammo_type] = self.player.itemsinventory.get(ammo_type, 0) + 1
                                                print("Your ammo belt provides +1 ammo for your gun.")
                                                ability_auto_ammo_belt = False
                                            ammo_count = self.player.itemsinventory.get(ammo_type, 0)
                                            ammo_info = f" | Ammo: {ammo_count}"
                                        print(f"{weapon.capitalize()} (Damage: {dmg}){ammo_info}")
                                    print(f"Fists (No weapon)")

                                    try:
                                        button_choices = owned_weapons + ["fists"]
                                        weapon_choice = self.player.AI_File.parse_choice(
                                        button_choices, 
                                        "Choose a weapon:"
                                        )
                                        if weapon_choice == "fists":
                                            player_attack = random.randint(2, 5)
                                            print("You swing your fists!")
                                            player.play_sound("punch.mp3")
                                            break # Exit the 'while True' loop
                                        elif weapon_choice in owned_weapons:
                                            weapon = weapon_choice # The choice *is* the weapon name
                                            info = weapons_data[weapon]
                                            ammo_type = info['ammo']
                                            # check ammo
                                            if ammo_type != 'none':
                                                if self.player.itemsinventory.get(ammo_type, 0) < 1:
                                                    print(f"You're out of {ammo_type}! Choose another weapon.")
                                                    player.play_sound("blank_click.mp3")
                                                    time.sleep(1)
                                                    continue # Stay in the 'while True' loop
                                                else:
                                                    self.player.itemsinventory[ammo_type] -= 1
                                                    if self.player.itemsinventory[ammo_type] <= 0:
                                                        del self.player.itemsinventory[ammo_type]
                                                    ammo_left = self.player.itemsinventory.get(ammo_type, 0)
                                                    player.weapon_ability(weapon)
                                                    print(f"You fire the {weapon}. Ammo left: {ammo_left}")
                                                    player.weapon_sound(weapon)
                                            else:
                                                if self.player.has_effect("sharpened_blade"):
                                                    print(f"Your blade is extra sharp, +10 damage!")
                                                    player.damage_modifier += 10
                                                    self.player.consume_effect("sharpened_blade")
                                                player.play_sound("knife.mp3")
                                                player.weapon_ability(weapon)

                                            # roll damage
                                            dmg_range = info['damage']
                                            player_attack = random.randint(*dmg_range)
                                            player_attack = player_attack * player.dmg_modifier_multiply

                                            break
                                        else:
                                            print("Invalid selection.")
                                    except ValueError:
                                        print("Please enter a valid number.")
                            player_attack += player.damage_modifier
                            if self.EnemyCombatant.get("special") == "ghostly_form":
                                if random.randint(1, 2) == 1:
                                    print("Your attack passes harmlessly through the Phantom Gunslinger!")
                                    continue
                            enemy_health -= player_attack
                            print(f"You hit the {self.Enemy} for {player_attack} damage!")
                            player.damage_modifier = 0
                            player.dmg_modifier_multiply = 1
                            print(f"Your health is {self.player.Health}.")
                            print(f"Enemy health is {enemy_health}.")

                        elif choice == "use item":
                            self.player.use_item(combat=True, enemy_name=self.Enemy, enemy_combatant=self.EnemyCombatant)


                        elif choice == "retreat":
                            player_turn_complete = True
                            new_speed = self.player.Speed + escape_boost
                            if self.EnemyCombatant.get("bound", False) == True:
                                print("The enemy blocks your escape, you can't flee!")
                                continue
                            if enemy_speed <= new_speed:
                                print("You manage to escape!")
                                escape = True
                                escape_boost = 0
                                self.player.Health = round(self.player.Health)
                                self.player.Armor_Boost = 1
                                player.dmg_modifier_multiply = 1
                                if player.invillage == True:
                                    player.change_music("Town.mp3", -1)
                                else:
                                    player.change_music("game_theme.mp3", -1)
                                    
                                return escape
                            else:
                                escape_boost += 1
                                print("You failed to escape!")
                                self.player.Health = self.player.Health - (enemy_damage)/5
                                break

                time.sleep(2,)
                if enemy_health <= 0:
                    print(f"{self.Enemy.capitalize()} is dead.")
                    loot_item = random.choice(self.loots[enemy_loot])
                    self.player.loot_drop(loot_item)
                    self.player.score = self.player.score + 5
                    self.player.Health = round(self.player.Health)
                    self.player.Armor_Boost = 1

                    player.dmg_modifier_multiply = 1
                    time.sleep(2,)
                    if player.invillage == True:
                        player.change_music("Town.mp3", -1)
                    else:
                        player.change_music("game_theme.mp3", -1)
                    return escape
                # Enemy's turn
                elif turn == "enemy":
                    current_turn_damage = enemy_damage 
                    print(f"\n--- {self.Enemy.capitalize()}'s Turn ---")
                    
                    # --- Status Effect Checks (EXISTING) ---
                    if self.player.has_effect("stun", target="enemy"):
                        stunned = True
                        self.player.consume_effect("stun", target="enemy")
                    if self.player.has_effect("hphalf", target="enemy"):
                        enemy_health -= enemy_health/2
                        self.player.consume_effect("hphalf", target="enemy")
                    if self.player.has_effect("+20HP", target="enemy"):
                        enemy_health += 20
                        self.player.consume_effect("+20HP", target="enemy")
                    if stunned == True and self.EnemyCombatant.get("special", None) != "alert":
                        print("The enemy is dazed, unable to attack.")
                        stunned = False
                        continue
                    
                    # --- START NEW BEHAVIOR LOGIC ---
                    behavior = self.EnemyCombatant.get("behavior", "aggressive")
                    # Use starting_enemy_health as the benchmark for percentages
                    curr_hp = enemy_health 
                    
                    # This is the damage for THIS turn, which we can modify

                    action_taken = False # Flag to skip attack if behavior dictates

                    match behavior:
                        case "reckless":
                            if random.randint(1, 10) <= 3: # 30% chance
                                print(f"The {self.Enemy} attacks recklessly!")
                                current_turn_damage = int(current_turn_damage * 1.5)
                                recoil = int(current_turn_damage * 0.25)
                                enemy_health -= recoil
                                print(f"It takes {recoil} recoil damage!")
                        
                        case "cautious":
                            # If below 50% of its *starting* max HP
                            if curr_hp < (base_enemy_health * 0.5): 
                                if random.randint(1, 10) <= 3: # 30% chance to defend
                                    print(f"The {self.Enemy} seems cautious and waits for an opening.")
                                    enemy_health += int(base_enemy_health * 0.1) # Regain 10% of starting health
                                    print(f"It regains {int(base_enemy_health * 0.1)} health!")
                                    action_taken = True # Skips the attack this turn
                        
                        case "fearful":
                            if random.randint(1, 10) <= 3: # 30% chance to flee
                                print(f"The {self.Enemy} attempts to flee!")
                                if enemy_speed < self.player.Speed:
                                    self.player.perform_stat_check(enemy_speed, base_target=12 + self.player.Speed)
                                    print("It successfully flees the battle!")
                                    return escape # Enemy flees
                                action_taken = True # Skips the attack this turn

                        case "desperate":
                            # If below 30% of its *starting* max HP
                            if curr_hp < (base_enemy_health * 0.3): 
                                print(f"The {self.Enemy} is desperate and attacks with fury!")
                                current_turn_damage = int(current_turn_damage * 1.3)
                        
                        case "intelligent":
                            if self.player.Health < (self.player.MaxHealth * 0.4): # Player is hurt
                                print(f"The {self.Enemy} sees an opening and strikes hard!")
                                current_turn_damage = int(current_turn_damage * 1.25)
                            elif self.player.Health > (self.player.MaxHealth * 0.75): # Player is healthy
                                if random.randint(1, 10) <= 4: # 40% chance of a probing attack
                                    print(f"The {self.Enemy} makes a quick, probing attack.")
                                    current_turn_damage = int(current_turn_damage * 0.5)
                        case "dynamite dave":
                            if enemy_health > (base_enemy_health * 0.4) and random.randint(1, 10) <= 4: # 40% chance
                                print(f"Dynamite Dave hurls a stick of dynamite at you!")
                                if self.player.perform_stat_check(self.player.Speed, base_target=15) == False:
                                    current_turn_damage = current_turn_damage + 10
                                    print("You are too slow, and the dynamite explodes on impact!")
                                else:
                                    print("You dodge the flying dynamite just in time!")
                            elif enemy_health < (base_enemy_health * 0.4):
                                print(f"Dynamite Dave is desperate and lights multiple sticks of dynamite!")
                                if random.randint(1, 10) <= 5: # 50% chance
                                    if self.player.perform_stat_check(self.player.Speed, base_target=12) == False:
                                        current_turn_damage = current_turn_damage + 15
                                        print("You fail to dodge the explosion! If only you had been faster...")
                                        print(f"The explosion deals massive damage +15 damage!")
                                else:
                                    print("He throws them wildly, and accidentally hits himself!")
                                    enemy_health -= 10
                                    print("Dynamite Dave takes 10 damage from the blast!")
                        
                        case "boss" | "aggressive":
                            pass # Fall through to standard attack logic
                        
                        case _: # Default for any other behavior
                            pass # Fall through to standard attack

                    if action_taken:
                        continue # The behavior (e.g., cower, defend) skipped the attack

                    # --- END NEW BEHAVIOR LOGIC ---

                    # --- Standard Miss/Hit Logic (Modified) ---
                    
                    # Base miss chance: 1 in 5
                    miss_threshold = 0
                    if self.EnemyCombatant.get("special") == "alert":
                        miss_threshold = 0  # No chance to miss
                    else:
                        miss_threshold = 1
                        # Use base_enemy_health as benchmark
                        if curr_hp < base_enemy_health * 0.5:
                            miss_threshold = miss_threshold + 2
                        if curr_hp < base_enemy_health * 0.25:
                            miss_threshold = miss_threshold + 5

                    if miss_threshold > 0 and random.randint(1, 15) <= miss_threshold:
                        print(f"The {self.Enemy} attacks but you manage to dodge it.")
                        continue
                        
                    # Apply damage using the (potentially modified) current_turn_damage
                    Nenemy_damage = current_turn_damage * self.player.Armor_Boost
                    if self.player.has_effect("half_incoming_damage"):
                        Nenemy_damage = Nenemy_damage / 2
                    self.player.Health -= Nenemy_damage
                    print(f"The {self.Enemy} strikes you for {Nenemy_damage} damage!")
                    print(f"Your health: {self.player.Health}")
                    print(f"Enemy health: {enemy_health}")
                    
                    if self.EnemyCombatant.get("special") == "venomous":
                        self.player.poisoned = 1
                    if self.player.Health <= 0:
                        self.player.Death("You have been defeated by the " + self.Enemy + ".")
                    time.sleep(2,)
        if enemy_health <= 0:
                print(f"{self.Enemy.capitalize()} is dead.")
                loot_item = random.choice(self.loots[enemy_loot])
                self.player.loot_drop(loot_item)
                self.player.score = self.player.score + 5
                self.player.Health = round(self.player.Health)
                self.player.Armor_Boost = 1

                player.dmg_modifier_multiply = 1
                time.sleep(2,)
                if player.invillage == True:
                    player.change_music("Town.mp3", -1)
                else:
                    player.change_music("game_theme.mp3", -1)
                return escape

