# Device-SMI

Self-contained Python lib with zero-dependencies that give you a unified `device` properties for `gpu`, `cpu`, and `npu`. No more calling separate tools such as `nvidia-smi` or `/proc/cpuinfo` and parsing it yourself.

<p align="center">
    <a href="https://github.com/ModelCloud/Device-SMI/releases" style="text-decoration:none;"><img alt="GitHub release" src="https://img.shields.io/github/release/ModelCloud/Device-SMI.svg"></a>
    <a href="https://pypi.org/project/device-smi/" style="text-decoration:none;"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/device-smi"></a>
    <a href="https://pepy.tech/projects/device-smi" style="text-decoration:none;"><img src="https://static.pepy.tech/badge/device-smi" alt="PyPI Downloads"></a>
    <a href="https://github.com/ModelCloud/Device-SMI/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/device-smi" alt="License"></a>
</p>

## News
* 12/02/2024 [0.3.0](https://github.com/ModelCloud/Device-SMI/releases/tag/v0.3.0) Added `OSDevice`.[`name`, `version`, `kernel`, `arch`] for Linux/MacOS/Windows/FreeBSD/Solaris. Added `cpu.`[`count`, `cores`, `threads`] properties. Bug fix for gpu device index. 
* 11/29/2024 [0.2.1](https://github.com/ModelCloud/Device-SMI/releases/tag/v0.2.1) Added `pcie.`[`gen`, `speed`, `id`] + [`firmware`, `driver`] properties to `GPU` device.

## Features

- Retrieve information for both CPU and GPU devices.
- Includes details about memory usage, utilization, driver, pcie info when applicable, and other device specifications.
- Zero pypi dependency.
- Linux/MacOS support

Supported Devices:

- **OS**: Linux, MacOS, Windows, FreeBSD, Solaris
- **CPU**: [Intel/AMD/Apple] Linux/MacOS system interface
- **NVIDIA GPU**: NVIDIA System Management Interface `nvidia-smi`
- **Intel XPU**: Intel/XPU System Management Interface `xpu-smi`
- **Apple GPU**: MacOS interfaces

## Usage

For OS, use `os` to init a new Device object.

```py
from device_smi import Device

dev = Device("os")
print(dev)
```

Output: (Ubuntu 22.04)

> {'type': 'os', 'name': 'ubuntu', 'version': '22.04', 'kernel': '6.12.1-x64v3-xanmod2', 'arch': 'x86_64'}

For GPU/XPU, use [`gpu`, `cuda`] for Nvidia and `xpu` for Intel/XPU. Index usage for multiple GPUs: `cuda:0`

```py
from device_smi import Device

dev = Device("cuda:0")
print(dev)
```

Output: (Nvidia 4090)

> {'pcie': {'gen': 2, 'speed': 1, 'id': '00000000:16:00.0'}, 'gpu': {'driver': '565.57.01', 'firmware': '95.02.3C.40.E7'}, 'type': 'gpu', 'model': 'geforce rtx 4090', 'memory_total': 25757220864, 'vendor': 'nvidia', 'features': ['8.9']}

For CPU, use `cpu` to init a new Device object. 

```py
from device_smi import Device

dev = Device("cpu")
print(dev)
```

Output: (AMD EPYC 7443)

> {'type': 'cpu', 'model': 'epyc 7443', 'vendor': 'amd', 'memory_total': 1000000000000, 'count': 2, 'cores': 48, 'threads': 96, 'features': ['3dnowprefetch', 'abm', 'adx', 'aes', 'amd_ppin', 'aperfmperf', 'apic', 'arat', 'avx', 'avx2', 'bmi1', 'bmi2', 'bpext', 'brs', 'cat_l3', 'cdp_l3', 'clflush', 'clflushopt', 'clwb', 'clzero', 'cmov', 'cmp_legacy', 'constant_tsc', 'cpb', 'cpuid', 'cqm', 'cqm_llc', 'cqm_mbm_local', 'cqm_mbm_total', 'cqm_occup_llc', 'cr8_legacy', 'cx16', 'cx8', 'de', 'debug_swap', 'decodeassists', 'erms', 'extapic', 'extd_apicid', 'f16c', 'flushbyasid', 'fma', 'fpu', 'fsgsbase', 'fsrm', 'fxsr', 'fxsr_opt', 'ht', 'hw_pstate', 'ibpb', 'ibrs', 'ibs', 'invpcid', 'irperf', 'lahf_lm', 'lbrv', 'lm', 'mba', 'mca', 'mce', 'misalignsse', 'mmx', 'mmxext', 'monitor', 'movbe', 'msr', 'mtrr', 'mwaitx', 'nonstop_tsc', 'nopl', 'npt', 'nrip_save', 'nx', 'ospke', 'osvw', 'overflow_recov', 'pae', 'pat', 'pausefilter', 'pcid', 'pclmulqdq', 'pdpe1gb', 'perfctr_core', 'perfctr_llc', 'perfctr_nb', 'pfthreshold', 'pge', 'pku', 'pni', 'popcnt', 'pse', 'pse36', 'rapl', 'rdpid', 'rdpru', 'rdrand', 'rdseed', 'rdt_a', 'rdtscp', 'rep_good', 'sep', 'sha_ni', 'skinit', 'smap', 'smca', 'smep', 'ssbd', 'sse', 'sse2', 'sse4_1', 'sse4_2', 'sse4a', 'ssse3', 'stibp', 'succor', 'svm', 'svm_lock', 'syscall', 'tce', 'topoext', 'tsc', 'tsc_scale', 'umip', 'user_shstk', 'v_spec_ctrl', 'v_vmsave_vmload', 'vaes', 'vgif', 'vmcb_clean', 'vme', 'vmmcall', 'vpclmulqdq', 'wbnoinvd', 'wdt', 'xgetbv1', 'xsave', 'xsavec', 'xsaveerptr', 'xsaveopt', 'xsaves', 'xtopology']}


## Roadmap

- Support AMD GPU
- Support Intel/Gaudi
- Support Google/TPU
- Add NPU support (ARM/Intel/AMD)
