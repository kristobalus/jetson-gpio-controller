
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
  "image": "",
  "tag": "",
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

