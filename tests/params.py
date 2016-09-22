# Definitions of sweep parameters.

from xenon.base.datatypes import IntParam, StrParam

cycle_time = IntParam("cycle_time", 1)
unrolling = IntParam("unrolling", 1)
partition_factor = IntParam("partition_factor", 1)
partition_type = StrParam("partition_type", "cyclic")
pipelining = IntParam("pipelining", 0)
