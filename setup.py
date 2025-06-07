from setuptools import setup, find_packages
#python setup.py sdist bdist_wheel.

exec(open('yourpackage/version.py').read())
setup(
       name='qstrader',
       version= __version__,
       packages=find_packages(),
       install_requires=[
           # List dependencies if any
       ],
   )