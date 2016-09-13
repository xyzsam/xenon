# Definitions of sweep parameters.

class BaseParam(object):
  def __init__(self, name, param_type):
    self.name = name
    self.param_type = param_type

cycle_time = "CYCLE_TIME"
unrolling = "UNROLLING"
partition_factor = "PARTITION_FACTOR"
partition_type = "PARTITION_TYPE"
pipelining = "PIPELINING"
