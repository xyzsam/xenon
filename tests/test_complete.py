# End-to-end tests.

import json
import os
import shutil
import unittest

from xenon.xenon_interpreter import XenonInterpreter

TEST_DIR = "tests/test_sweeps"
EXPECTED_OUTPUT_DIR = os.path.join(TEST_DIR, "expected_output")

class Common(object):
  class CompleteSweepTest(unittest.TestCase):
    def runTest(self):
      self.genfiles = []
      interpreter = XenonInterpreter(os.path.join(TEST_DIR, self.testcase))
      self.genfiles = interpreter.run()

      expected_fname = os.path.join(EXPECTED_OUTPUT_DIR, os.path.basename(self.genfiles[0]))
      with open(expected_fname, "r") as e:
        expected = json.load(e)
      with open(self.genfiles[0], "r") as o:
        output = json.load(o)
      self.assertEqual(expected, output)

    def tearDown(self):
      if len(self.genfiles):
        output_dir = os.path.dirname(self.genfiles[0])
        shutil.rmtree(output_dir)

class SimpleSweepParam(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "single_sweep_param.xe"

class MultiSweepParam(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "multi_sweep_param.xe"

class BigSweepParam(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "big_sweep_param.xe"

class SelectionsSweep0(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "sweep_with_selections_0.xe"

class SelectionsSweep1(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "sweep_with_selections_1.xe"

class SelectionsSweep2(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "sweep_with_selections_2.xe"

class ExpressionSweep(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "expression_with_sweep.xe"

class SourceCommand(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "source_test.xe"

class MultiUseCommands(Common.CompleteSweepTest):
  def setUp(self):
    self.testcase = "multi_use_commands.xe"

if __name__ == '__main__':
  unittest.main()
