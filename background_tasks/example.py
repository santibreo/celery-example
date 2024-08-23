# Builtins
from time import sleep
# Local
from celery_example import app


def test(time: int):
    sleep(time)
    return 'Finished'


@app.task(track_started=True)
def short_task(a, b, c, *, d, e):
    # Do something easy
    print(a)
    print(b)
    print(c)
    print(f"{d=}")
    print(f"{e=}")
    return test(5)
