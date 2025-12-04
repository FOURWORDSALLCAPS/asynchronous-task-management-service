from typing import Annotated
from pydantic import Field

TaskId = Annotated[int, Field(ge=1, description="ID задачи", examples=[123])]
