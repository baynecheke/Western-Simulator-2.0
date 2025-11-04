# This file just holds our HTML frontend as a Python string.
# This makes it easier for server.py to serve it.

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Western Simulator</title>
    <!-- 1. Load Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- 2. Load Socket.IO Client -->
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap');
        body {
            font-family: 'Merriweather', serif;
            background-color: #3a2e25; /* Dark brown background */
            background-image: url('https://www.toptal.com/designers/subtlepatterns/uploads/wood-pattern.png');
        }
        /* Custom scrollbar for the display */
        #game-display::-webkit-scrollbar { width: 8px; }
        #game-display::-webkit-scrollbar-track { background: #fdf6e3; }
        #game-display::-webkit-scrollbar-thumb { background: #8b4513; border-radius: 4px; }
        .game-button {
            transition: all 0.15s ease-in-out;
            border: 2px solid #5a2d0c;
        }
        .game-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            background-color: #a0522d; /* Sienna */
        }
        /* Style for the health/hunger bars */
        .progress-bar-bg {
            background-color: #c7a78b; /* Desaturated brown */
            border: 2px solid #5a2d0c;
        }
        .progress-bar-fill {
            transition: width 0.5s ease-in-out;
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">

    <!-- Main Game Container -->
    <div class="w-full max-w-5xl bg-[#fdf6e3] shadow-2xl rounded-lg border-4 border-[#8b4513] overflow-hidden" style="box-shadow: 0 10px 25px rgba(0,0,0,0.5); height: 90vh; display: flex; flex-direction: column;">
        
        <!-- Header / Main Stats -->
        <header class="p-4 bg-[#8b4513] text-white grid grid-cols-2 sm:grid-cols-4 gap-4 border-b-4 border-[#5a2d0c]">
            <div><strong>Location:</strong> <span id="stat-location">Starting...</span></div>
            <div><strong>Day:</strong> <span id="stat-day">1</span></div>
            <div><strong>Time:</strong> <span id="stat-time">9:00</span></div>
            <div><strong>Difficulty:</strong> <span id="stat-difficulty">Frontier</span></div>
        </header>

        <!-- Player Status Bar -->
        <section class="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4 border-b-2 border-[#d2b48c] bg-[#f7eecf]">
            <!-- Health Bar -->
            <div class="flex flex-col">
                <div class="flex justify-between font-bold text-sm">
                    <span>Health:</span>
                    <span id="stat-health-text">100 / 100</span>
                </div>
                <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                    <div id="stat-health-bar" class="progress-bar-fill bg-red-600 h-full text-white text-xs text-center leading-6" style="width: 100%;"></div>
                </div>
            </div>
            <!-- Hunger Bar -->
            <div class="flex flex-col">
                <div class="flex justify-between font-bold text-sm">
                    <span>Hunger:</span>
                    <span id="stat-hunger-text">0</span>
                </div>
                <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                    <div id="stat-hunger-bar" class="progress-bar-fill bg-yellow-600 h-full" style="width: 0%;"></div>
                </div>
            </div>
            <!-- Gold -->
            <div class="text-lg font-bold">
                Gold: $<span id="stat-gold">50</span>
            </div>
        </section>

        <!-- Main Game Display & Actions -->
        <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            <!-- Left: Game Text Display ("Console") -->
            <div id="game-display" class="w-full md:w-2/3 p-6 overflow-y-auto space-y-3">
                <p class="text-gray-700">Connecting to server...</p>
            </div>

            <!-- Right: Action Buttons/Input -->
            <div class="w-full md:w-1/3 p-6 bg-[#f7eecf] border-t-2 md:border-t-0 md:border-l-2 border-[#d2b48c] overflow-y-auto">
                <h3 id="action-title" class="text-xl font-bold mb-4 border-b-2 border-gray-400 pb-2">Actions</h3>
                <div id="action-area" class="flex flex-col space-y-2">
                    <p class="text-gray-500">Waiting for game to start...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Connect to our Socket.IO server
        const socket = io();

        // --- Get DOM Elements ---
        const display = document.getElementById('game-display');
        const actionArea = document.getElementById('action-area');
        const actionTitle = document.getElementById('action-title');
        
        // Stat elements
        const statLocation = document.getElementById('stat-location');
        const statDay = document.getElementById('stat-day');
        const statTime = document.getElementById('stat-time');
        const statDifficulty = document.getElementById('stat-difficulty');
        const statHealthText = document.getElementById('stat-health-text');
        const statHealthBar = document.getElementById('stat-health-bar');
        const statHungerText = document.getElementById('stat-hunger-text');
        const statHungerBar = document.getElementById('stat-hunger-bar');
        const statGold = document.getElementById('stat-gold');
        
        // --- NEW AUDIO LOGIC ---
        const soundEffects = {};
        let backgroundMusic = null;

        function loadAndPlaySound(src, loop = false) {
            try {
                if (backgroundMusic && loop) {
                    backgroundMusic.pause();
                    backgroundMusic = null;
                }
                
                let audio = soundEffects[src];
                if (!audio) {
                    audio = new Audio(src);
                    soundEffects[src] = audio;
                }
                
                audio.loop = loop;
                audio.play().catch(e => console.warn(`Audio play failed (user may need to click first): ${e.message}`));

                if (loop) {
                    backgroundMusic = audio;
                }
            } catch (e) {
                console.error(`Error playing sound ${src}:`, e);
            }
        }

        // --- Helper Function to Add Messages ---
        function addMessage(text) {
            const p = document.createElement('p');
            // This line supports newlines (like \n)
            p.innerHTML = text.replace(/(\\n|\\r\\n|\\r)/gm, '<br>');
            p.className = "text-gray-800";
            display.appendChild(p);
            // Auto-scroll to the bottom
            display.scrollTop = display.scrollHeight;
        }

        function clearActions() {
            actionArea.innerHTML = '';
        }

        function sendResponse(choice) {
            clearActions();
            actionTitle.textContent = "Actions";
            actionArea.innerHTML = '<p class="text-gray-500">Waiting for server...</p>';
            // Send the chosen value back to the server
            socket.emit('player_response', { 'choice': choice });
        }

        // --- Socket.IO Event Listeners (The "Ear") ---

        socket.on('connect', () => {
            display.innerHTML = ''; // Clear "Connecting..."
            addMessage('Connected! Starting game...');
            
            // Check for a local save file
            const localSave = localStorage.getItem('western_sim_save');
            if (localSave) {
                addMessage("Save file found. Loading game...");
                socket.emit('load_game', { 'save_data': localSave });
            } else {
                addMessage("No save file found. Starting new game...");
                // No need to send anything, server will start new game by default
            }
        });

        socket.on('game_message', (data) => {
            // This is our new "print()"
            addMessage(data.text);
        });
        
        socket.on('play_sound', (data) => {
            loadAndPlaySound(data.file, data.loop);
        });
        
        socket.on('change_music', (data) => {
            loadAndPlaySound(data.file, data.loop);
        });
        
        socket.on('update_stats', (data) => {
            // This listener updates all the stat bars
            statLocation.textContent = data.location;
            statDay.textContent = data.day;
            statTime.textContent = data.time;
            statDifficulty.textContent = data.difficulty;
            statGold.textContent = data.gold;
            
            // Health
            const healthPercent = (data.health / data.max_health) * 100;
            statHealthText.textContent = `${data.health} / ${data.max_health}`;
            statHealthBar.style.width = `${healthPercent}%`;
            
            // Hunger (assuming max hunger is 3 for the bar)
            const hungerPercent = (data.hunger / 3) * 100;
            statHungerText.textContent = data.hunger;
            statHungerBar.style.width = `${Math.min(hungerPercent, 100)}%`;
        });

        socket.on('ask_for_choice', (data) => {
            // This is our new "input()" for buttons
            clearActions();
            actionTitle.textContent = data.prompt || "Choose an action:";
            
            if (data.choices && data.choices.length > 0) {
                data.choices.forEach(choice => {
                    const button = document.createElement('button');
                    // Capitalize each word for the button text
                    button.textContent = choice.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    button.className = "game-button w-full text-left p-3 bg-[#8b4513] text-white rounded shadow-md";
                    
                    button.onclick = () => {
                        // Send the *original* value back, not the capitalized one
                        sendResponse(choice); 
                    };
                    actionArea.appendChild(button);
                });
            } else {
                addMessage("[Error: Server asked for a choice but provided no options.]")
            }
        });

        socket.on('ask_for_text', (data) => {
            // This is for free-form input (like save names)
            clearActions();
            actionTitle.textContent = data.prompt || "Enter a value:";
            
            const input = document.createElement('input');
            input.type = "text";
            input.className = "w-full p-2 border-2 border-gray-400 rounded focus:border-[#8b4513] outline-none";
            
            const submit = document.createElement('button');
            submit.textContent = "Submit";
            submit.className = "game-button w-full p-2 bg-[#8b4513] text-white rounded shadow-md mt-2";
            
            submit.onclick = () => {
                sendResponse(input.value);
            };
            
            // Allow pressing Enter
            input.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    sendResponse(input.value);
                }
            };
            
            actionArea.appendChild(input);
            actionArea.appendChild(submit);
            input.focus();
        });
        
        socket.on('save_data', (data) => {
            // Server is sending us a save file!
            localStorage.setItem('western_sim_save', data.json_string);
            addMessage("[Game Saved to Browser]");
        });

    </script>
</body>
</html>
"""

