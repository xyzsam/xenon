import abc
import sys
import pyparsing as pp

from commands import *
from parsers import *
from xenon_exceptions import *

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

class DesignSweep(object):
  def __init__(self, name=None, sweep_type=None):
    self.name = name
    self.sweep_type = sweep_type  # TODO Support different sweep types.
    self.generate_outputs = set()
    self.done = False
    self.output_dir = ""
    self.source_dir = ""
    self.memory_type = ""
    self.simulator = ""

  def __iter__(self):
    for key in self.__dict__:
      yield key

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
      raise SweepNotInitializedError()

  def __repr__(self):
    return "DesignSweep({0},{1})".format(self.name, self.sweep_type)
