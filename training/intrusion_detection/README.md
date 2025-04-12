# Intrusion Detection on Modbus

## Modifing Suricata Rules

Restart Docker Container
```sh
docker restart virtual-suricata-1
```

Execute in Docker Container
```sh
docker exec -it virtual-suricata-1
```
Reload suricata rules
```sh
suricatasc -c reload-rules
```
```sh
suricatasc -c reload-rules-nonblocking
```