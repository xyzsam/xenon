Xenon: Design Sweep Generation
==============================

[![build status](https://travis-ci.org/xyzsam/xenon.svg?branch=master)](https://travis-ci.org/xyzsam/xenon)

Xenon is a language and system for efficient generation of configurations for
design space sweeps. It is implemented as an embedded Python DSL. At a high
level, Xenon works by executing commands that set Python object attributes on
objects in a user-defined data model and then expanding these attributes into
a set of configurations. The expansion process is implemented by a class
representing a design sweep. At the end, all configurations are exported in
JSON format. The user is then responsible to write the backend to transform
the JSON output into a form usable by his/her tool.

#### Table of Contents ####
  1. [Tutorial](docs/tutorial.md) - Write a basic Xenon data model and
     configuration script and generate a design sweep.
  2. [Xenon syntax](docs/xenon_syntax.md) - Syntax specification for the Xenon
     command language.

Requirements
------------
Xenon requires the `pyparsing` module. Any version between 2.2.0 and 2.3.0
(inclusive) is supported.

Contact
-------
Sam Xi
Harvard University
samxi@seas.harvard.edu
