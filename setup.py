from setuptools import setup, find_packages

setup(
    name='tokmon',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'mitmproxy',
        'tiktoken',
    ],
    entry_points={
        'console_scripts': [
            "tokmon = cli:cli",
        ],
    },
)
