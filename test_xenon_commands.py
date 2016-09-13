# A suite of unit tests for command execution.

import pyparsing as pp
import sys
import unittest

from params import Param
from parsers import *
from commands import *
from base_datatypes import DesignSweep
from datatypes import Benchmark, Sweepable
import command_bindings

fake_param = Param("sweep_param", 0)
class FakeDesignSweep(DesignSweep):
  sweepable_params = DesignSweep.sweepable_params + [fake_param]
  def __init__(self, name):
    super(FakeDesignSweep, self).__init__(name)

def createFakeSweepEnviron(sweep):
  # Builds the following class attribute structure:
  # self.sweep = {
  #     "sweep_param": 0,
  #     "top0": "a top value",
  #     "top1": {
  #       "sweep_param": 0,
  #       "middle0": "a middle value",
  #       "middle1": {
  #         "low0": "a low value",
  #         "low1": "another low value",
  #         "sweep_param": 0,
  #         }
  #       "middle2": {
  #         "low0": "a second low value",
  #         "low1": "another second low value",
  #         "sweep_param": 0,
  #         }
  #     }
  # }
  middle1 = FakeDesignSweep("middle1")
  middle1.low0 = "a low value"
  middle1.low1 = "another low value"
  middle2 = FakeDesignSweep("middle2")
  middle2.low0 = "a second low value"
  middle2.low1 = "another second low value"
  top1 = FakeDesignSweep("top1")
  top1.middle0 = "a middle value"
  top1.middle1 = middle1
  top1.middle2 = middle2
  sweep.top0 = "a top value"
  sweep.top1 = top1

class CommandTestCase(unittest.TestCase):
  def setUp(self):
    self.sweep = FakeDesignSweep("mysweep")

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

class SelectionCommand(CommandTestCase):
  def setUp(self):
    super(SelectionCommand, self).setUp()
    createFakeSweepEnviron(self.sweep)

  def test_non_recursive(self):
    selected_objs = self.executeCommand("", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 1)
    self.assertEqual(selected_objs[0], self.sweep)

    selected_objs = self.executeCommand("for *", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 1)
    self.assertIn(self.sweep.top1, selected_objs)
    self.assertNotIn(self.sweep.top0, selected_objs)

    selected_objs = self.executeCommand("for top1.*", command_type=KW_FOR)
    self.assertEqual(len(selected_objs), 2)
    self.assertIn(self.sweep.top1.middle1, selected_objs)
    self.assertIn(self.sweep.top1.middle2, selected_objs)

    with self.assertRaises(xe.NotXenonObjError):
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
    createFakeSweepEnviron(self.sweep)

  def test_simple(self):
    """ Simple == no selections or expressions. """
    self.executeCommand("set output_dir \"path\"")
    self.assertEqual(self.sweep.output_dir, "path")

    self.executeCommand("set output_dir \"path/to/output\"")
    self.assertEqual(self.sweep.output_dir, "path/to/output")

  def test_set_with_selections(self):
    self.executeCommand("set sweep_param for * 3")
    self.assertEqual(self.sweep.sweep_param, 0)
    self.assertEqual(self.sweep.top1.sweep_param, 3)
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 0)

    self.executeCommand("set sweep_param for * \"astring\"")
    self.assertEqual(self.sweep.sweep_param, 0)
    self.assertEqual(self.sweep.top1.sweep_param, "astring")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 0)

    self.executeCommand("set sweep_param for top1 4")
    self.assertEqual(self.sweep.top1.sweep_param, 4)
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 0)

  def test_set_with_nested_selections(self):
    self.executeCommand("set sweep_param for top1.middle1 3")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 3)
    self.assertEqual(self.sweep.top1.middle2.sweep_param, 0)
    self.assertEqual(self.sweep.top1.sweep_param, 0)

    self.executeCommand("set sweep_param for top1.* 4")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, 4)
    self.assertEqual(self.sweep.top1.middle2.sweep_param, 4)
    self.assertEqual(self.sweep.top1.sweep_param, 0)

    self.executeCommand("set sweep_param for top1.* \"mystring\"")
    self.assertEqual(self.sweep.top1.middle1.sweep_param, "mystring")
    self.assertEqual(self.sweep.top1.middle2.sweep_param, "mystring")
    self.assertEqual(self.sweep.top1.sweep_param, 0)

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
    createFakeSweepEnviron(self.sweep)

  def test_global_sweep(self):
    self.executeCommand("sweep sweep_param from 1 to 8 linstep 2")
    self.assertIn("sweep_param", self.sweep.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.sweep_params_range)
    self.assertEqual(self.sweep.sweep_params_range["sweep_param"], [1,3,5,7])

    self.executeCommand("sweep sweep_param from 1 to 8 expstep 2")
    self.assertIn("sweep_param", self.sweep.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.sweep_params_range)
    self.assertEqual(self.sweep.sweep_params_range["sweep_param"], [1,2,4,8])

    self.executeCommand("sweep sweep_param from 4 to 16 expstep 3")
    self.assertIn("sweep_param", self.sweep.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.sweep_params_range)
    self.assertEqual(self.sweep.sweep_params_range["sweep_param"], [4, 12])

  def test_selective_sweeps(self):
    self.executeCommand("sweep sweep_param for * from 1 to 8 linstep 1")
    self.assertIn("sweep_param", self.sweep.top1.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.middle1.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.middle2.sweep_params_range)
    self.assertEqual(self.sweep.top1.sweep_params_range["sweep_param"], [1,2,3,4,5,6,7,8])

    self.executeCommand("sweep sweep_param for top1 from 2 to 5 linstep 1")
    self.assertIn("sweep_param", self.sweep.top1.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.middle1.sweep_params_range)
    self.assertNotIn("sweep_param", self.sweep.top1.middle2.sweep_params_range)
    self.assertEqual(self.sweep.top1.sweep_params_range["sweep_param"], [2,3,4,5])

    self.executeCommand("sweep sweep_param for top1.* from 4 to 7 linstep 1")
    self.assertIn("sweep_param", self.sweep.top1.middle1.sweep_params_range)
    self.assertIn("sweep_param", self.sweep.top1.middle2.sweep_params_range)
    self.assertEqual(self.sweep.top1.middle1.sweep_params_range["sweep_param"], [4,5,6,7])
    self.assertEqual(self.sweep.top1.middle2.sweep_params_range["sweep_param"], [4,5,6,7])

  def test_recursive_sweeps(self):
    self.executeCommand("sweep sweep_param for top1.** from 1 to 4 expstep 2")
    self.assertIn("sweep_param", self.sweep.top1.sweep_params_range)
    self.assertIn("sweep_param", self.sweep.top1.middle1.sweep_params_range)
    self.assertIn("sweep_param", self.sweep.top1.middle2.sweep_params_range)
    self.assertEqual(self.sweep.top1.sweep_params_range["sweep_param"], [1,2,4])
    self.assertEqual(self.sweep.top1.middle1.sweep_params_range["sweep_param"], [1,2,4])
    self.assertEqual(self.sweep.top1.middle2.sweep_params_range["sweep_param"], [1,2,4])

if __name__ == "__main__":
  unittest.main()
