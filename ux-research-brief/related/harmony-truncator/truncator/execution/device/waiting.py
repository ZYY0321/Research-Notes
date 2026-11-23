"""Bounded observation polling. Actions are dispatched by the caller exactly once."""

import time
from truncator.common.validation import finite


def wait_for_tree(
    read_tree,
    evaluate,
    timeout=10,
    interval=0.5,
    stable_samples=1,
    clock=time.monotonic,
    sleep=time.sleep,
):
    timeout, interval = finite(timeout, "timeout"), finite(interval, "poll_interval")
    if not 0 <= timeout <= 120 or not 0 < interval <= 10:
        raise ValueError("Timeout must be in [0,120] and poll interval in (0,10]")
    if (
        isinstance(stable_samples, bool)
        or not isinstance(stable_samples, int)
        or not 1 <= stable_samples <= 5
    ):
        raise ValueError("stable_samples must be an integer in [1,5]")
    started = clock()
    previous, consecutive, polls = None, 0, []
    while True:
        tree = read_tree()
        ready, identity = evaluate(tree)
        consecutive = consecutive + 1 if ready and identity == previous else int(ready)
        previous = identity
        elapsed = clock() - started
        polls.append(
            {"elapsed": elapsed, "ready": ready, "stable_samples": consecutive}
        )
        if consecutive >= stable_samples or elapsed >= timeout:
            return tree, {
                "ready": consecutive >= stable_samples,
                "polls": polls,
                "elapsed": elapsed,
            }
        sleep(min(interval, timeout - elapsed))
