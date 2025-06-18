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
            body: JSON.stringify({ set_code: setCode, num_packs: parseInt(numPacks), booster_type: boosterType })
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
                data.sessions.forEach(session => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <span>${session.set_code.toUpperCase()} (${session.players.length}/8 players)</span>
                        <button data-session-id="${session.id}">Join</button>
                    `;
                    li.querySelector('button').addEventListener('click', joinDraft);
                    sessionList.appendChild(li);
                });
            });
    }

    function joinDraft(event) {
        const sessionId = event.target.dataset.sessionId;
        fetch(`/api/v1/draft/${sessionId}/join`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.session_id) {
                    currentSessionId = data.session_id;
                    currentPlayerId = data.player_id;
                    isHost = false;
                    showDraftRoom(data.session);
                } else {
                    alert(data.error);
                }
            });
    }

    function showDraftRoom(session) {
        lobby.style.display = 'none';
        draftRoom.style.display = 'block';
        draftRoomTitle.textContent = `Drafting: ${session.set_code.toUpperCase()}`;
        updatePlayerList(session.players);
        if (isHost) {
            startDraftBtn.style.display = 'block';
        }
        pollForSessionState();
    }

    function updatePlayerList(players) {
        playerList.innerHTML = '<h3>Players:</h3>';
        const ul = document.createElement('ul');
        players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = `Player ${player.id}`;
            if (player.id === currentPlayerId) {
                li.textContent += ' (You)';
            }
            if (player.is_host) {
                li.textContent += ' (Host)';
            }
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
                        packDisplay.innerHTML = '<p>Waiting for other players to pick...</p>';
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
        pack.forEach(card => {
            const cardItem = document.createElement('div');
            cardItem.className = 'card-item';
            const cardImg = document.createElement('img');
            cardImg.src = `/${card.file_name}`;
            cardImg.alt = card.name;
            cardImg.title = card.name;
            cardImg.dataset.cardSafeName = card.safe_name;
            cardImg.addEventListener('click', pickCard);
            cardItem.appendChild(cardImg);
            packDisplay.appendChild(cardItem);
        });
    }

    function pickCard(event) {
        const cardSafeName = event.target.dataset.cardSafeName;
        // Visually indicate the card has been picked
        document.querySelectorAll('#pack-display .card-item img').forEach(img => {
            img.parentElement.classList.add('picked');
            img.removeEventListener('click', pickCard);
        });
        event.target.style.border = '3px solid lightgreen';

        fetch(`/api/v1/draft/${currentSessionId}/pick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_id: currentPlayerId, card_safe_name: cardSafeName })
        });
    }

    function displayPickedCards(deck) {
        pickedCardsContainer.innerHTML = "";
        console.log("Displaying picked cards:", deck);
        if (!deck) {
            return;
        }
        deck.forEach(card => {
            const cardItem = document.createElement('div');
            cardItem.className = 'card-item';
            const cardImg = document.createElement('img');
            cardImg.src = `/${card.file_name}`;
            cardImg.alt = card.name;
            cardImg.title = card.name;
            cardItem.appendChild(cardImg);
            pickedCardsContainer.appendChild(cardItem);
        });
    }

    function displayDecklist(deck) {
        draftRoomTitle.textContent = 'Your Decklist';
        packDisplay.style.display = 'none';
        pickedCardsContainer.innerHTML = '';
        deck.forEach(card => {
            const p = document.createElement('p');
            p.textContent = card.name;
            pickedCardsContainer.appendChild(p);
        });
        const copyButton = document.createElement('button');
        copyButton.textContent = 'Copy Decklist to Clipboard';
        copyButton.addEventListener('click', () => {
            const decklist = deck.map(card => "1 " + card.name).join('\n');
            navigator.clipboard.writeText(decklist).then(() => {
                alert('Decklist copied to clipboard!');
            });
        });
        pickedCardsContainer.appendChild(copyButton);
    }
});
