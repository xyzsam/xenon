# Definitions of sweep parameters.

from xenon.datatypes import *

cycle_time = Param("cycle_time", 1)
unrolling = Param("unrolling", 1)
partition_factor = Param("partition_factor", 1)
partition_type = Param("partition_type", "cyclic")
pipelining = Param("pipelining", False)
