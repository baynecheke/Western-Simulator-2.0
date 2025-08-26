import random
import time
import json
import os
import pygame
import yaml
from AI_Control_File import AI_Control
AI_File = AI_Control()

pygame.mixer.init()
with open('loot.yaml', 'r') as file:
    loot_data = yaml.safe_load(file)


with open('Game_Info.yaml', 'r') as file:
   data = yaml.safe_load(file)

with open("game_data.yaml", "w") as f:
    yaml.safe_dump(data, f, sort_keys=False)


class Player:
    def __init__(self):
        #Basic player stuff
        self.rumors = {}
        self.Day = 1
        self.Time = 9
        self.Speed = 3
        self.watch = False
        self.counter = 0
        self.Hunger = 0
        self.Health = 100
        self.MaxHealth = 100
        self.itemsinventory = {}
        self.gold = 50  # Starting gold
        self.distancenext = 0
        self.travelspeed = 3
        self.EmptyTown = False
        self.Speed = 3
        self.Hostility = 0
        self.invillage = True
        self.save_name = ""
        self.rumors_collected = 0
        self.rumors_heard = []
        self.rebirth = False

        #AI
        last_3_actions = []
        current_task = "survive"
        current_actions = []

        #stuff
        self.score = 0
        self.poisoned = 0
        self.difficulty = 'frontier'  # Default
        
        #boosts
        self.Armor_Boost = 1
        self.travel_bonus = 0
        self.trade_bonus = 0
        self.dmg_modifier_multiply = 1
        self.damage_modifier = 0
        self.shadow_skill = 3
        self.trail_skill = 3
        self.strength_skill = 3
        self.Temporaryspdboost = 0
        self.Temporarytravelboost = 0
        self.enemy_effects = []
        self.player_effects = []
        self.TownUpgrades = []
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




        self.cheat_code = False
        self.Tquest = "None"  
        self.quest = []
        self.iron_stage = 0
        self.iron_bonus = 0
        self.boots_used = False
        self.town_defense_outcome   = None
        self.town_aftermath_outcome = None
        self.town_final_outcome     = None
        self.town_defense_bonus = 0
        self.diary_bonuses = []
        self.diary_entries = []
        

        self.BasePossibleActions = [
            "town jail", 
            "doctor's office", 
            "general store", 
            "gunsmith's shop", 
            "bank", 
            "saloon", 
            "talk townspeople",
            "trading post",
            "blacksmith shop",
            "leave town",
            "use item",
            "inventory",
            "travel road"
        ]
        self.possibleactions = self.BasePossibleActions[:-1]  # Exclude "(J) Continue..."

        self.TownNames1 = ["Gray", "Dust", "Buffalo", "Coyote", "Gold", "Post", "North"]
        self.TownNames2 = ["Town", "Ridge", "Camp", "Fort", "Settlement"]

    @classmethod
    def load_game(cls):
        print("\n--- Load Game ---")
        save_folder = 'saves'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        save_files = [f for f in os.listdir(save_folder) if f.endswith('.json')]
        if not save_files:
            print("No save files found. Starting a new game.")
            return cls()

        # Display saves by number
        for idx, filename in enumerate(save_files, start=1):
            print(f"{idx}. {filename.replace('save_', '').replace('.json', '')}")

        slot_choice = input("Enter the number of the save slot you want to load: ").strip()

        if not slot_choice.isdigit() or not (1 <= int(slot_choice) <= len(save_files)):
            print("Invalid choice. Starting a new game.")
            return cls()

        save_file = save_files[int(slot_choice) - 1]
        filepath = os.path.join(save_folder, save_file)
        with open(filepath, 'r') as f:
            save_data = json.load(f)

        player = cls()

        # Restore saved data
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
        player.town_defense_outcome = save_data.get("defense_outcome", False)
        player.town_aftermath_outcome = save_data.get("aftermath_outcome", False)
        player.town_final_outcome = save_data.get("final_outcome", False)
        player.boots_used = save_data.get("boots", False)
        player.diary_entries = save_data.get("diary_entries", [])
        player.difficulty = save_data.get("difficulty", [])
        player.MaxHealth = save_data.get("MaxHealth", 0)
        player.TownUpgrades = save_data.get("TownUpgrades", [])
        player.Tquest = save_data.get("Tquest", "None")
        player.quest = save_data.get("quest", [])
        player.rumors = save_data.get("rumors", {})
        player.diary_bonuses = save_data.get("diary_bonuses", [])
        player.rumors_heard = save_data.get("rumors_heard", [])
        player.enemy_effects = save_data.get("enemy_effects", [])
        player.player_effects = save_data.get("player_effects", [])
        player.iron_bonus = save_data.get("iron_bonus", 0)
        player.iron_stage = save_data.get("iron_stage", 0)

        print(f"Game loaded from {save_file} successfully!")
        # Update possible actions based on whether the player is in a village
        player.save_name = save_data.get("save_name", save_file.replace("save_", "").replace(".json", ""))
        if player.invillage:
            player.possibleactions = player.BasePossibleActions[:-1] # all except explore
        else:
            player.possibleactions = player.BasePossibleActions[-3:] # inventory check & explore
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
                "iron_bonus": self.iron_bonus,
                "iron_stage": self.iron_stage,
                "rebirth": self.rebirth,
            }, file)
        print(f"Game saved successfully to 'save_{self.save_name}.json'.")

    def main_game_loop(self):
        global player
        print("Would you like to (1) Start New Game or (2) Load a Save?")
        choice = input("Enter 1 or 2: ").strip()
        if choice == "2":
            player = Player.load_game()
        else:
            print("Would you like the instructions?")
            Choice = input("Yes/No:").strip().lower()
            if Choice == "yes":
                print("Welcome to Western Simulator!")
                time.sleep(2,)
                print("In this game you will try and survive the western life and complete quests.")
                time.sleep(2,)
                print("The rules are simple. You chose options that you would like to do. I tell you what happens. If you run out of health, you die.")
                time.sleep(2,)
                print("Choose a difficulty: (1) adventure, (2) frontier, (3) savage")
                choice = input(": ").strip()
                if choice == "1":
                    player.difficulty = 'adventure'
                elif choice == "3":
                    player.difficulty = 'savage'
                else:
                    player.difficulty = 'frontier'
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
                player.change_music("Town.mp3", -1)
                player.add_item("diary")
                
            else:
                player.change_music("Town.mp3", -1)
                player.add_item("diary")
                print("Choose a difficulty: (1) adventure, (2) frontier, (3) savage")
                choice = input(": ").strip()
                if choice == "1":
                    player.difficulty = 'adventure'
                elif choice == "3":
                    player.difficulty = 'savage'
                else:
                    player.difficulty = 'frontier'


        while not player.Health <= 0:
            if player.invillage == True:
                player.HostilityFunc()
                player.change_music("Town.mp3", -1)
            else:
                player.change_music("game_theme.mp3", -1)
            player.RunDay()
            player.counter = 0
            player.Day += 1
            if player.Temporaryspdboost > 0:
                player.Speed -= player.Temporaryspdboost
                player.Temporaryspdboost = 0
            if player.Health <= 0:
                time.sleep(2,)
                player.Death("You have succumbed to your injuries and the harsh conditions of the wild west.")
            player.Hunger = player.Hunger + 1
            print("You feel hungrier...")
            time.sleep(2,)
            if player.Hunger >= 3:
                print("You stagger, feeling the effects of your ravenous hunger.")
                hunger_damage = player.Hunger*5
                lost_health = hunger_damage
                player.Health -= lost_health
                print(f"You lost {lost_health} health of hunger.")
                if player.Health <= 0:
                    player.Death("You have succumbed to starvation in the unforgiving wild west.")
                
            if player.poisoned > 0:
                print("You remain poisoned, feeling weak and faint.")
                time.sleep(2,)

            print(f"Your health is: {player.Health}.")
            if player.Health <= 0:
                break
            player.save_game()
            choice = input("Would you like to quit? (yes/no): ").strip().lower()
            if choice == 'yes':
                print("Thanks for playing! See you next time.")
                pygame.mixer.music.stop()
                exit()
            else:
                print("Continuing your adventure...")
                time.sleep(4,)

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
        if item in ["pistol_ammo", "rifle_ammo", "shotgun_ammo"]:
            self.itemsinventory[item] = self.itemsinventory.get(item, 0) + 3
            print(f"You found 3 x {item}!")
        else:
            self.add_item(loot)
            if self.difficulty == 'adventure' and loot in self.common_loot:
                print(f"You found extra {loot} due to adventure mode!")
                self.add_item(loot)
        self.day_memory["loot"] = item


    def TakeActionsChose(self):
        print("You may choose an action to take:")
        for action1 in self.possibleactions:
            print(action1)
        while True:
            choice = input("Choice: ").strip()
            parsed = AI_File.parse_action(choice, self.possibleactions)
            print(parsed['action'])
            if parsed['action'] in self.possibleactions:
                return parsed['action']
            else:
                print("Invalid or unavailable choice. Try again.")

    def generate_game_state(self):
        if self.invillage == True:
            village_part = "Player is in a western village"
        else:
            village_part = "Player is in the western prairy."
        if self.Health <= 80:
            health_status = f"Player has {self.Health}/{self.MaxHealth} health remaining."
        else:
            health_status = f"Player is in good health."
        if self.Hostility >= 1:
            hostility = f"The Townspeople have a hostility of {self.Hostility}."
        else: 
            hostility = ""
        game_state = village_part + health_status + hostility
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
            case "leave town":
                self.LeaveTown()
            case "use item":
                self.use_item1()
            case "inventory":
                self.Statcheck()
            case "travel road":
                self.Explore()
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
                "bread": "Restores 5 health or reduces 1 hunger. Can be used outside of combat.",
                "antivenom": "Cures poison if poisoned. Only usable outside of combat.",
                "lantern": "Gives you 1 extra hour of time. Only usable outside of combat.",
                "boots": "Increases travel speed by 1. Only usable outside of combat.",
                "leather armor": "Reduces combat damage taken (90%). Only usable in combat.",
                "chain mail": "Greatly reduces combat damage taken (70%). Only usable in combat.",
                "lasso": "Halves the health of animal-type enemies. Only usable in combat.",
                "fire cracker": "Halves health of pack-type enemies and stuns them. Only usable in combat.",
                "rope": "Could be used during events. Only usable outside of combat.",
                "ammo cartridge": "Gives 5 of a given ammo. Only usable outside of combat.",
                "tobacco pouch": "Boosts morale: +5 to your next attack. Only usable in combat.",
                "gun oil":       "Apply to weapon: +5 damage on next attack. Only usable in combat.",
                "coffee tin":    "Drink for a speed boost: +1 travel speed in next combat. Only usable outside of combat.",
                "gold nugget":   "A heavy nugget. Sell for a high price. Only usable outside of combat.",
                "bandit's map":  "Study to reveal a hidden stash. Only usable outside of combat.",
                "diary": "Open your journal and read past entries. Only usable outside of combat.",
                "flashbang": "Can be thrown at enemies. Stuns them for one turn. Only usable in combat.",
                "bandage": "Heals 25 health. Only usable outside of combat.",
                "field dressing kit": "prevents 50% of next damage. Only usable in combat.",
            }

            for idx, (item, qty) in enumerate(self.itemsinventory.items(), 1):
                description = item_descriptions.get(item, "This item can't be used.")
                print(f"{idx}. {item.capitalize()} (x{qty}) - {description}")

            choice = input("Enter the number of the item you want to use (or 'q to leave'): ").strip().lower()

            if choice == "q":
                print("You decided not to use anything.")
                use_continue = False
                break

            item_list = list(self.itemsinventory.keys())

            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(item_list):
                print("Invalid choice.")
                continue

            selected_item = item_list[int(choice) - 1]
            if combat == False:
                if selected_item == "bread":
                    self.Hunger = self.Hunger - 1
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    print(f"You eat some bread and reduce {1} hunger.")

                elif selected_item == "coffee tin":
                    print("You slam the coffee—your reflexes sharpen!")
                    self.Speed += 1
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    self.Temporaryspdboost = 1

                elif selected_item == "antivenom":
                    self.Hunger = self.Hunger - 1
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
                    # Let player choose which ammo to receive
                    print("Which ammo type would you like?") 
                    print("1) Pistol Ammo")
                    print("2) Rifle Ammo")
                    print("3) Shotgun Ammo")
                    choice = input("Choice: ").strip()
                    if choice == "1":
                        ammo = "pistol_ammo"
                    elif choice == "2":
                        ammo = "rifle_ammo"
                    elif choice == "3":
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

                elif selected_item == "tobacco pouch":
                    print("You puff on the tobacco pouch and feel emboldened.")
                    print("You will be faster and stronger in the fight to come. +1 damage, +1 speed")
                    self.damage_modifier += 5
                    self.Temporaryspdboost += 1
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "lasso":
                    if combat and enemy_combatant and enemy_combatant.get("type") == "animal":
                        self.enemy_effects.append("hphalf")
                        print(f"You used the lasso! The {enemy_name}'s health is halved!")
                        self.itemsinventory[selected_item] -= 1
                        if self.itemsinventory[selected_item] <= 0:
                            del self.itemsinventory[selected_item]
                    else:
                        print("The lasso has no effect on this enemy.")

                elif selected_item == "fire cracker":
                    if combat and enemy_combatant and enemy_combatant.get("type") == "pack":
                        print(f"You used the fire cracker! The {enemy_name}'s health is halved!")
                        print(f"They are much more disorganized.")
                        self.enemy_effects.append("stun")
                        self.enemy_effects.append("hphalf")
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
                    # Let player choose which ammo to receive
                    print("Which ammo type would you like?") 
                    print("1) Pistol Ammo")
                    print("2) Rifle Ammo")
                    print("3) Shotgun Ammo")
                    choice = input("Choice: ").strip()
                    if choice == "1":
                        ammo = "pistol_ammo"
                    elif choice == "2":
                        ammo = "rifle_ammo"
                    elif choice == "3":
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
                    self.enemy_effects.append("stun")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    print(f"The {enemy_name} is stunned!")

                elif selected_item == "bandage":
                    heal_amount = 25
                    self.Health = min(self.Health + heal_amount, self.MaxHealth)
                    print(f"You apply the bandage. You regain {heal_amount} health.")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                elif selected_item == "field dressing kit":
                    print("You quickly apply a field dressing, bracing for the next attack.")
                    self.player_effects.append("half_incoming_damage")
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]

                else:
                    print(f"You can't use {selected_item} right now.")
                    time.sleep(2,)
                                
            time.sleep(2,)

    def Statcheck(self):
        print(f"You are on day {self.Day}.")
        if "surveyor's kit" in self.itemsinventory:
            print(f"[Surveyor's Kit] {self.distancenext} miles to next town.")
        if self.watch:
            print(f"It is {self.Time}:00 o'clock.")
        else:
            print("It is morning." if self.Time < 13 else "It is afternoon.")
        print(f"You have {self.gold} gold in your pouch.")
        print("Your inventory contains:")
        if self.itemsinventory:
            for item, count in self.itemsinventory.items():
                print(f" - {item}: {count}")
        else:
            print(" - (empty)")
        #print(f"Your role is {self.active_role.name.capitalize()} (XP: {self.active_role.xp}).")
        print(f"Your hunger is {self.Hunger}.")
        print(f"Your health is {self.Health}.")
        input("Press Enter to continue:")

    def TownJail(self):
        print("You walk into the town jail.")
        print("The sheriff greets you.")
        print("Would you like to: ")
        print("(1) Pay a fine to reduce hostility.")
        print("(2) Return a criminal or loot to the sheriff.")
        print("(3) Ask the sheriff about rumors.")
        print("(4) Ask the sheriff to teach you some skills.")
        print("(5) Leave the jail.")
        choice = input("Enter your choice (1-5): ").strip()
        if choice == "1":
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
        elif choice == "2":
            if "outlaw" in self.caravan:
                print("You turn in the outlaw you captured.")
                print("The sheriff approaches you.")
                print("How can we reward you for bringing in this outlaw? (1) Gold (2) Supplies?")
                choice = input(": ").strip()
                if choice == "1":
                    reward = random.randint(20, 40)
                    self.gold += reward
                    print(f"The sheriff thanks you and gives you {reward} gold as a reward.")
                else:
                    supply = random.choice(self.rare_loot)
                    self.add_item(supply)
                    print(f"The sheriff thanks you and gives you some supplies: {supply}.")
                self.caravan.remove("outlaw")
            else:
                print("You have no criminals to turn in.")
        elif choice == "3":
            if "sheriff_rumor" not in self.rumors_heard:
                self.rumors_heard.append("sheriff_rumor")
                rumor_topics = {
                "bandits_coyote_camp": "People have been being robbed by coyote pass, somethings not right there.",
                "old_mine_lights": "Nobody goes near the old mine anymore.",
                "buried_gold_east": "Legend has it that there is gold east of here.",
                }
                topic, rumor = random.choice(list(rumor_topics.items()))
                print(f"A patron murmurs: \"{rumor}\"")
                self.rumors[topic] = self.rumors.get(topic, 0) + 1
                print(f"[Rumor about '{topic.replace('_',' ').capitalize()}' added! Heard {self.rumors[topic]} times.]")
                # Example: trigger a quest after hearing a rumor 2 times
                if self.rumors[topic] == 5:
                    print(f"A new quest is now available: {topic.replace('_',' ').capitalize()}!")
                    self.quest.append(topic)
            else:
                print("He shrugs: \"I told you all that a know.\"")
            time.sleep(2)
        elif choice == "4":
            print("The sheriff can teach you some skills.")
            print("Choose a skill to learn:")
            print("(1) Shadow Skill - Improves stealth and tracking.")
            print("(2) Trail Skill - Improves navigation and survival.")
            print("(3) Strength Skill - Improves combat effectiveness.")
            print("(4) Durability Skill - Improves max Health.")
            skill_choice = input("Enter your choice (1-3): ").strip()
            if skill_choice == "1":
                gold = self.shadow_skill * 5
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = input(": ").strip().lower()
                if choice == "yes":
                    self.shadow_skill += 1
                    print("Your shadow skill has improved! +1 shadow skill.")
                else:
                    print("You decided not to pay for the lesson.")
            elif skill_choice == "2":
                gold = self.trail_skill * 5
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = input(": ").strip().lower()
                if choice == "yes":
                    self.trail_skill += 1
                    print("Your trail skill has improved! +1 trail skill.")
                else:
                    print("You decided not to pay for the lesson.")
            elif skill_choice == "3":
                gold = self.strength_skill * 5
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = input(": ").strip().lower()
                if choice == "yes":
                    self.strength_skill += 1
                    print("Your strength skill has improved!")
                else:
                    print("You decided not to pay for the lesson.")
            elif skill_choice == "4":
                gold = (self.MaxHealth-95)/5 * 10
                print(f"The sheriff agrees to teach you for {gold}.")
                print("Will you pay? (yes/no)")
                choice = input(": ").strip().lower()
                if choice == "yes":
                    self.MaxHealth += 5
                    print("Your durability skill has improved! +5 max Health.")
                else:
                    print("You decided not to pay for the lesson.")
            else:
                print("Invalid choice.")
            
        elif choice == "5":
            print("You leave the jail.")

    def TradingPost(self):
        if not self.itemsinventory:
            print("You don't have any items to trade or sell.")
            return

        prices = {
            "small hide": 5, "medium hide": 10, "large hide": 25,
            "small meat": 5, "medium meat": 10, "large meat": 20,
            "horn": 35, "bread": 2, "knife": 5,
            "revolver": 20, "colt pistol": 20, "sharps rifle": 40,
            "rifle": 15, "shotgun": 25,
            "pistol_ammo": 1, "rifle_ammo": 2, "shotgun_ammo": 3,
            "lasso": 5, "winchester rifle": 50, "carved horn": 40,
            "gold nugget": random.randint(10, 40),
            "silver watch": random.randint(5, 15),
            "silver bar": random.randint(30, 40),
            "gold bar": random.randint(45, 75)
        }

        # --- NEW predetermined trades ---
        trade_offers = [
            {"give": "winchester barrel", "get": "winchester stock"},
            {"give": "winchester stock", "get": "winchester barrel"},
            {"give": "lasso", "get": "rope"},
            {"give": "gold nugget", "get": "field dressing kit"},
            {"give": "medium hide", "get": "bandage"},
            {"give": "shotgun_ammo", "get": "rifle_ammo"},
        ]

        self.play_sound("store_bell.mp3")
        print("You walk into the trading post.")
        print("The trader greets you.")
        time.sleep(2)

        while True:
            print("\n--- Trading Post ---")
            print("1) Sell items")
            print("2) Swap items (predetermined trades)")
            print("3) Leave")

            choice = input("What would you like to do? ").strip()

            if choice == "1":
                # --- Sell logic ---
                print("Your Inventory:")
                for idx, (item, qty) in enumerate(self.itemsinventory.items(), 1):
                    price = prices.get(item, 1)
                    print(f"{idx}. {item} (x{qty}) - Sell Price: ${price}")

                sell_choice = input("Enter the number of the item you want to sell or 'q' to cancel: ").strip()
                if sell_choice.lower() == "q":
                    continue
                if sell_choice.isdigit():
                    idx = int(sell_choice)
                    if 1 <= idx <= len(self.itemsinventory):
                        item_to_sell = list(self.itemsinventory.keys())[idx - 1]
                        price = prices.get(item_to_sell, 1) + self.trade_bonus
                        self.gold += price
                        self.itemsinventory[item_to_sell] -= 1
                        print(f"You sold 1 {item_to_sell} for ${price}. Current gold: ${self.gold}")
                        if self.itemsinventory[item_to_sell] <= 0:
                            del self.itemsinventory[item_to_sell]

            elif choice == "2":
                # --- Swap logic (predetermined) ---
                print("\nAvailable trades:")
                for idx, trade in enumerate(trade_offers, 1):
                    print(f"{idx}. Give {trade['give']}, Receive {trade['get']}")

                trade_choice = input("Pick a trade (or 'q' to cancel): ").strip()
                if trade_choice.lower() == "q":
                    continue
                if not trade_choice.isdigit():
                    continue

                trade_choice = int(trade_choice)
                if 1 <= trade_choice <= len(trade_offers):
                    offer = trade_offers[trade_choice - 1]
                    if offer["give"] in self.itemsinventory:
                        print(f"The trader will give you {offer['get']} in exchange for your {offer['give']}. Accept? (yes/no)")
                        if input(": ").strip().lower() == "yes":
                            # remove the offered item
                            self.itemsinventory[offer["give"]] -= 1
                            if self.itemsinventory[offer["give"]] <= 0:
                                del self.itemsinventory[offer["give"]]
                            # give the new item
                            self.add_item(offer["get"])
                            print(f"You traded {offer['give']} for {offer['get']}.")
                        else:
                            print("Trade declined.")
                    else:
                        print(f"You don't have a {offer['give']} to trade.")

            elif choice == "3":
                return
            else:
                print("Invalid choice.")

    def Blacksmith(self):
        self.play_sound("store_bell.mp3")
        print("You walk into the blacksmith.")
        print("The smith gives you a nod.")
        time.sleep(2,)
        inventory = {
            'leather armor': {'name': 'leather armor', 'price': 35, 'quantity': 3},
            'chain mail': {'name': 'chain mail', 'price': 75, 'quantity': 2},
            'boots': {'name': 'boots', 'price': 15, 'quantity': 5}
        }
        BlacksmithShop = GenericStore(self, "Blacksmith Shop", inventory)
        BlacksmithShop.run_shop()

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
        Choice = input(": ").strip().lower()
        if Choice == "yes":
            if self.gold >= cost:
                self.gold -= cost
                print(f"You were healed {Heal}")
                self.Health = 100
            else:
                print("You do not have enough gold.")
        doctor_inventory = {
            'bandage': {'name': 'bandage', 'price': 10, 'quantity': 5},
            'field dressing kit': {'name': 'field dressing kit', 'price': 20, 'quantity': 5},
            'antivenom': {'name': 'antivenom', 'price': 10, 'quantity': 5},
        }
        if random.randint(3,3) == 3:
            print(f"The owner walks over and greets you.")
            game_state = player.generate_game_state()
            event = f"The player walks into the Doctor's Supply Store, and is greeted by the owner."
            NpC = "doctor"
            AI_File.narrate_dialogue(game_state, event, NpC)
        doc_shop = GenericStore(self, "Doctor's Supply Store", doctor_inventory)
        doc_shop.run_shop()
        print("You leave the Doctor's Office.")

    def Gunsmiths(self):
        self.play_sound("store_bell.mp3")
        print("You enter the gunsmith.")
        print("The gunsmith greets you with a nod. Guns line the walls.")
        time.sleep(2,)
        inventory = {
        'revolver': {'name': 'revolver', 'price': 20, 'damage': (10, 15), 'quantity': 5},
        'rifle': {'name': 'rifle', 'price': 40, 'damage': (20, 25), 'quantity': 3},
        'shotgun': {'name': 'shotgun', 'price': 50, 'damage': (20, 35), 'quantity': 3},
        'knife': {'name': 'knife', 'price': 10, 'damage': (5, 10), 'quantity': 10},
        'pistol_ammo': {'name': 'pistol_ammo', 'price': 2, 'quantity': 50},
        'rifle_ammo': {'name': 'rifle_ammo', 'price': 3, 'quantity': 30},
        'shotgun_ammo': {'name': 'shotgun_ammo', 'price': 5, 'quantity': 10}
        }
        GunsmithStore = GenericStore(self, "Gunsmith", inventory)
        GunsmithStore.run_shop()

    def Bank(self):
        print("You walk into the Bank. The air smells of leather and dust.")

    def Armory(self):
        print("You enter the Armory, a shattered house on the edge of town.")
        print("A gruff soldier nods at you as you step inside.")
        time.sleep(2)
        print("You may choose two actions before the coming fight.")

        for i in range(2):
            print(f"\n--- Choice {i+1}/2 ---")
            print("1) Heal to full health")
            print("2) Buy ammo")
            print("3) Get supplies")
            choice = input("What would you like to do? (1-3): ").strip()

            if choice == "1":
                self.Health = self.MaxHealth
                print(f"You are fully healed. Health is now {self.Health}.")
            elif choice == "2":
                ammo_inventory = {
                    'pistol_ammo': {'name': 'pistol_ammo', 'price': 2, 'quantity': 10},
                    'rifle_ammo': {'name': 'rifle_ammo', 'price': 3, 'quantity': 10},
                    'shotgun_ammo': {'name': 'shotgun_ammo', 'price': 5, 'quantity': 10}
                }
                print("The quartermaster unlocks an ammo crate for you.")
                ammo_shop = GenericStore(self, "Armory Ammo Shop", ammo_inventory)
                ammo_shop.run_shop()
            elif choice == "3":
                print("The armory clerk hands you a crate of supplies...")
                loot = random.choice(["colt pistol", "revolver", "bandage", "ammo cartridge", "bread", "rope"])
                self.loot_drop(loot)
                time.sleep(1)
            else:
                print("Invalid choice. You missed that opportunity.")
            time.sleep(1)

        print("\nYou step out of the Armory, ready for what comes next.")

    def Saloon(self):
        self.play_sound("saloon door.mp3")
        print("You push open the swinging saloon doors.")
        print("The saloon is alive with music and conversation.")
        self.change_music("Saloon_music.mp3", -1)
        time.sleep(1)
        self.saloon_entry_event()

        for i in range(max(3-self.counter,0)):
            self.counter += 1
            print("\nWhat would you like to do?")
            print("1) Talk to the barkeeper")
            print("2) Sing a drinking song")
            print("3) Talk to the patrons")
            print("4) Leave the bar")
            choice = input("Choice: ").strip()
            if choice == "1":
                self.saloon_barkeeper()
            elif choice == "2":
                self.saloon_song()
            elif choice == "3":
                self.saloon_patrons()
            else:
                print("You decide to just watch the crowd for a while.")
                break
            time.sleep(1)
        print("You have gathered all new information.")
        self.change_music("Town.mp3", -1)

    def saloon_entry_event(self):
        roll = random.randint(1,5)
        if roll == 1:
            print("A brawl erupts in the corner—chairs fly as punches land.")
            combat = Combat(self)
            combat.FindAttacker("brawler")
            combat.Attack()
            
        elif roll == 2:
            print("A heated card game ends abruptly; someone storms out in a rage.")
            print("A coin rolls toward you and you pick it up. +5 gold.")
            self.gold += 5
        elif roll == 3:
            print("A piano player strikes up a ragtime tune; toes tap in time.")
        elif roll == 4:
            print("A drunk cowboy staggers over and offers you a swig of whiskey. (yes/no)")
            ans = input(": ").strip().lower()
            if ans == "yes":
                if random.randint(1,10) >= 9:
                    print("The whiskey was spoiled! You feel ill.")
                    self.poisoned = 1
                else:
                    print("You feel a warm buzz. +5 health.")
                    print("You feel faster. +1 speed.")
                    self.Temporaryspdboost += 1
                    self.Health = min(self.Health + 5, self.MaxHealth)
            else:
                print("You decline and step aside.")
        else:
            print("Lot's of people gather around the saloon's door and inside.")

    def saloon_barkeeper(self):
        print("\nThe barkeeper polishes a glass and nods.")
        print("1) Ask about rumors")
        print("2) Buy a drink (5 gold)")
        choice = input("Choice: ").strip()
        if choice == "1":
            if "barkeeper_rumor" not in self.rumors_heard:
                self.rumors_heard.append("barkeeper_rumor")
                rumor_topics = {
                "bandits_coyote_camp": "Bandits spotted near Coyote Camp.",
                "old_mine_lights": "Strange lights seen in the old mine.",
                "buried_gold_east": "A lost prospector buried gold east of here.",
                }
                topic, rumor = random.choice(list(rumor_topics.items()))
                print(f"He leans in: \"{rumor}.\"")
                self.rumors[topic] = self.rumors.get(topic, 0) + 1
                print(f"[Rumor about '{topic.replace('_',' ').capitalize()}' added! Heard {self.rumors[topic]} times.]")
            # Example: trigger a quest after hearing a rumor 2 times
                if self.rumors[topic] == 5:
                    print(f"A new quest is now available: {topic.replace('_',' ').capitalize()}!")
                    self.quest.append(topic)
            else:
                print("He shrugs: \"Nothing new to tell ya.\"")
        elif choice == "2":
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
        choice = input("Would you like to attempt to steal? (yes/no): ").strip().lower()

        if choice == "yes":
            # Determine success based on shadow skill
            base_chance = random.randint(1, self.shadow_skill - 1)

            print("You try and sneak something from the townspeople.")
            if 2 <= base_chance:
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
                Choice = input(": ").strip().lower()
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
                    self.Hostility += 1
                
        else:
            print("You decide against the risk and keep singing.")

    def saloon_patrons(self):
        print("\nYou join a group of patrons at a table.")
        print("1) Gather gossip")
        print("2) Play cards (gamble)")
        print("3) Arm-wrestling contest")
        choice = input("Choice: ").strip()
        if choice == "1":
            if "patron_rumor" not in self.rumors_heard:
                self.rumors_heard.append("patron_rumor")
                rumor_topics = {
                "bandits_coyote_camp": "People have been being robbed by coyote pass, somethings not right there.",
                "old_mine_lights": "Nobody goes near the old mine anymore.",
                "buried_gold_east": "Legend has it that there is gold east of here.",
                }
                topic, rumor = random.choice(list(rumor_topics.items()))
                print(f"A patron murmurs: \"{rumor}\"")
                self.rumors[topic] = self.rumors.get(topic, 0) + 1
                print(f"[Rumor about '{topic.replace('_',' ').capitalize()}' added! Heard {self.rumors[topic]} times.]")
                # Example: trigger a quest after hearing a rumor 2 times
                if self.rumors[topic] == 5:
                    print(f"A new quest is now available: {topic.replace('_',' ').capitalize()}!")
                    self.quest.append(topic)
            else:
                print("They shrug: \"We'll let you know if something happens.\"")
            time.sleep(2)
        elif choice == "2":
            bet = input("Enter bet amount: ").strip()
            if bet.isdigit() and int(bet) > 0 and int(bet) <= self.gold:
                bet = int(bet)
                self.gold -= bet
                if random.randint(1, self.shadow_skill) >= 3:
                    winnings = bet * 3
                    self.gold += winnings
                    print(f"You win! You gain {winnings} gold.")
                else:
                    print("You lose the hand and your bet.")
                    print("If you had been more stealthy, you might have won.")
            else:
                print("Invalid bet.")
        elif choice == "3":
            print("You grip a burly patron's hand and push...")
            if random.randint(1, self.strength_skill) > 2:
                prize = 5
                print(f"You win the arm-wrestle! +{prize} gold.")
                self.gold += prize
            else:
                print("You lose and take a punch. -5 health.")
                print("If you had been stronger, you might have won.")
                self.Health -= 5
        else:
            print("No one notices your hesitation.")
        time.sleep(2)

    def Townspeople(self):
        print(f"You chat with a few townsfolk.")
        time.sleep(1)
        self.counter += 1
        if self.counter >= 4:
            print("You've chatted for a while; there are no new conversations right now.")
            return

        roll = random.randint(1, 100)

        if roll <= 15:
            # Basic job
            print("A man asks if you'll help load wagons at the stable.")
            print("Work for 2 hours for gold? (yes/no)")
            if input(": ").strip().lower() == "yes":
                earned = random.randint(6, 14)
                self.gold += earned
                self.Time += 2
                print(f"You work and earn {earned} gold.")
            else:
                print("You politely decline.")

        elif roll <= 30:
            # Farmer & the plow
            print("A farmer waves you over. 'My plow's busted—can you help fix it?'")
            if "rope" in self.itemsinventory:
                print("You tie it back together with your rope.")
                self.itemsinventory["rope"] -= 1
                if self.itemsinventory["rope"] <= 0:
                    del self.itemsinventory["rope"]
                self.gold += 10
                print("You fix the plow. +10 gold.")
            elif self.strength_skill >= 4:
                print("You heave the plow upright and wedge it in tight.")
                self.gold += 8
                print("The farmer gives you 8 gold for your help.")
            else:
                print("You try to help, but it's beyond your skill. The farmer thanks you anyway.")

        elif roll <= 45:
            # Teaching children
            print("A schoolteacher asks if you'll speak to the children about survival.")
            if input("Do you agree? (yes/no): ").strip().lower() == "yes":
                self.shadow_skill += 1
                print("You tell them stories and teach a few tricks. +1 Shadow Skill.")
                self.Time += 1
            else:
                print("You shake your head and move on.")

        elif roll <= 60:
            # Help the blacksmith
            print("The blacksmith grunts, 'Hand me that hammer, would ya?'")
            if self.strength_skill >= 3:
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
            if input(": ").strip().lower() == "yes":
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
                    print("As the final bandit falls under you and the sherrifs fury, you breath a sigh of relief.")
                    print("The sheriff slaps your back and thanks you.")
                    print("You return his revolver, and he gives you a pouch of gold.")
                    self.gold += 15
                    selected_item = "revolver"
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                    

            else:
                print("You stay back, watching from a safe distance.")

        elif roll <= 90:
            # Crafting bonus (if tools owned)
            if self.shadow_skill >= 4:
                print("A merchant sees your intelligence and teaches you a couple haggling tricks.")
                print("You feel more confident with your skills.")
            else:
                print("You chat with a merchant, but nothing comes of it.")

        else:
            # Gift
            item = random.choice(["bandage", "bread", "antivenom", "coffee tin"])
            print(f"A town elder says, 'You look like you could use this.' He hands you a {item}.")
            self.add_item(item)

    def LeaveTown(self):
        self.counter = 0
        self.distancenext = random.randint(20, 25)
        print("You leave the town and head down the road.")
        if "surveyor's kit" in self.itemsinventory:
            print(f"[Surveyor's Kit] {self.distancenext} miles to next town.")
        self.play_sound("rolling_wheels.mp3")
        self.change_music("game_theme.mp3", -1)
        self.invillage = False
        self.Hostility = 0
        self.possibleactions = self.BasePossibleActions[-3:]  
        time.sleep(2,)

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
        quest_chance = random.randint(1, 3)
        if self.Tquest == "None" and quest_chance >= 3:
            Random = random.choice(["defend_town","iron_tracks"])
            if Random == "defend_town":
                # Episode 1 not done yet?
                if self.town_defense_outcome is None:
                    self.encounter_town_part1()
            elif Random == "iron_tracks":
                    self.encounter_iron_intro()
                    return
        if self.Tquest == "defend_town":
            # Episode 2 pending?
            if self.town_defense_outcome and self.town_aftermath_outcome is None:
                self.encounter_town_part2()
                return
            # Episode 3 pending?
            if self.town_aftermath_outcome and self.town_final_outcome is None:
                self.encounter_town_part3()
                return
        elif self.Tquest == "iron_tracks":
            if self.iron_stage == 1:
                self.encounter_iron_stage1()
                return
            elif self.iron_stage == 2:
                self.encounter_iron_stage2()
                return
            elif self.iron_stage == 3:
                self.encounter_iron_stage3()
                return
            elif self.iron_stage == 4:
                self.encounter_iron_stage4()
                return
            elif self.iron_stage == 5:
                self.encounter_iron_stage5()
                return
            else:
                self.encounter_iron_intro()
                return

    def ArriveTown(self):
        name = f"{random.choice(self.TownNames1)} {random.choice(self.TownNames2)}"
        self.play_sound("rolling_wheels.mp3")
        self.play_sound("horse_neigh.mp3")
        print(f"You arrive in the town of {name}!")
        self.change_music("Town.mp3", -1)

        if "family" in self.caravan:
            self.travel_bonus += 1
            print("The family thanks you sincerely for allowing them to travel with you, and gives you a handsome reward. +20 gold.")
            self.gold += 20
            self.caravan.remove("family")
        self.gold += 10
        print("You feel a sense of relief as you enter the town.")
        print("You gain 10 gold from your travels.")
        self.invillage = True
        self.possibleactions = self.BasePossibleActions[:-1]
        self.score = self.score + 5
        time.sleep(2)
        self.town_encounter()
      
    def GeneralStore(self):
        self.play_sound("store_bell.mp3")
        print("You walk into the general store. A friendly shopkeeper greets you.")
        time.sleep(2,)
        general_inventory = {            
            'lantern': {'name': 'lantern', 'price': 3, 'quantity': 10},
            'bread': {'name': 'bread', 'price': 5, 'quantity': 30},
            'rope': {'name': 'rope', 'price': 3, 'quantity': 20},
            'lasso': {'name': 'lasso', 'price': 7, 'quantity': 10},
            'fire cracker': {'name': 'fire cracker', 'price': 5, 'quantity': 10},
            'antivenom': {'name': 'antivenom', 'price': 5, 'quantity': 10},
            'tobacco pouch': {'name': 'tobacco pouch', 'price': 7, 'quantity': 7},
            'gun oil': {'name': 'gun oil', 'price': 7, 'quantity': 3},
            'coffee tin': {'name': 'coffee tin', 'price': 5, 'quantity': 5},
            'diary': {'name': 'diary', 'price': 5, 'quantity': 5},}
        gen_shop = GenericStore(self, "General Store", general_inventory)
        gen_shop.run_shop()

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
        pygame.mixer.music.stop()
        self.play_sound("death.mp3")
        print("You fall to the ground, your vision fading...")
        time.sleep(2,)
        print(death_cause)
        if self.rebirth == True:
            print("You have already respawned once.")
            print("You feel your life slipping away, and you know this is the end.")
        else:
            print("Your stats:")
            print(f"Days survived: {self.Day}")
            print(f"Score: {self.score}")
            input("Press Enter to continue...")
            self.Statcheck()
            print("You have come so far, would you like to respawn at your current position? (yes/no)")
            print("You will no longer track score.")
            choice = input(": ").strip().lower()
            if choice == "yes":
                self.lose_random_item(2)
                self.gold -= self.gold/2
                print("You feel a strange sensation, as if you are being pulled back to life...")
                self.Health = self.MaxHealth
                self.rebirth = True
                return
        print("Would you like to restart the game? (yes/no)")
        choice = input(": ").strip().lower()
 

        print("Credits: Bayne Cheke, Designer and Programmer.")
        time.sleep(1,)
        print("Music/audio effects: Freesound.com")
        time.sleep(1,)
        print("Playtesters: Deric R Cheke, Dax Cheke, Jessica Cheke, Silas Cheke")
        time.sleep(1,)
        print("Other contributions: ChatGPT")
        time.sleep(1,)
        if choice == "yes":
            print("Restarting game...")
            
            player = Player()
            player.main_game_loop()
            exit()
        else:
            print("Thank you for playing!")
            print("Until next time...")
            time.sleep(2,)
            exit()

        


    #RunDay
    def RunDay(self):
        
        print("You step out of your wagon and stretch.")
        time.sleep(2,)
        while self.Time < 21:
            self.DoAction()
            print()
            if self.Hunger < 0:
                Heal_bonus = self.Hunger
                Heal_bonus = Heal_bonus*10
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
            print("You make camp under the stars.")
            self.write_diary_entry()
            print("You sleep through the night")
            time.sleep(4,)
        self.Time = 9

    #Quests
    def PossibleQuest(self):
        Random = random.randint(1,40)
        Random = Random + self.Day*5-5
            # --- Rumor quest handler ---
        if self.quest:
            quest_topic = self.quest.pop(0)  # Remove and get the oldest quest
            print(f"\nYou follow up on a rumor: {quest_topic.replace('_',' ').capitalize()}!")
            # Trigger a special event based on the quest topic
            if quest_topic == "bandits_coyote_camp":
                print("You arrive at Coyote Camp and find a group of bandits plotting a robbery!")
                combat = Combat(self)
                combat.FindAttacker("bandit")
                combat.Attack()
                if self.Health > 0:
                    print("You defeat the bandits and find some loot.")
                    self.loot_drop("gold nugget")
                    self.loot_drop("pistol_ammo")
            elif quest_topic == "old_mine_lights":
                self.encounter_haunted_mine()
            elif quest_topic == "buried_gold_east":
                print("You search east of town and, after some digging, uncover a buried chest!")
                self.loot_drop("gold bar")
                self.gold += 25
                print("You gain 25 gold!")
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
            choice = input(": ").strip().capitalize()
            time.sleep(2,)
            if choice == "Yes":
                print("You attempt to capture the outlaw.")
                if self.strength_skill + self.Speed >= 7:
                    print("You successfully capture the outlaw.")
                    print("Go to the next town's jail to turn him in.")
                else: 
                    print("The outlaw overpowers you and escapes.")
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
            choice = input(": ").strip().capitalize()
            if choice == "Yes":
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
        print("You could (1) leave it, (2) enter the broken down door, (3) enter the cellar, or (4) loot the garden.")
        choice = input(": ")
        if choice == "1":
            print("You decide it is wisest to leave it alone.")
            time.sleep(2,)
        elif choice == "2":
            print("You enter the door.")
            print("It makes a creaking sound as you walk in.")
            time.sleep(2,)
            print("(1) On the wall hangs a dusty rifle,(2) on the table lies a bundle, and (3), there is a painting on the far wall.")
            choice = input(": ")
            if choice == "1":
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
            elif choice == "2":
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
            elif choice == "3":
                print("You examine the picture...")
                time.sleep(2,)
                Random = random.randint(1, self.shadow_skill)
                if Random == 1:
                    print("You accidentally trigger the trap attached to the painting!")
                    print("Out of the darkness a blade hits you.")
                    print("You stumble out of the building.")
                    print("You were, close, if your shadow skill was higher you have had a better chance of disarming it.")
                    time.sleep(4,)
                else:
                    print("You notice the elaborate trap around the painting, and streching around the room.")
                    print("You carefully disarm the trap, glad your shadow skills have served you.")
                    time.sleep(2,)
                    print("You find a crate behind the painting.")
                    print("Now that the trap is disarmed, you can loot the room safely.")
                    print("(1), On the wall hangs a dusty rifle,(2), on the table lies a bundle, and (3), there is a crate behind the painting.")
                    time.sleep(2,)
                    choice = input(": ")
                    if choice == "1":
                        print("You grab the rifle")
                        self.loot_drop("rifle")
                    elif choice == "2":
                        print("You rummage around through the table")
                        self.loot_drop(random.choice(self.common_loot))
                    elif choice == "3":
                        print("You find a wealth of supplies")
                        self.gold += 20
                        self.loot_drop(random.choice(self.uncommon_loot))
                        self.loot_drop(random.choice(self.rare_loot))

            else:
                print("Invalid")
                return
        elif choice == "3":
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
        elif choice == "4":
            print("You loot the garden.")
            self.loot_drop(random.choice(self.common_loot))
            time.sleep(2,)
        else:
            print("Invalid")
        print("Suddenly, you here someone approaching the house.")
        print("You quickly exit the house and get back on the road.")
        time.sleep(2,)

    def encounter_stage_coach(self):
        print("You come upon a stagecoach dangling over a ravine. The driver pleads for help.")
        print("1) Attempt to secure the coach with your rope")
        print("2) Try to push the coach back yourself")
        print("3) Leave the scene and continue on your way")
        choice = input(": ").strip()

        if choice == "1":
            if "rope" in self.itemsinventory:
                print("You tie off your rope and carefully secure the stagecoach...")
                if random.randint(1, 4) == 1:  # 75% chance of success
                    print("With effort, you pull it back to safety! The driver rewards you.")
                    print("The rope frays! The coach lurches but you can't hold it.")
                    print("Your rope isn't strong enough. The coach slips over the edge.")
                    self.Health -= 5
                    print("-5 health from the strain.")
                else:
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

        elif choice == "2":
            print("You brace yourself and try to push the stagecoach back...")
            if random.randint(1, self.strength_skill) > 2:
                print("Your strength prevails! You save the stagecoach and earn a reward.")
                reward = random.randint(10, 30)
                self.gold += reward
                print(f"+{reward} gold")
            else:
                print("Your strength isn't enough. The coach slips over the edge.")
                self.Health -= 5
                print("-5 health from the effort.")

        else:
            print("You decide it's too dangerous and ride on, losing some daylight.")
            self.Time += 1
        time.sleep(2,)

    def encounter_dry_river_bed(self):
        print("A dry river bed lies in your path.")
        time.sleep(1,)
        print("A storm is brewing in the West, and this location could flood easily.")
        print("You could either cross here, and risk the storm, or travel around.")
        time.sleep(2,)
        print("(1) cross, (2) travel around.")
        time.sleep(2,)
        Choice = input(": ").strip()
        if Choice == "1":
            print("You take the chance and cross the river bank.")
            if "weather cloak" in self.itemsinventory:
                print("Your weather cloak shields you from the flooding; you cross safely.")
                self.itemsinventory["weather cloak"] -= 1
                if self.itemsinventory["weather cloak"] <= 0:
                    del self.itemsinventory["weather cloak"]
            else:
            # … your original flood/random-fail code …
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
        print(f"You notice an abandoned wagon a little ways off the trail.")
        print(f"You could either search the wagon or leave and save time.")
        time.sleep(2,)
        print(f"1, search it.")
        print(f"2, leave it.")
        Choice = input(f": ")
        if Choice == "1":
            print(f"You take the time to search the wagon.")
            Random1 = random.randint(1,2)
            if Random1 == 1:
                print(f"As you rummage through the bags and boxes you uncover a rattlesnake.")
                if "rope" in self.itemsinventory:
                    print("You use your rope to whack the snakes head away, and it flees through the grass.")
                    selected_item = 'rope'
                    self.itemsinventory[selected_item] -= 1
                    if self.itemsinventory[selected_item] <= 0:
                        del self.itemsinventory[selected_item]
                elif self.Speed >= 5:
                    print(f"You dodge the snakes attack, then strangle it")
                else:
                    print("The snake bites you, then retreats.")
                    self.poisoned = 1
                time.sleep(2,)
            print("Inside the wagon you find many useful items.")
            rare = random.choice(["colt pistol", "bowie knife", "bread", "rope"])
            self.loot_drop(rare)
            time.sleep(2,)
        else:
            print(f"You leave the wagon alone and proceed down the trail.")

    def encounter_wounded_bandit(self):
        Random = random.randint(1, 100)  # you can ignore or repurpose this if you like
        print("\nYou spot a wounded bandit slumped against a rock. His pistol lies beside him.")
        print("1) Help him")
        print("2) Loot him")
        print("3) Leave him be")
        Choice = input(": ").strip()
        if Choice == "1":
            print("You tend his wounds and give him water.")
            gold = random.randint(5, 15)
            self.gold += gold
            print(f"He thanks you and staggers off. +{gold} gold.")
            if Random <= 50:
                print("The bandit robbed you while you weren't looking!")
                self.lose_random_item(1)
        elif Choice == "2":
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
        print("1) Join the fight")
        print("2) Stay hidden")
        print("3) Loot the fallen afterwards")
        Choice = input(": ").strip()
        if Choice == "1":
            print("You rush in to defend them!")
            combat = Combat(self)
            combat.FindAttacker("bandit")
            combat.Attack()
            if self.Health > 0:
                reward = random.randint(15, 30)
                self.gold += reward
                print(f"The grateful merchants reward you with {reward} gold.")
                print("They also give you some supplies.")
                self.loot_drop("bandage")
        elif Choice == "2":
            print("You stay hidden until it's over. No one notices you.")
        else:
            print("You wait for the dust to settle, then loot the fallen.")
            loot = random.choice(["bread", "pistol_ammo", "rope"])
            self.loot_drop(loot)
        time.sleep(2)

    def encounter_wild_stallion(self):
        print("\nA wild stallion rears up in a clearing—untamed and swift.")
        print("1) Try to catch it with your lasso")
        print("2) Leave it be")
        Choice = input(": ").strip()
        if Choice == "1":
            if "lasso" in self.itemsinventory:
                print("You manage to lasso the stallion! Your travels feel faster now. +1 travel speed.")
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
        time.sleep(2)
        self.Tquest == "defend_town"

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
        self.Tquest = "None"

        time.sleep(2)

    def wandering_trader(self):
        print("\nYou encounter a wandering trader on the trail.")
        all_items = {
            "colt pistol": 20,
            "remington pistol": 25,
            "henry rifle": 45,
            "bread": 4,
            'derringer pistol': 5,
            'carbine rifle': 35,
            'double barrel shotgun' :80,
            'tomahawk': 25,
            'sharps rifle': 100,
            'lever-action rifle': 70,
            'sawed-off shotgun': 55,
            'colt navy revolver': 30,
            'cavalry saber': 35,
        }

        print(f"\nYour gold: {self.gold}")
        print("Your inventory:")
        for item, qty in self.itemsinventory.items():
            print(f"  {item}: {qty}")
        print()

        # Pick 3 random items to sell
        available_items = dict(random.sample(list(all_items.items()), 3))

        # Show items for sale
        print("The trader offers the following items:")
        for i, (item, price) in enumerate(available_items.items(), start=1):
            print(f"  {i}. {item} - {price} gold")

        # Let the player buy
        while True:
            choice = input("Enter the number of the item you want to buy (or '0' to leave): ").strip()
            if choice == "0":
                print("You move on from the trader.\n")
                break
            if choice.isdigit() and 1 <= int(choice) <= len(available_items):
                item_name = list(available_items.keys())[int(choice) - 1]
                item_price = available_items[item_name]

                if self.gold >= item_price:
                    self.gold -= item_price
                    self.itemsinventory[item_name] = self.itemsinventory.get(item_name, 0) + 1
                    print(f"You bought 1 {item_name} for {item_price} gold.")
                    print(f"Remaining gold: {self.gold}")
                else:
                    print("You don't have enough gold.")
            else:
                print("Invalid input. Try again.")

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
            self.enemy_effects.append("+20HP")
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
            self.enemy_effects.append("stunned")
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
                if random.randint(1, self.shadow_skill) >=3:
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
                if random.randint(1, self.strength_skill) >= 3:
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
            combat.Attack()
            if self.Health <= 0:
                self.Death("The bear has defeated you in the cave.")
        else:
            print("You take the right tunnel...")
            print("A pack of wolves lurks here!")
            combat = Combat(self)
            combat.FindAttacker("pack of wolves")
            combat.Attack()
            if self.Health <= 0:
                self.Death("The wolves have defeated you in the cave.")

        time.sleep(1)
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
                if self.strength_skill >= 4:
                    print("You brace yourself and stop the minecart just in time! Your strength saves you.")
                    self.strength_skill += 1
                    print("+1 Strength Skill.")
                else:
                    print("You try to stop the minecart, but it's too heavy! It knocks you aside.")
                    dmg = random.randint(10, 20)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "2":
                if self.Speed >= 4:
                    print("You leap aside with quick reflexes, narrowly avoiding the cart.")
                    self.shadow_skill += 1
                    print("+1 Shadow Skill.")
                else:
                    print("You try to dodge, but the cart clips you as it passes.")
                    dmg = random.randint(15, 25)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "3":
                print("You expertly lasso the minecart, slowing it enough to avoid harm.")
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
                if self.strength_skill >= 3:
                    print("You brace yourself and stop the minecart just in time! Your strength saves you.")
                    self.strength_skill += 1
                    print("+1 Strength Skill.")
                else:
                    print("You try to stop the minecart, but it's too heavy! It knocks you aside.")
                    dmg = random.randint(5, 12)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "2":
                if self.Speed >= 3:
                    print("You leap aside with quick reflexes, narrowly avoiding the cart.")
                    self.shadow_skill += 1
                    print("+1 Shadow Skill.")
                else:
                    print("You try to dodge, but the cart clips you as it passes.")
                    dmg = random.randint(5, 10)
                    self.Health -= dmg
                    print(f"-{dmg} health.")
            elif action == "3":
                print("You expertly lasso the minecart, slowing it enough to avoid harm.")
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
            if self.shadow_skill >= 4:
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
                choice = input(": ").strip().lower()
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

    def change_music(self, filename, loop):
        music_path = os.path.join(os.path.dirname(__file__), filename)
        if self.music == False:
            return
        else:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(loop)
            except pygame.error as e:
                print(f"Could not play {filename}: {e}")

    def play_sound(self, filename):
        try:
            full_path = os.path.join(os.path.dirname(__file__), filename)
            sound = pygame.mixer.Sound(full_path)
            sound.play()
        except pygame.error as e:
            print(f"Error playing sound: {e}")

    def weapon_sound(self, weapon):
        if weapon in [
            "rifle", "winchester rifle", "henry rifle",
            "carbine rifle", "sharps rifle", "lever-action rifle"]:
            self.play_sound("rifle_shot.mp3")
            self.play_sound("rifle_prime.mp3")
        elif weapon in ["shotgun", "double barrel shotgun", "sawed-off shotgun"]:
            self.play_sound("shotgun.mp3")
        elif weapon in [
            "revolver", "colt pistol", "remington pistol",
            "derringer pistol", "colt navy revolver"]:
            self.play_sound("revolver_shot.mp3")

    def enemy_sound(self, name):
        if name == "rattlesnake":
            self.play_sound("rattle_snake.mp3")

    def weapon_ability(self, weapon):
        if weapon in ["revolver", "colt pistol"]:
            if self.itemsinventory[weapon] >= 2:
                if self.itemsinventory.get("pistol_ammo", 0) > 1:
                    print(f"You fire pull out both {weapon}s and fire!")
                    self.itemsinventory["pistol_ammo"] -= 1
                    self.dmg_modifier_multiply = 2
                    self.play_sound("revolver_shot.mp3")
                    time.sleep(1,)

        if weapon in ["winchester rifle", "henry rifle"]:
            print("You steady your aim...")
            if random.randint(1, 4) == 1:
                self.dmg_modifier_multiply = 1.5
        if weapon in ["remington pistol", "derringer pistol"]:
            print("Would you like to fire multiple shots? yes/no")
            choice = input(": ").capitalize().strip()
            if choice == "Yes":
                print("You fire multiple shots")
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
        if weapon == "double barrel shotgun":
            print("Double Barrel! Fire both barrels? (yes/no)")
            choice = input(": ").strip().lower()
            if choice == "yes" and self.itemsinventory.get("shotgun_ammo", 0) >= 2:
                self.itemsinventory["shotgun_ammo"] -= 2
                print("You fire both barrels in a devastating volley!")
                self.dmg_modifier_multiply = 2
                self.play_sound("shotgun.mp3")
                time.sleep(1,)
                print("The kickback bruizes your arm.")
                self.Health -= 5
            else:
                print("You decide not to use the double shot.")

        if weapon == "tomahawk":
            print("Throw your tomahawk for extra damage? (yes/no)")
            choice = input(": ").strip().lower()
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

        if weapon == "sharps rifle":
            print("You take a steady breath for a precision shot…")
            if random.randint(1, 4) == 1:
                print("Bullseye! Your shot hits extra savage.")
                self.dmg_modifier_multiply = 2

        if weapon == "cavalry saber":
            print("You slash with your saber, aiming for weak points.")
            self.dmg_modifier_multiply = 1.5

    def donate_supplies(self):
        if not self.itemsinventory:
            print("You have nothing to donate.")
            return

        while True:
            print("\nChoose an item to donate (or 0 to finish):")
            for i,(item,qty) in enumerate(self.itemsinventory.items(),1):
                print(f"{i}) {item} x{qty}")
            print("0) Done donating")
            choice = input("Choice: ").strip()
            if choice == "0":
                break
            if not choice.isdigit() or not (1 <= int(choice) <= len(self.itemsinventory)):
                print("Invalid.")
                continue

            item = list(self.itemsinventory.keys())[int(choice)-1]
            max_q = self.itemsinventory[item]
            num = input(f"How many {item}? (1–{max_q}): ").strip()
            if not num.isdigit() or not (1 <= int(num) <= max_q):
                print("Invalid quantity.")
                continue
            num = int(num)

            # determine bonus per unit
            if item in self.common_loot:      bonus = 0.5
            elif item in self.uncommon_loot:  bonus = 1
            elif item in self.rare_loot:      bonus = 3
            elif item in self.ultra_rare_loot: bonus = 6
            else:                   bonus = 0.5

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

        lines = []

        # Health line
        lines.append(
            f"I only have {self.Health} health left, {self.health_tone_phrase(tone)}."
        )

        # Combat line
        if self.day_memory["encounter"]:
            # day_memory["encounter"] already contains e.g. "a buffalo"
            lines.append(
                f"I fought {self.day_memory['encounter']} today, {self.combat_tone_phrase(tone)}."
            )

        # Loot line
        if self.day_memory["loot"]:
            lines.append(
                f"Found {self.day_memory['loot']} on the way, {self.loot_tone_phrase(tone)} could be useful sometime."
            )

        add = input("\nWould you like to add your own diary line? (yes/no) ").strip().lower()
        if add == 'yes':
            custom = input("Enter your custom diary line: ").strip()
            if custom:
                lines.append(custom)

        # Cap lines at 3
        lines = lines[:4]

        # Save it
        self.diary_entries.append({
            "Day": self.Day,
            "Tone": tone,
            "Entry": lines
        })

        # Display
        print("\n— Your diary entry —")
        for l in lines:
            print("  " + l)

        diary_milestones = {
            10:  ("Hopeful Spirit", "Max health +5"),
            20:  ("Sharpened Mind", "Shadow skill +1"),
            35:  ("Strong Constitution", "Hunger reduced by 2."),
            50: ("Frontier Wisdom", "Travel speed +1"),
            75: ("Iron Will", "Max health increased by 10."),
            }


        # Reset for next day
        self.day_memory = {k: None for k in self.day_memory}
        # Passive bonus check
        entry_count = sum(len(entry["Entry"]) for entry in self.diary_entries)
        for milestone, (title, bonus) in diary_milestones.items():
            bonus = f"day_{self.Day}_bonus"
            if entry_count >= milestone and title not in self.diary_bonuses:
                print(f"\nAs you close your journal, you feel a change within you…")
                
                print(f"[Diary Bonus] {title}: {bonus}")
                self.diary_bonuses.append(title)

                # Apply effects
                if title == "Hopeful Spirit":
                    self.MaxHealth += 5
                elif title == "Sharpened Mind":
                    self.shadow_skill += 1
                elif title == "Strong Constitution":
                    self.Hunger -= 2
                elif title == "Frontier Wisdom":
                    self.travelspeed += 1
                elif title == "Iron Will":
                    self.MaxHealth += 10

    def select_tone(self):
        tones = ["witty", "serious", "nervous", "hopeful"]
        print("Choose a tone for tonight's diary:")
        for i, t in enumerate(tones, 1):
            print(f"{i}) {t.capitalize()}")
        while True:
            choice = input(": ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(tones):
                return tones[int(choice) - 1]
            print("Invalid choice. Try again.")

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

    def encounter_iron_intro(self):
        print("At the saloon, you overhear a group of railroad men talking.")
        print("'Tracks are coming through this territory... but bandits don't like progress.'")
        choice = input("Do you agree to help the railroad? (yes/no): ").strip().lower()
        if choice == "yes":
            print("You agree to aid the foreman in keeping the line safe.")
            self.Tquest = "iron_tracks"
            self.iron_stage = 1
            print("They give you a reward of 10 gold and a box of ammo cartridges.")
            self.gold += 10
            self.loot_drop("ammo cartridge")
            self.iron_bonus += 2
        else:
            print("You shake your head. The railroad men mutter that you're missing an opportunity.")
            self.Tquest = "None"

    def encounter_iron_stage1(self):
        print("The railroad foreman storms into town.")
        print("'A wagon full of steel rails and tools never arrived. Bandits must've taken it!'")
        print("Options:")
        print("1) Track the missing wagon.")
        print("2) Refuse to help.")
        choice = input(": ").strip()

        if choice == "1":
            print("You ride out and find the wagon under bandit guard!")
            combat = Combat(self)
            combat.FindAttacker("bandit")
            escape = combat.Attack()
            if escape == False:
                print("You defeat the bandits and recover the supplies.")
                self.gold += 20
                self.loot_drop("ammo cartridge")
                self.iron_bonus += 1
            else:
                print("You retreat to save yourself.")
                self.Tquest = "None"
                self.iron_bonus -= 1
        else:
            print("The foreman scowls. 'Fine, I'll find someone else.'")
            self.iron_bonus -= 2
        self.iron_stage = 2
            

    def encounter_iron_stage2(self):
        print("Night falls. You hear shouting at the new train depot!")
        print("Options:")
        print("1) Investigate the depot.")
        print("2) Stay away.")
        choice = input(": ").strip()

        if choice == "1":
            print("You sneak into the depot and spot saboteurs planting dynamite.")
            if random.randint(1,10) <= self.shadow_skill + 2:
                print("You catch one saboteur alive. He blurts out about a coming train heist.")
                self.iron_stage = 3
            else:
                print("The saboteurs notice you! A fight breaks out.")
                combat = Combat(self)
                combat.FindAttacker("saboteur")
                combat.Attack()
                if self.Health > 0:
                    print("You stop the sabotage, but the plot deepens.")
                    self.iron_stage = 3
                else:
                    print("You fall at the depot. The railroad effort is doomed.")
                    self.Tquest = "None"
        else:
            print("You ignore the commotion. In the morning, the depot lies in ruins.")
            self.Hostility += 1
            self.Tquest = "None"

    def encounter_iron_stage3(self):
        bonus_used = False
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
            if self.iron_bonus >= 2:
                print("You may spend two bonus points you have gained to gain a temporary boost!")
                print("Will you spend them now?")
                choice = input(": ").strip()
                if choice.lower() == "yes":
                    self.iron_bonus -= 2
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
                        if random.randint(1, 10) <= self.trail_skill + 3:
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
                        if random.randint(1, 10) <= self.trail_skill + 2:
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
                        if random.randint(1, 10) <= self.trail_skill + 1:
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
                        if random.randint(1, 10) <= self.Speed + 3:
                            print("You slash a bandit and throw him out the window!")
                            bandits_in_car -= 1
                        else:
                            print("The bandit shoots first, grazing your shoulder! -8hp")
                            self.Health -= 8
                    else:
                        if random.randint(1, 10) <= self.strength_skill:
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
                    if random.randint(1, 10) <= self.shadow_skill + 2:
                        print("Bullets ping off the steel — you stay safe for now.")
                    else:
                        print("A stray shot punches through, grazing you! -4hp")
                        self.Health -= 4

                # --- Option 4: Melee rush ---
                elif choice == "4":
                    print("You charge forward, fists swinging!")
                    if bandits_in_car > 0:
                        if random.randint(1, 10) <= self.strength_skill + 1:
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
                        self.iron_bonus -= 2
                    else:
                        self.iron_bonus -= 1
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
                self.iron_stage = 4
            if bonus_used == True:
                self.MaxHealth -= 20

        else:
            print("You stay behind. The train arrives looted, passengers shaken.")
            self.Hostility += 2
            self.Tquest = "None"

    def encounter_iron_stage4(self):
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
                self.iron_stage = 5
            else:
                print("You fall. The bridge collapses. The railroad halts here forever.")
                self.Tquest = "None"
        else:
            print("You turn away. Hours later, the bridge collapses with a thunderous roar.")
            self.Hostility += 2
            self.Tquest = "None"

    def encounter_iron_stage5(self):
        print("A notorious outlaw, the Dynamite Kid, rides into town with crates of explosives.")
        print("He plans to stop the railroad once and for all.")
        print("Options:")
        print("1) Confront him in the streets.")
        print("2) Try to ambush him.")
        print("3) Walk away.")
        choice = input(": ").strip()

        if choice == "1":
            combat = Combat(self)
            combat.FindAttacker("dynamite kid")
            combat.Attack()
            if self.Health > 0:
                print("You defeat the Dynamite Kid in a blazing showdown!")
                self.gold += 100
                self.loot_drop("railway rifle")
                print("The railroad is saved. Fast travel between towns is now safer!")
            else:
                print("The Dynamite Kid plants his bombs. The town burns.")
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
        self.iron_stage = None


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
            "rattlesnake": {"health": 20, "damage": 7, "speed": 4, "loot": "small","type": "animal", "special": "venomous"}, 
            "viper": {"health": 10, "damage": 5, "speed": 5, "loot": "small", "type": "animal",},
            "cobra": {"health": 15, "damage": 10, "speed": 2, "loot": "small",  "type": "animal",},
            "wolf": {"health": 50, "damage": 15, "speed": 4, "loot": "medium", "type": "animal",},  
            "bison": {"health": 100, "damage": 15, "speed": 2, "loot": "large", "passive": True,  "type": "animal"},
            "pack of wolves": {"health": 70, "damage": 20, "speed": 4, "loot": "medium", "type": "pack"},
            "bear": {"health": 125, "damage": 30, "speed": 3, "loot": "medium",  "type": "animal"},
            "bandit": {"health": 80, "damage": 10, "speed": 4, "loot": "bandit",  "type": "human"},
            "mounted bandit": {"health": 120, "damage": 15, "speed": 7, "loot": "bandit",  "type": "human"},
            "brawler": {"health": 60, "damage": 5, "speed": 2, "loot": "townsperson",  "type": "human", },
            "sheriff": {"health": 65, "damage": 20, "speed": 2, "loot": "townsperson",  "type": "human"},
            "looter": {"health": 90, "damage": 10, "speed": 5, "loot": "rare",  "type": "human"},
            "bandit leader": {"health": 100, "damage": 35, "speed": 3, "loot": "ultra_rare",  "type": "human", "special": "alert", "bound": True},
            "tester": {"health": 100, "damage": 5, "speed": 3, "loot": "ultra_rare",  "type": "human", "armored": True, "bound": True},
            "phantom gunslinger": {"health": 100, "damage": 20, "speed": 3, "loot": "ultra_rare", "type": "ghost", "special": "ghostly_form"},
            }
        self.loots = {
            "small": ["small hide", "small meat"],
            "medium": ["medium hide", "medium meat"],
            "large": ["large hide", "large meat", "horn"],
            "bandit": ["revolver", "pistol_ammo", "bread"],
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
        enemy_damage = self.EnemyCombatant["damage"]
        enemy_speed = self.EnemyCombatant["speed"]
        enemy_loot = self.EnemyCombatant["loot"]
        enemy_health = self.EnemyCombatant["health"]
        # After setting up the enemy combatant
        if self.player.Day <= 7:
            if self.player.difficulty == 'adventure':
                enemy_health = int(self.EnemyCombatant["health"] * 0.75)
                enemy_damage = int(self.EnemyCombatant["damage"] * 0.75)
            elif self.player.difficulty == 'savage':
                enemy_health = int(self.EnemyCombatant["health"] * 1.25)
                enemy_damage = int(self.EnemyCombatant["damage"] * 1.1)

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
        
        Choice = input("Would you like to use an item before the combat? Yes/No:")
        if Choice == "Yes":
            self.player.use_item(combat=True, enemy_name=self.Enemy, enemy_combatant=self.EnemyCombatant)
        if self.player.Speed > self.EnemyCombatant["speed"]:
            TurnOrder = ["player", "enemy"]
        elif self.player.Speed < self.EnemyCombatant["speed"]:
            TurnOrder = ["enemy", "player"]
        else:
            TurnOrder = random.choice([["player", "enemy"], ["enemy", "player"]])
        stunned = False
        escape_boost = 0

        
        while self.EnemyCombatant["health"] > 0 and self.player.Health > 0:
            for turn in TurnOrder:
                if turn == "player":
                    print("\n--- Your Turn ---")
                    print("What will you do?")
                    print("1. Attack")
                    print("2. Use Item")
                    print("3. Try to Retreat")

                    choice = input("Choose an action: ").strip()


                    if choice == "1":
                        # Get list of owned weapons (weapons with known names)
                        weapon_choices = {
                            'revolver': (10, 15),
                            'rifle': (20, 25),
                            'shotgun': (20,40),
                            'colt pistol': (15,20),
                            'knife': (5, 10),
                            'bowie knife': (10, 15),
                            'winchester rifle': (50, 55),
                            'henry rifle': (30, 35),
                            'remington pistol': (15, 25),
                            'derringer pistol':      (5,  15),
                            'carbine rifle':         (25, 35),
                            'double barrel shotgun': (30, 50),
                            'tomahawk':              (15, 25),
                            'sharps rifle':     (35, 50),
                            'lever-action rifle':    (30, 35),
                            'sawed-off shotgun':     (15, 30),
                            'colt navy revolver':    (20, 25),
                            'cavalry saber':         (15, 25),
                        }
                        ammo_needed = {
                            'revolver': 'pistol_ammo',
                            'colt pistol': 'pistol_ammo',
                            'rifle': 'rifle_ammo',
                            'shotgun': 'shotgun_ammo',
                            'winchester rifle': 'rifle_ammo',
                            'henry rifle': 'rifle_ammo',
                            'remington pistol': 'pistol_ammo',
                            'derringer pistol': 'pistol_ammo',
                            'carbine rifle':      'rifle_ammo',
                            'double barrel shotgun': 'shotgun_ammo',
                            'sharps rifle':  'rifle_ammo',
                            'lever-action rifle': 'rifle_ammo',
                            'sawed-off shotgun':  'shotgun_ammo',
                            'colt navy revolver': 'pistol_ammo',
                        }


                        owned_weapons = [w for w in weapon_choices if w in self.player.itemsinventory]
                        if not owned_weapons:
                            print("You don't have any weapons, so you fight with your fists!")
                            player_attack = random.randint(2, 5)
                            player.play_sound("punch.mp3")
                        else:
                            while True:
                                print("Choose a weapon:")
                                for i, weapon in enumerate(owned_weapons, start=1):
                                    dmg = weapon_choices[weapon]
                                    ammo_info = ""
                                    if weapon in ammo_needed:
                                        ammo_type = ammo_needed[weapon]
                                        if ability_auto_ammo_belt == True:
                                            self.player.itemsinventory[ammo_type] = self.player.itemsinventory.get(ammo_type, 0) + 1
                                            print("Your ammo belt provides +1 ammo for your gun.")
                                            ability_auto_ammo_belt = False
                                        ammo_count = self.player.itemsinventory.get(ammo_type, 0)
                                        ammo_info = f" | Ammo: {ammo_count}"
                                    print(f"{i}. {weapon.capitalize()} (Damage: {dmg}){ammo_info}")
                                print(f"{len(owned_weapons) + 1}. Fists (No weapon)")

                                try:
                                    weapon_choice = int(input("Choice: "))
                                    if weapon_choice == len(owned_weapons) + 1:
                                        player_attack = random.randint(2, 5)
                                        print("You swing your fists!")
                                        player.play_sound("punch.mp3")
                                        break
                                    elif 1 <= weapon_choice <= len(owned_weapons):
                                        weapon = owned_weapons[weapon_choice - 1]
                                        if weapon in ammo_needed:
                                            ammo_type = ammo_needed[weapon]
                                            if self.player.itemsinventory.get(ammo_type, 0) < 1:
                                                print(f"You're out of {ammo_type}! Choose another weapon.")
                                                player.play_sound("blank_click.mp3")
                                                time.sleep(1,)
                                                continue
                                            else:
                                                self.player.itemsinventory[ammo_type] -= 1
                                                if self.player.itemsinventory[ammo_type] <= 0:
                                                    del self.player.itemsinventory[ammo_type]
                                                ammo_left = self.player.itemsinventory.get(ammo_type, 0)
                                                player.weapon_ability(weapon)
                                                print(f"You fire the {weapon}. Ammo left: {ammo_left}")
                                                player.weapon_sound(weapon)
                                        else:
                                            player.play_sound("knife.mp3")
                                            player.weapon_ability(weapon)
                                        dmg_range = weapon_choices[weapon]
                                        player_attack = random.randint(*dmg_range)
                                        player_attack = player_attack*player.dmg_modifier_multiply
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

                    elif choice == "2":
                        self.player.use_item(combat=True, enemy_name=self.Enemy, enemy_combatant=self.EnemyCombatant)


                    elif choice == "3":
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

                    else:
                        print("Invalid choice.")
                        continue
                time.sleep(2,)
                if enemy_health <= 0:
                    print(f"{self.Enemy.capitalize()} is dead.")
                    loot_item = random.choice(self.loots[enemy_loot])
                    self.player.loot_drop(loot_item)
                    self.player.score = self.player.score + 5
                    self.player.Health = round(self.player.Health)
                    self.player.Armor_Boost = 1
                    self.player.escape_boost = 0

                    player.dmg_modifier_multiply = 1
                    time.sleep(2,)
                    if player.invillage == True:
                        player.change_music("Town.mp3", -1)
                    else:
                        player.change_music("game_theme.mp3", -1)
                    return escape
                # Enemy's turn
                elif turn == "enemy":
                    print(f"\n--- {self.Enemy.capitalize()}'s Turn ---")
                    if "stun" in self.player.enemy_effects:
                        stunned = True
                        self.player.enemy_effects.remove("stun")
                    if "hphalf" in self.player.enemy_effects:
                        enemy_health -= enemy_health/2
                        self.player.enemy_effects.remove("hphalf")
                    if "+20HP" in self.player.enemy_effects:
                        enemy_health += 20
                        self.player.enemy_effects.remove("+20HP")
                    if stunned == True and self.EnemyCombatant.get("special", None) != "alert":
                        print("The enemy is dazed, unable to attack.")
                        stunned = False
                        continue
                    #Look up enemy's original max health
                    max_hp = self.Enemies[self.Enemy]["health"]
                    curr_hp = enemy_health
                    # Base miss chance: 1 in 5
                    if self.EnemyCombatant.get("special") == "alert":
                        miss_threshold = 0  # No chance to miss
                    else:
                        miss_threshold = 1
                        if curr_hp < max_hp * 0.5:
                            miss_threshold = 2
                        if curr_hp < max_hp * 0.25:
                            miss_threshold = 5

                    if miss_threshold > 0 and random.randint(1, 15) <= miss_threshold:
                        print(f"The {self.Enemy} attacks but you manage to dodge it.")
                        continue
                    Nenemy_damage = enemy_damage*self.player.Armor_Boost
                    self.player.Health -= Nenemy_damage
                    print(f"The {self.Enemy} strikes you for {Nenemy_damage} damage!")
                    print(f"Your health: {self.player.Health}")
                    print(f"Enemy health: {enemy_health}")
                    if self.EnemyCombatant.get("special") == "venomous":
                        self.player.poisoned = 1
                    if self.player.Health <= 0:
                        self.player.Death("You have been defeated by the " + self.Enemy + ".")
                    time.sleep(2,)


class GenericStore:
    def __init__(self, player, store_name, inventory):
        self.player = player
        self.store_name = store_name
        self.inventory = inventory

    def show_player_inventory(self):
        print("\nYour Inventory:")
        if not self.player.itemsinventory:
            print(" - (empty)")
        else:
            for item, quantity in self.player.itemsinventory.items():
                print(f" - {item.capitalize()}: {quantity}")
        input("Press enter to coninue:")

    def get_price_with_difficulty(self, base_price):
        if self.player.Hostility == 1:
            print()

        if self.player.difficulty == 'adventure':
            return int(base_price * 0.9)  # 10% cheaper
        elif self.player.difficulty == 'savage':
            return int(base_price * 1.1)  # 10% more expensive
        return base_price
        
    def show_inventory(self):
        print(f"\n--- {self.store_name} Inventory ---")
        item_list = []
        count = 0
        for value in self.inventory.items():
            count += 1
        for count, item in self.inventory.items():
            print(f"{item['name'].capitalize()} - ${self.get_price_with_difficulty(item['price'])} | Stock: {item['quantity']}")
            item_list.append(item['name'])
        print(f"\nYour Gold: ${self.player.gold:.2f}")
            
        return item_list

    def run_shop(self):
        print(f"Welcome to the {self.store_name}!")
        if random.randint(1,3) == 3:
            print(f"The owner walks over and greets you.")
            game_state = player.generate_game_state()
            event = f"The player walks into the {self.store_name}, and is greeted by the owner."
            NpC = "store owner"
            AI_File.narrate_dialogue(game_state, event, NpC)
        while True:
            item_list = self.show_inventory()
            print("\nWhat would you like to buy?")
            print("You can leave or look at your inventory at any time.")
            choice1 = input(": ").strip()

            actions = ['leave', 'inventory']
            complete_list = item_list + actions
            parsed = AI_File.parse_purchase(complete_list, choice1)
            print(parsed['choice'])
            choice = parsed.get('choice')
            if not choice:
                print("Invalid input, defaulting to 'help'.")
                choice = 'help'
            raw_quantity = parsed.get('quantity', '1')   # get as string
            if not raw_quantity.isdigit() or raw_quantity == "":
                amount = 1
            else:
                amount = int(raw_quantity)


            if choice == 'leave':
                print(f"Thanks for visiting the {self.store_name}.")
                break
            
            if choice == 'inventory':
                self.show_player_inventory()
                continue

            


            if choice not in item_list:
                print("That item doesn't exist.")
                continue
            item_name = choice.lower()  # string like "lasso"
            item = self.inventory[item_name]
            adjusted_price = self.get_price_with_difficulty(item['price'])
            
            if item['quantity'] < amount:
                print(f"{item['name'].capitalize()} is out of stock.")
                continue
            amount_price = adjusted_price*amount
            

            print(f"The AI understood you want to buy {amount} x {choice.capitalize()} for ${amount_price}.")
            confirm = input("Confirm purchase? (y/n): ").lower()

            if confirm != "n":
                print("Purchase cancelled.")
                continue

            if self.player.gold < amount_price:
                print("You don't have enough gold.")
                continue



            # Transaction
            item['quantity'] -= amount
            self.player.gold -= amount_price
            
            self.player.itemsinventory[item['name']] = self.player.itemsinventory.get(item['name'], 0) + amount
            print(f"You bought {amount} {item['name']} for ${amount_price}. Remaining gold: ${self.player.gold:.2f}")
            time.sleep(1,)


player = Player()

choice = input("Enter cheat code, or press enter to continue:").strip().upper()
if choice == "DAX":
    print("Correct")
    player.gold += 15

music_path = os.path.join(os.path.dirname(__file__), "game_theme.mp3")
if not os.path.exists(music_path):
    print("Music file not found!")
else:
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.5)

    print("Would you like music to play during the game? (yes/no)")
    choice = input(": ").strip().upper()
    if choice == "YES":
        pygame.mixer.music.play(-1)
    else:
        player.music = False


player.main_game_loop()
pygame.mixer.music.stop()
