import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional



from redis_om import Field, JsonModel, Migrator

class VirtualBond(JsonModel):
    id : str = Field(index=True, primary_key=True)
    row_code : str = Field(index=True)
    description : Optional[str] = Field(index=True)
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
# API Keys Wallet
class Wallet(JsonModel):
    id : Optional[str] = Field(index=True, primary_key=True)
    token : str = Field(index=True)
    apis_id : Skeletons.id = Field(index=True)
    keys : str = Field(index=True)
    date_created_timestamp: Optional[float] = Field(index=True)
    date_updated_timestamp: Optional[float] = Field(index=True)
    date_accessed_timestamp: Optional[float] = Field(index=True)

    def save(self) -> None:
        now = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.date_created_timestamp is None:
            self.date_created_timestamp = now.timestamp()
        if self.date_accessed_timestamp is None:
            self.date_accessed_timestamp = now.timestamp()
        self.date_updated_timestamp = now.timestamp()
        super().save()

# Define AI Config model
class ConfigModel(JsonModel):
    id: str = Field(index=True, primary_key=True)
    api_id: str = Field(index=True)
    api_key: Optional[str]
    function_name : str = Field(index=True)
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

Migrator().run()