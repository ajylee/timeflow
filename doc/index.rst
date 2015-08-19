

########
Timeflow
########


API
===


There are two kinds of time dependent objects, or "flows". The TimeLine, and the TimeStep.

A Flow type is further parameterized by its data type at a given time. For example::


  timeline = TimeLine({0: SnapshotMapping({'a', 10})})

  assert timeline.at(0)['a'] == 10




Memory
======

TimeFlow tries to minimize memory usage of similar data by only storing
differences. Specifically, TimeFlow keeps the literal representation of the
latest version of a datastructure while keeping only the diffs for past
versions. In doing so, TimeFlow mutates internal variables.

For safety, TimeFlow makes copies when creating internal variables. In the
timeline example above, SnapshotMapping creates a copy of its argument.
This is not necessary if the argument is never referred to from outside
the TimeLine object. One can cancel the copy operation like so::

  TimeLine({0: SnapshotMapping({'a', 10}, copy=False)})
