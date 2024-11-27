# Device-SMI

Self-contained Python lib with zero-dependencies that give you a unified `device` properties for `gpu`, `cpu`, and `npu`. No more calling separate tools such as `nvidia-smi` or `/proc/cpuinfo` and parsing it yourself.

## Features

- Retrieve information for both CPU and GPU devices.
- Includes details about memory usage, utilization, driver, pcie info when applicable, and other device specifications.
- Zero pypi dependency.
- Linux/MacOS support

Supported Devices:

- **CPU**: [Intel/Amd/Apple] Linux/MacOS system interface
- **NVIDIA GPU**: NVIDIA System Management Interface `nvidia-smi`
- **Intel XPU**: Intel/XPU System Management Interface `xpu-smi`
- **Apple GPU**: MacOS interfaces

## Roadmap

- Support Non-Apple ARM
- Support AMD GPU
- Support Intel/Gaudi
- Support Google/TPU
- Add PCIE property info to GPU/XPU
- Add NPU support (ARM/Intel/AMD)
- Add Non-Linux/MacOS support (BSD/Sun)
