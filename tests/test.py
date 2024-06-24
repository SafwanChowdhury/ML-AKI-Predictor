#!/usr/bin/env python3
import unittest
from test_mllp import TestMllp
from test_database import TestDatabase

# Create a test suite
suite = unittest.TestLoader().loadTestsFromTestCase(TestMllp)
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDatabase))


# Run the test suite
unittest.TextTestRunner().run(suite)
