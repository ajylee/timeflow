timefunc
=========

Status: WIP

FRP-style data structures for python. The data structures
become a function of time, allowing you to construct the future with
explicit reference to objects at various times.

The idea is to limit mutation. The past is immutable, we work on a mutable plan,
and commit it to step into the future.


Motivation:

Where is the company that the mayor of Baztown in 2010 worked at in 2000 located today?

    | Mayor of Baztown in 2010 -> Wizzy         (not the current mayor)
    | Wizzy's job in 2000 -> CEO of Eggycom     (not his job in 2010)
    | Eggycom location today -> Footown       (not its location in 2000)

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
