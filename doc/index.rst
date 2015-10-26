

########
Timeflow
########

We describe mutating data structures as explicitly changing "flows" over time.
"Flows" are parameterized by "events", which are managed by "time lines".
Updates to flows are mediated by "plans".
For example::

  tl = TimeLine()
  sf = SetFlow()             # initialize a flow that represents a mutable set.

  initial_plan = tl.new_plan()

  sf.at(initial_plan).add('initial_element')

  e0 = initial_event = tl.commit(initial_plan)

  assert 'initial_element' in sf.at(initial_event)

  plan = tl.new_plan()
  sf.at(plan).add('new_element')
  e1 = tl.commit(plan)

  assert 'new_element' in sf.at(e1)


API
===


Flow Implementations
---------------------

`SetFlow` and `MappingFlow` have been implemented.




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
