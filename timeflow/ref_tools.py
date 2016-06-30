

def strong_ref(xx):
    def _strong_ref():
        return xx

    return _strong_ref

empty_ref = strong_ref(None)
