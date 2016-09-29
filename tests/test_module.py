# A fake sweep environment for testing purposes.
#
# This is implemented as a module to also enable testing the use command.

from xenon.base.datatypes import *

int_param = IntParam("int_param", 0)
str_param = StrParam("str_param", "a")
inner0_param = IntParam("inner0_param", 0)
inner1_param = IntParam("inner1_param", 0)

class FakeDesignSweep(BaseDesignSweep):
  sweepable_params = [int_param, str_param]
  def __init__(self, name):
    super(FakeDesignSweep, self).__init__(name)

class FakeSweepable(Sweepable):
  sweepable_params = [int_param, str_param, inner0_param, inner1_param]
  def __init__(self, name):
    super(FakeSweepable, self).__init__(name)

def createFakeSweepEnviron():
  """ Builds the following class attribute structure:

  self.sweep = {
      "int_param": 0,
      "str_param": "a",
      "top0": "a top value",
      "top1": {
        "int_param": 0,
        "middle0": "a middle value",
        "middle1": {
          "low0": "a low value",
          "low1": "another low value",
          "int_param": 0,
          "str_param": "a",
          }
        "middle2": {
          "low0": "a second low value",
          "low1": "another second low value",
          "int_param": 0,
          "str_param": "a",
          }
      }
  }
  """
  middle1 = FakeSweepable("middle1")
  middle1.low0 = "a low value"
  middle1.low1 = "another low value"
  middle2 = FakeSweepable("middle2")
  middle2.low0 = "a second low value"
  middle2.low1 = "another second low value"
  top1 = FakeSweepable("top1")
  top1.middle0 = "a middle value"
  top1.middle1 = middle1
  top1.middle2 = middle2
  sweep = FakeDesignSweep("mysweep")
  sweep.top0 = "a top value"
  sweep.top1 = top1
  return sweep

USE_COMMAND_SWEEP_TEST_OBJ = createFakeSweepEnviron()
