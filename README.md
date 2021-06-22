![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/z0r3f/wallbot-docker) [![Docker pulls](https://img.shields.io/docker/pulls/z0r3f/wallbot-docker?style=flat-square)](https://hub.docker.com/r/z0r3f/wallbot-docker)  [![commit_freq](https://img.shields.io/github/commit-activity/m/z0r3f/wallbot?style=flat-square)](https://github.com/z0r3f/wallbot/commits) [![Build Status](https://travis-ci.com/z0r3f/wallbot.svg)](https://travis-ci.com/z0r3f/wallbot)  [![last_commit](https://img.shields.io/github/last-commit/z0r3f/wallbot?style=flat-square)](https://github.com/z0r3f/wallbot/commits) ![Docker Image Version (latest by date)](https://img.shields.io/docker/v/z0r3f/wallbot-docker) ![GitHub](https://img.shields.io/github/license/z0r3f/wallbot)


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
docker build --tag z0r3f/wallbot-docker:latest .
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
docker tag z0r3f/wallbot-docker:latest z0r3f/wallbot-docker:$version
```
###### Push
```bash
docker push z0r3f/wallbot-docker:latest 
docker push z0r3f/wallbot-docker:$version
```
## See images

```bash
docker images
```

## Run on container

```bash
docker run --env BOT_TOKEN=<YOUR-TOKEN> z0r3f/wallbot-docker:latest --name wallbot
```

## Export image
```bash
docker save -o wallbot-docker.tar z0r3f/wallbot-docker:latest
```