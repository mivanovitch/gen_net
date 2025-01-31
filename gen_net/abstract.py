from abc import ABC
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field


class AbstractObject(BaseModel, ABC):
    class Config:
        arbitrary_types_allowed = True

    id: str = Field(default="", title="unique identifier")
    metadata: dict = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = self.__class__.__name__ + ":" + str(uuid4())

    def __str__(self):
        return yaml.dump(self.dict(), sort_keys=False)

    def __hash__(self):
        return hash(self.id)
