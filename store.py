# In store.py
import time
import random

class ShopItem:
    """A simple data class to hold item info."""
    def __init__(self, name, base_price, quantity):
        self.name = name
        self.base_price = base_price
        self.quantity = quantity

class ShopSession:
    """Handles the entire shopping interaction (UI and logic)."""
    def __init__(self, player, ai_file, store_name, inventory, use_ollama=True):
        self.player = player
        self.ai_file = ai_file
        self.store_name = store_name
        self.inventory = inventory # This will be a dict of {'item_name': ShopItem}
        self.use_ollama = use_ollama

    def _show_player_inventory(self):
        """Internal helper to show the player's inventory."""
        print("\nYour Inventory:")
        if not self.player.itemsinventory:
            print(" - (empty)")
        else:
            for item, quantity in self.player.itemsinventory.items():
                print(f" - {item.capitalize()}: {quantity}")
        input("Press enter to continue:")

    def _calculate_price(self, item, action="buy"):
        """Calculates the final price based on difficulty, hostility, or trade skill."""
        base_price = item.base_price
        
        if action == "buy":
            # Apply penalties for buying
            if self.player.Hostility == 1:
                base_price += 1
            elif self.player.Hostility == 2:
                base_price += 2
            elif self.player.Hostility >= 3:
                base_price += 3

            if self.player.difficulty == 'adventure':
                base_price = int(base_price * 0.9)  # 10% cheaper
            elif self.player.difficulty == 'savage':
                base_price = int(base_price * 1.1)  # 10% more expensive
            return base_price
        
        if action == "sell":
            # Apply bonuses for selling (e.g., trade_bonus)
            price = base_price + self.player.trade_bonus
            return int(price)
            
        return int(base_price) # Fallback: just return the base price

    def _display_wares(self):
        """Internal helper to print the store's inventory."""
        print(f"\n--- {self.store_name} Inventory ---")
        item_list = []
        for item_name, item_obj in self.inventory.items():
            price = self._calculate_price(item_obj, action="buy")
            print(f"{item_obj.name.capitalize()} - ${price} | Stock: {item_obj.quantity}")
            item_list.append(item_name)
        print(f"\nYour Gold: ${self.player.gold:.2f}")
        return item_list

    def run_buy_session(self):
        """Runs the main loop for a 'buy-only' shop."""
        print(f"Welcome to the {self.store_name}!")
        if random.randint(1,3) == 3:
            print(f"The owner walks over and greets you.")
            game_state = self.player.generate_game_state()
            event = f"The player walks into the {self.store_name}, and is greeted by the owner."
            NpC = "store owner"
            leave = self.ai_file.narrate_shop(game_state, event, NpC)
            if leave == 'leave':
                return
        
        while True:
            item_list = self._display_wares()
            print("\nWhat would you like to buy?")
            print("You can 'leave' or look at your 'inventory' at any time.")
            choice1 = input(": ").strip()

            actions = ['leave', 'inventory']
            complete_list = item_list + actions
            parsed = self.ai_file.parse_purchase(complete_list, choice1)
            choice = parsed.get('choice')
            
            if not choice:
                print("Invalid input, please try again.")
                continue

            raw_quantity = parsed.get('quantity', '1')
            amount = int(raw_quantity) if raw_quantity.isdigit() and int(raw_quantity) > 0 else 1

            if choice == 'leave':
                print(f"Thanks for visiting the {self.store_name}.")
                break
            
            if choice == 'inventory':
                self._show_player_inventory()
                continue
            
            if choice not in self.inventory:
                print("That item doesn't exist.")
                continue

            item = self.inventory[choice] # Get the ShopItem object
            adjusted_price = self._calculate_price(item, action="buy")
            
            if item.quantity < amount:
                print(f"Not enough {item.name.capitalize()} in stock.")
                continue
            
            total_cost = adjusted_price * amount
            
            print(f"I understood you want to buy {amount} x {choice.capitalize()} for ${total_cost}.")
            confirm = input("Confirm purchase? (yes/no): ").lower()
            yn_choice = self.ai_file.parse_YN(confirm)
            
            if yn_choice != "yes":
                print("Purchase cancelled.")
                continue

            if self.player.gold < total_cost:
                print("You don't have enough gold.")
                continue

            # Transaction
            item.quantity -= amount
            self.player.gold -= total_cost
            self.player.itemsinventory[item.name] = self.player.itemsinventory.get(item.name, 0) + amount
            print(f"You bought {amount} {item.name} for ${total_cost}. Remaining gold: ${self.player.gold:.2f}")
            time.sleep(1)

    def run_trade_session(self, sell_prices, trade_offers):
        """Runs a full trade/sell session."""
        self.player.play_sound("store_bell.mp3")
        print("You walk into the trading post. The trader greets you.")
        time.sleep(2)

        while True:
            print("\n--- Trading Post ---")
            print("1) Sell items")
            print("2) Swap items")
            print("3) Leave")

            choice = input("What would you like to do? ").strip()

            if choice == "1":
                # --- Sell logic ---
                if not self.player.itemsinventory:
                    print("Your inventory is empty.")
                    continue
                    
                print("Your Inventory (Sell Prices):")
                sellable_items = []
                for idx, (item, qty) in enumerate(self.player.itemsinventory.items(), 1):
                    price = sell_prices.get(item, 1) # Get price from provided dict
                    # We can use our new _calculate_price method for selling!
                    item_obj = ShopItem(item, price, qty) # Create a temp ShopItem
                    sell_price = self._calculate_price(item_obj, action="sell")
                    
                    print(f"{idx}. {item} (x{qty}) - Sell Price: ${sell_price}")
                    sellable_items.append(item)

                sell_choice = input("Enter the number of the item to sell or 'q' to cancel: ").strip()
                if sell_choice.lower() == "q":
                    continue
                if sell_choice.isdigit():
                    idx = int(sell_choice)
                    if 1 <= idx <= len(sellable_items):
                        item_to_sell = sellable_items[idx - 1]
                        
                        item_obj = ShopItem(item_to_sell, sell_prices.get(item_to_sell, 1), 1)
                        price = self._calculate_price(item_obj, action="sell")
                        
                        self.player.gold += price
                        self.player.itemsinventory[item_to_sell] -= 1
                        print(f"You sold 1 {item_to_sell} for ${price}. Current gold: ${self.player.gold}")
                        if self.player.itemsinventory[item_to_sell] <= 0:
                            del self.player.itemsinventory[item_to_sell]

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
                    if offer["give"] in self.player.itemsinventory:
                        print(f"Trade {offer['give']} for {offer['get']}? (yes/no)")
                        if input(": ").strip().lower() == "yes":
                            self.player.itemsinventory[offer["give"]] -= 1
                            if self.player.itemsinventory[offer["give"]] <= 0:
                                del self.player.itemsinventory[offer["give"]]
                            self.player.add_item(offer["get"]) # Use player's add_item
                            print(f"You traded {offer['give']} for {offer['get']}.")
                        else:
                            print("Trade declined.")
                    else:
                        print(f"You don't have a {offer['give']} to trade.")
            
            elif choice == "3":
                break
            else:
                print("Invalid choice.")