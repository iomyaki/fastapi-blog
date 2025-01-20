import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Cookie, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_async_db
from app.db.models import User, Post

router = APIRouter(
    prefix="/api",
    tags=["API"],
)
templates = Jinja2Templates(directory="templates")
sessions = {}  # in the future, replace with FastAPI-Users or another


def get_session_id(session_id: str = Cookie(default=None)):
    return session_id


@router.get("/signup/", response_class=RedirectResponse)
def render_signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup/")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=username)
    new_user.set_password(password)
    db.add(new_user)
    await db.commit()

    return RedirectResponse(url="/api/login/", status_code=303)


@router.get("/login/", response_class=RedirectResponse)
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login/")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not user.verify_password(password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    session_id = secrets.token_hex(16)
    sessions[session_id] = user.id

    response = RedirectResponse(url="/api/blog", status_code=303)
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    return response


@router.get("/logout/")
def logout():
    response = RedirectResponse(url="/api/blog", status_code=303)
    response.delete_cookie("session_id")

    return response


@router.get("/blog/", response_class=RedirectResponse)
async def get_all_blogs(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    session_id: str = Depends(get_session_id),
):
    if session_id not in sessions:
        user = False
    else:
        user = sessions[session_id]

    result = await db.execute(
        select(
            Post.id,
            Post.author_id,
            Post.title,
            Post.body,
            Post.created_at,
            User.username,
        )
        .join(User)
        .order_by(Post.created_at.desc())
    )
    posts = result.all()

    return templates.TemplateResponse(
        "posts_all.html", {"request": request, "user": user, "posts": posts}
    )


@router.get("/blog/create/", response_class=RedirectResponse)
def render_create_post_page(
    request: Request, session_id: str = Depends(get_session_id)
):
    if session_id not in sessions:
        return RedirectResponse(url="/api/login/", status_code=303)

    return templates.TemplateResponse("post_create.html", {"request": request})


@router.post("/blog/create/", response_class=RedirectResponse)
async def create_post(
    title: str = Form(...),
    body: str = Form(...),
    db: AsyncSession = Depends(get_async_db),
    session_id: str = Depends(get_session_id),
):
    user_id = sessions[session_id]
    new_post = Post(
        author_id=user_id,
        title=title,
        body=body,
    )
    db.add(new_post)

    user = await db.scalar(select(User).where(User.id == user_id))
    user.recent_post_at = datetime.now()

    await db.commit()
    await db.refresh(new_post)

    return RedirectResponse(url=f"/api/blog/{new_post.id}/", status_code=303)


@router.get("/blog/{blog_id}/", response_class=RedirectResponse)
async def get_blog(
    request: Request, blog_id: int, db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(
            Post.id,
            Post.author_id,
            Post.title,
            Post.body,
            Post.created_at,
            User.username,
        )
        .join(User)
        .where(Post.id == blog_id)
    )
    post = result.first()

    if not post:
        raise HTTPException(status_code=404, detail="Blog not found")

    return templates.TemplateResponse(
        "post_page.html", {"request": request, "post": post}
    )


@router.get("/users/", response_class=RedirectResponse)
async def get_all_users(request: Request, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(
            User.id,
            User.username,
            User.role,
            User.created_at,
            User.recent_post_at,
            func.count(Post.id).label("post_count"),
        )
        .join(Post, isouter=True)
        .group_by(
            User.id, User.username, User.role, User.created_at, User.recent_post_at
        )
        .order_by(
            func.count(Post.id).label("post_count").desc(),
            User.recent_post_at.desc(),
            User.created_at.desc(),
        )
    )
    users = result.all()

    return templates.TemplateResponse(
        "users_all.html", {"request": request, "users": users}
    )


@router.get("/users/{user_id}/", response_class=RedirectResponse)
async def get_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    session_id: str = Depends(get_session_id),
):
    if session_id not in sessions:
        owner = False
    else:
        owner = sessions[session_id] == user_id

    result_user = await db.execute(
        select(User.username, User.created_at).where(User.id == user_id)
    )
    user = result_user.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result_posts = await db.execute(
        select(Post.id, Post.title, Post.created_at, Post.body)
        .where(Post.author_id == user_id)
        .order_by(Post.created_at.desc())
    )
    posts = result_posts.all()

    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": user,
            "owner": owner,
            "posts": posts,
        },
    )
