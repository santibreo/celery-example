"""
This file is suppossed to contain all the logic of your API (routers, endpoints,
etc.) but for simplicity it just executes a task.
"""
from time import sleep
from ast import literal_eval
from background_tasks import example
from celery_example import app
from celery_example import request_flower
from celery_example import TaskStatusEnum
from celery_example import FINISHED_STATUSES
from celery_example import TaskError
from celery_example import TaskNotFinishedError
from typing import Any


def get_task_result(task_id: str) -> Any:
    response = request_flower(f"/api/task/info/{aresult.task_id}")
    if not response.status_code == 200:
        raise RuntimeError(f"Flower {response.status_code}: {response.text}")
    response_json = response.json()
    task_status = TaskStatusEnum(response_json['state'].lower())
    if task_status not in FINISHED_STATUSES:
        raise TaskNotFinishedError(f"Task '{task_id}' has not finished yet")
    if task_status == TaskStatusEnum.REVOKED:
        raise TaskError(f"Task '{task_id}' was revoked")
    if task_status != TaskStatusEnum.SUCCESS:
        raise TaskError(f"Task '{task_id}' has raised an error")
    return literal_eval(response_json['result'])


if __name__ == '__main__':
    aresult = app.send_task(
        example.short_task.name,
        args=('hola', 'buenas', 'tardes'),
        kwargs={'d': 'que', 'e': 'tal?'}
    )
    while True:
        try:
            result = get_task_result(task_id := aresult.task_id)
        except TaskNotFinishedError:
            sleep(2)
        else:
            break
    print(f"Task '{task_id}' result: {result!r}")
