# A suite of unit tests for command execution.

import numpy as np
import unittest

import xenon.base.parser
import xenon.base.globalscope as g
from xenon.base.commands import *
from xenon.base.datatypes import Param

from xenon.tests import test_module

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
    command_parser = xenon.base.parser.getParser(command_type)
    results = command_parser.parseString(command_str)
    command = xenon.base.parser.getCommandClass(command_type)(0, command_str, results)
    return command(self.sweep)

class BeginAndEndCommands(CommandTestCase):
  def runTest(self):
    # The begin command requires that sweep = None.
    self.sweep = None
    self.sweep = self.executeCommand("begin ExhaustiveSweep mysweep")
    self.assertEqual(self.sweep.name, "mysweep")

    self.executeCommand("end sweep")
    self.assertTrue(self.sweep.isDone())

class UseCommand(CommandTestCase):
  def test_normal(self):
    # Must import fully qualified name while we are under tests/.
    self.executeCommand("use xenon.tests.test_module.*")
    self.assertIn("USE_COMMAND_SWEEP_TEST_OBJ", self.sweep.__dict__)

  def test_global_import(self):
    """ Tests importing into global scope before a sweep is declared. """
    self.sweep = None
    self.executeCommand("use xenon.tests.test_module.*")
    self.assertIn("FakeDesignSweep", g.scope.__dict__)
    self.assertEqual(test_module.FakeDesignSweep, g.scope.__dict__["FakeDesignSweep"])

class SelectionCommand(CommandTestCase):
  def setUp(self):
    super(SelectionCommand, self).setUp()

  def runTests(self):
    selected_objs = self.executeCommand("for *", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 4)
    self.assertIn(self.sweep.top1, selected_objs)
    self.assertIn(self.sweep.top1.middle1, selected_objs)
    self.assertIn(self.sweep.top1.middle2, selected_objs)

    selected_objs = self.executeCommand("for top1.*", command_type=KW_FOR)
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

    self.executeCommand("set output_dir ['a','b','c']")
    self.assertEqual(self.sweep.output_dir, ["a", "b", "c"])

    self.executeCommand("set output_dir [0,1,2]")
    self.assertEqual(self.sweep.output_dir, [0,1,2])

    self.executeCommand("set output_dir [True,False,True]")
    self.assertEqual(self.sweep.output_dir, [True, False, True])

    self.executeCommand("set output_dir [0,False,\"s\"]")
    self.assertEqual(self.sweep.output_dir, [0, False, "s"])

  def test_set_with_selections(self):
    self.executeCommand("set int_param for * 3")
    self.assertEqual(self.sweep.int_param, 3)
    self.assertEqual(self.sweep.top1.int_param, 3)
    self.assertEqual(self.sweep.top1.middle1.int_param, 3)
    self.assertEqual(self.sweep.top1.middle2.int_param, 3)

    self.executeCommand("set str_param for * \"astring\"")
    self.assertEqual(self.sweep.str_param, "astring")
    self.assertEqual(self.sweep.top1.str_param, "astring")
    self.assertEqual(self.sweep.top1.middle1.str_param, "astring")
    self.assertEqual(self.sweep.top1.middle2.str_param, "astring")

    self.executeCommand("set int_param for top1 4")
    self.assertEqual(self.sweep.top1.int_param, 4)
    self.assertEqual(self.sweep.top1.middle1.int_param, 3)

  def test_set_with_nested_selections(self):
    self.executeCommand("set int_param for top1.* 4")
    self.assertEqual(self.sweep.top1.middle1.int_param, 4)
    self.assertEqual(self.sweep.top1.middle2.int_param, 4)
    self.assertEqual(self.sweep.top1.int_param, 4)

    self.executeCommand("set int_param for top1.middle1 3")
    self.assertEqual(self.sweep.top1.middle1.int_param, 3)
    # These two remain unchanged.
    self.assertEqual(self.sweep.top1.middle2.int_param, 4)
    self.assertEqual(self.sweep.top1.int_param, 4)

    self.executeCommand("set str_param for top1.* \"mystring\"")
    self.assertEqual(self.sweep.top1.middle1.str_param, "mystring")
    self.assertEqual(self.sweep.top1.middle2.str_param, "mystring")
    self.assertEqual(self.sweep.top1.str_param, "mystring")

class Expressions(CommandTestCase):
  def test_simple_expressions(self):
    self.executeCommand("set int_param 3")
    self.executeCommand("set int_param for top1 2")
    self.assertEqual(self.sweep.int_param, 3)
    self.assertEqual(self.sweep.top1.int_param, 2)

    self.executeCommand("set int_param 1")
    self.assertEqual(self.sweep.int_param, 1)

    self.executeCommand("set int_param for top1 int_param")
    self.assertEqual(self.sweep.top1.int_param, self.sweep.int_param)

    self.executeCommand("set int_param for top1 int_param + 3")
    self.assertEqual(self.sweep.top1.int_param, 4)

    self.executeCommand("set int_param for top1.middle1 top1.int_param + 3")
    self.assertEqual(self.sweep.top1.middle1.int_param, 7)

    # IntParam should be only int, but since this is Python, the user can do
    # whatever they like. In the real scenario, we should catch this type error
    # during validation.
    self.executeCommand("set int_param for top1.middle1 top1.int_param + 3.3")
    self.assertAlmostEqual(self.sweep.top1.middle1.int_param, 7.3)

    self.executeCommand("set int_param for top1.middle1 top1.int_param - 3.3")
    self.assertAlmostEqual(self.sweep.top1.middle1.int_param, 0.7)

    self.executeCommand("set int_param for top1 int_param / 3")
    self.assertAlmostEqual(self.sweep.top1.int_param, 1.0/3)

    self.executeCommand("set int_param for top1 int_param * 5")
    self.assertAlmostEqual(self.sweep.top1.int_param, 5)

  def test_compare_expressions(self):
    self.executeCommand("set int_param 1")
    self.assertEqual(self.sweep.int_param, 1)

    self.executeCommand("set int_param for top1 int_param == 1")
    self.assertTrue(self.sweep.top1.int_param)

    self.executeCommand("set int_param for top1 int_param > 5")
    self.assertFalse(self.sweep.top1.int_param)

    self.executeCommand("set int_param for top1 int_param > 0")
    self.assertTrue(self.sweep.top1.int_param)

    self.executeCommand("set int_param for top1 int_param >= 1")
    self.assertTrue(self.sweep.top1.int_param)

    self.executeCommand("set int_param for top1 int_param <= 1")
    self.assertTrue(self.sweep.top1.int_param)

    self.executeCommand("set int_param for top1 int_param < 0")
    self.assertFalse(self.sweep.top1.int_param)

    self.executeCommand("set int_param for top1 int_param != 0")
    self.assertTrue(self.sweep.top1.int_param)

  def test_nested_expressions(self):
    self.executeCommand("set int_param 10")
    self.executeCommand("set int_param for top1 5")
    self.assertEqual(self.sweep.int_param, 10)
    self.assertEqual(self.sweep.top1.int_param, 5)

    self.executeCommand("set int_param for top1 (int_param * 5) - 3")
    self.assertAlmostEqual(self.sweep.top1.int_param, 47)

    self.executeCommand("set int_param for top1 (int_param * 5) / 10")
    self.assertAlmostEqual(self.sweep.top1.int_param, 5)

    self.executeCommand(
        "set int_param for top1.middle1 (top1.int_param * 5) / (int_param)")
    self.assertAlmostEqual(self.sweep.top1.middle1.int_param, 2.5)

    self.executeCommand(
        "set int_param for top1.middle1 (top1.int_param * 5) / (int_param - 1)")
    self.assertAlmostEqual(self.sweep.top1.middle1.int_param, 25/9.0)

    self.executeCommand(
        "set int_param for top1.middle1 (top1.int_param * 5) / (top1.int_param - 1)")
    self.assertAlmostEqual(self.sweep.top1.middle1.int_param, 25/4.0)

  def test_expressions_with_lists(self):
    self.executeCommand("set int_param [1,2,3]")
    self.executeCommand("set int_param for top1 [2,3,4]")

    self.executeCommand("set int_param for top1.middle1 top1.int_param + int_param")
    self.assertTrue(np.array_equal(self.sweep.top1.middle1.int_param, [3,5,7]))

    self.executeCommand("set int_param for top1.middle1 top1.int_param - int_param")
    self.assertTrue(np.array_equal(self.sweep.top1.middle1.int_param, [1,1,1]))

    self.executeCommand("set int_param for top1.middle1 top1.int_param * 10")
    self.assertTrue(np.array_equal(self.sweep.top1.middle1.int_param, [20,30,40]))

    self.executeCommand("set int_param for top1.middle1 top1.int_param / 2")
    self.assertTrue(np.array_equal(self.sweep.top1.middle1.int_param, [1,1.5,2]))

    self.executeCommand("set int_param for top1.middle1 top1.int_param + 10")
    self.assertTrue(np.array_equal(self.sweep.top1.middle1.int_param, [12,13,14]))

    self.executeCommand("set int_param for top1.middle1 top1.int_param - 10")
    self.assertTrue(np.array_equal(self.sweep.top1.middle1.int_param, [-8,-7,-6]))

class SweepCommand(CommandTestCase):
  def setUp(self):
    super(SweepCommand, self).setUp()

  def test_global_sweep(self):
    self.executeCommand("sweep int_param from 1 to 8 linstep 2")
    self.assertTrue(self.sweep.hasSweepParamRange("int_param"))
    self.assertTrue(self.sweep.top1.hasSweepParamRange("int_param"))
    self.assertTrue(self.sweep.top1.middle1.hasSweepParamRange("int_param"))
    self.assertTrue(self.sweep.top1.middle2.hasSweepParamRange("int_param"))
    self.assertEqual(self.sweep.getSweepParamRange("int_param"), [1,3,5,7])
    self.assertEqual(self.sweep.top1.getSweepParamRange("int_param"), [1,3,5,7])
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("int_param"), [1,3,5,7])
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("int_param"), [1,3,5,7])

    # Don't need to re-test everything we already did above.
    self.executeCommand("sweep int_param from 1 to 8 expstep 2")
    self.assertTrue(self.sweep.hasSweepParamRange("int_param"))
    self.assertEqual(self.sweep.getSweepParamRange("int_param"), [1,2,4,8])

    self.executeCommand("sweep int_param from 4 to 16 expstep 3")
    self.assertTrue(self.sweep.hasSweepParamRange("int_param"))
    self.assertEqual(self.sweep.getSweepParamRange("int_param"), [4, 12])

    self.executeCommand("sweep int_param [1,4,6,9]")
    self.assertTrue(self.sweep.getSweepParamRange("int_param"), [1,4,6,9])

  def test_selective_sweeps(self):
    self.executeCommand("sweep int_param for * from 1 to 8 linstep 1")
    self.assertTrue(self.sweep.top1.hasSweepParamRange("int_param"))
    self.assertTrue(self.sweep.top1.middle1.hasSweepParamRange("int_param"))
    self.assertTrue(self.sweep.top1.middle2.hasSweepParamRange("int_param"))
    self.assertEqual(self.sweep.top1.getSweepParamRange("int_param"), [1,2,3,4,5,6,7,8])

    self.executeCommand("sweep int_param for top1 from 2 to 5 linstep 1")
    self.assertEqual(self.sweep.top1.getSweepParamRange("int_param"), [2,3,4,5])
    # These two should not be changed.
    self.assertEqual(self.sweep.getSweepParamRange("int_param"), [1,2,3,4,5,6,7,8])
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("int_param"), [1,2,3,4,5,6,7,8])

    self.executeCommand("sweep int_param for top1.* from 4 to 7 linstep 1")
    self.assertEqual(self.sweep.top1.middle1.getSweepParamRange("int_param"), [4,5,6,7])
    self.assertEqual(self.sweep.top1.middle2.getSweepParamRange("int_param"), [4,5,6,7])
    self.assertEqual(self.sweep.top1.getSweepParamRange("int_param"), [4,5,6,7])
    self.assertEqual(self.sweep.getSweepParamRange("int_param"), [1,2,3,4,5,6,7,8])

if __name__ == "__main__":
  unittest.main()
