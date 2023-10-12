import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from redis_om import Field, JsonModel, Migrator

# Define AI Config model
class ConfigModel(JsonModel):
    id: str = Field(index=True, primary_key=True)
    api_id: str = Field(index=True)
    model_type: str = Field(index=True)
    api_key: str
    config : Dict[str, Any]
    date_created_timestamp: Optional[float] = Field(index=True)
    date_updated_timestamp: Optional[float] = Field(index=True)
    date_accessed_timestamp: Optional[float] = Field(index=True)

    def save(self) -> None:
        now = datetime.now()
        if self.date_created_timestamp is None:
            self.date_created_timestamp = now.timestamp()
        if self.date_accessed_timestamp is None:
            self.date_accessed_timestamp = now.timestamp()
        self.date_updated_timestamp = now.timestamp()
        super().save()

class VirtualBond(JsonModel):
    id : str = Field(index=True, primary_key=True)
    bond : str = Field(index=True)
    row_code : str = Field(index=True)
    date_created_timestamp: Optional[float] = Field(index=True)
    date_updated_timestamp: Optional[float] = Field(index=True)
    date_accessed_timestamp: Optional[float] = Field(index=True)

    def save(self) -> None:
        now = datetime.now()
        if self.date_created_timestamp is None:
            self.date_created_timestamp = now.timestamp()
        if self.date_accessed_timestamp is None:
            self.date_accessed_timestamp = now.timestamp()
        self.date_updated_timestamp = now.timestamp()
        super().save()

class Skeletons(JsonModel):
    id : str = Field(index=True, primary_key=True)
    type_model : str = Field(index=True)
    skeleton : Dict[str, Any]
    date_created_timestamp: Optional[float] = Field(index=True)
    date_updated_timestamp: Optional[float] = Field(index=True)
    date_accessed_timestamp: Optional[float] = Field(index=True)

    def save(self) -> None:
        now = datetime.now()
        if self.date_created_timestamp is None:
            self.date_created_timestamp = now.timestamp()
        if self.date_accessed_timestamp is None:
            self.date_accessed_timestamp = now.timestamp()
        self.date_updated_timestamp = now.timestamp()
        super().save()

Migrator().run()