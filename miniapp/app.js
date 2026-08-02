const tg = window.Telegram.WebApp;
let userId = null;
let currentPage = 'pet';

document.addEventListener('DOMContentLoaded', async () => {
    tg.ready();
    tg.expand();

    userId = tg.initDataUnsafe?.user?.id;

    if (!userId) {
        console.error('User ID not found');
        document.getElementById('loading').textContent = 'Ошибка: не удалось получить данные пользователя';
        return;
    }

    await loadPetState();
    await loadStats();

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
    try {
        const response = await fetch(`/api/pet?user_id=${userId}`);
        const data = await response.json();

        updatePetDisplay(data);
    } catch (error) {
        console.error('Error loading pet state:', error);
        tg.showAlert('Ошибка загрузки данных питомца');
    }
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
        const response = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, action })
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
        tg.showAlert('Ошибка выполнения действия');
    }
}

async function loadStats() {
    try {
        const response = await fetch(`/api/stats?user_id=${userId}`);
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
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadShop() {
    try {
        const response = await fetch('/api/shop');
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
        if (confirmed) {
            tg.showAlert('Функция покупки будет реализована');
        }
    });
}

async function updatePetState() {
    if (currentPage === 'pet') {
        await loadPetState();
    }
}
