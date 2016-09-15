# A suite of unit tests for command execution.

import pyparsing as pp
import unittest

import xenon.base.command_bindings as command_bindings
from xenon.base.commands import *
from xenon.base.datatypes import DesignSweep, Param
from xenon.base.parsers import *

import test_module

class CommandTestCase(unittest.TestCase):
  def setUp(self):
    self.sweep = test_module.createFakeSweepEnviron()

  def executeCommand(self, command_str, command_type=None):
    """ Execute the command.

    The type of command is usually determined from the first word in the command.
    This can be overridden by passing the command_type keyword argument to be one
    of CMD_*, as defined in parser.py.
    """
    if not command_type:
      command_type = command_str.split()[0]
    parser = command_bindings.getParser(command_type)
    results = parser.parseString(command_str)
    command = command_bindings.getCommandClass(command_type)(0, command_str, results)
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
    # Must import fully qualified name while we are under tests/.
    self.executeCommand("use xenon.tests.test_module")
    self.assertIn("USE_COMMAND_SWEEP_TEST_OBJ", self.sweep.__dict__)

class SelectionCommand(CommandTestCase):
  def setUp(self):
    super(SelectionCommand, self).setUp()

  def test_non_recursive(self):
    selected_objs = self.executeCommand("", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 4)
    self.assertIn(self.sweep, selected_objs)
    self.assertIn(self.sweep.top1, selected_objs)
    self.assertIn(self.sweep.top1.middle1, selected_objs)
    self.assertIn(self.sweep.top1.middle2, selected_objs)

    selected_objs = self.executeCommand("for *", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 2)
    self.assertIn(self.sweep, selected_objs)
    self.assertIn(self.sweep.top1, selected_objs)

    selected_objs = self.executeCommand("for top1.*", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 3)
    self.assertIn(self.sweep.top1.middle1, selected_objs)
    self.assertIn(self.sweep.top1.middle2, selected_objs)

    with self.assertRaises(TypeError):
      selected_objs = self.executeCommand("for top1.middle0", command_type=KW_FOR)
      self.assertEqual(len(selected_objs), 0)

  def test_recursive(self):
    selected_objs = self.executeCommand("for **", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 4)
    self.assertIn(self.sweep.top1, selected_objs)
    self.assertIn(self.sweep.top1.middle1, selected_objs)
    self.assertIn(self.sweep.top1.middle2, selected_objs)

    selected_objs = self.executeCommand("for top1.**", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 3)
    self.assertIn(self.sweep.top1, selected_objs)
    self.assertIn(self.sweep.top1.middle1, selected_objs)
    self.assertIn(self.sweep.top1.middle2, selected_objs)

class SetCommand(CommandTestCase):
  def setUp(self):
    super(SetCommand, self).setUp()

  def test_simple(self):
    """ Simple == no selections or expressions. """
    self.executeCommand("set output_dir \"path\"")
    self.assertEqual(self.sweep.output_dir, "path")

    self.executeCommand("set output_dir \"path/to/output\"")
    self.assertEqual(self.sweep.output_dir, "path/to/output")

  def test_set_with_selections(self):
    self.executeCommand("set sweep_param for * 3")
    self.assertEqual(self.sweep.sweep_param, 3)
    self.assertEqual(self.sweep.top1.sweep_param, 3)
    self.assertEqual(self.sweep.top1.middle1.sweep_param, None)

    self.executeCommand("set sweep_param for * \"astring\"")
    self.assertEqual(self.sweep.sweep_param, "astring")
    self.assertEqual(self.sweep.top1.sweep_param, "astring")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, None)

    self.executeCommand("set sweep_param for top1 4")
    self.assertEqual(self.sweep.top1.sweep_param, 4)
    self.assertEqual(self.sweep.top1.middle1.sweep_param, None)

  def test_set_with_nested_selections(self):
    self.executeCommand("set sweep_param for top1.middle1 3")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 3)
    self.assertEqual(self.sweep.top1.middle2.sweep_param, None)
    self.assertEqual(self.sweep.top1.sweep_param, None)

    self.executeCommand("set sweep_param for top1.* 4")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 4)
    self.assertEqual(self.sweep.top1.middle2.sweep_param, 4)
    self.assertEqual(self.sweep.top1.sweep_param, 4)

    self.executeCommand("set sweep_param for top1.* \"mystring\"")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, "mystring")
    self.assertEqual(self.sweep.top1.middle2.sweep_param, "mystring")
    self.assertEqual(self.sweep.top1.sweep_param, "mystring")

  def test_set_with_recursive_selections(self):
    self.executeCommand("set sweep_param for ** 4")
    self.assertEqual(self.sweep.sweep_param, 4)
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 4)
    self.assertEqual(self.sweep.top1.middle2.sweep_param, 4)

    self.executeCommand("set sweep_param for top1.** 7")
    self.assertEqual(self.sweep.sweep_param, 4)   # This is UNCHANGED.
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 7)
    self.assertEqual(self.sweep.top1.middle2.sweep_param, 7)

class SweepCommand(CommandTestCase):
  def setUp(self):
    super(SweepCommand, self).setUp()

  def test_global_sweep(self):
    self.executeCommand("sweep sweep_param from 1 to 8 linstep 2")
    self.assertTrue(self.sweep.hasSweepParamRange("sweep_param"))
    self.assertTrue(self.sweep.top1.hasSweepParamRange("sweep_param"))
    self.assertTrue(self.sweep.top1.middle1.hasSweepParamRange("sweep_param"))
    self.assertTrue(self.sweep.top1.middle2.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.getSweepParamRange("sweep_param"), [1,3,5,7])
    self.assertEqual(self.sweep.top1.getSweepParamRange("sweep_param"), [1,3,5,7])
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("sweep_param"), [1,3,5,7])
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("sweep_param"), [1,3,5,7])

    # Don't need to re-test everything we already did above.
    self.executeCommand("sweep sweep_param from 1 to 8 expstep 2")
    self.assertTrue(self.sweep.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.getSweepParamRange("sweep_param"), [1,2,4,8])

    self.executeCommand("sweep sweep_param from 4 to 16 expstep 3")
    self.assertTrue(self.sweep.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.getSweepParamRange("sweep_param"), [4, 12])

  def test_selective_sweeps(self):
    self.executeCommand("sweep sweep_param for * from 1 to 8 linstep 1")
    self.assertTrue(self.sweep.top1.hasSweepParamRange("sweep_param"))
    self.assertFalse(self.sweep.top1.middle1.hasSweepParamRange("sweep_param"))
    self.assertFalse(self.sweep.top1.middle2.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.top1.getSweepParamRange("sweep_param"), [1,2,3,4,5,6,7,8])

    self.executeCommand("sweep sweep_param for top1 from 2 to 5 linstep 1")
    self.assertTrue(self.sweep.top1.hasSweepParamRange("sweep_param"))
    self.assertFalse(self.sweep.top1.middle1.hasSweepParamRange("sweep_param"))
    self.assertFalse(self.sweep.top1.middle2.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.top1.getSweepParamRange("sweep_param"), [2,3,4,5])

    self.executeCommand("sweep sweep_param for top1.* from 4 to 7 linstep 1")
    self.assertTrue(self.sweep.top1.middle1.hasSweepParamRange("sweep_param"))
    self.assertTrue(self.sweep.top1.middle2.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("sweep_param"), [4,5,6,7])
    self.assertEqual(self.sweep.top1.middle2.getSweepParamRange("sweep_param"), [4,5,6,7])
    self.assertEqual(self.sweep.top1.getSweepParamRange("sweep_param"), [4,5,6,7])

  def test_recursive_sweeps(self):
    self.executeCommand("sweep sweep_param for top1.** from 1 to 4 expstep 2")
    self.assertTrue(self.sweep.top1.hasSweepParamRange("sweep_param"))
    self.assertTrue(self.sweep.top1.middle1.hasSweepParamRange("sweep_param"))
    self.assertTrue(self.sweep.top1.middle2.hasSweepParamRange("sweep_param"))
    self.assertEqual(self.sweep.top1.getSweepParamRange("sweep_param"), [1,2,4])
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("sweep_param"), [1,2,4])
    self.assertEqual(self.sweep.top1.middle2.getSweepParamRange("sweep_param"), [1,2,4])

if __name__ == "__main__":
  unittest.main()
