from xenon.base.datatypes import BaseDesignSweep
from xenon.generators import exhaustive_configs

# TODO: Documentation to describe the generate_* system.

class ExhaustiveSweep(BaseDesignSweep):
  """ Default exhaustive design sweep that produces every combination of parameters. """
  sweepable_params = BaseDesignSweep.sweepable_params

  def __init__(self, name=None):
    super(ExhaustiveSweep, self).__init__(name)

  def generate_configs(self):
    generator = exhaustive_configs.ConfigGenerator(self)
    return generator.run()
