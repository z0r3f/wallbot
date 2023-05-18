![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/tamasco/wallbot-docker) [![Docker pulls](https://img.shields.io/docker/pulls/tamasco/wallbot-docker?style=flat-square)](https://hub.docker.com/r/tamasco/wallbot-docker) [![commit_freq](https://img.shields.io/github/commit-activity/m/Borja-Garduno/wallbot?style=flat-square)](https://github.com/Borja-Garduno/wallbot/commits) [![last_commit](https://img.shields.io/github/last-commit/Borja-Garduno/wallbot?style=flat-square)](https://github.com/Borja-Garduno/wallbot/commits) ![Docker Image Version (latest by date)](https://img.shields.io/docker/v/tamasco/wallbot-docker) ![GitHub](https://img.shields.io/github/license/Borja-Garduno/wallbot)


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
docker build --tag tamasco/wallbot-docker:latest .
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
docker tag tamasco/wallbot-docker:latest tamasco/wallbot-docker:$version
```
###### Push
```bash
docker push tamasco/wallbot-docker:latest 
docker push tamasco/wallbot-docker:$version
```
## See images

```bash
docker images
```

## Run on container

```bash
docker run --env BOT_TOKEN=<YOUR-TOKEN> tamasco/wallbot-docker:latest --name wallbot
```

## Export image
```bash
docker save -o wallbot-docker.tar tamasco/wallbot-docker:latest
```