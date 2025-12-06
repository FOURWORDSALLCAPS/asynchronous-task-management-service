import sys
import logging
import asyncio
import time
from typing import Optional
from multiprocessing import get_context, Manager
from numpy import sum, array
from concurrent import futures
from datetime import datetime

from enums import PriorityType, StatusType
from repositories import TasksRepository
from services import BaseWorker
from settings import settings


log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class TaskConsumer(BaseWorker):
    def __init__(self, queue_name: str, max_workers: int = None):
        super().__init__(queue_name, prefetch_count=max_workers)
        self.tasks_repository: TasksRepository = TasksRepository()
        self.max_workers = max_workers
        self.futures: dict[int, futures.Future] = {}
        self.executor = futures.ProcessPoolExecutor(
            max_workers=self.max_workers, mp_context=get_context("spawn")
        )
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.manager = Manager()
        self.cancel_flags = self.manager.dict()

    async def process_message(self, message: dict[str]):
        task_id = message.get("id")
        task_priority = message.get("priority")

        self.loop = asyncio.get_running_loop()

        try:
            if task_priority == PriorityType.HIGH.value:
                self.cancel_flags[task_id] = False
                future = self.executor.submit(
                    self._process_task_sync,
                    task_id=task_id,
                    cancel_flags=self.cancel_flags,
                )
            else:
                future = asyncio.create_task(self._process_task_async(task_id=task_id))

            await self.tasks_repository.set_task_status(
                task_id=task_id, status=StatusType.IN_PROGRESS
            )
            await self.tasks_repository.set_task_stared_at(
                task_id=task_id, stared_at=datetime.now()
            )

            self.futures[task_id] = future
            future.add_done_callback(
                lambda futura: self.__on_task_complete(futura, task_id)
            )
        except Exception as e:
            failed_completed_at = datetime.now()
            await self.tasks_repository.set_task_status(
                task_id=task_id, status=StatusType.FAILED
            )
            await self.tasks_repository.set_task_completed_at(
                task_id=task_id, completed_at=failed_completed_at
            )
            await self.tasks_repository.set_task_error_info(
                task_id=task_id, error_info=e
            )
            log.error(f"Ошибка отправки задачи: {e}")

    async def cancel_task(self, message: dict[str]) -> bool:
        task_id = int(message.get("id"))

        if task_id not in self.futures:
            return False

        future = self.futures[task_id]
        if isinstance(future, asyncio.Future) or isinstance(future, asyncio.Task):
            if not future.done():
                future.cancel()
                try:
                    await asyncio.wait_for(future, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                await self.tasks_repository.set_task_status(
                    task_id=task_id, status=StatusType.CANCELLED
                )
        elif isinstance(future, futures.Future):
            if task_id in self.cancel_flags:
                self.cancel_flags[task_id] = True

            if not future.done():
                canceled = future.cancel()
                if canceled:
                    await self.tasks_repository.set_task_status(
                        task_id=task_id, status=StatusType.CANCELLED
                    )

        self.futures.pop(task_id, None)
        return True

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

    def __on_task_complete(self, futura, task_id):
        asyncio.run_coroutine_threadsafe(
            self.__handle_task_completion(futura, task_id), self.loop
        )

    async def __handle_task_completion(self, futura, task_id):
        failed_completed_at = datetime.now()

        try:
            if futura_exception := futura.exception():
                await self.tasks_repository.set_task_status(
                    task_id=task_id, status=StatusType.FAILED
                )
                await self.tasks_repository.set_task_completed_at(
                    task_id=task_id, completed_at=failed_completed_at
                )
                await self.tasks_repository.set_task_error_info(
                    task_id=task_id, error_info=str(futura_exception)
                )
                log.error(f"Задача {task_id} завершилась ошибкой: {futura_exception}")
            else:
                future = futura.result()
                task_id = future.get("task_id")
                status = future.get("status")
                result = future.get("result")
                completed_at = future.get("completed_at")
                error_info = future.get("error_info")
                await self.tasks_repository.set_task_status(
                    task_id=task_id, status=status
                )
                await self.tasks_repository.set_task_completed_at(
                    task_id=task_id, completed_at=completed_at
                )
                await self.tasks_repository.set_task_result(
                    task_id=task_id, result=result
                )
                await self.tasks_repository.set_task_error_info(
                    task_id=task_id, error_info=error_info
                )
        except Exception as e:
            log.error(f"Ошибка обработки результата задачи {task_id}: {e}")
        finally:
            self.futures.pop(task_id, None)

    @staticmethod
    def _process_task_sync(task_id: int, cancel_flags: dict):
        try:
            result = sum(array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]) ** 2)

            sleep_time = 10.0
            interval = 0.1

            while sleep_time > 0:
                if cancel_flags.get(task_id, False):
                    if task_id in cancel_flags:
                        del cancel_flags[task_id]
                    return {
                        "task_id": task_id,
                        "status": StatusType.CANCELLED,
                        "completed_at": datetime.now(),
                    }

                chunk = min(sleep_time, interval)
                time.sleep(chunk)
                sleep_time -= chunk

            if task_id in cancel_flags:
                del cancel_flags[task_id]

            return {
                "task_id": task_id,
                "status": StatusType.COMPLETED,
                "result": f"Получена сумма квадратов = {result}",
                "completed_at": datetime.now(),
            }
        except Exception as e:
            log.error(f"Задача {task_id} завершилась ошибкой: {e}")
            if task_id in cancel_flags:
                del cancel_flags[task_id]

            return {
                "task_id": task_id,
                "status": StatusType.FAILED,
                "completed_at": datetime.now(),
                "error_info": str(e),
            }

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
