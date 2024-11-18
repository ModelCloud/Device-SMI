# Device-SMI

Python lib with zero-dependencies and will get you a unified `device.info` properties for `gpu`, `cpu`, and `npu`. No more calling separate tools such as `nvidia-smi` or `/proc/cpuinfo` and parsing it yourself.

Device data sources:

- **CPU**: [Intel/Amd/Apple] Linux/MacOS system interface
- **NVIDIA GPU**: NVIDIA System Management Interface (NVIDIA-SMI).
- **AMD GPU**: (PENDING)
- **Intel GPU**: (PENDING)

## Features

- Retrieve information for both CPU and GPU devices.
- Includes details about memory usage, utilization, driver, pcie info when applicable, and other device specifications.
