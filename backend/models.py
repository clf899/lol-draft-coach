from typing import Literal
from pydantic import BaseModel, Field, model_validator

Role = Literal['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
class Pick(BaseModel):
    champion_id: str | None = None
    role: Role | None = None
    status: Literal['locked', 'hover'] = 'locked'

class Draft(BaseModel):
    role: Role = 'UTILITY'
    allies: list[Pick] = Field(default_factory=list, max_length=5)
    enemies: list[Pick] = Field(default_factory=list, max_length=5)
    bans: list[str] = Field(default_factory=list, max_length=10)
    pool_only: bool = False
    queue: Literal[420, 440] = 420

    @model_validator(mode='after')
    def unique_picks(self):
        selected = [p.champion_id for p in self.allies + self.enemies if p.champion_id]
        if len(selected) != len(set(selected)):
            raise ValueError('双方阵容不能重复选择同一英雄')
        if set(selected) & set(self.bans):
            raise ValueError('英雄不能同时出现在已选与 Ban 列表')
        return self

class PoolEntry(BaseModel):
    champion_id: str
    role: Role
    comfort: int = Field(ge=1, le=5)

class SyncRequest(BaseModel):
    game_name: str = Field(min_length=1, max_length=80)
    tag_line: str = Field(min_length=1, max_length=20)
    queue: Literal[420, 440] = 420
    count: int = Field(default=50, ge=10, le=100)
