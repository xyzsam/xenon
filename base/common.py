from xenon.base.datatypes import XenonObj
from xenon.base.keywords import LIT_STAR
import xenon.base.exceptions as xe

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

def getSelectedObjs(select_tokens, env):
  """ Return a list of objects in an environment selected by this selection.

  TODO: Fix documentation.
  """
  if not isinstance(env, XenonObj):
    raise TypeError("%s is not of type XenonObj." % str(env))

  # If there was no selection defined, then the selection is implicitly the
  # entire environment, recursively.
  if len(select_tokens) == 0:
    select_tokens.append(LIT_STAR)

  current_view = env
  for token in select_tokens[0]:
    if token == LIT_STAR:
      break
    try:
      current_view = getattr(current_view, token)
    except AttributeError:
      raise xe.XenonSelectionError(".".join(select_tokens[0]))

  selected_objs = []
  if token == LIT_STAR:
    if not isinstance(current_view, XenonObj):
      selection_path = ".".join(select_tokens[:-1])
      raise TypeError("%s is not of type XenonObj." % selection_path)
    selected_objs = recursiveSelect(current_view, objtype=XenonObj)
  # Remember: * returns not just all the children of the current view,
  # but the current view itself.
  selected_objs.extend([current_view])
  return selected_objs

def getSelectedAttrOnView(select_tokens, view):
  """ Return the selected attribute over a SweepableView.

  Unlike getSelectedObjs, this does not return a list of XenonObjs, but rather
  a single object. * is not supported in this case.
  """
  if len(select_tokens) == 0:
    return view

  selection_path = ".".join(select_tokens)
  current_view = view
  for token in select_tokens:
    if token == LIT_STAR:
      raise SyntaxError(
          "%s: * is not a valid selection in an expression." % selection_path)
    try:
      current_view = getattr(current_view, token)
    except AttributeError:
      raise xe.XenonSelectionError(selection_path)

  return current_view
