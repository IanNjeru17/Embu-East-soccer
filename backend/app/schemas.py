from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    home_venue: str = Field(..., min_length=2, max_length=200)

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    home_venue: Optional[str] = Field(None, min_length=2, max_length=200)
    is_active: Optional[bool] = None


class PlayerCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    id_number: str = Field(..., min_length=5, max_length=50)
    id_type: str = Field(..., pattern='^(national_id|birth_certificate)$')
    team_id: int = Field(..., gt=0)
    position: Optional[str] = Field(None, pattern='^(gk|def|mid|fwd)$')
    jersey_number: Optional[int] = Field(None, ge=1, le=99)

class PlayerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    team_id: Optional[int] = Field(None, gt=0)
    position: Optional[str] = Field(None, pattern='^(gk|def|mid|fwd)$')
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    is_active: Optional[bool] = None

class FixtureGenerateRequest(BaseModel):
    season_start_date: date
    
    @validator('season_start_date')
    def validate_sunday(cls, v):
        if v.weekday() != 6:  # Sunday = 6
            raise ValueError('Season must start on a Sunday')
        return v

class FixtureUpdate(BaseModel):
    match_date: Optional[datetime] = None
    venue: Optional[str] = None
    status: Optional[str] = Field(None, pattern='^(scheduled|completed|postponed|cancelled)$')
    home_score: Optional[int] = Field(None, ge=0)
    away_score: Optional[int] = Field(None, ge=0)



class GoalCreate(BaseModel):
    player_id: int = Field(..., gt=0)
    minute: int = Field(..., ge=1, le=120)

class ResultCreate(BaseModel):
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)