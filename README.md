# Device-SMI

**Device-SMI** is a Python module designed to retrieve system information about devices, including CPUs and NVIDIA CUDA-enabled GPUs.

The module fetches:
- **NVIDIA GPU information** using the NVIDIA System Management Interface (NVIDIA-SMI).
- **CPU information** via system interfaces.

Future updates will include support for additional device types.

## Features

- Retrieve information for both CPU and NVIDIA CUDA devices.
- Includes details about memory usage, utilization, and model specifications.



[WIP] Python lib with zero-dependencies and will get you a unified `device.info` properties for `gpu`, `cpu`, and `npu`. No more calling separate tools such as `nvidia-smi` or `/proc/cpuinfo` and parsing it yourself.  
