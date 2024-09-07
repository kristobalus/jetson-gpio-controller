Start docker-compose.yml
```shell
docker compose up --build -d
```

```shell
mqttx pub -t 'neurons/test-forward/out' -h 'localhost' -p 1883 -m "0.6"
```

```shell
mqttx pub -t 'neurons/test-steering/out' -h 'localhost' -p 1883 -m "0.5"
```