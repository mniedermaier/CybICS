<p align="center">
  <img alt="CybICS Logo" src="doc/pics/CybICS_logo.png" height="120" />
  <p align="center">Understanding industrial Cybersecurity.</p>
</p>

---

<div align="center">

[![License](https://img.shields.io/badge/license-MIT%20License-32c955)](/LICENSE)
[![KiBot](https://github.com/mniedermaier/CybICS/actions/workflows/kibotVerify.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/kibotVerify.yml)
[![C/C++ CI](https://github.com/mniedermaier/CybICS/actions/workflows/buildTest.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/buildTest.yml)
[![flawFinder C](https://github.com/mniedermaier/CybICS/actions/workflows/flawfinder.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/flawfinder.yml)
[![TruffleHog](https://github.com/mniedermaier/CybICS/actions/workflows/trufflehog.yaml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/trufflehog.yaml)
[![devContainer](https://github.com/mniedermaier/CybICS/actions/workflows/devContainer.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/devContainer.yml)
[![pytest](https://github.com/mniedermaier/CybICS/actions/workflows/pytest.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/pytest.yml)
</div>

---

## What is CybICS?

CybICS (Cybersecurity for Industrial Control Systems) is an open-source training platform designed to help cybersecurity professionals, students, and researchers understand the unique challenges of securing industrial control systems (ICS) and SCADA environments.

The platform simulates a realistic industrial gas pressure control system complete with:
- **PLC** (Programmable Logic Controller) - OpenPLC
- **HMI** (Human-Machine Interface) - FUXA
- **Physical Process Simulation** - Gas pressure control system
- **Multiple Industrial Protocols** - Modbus TCP, OPC-UA, S7comm, DNP3, EtherNet/IP

### Why CybICS?

- ✅ **Hands-on Learning**: Practice real-world ICS security techniques in a safe environment
- ✅ **Cost-Effective**: Free and open-source
- ✅ **Flexible**: Choose between virtual (Docker) or physical (Raspberry Pi + STM32) deployment
- ✅ **Comprehensive**: Covers reconnaissance, exploitation, and defense
- ✅ **CTF-Ready**: Built-in capture-the-flag challenges for training exercises

---

## Table of Contents

- [What is CybICS?](#what-is-cybics)
- [Deployment Options](#deployment-options)
- [Quick Start - Virtual Testbed](#-quick-start---virtual-testbed)
- [Physical Process Description](#physical-process-description)
- [Hardware](#hardware)
- [Software Components](#software-components)
- [Training Modules](#training-modules)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Abbreviations](#abbreviations)
- [Contributing](#contributing)
- [License](#license)

---

## Deployment Options

CybICS offers two deployment modes to suit different learning needs and budgets:

<table>
<tr>
<td width="50%" valign="top">

### 💻 Virtual (Recommended for Beginners)
**Docker-based deployment for easy setup**

<img src="doc/pics/landing.png" width="100%">

</td>
<td width="50%" valign="top">

### 🔧 Physical (Advanced)
**Hardware-based deployment with Raspberry Pi**

<img src="doc/pics/cybics.png" width="100%">

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Advantages**:
- ✅ No hardware required
- ✅ Quick setup (5 minutes)
- ✅ Easy to reset and reproduce
- ✅ Perfect for classroom/online training
- ✅ Runs on Windows, Linux, macOS

</td>
<td width="50%" valign="top">

**Advantages**:
- ✅ Realistic physical hardware
- ✅ Learn embedded systems security
- ✅ Practice hardware attacks (UART, SWD)
- ✅ Portable standalone device
- ✅ Visual LED indicators

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Requirements**:
- Docker & Docker Compose
- 4GB RAM minimum
- 10GB disk space

</td>
<td width="50%" valign="top">

**Requirements**:
- Raspberry Pi Zero 2 W
- Custom CybICS PCB (~50 EUR)
- LCD display
- MicroSD card

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Use Cases**:
- Learning ICS security fundamentals
- Developing attack/defense techniques
- Classroom training sessions
- CTF competitions

</td>
<td width="50%" valign="top">

**Use Cases**:
- Advanced ICS security training
- Hardware hacking workshops
- Demonstrations at conferences
- Permanent lab installations

</td>
</tr>
<tr>
<td colspan="2">

**Comparison**:

| Feature | Virtual | Physical |
|---------|---------|----------|
| **Cost** | Free | ~50-70 EUR |
| **Setup Time** | 5 minutes | 1-2 hours |
| **Hardware Attacks** | ❌ | ✅ |
| **Portability** | Cloud-ready | Portable device |
| **Scalability** | Unlimited instances | Limited by hardware |
| **Realism** | Software simulation | Physical LEDs & display |

</td>
</tr>
</table>

---

## 🚀 Quick Start - Virtual Testbed

Get CybICS running in under 5 minutes using the virtual environment!

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- At least 4GB of free RAM
- Linux, macOS, or Windows with WSL2

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mniedermaier/CybICS.git --recursive
   cd CybICS
   ```

2. **Start the virtual environment**:
   ```bash
   ./cybics.sh start
   ```

3. **Access the services**:

   Once started, open your browser and navigate to:

   | Service | URL | Default Credentials |
   |---------|-----|---------------------|
   | **Landing Page** | http://localhost | - |

### Managing the Environment

```bash
# Check status of all services
./cybics.sh status

# View logs from all containers
./cybics.sh logs

# Stop the environment
./cybics.sh stop

# Restart the environment
./cybics.sh restart
```
---

## Physical Process Description

CybICS simulates a gas pressure control system commonly found in industrial environments. This simple yet realistic process provides an excellent foundation for learning ICS cybersecurity concepts.

### System Overview

The system maintains gas pressure in a High Pressure Tank (HPT) using gas from a Gas Storage Tank (GST). A PLC controls a compressor that transfers gas between tanks while monitoring pressure levels and safety conditions.

### Components

#### Gas Storage Tank (GST)
Buffer tank for the external gas supply. The PLC maintains GST pressure between 60-240 bar.

| Pressure | Status | Range (bar) | Color Indicator |
|----------|--------|-------------|-----------------|
| <50 | Low | 0-49 | Red |
| 50-149 | Normal | 50-149 | Green |
| 150+ | Full | 150-255 | Blue |

**Control Loop**:
- When GST < 60 bar → Start filling from external supply
- Continue until GST ≥ 240 bar → Stop filling
- Prevents compressor operation when GST is too low

#### High Pressure Tank (HPT)
Main buffer tank providing pressure to the system. Target range: 60-90 bar.

| Pressure | Status | Range (bar) | Meaning |
|----------|--------|-------------|---------|
| 0 | Empty | 0 | System offline |
| 1-49 | Low | 1-49 | Below operating range |
| 50-99 | Normal | 50-99 | Safe operating range |
| 100-149 | High | 100-149 | Above target, but safe |
| 150+ | Critical | 150+ | Dangerous overpressure |

**Control Loop**:
- When HPT < 60 bar AND GST > 50 bar → Start compressor
- Continue until HPT ≥ 90 bar → Stop compressor
- Compressor disabled if GST < 50 bar (safety interlock)

#### System Operation
The system can operate normally when HPT is between 50-100 bar:
- HPT < 50 bar → System cannot operate (insufficient pressure)
- HPT > 100 bar → System at risk of damage

#### Safety: Blowout Valve (BO)
Mechanical safety valve (not PLC-controlled) that prevents catastrophic failure:
- Opens when HPT > 220 bar
- Vents toxic gas to atmosphere
- Closes when HPT < 200 bar
- **Security implication**: Triggering the blowout releases toxic gas


---

## Hardware

For those choosing the physical deployment, CybICS uses affordable, off-the-shelf components.

**Detailed instructions**: [Hardware Guide](hardware/README.md) | [PCB Ordering Guide](hardware/pcb/README.md)

---

## Training Modules

CybICS includes 13+ hands-on training modules covering the full ICS security lifecycle:

Each module includes:
- 📖 Background theory
- 🎯 Hands-on exercises
- 🚩 CTF-style flags
- 💡 Hints and solutions

**Start training**: [Training Overview](training/README.md)

---

## Documentation

Comprehensive documentation is available for all components:

### Getting Started
- 📘 [Quick Start Guide](doc/README.md) - Detailed installation instructions
- 🎓 [Training Overview](training/README.md) - All training modules
- 🧪 [Testing Guide](tests/README.md) - Automated testing

### Hardware
- 🔧 [Hardware Overview](hardware/README.md) - BOM, assembly, specifications
- 📟 [PCB Ordering Guide](hardware/pcb/README.md) - Step-by-step JLCPCB ordering
- 📦 [3D Case Files](hardware/case/README.md) - Printable enclosure

### Software
- 💾 [Software Overview](software/README.md) - Setup and configuration
- 🎛️ [OpenPLC Integration](software/OpenPLC/README.md) - PLC programming and configuration
- 🖥️ [FUXA HMI](software/FUXA/README.md) - HMI configuration
- 🔌 [Virtual Hardware I/O](software/hwio-virtual/README.md) - Virtual process simulation
- 🍓 [Raspberry Pi I/O](software/hwio-raspberry/README.md) - Physical hardware interface
- 🔬 [STM32 Firmware](software/stm32/README.md) - Embedded firmware (Zephyr RTOS)

---

## Abbreviations

| Abbreviation | Full Name | Description |
| ------------ | --------- | ----------- |
| **BO** | Blowout | Safety valve that vents gas at critical pressure |
| **CTF** | Capture The Flag | Security training challenge format |
| **DNP3** | Distributed Network Protocol 3 | SCADA communication protocol |
| **GST** | Gas Storage Tank | Buffer tank for external gas supply |
| **HMI** | Human-Machine Interface | Operator control and monitoring interface |
| **HPT** | High Pressure Tank | Main system pressure buffer |
| **I2C** | Inter-Integrated Circuit | Serial communication protocol |
| **ICS** | Industrial Control System | Systems controlling industrial processes |
| **LED** | Light-Emitting Diode | Visual indicator on hardware |
| **OPC-UA** | OPC Unified Architecture | Industry 4.0 communication standard |
| **PCB** | Printed Circuit Board | CybICS custom hardware board |
| **PLC** | Programmable Logic Controller | Industrial controller (OpenPLC) |
| **RTOS** | Real-Time Operating System | Zephyr (on STM32) |
| **SCADA** | Supervisory Control and Data Acquisition | Industrial monitoring system |
| **STM32** | STMicroelectronics 32-bit MCU | Microcontroller on CybICS PCB |
| **SWD** | Serial Wire Debug | Programming/debugging interface for STM32 |
| **UART** | Universal Asynchronous Receiver-Transmitter | Serial communication |

---

## Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Report bugs** via GitHub Issues
- 💡 **Suggest features** or improvements
- 📝 **Improve documentation** (typos, clarity, examples)
- 🎓 **Create training modules** for new attack/defense techniques
- 🔧 **Submit code improvements** via Pull Requests
- 🌍 **Translate documentation** to other languages

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone --recursive https://github.com/YOUR_USERNAME/CybICS.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make changes and test thoroughly
5. Commit: `git commit -m "Description of changes"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request

---

## License

CybICS is released under the **MIT License**. See [LICENSE](/LICENSE) for details.

### Third-Party Components

- **OpenPLC**: GPL-3.0 License
- **FUXA**: MIT License
- **Zephyr RTOS**: Apache-2.0 License

---

## Acknowledgments

CybICS is developed for educational purposes to improve ICS cybersecurity awareness. Special thanks to the open-source community and all contributors.

**Disclaimer**: This platform is designed for authorized training and education only. Unauthorized use against production systems is illegal and unethical.

---

<p align="center">
  <strong>Ready to start?</strong><br>
  <code>./cybics.sh start</code>
</p>

<p align="center">
  <a href="doc/README.md">📘 Detailed Setup Guide</a> •
  <a href="training/README.md">🎓 Training Modules</a> •
  <a href="https://github.com/mniedermaier/CybICS/issues">🐛 Report Issues</a>
</p>
