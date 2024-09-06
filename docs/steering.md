

image: 
```text
ghcr.io/flux-agi/flux-cart-control-steering:1.0.0
```
see https://github.com/orgs/flux-agi/packages/container/package/flux-cart-control-steering for versions and tags



service should have settings
```json
{
  "settings": {
    "neutral_position":  60,
    "max_right_position": 70,
    "max_left_position": 50,
    "pin":  15,
    "frequency": 400,
    "topic": "neurons/{id}/out"
  }
}
```


e.g. in activeConfig
```json
{
  "__typename": "Service",
  "id": "hazs57df2",
  "serviceType": "RIM",
  "location": null,
  "image": "ghcr.io/flux-agi/flux-cart-control-steering:1.0.0",
  "tag": "ghcr.io/flux-agi/flux-cart-control-steering",
  "alias": "rcCarPeriphery",
  "description": "Car steering wheel controller",
  "settings": {
    "neutral_position":  60,
    "max_right_position": 70,
    "max_left_position": 50,
    "pin":  15,
    "frequency": 400,
    "topic": "neurons/{id}/out"
  }
}
```

```text
cz bump
bash build-steering.sh
```

