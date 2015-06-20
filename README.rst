timefunc
=========

Status: WIP

FRP-style data structures for python. The data structures
become a function of time, allowing you to construct the future with
explicit reference to objects at certian time.


Example:

Where is the company that the mayor of Baztown in 2010 worked at in 2000 located?

| Mayor of Baztown in 2010 -> Wizzy         (but not the current mayor!)
| Wizzy's job in 2000 -> CEO of Eggycom     (but not his job in 2010!)
| Eggycom location in 2000 -> Footown       (but not its location in 2000!)


The question depends crucially on the ability to determine relationships at
different times. If we used python dictionaries to keep track of
all these these relationships, and we updated them over time, we would have
difficulty answering this question. 

The timefunc package allows the efficient representation of time-dependent
datastructures.


Caveats
--------

Timelines are discrete, although it could be extended to be continuous. (In FRP,
time is continuous.)
