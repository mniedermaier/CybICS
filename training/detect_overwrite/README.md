# Detection Training - Override

One common attack is Modbus TCP register flooding, where an attacker sends a continuous stream of malicious Modbus commands to overwrite or spoof register values.
This can disrupt processes, cause equipment failure, or provide incorrect data to operators.
This training focuses on how to detect this type of attack by analyzing network traffic and monitoring system behavior.

## Indicators of Modbus Flooding Attacks
Detecting Modbus flooding and register overwriting attacks requires understanding how normal Modbus traffic behaves and recognizing anomalies in the communication pattern. Key indicators include:

1. ***High Frequency of Modbus Write Requests***

    Modbus systems typically have a stable frequency of write operations. A sudden spike in write requests, particularly to the same registers, is a sign of flooding. Monitor for:
    Unusual write frequencies: Multiple write commands to the same register in a short time span.
    Repeated overwrites: The same register being modified continuously.

2. ***Unexplained Process Values Changes***

    When a Modbus register is being spoofed, the values stored in registers might change frequently without corresponding physical events. For example:
    A temperature sensor reports fluctuating values despite stable environmental conditions.
    Equipment parameters (e.g., pressure, motor speed) are altered without operator action.

3. ***Unusual Source IPs or Unauthorized Devices***

    Flooding may come from unauthorized IP addresses or devices not normally involved in the communication. Look for:
    Write commands originating from unknown sources.
    Devices sending Modbus traffic that do not typically perform write operations.

4. ***Network Traffic Abnormalities***

    Flooding often generates a high volume of packets, potentially leading to congestion or delays in legitimate traffic. Watch for:
    * Unusually high Modbus traffic: A sharp increase in Modbus TCP packets on the network.
    * Packet loss: Legitimate Modbus traffic may be delayed or dropped due to the attack.

***Questions:***
* What is happening with the physical process?
* What can you observe within the network capture?

***!!! Execute the python script without looking into it !!!***

```sh
python3 override.py <DEVICE_IP>
```

<details>
  <summary><strong><span style="color:orange;font-weight: 900">Solution</span></strong></summary>

* ***Modbus Filter:***

    To filter only Modbus traffic, use the following filter in Wireshark:

    ```sh
    tcp.port == 502
    ```

* ***Identifying Excessive Write Requests:***

    Apply a filter for Modbus function codes responsible for writing registers:
    ```sh
    modbus.func_code == 6 || modbus.func_code == 16
    ```
    Look for a large number of write requests to the same register (e.g., modbus.reference_num indicates the register address).

* ***IO Graphs:***

    Use Wireshark's IO Graphs to visualize the traffic over time. A spike in the number of write requests is a strong indicator of flooding.

</details>