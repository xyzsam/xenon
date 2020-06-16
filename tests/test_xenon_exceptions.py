# Unit tests to verify the right exceptions are raised.
#
# This only does some basic tests. Some exceptions are only raised under more
# complex scenarios, and those are left for end-to-end tests.

import unittest

from xenon.base.datatypes import *
import xenon.base.exceptions as xe
from xenon.tests.test_xenon_commands import CommandTestCase

class ParamExceptions(CommandTestCase):
  def test_invalid_default_type(self):
    self.assertRaises(TypeError, IntParam, "name", "not_an_int")
    self.assertRaises(TypeError, IntParam, "name", "not_an_int")
    self.assertRaises(TypeError, StrParam, "name", -1)
    self.assertRaises(TypeError, BoolParam, "name", 100)

  def test_invalid_valid_opt_type(self):
    self.assertRaises(TypeError, IntParam, "name", 0, [0, True, "not_an_int"])
    self.assertRaises(TypeError, StrParam, "name", "value", [0, True, "str"])
    self.assertRaises(TypeError, BoolParam, "name", False, [0, True, "str"])

class SweepableExceptions(CommandTestCase):
  def test_sweep_range(self):
    self.assertRaises(xe.XenonInvalidStepTypeError,
        self.sweep.setSweepParameter, "sweep_param", 0, 1, 1, "step")

    self.assertRaises(xe.XenonInvalidStepAmountError,
        self.sweep.setSweepParameter, "sweep_param", 0, 2, 0, "linstep")
    self.assertRaises(xe.XenonInvalidStepAmountError,
        self.sweep.setSweepParameter, "sweep_param", 1, 2, 1, "expstep")

    self.assertRaises(ValueError,
        self.sweep.setSweepParameter, "sweep_param", 0, 2, 2, "expstep")

  def test_validate_no_generator(self):
    self.sweep.addGenerateOutput("some_output")
    self.assertRaises(AttributeError, self.sweep.validate)

  def test_validate_invalid_generator(self):
    self.sweep.generate_fake = 0
    self.sweep.addGenerateOutput("fake")
    self.assertRaises(TypeError, self.sweep.validate)

  def test_not_initialized(self):
    sweep = BaseDesignSweep()
    self.assertRaises(xe.SweepNotInitializedError, sweep.checkInitializedAndRaise_)

class CommandExceptions(CommandTestCase):
  def test_selections(self):
    self.assertRaises(TypeError,
        self.executeCommand, "for top1.middle0.*", command_type=KW_FOR)
    self.assertRaises(xe.XenonSelectionError,
        self.executeCommand, "for top1.bad_attr", command_type=KW_FOR)
    self.sweep = 0
    self.assertRaises(TypeError, "0 is not of type XenonObj",
      self.executeCommand, "for *", command_type=KW_FOR)

  def test_begin(self):
    self.sweep = None  # Begin requires the sweep obj to be None.
    self.assertRaises(xe.XenonTypeError,
        self.executeCommand, "begin BadSweepType sweep")

  def test_set(self):
    self.assertRaises(xe.XenonEmptySelectionError,
        self.executeCommand, "set some_attr 0")
    self.assertRaises(xe.XenonSelectionError,
        self.executeCommand, "set some_attr for mysweep 0")
    self.sweep = 0
    self.assertRaises(TypeError,
        self.executeCommand, "set int_param for top1 1")

  def test_use(self):
    self.assertRaises(xe.XenonImportError,
        self.executeCommand, "use bad_package")

class ExpressionExceptions(CommandTestCase):
  def test_env_not_xenonobj(self):
    self.sweep = 0
    self.assertRaises(TypeError, "0 is not of type XenonObj",
        self.executeCommand, "set int_param for top1 1")

  @unittest.skip("Attributes that have not been set are assigned value None.")
  def test_bad_selection(self):
    self.assertRaises(xe.XenonSelectionError,
        self.executeCommand, "set int_param for top1 top1.middle2.int_param")


if __name__ == "__main__":
  unittest.main()
