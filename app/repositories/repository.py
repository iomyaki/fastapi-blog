import secrets
from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Post

templates = Jinja2Templates(directory="templates")
sessions = {}  # in the future, replace with FastAPI-Users or another


class BlogRepository(ABC):
    @abstractmethod
    def render_signup_page(self, request):
        pass

    @abstractmethod
    async def register_user(self, username, password):
        pass

    @abstractmethod
    def render_login_page(self, request):
        pass

    @abstractmethod
    async def login_user(self, username, password):
        pass

    @abstractmethod
    async def get_all_blogs(self, request, session_id):
        pass

    @abstractmethod
    def render_create_post_page(self, request, session_id):
        pass

    @abstractmethod
    async def create_post(self, title, body, session_id):
        pass

    @abstractmethod
    async def get_blog(self, request, blog_id):
        pass

    @abstractmethod
    async def get_all_users(self, request):
        pass

    @abstractmethod
    async def get_user(self, request, user_id, session_id):
        pass


class SQLAlchemyBlogRepository(BlogRepository):
    def __init__(self, database: AsyncSession):
        self.db = database

    def render_signup_page(self, request):
        return templates.TemplateResponse("signup.html", {"request": request})

    async def register_user(self, username, password):
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if user:
            raise HTTPException(status_code=400, detail="Username already exists")

        new_user = User(username=username)
        new_user.set_password(password)
        self.db.add(new_user)
        await self.db.commit()

        return RedirectResponse(url="/api/login/", status_code=303)

    def render_login_page(self, request):
        return templates.TemplateResponse("login.html", {"request": request})

    async def login_user(self, username, password):
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if not user or not user.verify_password(password):
            raise HTTPException(status_code=400, detail="Invalid username or password")

        session_id = secrets.token_hex(16)
        sessions[session_id] = user.id

        response = RedirectResponse(url="/api/blog", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True)

        return response

    async def get_all_blogs(self, request, session_id):
        if session_id not in sessions:
            user = False
        else:
            user = sessions[session_id]

        result = await self.db.execute(
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

    def render_create_post_page(self, request, session_id):
        if session_id not in sessions:
            return RedirectResponse(url="/api/login/", status_code=303)

        return templates.TemplateResponse("post_create.html", {"request": request})

    async def create_post(self, title, body, session_id):
        user_id = sessions[session_id]
        new_post = Post(
            author_id=user_id,
            title=title,
            body=body,
        )
        self.db.add(new_post)

        user = await self.db.scalar(select(User).where(User.id == user_id))
        user.recent_post_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(new_post)

        return RedirectResponse(url=f"/api/blog/{new_post.id}/", status_code=303)

    async def get_blog(self, request, blog_id):
        result = await self.db.execute(
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

    async def get_all_users(self, request):
        result = await self.db.execute(
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

    async def get_user(self, request, user_id, session_id):
        if session_id not in sessions:
            owner = False
        else:
            owner = sessions[session_id] == user_id

        result_user = await self.db.execute(
            select(User.username, User.created_at).where(User.id == user_id)
        )
        user = result_user.first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result_posts = await self.db.execute(
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
