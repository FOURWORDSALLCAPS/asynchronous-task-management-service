# asynchronous-task-management-service

[toc]

Сервис для асинхронной обработки задач с возможностью масштабирования и отказоустойчивости

## Как развернуть local-окружение

### Необходимое ПО

Для запуска понадобятся Make и Docker

- [GNU Make](https://www.gnu.org/software/make/)
- [Get Started with Docker](https://www.docker.com/get-started/)

### Переменные окружения

Создайте .env файл по образцу
```shell
cd src
cp example.env .env
```

Необходимые параметры находятся в `src/setting.py`

### Pre-commit

Запустите команду для настройки хуков
```shell
pre-commit install
```

### Сборка проекта

Скачайте и соберите докер-образы
```shell
make update
```

### Запуск
```shell
make start
```

### Остановка
```shell
make stop
```

### Миграции

Накатить миграции можно с помощью alembic. Проект должен быть запущен!

```shell
make migrations
make migrate
```

## Как пользоваться

### Make файл

Набор доступных команд `make` [Makefile](Makefile)
```shell
make help
Cписок доступных команд:
stop                         Останавливает докер-сервисы
start                        Запускает докер-сервисы
update                       Обновляет докер-сервисы
migrations                   Накатывает миграции
migrate                      Применяет миграции
help                         Отображает список доступных команд и их описания
```
