import abc
import sys
import pyparsing as pp

from commands import *
from parsers import *

# class ArrayType(object):
#   def __init__(self):
#     return
#
# class LoopType(object):
#   def __init__(self):
#     return
#
# class BenchmarkType(object):
#   def __init__(self):
#     return
#
class SweepNotInitializedException(Exception):
  def __init__(self):
    super(SweepNotInitializedException, self).__init__(
        "Sweep has not been initialized with a begin statement.")

# TODO: Needs to implement __contains__, __getitem__, and __setitem__
class DesignSweep(object):
  def __init__(self):
    self.name = None
    self.sweep_type = None  # TODO Support different sweep types.
    self.generate_outputs = set()
    self.done = False

  def initializeSweep(self, name, sweep_type):
    self.name = name
    self.sweep_type = sweep_type

  def endSweep(self):
    self.checkInitializedAndRaise_()
    self.done = True

  def addGenerateOutput(self, output):
    self.checkInitializedAndRaise_()
    self.generate_outputs.add(output)

  def checkInitializedAndRaise_(self):
    if self.name == None:
      raise SweepNotInitializedException()
