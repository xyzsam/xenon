# A set of simple datatypes for testing.

from xenon.base.datatypes import Sweepable

import xenon.tests.params as params

class Benchmark(Sweepable):
  sweepable_params = [
      params.cycle_time,
      params.pipelining,
  ]

  def __init__(self, name):
    super(Benchmark, self).__init__(name)

  def add_array(self, array_name, array_size, array_word_length):
    array = Array(array_name, array_size, array_word_length)
    assert(not hasattr(self, array_name))
    setattr(self, array_name, array)

  def add_loop(self, function_name, loop_name):
    if not hasattr(self, function_name):
      f = Function(function_name)
      setattr(self, function_name, f)
    getattr(self, function_name).add_loop(loop_name)

class Array(Sweepable):
  sweepable_params = [
      params.partition_type,
      params.partition_factor,
  ]

  def __init__(self, name, size, word_length):
    super(Array, self).__init__(name)
    self.size = size
    self.word_length = word_length

class Function(Sweepable):
  sweepable_params = []

  def __init__(self, name):
    super(Function, self).__init__(name)

  def add_loop(self, loop_name):
    assert(not hasattr(self, loop_name))
    l = Loop(loop_name)
    setattr(self, loop_name, l)

class Loop(Sweepable):
  sweepable_params = [
      params.unrolling,
  ]

  def __init__(self, name):
    super(Loop, self).__init__(name)
