timeflow
=========

*Handle time dependence naturally*

Status: WIP

FRP-style data structures for python. The data structures
become a function of time, allowing you to construct the future with
explicit reference to objects at various times.

- The timeflow package allows the efficient representation of time-dependent
  datastructures.

- Simplify the modification of data structures via a git-like workflow. The past
  is immutable, we work on a mutable plan, and commit when we are done. The
  commit then becomes part of the immutable past and we work on a new plan.

- Resolve complicated time-dependent relationships, like the
  following:

  *Where is the company that the mayor of Baztown in 2010 worked at in 2000 located today?*
  
    | Mayor of Baztown in 2010 -> Wizzy         (not the current mayor)
    | Wizzy's job in 2000 -> CEO of Eggycom     (not his job in 2010)
    | Eggycom location today -> Footown         (not its location in 2000)
  
  The question depends crucially on the ability to determine relationships at
  different times. If we used python dictionaries to keep track of all these
  these relationships, and we updated them over time, we would have difficulty
  answering this question. With the timeflow package we model time-dependence
  explicitly such questions are easy to answer.



Examples
---------



The simplest use case is to have only a head and a stage, to manage mutation.
This is almost a drop-in replacement for existing dictionaries.

.. code:: python

  from timeflow import StepMapping

  original = dict(a=10, b=20, to_delete=1000)
  sm = StepMapping(original.copy())

  sm.stage['a'] = 30
  sm.stage['new'] = 100
  del sm.stage['to_delete']

  assert sm.head == original
  sm.commit()
  assert sm.head == {'a':30, 'b':20, 'new':100}
