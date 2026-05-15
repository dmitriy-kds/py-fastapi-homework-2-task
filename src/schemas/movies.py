import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


from database.models import MovieStatusEnum


class LanguageBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ActorBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class GenreBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CountryBase(BaseModel):
    id: int
    code: str
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int
    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = Field(default=None)
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = Field(default=None)
    status: Optional[MovieStatusEnum] = Field(default=None)
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value) -> datetime.date | None:
        if value is None:
            return None
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date cannot be more than 1 year in the future")
        return value


class MovieCreateSchema(MovieUpdateSchema):
    name: str = Field(max_length=255)
    date: datetime.date = Field()
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str | CountryBase
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date cannot be more than 1 year in the future")
        return value


class MovieDetailSchema(MovieCreateSchema):
    id: int
    country: CountryBase
    genres: List[GenreBase]
    actors: List[ActorBase]
    languages: List[LanguageBase]
