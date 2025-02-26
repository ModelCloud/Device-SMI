from pathlib import Path

from setuptools import find_packages, setup

__version__ = "0.4.0"

setup(
    name="device-smi",
    version=__version__,
    author="ModelCloud",
    author_email="qubitium@modelcloud.ai",
    description="Retrieve gpu, cpu, and npu device info and properties from Linux/MacOS with zero package dependency.",
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="UTF-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/ModelCloud/Device-SMI/",
    packages=find_packages(),
    install_requires=[],
    platform=["linux", "windows", "darwin", "solaris", "freebsd"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
)
