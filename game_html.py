# This file just holds our HTML frontend as a Python string.

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Western Simulator</title>
    <script src="https://cdn.tailwindcss.com"></script>
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

    <div class="w-full max-w-5xl bg-[#fdf6e3] shadow-2xl rounded-lg border-4 border-[#8b4513] overflow-hidden" style="box-shadow: 0 10px 25px rgba(0,0,0,0.5); height: 90vh; display: flex; flex-direction: column;">
        
        <header class="p-4 bg-[#8b4513] text-white grid grid-cols-2 sm:grid-cols-4 gap-4 border-b-4 border-[#5a2d0c]">
            <div><strong>Location:</strong> <span id="stat-location">Starting...</span></div>
            <div><strong>Day:</strong> <span id="stat-day">1</span></div>
            <div><strong>Time:</strong> <span id="stat-time">9:00</span></div>
            <div><strong>Difficulty:</strong> <span id="stat-difficulty">Frontier</span></div>
        </header>

        <section class="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4 border-b-2 border-[#d2b48c] bg-[#f7eecf]">
            <div class="flex flex-col">
                <div class="flex justify-between font-bold text-sm">
                    <span>Health:</span>
                    <span id="stat-health-text">100 / 100</span>
                </div>
                <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                    <div id="stat-health-bar" class="progress-bar-fill bg-red-600 h-full text-white text-xs text-center leading-6" style="width: 100%;"></div>
                </div>
            </div>
            <div class="flex flex-col">
                <div class="flex justify-between font-bold text-sm">
                    <span>Hunger:</span>
                    <span id="stat-hunger-text">0</span>
                </div>
                <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                    <div id="stat-hunger-bar" class="progress-bar-fill bg-yellow-600 h-full" style="width: 0%;"></div>
                </div>
            </div>
            <div class="text-lg font-bold">
                Gold: $<span id="stat-gold">50</span>
            </div>
        </section>

        <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            <div id="game-display" class="w-full md:w-2/3 p-6 overflow-y-auto space-y-3">
                <p class="text-gray-700">Connecting to server...</p>
            </div>

            <div class="w-full md:w-1/3 p-6 bg-[#f7eecf] border-t-2 md:border-t-0 md:border-l-2 border-[#d2b48c] overflow-y-auto">
                <h3 id="action-title" class="text-xl font-bold mb-4 border-b-2 border-gray-400 pb-2">Actions</h3>
                <div id="action-area" class="flex flex-col space-y-2">
                    <p class="text-gray-500">Waiting for game to start...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
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
            p.innerHTML = text.replace(/(\\n|\\r\\n|\\r)/gm, '<br>');
            p.className = "text-gray-800";
            display.appendChild(p);
            display.scrollTop = display.scrollHeight; // Auto-scroll
        }

        function clearActions() {
            actionArea.innerHTML = '';
        }

        // --- NEW: Send player's response to the server ---
        async function sendResponse(choice) {
            clearActions();
            actionTitle.textContent = "Actions";
            actionArea.innerHTML = '<p class="text-gray-500">Waiting for server...</p>';
            
            try {
                await fetch('/send_response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 'choice': choice })
                });
                // After sending, immediately poll for the next update
                pollServer();
            } catch (error) {
                addMessage(`[Connection Error] Could not send response: ${error.message}`);
            }
        }
        
        // --- NEW: Handle all commands from the server ---
        function handleServerMessages(messages) {
            messages.forEach(msg => {
                switch (msg.type) {
                    case 'game_message':
                        addMessage(msg.text);
                        break;
                    case 'play_sound':
                        loadAndPlaySound(msg.file, msg.loop);
                        break;
                    case 'change_music':
                        loadAndPlaySound(msg.file, msg.loop);
                        break;
                    case 'update_stats':
                        updateStats(msg.payload);
                        break;
                    case 'ask_for_choice':
                        showChoices(msg.prompt, msg.choices);
                        break;
                    case 'ask_for_text':
                        showTextInput(msg.prompt);
                        break;
                    case 'game_over':
                        addMessage(msg.text);
                        stopPolling(); // Stop the game loop
                        break;
                }
            });
        }
        
        function updateStats(data) {
            statLocation.textContent = data.location;
            statDay.textContent = data.day;
            statTime.textContent = data.time;
            statDifficulty.textContent = data.difficulty;
            statGold.textContent = data.gold;
            const healthPercent = (data.health / data.max_health) * 100;
            statHealthText.textContent = `${data.health} / ${data.max_health}`;
            statHealthBar.style.width = `${healthPercent}%`;
            const hungerPercent = (data.hunger / 3) * 100;
            statHungerText.textContent = data.hunger;
            statHungerBar.style.width = `${Math.min(hungerPercent, 100)}%`;
        }

        function showChoices(prompt, choices) {
            clearActions();
            actionTitle.textContent = prompt || "Choose an action:";
            if (choices && choices.length > 0) {
                choices.forEach(choice => {
                    const button = document.createElement('button');
                    button.textContent = choice.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    button.className = "game-button w-full text-left p-3 bg-[#8b4513] text-white rounded shadow-md";
                    button.onclick = () => sendResponse(choice); 
                    actionArea.appendChild(button);
                });
            } else {
                addMessage("[Error: Server asked for a choice but provided no options.]")
            }
        }

        function showTextInput(prompt) {
            clearActions();
            actionTitle.textContent = prompt || "Enter a value:";
            
            const input = document.createElement('input');
            input.type = "text";
            input.className = "w-full p-2 border-2 border-gray-400 rounded focus:border-[#8b4513] outline-none";
            
            const submit = document.createElement('button');
            submit.textContent = "Submit";
            submit.className = "game-button w-full p-2 bg-[#8b4513] text-white rounded shadow-md mt-2";
            
            submit.onclick = () => sendResponse(input.value);
            input.onkeydown = (e) => {
                if (e.key === 'Enter') sendResponse(input.value);
            };
            
            actionArea.appendChild(input);
            actionArea.appendChild(submit);
            input.focus();
        }

        // --- NEW: Polling Logic ---
        let pollInterval;
        let isPolling = false; // Prevents multiple polls at once

        async function pollServer() {
            if (isPolling) return; // Don't stack requests
            isPolling = true;
            try {
                const response = await fetch('/get_update');
                if (!response.ok) {
                    throw new Error(`Server responded with status ${response.status}`);
                }
                const data = await response.json();
                if (data.messages && data.messages.length > 0) {
                    handleServerMessages(data.messages);
                }
            } catch (error) {
                addMessage(`[Connection Error] Lost connection to server. Retrying...`);
                console.error("Poll error:", error);
            }
            isPolling = false;
        }

        function startPolling() {
            pollInterval = setInterval(pollServer, 1000); // Poll every 1 second
        }

        function stopPolling() {
            clearInterval(pollInterval);
        }

        // --- NEW: Start the Game ---
        async function initializeGame() {
            display.innerHTML = '';
            addMessage('Connecting to server...');
            try {
                // 1. Tell the server to start the game thread
                await fetch('/start_game', { method: 'POST' });
                addMessage('Connected! Starting game...');
                
                // 2. Start polling for updates
                startPolling();
                
                // Note: We don't need save game logic for this rewrite,
                // but you could add it back here later.
                
            } catch (error) {
                addMessage(`[Fatal Error] Could not connect to server: ${error.message}`);
            }
        }

        // Start the game when the page loads
        initializeGame();

    </script>
</body>
</html>
"""