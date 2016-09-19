from xenon.base.datatypes import XenonObj

def recursiveSelect(root, objtype=object):
  """ Recursively selects all attributes of type objtype from root. """
  assert(isinstance(root, XenonObj))
  selected_objs = []
  for obj in root.iterattrvalues(objtype=objtype):
    # Safety check to avoid infinite recursion.
    if obj == root:
      continue
    selected_objs.append(obj)
    selected_objs.extend(recursiveSelect(obj, objtype=objtype))
  return selected_objs
