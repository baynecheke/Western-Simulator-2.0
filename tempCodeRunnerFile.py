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
            6:  ("Hopeful Spirit", "Max health +5"),
            10:  ("Sharpened Mind", "Shadow skill +1"),
            16:  ("Strong Constitution", "Hunger reduced by 2."),
            20: ("Frontier Wisdom", "Travel speed +1"),
            30: ("Iron Will", "Max health increased by 10."),
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
