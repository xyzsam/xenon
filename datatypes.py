from base_datatypes import Sweepable
import params

class Benchmark(Sweepable):
  sweepable_params_ = Sweepable.sweepable_params_ + [
      params.cycle_time,
      params.pipelining,
  ]

  def __init__(self, name):
    super(Benchmark, self).__init__(name)
    return

class Array(Sweepable):
  sweepable_params_ = Sweepable.sweepable_params_ + [
      params.partition_type,
      params.partition_factor,
  ]

  def __init__(self, name):
    super(Array, self).__init__(name)
    return

class Function(Sweepable):
  sweepable_params_ = Sweepable.sweepable_params_ + []

  def __init__(self, name):
    super(Function, self).__init__(name)
    return

class Loop(Sweepable):
  sweepable_params_ = Sweepable.sweepable_params_ + [
      params.unrolling,
  ]

  def __init__(self, name):
    super(Loop, self).__init__(name)
    return
