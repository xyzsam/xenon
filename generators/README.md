Output Generation
=================

The generator subsystem of Xenon is designed to consume the results of
executing a Xenon script and produce useful output. Since Xenon is designed for
sweep generation, we provide a built-in generator for generating all possible
design sweep combinations based on a configured DesignSweep object. To write your
own generator module, follow these instructions:

1. The generator must be named `generate_[target].py`, where TARGET is the name
   that Xenon scripts will use to invoke this generator. For example, the Xenon
   command `generate configs` would invoke the generator
   `generator_configs.py`.
2. The generator must either be placed in the `xenon.generators` package or
   in a user package under the top-level directory named `generators`.
3. The generator must implement the top level method `get_generator(sweep)`,
   which returns an instance of a class with a `run()` method. This class
   implements the complete generator functionality using the configured
   DesignSweep object as the only constructor parameter.
