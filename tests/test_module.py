# A fake sweep environment for testing purposes.
#
# This is implemented as a module to also enable testing the use command.

from xenon.base.datatypes import *

fake_param = Param("sweep_param", 0)

class FakeDesignSweep(BaseDesignSweep):
  sweepable_params = BaseDesignSweep.sweepable_params + [fake_param]
  def __init__(self, name):
    super(FakeDesignSweep, self).__init__(name)

def createFakeSweepEnviron():
  """ Builds the following class attribute structure:

  self.sweep = {
      "sweep_param": 0,
      "top0": "a top value",
      "top1": {
        "sweep_param": 0,
        "middle0": "a middle value",
        "middle1": {
          "low0": "a low value",
          "low1": "another low value",
          "sweep_param": 0,
          }
        "middle2": {
          "low0": "a second low value",
          "low1": "another second low value",
          "sweep_param": 0,
          }
      }
  }
  """
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
  sweep = FakeDesignSweep("mysweep")
  sweep.top0 = "a top value"
  sweep.top1 = top1
  return sweep

USE_COMMAND_SWEEP_TEST_OBJ = createFakeSweepEnviron()
