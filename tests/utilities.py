__author__ = "smiley"
"""
Tests common, global utilities in use throughout steamapi.
"""
import os
import sys
import unittest

# Allow us to import "steamapi", which is one level above.
sys.path += ['..']

from steamapi.core import APIResponse


def match_APIResponse(instance, original_dictionary):
    


class TestAPIResponse(unittest.TestCase):
    def test_basicWrapping(self):
        
        