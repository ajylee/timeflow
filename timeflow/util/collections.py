
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


_key_error = KeyError()

def clean_if_empty(dd, key):
    val = dd.get(key, _key_error)
    if val is _key_error:
        return

    if not val:
        del dd[key]


_callback_refs = []   # contains weakrefs whose only function is to call cleanup
                     # callbacks

def clean_if_empty_and_isolated(dd, event, key):
    # Note: do not call if it has children

    val = dd.get(key, _key_error)
    if val is _key_error:
        return

    resolved = val.read_at(event)

    if not resolved:
        def callback(_unused):
            if not event.child():
                try:
                    del dd[key]
                except KeyError:
                    pass

        if resolved.parent() is None:
            callback(None)
        else:
            _callback_refs.append(weakref.ref(resolved.parent(), callback))
