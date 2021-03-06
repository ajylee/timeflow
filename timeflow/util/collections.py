
import weakref
from ..linked_structure import SELF
from ..linked_mapping import empty_linked_mapping
from ..linked_set import empty_linked_set

class WeakKeyDefaultDictionary(weakref.WeakKeyDictionary):
    """Calls default() when getting a key not in the dict"""

    def __init__(self, default):
        weakref.WeakKeyDictionary.__init__(self)
        self._default = default

    def __getitem__(self, key):
        try:
            return weakref.WeakKeyDictionary.__getitem__(self, key)
        except KeyError:
            val = self._default()
            self[key] = val
            return val


class WeakValueDefaultDictionary(weakref.WeakValueDictionary):
    """Calls default() when getting a key not in the dict"""

    def __init__(self, default):
        weakref.WeakValueDictionary.__init__(self)
        self._default = default

    def __getitem__(self, key):
        try:
            return weakref.WeakValueDictionary.__getitem__(self, key)
        except KeyError:
            val = self._default()
            self[key] = val
            return val


_key_error = KeyError()

def clean_if_empty(dd, key):
    val = dd.get(key, _key_error)
    if val is _key_error:
        return

    if not val:
        del dd[key]


_callback_refs = []   # contains weakrefs whose only function is to call cleanup
                     # callbacks
