from setuptools import setup

setup(
    name='pachyderm-ide-authenticator',
    version='0.1.0',
    license='Apache 2.0',
    packages=['pachyderm_authenticator'],
    install_requires=[
        'python-pachyderm>=4.0.0',
    ],
)