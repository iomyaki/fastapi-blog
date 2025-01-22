from fastapi import APIRouter, Cookie, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_async_db
from app.repositories.repository import BlogRepository, SQLAlchemyBlogRepository

router = APIRouter(
    prefix="/api",
    tags=["API"],
)


def get_session_id(session_id: str = Cookie(default=None)):
    return session_id


async def get_repository(
    database: AsyncSession = Depends(get_async_db),
) -> BlogRepository:
    return SQLAlchemyBlogRepository(database)


@router.get("/signup/", response_class=RedirectResponse)
def render_signup_page(
    request: Request, repo: BlogRepository = Depends(get_repository)
):
    return repo.render_signup_page(request)


@router.post("/signup/")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    repo: BlogRepository = Depends(get_repository),
):
    return await repo.register_user(username, password)


@router.get("/login/", response_class=RedirectResponse)
def render_login_page(request: Request, repo: BlogRepository = Depends(get_repository)):
    return repo.render_login_page(request)


@router.post("/login/")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    repo: BlogRepository = Depends(get_repository),
):
    return await repo.login_user(username, password)


@router.get("/logout/")
def logout():
    response = RedirectResponse(url="/api/blog", status_code=303)
    response.delete_cookie("session_id")

    return response


@router.get("/blog/", response_class=RedirectResponse)
async def get_all_blogs(
    request: Request,
    repo: BlogRepository = Depends(get_repository),
    session_id: str = Depends(get_session_id),
):
    return await repo.get_all_blogs(request, session_id)


@router.get("/blog/create/", response_class=RedirectResponse)
def render_create_post_page(
    request: Request,
    repo: BlogRepository = Depends(get_repository),
    session_id: str = Depends(get_session_id),
):
    return repo.render_create_post_page(request, session_id)


@router.post("/blog/create/", response_class=RedirectResponse)
async def create_post(
    title: str = Form(...),
    body: str = Form(...),
    repo: BlogRepository = Depends(get_repository),
    session_id: str = Depends(get_session_id),
):
    return await repo.create_post(title, body, session_id)


@router.get("/blog/{blog_id}/", response_class=RedirectResponse)
async def get_blog(
    request: Request, blog_id: int, repo: BlogRepository = Depends(get_repository)
):
    return await repo.get_blog(request, blog_id)


@router.get("/users/", response_class=RedirectResponse)
async def get_all_users(
    request: Request, repo: BlogRepository = Depends(get_repository)
):
    return await repo.get_all_users(request)


@router.get("/users/{user_id}/", response_class=RedirectResponse)
async def get_user(
    request: Request,
    user_id: int,
    repo: BlogRepository = Depends(get_repository),
    session_id: str = Depends(get_session_id),
):
    return await repo.get_user(request, user_id, session_id)
