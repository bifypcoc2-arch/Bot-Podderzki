const tg = window.Telegram.WebApp;
let currentPage = 'pet';

// Подписанные данные Telegram. Сервер сам достаёт из них user_id,
// поэтому передавать ID вручную больше не нужно и нельзя.
const initData = tg.initData || '';

async function apiFetch(url, options = {}) {
    const headers = Object.assign(
        { 'X-Telegram-Init-Data': initData },
        options.headers || {}
    );

    const response = await fetch(url, Object.assign({}, options, { headers }));

    if (response.status === 401) {
        throw new Error('unauthorized');
    }

    return response;
}

document.addEventListener('DOMContentLoaded', async () => {
    tg.ready();
    tg.expand();

    if (!initData) {
        document.getElementById('loading').textContent =
            'Откройте приложение через Telegram';
        return;
    }

    try {
        await loadPetState();
        await loadStats();
    } catch (error) {
        document.getElementById('loading').textContent =
            'Ошибка авторизации. Откройте приложение заново из чата с ботом';
        return;
    }

    document.getElementById('loading').style.display = 'none';
    document.getElementById('content').style.display = 'block';

    setupNavigation();
    setInterval(updatePetState, 60000);
});

function setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`${page}-page`).classList.add('active');
    document.querySelector(`[data-page="${page}"]`).classList.add('active');

    currentPage = page;

    if (page === 'profile') {
        loadStats();
    } else if (page === 'shop') {
        loadShop();
    }
}

async function loadPetState() {
    const response = await apiFetch('/api/pet');
    const data = await response.json();

    updatePetDisplay(data);
}

function updatePetDisplay(pet) {
    document.getElementById('pet-stage').textContent = translateStage(pet.stage);
    document.getElementById('pet-type').textContent = pet.pet_type ? translatePetType(pet.pet_type) : 'Неизвестно';
    document.getElementById('pet-xp').textContent = pet.xp;

    document.getElementById('pet-avatar').textContent = getPetEmoji(pet.stage, pet.pet_type);

    updateParameter('hunger', pet.hunger);
    updateParameter('happiness', pet.happiness);
    updateParameter('hygiene', pet.hygiene);
    updateParameter('energy', pet.energy);
    updateParameter('discipline', pet.discipline);
    updateParameter('strength', pet.strength);
}

function updateParameter(param, value) {
    document.getElementById(param).value = value;
    document.getElementById(`${param}-value`).textContent = value;
}

function getPetEmoji(stage, type) {
    if (stage === 'conception') return '✨';
    if (stage === 'egg') return '🥚';

    const emojis = {
        cat: '🐱',
        dog: '🐶',
        fox: '🦊',
        panda: '🐼',
        rabbit: '🐰',
        hedgehog: '🦔',
        penguin: '🐧'
    };

    return emojis[type] || '🐾';
}

function translateStage(stage) {
    const stages = {
        conception: 'Зарождение',
        egg: 'Яйцо',
        baby: 'Малыш',
        teen: 'Подросток',
        adult: 'Взрослый'
    };
    return stages[stage] || stage;
}

function translatePetType(type) {
    const types = {
        cat: 'Кошка',
        dog: 'Собака',
        fox: 'Лиса',
        panda: 'Панда',
        rabbit: 'Кролик',
        hedgehog: 'Ёжик',
        penguin: 'Пингвин'
    };
    return types[type] || type;
}

async function performAction(action) {
    try {
        const response = await apiFetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });

        const result = await response.json();

        if (result.success) {
            tg.showAlert('✅ Действие выполнено!');
            await loadPetState();
        } else {
            tg.showAlert('❌ ' + result.message);
        }
    } catch (error) {
        console.error('Error performing action:', error);

        if (error.message === 'unauthorized') {
            tg.showAlert('Сессия устарела. Откройте приложение заново из чата с ботом');
        } else {
            tg.showAlert('Ошибка выполнения действия');
        }
    }
}

async function loadStats() {
    const response = await apiFetch('/api/stats');
    const stats = await response.json();

    document.getElementById('stat-messages').textContent = stats.messages_sent;
    document.getElementById('stat-games').textContent = stats.games_played;
    document.getElementById('stat-wins').textContent = stats.games_won;
    document.getElementById('stat-streak').textContent = stats.win_streak;
    document.getElementById('stat-feedings').textContent = stats.feedings;
    document.getElementById('stat-baths').textContent = stats.baths;
    document.getElementById('stat-sleeps').textContent = stats.sleeps;
    document.getElementById('stat-trainings').textContent = stats.trainings;
    document.getElementById('currency').textContent = stats.currency;
}

async function loadShop() {
    try {
        const response = await apiFetch('/api/shop');
        const data = await response.json();

        const shopContainer = document.getElementById('shop-items');
        shopContainer.innerHTML = '';

        data.items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'shop-item';
            itemDiv.innerHTML = `
                <h3>${item.name}</h3>
                <p>Цена: ${item.price} монет</p>
                <button onclick="buyItem(${item.id})">Купить</button>
            `;
            shopContainer.appendChild(itemDiv);
        });
    } catch (error) {
        console.error('Error loading shop:', error);
    }
}

async function buyItem(itemId) {
    tg.showConfirm('Купить этот предмет?', async (confirmed) => {
        if (!confirmed) {
            return;
        }

        try {
            const response = await apiFetch('/api/shop/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId })
            });

            const result = await response.json();

            if (result.success) {
                tg.showAlert('✅ Покупка совершена!');
                await loadStats();
            } else {
                tg.showAlert('❌ ' + result.message);
            }
        } catch (error) {
            console.error('Error buying item:', error);
            tg.showAlert('Ошибка покупки');
        }
    });
}

async function updatePetState() {
    if (currentPage !== 'pet') {
        return;
    }

    try {
        await loadPetState();
    } catch (error) {
        console.error('Error updating pet state:', error);
    }
}
