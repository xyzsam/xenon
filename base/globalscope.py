from xenon.base.datatypes import XenonObj

class GlobalScope(XenonObj):
  """ Contains global shared state across sweeps.

  This is required in order to allow subclassing of BaseDesignSweep. In such a case,
  the user would include a use statement that imports the subclass into global scope
  first before declaring a sweep of that type.

  Local use statements always override global statements in the case of a name
  collision.

  TODO: In the future, we may enable global set commands as well, for global constants.
  """
  def __init__(self):
    pass

scope = GlobalScope()
