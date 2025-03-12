# Network Fuzzing

## Introduction
Network fuzzing is a security testing technique used to identify vulnerabilities in network protocols, services, and applications by sending malformed or unexpected data. The goal is to discover security flaws such as buffer overflows, denial-of-service (DoS) vulnerabilities, and other unintended behaviors.

## How It Works
Network fuzzing involves the following steps:

1. **Selecting a Target** – Identify the network service, protocol, or application to be tested.
2. **Generating Test Cases** – Create malformed, randomized, or unexpected inputs that interact with the target.
3. **Sending Inputs** – Transmit the test cases to the target over the network.
4. **Monitoring Responses** – Observe how the target handles the malformed data, checking for crashes, hangs, or unexpected behavior.
5. **Analyzing Results** – Identify potential security vulnerabilities based on anomalies detected during testing.

## Types of Network Fuzzing
There are different approaches to network fuzzing:

- **Mutation-based Fuzzing** – Modifies existing valid inputs to generate test cases.
- **Generation-based Fuzzing** – Constructs test cases from scratch based on protocol specifications.
- **Stateful vs. Stateless Fuzzing** – Stateful fuzzing maintains session states, while stateless fuzzing sends individual test cases without tracking interactions.

## Challenges and Considerations
- **False Positives** – Some anomalies may not indicate real vulnerabilities.
- **Target Stability** – Frequent crashes may disrupt testing.
- **Protocol Complexity** – Some network protocols require deep understanding for effective fuzzing.
- **Legal and Ethical Considerations** – Unauthorized fuzzing can violate laws and agreements.


# Use it on the CybICS
Clone the repository:
```sh
git clone https://github.com/s-e-knudsen/Modbus_network_fuzzer
```

Switch to the folder:
```sh
cd Modbus_network_fuzzer 
```

Install the dependencies for the modbus network fuzzer:
```sh
python3 -m pip install -r requirements.txt
```

Select the proper fuzzing method. E.g. 1 for all:
```sh
        --------------------------------------
        Created by Soren Egede Knudsen @Egede
        --------------------------------------
        What do you want to fuzz?
        1.  Fuzz all function codes and base
        2.  Fuzz Read Device Identification
        3.  Fuzz Read Discrete Inputs
        4.  Fuzz Read Input Registers
        5.  Fuzz Read Multiple Holding Registers
        6.  Fuzz Write Single Holding Register
        7.  Fuzz Write Single Coil
        8.  Fuzz Write Multiple Coils
        9.  Fuzz Write Multiple Holding Registers
        10. Fuzz Read/Write Multiple Registers
        11. Fuzz Mask Write Register
        12. Fuzz Read File Record
        13. Fuzz Write File Record
        14. Fuzz Read Exception Status
        15. Fuzz Report Slave ID
        16. Fuzz Read Coil Memory
        20. Fuzz ModbusTCP - Base protocol
        - - - - - - - - - - - - - - - - - - - 
        90. Fuzz ModbusTCP - FC67 - non standard - Read float registers
        91. Fuzz ModbusTCP - FC68 - non standard - Read float registers
        92. Fuzz ModbusTCP - FC70 - non standard - Write single float registers
        93. Fuzz ModbusTCP - FC80 - Non standard - Write multible float registers
        - - - - - - - - - - - - - - - - - - - 
        0. Exit
```

Grab a coffee ☕☕☕☕