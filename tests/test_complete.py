# End-to-end tests.

import filecmp
import os
import unittest

from xenon.xenon_interpreter import XenonInterpreter

TEST_DIR = "tests/test_sweeps"
EXPECTED_OUTPUT_DIR = os.path.join(TEST_DIR, "expected_output")
TEST_FILE = "test.out"

class Common(object):
  class CompleteSweepTest(unittest.TestCase):
    def runTest(self):
      with open(TEST_FILE, "w") as f:
        interpreter = XenonInterpreter(
            os.path.join(TEST_DIR, self.testcase), test_mode=True, stream=f)
        interpreter.run()

      output_name = os.path.join(EXPECTED_OUTPUT_DIR, self.testcase[:-6] + ".out")
      self.assertTrue(filecmp.cmp(TEST_FILE, output_name))

    def tearDown(self):
      os.remove(TEST_FILE)

class SimpleSweepParam(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "single_sweep_param.xenon"

class MultiSweepParam(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "multi_sweep_param.xenon"

class BigSweepParam(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "big_sweep_param.xenon"

class SelectionsSweep(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "sweep_with_selections.xenon"

if __name__ == '__main__':
  unittest.main()
