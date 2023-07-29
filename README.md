# praktikum_Foodgram_diplom
![](./foodgram-project-react/static/logo.png)
![Django-app workflow](https://github.com/Xaliy/foodgram-project-react/actions/workflows/main.yml/badge.svg)

## Проект «foodgram»
1. [Описание проекта](#описание-проекта)
2. [Ресурсы API](#Ресурсы-API-foodgram)
3. [Как запустить проект локально](#как-запустить-проект-локально)
4. [Как запустить проект локально в контейнерах](#Как-запустить-проект-локально-в-контейнерах)
5. [Как запустить проект на ВМ](#Как-запустить-проект-на-ВМ)
6. [Шаблон наполнения .env](#шаблон-наполнения-env)
7. [Стек технологий](#стек-технологий)
8. [Автор](#автор)

## Описание проекта:
Foodgram (Продуктовый помощник). Дипломный проект.
Проект позволяет сохранять и публиковать рецепты, просматривать рецепты других пользователей,
отмечать предпочтительные рецепты и формировать список покупок из выбранных рецептов.

## Ресурсы API foodgram (основные)
- Ресурс auth: аутентификация.
* ```/api/auth/token/login/``` ```/api/auth/token/logout/``` - (POST) получение/удаление токена
- Ресурс users: пользователи.
```/api/users/{id}``` - (GET) персональная страница пользователя
- Ресурс tags: теги.
```/api/tags/``` - (GET) получение списка всех тегов
- Ресурс ingredients: ингридиенты.
```/api/recipes/``` - (GET) получение списка всех ингредиентов
- Ресурс recipes: рецепты.
```/api/recipes/``` - (GET) получение списка всех рецептов


Каждый ресурс описан в документации: указаны эндпоинты
(адреса, по которым можно сделать запрос),
разрешённые типы запросов,
права доступа и дополнительные параметры.
### Полный список запросов
Все примеры доступны в документации:
```
http://localhost/redoc/
```

## Как запустить проект локально:
1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:Xaliy/foodgram-project-react.git
```
2. Создать и активировать виртуальное окружение:
```
 python3 -m venv venv
```
3. Установить зависимости из файла requirements:
```
pip install -r requirements.txt
``` 
4. Выполнить миграции:
```
python3 manage.py load_tags
backend python manage.py load_ingredients
``` 
5. Запустить проект:
```
python3 manage.py runserver
``` 

## Как запустить проект локально в контейнерах
1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:Xaliy/foodgram-project-react.git
```
```
cd foodgram-project-react/infra
```
2. Развернуть докер контэйнеры:
```
sudo docker-compose up -d --build
```
3. Выполнить миграции
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_tags
docker-compose exec backend python manage.py load_ingredients
```
4. Создать суперпользователя
```
docker-compose exec backend python manage.py createsuperuser
```
5. Загрузить статику
```
docker-compose exec backend python manage.py collectstatic --no-input
```

## Как запустить проект на ВМ:
1. Клонировать репозиторий
```
git clone git@github.com:Xaliy/foodgram-project-react.git
```
2. Подключиться к серверу. Установить на сервере docker и docker-compose.
3. Скопировать на сервер файлы docker-compose.yml и nginx.conf
4. Создать .env файл на сервере и добавить в него настройки .env
5. НА локальном сервере собрать образы
6. Запушить с локального сервера на GitHub сборку
7. После автоматического деплоя на ВМ выполнить миграции, заливки и создать суперпользователя.
```
sudo docker-compose exec -T backend python manage.py makemigrations
sudo docker-compose exec -T backend python manage.py migrate
sudo docker-compose exec -T backend python manage.py collectstatic --no-input
sudo docker-compose exec -T backend python manage.py load_tags
sudo docker-compose exec -T backend python manage.py load_ingredients
sudo docker-compose exec backend python manage.py createsuperuser
```
## Шаблон наполнения .env
- DB_ENGINE # указываем, что работаем с postgresql
- DB_NAME # имя базы данных
- POSTGRES_USER # логин для подключения к базе данных
- POSTGRES_PASSWORD # пароль для подключения к БД (установите свой)
- DB_HOST  # название сервиса (контейнера)
- DB_PORT # порт для подключения к БД

## Стек технологий
- Python Django REST Framework
- библиотека django-filter
- GIT
- SQLite3/PostgreSQL
- Nginx
- Docker

## Автор:
- [Xaliy](https://github.com/Xaliy)
