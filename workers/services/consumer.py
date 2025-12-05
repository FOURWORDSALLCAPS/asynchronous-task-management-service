import sys
import logging
import asyncio
import time
from multiprocessing import get_context
from numpy import sum, array
from concurrent import futures
from datetime import datetime

from enums import PriorityType, StatusType
from services import BaseWorker
from settings import settings


log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class TaskConsumer(BaseWorker):
    def __init__(self, queue_name: str, max_workers: int = None):
        super().__init__(queue_name, prefetch_count=max_workers)
        self.max_workers = max_workers
        self.futures: dict[str, futures.Future] = {}
        self.executor = futures.ProcessPoolExecutor(
            max_workers=self.max_workers, mp_context=get_context("spawn")
        )

    async def process_message(self, message: dict[int | str]):
        try:
            task_id = message.get("id")
            task_priority = message.get("priority")

            if task_priority == PriorityType.HIGH.value:
                future = self.executor.submit(self._process_task_sync, task_id=task_id)
            else:
                future = asyncio.create_task(self._process_task_async(task_id=task_id))

            self.futures[task_id] = future
            future.add_done_callback(
                lambda futura: self.__on_task_complete(futura, task_id)
            )
        except Exception as e:
            log.error(f"Ошибка отправки задачи: {e}")

    def __on_task_complete(self, futura, task_id):
        try:
            if futura_exception := futura.exception():
                log.error(f"Задача {task_id} завершилась ошибкой: {futura_exception}")
            else:
                future = futura.result()
                status = future.get("status")  # noqa
                result = future.get("result")  # noqa
                completed_at = future.get("completed_at")  # noqa
                error_info = future.get("error_info")  # noqa
        except Exception as e:
            log.error(f"Ошибка обработки результата задачи {task_id}: {e}")
        finally:
            self.futures.pop(task_id, None)

    async def stop(self):
        if self.futures:
            log.info(f"Ожидаем завершения задач: {len(self.futures)}")

            running_futures = [
                f
                for f in self.futures.values()
                if isinstance(f, futures.Future) and not f.done()
            ]

            if running_futures:
                done, not_done = futures.wait(
                    running_futures, timeout=30, return_when=futures.ALL_COMPLETED
                )

                for future in not_done:
                    future.cancel()

        self.executor.shutdown(wait=True)

    @staticmethod
    async def _process_task_async(task_id: int):
        try:
            result = "Получен id пользователя = 555"
            await asyncio.sleep(10)
            return {
                "task_id": task_id,
                "status": StatusType.COMPLETED,
                "result": result,
                "completed_at": datetime.now(),
            }
        except Exception as e:
            log.error(f"Задача {task_id} завершилась ошибкой: {e}")
            return {
                "task_id": task_id,
                "status": StatusType.FAILED,
                "completed_at": datetime.now(),
                "error_info": str(e),
            }

    @staticmethod
    def _process_task_sync(task_id: int):
        try:
            result = sum(array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]) ** 2)
            time.sleep(10)
            return {
                "task_id": task_id,
                "status": StatusType.COMPLETED,
                "result": f"Получена сумма квадратов = {result}",
                "completed_at": datetime.now(),
            }
        except Exception as e:
            log.error(f"Задача {task_id} завершилась ошибкой: {e}")
            return {
                "task_id": task_id,
                "status": StatusType.FAILED,
                "completed_at": datetime.now(),
                "error_info": str(e),
            }
