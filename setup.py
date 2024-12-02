from setuptools import setup, find_packages

__version__ = "0.3.0"

setup(
    name="device-smi",
    version=__version__,
    author="ModelCloud",
    author_email="qubitium@modelcloud.ai",
    description="Retrieve gpu, cpu, and npu device info and properties from Linux/MacOS with zero package dependency.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ModelCloud/Device-SMI/",
    packages=find_packages(),
    install_requires=[],
    platform=["linux"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
)
