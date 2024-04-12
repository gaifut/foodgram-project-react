# praktikum_new_diplom

**Домен**:
https://foooodgram.ddns.net

Описание проекта:
Foodgram - это веб-приложение, предоставляющее пользователям платформу для обмена рецептами. Пользователи могут делиться своими кулинарными шедеврами, добавлять понравившиеся рецепты в избранное и подписываться на авторов для получения обновлений. Кроме того, в приложении доступен сервис "Список покупок", который поможет упростить планирование покупок продуктов для приготовления блюд. Проект развернут в контейнерах Docker, с автоматическим тестированием и развертыванием на виртуальном сервере с Ubuntu через Github Actions. Важно отметить, что сайт обеспечивает безопасное соединение с использованием протокола HTTPS, обеспечивая конфиденциальность пользовательских данных.

**Как развернуть в докере**:
1. Скачать docker на сервер, если его нет. Инструкции: https://docs.docker.com/get-docker/

2. Перейти на старницу https://hub.docker.com/u/gaifut и скачать:
- gaifut/foodgram_frontend
- gaifut/foodgram_backend
- gaifut/foodgram_nginx

Необходимо кликнуть на название, в открывшемся окне будет доступна ссылка на pull.

3. Скачать файл docker-compose.production.yml c https://github.com/gaifut
Репозиторий - foodgram.

4. Создать .env файл со сделующей информацией:                                                       
TOKEN= указать секретный токен 
DEBUG=выбрать True или False и указать
ALLOWED_HOSTS= ip сервера,127.0.0.1,localhost,домен сайта
POSTGRES_USER= логин
POSTGRES_PASSWORD= пароль
POSTGRES_DB= имя БД
DB_HOST= название хоста
DB_PORT=5432

5. Прописать для заполнения БД:
```
sudo docker exec имя_контейнера python manage.py migrate
sudo docker exec имя_контейнера python manage.py csv_to_db
sudo docker exec имя_контейнера python manage.py collectstatic --no-input
```

6. Зайти в контейнер с БД:
sudo docker exec it имя_контейнера psql -U имя_пользователя -d имя_БД
в открывшемся терминале прописать
```
INSERT INTO recipes_tag VALUES (1,'завтрак', '008000', 'breakfast');
INSERT INTO recipes_tag VALUES (2,'обед', 'FF0000', 'lunch');
INSERT INTO recipes_tag VALUES (3,'ужин', '0000FF', 'dinner');
```

7. Выполнить команду sudo docker compose up.

**Стек технологий:**
- Django and Django REST Framework
- Docker
- GithubActions
- Gunicorn
- Nginx
- PostgreSQL
- Python

**Как открыть доку:**
После скачивания репозиория foodgram с гитхаб доступно в нем и по адресу:
http://localhost/api/docs/redoc.html

**Пример запросов и ответов:**
*Список пользователей*
Запрос списка пользователей, может производиться как зарегистрированным пользователем, так и анонимным.
Тип запроса: GET.
Можно задать параметры запроса (query parameters): page(целое число - номер страницы) и limit(целое число - кол-во объектов на странице).
URL:
```
http://localhost/api/users/
```

Пример ответа на запрос:
```
{
  "count": 123,
  "next": "http://foodgram.example.org/api/users/?page=4",
  "previous": "http://foodgram.example.org/api/users/?page=2",
  "results": [
    {
      "email": "user@example.com",
      "id": 0,
      "username": "string",
      "first_name": "Вася",
      "last_name": "Пупкин",
      "is_subscribed": false
    }
  ]
}
```

*Создание рецепта*
Доступно только авторизованному пользователю.
Тип запроса: POST

URL:
```
http://localhost/api/recipes/
```

В запросе указываются:
ingredients (Array of objects) Список ингредиентов
tags (Array of integers) Список id тегов
image (string <binary> ) Картинка, закодированная в Base64
name (string <= 200 characters ) Название
text (string) Описание
cooking_time (integer >= 1 ) Время приготовления (в минутах)

Пример запроса:
```
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

Пример ответа:
```
{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "color": "#E26C2D",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "string",
    "first_name": "Вася",
    "last_name": "Пупкин",
    "is_subscribed": false
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
  "text": "string",
  "cooking_time": 1
}
```

*Добавить рецепт в список покупок*
Доступно только авторизованным пользователям.
Тип запроса: POST.

URL:
```
http://localhost/api/recipes/{id}/shopping_cart/
```

Обязательный path parameter: id (string) - уникальный идентификатор рецепта.

Пример ответа:
```
{
  "id": 0,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
  "cooking_time": 1
}
```

**Автор проекта:**
Гайфутдинов Артур
