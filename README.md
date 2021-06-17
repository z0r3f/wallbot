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
docker build --tag wallbot-docker .
```

## See images

```bash
docker images
```

## Run on container

```bash
docker run --env BOT_TOKEN=<YOUR-TOKEN> wallbot-docker:latest --name wallbot
```

## Export image
```bash
docker save -o wallbot-docker.tar wallbot-docker:latest
```