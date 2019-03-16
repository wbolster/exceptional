import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as fp:
    long_description = fp.read()

setup(
    name="exceptional",
    description="exception handling utilities",
    long_description=long_description,
    version="2.0.0",
    author="wouter bolsterlee",
    author_email="wouter@bolsterl.ee",
    url="https://github.com/wbolster/exceptional",
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    py_modules=["exceptional"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
