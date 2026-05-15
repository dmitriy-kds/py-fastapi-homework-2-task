from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException
)
from httpx import Response
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
) -> dict:
    result = await db.execute(
        select(MovieModel).limit(per_page).offset(
            (page - 1) * per_page
        ).order_by(desc("id"))
    )

    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )
    total_pages = (total_items + per_page - 1) // per_page

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    return {
        "movies": movies,
        "prev_page": f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1 else None,
        "next_page": f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    existing = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    data = movie.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )
    db_movie = MovieModel(
        **data
    )

    db_country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )

    if not db_country:
        db_country = CountryModel(
            code=movie.country,
        )
        db.add(db_country)
        await db.commit()
        await db.refresh(db_country)

    db_genres = []
    for genre in movie.genres:
        db_genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == genre)
        )
        if not db_genre:
            db_genre = GenreModel(
                name=genre,
            )
            db.add(db_genre)
            await db.commit()
            await db.refresh(db_genre)
        db_genres.append(db_genre)

    db_actors = []
    for actor in movie.actors:
        db_actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == actor)
        )
        if not db_actor:
            db_actor = ActorModel(
                name=actor,
            )
            db.add(db_actor)
            await db.commit()
            await db.refresh(db_actor)
        db_actors.append(db_actor)

    db_langs = []
    for lang in movie.languages:
        db_lang = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == lang)
        )
        if not db_lang:
            db_lang = LanguageModel(
                name=lang,
            )
            db.add(db_lang)
            await db.commit()
            await db.refresh(db_lang)
        db_langs.append(db_lang)

    db_movie.country = db_country
    db_movie.genres = db_genres
    db_movie.languages = db_langs
    db_movie.actors = db_actors

    db.add(db_movie)
    await db.commit()
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == db_movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    return db_movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(db_movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> dict:
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    if db_movie.name:
        db_movie.name = movie.name

    if movie.date:
        db_movie.date = movie.date

    if movie.score:
        db_movie.score = movie.score

    if movie.overview:
        db_movie.overview = movie.overview

    if movie.status:
        db_movie.status = movie.status

    if movie.budget:
        db_movie.budget = movie.budget

    if movie.revenue:
        db_movie.revenue = movie.revenue

    db.add(db_movie)
    await db.commit()

    return {"detail": "Movie updated successfully."}
