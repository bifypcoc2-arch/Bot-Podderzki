const tg = window.Telegram.WebApp;
let currentPage = 'pet';

// Подписанные данные Telegram. Сервер сам достаёт из них user_id,
// поэтому передавать ID вручную больше не нужно и нельзя.
const initData = tg.initData || '';

const RING_PARAMS = ['hunger', 'happiness', 'hygiene', 'energy'];
const BAR_PARAMS = ['discipline', 'strength'];

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

    if (typeof tg.setHeaderColor === 'function') {
        tg.setHeaderColor('#0d0f1a');
    }

    if (!initData) {
        showLoadingMessage('Откройте приложение через Telegram');
        return;
    }

    try {
        await loadPetState();
        await loadStats();
    } catch (error) {
        showLoadingMessage('Ошибка авторизации. Откройте приложение заново из чата с ботом');
        return;
    }

    document.getElementById('loading').hidden = true;
    document.getElementById('content').hidden = false;

    setupNavigation();
    setupActions();
    setInterval(updatePetState, 60000);
});

function showLoadingMessage(text) {
    const loading = document.getElementById('loading');
    loading.innerHTML = '';

    const paragraph = document.createElement('p');
    paragraph.textContent = text;
    loading.appendChild(paragraph);
}

function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.page));
    });
}

function setupActions() {
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => performAction(btn.dataset.action));
    });
}

function switchPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`${page}-page`).classList.add('active');
    document.querySelector(`[data-page="${page}"]`).classList.add('active');

    window.scrollTo(0, 0);
    currentPage = page;

    if (page === 'profile') {
        loadStats().catch(logError);
        loadAchievements().catch(logError);
    } else if (page === 'shop') {
        loadShop().catch(logError);
    } else if (page === 'home') {
        loadInventory().catch(logError);
    }
}

function logError(error) {
    console.error(error);
}

async function loadPetState() {
    const response = await apiFetch('/api/pet');
    const data = await response.json();

    updatePetDisplay(data);
}

function updatePetDisplay(pet) {
    const stage = translateStage(pet.stage);
    const type = pet.pet_type ? translatePetType(pet.pet_type) : null;

    // До стадии «Малыш» вид ещё не выбран, поэтому заголовком служит стадия.
    document.getElementById('pet-name').textContent = type || stage;
    document.getElementById('pet-caption').textContent = type ? stage : 'ещё не проявился';
    document.getElementById('pet-avatar').textContent = getPetEmoji(pet.stage, pet.pet_type);

    RING_PARAMS.forEach(param => updateRing(param, pet[param]));
    BAR_PARAMS.forEach(param => updateBar(param, pet[param]));

    updateExperience(pet);
}

function clamp(value) {
    const number = Number(value) || 0;
    return Math.max(0, Math.min(100, number));
}

function updateRing(param, value) {
    const ring = document.getElementById(`ring-${param}`);
    const percent = clamp(value);

    ring.style.setProperty('--value', percent);
    ring.classList.toggle('is-low', percent < 30);
    document.getElementById(`${param}-value`).textContent = percent;
}

function updateBar(param, value) {
    const percent = clamp(value);

    document.getElementById(`bar-${param}`).style.width = `${percent}%`;
    document.getElementById(`${param}-value`).textContent = percent;
}

function updateExperience(pet) {
    const xp = Number(pet.xp) || 0;
    const target = pet.next_stage_xp;
    const fill = document.getElementById('xp-fill');
    const title = document.getElementById('xp-title');
    const numbers = document.getElementById('xp-numbers');
    const note = document.getElementById('growth-note');

    if (target) {
        const percent = Math.max(0, Math.min(100, Math.round((xp / target) * 100)));
        title.textContent = 'Опыт до следующей стадии';
        numbers.textContent = `${xp} / ${target} XP`;
        fill.style.width = `${percent}%`;
    } else {
        title.textContent = 'Максимальная стадия';
        numbers.textContent = `${xp} XP`;
        fill.style.width = '100%';
    }

    // Опыта мало: стадия не растёт, пока все параметры не выше порога.
    if (!target) {
        note.textContent = '';
    } else if (pet.growth_ready) {
        note.textContent = 'Уход в порядке — питомец растёт.';
    } else {
        const minimum = pet.growth_param_minimum || 60;
        note.textContent = `Для роста все параметры должны быть не ниже ${minimum}.`;
    }
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
            if (tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }
            await loadPetState();
        } else {
            tg.showAlert(result.message || 'Действие недоступно');
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

    const fields = {
        'currency': stats.currency,
        'login-streak': stats.login_streak,
        'stat-messages': stats.messages_sent,
        'stat-login-streak': stats.login_streak,
        'stat-games': stats.games_played,
        'stat-wins': stats.games_won,
        'stat-streak': stats.win_streak,
        'stat-feedings': stats.feedings,
        'stat-baths': stats.baths,
        'stat-sleeps': stats.sleeps,
        'stat-trainings': stats.trainings
    };

    Object.keys(fields).forEach(id => {
        document.getElementById(id).textContent = fields[id] ?? 0;
    });
}

function describeItem(item) {
    const parts = [];

    if (item.type) {
        parts.push(translateItemType(item.type));
    }

    if (item.effect_type && item.effect_value) {
        parts.push(`+${item.effect_value} к характеристике «${item.effect_type}»`);
    }

    return parts.join(' · ');
}

function translateItemType(type) {
    const types = {
        food: 'Еда',
        toy: 'Игрушка',
        accessory: 'Аксессуар',
        background: 'Фон',
        decoration: 'Декор'
    };
    return types[type] || type;
}

async function loadShop() {
    const response = await apiFetch('/api/shop');
    const data = await response.json();

    const container = document.getElementById('shop-items');
    container.innerHTML = '';

    document.getElementById('shop-empty').hidden = data.items.length > 0;

    data.items.forEach(item => {
        const card = document.createElement('article');
        card.className = 'shop-card';

        const name = document.createElement('h3');
        name.textContent = item.name;

        const description = document.createElement('p');
        description.textContent = describeItem(item);

        const price = document.createElement('button');
        price.className = 'price-btn';
        price.textContent = `◆ ${item.price}`;
        price.addEventListener('click', () => buyItem(item.id, item.name));

        card.append(name, description, price);
        container.appendChild(card);
    });
}

async function loadInventory() {
    const response = await apiFetch('/api/inventory');
    const data = await response.json();

    const container = document.getElementById('home-items');
    container.innerHTML = '';

    document.getElementById('home-empty').hidden = data.items.length > 0;

    data.items.forEach(item => {
        const card = document.createElement('article');
        card.className = 'shop-card';

        const name = document.createElement('h3');
        name.textContent = item.name;

        const description = document.createElement('p');
        const details = [translateItemType(item.type)];
        if (item.quantity > 1) {
            details.push(`${item.quantity} шт.`);
        }
        if (item.is_equipped) {
            details.push('надето');
        }
        description.textContent = details.join(' · ');

        card.append(name, description);
        container.appendChild(card);
    });
}

async function loadAchievements() {
    const response = await apiFetch('/api/achievements');
    const data = await response.json();

    const container = document.getElementById('achievements-list');
    container.innerHTML = '';

    document.getElementById('achievements-empty').hidden = data.achievements.length > 0;

    data.achievements.forEach(achievement => {
        const card = document.createElement('article');
        card.className = 'card';

        const body = document.createElement('div');
        body.className = 'card-body';

        const name = document.createElement('h3');
        name.textContent = achievement.name;

        const description = document.createElement('p');
        description.textContent = achievement.description || '';

        body.append(name, description);
        card.appendChild(body);
        container.appendChild(card);
    });
}

async function buyItem(itemId, itemName) {
    tg.showConfirm(`Купить «${itemName}»?`, async (confirmed) => {
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
