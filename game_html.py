# game_html.py - WINTER VERSION

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

        /* WINTER THEME */
        body {
            font-family: 'Merriweather', serif;
            background-color: #0f172a; /* Slate 900 */
            color: #e2e8f0; /* Slate 200 */
            background-image: url('https://www.transparenttextures.com/patterns/snow.png');
        }

        /* Custom Scrollbar (Icy Blue) */
        #game-display::-webkit-scrollbar { width: 8px; }
        #game-display::-webkit-scrollbar-track { background: #1e293b; }
        #game-display::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 4px; }

        /* Button Styling (Cold Steel) */
        .game-button {
            transition: all 0.15s ease-in-out;
            border: 1px solid #475569; /* Slate border */
            background-color: #1e293b; 
            color: #f1f5f9;
        }
        .game-button:hover {
            background-color: #334155; 
            border-color: #94a3b8; 
            transform: translateY(-2px);
            box-shadow: 0 0 10px rgba(148, 163, 184, 0.3); /* Icy glow */
        }
        
        .progress-bar-bg {
            background-color: #334155; 
            border: 1px solid #64748b;
        }
        .progress-bar-fill {
            transition: width 0.5s ease-in-out;
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">

    <div class="w-full max-w-5xl bg-[#1e293b] shadow-2xl rounded-lg border-2 border-[#475569] overflow-hidden" style="box-shadow: 0 10px 25px rgba(0,0,0,0.8); height: 90vh; display: flex; flex-direction: column;">
        
        <header class="p-4 bg-[#0f172a] text-blue-100 grid grid-cols-2 sm:grid-cols-4 gap-4 border-b-2 border-[#334155]">
            <div><strong>Location:</strong> <span id="stat-location" class="text-blue-200">Starting...</span></div>
            <div><strong>Day:</strong> <span id="stat-day" class="text-blue-200">1</span></div>
            <div><strong>Time:</strong> <span id="stat-time" class="text-blue-200">9:00</span></div>
            <div><strong>Difficulty:</strong> <span id="stat-difficulty" class="text-blue-200">Frontier</span></div>
        </header>

        <section class="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4 border-b-2 border-[#334155] bg-[#1e293b]">
            <div class="flex flex-col">
                <div class="flex justify-between font-bold text-sm text-slate-300">
                    <span>Health:</span>
                    <span id="stat-health-text">100 / 100</span>
                </div>
                <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                    <div id="stat-health-bar" class="progress-bar-fill bg-cyan-700 h-full text-white text-xs text-center leading-6" style="width: 100%;"></div>
                </div>
            </div>
            <div class="flex flex-col">
                <div class="flex justify-between font-bold text-sm text-slate-300">
                    <span>Heat/Hunger:</span>
                    <span id="stat-hunger-text">0</span>
                </div>
                <div class="w-full progress-bar-bg rounded overflow-hidden mt-1 h-6">
                    <div id="stat-hunger-bar" class="progress-bar-fill bg-orange-600 h-full" style="width: 0%;"></div>
                </div>
            </div>
            <div class="text-lg font-bold text-slate-200">
                Gold: $<span id="stat-gold" class="text-yellow-400">50</span>
            </div>
        </section>

        <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            <div id="game-display" class="w-full md:w-2/3 p-6 overflow-y-auto space-y-3 bg-[#0f172a]">
                <p class="text-slate-400">Connecting to server...</p>
            </div>

            <div class="w-full md:w-1/3 p-6 bg-[#1e293b] border-t-2 md:border-t-0 md:border-l-2 border-[#334155] overflow-y-auto">
                <h3 id="action-title" class="text-xl font-bold mb-4 border-b-2 border-slate-600 pb-2 text-blue-100">Actions</h3>
                <div id="action-area" class="flex flex-col space-y-2">
                    <p class="text-slate-500">Waiting for game to start...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const display = document.getElementById('game-display');
        const actionArea = document.getElementById('action-area');
        const actionTitle = document.getElementById('action-title');
        const statLocation = document.getElementById('stat-location');
        const statDay = document.getElementById('stat-day');
        const statTime = document.getElementById('stat-time');
        const statDifficulty = document.getElementById('stat-difficulty');
        const statHealthText = document.getElementById('stat-health-text');
        const statHealthBar = document.getElementById('stat-health-bar');
        const statHungerText = document.getElementById('stat-hunger-text');
        const statHungerBar = document.getElementById('stat-hunger-bar');
        const statGold = document.getElementById('stat-gold');
        
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
                audio.play().catch(e => console.warn(`Audio play failed: ${e.message}`));
                if (loop) backgroundMusic = audio;
            } catch (e) { console.error(`Error playing sound ${src}:`, e); }
        }

        // Updated for Winter text color
        function addMessage(text) {
            const p = document.createElement('p');
            p.innerHTML = text.replace(/(\\n|\\r\\n|\\r)/gm, '<br>');
            p.className = "text-slate-300"; // Light grey text for dark background
            display.appendChild(p);
            display.scrollTop = display.scrollHeight; 
        }

        function clearActions() { actionArea.innerHTML = ''; }

        async function sendResponse(choice) {
            clearActions();
            actionTitle.textContent = "Actions";
            actionArea.innerHTML = '<p class="text-slate-500">Waiting for server...</p>';
            try {
                await fetch('/send_response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 'choice': choice })
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
                    // Winter Button Styles
                    button.className = "game-button w-full text-left p-3 rounded shadow-md text-blue-100 hover:text-white";
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
            // Winter Input Styles
            input.className = "w-full p-2 border-2 border-slate-600 bg-slate-900 text-white rounded focus:border-blue-400 outline-none";
            const submit = document.createElement('button');
            submit.textContent = "Submit";
            // Winter Submit Styles
            submit.className = "game-button w-full p-2 text-white rounded shadow-md mt-2";
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
                const response = await fetch('/get_update');
                if (!response.ok) throw new Error(`Server responded with status ${response.status}`);
                const data = await response.json();
                if (data.messages && data.messages.length > 0) handleServerMessages(data.messages);
            } catch (error) {
                addMessage(`[Connection Error] Lost connection to server. Retrying...`);
                console.error("Poll error:", error);
            }
            isPolling = false;
        }

        function startPolling() { pollInterval = setInterval(pollServer, 1000); }
        function stopPolling() { clearInterval(pollInterval); }

        async function initializeGame() {
            display.innerHTML = '';
            addMessage('Connecting to server...');
            try {
                await fetch('/start_game', { method: 'POST' });
                addMessage('Connected! Starting game...');
                startPolling();
            } catch (error) { addMessage(`[Fatal Error] Could not connect to server: ${error.message}`); }
        }

        initializeGame();
    </script>
</body>
</html>
"""