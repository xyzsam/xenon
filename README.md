Xenon: Design Sweep Generation
==============================

[![build status](https://travis-ci.org/xyzsam/xenon.svg?branch=master)](https://travis-ci.org/xyzsam/xenon)

Xenon is a language and system for efficient generation of configurations for
design space sweeps. It is implemented as an embedded Python DSL. At a high
level, Xenon works by executing commands that set Python object attributes on
objects in a user-definefd data model and then expanding these attributes into
a set of configurations that is exported in JSON format.

** Table of Contents **
  1. [Tutorial](docs/tutorial.md) - Write a basic Xenon data model and
     configuration script and generate a design sweep.
  2. [Xenon data model](docs/xenon_data_model.md) - Describes the Xenon data
     model and basic datatypes.
  3. [Xenon syntax](docs/xenon_syntax.md) - Syntax specification for the Xenon
     command language.

Contact
-------
Sam Xi
Harvard University
samxi@seas.harvard.edu
