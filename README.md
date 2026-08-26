<!-- Docker Badges -->
[![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/clonikal/wallbot-docker)](https://hub.docker.com/r/clonikal/wallbot-docker)
[![Docker pulls](https://img.shields.io/docker/pulls/clonikal/wallbot-docker?style=flat-square)](https://hub.docker.com/r/clonikal/wallbot-docker)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/clonikal/wallbot-docker)](https://hub.docker.com/r/clonikal/wallbot-docker)

<!-- GitHub Actions Badges -->
[![Docker Release](https://github.com/clonikal/wallbot/actions/workflows/docker-release.yml/badge.svg)](https://github.com/clonikal/wallbot/actions/workflows/docker-release.yml)
[![Build Status](https://github.com/clonikal/wallbot/actions/workflows/main.yml/badge.svg)](https://github.com/clonikal/wallbot/actions/workflows/main.yml)

[//]: # ([![Codecov]&#40;https://codecov.io/gh/clonikal/wallbot/branch/main/graph/badge.svg&#41;]&#40;https://codecov.io/gh/clonikal/wallbot&#41;)

<!-- Proyecto y actividad -->
[![commit_freq](https://img.shields.io/github/commit-activity/m/clonikal/wallbot?style=flat-square)](https://github.com/clonikal/wallbot/commits)
[![last_commit](https://img.shields.io/github/last-commit/clonikal/wallbot?style=flat-square)](https://github.com/clonikal/wallbot/commits)
[![Python Version](https://img.shields.io/pypi/pyversions/wallbot-docker)](https://github.com/clonikal/wallbot)

<!-- Licencia -->
![GitHub](https://img.shields.io/github/license/clonikal/wallbot)

# wallbot

wallapop search bot

bot de Telegram para gestionar busquedas sobre wallapop

- Notifica cuando encuentra alguna busqueda
- Avisa cuando algún ítem baja de precio
- Permite gestionar tu lista de ítems

pip3 install -r requirements.txt

# Docker

## Generate image docker

```bash
docker build --tag clonikal/wallbot-docker:latest .
```

## Tag version

###### Windows

```ps
$version = Get-Content "VERSION"
```

###### Unix

```bash
version=`cat VERSION`
```

###### Tag

```bash
docker tag clonikal/wallbot-docker:latest clonikal/wallbot-docker:$version
```

###### Push

```bash
docker push clonikal/wallbot-docker:latest 
docker push clonikal/wallbot-docker:$version
```

## See images

```bash
docker images
```

## Run on container

```bash
docker run --name wallbot --env BOT_TOKEN=<YOUR-TOKEN> AUTHORIZED_USERS=<CHAT_ID[,CHAT_ID]> clonikal/wallbot-docker:latest
```

## Export image

```bash
docker save -o wallbot-docker.tar clonikal/wallbot-docker:latest
```

## Target Project Structure

```
wallapop_bot/
├── __init__.py
├── main.py                    # Punto de entrada principal
├── config/
│   ├── __init__.py
│   ├── settings.py           # Configuración general
│   └── constants.py          # Constantes (emojis, URLs)
├── database/
│   ├── __init__.py
│   ├── db_helper.py          # Tu DBHelper actual
│   ├── models.py             # Clases ChatSearch, Item
│   └── migrations.py         # Migraciones de BD
├── telegram/
│   ├── __init__.py
│   ├── bot.py                # Configuración del bot
│   ├── handlers.py           # Manejadores de comandos
│   └── notifications.py      # Función notel y similares
├── wallapop/
│   ├── __init__.py
│   ├── api_client.py         # Cliente API Wallapop
│   ├── search.py             # Lógica de búsqueda
│   └── item_processor.py     # Procesamiento de items
├── utils/
│   ├── __init__.py
│   ├── logger.py             # Configuración de logging
│   ├── currency.py           # Utilidades de moneda
│   └── exceptions.py         # Excepciones personalizadas
└── requirements.txt
```
