from pydantic import BaseModel, ConfigDict, Field


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str


class SettingUpsert(BaseModel):
    scope: str = Field(min_length=1, max_length=20)
    key: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1)
