"""
Rich-feature and easy-to-use XUI client
"""

__version__ = "1.0.0"
__author__ = "awolverp"

# connection module
from . import connection

# structure types, and protocol types
from . import types, protocols

# Client
from .client import Client, LoginError, UnknownError
