import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

tests_require = [
    'pytest-cov',
    'pytest',
    ]

setup(name='kemi',
      version='0.1dev',
      description="",
      long_description=README,
      classifiers=[
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python",
        ],
      author='Daniel Nouri and Jure Cerjak',
      author_email='daniel.nouri@gmail.com',
      url='http://pypi.python.org/pypi/kemi',
      license="MIT License",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=['SQLAlchemy'] + tests_require,
      )
