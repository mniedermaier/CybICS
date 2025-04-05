# Intrusion Detection on Modbus

## Configure Virtual CybICS Docker Envronment

Configure iptables
```sh
iptables -t mangle -A PREROUTING -i br-$(docker network inspect -f '{{.Id}}' virtual_virt-cybics | cut -c1-12) -j TEE --gateway 172.18.0.7
iptables -t mangle -A POSTROUTING -o br-$(docker network inspect -f '{{.Id}}' virtual_virt-cybics | cut -c1-12) -j TEE --gateway 172.18.0.7
```

Running shell in suricata container
```sh
docker exec -it virtual-suricata-1 sh
```

Running TCPDmp in suricata docker container
```sh
tcpdump -c 15 -i eth0
```


## Modifing Suricata Rules

Restart Docker Container
```sh
docker restart virtual-surricata-1
```