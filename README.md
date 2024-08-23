# Celery example

> **DISCLAIMER**: This is meant to be a didactic repo and not supposed to be taken seriously

A really neat example of how to use:

- [RabbitMQ](https://www.rabbitmq.com/) as a broker for Celery.
- [Celery](https://docs.celeryq.dev/en/latest/index.html) to execute background tasks.
- [Flower](https://flower.readthedocs.io/en/latest/) to requests tasks information.
- **[PENDING]** `EventReceiver` custom class to monitor tasks in an event-oriented fashion.

It should work out of the box by just running:

```bash
docker volume create API_GLOBAL_DATA
docker compose up --build
```

## How code is organized?

- `app.py`: Module to execute a background task and print its result.
- `celery_example.py`: Module with Celery application and classes for tasks' statuses.
- `celery_events.py`: Module with classes for monitoring tasks' events.
- `background_tasks`: Package with background tasks registered by Celery application organized in different modules.

## What is going to happen?

The `rabbitmq` service starts, then the `celery` service starts and then the
`flower` service starts. Finally the `app.py` is executed.

You can see in the logs of the `celery` service the arguments passed to `short_task` and then, in `app` service logs, the result of the task.
