import uuid

from pydantic import BaseModel, ConfigDict


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nickname: str
    sso_subject: str
