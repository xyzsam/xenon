from __future__ import print_function
import os
import sys

class Generator(object):
  """ Base generator class.

  This contains some helpful error handling functions.
  """

  def __init__(self):
    pass

  def handle_error(self, message, error_msg_f):
    """ Handle an error that sent error text to a file.

    Args:
      message: Helpful message to display to the user.
      error_msg_f: File handle containing error text.
    """
    print("[ERROR]: {}".format(message))
    error_msg_f.flush()
    error_msg_f.seek(0)
    data = error_msg_f.read()
    print(data)
    error_msg_f.close()
    os.remove(error_msg_f.name)
    sys.exit(1)
