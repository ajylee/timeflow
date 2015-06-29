
commit_callbacks = []

def commit(*args):
    for callback in commit_callbacks:
        callback(*args)

    commit_callbacks[:] = []
