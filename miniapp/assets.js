// Слой иллюстраций.
//
// Разметка и логика живут без картинок: в index.html и app.js остаются
// символы и эмодзи, а этот файл поверх подставляет SVG из assets/.
// Так мини-приложение остаётся рабочим даже если пак картинок ещё не
// выложен или один файл потерялся: при ошибке загрузки возвращается
// исходный символ.

(function () {
    'use strict';

    var BASE = 'assets/';

    var NAV_ICONS = {
        pet: 'ui/avatar',
        games: 'nav/games',
        home: 'nav/home',
        shop: 'nav/shop',
        profile: 'nav/profile'
    };

    var ACTION_ICONS = {
        feed: 'actions/feed',
        play: 'actions/play',
        wash: 'actions/wash',
        sleep: 'actions/sleep',
        train: 'actions/train'
    };

    var RING_ICONS = {
        'ring-hunger': 'stats/hunger',
        'ring-happiness': 'stats/mood',
        'ring-hygiene': 'stats/clean',
        'ring-energy': 'stats/energy'
    };

    var GAME_ICONS = {
        'Кости духов': 'games/dice',
        'Шёпот цифр': 'games/numbers',
        'Слово из тумана': 'games/wordle'
    };

    // app.js ставит в #pet-avatar эмодзи, по нему и узнаём вид питомца.
    var PET_BY_EMOJI = {
        '🐱': 'cat',
        '🐶': 'dog',
        '🦊': 'fox',
        '🐼': 'panda',
        '🐰': 'rabbit',
        '🦔': 'hedgehog',
        '🐧': 'penguin'
    };

    // Имён товаров и достижений в базе много и они меняются, поэтому
    // картинка подбирается по корню слова, а не по точному совпадению.
    var ITEM_KEYWORDS = [
        ['миск', 'shop/bowl'],
        ['корм', 'shop/bowl'],
        ['кекс', 'shop/cupcake'],
        ['пирож', 'shop/cupcake'],
        ['торт', 'shop/cupcake'],
        ['зель', 'shop/potion'],
        ['эликсир', 'shop/potion'],
        ['насто', 'shop/potion'],
        ['суп', 'shop/soup'],
        ['похлеб', 'shop/soup'],
        ['ягод', 'shop/berries'],
        ['черник', 'shop/berries'],
        ['мяс', 'shop/meat'],
        ['косточк', 'shop/meat'],
        ['ловец', 'shop/dreamcatcher'],
        ['сновид', 'shop/dreamcatcher'],
        ['клубок', 'shop/yarn'],
        ['пряж', 'shop/yarn'],
        ['волч', 'shop/spinner'],
        ['юл', 'shop/spinner'],
        ['мыш', 'shop/mouse'],
        ['мяч', 'shop/ball'],
        ['шар', 'shop/ball']
    ];

    var ITEM_TYPE_ICONS = {
        'еда': 'shop/bowl',
        'игрушка': 'shop/ball',
        'аксессуар': 'achievements/chest',
        'фон': 'achievements/crystal',
        'декор': 'achievements/crystal'
    };

    var ACHIEVEMENT_KEYWORDS = [
        ['перв', 'achievements/sprout'],
        ['рост', 'achievements/sprout'],
        ['вырос', 'achievements/sprout'],
        ['корм', 'actions/feed'],
        ['сыт', 'actions/feed'],
        ['купа', 'achievements/brush'],
        ['чист', 'achievements/brush'],
        ['сон', 'achievements/sleep-mask'],
        ['сп', 'achievements/sleep-mask'],
        ['трен', 'actions/train'],
        ['сил', 'actions/train'],
        ['кост', 'achievements/dice'],
        ['игр', 'achievements/dice'],
        ['побед', 'achievements/crown'],
        ['чемпион', 'achievements/crown'],
        ['сери', 'achievements/infinity'],
        ['дней', 'achievements/infinity'],
        ['слов', 'achievements/book'],
        ['друж', 'achievements/friendship'],
        ['забот', 'achievements/care'],
        ['сердц', 'achievements/heart'],
        ['люб', 'achievements/heart'],
        ['звезд', 'achievements/star'],
        ['монет', 'achievements/bag'],
        ['богат', 'achievements/chest'],
        ['тайн', 'achievements/crystal'],
        ['загад', 'achievements/crystal'],
        ['защит', 'achievements/shield']
    ];

    var STYLE = [
        '.asset-icon{display:block;width:100%;height:100%;object-fit:contain;pointer-events:none}',
        '.nav-icon.has-asset,.action-icon.has-asset{display:flex;align-items:center;justify-content:center}',
        '.nav-icon.has-asset{width:26px;height:26px}',
        '.action-icon.has-asset{width:34px;height:34px}',
        '.ring-icon{position:absolute;top:6px;left:50%;transform:translateX(-50%);width:18px;height:18px;opacity:.9}',
        '.badge-icon{width:16px;height:16px;vertical-align:-3px;margin-right:4px}',
        '.meter-icon{width:18px;height:18px;flex:none;margin-right:6px;vertical-align:-4px}',
        '.game-icon{width:28px;height:28px;vertical-align:-6px;margin-right:8px}',
        '.card-icon{width:44px;height:44px;flex:none;margin-right:10px}',
        '.shop-card{position:relative}',
        '.shop-card .card-icon{float:left}',
        '#pet-avatar .asset-icon{width:100%;height:100%;filter:drop-shadow(0 12px 24px rgba(10,12,24,.55))}',
        '#pet-avatar.has-asset{font-size:0}'
    ].join('');

    function injectStyle() {
        var style = document.createElement('style');
        style.id = 'asset-style';
        style.textContent = STYLE;
        document.head.appendChild(style);
    }

    // При ошибке загрузки возвращаем текст, который был в элементе.
    function buildIcon(name, alt, className) {
        var image = document.createElement('img');
        image.className = 'asset-icon' + (className ? ' ' + className : '');
        image.src = BASE + name + '.svg';
        image.alt = alt || '';
        image.loading = 'lazy';
        image.draggable = false;
        return image;
    }

    function replaceContent(element, name, alt) {
        if (!element || element.dataset.assetApplied === name) {
            return;
        }

        var fallback = element.textContent;
        var image = buildIcon(name, alt);

        image.addEventListener('error', function () {
            element.classList.remove('has-asset');
            element.dataset.assetApplied = '';
            element.textContent = fallback;
        });

        element.textContent = '';
        element.appendChild(image);
        element.classList.add('has-asset');
        element.dataset.assetApplied = name;
    }

    function prependIcon(element, name, alt, className) {
        if (!element || element.querySelector('.asset-icon')) {
            return;
        }

        var image = buildIcon(name, alt, className || 'card-icon');

        image.addEventListener('error', function () {
            if (image.parentNode) {
                image.parentNode.removeChild(image);
            }
        });

        element.insertBefore(image, element.firstChild);
    }

    function matchKeyword(text, table) {
        var lower = (text || '').toLowerCase();

        for (var index = 0; index < table.length; index += 1) {
            if (lower.indexOf(table[index][0]) !== -1) {
                return table[index][1];
            }
        }

        return null;
    }

    function applyStaticIcons() {
        document.querySelectorAll('.nav-btn').forEach(function (button) {
            var name = NAV_ICONS[button.dataset.page];
            var icon = button.querySelector('.nav-icon');
            var label = button.querySelector('.nav-text');

            if (name && icon) {
                replaceContent(icon, name, label ? label.textContent : '');
            }
        });

        document.querySelectorAll('.action-btn').forEach(function (button) {
            var name = ACTION_ICONS[button.dataset.action];
            var icon = button.querySelector('.action-icon');
            var label = button.querySelector('.action-text');

            if (name && icon) {
                replaceContent(icon, name, label ? label.textContent : '');
            }
        });

        Object.keys(RING_ICONS).forEach(function (id) {
            var ring = document.getElementById(id);

            if (!ring || ring.querySelector('.ring-icon')) {
                return;
            }

            var label = ring.querySelector('.ring-label');
            prependIcon(ring, RING_ICONS[id], label ? label.textContent : '', 'ring-icon');
        });

        document.querySelectorAll('.meter').forEach(function (meter) {
            var name = meter.querySelector('.meter-name');

            if (!name) {
                return;
            }

            var icon = name.textContent.indexOf('Лапк') !== -1
                ? 'stats/paws'
                : 'achievements/shield';

            prependIcon(name, icon, '', 'meter-icon');
        });

        document.querySelectorAll('.badge').forEach(function (badge) {
            var title = badge.getAttribute('title') || '';
            var icon = title.indexOf('Серия') !== -1 ? 'stats/xp' : 'stats/paws';

            prependIcon(badge, icon, title, 'badge-icon');
        });

        var xpHead = document.querySelector('.xp-head');

        if (xpHead) {
            prependIcon(xpHead, 'stats/xp', '', 'badge-icon');
        }

        document.querySelectorAll('.game-card h3').forEach(function (heading) {
            var name = GAME_ICONS[heading.textContent.trim()];

            if (name) {
                prependIcon(heading, name, '', 'game-icon');
            }
        });
    }

    function applyPetAvatar() {
        var avatar = document.getElementById('pet-avatar');

        if (!avatar) {
            return;
        }

        var existing = avatar.querySelector('.asset-icon');
        var emoji = existing ? '' : avatar.textContent.trim();
        var type = PET_BY_EMOJI[emoji];

        if (!type) {
            return;
        }

        replaceContent(avatar, 'pets/' + type, 'Питомец');
    }

    function applyCardIcons(container, table, fallback) {
        if (!container) {
            return;
        }

        container.querySelectorAll('h3').forEach(function (heading) {
            var card = heading.closest('article') || heading.parentNode;

            if (!card || card.querySelector('.card-icon')) {
                return;
            }

            var description = card.querySelector('p');
            var byName = matchKeyword(heading.textContent, table);
            var byType = null;

            if (!byName && description) {
                var typeText = description.textContent.split('·')[0].trim().toLowerCase();
                byType = ITEM_TYPE_ICONS[typeText] || null;
            }

            prependIcon(card, byName || byType || fallback, '', 'card-icon');
        });
    }

    function applyDynamicIcons() {
        applyPetAvatar();
        applyCardIcons(document.getElementById('shop-items'), ITEM_KEYWORDS, 'achievements/chest');
        applyCardIcons(document.getElementById('home-items'), ITEM_KEYWORDS, 'achievements/chest');
        applyCardIcons(document.getElementById('achievements-list'), ACHIEVEMENT_KEYWORDS, 'achievements/star');
    }

    function watch() {
        var observer = new MutationObserver(function () {
            applyDynamicIcons();
        });

        ['pet-avatar', 'shop-items', 'home-items', 'achievements-list'].forEach(function (id) {
            var target = document.getElementById(id);

            if (target) {
                observer.observe(target, { childList: true, characterData: true, subtree: true });
            }
        });
    }

    function start() {
        injectStyle();
        applyStaticIcons();
        applyDynamicIcons();
        watch();
    }

    // app.js раскрывает #content после загрузки данных, поэтому ждём
    // полного разбора разметки, а динамические карточки ловим наблюдателем.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
