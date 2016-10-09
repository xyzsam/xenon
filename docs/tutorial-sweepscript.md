# Writing a Xenon sweep script #

Xenon defines a simple and concise command language for specifying a design
sweep.  In a design sweep, the user sets the value or range of values for each
parameter of each `Sweepable` object in a data model. The Xenon interpreter
will read the design sweep file, execute each command, and then expand the data
model into a set of configurations.

## Simple example ##

Let's begin with a simple example. Open up a file called `sweep.xe`:

  ```python
  begin ExhaustiveSweep myfirstsweep

  use collection.*

  set output_dir 'outputs'
  generate configs

  end myfirstsweep
  ```

Let's see what happened here:

1. `begin ExhaustiveSweep myfirstsweep`: The `begin` command denotes the start
   of a design sweep of a certain **type** and **name**. Here, the type is
   `ExhaustiveSweep` and the name is `myfirstsweep`.  `ExhaustiveSweep` is a
   built-in Xenon type that generates a configuration for every possible
   combination of swept parameter values.

   A single file can contain multiple distinct sweeps.
2. `use collection.*`: The `use` command is similar to the Python `import`
   statement. In this example, we have "imported" all of the top level
   `Sweepable` objects from the `collection` module into the scope of this
   design sweep, so they can now be referred to by name (e.g. `threelegdesk`,
   `fourlegdesk`). Module paths are specified in the same way as Python module
   paths.
3. `set output_dir 'output'`: The `set` command is one of the two primary Xenon
   commands. It assigns a single value to one or more attributes. In this case,
   because the object that contains the `output_dir` attribute is not
   explicitly specified in this command, Xenon assumes the command is referring
   to the design sweep object. Indeed, the ExhaustiveSweep class contains a
   member variable called `output_dir` which specifies where the output of the
   Xenon sweep generation will go.
4. `generate configs`: The `generate` command instructs Xenon to invoke a
   generator function (not to be confused with Python generators) after
   executing all commands. `configs` implies that this design sweep type has a
   function called `generate_configs`, and this means that Xenon will produce
   a dump of all generated configurations.
5. `end myfirstsweep`: The `end` command ends the current sweep. The Xenon
   interpreter will stop parsing the file at this point and begin executing the
   commands.

Now, let's execute this Xenon script.  Although we haven't specified any values
for any of our desk's attributes, every attribute has a default value, and since
we have not swept any of its attributes, Xenon will only generate a single
configuration. Go to the top level Xenon directory and execute the following command:

  ```
  python xenon_interpreter.py sweep.xe
  ```

When the intepreter is finished, there will be a file named
`outputs/myfirstsweep.json`. This is a JSON dump of all configurations
generated. Take a look inside this file. It should look something like this
(abbreviated):

  ```json
  [
    {
      "ExhaustiveDesignSweep(\"myfirstsweep\")": {
        "Desk(\"threelegdesk\")": {
          "Top(\"top\")": {
            "length": 10,
            "width": 10,
          },
          "Drawer(\"drawer\")": {
            "length": 10,
            "width": 10,
            "height": 10,
          },
          "Leg(\"front_leg\")": {
            "length": 10,
            "diameter": 3,
          },
         "material": "wood",
        },
        "Desk(\"fourlegdesk\")": {
          "Leg(\"front_left_leg\")": {
            "length": 10,
            "diameter": 3,
          },
         "material": "wood",
        },
      },
    },
  ]
  ```

This JSON dump is the final output of Xenon. This JSON dump is probably not of
any immediate use for an end user tool, which expects input files in its own
format. However, the JSON dump is trivial to load as a Python structure. The
user is expected to implement the backend that transforms the JSON into tool
specific input formats.

## Setting values of parameters ##

Xenon allows user to set values of parameters at varying levels of granularity.
Earlier, we saw how to set the value of an attribute at the design sweep level.
Now we will see how to set values for individual Sweepable objects.

Suppose we want to set the leg diameter for all desk designs to 5. This can be
done in one of two ways:

  ```python
  set diameter for threelegdesk.* 5
  set diameter for fourlegdesk.* 5
  ```

`threelegdesk.*` is a Xenon *selection*: it returns a subset of all `Sweepable`
objects that match the given expression. The asterisk is a wildcard that
recursively traverses the data structure and returns all `Sweeapble` children
below the root (`threelegdesk`). In this case, `threelegdesk.*` returns the following list of
objects:

  ```python
  [Desk("threelegdesk"), Drawer("drawer"), Top("top"),
   Leg("front_leg"), Leg("back_left_leg"), Leg("back_right_leg")]
  ```

Note that in addition to the children of `threelegdesk`, the asterisk includes
the root as well. This behavior was found to be useful in certain scenarios,
although in this particular case it does not apply.

The `set` command now attempts to set the `diameter` attribute on each of these
objects.  However, not all objects will have this attribute. This is fine;
Xenon will simply skip objects that don't qualify. However, if the selection
does not return *any* items with the attribute that is being set, then Xenon
will throw an error.

If you have many desk designs in your collection, it would be tedious to write
out each one explicitly. Fortunately, the asterisk comes to the rescue:

  ```python
  set diameter for * 5
  ```

This time, the root of recursive expansion is is the design sweep object. The
list of objects that would be returned would look something like this:

  ```python
  [
   Desk("threelegdesk"), Drawer("drawer"), Top("top"),
   Leg("front_leg"), Leg("back_left_leg"), Leg("back_right_leg"),
   Desk("fourlegdesk"), Drawer("drawer"), Top("top"),
   Leg("front_left_leg"), Leg("front_right_leg"),
   Leg("back_left_leg"), Leg("back_right_leg"),
  ]
  ```

We can be even more specific and set individual leg diameters:

  ```python
  set diameter for * 5
  set diameter for threelegdesk.back_left_leg 1
  set diameter for threelegdesk.back_right_leg 1
  ```

This sequence of commands first sets all leg diameters to 5, then
individually sets diameters for two legs. The second two commands naturally
overwrite the values set by the first.

We can do even more: we can set leg diameters with expressions based on the
value of another leg. Suppose we want the back legs to always be twice the
diameter of the front legs:

  ```python
  set diameter for threelegdesk.front_leg 10
  set diameter for threelegdesk.back_left_leg threelegdesk.front_leg/2
  set diameter for threelegdesk.back_right_leg threelegdesk.front_leg/2
  ```

Expressions can refer to the value of other attributes, even if they were never
explicitly assigned a value (in that case, it will use the default value).
They support the four basic arithmetic operations and parentheses.

## Sweeping values of parameters ##

Thus far, we have only looked at how to set a single value to an attribute.
When we want to sweep the attribute, we use the `sweep` command, which
specifies an attribute to sweep, a selection of objects on which to apply this
sweep, and a range of values to sweep. For example:

  ```python
  sweep diameter for * from 1 to 5 linstep 1
  ```

This command will tell Xenon to sweep the diameters of all legs from 1 to 5 in
linear steps of 1, inclusively. Note: this sweep command applies each value of
the sweep range to all objects in the selection at once. That is, for
`threelegdesk`, it will generate the following sweep configurations:

| front_leg | back_left_leg | back_right_leg |
|:---------:|:-------------:|:--------------:|
| 1         | 1             | 1              |
| 2         | 2             | 2              |
| 3         | 3             | 3              |
| 4         | 4             | 4              |
| 5         | 5             | 5              |

It does *not* sweep each leg diameter independently, like so:

| front_leg | back_left_leg | back_right_leg |
|:---------:|:-------------:|:--------------:|
| 1         | 1             | 1              |
| 2         | 1             | 1              |
| 3         | 1             | 1              |
| 4         | 1             | 1              |
| 5         | 1             | 1              |
| 1         | 2             | 1              |
| 1         | 3             | 1              |
| 1         | 4             | 1              |
| 1         | 5             | 1              |
| 1         | 1             | 2              |
| 1         | 1             | 3              |
| 1         | 1             | 4              |
| 1         | 1             | 5              |

This behavior is currently not supported; it is planned for a future release of
Xenon. Currently, if this latter behavior is the desired result, you must
create separate attributes for each leg.

Xenon treats each top level `Sweepable` object independently; that means that
you can set entirely different sweep parameters on `threelegdesk` and
`fourlegdesk`.

Just as with the `set` command, we can perform selections to limit the
attributes being swept.

  ```python
  set diameter for threelegdesk.* 5
  sweep diameter for threelegdesk.front_leg from 2 to 8 expstep 2
  ```

If we omit the `linstep 1` clause, Xenon assumes a linear step size of 1.
`expstep 2` specifies an exponential step size of base 2 -- in other words, it
doubles the value each time. This sequence would produce the following sweep
configurations:

| front_leg | back_left_leg | back_right_leg |
|:---------:|:-------------:|:--------------:|
| 2         | 5             | 5              |
| 4         | 5             | 5              |
| 8         | 5             | 5              |

If you want to sweep leg diameters with different values, this can be done
without specifying separate attributes for each leg as long as the number of
values in the sweep ranges is the same:

  ```python
  sweep diameter for threelegdesk.front_leg from 1 to 3
  sweep diameter for threelegdesk.back_leg from 3 to 5
  sweep diameter for threelegdesk.back_leg from 2 to 8 expstep 2
  ```

This produces the following sweep:

| front_leg | back_left_leg | back_right_leg |
|:---------:|:-------------:|:--------------:|
| 1         | 3             | 2              |
| 2         | 4             | 4              |
| 3         | 5             | 8              |

Again, note that each diameter is not individually swept; instead, each
diameter is swept in parallel.

Here is an example of sweeping multiple parameters:

  ```python
  sweep height for threelegdesk.top from 2 to 5
  sweep diameter for threelegdesk.* from 1 to 3
  ```

This produces the following sweep (for brevity, all legs are collapsed into one
column):

| top height | leg diameter |
|:----------:|:------------:|
| 2          | 1            |
| 3          | 1            |
| 4          | 1            |
| 5          | 1            |
| 2          | 2            |
| 3          | 2            |
| 4          | 2            |
| 5          | 2            |
| 2          | 3            |
| 3          | 3            |
| 4          | 3            |
| 5          | 3            |

Finally, we can use expressions in `sweep` commands too:

  ```python
  sweep length for threelegdesk.* from 10 to 30 step 5
  sweep diameter for threelegdesk.* threelegdesk.front_leg/5
  ```

This produces the following sweep:

| leg_length | leg diameter |
|:----------:|:------------:|
| 10         | 2            |
| 15         | 3            |
| 20         | 4            |
| 25         | 5            |
| 30         | 6            |

There are two things to note here:

1. Although these attributes are different and would typically be swept
   independently, because the value of one is a funtion of the value of
   another, instead the two attributes are swept in parallel.
2. We used the expression `threelegdesk.front_leg` in the second `sweep`
   command. Since we applied the same sweep to all of the leg diameters, we
   could have chosen any leg to be the reference.
