A modular and scalable Telegram bot with its own database. It allows administrators to manage contest regulations (upload, view, delete) and provides AI integration to explain selected contest rules.

Features:

Modular and maintainable code structure

Configurable database for contests and departments

AI-powered explanations of contest regulations

Admin panel: upload, view, delete contests, add departments

Secure handling of API keys using .env

Requirements:

Python 3.10+

Libraries: aiogram, python-dotenv, PyMuPDF (for PDF previews), etc.

Usage:

Create a .env file with your tokens and keys.

Run the bot: python main.py

Admins can manage contests and departments; users can ask questions and get AI explanations.

Developer Notes:

Code is split into modules: bot, handlers, database, config

FSM (Finite State Machine) handles contest upload and department selection

Inline keyboards and reply keyboards are modular for easy extension

Adding new AI functionality or contest types is straightforward

Logging is implemented via logs/actions.log for actions and errors


his bot is designed to be modular and scalable, so contributions are welcome. Here’s how to work with it:

Fork the repository and clone it locally.

Setup environment:

Copy .env.example to .env and fill in your keys

Install dependencies: pip install -r requirements.txt

Understand the structure:

bot.py – main bot launcher

handlers/ – modular handlers for contests, departments, AI

database.py – database operations

config.py – configuration and environment variables

logs/ – log files for debugging and action tracking

Adding new features:

Create new modules in handlers/ or extend FSM states

Use inline keyboards and reply keyboards for interactions

Keep code modular; avoid putting everything in a single file

Testing:

Run the bot locally and use a test Telegram account

Ensure all FSM flows work correctly before pushing changes

Pull Requests:

Write clear commit messages

Describe your changes in the PR

Make sure no API keys are committed

Tips:

Always use state and FSMContext for multi-step user interactions

Keep AI-related code separate for easy upgrades

Follow existing logging patterns to track errors and actions


Бот-помощник по конкурсам

Модульный и масштабируемый Telegram-бот с собственной базой данных. Позволяет администраторам управлять положениями конкурсов (загрузка, просмотр, удаление) и предоставляет интеграцию с ИИ для объяснения выбранных положений.

Возможности:

Модульный и поддерживаемый код

Настраиваемая база данных конкурсов и отделов

Объяснения положений конкурсов с помощью ИИ

Панель администратора: загрузка, просмотр, удаление конкурсов, добавление отделов

Безопасная работа с API-ключами через .env

Требования:

Python 3.10+

Библиотеки: aiogram, python-dotenv, PyMuPDF и др.

Использование:

Создать .env с токенами и ключами.

Запустить бота: python main.py

Администраторы управляют конкурсами и отделами; пользователи задают вопросы и получают объяснения от ИИ.

Для разработчиков:

Код разделён на модули: bot, handlers, database, config

FSM (конечный автомат состояний) управляет загрузкой конкурсов и выбором отделов

Инлайн-клавиатуры и обычные клавиатуры реализованы модульно для лёгкого расширения

Добавление новых функций ИИ или типов конкурсов — простое

Логирование действий и ошибок ведётся в logs/actions.log

Вклад в проект

Бот сделан модульным и масштабируемым, поэтому вклад приветствуется. Вот как с ним работать:

Сделайте fork репозитория и клонируйте его локально.

Настройте окружение:

Скопируйте .env.example в .env и заполните ключи

Установите зависимости: pip install -r requirements.txt

Разберите структуру проекта:

bot.py – основной файл запуска бота

handlers/ – модульные обработчики конкурсов, отделов, ИИ

database.py – операции с базой данных

config.py – конфигурация и переменные окружения

logs/ – файлы логов для отладки и отслеживания действий

Добавление новых функций:

Создавайте новые модули в handlers/ или расширяйте FSM состояния

Используйте инлайн-клавиатуры и обычные клавиатуры для взаимодействия

Сохраняйте код модульным; не загромождайте один файл

Тестирование:

Запускайте бота локально с тестовым аккаунтом Telegram

Убедитесь, что все FSM-процессы работают корректно перед коммитом

Pull Requests:

Пишите понятные сообщения коммитов

Опишите изменения в PR

Убедитесь, что API-ключи не коммитятся

Советы:

Всегда используйте state и FSMContext для многошаговых взаимодействий с пользователем

Держите код ИИ отдельно для удобного апгрейда

Следуйте существующим паттернам логирования для отслеживания ошибок и действий
