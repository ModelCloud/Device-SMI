# Device-SMI

Self-contained Python lib with zero-dependencies that give you a unified `device` properties for `gpu`, `cpu`, and `npu`. No more calling separate tools such as `nvidia-smi` or `/proc/cpuinfo` and parsing it yourself.

## Features

- Retrieve information for both CPU and GPU devices.
- Includes details about memory usage, utilization, driver, pcie info when applicable, and other device specifications.
- Zero pypi dependency.
- Linux/MacOS support

Supported Devices:

- **CPU**: [Intel/AMD/Apple] Linux/MacOS system interface
- **NVIDIA GPU**: NVIDIA System Management Interface `nvidia-smi`
- **Intel XPU**: Intel/XPU System Management Interface `xpu-smi`
- **Apple GPU**: MacOS interfaces

## Examples

To get GPU info, Device-SMI allows 'gpu', 'cuda' (for Nvidia), 'xpu'(for Intel). or adding device index like 'cuda:0'

```py
from device_smi import Device

smi = Device("cuda:0")
info = smi.info()
print(info)
```

result:

> {'type': 'gpu', 'model': 'geforce rtx 4090', 'vendor': 'nvidia', 'memory_total': 25757220864}


To get CPU info, just simply using 'cpu' to create a new Device object. then you can get all infos

```py
from device_smi import Device

smi = Device("cpu")
info = smi.info()
print(info)
```

result:

> {'type': 'cpu', 'model': 'epyc 7443', 'vendor': 'amd', 'memory_total': 1000000000000, 'features': ['3dnowprefetch', 'abm', 'adx', 'aes', 'amd_ppin', 'aperfmperf', 'apic', 'arat', 'avx', 'avx2', 'bmi1', 'bmi2', 'bpext', 'brs', 'cat_l3', 'cdp_l3', 'clflush', 'clflushopt', 'clwb', 'clzero', 'cmov', 'cmp_legacy', 'constant_tsc', 'cpb', 'cpuid', 'cqm', 'cqm_llc', 'cqm_mbm_local', 'cqm_mbm_total', 'cqm_occup_llc', 'cr8_legacy', 'cx16', 'cx8', 'de', 'debug_swap', 'decodeassists', 'erms', 'extapic', 'extd_apicid', 'f16c', 'flushbyasid', 'fma', 'fpu', 'fsgsbase', 'fsrm', 'fxsr', 'fxsr_opt', 'ht', 'hw_pstate', 'ibpb', 'ibrs', 'ibs', 'invpcid', 'irperf', 'lahf_lm', 'lbrv', 'lm', 'mba', 'mca', 'mce', 'misalignsse', 'mmx', 'mmxext', 'monitor', 'movbe', 'msr', 'mtrr', 'mwaitx', 'nonstop_tsc', 'nopl', 'npt', 'nrip_save', 'nx', 'ospke', 'osvw', 'overflow_recov', 'pae', 'pat', 'pausefilter', 'pcid', 'pclmulqdq', 'pdpe1gb', 'perfctr_core', 'perfctr_llc', 'perfctr_nb', 'pfthreshold', 'pge', 'pku', 'pni', 'popcnt', 'pse', 'pse36', 'rapl', 'rdpid', 'rdpru', 'rdrand', 'rdseed', 'rdt_a', 'rdtscp', 'rep_good', 'sep', 'sha_ni', 'skinit', 'smap', 'smca', 'smep', 'ssbd', 'sse', 'sse2', 'sse4_1', 'sse4_2', 'sse4a', 'ssse3', 'stibp', 'succor', 'svm', 'svm_lock', 'syscall', 'tce', 'topoext', 'tsc', 'tsc_scale', 'umip', 'user_shstk', 'v_spec_ctrl', 'v_vmsave_vmload', 'vaes', 'vgif', 'vmcb_clean', 'vme', 'vmmcall', 'vpclmulqdq', 'wbnoinvd', 'wdt', 'xgetbv1', 'xsave', 'xsavec', 'xsaveerptr', 'xsaveopt', 'xsaves', 'xtopology']}

## Roadmap

- Support Non-Apple ARM
- Support AMD GPU
- Support Intel/Gaudi
- Support Google/TPU
- Add PCIE property info to GPU/XPU
- Add NPU support (ARM/Intel/AMD)
- Add Non-Linux/MacOS support (BSD/Sun)
