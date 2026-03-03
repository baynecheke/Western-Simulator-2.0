# game_html.py - WINTER VERSION WITH DYNAMIC THEMES & STATUSES

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Western Simulator - Winter</title>
    <link rel="icon" href="/static/favicon.ico">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap');

        /* --- 1. CSS VARIABLES FOR DYNAMIC THEMES --- */
        :root, body.theme-default {
            --bg-body: #3a2e25;
            --bg-image: url('https://www.transparenttextures.com/patterns/wood-pattern.png');
            --bg-panel: #fdf6e3;
            --bg-header: #8b4513;
            --border-main: #8b4513;
            --border-sub: #5a2d0c;
            --border-inner: #d2b48c;
            --text-main: #333333;
            --text-header: #ffffff;
            --text-muted: #6b7280;
            --btn-bg: #8b4513;
            --btn-hover: #a0522d;
            --btn-text: #ffffff;
            --progress-bg: #c7a78b;
        }

        body.theme-winter {
            --bg-body: #0f172a;
            --bg-image: url('https://www.transparenttextures.com/patterns/snow.png');
            --bg-panel: #1e293b;
            --bg-header: #0f172a;
            --border-main: #475569;
            --border-sub: #334155;
            --border-inner: #334155;
            --text-main: #e2e8f0;
            --text-header: #dbeafe; 
            --text-muted: #94a3b8;
            --btn-bg: #1e293b;
            --btn-hover: #334155;
            --btn-text: #f1f5f9;
            --progress-bg: #334155;
        }

        body.theme-night {
            --bg-body: #050505;
            --bg-image: url('https://www.transparenttextures.com/patterns/stardust.png');
            --bg-panel: #1a1512;
            --bg-header: #0a0807;
            --border-main: #3d2b1f;
            --border-sub: #261b14;
            --border-inner: #3d2b1f;
            --text-main: #d1c5b4;
            --text-header: #e8dcc8;
            --text-muted: #8c7b6b;
            --btn-bg: #2a1f18;
            --btn-hover: #3d2b1f;
            --btn-text: #d1c5b4;
            --progress-bg: #261b14;
        }

        body.theme-rain {
            --bg-body: #2c3539;
            --bg-image: url('https://www.transparenttextures.com/patterns/pinstriped-suit.png');
            --bg-panel: #3b444b;
            --bg-header: #232b2b;
            --border-main: #536872;
            --border-sub: #36454f;
            --border-inner: #536872;
            --text-main: #e0e5e5;
            --text-header: #ffffff;
            --text-muted: #9ba4a5;
            --btn-bg: #4a5d66;
            --btn-hover: #5c737e;
            --btn-text: #ffffff;
            --progress-bg: #36454f;
        }

        /* --- 2. BASE STYLING USING VARIABLES --- */
        body {
            font-family: 'Merriweather', serif;
            background-color: var(--bg-body);
            background-image: var(--bg-image);
            color: var(--text-main);
            transition: background-color 0.5s ease, color 0.5s ease;
        }

        .themed-panel { background-color: var(--bg-panel); border-color: var(--border-main); }
        .themed-header { background-color: var(--bg-header); border-color: var(--border-sub); color: var(--text-header); }
        .themed-section { background-color: var(--bg-panel); border-color: var(--border-inner); }
        .themed-text { color: var(--text-main); }
        .themed-text-header { color: var(--text-header); }
        .themed-muted { color: var(--text-muted); }

        /* Custom Scrollbars */
        #game-display::-webkit-scrollbar { width: 8px; }
        #game-display::-webkit-scrollbar-track { background: var(--bg-panel); }
        #game-display::-webkit-scrollbar-thumb { background: var(--border-main); border-radius: 4px; }

        /* Button Styling */
        .game-button {
            transition: all 0.15s ease-in-out;
            border: 1px solid var(--border-main);
            background-color: var(--btn-bg);
            color: var(--btn-text);
        }
        .game-button:hover {
            background-color: var(--btn-hover);
            border-color: var(--text-muted);
            transform: translateY(-2px);
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        
        .progress-bar-bg {
            background-color: var(--progress-bg);
            border: 1px solid var(--border-sub);
        }
        .progress-bar-fill {
            transition: width 0.5s ease-in-out;
        }

        /* --- 3. ZERO CLOG STATUS PILLS --- */
        .status-pill {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
        .status-negative { background-color: #991b1b; border: 1px solid #7f1d1d; } /* Deep Red */
        .status-positive { background-color: #166534; border: 1px solid #14532d; } /* Deep Green */
        .status-neutral { background-color: #ca8a04; border: 1px solid #a16207; } /* Deep Yellow/Orange */
    </style>
</head>

<body class="theme-winter flex items-center justify-center min-h-screen p-4">

    <div class="themed-panel w-full max-w-6xl shadow-2xl rounded-lg border-2 overflow-hidden flex flex-col" style="box-shadow: 0 10px 25px rgba(0,0,0,0.8); height: 90vh;">
        
        <header class="themed-header p-4 grid grid-cols-2 sm:grid-cols-4 gap-4 border-b-2">
            <div><strong>Location:</strong> <span id="stat-location" class="themed-text-header">Starting...</span></div>
            <div><strong>Day:</strong> <span id="stat-day" class="themed-text-header">1</span></div>
            <div><strong>Time:</strong> <span id="stat-time" class="themed-text-header">9:00</span></div>
            <div><strong>Difficulty:</strong> <span id="stat-difficulty" class="themed-text-header">Frontier</span></div>
        </header>

        <section class="themed-section p-4 border-b-2">
            <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
                
                <div class="flex flex-col">
                    <div class="flex justify-between font-bold text-sm themed-text">
                        <span>Health:</span>
                        <span id="stat-health-text">100 / 100</span>
                    </div>
                    <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                        <div id="stat-health-bar" class="progress-bar-fill bg-red-600 h-full text-white text-xs text-center leading-6" style="width: 100%;"></div>
                    </div>
                </div>

                <div id="heat-container" class="flex flex-col">
                    <div class="flex justify-between font-bold text-sm themed-text">
                        <span>Heat:</span>
                        <span id="stat-heat-text">100 / 100</span>
                    </div>
                    <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                        <div id="stat-heat-bar" class="progress-bar-fill bg-orange-500 h-full text-white text-xs text-center leading-6" style="width: 100%;"></div>
                    </div>
                </div>

                <div class="flex flex-col">
                    <div class="flex justify-between font-bold text-sm themed-text">
                        <span>Hunger:</span>
                        <span id="stat-hunger-text">0</span>
                    </div>
                    <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                        <div id="stat-hunger-bar" class="progress-bar-fill bg-emerald-600 h-full" style="width: 0%;"></div>
                    </div>
                </div>

                <div class="flex flex-col justify-center">
                    <div class="text-lg font-bold themed-text">
                        Gold: $<span id="stat-gold" class="text-yellow-400">50</span>
                    </div>
                </div>
            </div>

            <div id="status-area" class="mt-3 flex flex-wrap gap-2 empty:hidden">
                </div>
        </section>

        <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
            <div id="game-display" class="w-full md:w-2/3 p-6 overflow-y-auto space-y-3 themed-header">
                <p class="themed-muted">Connecting to server...</p>
            </div>

            <div class="w-full md:w-1/3 p-6 themed-panel border-t-2 md:border-t-0 md:border-l-2 border-[var(--border-inner)] overflow-y-auto">
                <h3 id="action-title" class="text-xl font-bold mb-4 border-b-2 border-[var(--border-sub)] pb-2 themed-text-header">Actions</h3>
                <div id="action-area" class="flex flex-col space-y-2">
                    <p class="themed-muted">Waiting for game to start...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const display = document.getElementById('game-display');
        const actionArea = document.getElementById('action-area');
        const actionTitle = document.getElementById('action-title');
        
        // Stat Elements
        const statLocation = document.getElementById('stat-location');
        const statDay = document.getElementById('stat-day');
        const statTime = document.getElementById('stat-time');
        const statDifficulty = document.getElementById('stat-difficulty');
        const statGold = document.getElementById('stat-gold');
        
        // Bars
        const statHealthText = document.getElementById('stat-health-text');
        const statHealthBar = document.getElementById('stat-health-bar');
        
        const statHeatText = document.getElementById('stat-heat-text');
        const statHeatBar = document.getElementById('stat-heat-bar');
        
        const statHungerText = document.getElementById('stat-hunger-text');
        const statHungerBar = document.getElementById('stat-hunger-bar');

        // Status Area
        const statusArea = document.getElementById('status-area');
        
        const soundEffects = {};
        let backgroundMusic = null;
        let sessionId = null;

        // --- NEW HELPER FUNCTIONS FOR IMMERSION ---
        function setTheme(themeName) {
            // 1. Change the background and colors
            document.body.className = `theme-${themeName} flex items-center justify-center min-h-screen p-4`;
            
            // 2. Hide or Show the Heat bar
            const heatContainer = document.getElementById('heat-container');
            if (heatContainer) {
                if (themeName === 'winter') {
                    heatContainer.classList.remove('hidden'); // Show it
                } else {
                    heatContainer.classList.add('hidden');    // Hide it
                }
            }
        }

        function updateStatuses(activeStatuses) {
            // activeStatuses should be an array of objects: [{id: 'poison', text: 'Poisoned', type: 'negative'}, ...]
            statusArea.innerHTML = ''; // Clear old statuses
            
            if (!activeStatuses || activeStatuses.length === 0) return;

            activeStatuses.forEach(status => {
                const pill = document.createElement('span');
                pill.textContent = status.text;
                pill.className = `status-pill status-${status.type}`;
                pill.id = `status-${status.id}`;
                statusArea.appendChild(pill);
            });
        }
        // ------------------------------------------

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
                audio.play().catch(e => console.warn(`Audio play failed: ${e.message}`));
                if (loop) backgroundMusic = audio;
            } catch (e) { console.error(`Error playing sound ${src}:`, e); }
        }

        function addMessage(text) {
            const p = document.createElement('p');
            p.innerHTML = text.replace(/(\\n|\\r\\n|\\r)/gm, '<br>');
            p.className = "themed-text"; 
            display.appendChild(p);
            display.scrollTop = display.scrollHeight; 
        }

        function clearActions() { actionArea.innerHTML = ''; }

        async function sendResponse(choice) {
            clearActions();
            actionTitle.textContent = "Actions";
            actionArea.innerHTML = '<p class="themed-muted">Waiting for server...</p>';
            try {
                if (!sessionId) {
                    addMessage("[Session Error]: No active session. Refresh to start again.");
                    return;
                }
                await fetch('/send_response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 'choice': choice, 'session_id': sessionId })
                });
                pollServer();
            } catch (error) { addMessage(`[Connection Error]: ${error.message}`); }
        }
        
        function handleServerMessages(messages) {
            messages.forEach(msg => {
                switch (msg.type) {
                    case 'game_message': addMessage(msg.text); break;
                    case 'play_sound': loadAndPlaySound(msg.file, msg.loop); break;
                    case 'change_music': loadAndPlaySound(msg.file, msg.loop); break;
                    case 'update_stats': updateStats(msg.payload); break;
                    case 'ask_for_choice': showChoices(msg.prompt, msg.choices); break;
                    case 'ask_for_text': showTextInput(msg.prompt); break;
                    case 'game_over': addMessage(msg.text); stopPolling(); break;
                    
                    // NEW COMMANDS FOR YOU TO WIRE UP LATER
                    case 'set_theme': setTheme(msg.theme); break;
                    case 'update_statuses': updateStatuses(msg.statuses); break;
                }
            });
        }
        
        function updateStats(data) {
            if (!data) return;
            statLocation.textContent = data.location;
            statDay.textContent = data.day;
            statTime.textContent = data.time;
            statDifficulty.textContent = data.difficulty;
            statGold.textContent = data.gold;
            
            // Health
            const healthPercent = (data.health / data.max_health) * 100;
            statHealthText.textContent = `${data.health} / ${data.max_health}`;
            statHealthBar.style.width = `${healthPercent}%`;
            
            // Heat
            const currentHeat = data.heat !== undefined ? data.heat : 100;
            const maxHeat = data.max_heat !== undefined ? data.max_heat : 100;
            const heatPercent = (currentHeat / maxHeat) * 100;
            statHeatText.textContent = `${currentHeat} / ${maxHeat}`;
            statHeatBar.style.width = `${heatPercent}%`;

            // Hunger (Scale of 10)
            const maxHunger = 10; 
            const hungerPercent = (data.hunger / maxHunger) * 100;
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
                    button.className = "game-button w-full text-left p-3 rounded shadow-md";
                    button.onclick = () => sendResponse(choice); 
                    actionArea.appendChild(button);
                });
            } else { addMessage("[Error: Server asked for a choice but provided no options.]") }
        }

        function showTextInput(prompt) {
            clearActions();
            actionTitle.textContent = prompt || "Enter a value:";
            const input = document.createElement('input');
            input.type = "text";
            input.className = "w-full p-2 border-2 border-[var(--border-main)] bg-[var(--bg-body)] text-[var(--text-main)] rounded outline-none";
            const submit = document.createElement('button');
            submit.textContent = "Submit";
            submit.className = "game-button w-full p-2 rounded shadow-md mt-2";
            submit.onclick = () => sendResponse(input.value);
            input.onkeydown = (e) => { if (e.key === 'Enter') sendResponse(input.value); };
            actionArea.appendChild(input);
            actionArea.appendChild(submit);
            input.focus();
        }

        let pollInterval;
        let isPolling = false; 

        async function pollServer() {
            if (isPolling) return; 
            isPolling = true;
            try {
                const url = sessionId ? `/get_update?session_id=${encodeURIComponent(sessionId)}` : '/get_update';
                const response = await fetch(url);
                if (!response.ok) throw new Error(`Server responded with status ${response.status}`);
                const data = await response.json();
                if (data.messages && data.messages.length > 0) handleServerMessages(data.messages);
            } catch (error) {
                console.error("Poll error:", error);
            }
            isPolling = false;
        }

        function startPolling() { 
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(pollServer, 1000); 
        }
        function stopPolling() { clearInterval(pollInterval); }

        async function initializeGame() {
            display.innerHTML = '';
            addMessage('Connecting to server...');
            try {
                const response = await fetch('/start_game', { method: 'POST' });
                const data = await response.json();
                sessionId = data.session_id;
                addMessage('Connected! Starting game...');
                startPolling();
            } catch (error) { addMessage(`[Fatal Error] Could not connect to server: ${error.message}`); }
        }

        initializeGame();
    </script>
    <script>
        function endSession() {
            if (!sessionId || !navigator.sendBeacon) return;
            const payload = JSON.stringify({ session_id: sessionId });
            const blob = new Blob([payload], { type: 'application/json' });
            navigator.sendBeacon('/end_session', blob);
        }

        window.addEventListener('pagehide', endSession);
        window.addEventListener('beforeunload', endSession);
    </script>

    <div class="fixed bottom-0 right-0 p-4 flex gap-2 bg-[var(--bg-header)] border-t border-[var(--border-sub)] z-50">
        <input type="text" id="saveName" placeholder="Save Name" class="bg-[var(--bg-body)] text-[var(--text-main)] p-2 border border-[var(--border-main)] rounded outline-none">
        <button onclick="saveGame()" class="bg-green-700 hover:bg-green-600 text-white px-3 py-1 rounded border border-green-900 shadow">Save</button>
        <button onclick="loadGame()" class="bg-blue-700 hover:bg-blue-600 text-white px-3 py-1 rounded border border-blue-900 shadow">Load</button>
    </div>

    <script>
        async function saveGame() {
            const name = document.getElementById('saveName').value;
            if (!name) return alert("Please enter a name to save.");
            
            try {
                const res = await fetch('/save_game', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: name, session_id: sessionId})
                });
                const data = await res.json();
                alert(data.status);
            } catch (e) {
                alert("Connection error: " + e);
            }
        }

        async function loadGame() {
            const name = document.getElementById('saveName').value;
            if (!name) return alert("Please enter a name to load.");
            
            try {
                const res = await fetch('/load_game', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: name, session_id: sessionId})
                });
                const data = await res.json();
                alert(data.status);
                // Force an immediate update to show loaded stats
                pollServer(); 
            } catch (e) {
                alert("Connection error: " + e);
            }
        }
    </script>
</body>
</html>
"""