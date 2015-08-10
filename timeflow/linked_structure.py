delete = ('delete', object)

PARENT = 0
CHILD = 1
SELF = 2


def transfer_core(self, other):
    assert self.base_relation is SELF

    core = self.base

    for k,v in other.diff_base.items():
        if v[other.diff_side] is delete:
            del core[k]
        else:
            core[k] = v[other.diff_side]

    if self.parent() is other:
        self.set_base(other, PARENT)
    else:
        assert other.parent() is self
        self.set_base(other, CHILD)

    other.set_base(core, SELF)


