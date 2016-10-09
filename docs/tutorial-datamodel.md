# Defining the data model #

There are two primary Xenon datatypes that will be used.

1. `Sweepable`: A base class for any object that has attributes (i.e. design
   parameters) the designer will want to control from a Xenon script.
2. `Param`: A class that describes a design parameter.

Let's see how we would describe a desk in Xenon.  Our desk has three
components: the table top, a drawer, and some number of legs. Suppose we want
to control the following attributes:

  - Material used to build the desk (applies to all components).
  - Width and length of the tabletop.
  - Width, length, and height of the drawer.
  - Length and diameter of each leg.

We'll define our data model (aka datatypes) in a file named `datatypes.py`. The
data model would start out looking something like this:

  ```python
  from xenon.base.datatypes import Sweepable
  from xenon.base.params import IntParam, StrParam

  # Typically, these parameters would go into their own module.
  material = StrParam("material", "wood", valid_opts=["wood", "steel"])
  width = IntParam("width", 10) # inches
  length = IntParam("length", 10)
  height = IntParam("height", 10)
  diameter = IntParam("diameter", 3)

  class Desk(Sweepable):
    sweepable_params = [material]

  class Top(Sweepable):
    sweepable_params = [width, length]

  class Drawer(Sweepable):
    sweepable_params = [width, length, height]

  class Leg(Sweepable):
    sweepable_params  = [length, diameter]
  ```

We began by first defining all design parameters we want to control from the
script as instances of the `Param` class. `IntParam` and `StrParam` are
specializations of `Param` that implement basic type checking for their values.
Each parameter is given a name and a default value as the second argument.
Optionally, a parameter can be assigned a set of valid values; in our case,
we constrained the choice of table material to either wood or steel. Attempting
to set a value that is not one of these will throw an error.

Then, we defined a subclass of `Sweepable` for each type of object in our
table.  We also defined a *class* variable (not an *instance* variable!) called
`sweepable_params`.  This list defines all the parameters that can be swept --
that is, assigned a *range* of values -- for any instance of this class (hence
the name). The reason we use class variables instead of instance variables is
mostly to avoid boilerplate. All `Sweepable` objects, during construction, copy
each `Param` object from `sweepable_params` into a per-instance variable; the
reason for this copy operation will be explained when we describe how to write
and run a Xenon script.

Now, different table designs may have different numbers of legs or differently
sized front and back legs. We'll assume each table only has one top and drawer,
for simplicity. Let's add a method to add a top, drawer, and legs to a table.
Assume that all classes take a `name` constructor parameter.

  ```python
  class Desk(Sweepable):
    sweepable_params = [material]
    def __init__(self, name):
      super(Desk, self).__init__(name)

    def add_leg(self, leg_name):
      leg = Leg(leg_name)
      setattr(self, leg_name, leg)

    def add_top(self, leg_name):
      top = Top(top_name)
      setattr(self, top_name, top)

    def add_drawer(self, leg_name):
      drawer = Drawer(drawer_name)
      setattr(self, drawer_name, drawer)
  ```

Note the use of the Python `setattr` function. In Xenon, all parent-child
relationships are specified through attributes.

With this, we are done defining the data model! Now, let's instantiate some instances.

# Instantiating the data model #

Let's define a collection of desk designs. For simplicity, our collection of
designs differ structurally only in the number of legs (a real collection might
have desks with different numbers of tops, multiple materials, etc.). We'll put
this into a file called `collection.py`.

  ```python
  from datatypes import *

  Desk threelegdesk = Desk("threelegdesk")
  threelegdesk.add_top("top")
  threelegdesk.add_drawer("drawer")
  threelegdesk.add_leg("front_leg")
  threelegdesk.add_leg("back_left_leg")
  threelegdesk.add_leg("back_right_leg")

  Desk fourlegdesk = Desk("fourlegdesk")
  fourlegdesk.add_top("top")
  fourlegdesk.add_drawer("drawer")
  fourlegdesk.add_leg("front_left_leg")
  fourlegdesk.add_leg("front_right_leg")
  fourlegdesk.add_leg("back_left_leg")
  fourlegdesk.add_leg("back_right_leg")
  ```

We are now ready to sweep the design spaces of our three-legged and four-legged
desks!
