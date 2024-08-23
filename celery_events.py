import asyncio
import logging
import datetime
# Types
from celery import Celery
from types import NoneType
from typing import Type
from typing import Optional
from typing import Callable
from typing import TypedDict


logger = logging.getLogger('CeleryEvents')


class TaskSentEventDict(TypedDict):
    uuid: str
    name: str
    args: tuple[...]
    kwargs: dict[str, ...]
    retries: int
    eta: str
    expires: datetime
    queue: str
    exchange: str
    routing_key: str
    root_id: str
    parent_id: str


class TaskReceivedEventDict(TypedDict):
    uuid: str
    name: str
    args: tuple[...]
    kwargs: dict[str, ...]
    retries: int
    eta: str
    hostname: str
    timestamp: int
    root_id: str
    parent_id: str


class TaskStartedEventDict(TypedDict):
    uuid: str
    hostname: str
    timestamp: int
    pid: str


class TaskSucceededEventDict(TypedDict):
    uuid: str
    result: str
    runtime: int
    hostname: str
    timestamp: int


class TaskFailedEventDict(TypedDict):
    uuid: str
    exception: str
    traceback: int
    hostname: str
    timestamp: int


class TaskRejectedEventDict(TypedDict):
    uuid: str
    requeue: str


class TaskRevokedEventDict(TypedDict):
    uuid: str
    terminated: bool
    signum: str
    expired: str


class TaskRetriedEventDict(TypedDict):
    uuid: str
    exception: str
    traceback: int
    hostname: str
    timestamp: int


TaskEventDict = (
    TaskSentEventDict
    | TaskReceivedEventDict
    | TaskStartedEventDict
    | TaskSucceededEventDict
    | TaskFailedEventDict
    | TaskRejectedEventDict
    | TaskRetriedEventDict
    | TaskRevokedEventDict
)


TaskEventHandlers = TypedDict('TaskEventHandlers', {
    'task-sent': Callable[[TaskSentEventDict], NoneType],
    'task-received': Callable[[TaskReceivedEventDict], NoneType],
    'task-started': Callable[[TaskStartedEventDict], NoneType],
    'task-succeeded': Callable[[TaskSucceededEventDict], NoneType],
    'task-failed': Callable[[TaskFailedEventDict], NoneType],
    'task-rejected': Callable[[TaskRejectedEventDict], NoneType],
    'task-retried': Callable[[TaskRetriedEventDict], NoneType],
    'task-revoked': Callable[[TaskRevokedEventDict], NoneType],
})

TaskEventHandler = Callable[[TaskEventDict], NoneType]


class EventReceiver:

    def __init__(
        self,
        app: Celery,
        handlers: Optional[TaskEventHandlers] = None,
        name: str = ''
    ) -> None:
        self.app = app
        self.handlers = handlers
        self.name = name or type(self).__name__

    def run(self, **capture_kwargs):
        # Celery app monitoring
        #  state = app.events.State()
        capture_kwargs['limit'] = capture_kwargs.get('limit', None)
        capture_kwargs['timeout'] = capture_kwargs.get('timeout', None)
        capture_kwargs['wakeup'] = capture_kwargs.get('wakeup', True)
        with self.app.connection() as connection:
            recv = self.app.events.Receiver(connection, handlers=self.handlers)
            logger.info(f"Running {self.name} for capturing tasks' events")
            recv.capture(**capture_kwargs)

    def run_as_daemon(self, **capture_kwargs):
        import threading
        self._thread = threading.Thread(target=self.run, kwargs=capture_kwargs)
        self._thread.daemon = True
        self._thread.start()


async def run_event_receivers(
    app: Celery,
    *event_receiver_classes: Type[EventReceiver]
):
    """Runs all provided classes that must inherit from :class:`EventReceiver`"""
    coros = []
    for event_receiver_class in event_receiver_classes:
        event_receiver = event_receiver_class(app)
        coros.append(event_receiver.run())
    await asyncio.gather(*coros)
