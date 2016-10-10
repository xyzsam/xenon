Xenon Syntax Guide
==================

Xenon is a basic command language, implemented as an embedded Python DSL. Each
line begins with a command keyword, and each command has its own set of valid
syntatical structures. Command keywords are all lowercase. There is no support
for multiline statements at this time.

**Table of Contents**

1. [Basic syntax constructs](#basic-syntax-constructs)
2. [Commands](#commands)
3. [Selections](#selections)
4. [Expressions](#expressions)
5. [Global scope](#global-scope)
6. [List of commands and keywords](#list-of-commands-and-keywords)

# Basic syntax constructs #

Xenon recognizes the following basic syntax constructs:

* Xenon commands and keywords.
* Constants: Integers and floating point numbers (no scientific notation).
* Strings: either single-quoted or double-quoted.
* Booleans: True, False, case sensitive.
* Identifiers: Words that can contain numbers, letters, and underscores, but
  cannot begin with a number. Identifiers are names of objects or properties of
  objects.
* Lists of constants, strings, and booleans, surrounded by [ and ], delimited
  by commas.
* Comments: Started with # and ended by the end of the line.
* Xenon selections: similar to nested Python type specifiers.
* Xenon expressions.
* Python module paths.

# Commands #

This section is a comprehensive guide to the syntax and semantics of each
command, as well as common errors that may be thrown by the Xenon interpreter.

## begin ##

Marks the start of a design sweep specification.

Usage:
  
  ```python
  begin SweepType name_of_sweep
  ```

where:
* `SweepType` is a class or subclass of type `xenon.base.BaseDesignSweep`. This
  class must either a member of `xenon.base.designsweeptypes` or the current
  file's global scope (see [use](#use) and [global scope](#global-scope)).
* `name_of_sweep` is a valid identifier that uniquely identifies this sweep
  specification.

Design sweep specifications cannot be nested.

## end ##

Marks the end of a design sweep specification.

Usage:

  ```python
  end name_of_sweep
  ```

where:
* `name_of_sweep` is the name of the sweep this command is ending.

Throws:
* `XenonSweepNotInitialized` if this command is not preceded by a matching
  `begin` command.

## set ##

Sets an attribute of an object or set of objects to a value.  The values may be
a constant, string, boolean, list, or expression.

Usage:

  ```python
  set attribute [selection] value
  ```

where:
* `attribute` is the name of the Python object attribute whose value will be
  modified.
* `selection` is an optional clause that specifies which objects will be
  modified. See [selections](#selections) for more details. The pair of
  attribute and selection is valid as long as at least one object in the
  selection contains the named attribute.

Throws:
* `XenonSelectionError` if no objects in the selection have the named attribute.
* `TypeError` if the selected object is not of type `XenonObj`.

## sweep ##

Sweep the value of an attribute of an object or set of objects over a list of
values.

Usage:

  ```python
  sweep attribute [selection] sweep_values
  ```

where:
* `attribute` is the name of the Python object attribute whose value will be
  modified.
* `selection` is An optional clause that specifies which objects will be subject
  to this sweep. See [selections](#selections) for more details.
* `sweep_values` are the values to sweep for this attribute. This can be specified
  as a linear or exponentially spaced range (see [ranges](#ranges)), a list of
  values, or an expression.

## generate ##

Instruct Xenon to call the member function of the design sweep class named by
the argument of this command.

Usage:

  ```python
  generate target
  ```

where:
* target is a valid identifier for the generator function, which should be named
  `generate_[target]`. This function takes no arguments and returns a list of any
  files produced by this function.

## use ##

Import a Python module or one or more of its children into the current scope.

The scope of import is either the current design sweep (which will not affect
other design sweeps specified in the same file), or it is the global scope,
in which case this statement appears outside of a design sweep specification.
Global scope `use` commands are usually used for users to use a custom design
sweep type.

This command is the only command that can be used outside of a design sweep
specification.

Usage:

  ```python
  use modulepath
  ```

where:
* `modulepath` is a valid Python modulepath from the current executing directory,
  possibly terminated by `.*` to include all children of that module.

## source ##

Include another Xenon sweep script into the current script at the location of
the source command.

This is equivalent to copy-pasting the sourced file into the current file.

Usage:

  ```python
  source filepath
  ```

where:
* `filepath` is a valid file path, either absolute or relative from the directory
  that contains the current file being parsed.

# Selections #

Selections are an integral part of the Xenon system. They enable users to
selectively apply `set` and `sweep` commands on certain objects. Generally
speaking, they are fully qualified Python object names, with an optional
terminating asterisk.

Selection paths are fully qualified Python names that are rooted either at the
current design sweep scope or at global scope. Xenon searches at design sweep
scope first and then at global scope. If the selection path was successfully
resolved and the path does not have a terminating asterisk, then that object
is returned. If the path does include a terminating asterisk, all children of
type `Sweepable`are returned, *as well as the parent object*. This latter
behavior was found to be very useful in certain cases.  If the selection path
cannot be resolved, then a `XenonSelectionError` is raised.

Selections will only return objects of type `XenonObj`, the base class for all
objects in the Xenon system. If the fully qualified path refers to an object which
is not a `XenonObj`, a TypeError will be thrown.

Selections never appear on their own, but rather as part of another command and
are always preceded by the `for` keyword.

# Expressions #

Expressions enable users to set or sweep attributes based on a function of
other attributes. If other attributes appear in an expression, they must be in
the form of a fully qualified Python object name (essentially the same as a
selection without the asterisk). Expressions support the four basic
mathematical operations: add, subtract, multiply, and divide, along with
parentheses for grouping expressions.

One current limitation of Xenon expressions is that they cannot refer to an
attribute whose value is also an expression. This is due to be addressed in the
future.

Examples of using expressions:

  ```python
  set value for myfirstobject 3
  set value for mysecondobject 5
  set value for mythirdobject (myfirstobject.value / mysecondobject.value) + 5

  ```

# Global Scope #

Global scope permits users to import Python classes and modules for all design
sweep specifications in a Xenon file to use. Currently, the only command that
can be used in global scope is `use`. The most common use case for global scope
is to enable the use of user-defined design sweep types.

Suppose a user wants to extend the capabilities of `ExhaustiveSweep` to add
some more generator functions, and he/she has implemented this as a subclass of
`ExhaustiveSweep` called `CustomSweep`. The Xenon script might look like so:

  ```python
  use path.to.module.CustomSweep
  
  begin CustomSweep sweepname
  # script commands...
  end sweepname
  ```

# List of Commands and Keywords #

Commands:
* begin
* end
* sweep
* set
* generate
* use
* source

Other Keywords:
* for
* from
* to
* linstep
* expstep
* True
* False
* \*
