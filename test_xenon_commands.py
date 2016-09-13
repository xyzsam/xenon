# A suite of unit tests for command execution.

import pyparsing as pp
import sys
import unittest

from parsers import *
from commands import *
from datatypes import DesignSweep
import command_bindings

def createFakeSweepEnviron(sweep):
  # Builds the following class attribute structure:
  # self.sweep = {
  #     "common": None,
  #     "top0": "a top value",
  #     "top1": {
  #       "middle0": "a middle value",
  #       "middle1": {
  #         "low0": "a low value",
  #         "low1": "another low value",
  #         "common": None,
  #         }
  #       "middle2": {
  #         "low0": "a second low value",
  #         "low1": "another second low value",
  #         "common": None,
  #         }
  #     }
  # }
  middle1 = DesignSweep("middle1")
  middle1.low0 = "a low value"
  middle1.low1 = "another low value"
  middle1.common = None
  middle2 = DesignSweep("middle2")
  middle2.low0 = "a second low value"
  middle2.low1 = "another second low value"
  middle2.common = None
  top1 = DesignSweep("top1")
  top1.middle0 = "a middle value"
  top1.middle1 = middle1
  top1.middle2 = middle2
  top1.common = None
  sweep.top0 = "a top value"
  sweep.top1 = top1

class CommandTestCase(unittest.TestCase):
  def setUp(self):
    self.sweep = DesignSweep("mysweep")

  def executeCommand(self, command, command_type=None):
    """ Execute the command.

    The type of command is usually determined from the first word in the command.
    This can be overridden by passing the command_type keyword argument to be one
    of CMD_*, as defined in parser.py.
    """
    if not command_type:
      command_type = command.split()[0]
    parser = command_bindings.getParser(command_type)
    results = parser.parseString(command)
    command = command_bindings.getCommandClass(command_type)(0, results)
    return command(self.sweep)

class BeginAndEndCommands(CommandTestCase):
  def runTest(self):
    self.executeCommand("begin sweep mysweep")
    self.assertEqual(self.sweep.name, "mysweep")
    self.assertEqual(self.sweep.sweep_type, None)

    self.executeCommand("end sweep")
    self.assertEqual(self.sweep.done, True)

class UseCommand(CommandTestCase):
  def runTest(self):
    sys.path.append("/group/vlsiarch/samxi/active_projects/gem5-stable/sweeps")
    self.executeCommand("use benchmark_configs.machsuite_config")
    self.assertIn("aes_aes", self.sweep.__dict__)
    self.assertIn("md_knn",self.sweep.__dict__)
    self.assertIn("DMA", self.sweep.__dict__)

class SetCommand(CommandTestCase):
  def setUp(self):
    super(SetCommand, self).setUp()
    createFakeSweepEnviron(self.sweep)

  def test_simple(self):
    """ Simple == no selections or expressions. """
    self.executeCommand("set output_dir \"path\"")
    self.assertEqual(self.sweep.output_dir, "path")

    self.executeCommand("set output_dir \"path/to/output\"")
    self.assertEqual(self.sweep.output_dir, "path/to/output")

  def test_set_with_selections(self):
    self.executeCommand("set common for * 3")
    self.assertEqual(self.sweep.top1.common, 3)
    self.assertEqual(self.sweep.top1.middle1.common, None)

    self.executeCommand("set common for * \"astring\"")
    self.assertEqual(self.sweep.top1.common, "astring")
    self.assertEqual(self.sweep.top1.middle1.common, None)

    self.executeCommand("set common for top1 4")
    self.assertEqual(self.sweep.top1.common, 4)
    self.assertEqual(self.sweep.top1.middle1.common, None)

  def test_set_with_nested_selections(self):
    self.executeCommand("set common for top1.middle1 3")
    self.assertEqual(self.sweep.top1.middle1.common, 3)
    self.assertEqual(self.sweep.top1.middle2.common, None)
    self.assertEqual(self.sweep.top1.common, None)

    self.executeCommand("set common for top1.* 4")
    self.assertEqual(self.sweep.top1.middle1.common, 4)
    self.assertEqual(self.sweep.top1.middle2.common, 4)
    self.assertEqual(self.sweep.top1.common, None)

    self.executeCommand("set common for top1.* \"mystring\"")
    self.assertEqual(self.sweep.top1.middle1.common, "mystring")
    self.assertEqual(self.sweep.top1.middle2.common, "mystring")
    self.assertEqual(self.sweep.top1.common, None)

class SelectionCommand(CommandTestCase):
  def setUp(self):
    super(SelectionCommand, self).setUp()
    createFakeSweepEnviron(self.sweep)

  def runTest(self):
    selected_objs = self.executeCommand("", command_type=KW_FOR)
    self.assertEqual(selected_objs[0], self.sweep)

    selected_objs = self.executeCommand("for *", command_type=KW_FOR)
    self.assertIn(self.sweep.top0, selected_objs)
    self.assertIn(self.sweep.top1, selected_objs)

    selected_objs = self.executeCommand("for top1.*", command_type=KW_FOR)
    self.assertIn(self.sweep.top1.middle0, selected_objs)

    selected_objs = self.executeCommand("for top1.middle0", command_type=KW_FOR)
    self.assertIn(self.sweep.top1.middle0, selected_objs)

if __name__ == "__main__":
  unittest.main()
