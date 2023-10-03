try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from xuiclient import __version__

with open("README.md", "r") as f:
    desc = f.read()

setup(
    name="xuiclient",
    version=__version__,
    description="Rich-feature and easy-to-use XUI client",
    long_description=desc,
    long_description_content_type = "text/markdown",
    author="awolverp",
    author_email="awolverp@gmail.com",
    url="https://github.com/awolverp/xuiclient",
    packages=['xuiclient'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ]
)
