# Telegram Support Bot

> **Note:** This repository is a demonstration of a Telegram support bot. Do not use it in production without additional development, security review, and testing tailored to your requirements.

## Description

Telegram Support Bot is designed to showcase how user requests can be received, processed by operators, and managed via Telegram. The bot provides multilingual support using Fluent, and can be deployed quickly using Docker.

## Main Features

- Creating and tracking user support tickets
- Operator responses and ticket management within Telegram
- Dialog history logging
- Multilingual interface (Fluent)
- Simple deployment via Docker and Docker Compose

## Technologies Used

- **Python** — core bot logic
- **Fluent** — internationalized messages
- **Docker** — containerization and deployment
- **MongoDB** — database for tickets and users

> **Database:** MongoDB is used for persistent storage (see [bot/src/utils/db.py](bot/src/utils/db.py)). Configure connection parameters using environment variables in your `.env` file.

## Getting Started

1. Clone the repository:
    ```bash
    git clone https://github.com/Danylo101/telegram-support-bot.git
    cd telegram-support-bot
    ```

2. Create a `.env` file with your bot token and MongoDB connection details:
    ```
    BOT_TOKEN=your_bot_token
    ADMIN_ID=123456789
    OPERATOR_IDS=987654321,123123123
    MONGO_USERNAME=...
    MONGO_PASSWORD=...
    MONGO_HOST=...
    MONGO_PORT=...
    MONGO_DB_NAME=...
    ```
    > For MongoDB setup and configuration (ports, authentication, etc.), refer to the official documentation: [MongoDB Installation Docs](https://docs.mongodb.com/manual/installation/)

## Running with Docker

Start the project with using Docker Compose (recommended):

```bash
docker-compose up
```
> **Tip:** Add the `-d` flag (`docker-compose up -d`) to run containers in the background.

For more details on Docker Compose, visit the [Docker Compose documentation](https://docs.docker.com/compose/).

## Localization

Bot message texts are stored in Fluent files (`bot/src/i18n/uk/`). You can easily add support for new languages by creating additional Fluent files.

## Author & Contact

- Author: [Danylo101](https://github.com/Danylo101)
- For questions or suggestions, please open an issue on GitHub.

---

**License:** MIT

> **Disclaimer:** This project is for demonstration purposes only! For production use, you must carefully review, test, and adapt the code to meet your application's requirements and security standards.