[![Build Status](https://travis-ci.com/z0r3f/wallbot.svg)](https://travis-ci.com/z0r3f/wallbot)

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