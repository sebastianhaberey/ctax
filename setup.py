from setuptools import setup

setup(
    name='ctax',
    version='0.8.0',
    description='Python crypto currency tax calculator',
    author='Sebastian Haberey',
    author_email='sebastian@haberey.com',
    license='MIT',
    python_requires='>=3',
    install_requires=['sqlalchemy', 'ccxt', 'python-dateutil', 'cryptocompy'],
)
