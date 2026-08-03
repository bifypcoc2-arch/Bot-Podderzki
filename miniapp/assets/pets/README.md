# Картинки питомцев

Сюда складываются SVG питомцев для мини-приложения.

## Формат

- SVG, квадрат, `viewBox="0 0 512 512"`, без фона.
- Перед добавлением прогонять через svgo, иначе файлы весят в пять раз больше
  без видимой разницы: `npx svgo --multipass --precision=0 -f . -o .`

## Именование

Имя файла — вид питомца из `PetType` в `database/models.py`:

```
cat.svg  dog.svg  fox.svg  panda.svg  rabbit.svg  hedgehog.svg  penguin.svg
```

Если у вида появятся отдельные стадии — подпапка на вид:

```
fox/baby.svg  fox/teen.svg  fox/adult.svg
```

Стадии `conception` и `egg` общие для всех видов: `conception.svg`, `egg.svg`.

## Как подключать

В `miniapp/app.js` сейчас рисуются эмодзи (`getPetEmoji`). Когда пак будет полным,
эмодзи остаются запасным вариантом на случай, если картинка не загрузилась.
