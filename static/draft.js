document.addEventListener('DOMContentLoaded', () => {
    const setSelect = document.getElementById('set-select');
    const createDraftBtn = document.getElementById('create-draft-btn');
    const sessionList = document.getElementById('session-list');
    const lobby = document.getElementById('lobby');
    const draftRoom = document.getElementById('draft-room');
    const draftRoomTitle = document.getElementById('draft-room-title');
    const playerList = document.getElementById('player-list');
    const startDraftBtn = document.getElementById('start-draft-btn');
    const packDisplay = document.getElementById('pack-display');
    const pickedCardsContainer = document.getElementById('picked-cards');
    const nameInput = document.getElementById('name-input')

    let currentSessionId = null;
    let currentPlayerId = null;
    let isHost = false;
    let sessionStateInterval = null;

    const SessionPollingInterval = 750;

    // Fetch sets for the dropdown
    fetch('/api/v1/sets?only_draftable=true')
        .then(response => response.json())
        .then(data => {
            data.sets.forEach(set => {
                const option = document.createElement('option');
                option.value = set;
                option.textContent = set.toUpperCase();
                setSelect.appendChild(option);
            });
        });

    // Create a new draft
    createDraftBtn.addEventListener('click', () => {
        const setCode = setSelect.value;
        const numPacks = document.getElementById('num-packs-input').value;
        const boosterType = document.getElementById('booster-type-select').value;
        fetch('/api/v1/draft/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ set_code: setCode, num_packs: parseInt(numPacks), booster_type: boosterType, player_name: getPlayerName() })
        })
        .then(response => response.json())
        .then(data => {
            if (data.session_id) {
                currentSessionId = data.session_id;
                currentPlayerId = data.player_id;
                isHost = true;
                showDraftRoom(data.session);
            }
        });
    });

    // Periodically refresh the list of sessions
    setInterval(refreshSessions, SessionPollingInterval);
    refreshSessions();

    function refreshSessions() {
        fetch('/api/v1/draft/sessions')
            .then(response => response.json())
            .then(data => {
                sessionList.innerHTML = '';
                if (data.sessions.length === 0) {
                    sessionList.innerHTML = '<li class="text-gray-600 italic">NO_ACTIVE_SIGNALS_DETECTED</li>';
                    return;
                }
                data.sessions.forEach(session => {
                    const li = document.createElement('li');
                    li.className = 'flex justify-between items-center bg-black/30 p-3 rounded border border-white/5 hover:border-accent/30 transition-colors';
                    li.innerHTML = `
                        <span class="text-gray-300"><span class="text-accent font-bold">${session.set_code.toUpperCase()}</span> // ${session.players.length}/8 OPERATORS</span>
                        <button data-session-id="${session.id}" class="text-xs bg-green-900/30 text-green-400 border border-green-800 px-3 py-1 hover:bg-green-400 hover:text-black transition-colors uppercase">Join_Link</button>
                    `;
                    li.querySelector('button').addEventListener('click', joinDraft);
                    sessionList.appendChild(li);
                });
            });
    }

    function joinDraft(event) {
        const sessionId = event.target.dataset.sessionId;
        fetch(`/api/v1/draft/${sessionId}/join`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: getPlayerName() })
        })
            .then(response => response.json())
            .then(data => {
                if (data.session_id) {
                    currentSessionId = data.session_id;
                    currentPlayerId = data.player_id;
                    isHost = false;
                    showDraftRoom(data.session);
                } else {
                    alert("ERROR: " + data.error);
                }
            });
    }

    function showDraftRoom(session) {
        lobby.style.display = 'none';
        draftRoom.style.display = 'block';
        draftRoomTitle.innerHTML = `DRAFT_SEQUENCE: <span class="text-accent">${session.set_code.toUpperCase()}</span>`;
        updatePlayerList(session.players);
        if (isHost) {
            startDraftBtn.style.display = 'block';
        }
        pollForSessionState();
    }

    function updatePlayerList(players) {
        playerList.innerHTML = '<h3 class="text-accent mb-2">> CONNECTED_OPERATORS:</h3>';
        const ul = document.createElement('ul');
        ul.className = 'flex flex-wrap gap-4';
        players.forEach(player => {
            const li = document.createElement('li');
            li.className = 'bg-white/5 px-3 py-1 rounded text-xs border border-white/5';
            
            let content = player.name;
            if (player.id === currentPlayerId) {
                li.classList.add('border-accent', 'text-accent');
                content += ' (YOU)';
            }
            if (player.is_host) {
                content += ' [HOST]';
            }
            li.textContent = content;
            ul.appendChild(li);
        });
        playerList.appendChild(ul);
    }

    startDraftBtn.addEventListener('click', () => {
        // Just send the start request. The polling will handle UI updates.
        fetch(`/api/v1/draft/${currentSessionId}/start`, { method: 'POST' });
    });

    function pollForSessionState() {
        if (sessionStateInterval) {
            clearInterval(sessionStateInterval);
        }
        sessionStateInterval = setInterval(() => {
            if (!currentSessionId || !currentPlayerId) {
                clearInterval(sessionStateInterval);
                return;
            }
            fetch(`/api/v1/draft/${currentSessionId}/status?player_id=${currentPlayerId}`)
                .then(response => response.json())
                .then(state => {
                    updatePlayerList(state.players);

                    if (state.status === 'lobby') {
                        // Still in lobby, just keep updating player list.
                        // Host can see the start button.
                        if (isHost) {
                            startDraftBtn.style.display = 'block';
                        }
                    } else if (state.status === 'picking') {
                        startDraftBtn.style.display = 'none';
                        displayPack(state.pack);
                        displayPickedCards(state.deck);
                    } else if (state.status === 'waiting') {
                        startDraftBtn.style.display = 'none';
                        packDisplay.innerHTML = '<p class="col-span-full text-center font-mono text-accent animate-pulse py-12">> AWAITING_PEER_INPUT...</p>';
                        displayPickedCards(state.deck);
                    } else if (state.status === 'finished') {
                        clearInterval(sessionStateInterval);
                        startDraftBtn.style.display = 'none';
                        displayDecklist(state.deck);
                    }
                })
                .catch(error => {
                    console.error("Error polling for draft state:", error);
                    clearInterval(sessionStateInterval);
                });
        }, SessionPollingInterval);
    }

    function displayPack(pack) {
        packDisplay.innerHTML = '';
        pack.forEach((card, index) => {
            const cardItem = document.createElement('div');
            cardItem.className = 'card-item glass-panel p-2 rounded border border-white/5 hover:border-accent/50 transition-all cursor-pointer group relative';
            
            const imgWrapper = document.createElement('div');
            imgWrapper.className = 'img-cyberpunk-wrapper rounded overflow-hidden relative';

            const cardImg = document.createElement('img');
            cardImg.src = `/${card.file_name}`;
            cardImg.alt = card.name;
            cardImg.title = card.name;
            cardImg.className = 'img-cyberpunk w-full h-auto';
            cardImg.dataset.cardSafeName = card.safe_name;
            cardImg.addEventListener('click', pickCard);
            
            imgWrapper.appendChild(cardImg);
            cardItem.appendChild(imgWrapper);
            packDisplay.appendChild(cardItem);

            // Animation
            if (window.gsap) {
                gsap.fromTo(cardItem, 
                    { y: 20, opacity: 0 },
                    { y: 0, opacity: 1, duration: 0.5, delay: index * 0.05 }
                );
            }
        });
    }

    function pickCard(event) {
        const cardSafeName = event.target.dataset.cardSafeName;
        // Visually indicate the card has been picked
        document.querySelectorAll('#pack-display .card-item').forEach(item => {
            item.classList.add('picked'); // Add class for grayscale/opacity
            const img = item.querySelector('img');
            if (img) img.removeEventListener('click', pickCard);
        });
        
        // Highlight selected
        const selectedItem = event.target.closest('.card-item');
        selectedItem.classList.remove('picked');
        selectedItem.classList.add('border-accent', 'shadow-[0_0_20px_rgba(0,243,255,0.3)]');

        fetch(`/api/v1/draft/${currentSessionId}/pick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_id: currentPlayerId, card_safe_name: cardSafeName })
        });
    }

    function displayPickedCards(deck) {
        pickedCardsContainer.innerHTML = "";
        if (!deck) {
            return;
        }
        deck.forEach(card => {
            const cardItem = document.createElement('div');
            cardItem.className = 'card-item opacity-80 hover:opacity-100 transition-opacity';
            
            const img = document.createElement('img');
            img.src = `/${card.file_name}`;
            img.alt = card.name;
            img.title = card.name;
            img.className = 'w-full h-auto rounded border border-white/10';
            
            cardItem.appendChild(img);
            pickedCardsContainer.appendChild(cardItem);
        });
    }

    function displayDecklist(deck) {
        draftRoomTitle.textContent = 'FINAL_DECK_MANIFEST';
        packDisplay.style.display = 'none';
        pickedCardsContainer.innerHTML = '';
        
        const listContainer = document.createElement('div');
        listContainer.className = 'font-mono text-sm text-gray-300 space-y-1 mb-6';

        deck.forEach(card => {
            const p = document.createElement('p');
            p.textContent = `1 ${card.name}`;
            listContainer.appendChild(p);
        });
        pickedCardsContainer.appendChild(listContainer);

        const copyButton = document.createElement('button');
        copyButton.textContent = 'Copy_To_Clipboard';
        copyButton.className = 'bg-white text-black font-mono uppercase text-sm px-6 py-3 hover:bg-accent transition-colors font-bold tracking-wider';
        copyButton.addEventListener('click', () => {
            const decklist = deck.map(card => "1 " + card.name).join('\n');
            navigator.clipboard.writeText(decklist).then(() => {
                alert('SUCCESS: DATA_COPIED');
            });
        });
        pickedCardsContainer.appendChild(copyButton);
    }

    function getPlayerName() {

        const animals = ["Panda", "Koala", "Penguin", "Dolphin", "Tiger", "Lion", "Elephant", "Giraffe"];
        const colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink", "White"];
        
        if (nameInput.value.trim().length > 2) {
            return nameInput.value.trim();
        } else {
            const randomAnimal = animals[Math.floor(Math.random() * animals.length)];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            return randomColor + randomAnimal;
        }
    }
});
