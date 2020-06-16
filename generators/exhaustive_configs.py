import itertools
import json
import numpy as np
import os
import sys

import xenon.base.common as common
import xenon.base.exceptions as xe
from xenon.base.datatypes import *
from xenon.base.expressions import Expression
from xenon.generators import base_generator

class SweepableView(XenonObj):
  """ An overlay for Sweepable objects.

  Sweepable objects describe a range of values that their attributes can take
  on.  A SweepableView is an instantiation of one possible combination of those
  values that does not modify any state of the wrapped Sweepable object. When
  fully generated, a SweepableView can be dumped in JSON form and reformatted
  by a backend for some target output.
  """
  def __init__(self, sweepable_obj):
    super(SweepableView, self).__init__()
    # Wrap the sweepable object so we can access its range.
    self.sweepable = sweepable_obj
    # A list of attributes that we've copied from sweepable_obj.
    self.attrs = []
    # Copy the sweepable attributes from sweepable_obj.
    for name in self.sweepable.user_attrs:
      value = getattr(self.sweepable, name)
      if not isinstance(value, Sweepable):
        setattr(self, name, value)
        self.attrs.append(name)
    # Recursively copy all Sweepable children from sweepable_obj.
    for child_name, child in self.sweepable.iterattritems(objtype=Sweepable):
      setattr(self, child_name, SweepableView(child))
      self.attrs.append(child_name)
    # Make an attribute for the type name.
    self.attrs.append("type")
    setattr(self, "type", sweepable_obj.__class__.__name__)

  def dump(self, stream=sys.stdout):
    dictified = self.dictify()
    json.dump(dictified, stream, sort_keys=True, indent=2)

  def dictify(self):
    top_attr = str(self)
    return {top_attr: self.dictify_recursive_()}

  def dictify_recursive_(self):
    children = {}
    for attr_name in self.attrs:
      attr_value = getattr(self, attr_name)
      if isinstance(attr_value, SweepableView):
        # If this object has SweepableView children, then we want to identify
        # its type in the string.
        expanded_name = str(attr_value)
        children[expanded_name] = attr_value.dictify_recursive_()
      else:
        # Otherwise, this is just a plain variable, so just use attr_name.
        children[attr_name] = attr_value
    return children

  def __repr__(self):
    return "{0}(\"{1}\")".format(
        self.sweepable.__class__.__name__, self.sweepable.name)

class ConfigSet(object):
  """ A wrapper for the set of configurations generated from a design sweep.

  The only purpose of this class is to dump the complete list of configurations
  as a valid JSON file.
  """
  def __init__(self, configs):
    # List of generated configurations, where each config is dict.
    self.configs = configs

  def dump(self, stream=sys.stdout):
    json_repr = [config.dictify() for config in self.configs]
    json.dump(json_repr, stream, sort_keys=True, indent=2)

class ConfigGenerator(base_generator.Generator):
  def __init__(self, configured_sweep):
    self.sweep = configured_sweep

  def run(self):
    """ Generate and dump output.

    Returns the list of files generated.
    """
    config_set = self.generate()
    generated_files = []
    if not os.path.exists(self.sweep.output_dir):
      os.makedirs(self.sweep.output_dir)
    output_file_name = os.path.join(self.sweep.output_dir, "%s.json" % self.sweep.name)
    with open(output_file_name, "w") as f:
      config_set.dump(f)
      generated_files.append(output_file_name)
    return generated_files

  def generate(self):
    """ Generate all configurations of this sweep. """
    param_range_len = self.discoverSweptParameters()
    indices_list = []
    id_list = []
    # To preserve stability in sweep parameter ordering, first obtain the list
    # of param ids, sort them, then get the appropriate index ranges. Splitting
    # it up this way lets us achieve the same result as applying np.argsort()
    # to both arrays without requiring numpy.
    for param_id in param_range_len:
      id_list.append(param_id)
    id_list.sort()
    for param_id in id_list:
      indices_list.append(range(0, param_range_len[param_id]))
    indices_list = tuple(indices_list)

    # index_combinations is a generator of tuples, where the ith value is the
    # index of the parameter range with parameter id id_list[i].
    index_combinations = itertools.product(*indices_list)
    generated_configs = []
    for indices in index_combinations:
      top_view = SweepableView(self.sweep)
      self.applySweepParamValues(top_view, id_list, indices)
      self.applyExpressionValues(top_view)
      self.applyDefaultParamValues(top_view)
      generated_configs.append(top_view)

    return ConfigSet(generated_configs)

  def applySweepParamValues(self, root_view, ids, indices):
    """ Recursively apply the values of the swept parameter ranges. """
    for param_id, param_idx in zip(ids, indices):
      if param_id in root_view.sweepable.iterparamids():
        param_value = root_view.sweepable.getSweepParamRange(param_id)[param_idx]
        param_name = root_view.sweepable.getParamName(param_id)
        setattr(root_view, param_name, param_value)

    for child_view in root_view.iterattrvalues(objtype=SweepableView):
      self.applySweepParamValues(child_view, ids, indices)

  def applyDefaultParamValues(self, root_view):
    """ Set any parameters untouched by 'set' or 'sweep' commands to default values. """
    for attr in root_view.attrs:
      if isinstance(getattr(root_view, attr), UnassignedParamValue):
        setattr(root_view, attr, root_view.sweepable.getParamDefaultValue(attr))

    for child_view in root_view.iterattrvalues(objtype=SweepableView):
      self.applyDefaultParamValues(child_view)

  def applyExpressionValues(self, root_view, parent_view=None):
    """ Evaluate any expressions that could not be evaluated earlier.

    Expressions that cannot be evaluated at command execution time are those
    that:
      - Reference an attribute that was marked to be swept.
      - Reference an attribute that was left to its default value. Default
        values are resolved at sweep generation time.
    """
    if parent_view == None:
      parent_view = root_view
    for attr in root_view.attrs:
      attr_value = getattr(root_view, attr)
      if isinstance(attr_value, Expression):
        setattr(root_view, attr, attr_value.eval(parent_view))

    for child_view in root_view.iterattrvalues(objtype=SweepableView):
      self.applyExpressionValues(child_view, parent_view)

  def discoverSweptParameters(self):
    """ Return a list of all swept Param objects.

    TODO: Fix documentation.
    """
    # Get all the sweepable objects.
    all_sweepable = common.recursiveSelect(self.sweep, objtype=Sweepable)
    range_len = {}
    for sweepable in all_sweepable:
      for param_id, param_range in sweepable.iterparamitems():
        if param_id in range_len and range_len[param_id] != len(param_range):
            param_name = sweepable.getParamName(param_id)
            raise xe.XenonMismatchingRangeError(
                param_name, len(param_range), range_len[param_id])
        else:
          range_len[param_id] = len(param_range)

    return range_len
