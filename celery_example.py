# Builtins
import os
from enum import auto
from enum import StrEnum
from pathlib import Path
from functools import total_ordering
# Installed
import requests
from celery import Task
from celery import Celery
from dotenv import load_dotenv
# Types
from typing import Literal
from typing import Sequence


assert load_dotenv(Path(__file__).parent / '.env'), '.env file NOT found'
GLOBAL_DIR = Path(os.getenv('API_GLOBAL_DIR', '/usr/src/user-data'))
RABBITMQ_HOST, FLOWER_HOST = 'rabbitmq', 'flower'
#  RABBITMQ_HOST, FLOWER_HOST = '127.0.0.1', '127.0.0.1'
RABBITMQ_URL = (
    f"amqp://{os.environ['RABBITMQ_DEFAULT_USER']}:"
    f"{os.environ['RABBITMQ_DEFAULT_PASS']}@{RABBITMQ_HOST}:5672"
)


class TaskError(Exception):
    """Base exception for all exceptions related with tasks"""
    pass


class TaskNotFinishedError(TaskError):
    """Exception raised when trying to perform an action on not finished task"""
    pass


@total_ordering
class TaskStatusEnum(StrEnum):

    PENDING = auto()
    STARTED = auto()
    FAILURE = auto()
    REVOKED = auto()
    SUCCESS = auto()

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.casefold() == other.casefold()
        raise NotImplementedError()

    def __lt__(self, other) -> bool:
        order_list = list(type(self))
        try:
            return order_list.index(self) < order_list.index(other)
        except ValueError:
            raise NotImplementedError()

    def __hash__(self):
        return hash(self.casefold())

    def corpus(self) -> Sequence[str]:
        return tuple(map(str, self))

    @property
    def icon(self) -> str:
        """Font-awesome icon associated to each status"""
        match self.value:
            case 'pending':
                return 'fa-solid fa-clock'
            case 'started':
                return 'fa-solid fa-spinner'
            case 'success':
                return 'fa-solid fa-clipboard-check'
            case 'failure':
                return 'fa-solid fa-skull'
            case 'revoked':
                return 'fa-solid fa-hand'
            case _:
                return 'fa-solid fa-question'


TaskStatusType = Literal[
    'PENDING',
    'STARTED',
    'SUCCESS',
    'FAILURE',
    'REVOKED',
]


FINISHED_STATUSES = {
    TaskStatusEnum.REVOKED,
    TaskStatusEnum.SUCCESS,
    TaskStatusEnum.FAILURE,
}

NON_REVOKABLE_STATUSES = FINISHED_STATUSES.union({TaskStatusEnum.STARTED})


def request_flower(
    url_path: str,
    method: str = 'GET',
    body: bytes = b''
) -> requests.Response:
    """Send requests to
    :link:`Flower <https://flower.readthedocs.io/en/latest>`_
    """
    session = requests.session()
    request = requests.Request(
        url=f"http://{FLOWER_HOST}:5555/{url_path.strip('/')}",
        auth=(os.environ['FLOWER_USER'], os.environ['FLOWER_PASS']),
        method=method,
        data=body
    ).prepare()
    return session.send(request)


class LuaTask(Task):

    def __init__(self, *args, description: str = '', **kwargs):
        super().__init__(*args, **kwargs)
        self.description = description


app = Celery(
    'LuaTasks',
    broker=RABBITMQ_URL,
    backend=f'db+sqlite:///{(GLOBAL_DIR / "celery-results.db").as_posix()}',
    include=[
        'background_tasks',
    ],
    task_cls=LuaTask,
)

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    task_annotations={'*': {'track_started': True}},
    result_extended=True,
    task_send_sent_event=True,
    # Following seems to have not effect (so pass -E option to celery CLI)
    worker_send_task_events=True,
)


if __name__ == '__main__':
    app.start()
