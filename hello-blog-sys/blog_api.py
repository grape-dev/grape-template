"""Blog System API — FastAPI 博客发布/管理系统

功能：文章 CRUD、评论/留言/说说、文件上传、base64图片自动保存、外部视频下载、
HTML 安全过滤、博客前端页面、后台管理（admin/admin）。
连接 MySQL 数据库，通过环境变量配置 DB 和端口。
"""
import os
import re as _re
import pymysql
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import shutil
import uuid

# ====== 数据库配置 ======
DB_CONFIG = {
    "host": os.environ.get("BLOG_DB_HOST", ""),
    "port": int(os.environ.get("BLOG_DB_PORT", 3306)),
    "user": os.environ.get("BLOG_DB_USER", "root"),
    "password": os.environ.get("BLOG_DB_PASSWORD", ""),
    "database": os.environ.get("BLOG_DB_NAME", "blog_system"),
    "charset": "utf8mb4",
}

app = FastAPI(title="Blog System API", version="1.0.0")

# ====== 上传目录和允许的文件类型 ======
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"}
ALLOWED_FILE_EXT = ALLOWED_IMAGE_EXT | ALLOWED_VIDEO_EXT | {".pdf", ".doc", ".docx", ".txt", ".zip", ".tar", ".gz", ".md"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    conn.autocommit(True)
    return conn


def ensure_database():
    """首次启动时自动创建数据库和表（幂等）"""
    cfg = {**DB_CONFIG, "database": None}
    conn = pymysql.connect(**cfg)
    conn.autocommit(True)
    c = conn.cursor()
    c.execute("CREATE DATABASE IF NOT EXISTS `blog_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    c.execute("USE `blog_system`")

    # 建表（与原 Blog_system 项目对齐）
    c.execute("""
        CREATE TABLE IF NOT EXISTS `user` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `uname` VARCHAR(100) NOT NULL,
            `phone` VARCHAR(20) DEFAULT '',
            `pwd` VARCHAR(100) DEFAULT '',
            `img` VARCHAR(255) DEFAULT 'img/moren.jpg',
            `email` VARCHAR(100) DEFAULT '',
            `address` VARCHAR(255) DEFAULT '',
            `profession` VARCHAR(100) DEFAULT '',
            `deleted` INT DEFAULT 0,
            `logintime` DATETIME DEFAULT NULL,
            `createtime` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS `lable` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `lname` VARCHAR(50) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS `article` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `img` VARCHAR(255) DEFAULT NULL,
            `uid` INT DEFAULT 1,
            `title` VARCHAR(200) NOT NULL,
            `lid` INT DEFAULT 1,
            `content` LONGTEXT,
            `heat` INT DEFAULT 0,
            `deleted` INT DEFAULT 0,
            `createtime` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS `comment` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `uid` INT NOT NULL,
            `aid` INT NOT NULL,
            `content` TEXT,
            `deleted` INT DEFAULT 0,
            `createtime` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS `message` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `uid` INT NOT NULL,
            `content` TEXT,
            `deleted` INT DEFAULT 0,
            `createtime` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS `message2` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `uid` INT NOT NULL,
            `mid` INT NOT NULL,
            `content` TEXT,
            `deleted` INT DEFAULT 0,
            `createtime` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS `mood` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `title` VARCHAR(200) DEFAULT '',
            `content` TEXT,
            `src` VARCHAR(255) DEFAULT '',
            `createtime` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 插入默认标签（幂等）
    c.execute("SELECT COUNT(*) FROM lable")
    if c.fetchone()[0] == 0:
        labels = [('技术',), ('生活',), ('随笔',), ('教程',)]
        c.executemany("INSERT INTO lable(lname) VALUES(%s)", labels)

    # 插入默认用户（幂等）
    c.execute("SELECT COUNT(*) FROM user")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO user(uname,phone,pwd,img,email,deleted,createtime) "
            "VALUES('admin','admin','admin','img/moren.jpg','admin@blog.com',0,NOW())"
        )

    conn.close()


@app.on_event("startup")
def startup():
    ensure_database()
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ====== 请求模型 ======

class ArticleCreate(BaseModel):
    title: str
    content: str
    uid: int = 1
    lid: int = 1
    img: Optional[str] = None
    heat: int = 0


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    lid: Optional[int] = None
    img: Optional[str] = None
    heat: Optional[int] = None


class CommentCreate(BaseModel):
    uid: int
    aid: int
    content: str


class MessageCreate(BaseModel):
    uid: int
    content: str


class Message2Create(BaseModel):
    uid: int
    mid: int
    content: str


class MoodCreate(BaseModel):
    title: str = ""
    content: str
    src: str = ""


class LableCreate(BaseModel):
    lname: str


class UserCreate(BaseModel):
    uname: str
    phone: str = ""
    pwd: str = ""
    email: str = ""
    img: str = "img/moren.jpg"


# ====== 文章 API ======

@app.get("/api/articles")
def list_articles(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    lid: int = 0,
    keyword: str = "",
):
    """分页查询文章列表（关联用户名和标签名）"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    offset = (page - 1) * size
    sql = (
        "SELECT a.id, a.img, a.uid, a.title, a.lid, a.content, a.heat, a.deleted, "
        "a.createtime, u.uname, l.lname "
        "FROM article a LEFT JOIN user u ON a.uid=u.id LEFT JOIN lable l ON a.lid=l.id "
        "WHERE a.deleted=0"
    )
    params = []
    if lid > 0:
        sql += " AND a.lid=%s"
        params.append(lid)
    if keyword:
        sql += " AND a.title LIKE %s"
        params.append(f"%{keyword}%")
    sql += " ORDER BY a.createtime DESC LIMIT %s OFFSET %s"
    params.extend([size, offset])
    c.execute(sql, params)
    rows = c.fetchall()
    # 查总数
    count_sql = "SELECT COUNT(*) as total FROM article WHERE deleted=0"
    count_params = []
    if lid > 0:
        count_sql += " AND lid=%s"
        count_params.append(lid)
    if keyword:
        count_sql += " AND title LIKE %s"
        count_params.append(f"%{keyword}%")
    c.execute(count_sql, count_params)
    total = c.fetchone()["total"]
    conn.close()
    return {"code": 200, "data": rows, "total": total, "page": page, "size": size}


@app.get("/api/articles/{article_id}")
def get_article(article_id: int):
    """查询单篇文章详情（含评论）"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    # 热度+1
    c.execute("UPDATE article SET heat=heat+1 WHERE id=%s", (article_id,))
    # 文章详情
    c.execute(
        "SELECT a.*, u.uname, l.lname FROM article a "
        "LEFT JOIN user u ON a.uid=u.id LEFT JOIN lable l ON a.lid=l.id "
        "WHERE a.id=%s", (article_id,)
    )
    article = c.fetchone()
    if not article:
        conn.close()
        raise HTTPException(status_code=404, detail="文章不存在")
    # 评论列表
    c.execute(
        "SELECT c.*, u.uname, u.img FROM comment c "
        "LEFT JOIN user u ON c.uid=u.id "
        "WHERE c.aid=%s AND c.deleted=0 ORDER BY c.createtime DESC", (article_id,)
    )
    comments = c.fetchall()
    conn.close()
    return {"code": 200, "data": {"article": article, "comments": comments}}


@app.post("/api/articles")
def create_article(body: ArticleCreate):
    """发布新文章"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(
        "INSERT INTO article(img, uid, title, lid, content, heat, deleted, createtime) "
        "VALUES(%s, %s, %s, %s, %s, %s, 0, NOW())",
        (body.img, body.uid, body.title, body.lid, body.content, body.heat)
    )
    article_id = c.lastrowid
    conn.close()
    return {"code": 200, "message": "文章发布成功", "data": {"id": article_id}}


@app.put("/api/articles/{article_id}")
def update_article(article_id: int, body: ArticleUpdate):
    """更新文章"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM article WHERE id=%s AND deleted=0", (article_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="文章不存在")
    sets = []
    params = []
    for field, val in [("title", body.title), ("content", body.content),
                       ("lid", body.lid), ("img", body.img), ("heat", body.heat)]:
        if val is not None:
            sets.append(f"{field}=%s")
            params.append(val)
    if not sets:
        conn.close()
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    params.append(article_id)
    c.execute(f"UPDATE article SET {', '.join(sets)} WHERE id=%s", params)
    conn.close()
    return {"code": 200, "message": "文章更新成功"}


@app.delete("/api/articles/{article_id}")
def delete_article(article_id: int, soft: bool = True):
    """删除文章（默认软删除，soft=false 硬删除）"""
    conn = get_db()
    c = conn.cursor()
    if soft:
        c.execute("UPDATE article SET deleted=1 WHERE id=%s", (article_id,))
    else:
        c.execute("DELETE FROM article WHERE id=%s", (article_id,))
    affected = c.rowcount
    conn.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"code": 200, "message": "文章已删除"}


@app.post("/api/articles/{article_id}/restore")
def restore_article(article_id: int):
    """恢复软删除的文章"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE article SET deleted=0 WHERE id=%s", (article_id,))
    affected = c.rowcount
    conn.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"code": 200, "message": "文章已恢复"}


# ====== 热门文章 ======

@app.get("/api/articles/heat/top")
def top_heat_articles(limit: int = Query(5, ge=1, le=20)):
    """获取热门文章 Top N"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(
        "SELECT id, title, heat FROM article WHERE deleted=0 ORDER BY heat DESC LIMIT %s",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return {"code": 200, "data": rows}


# ====== 标签 API ======

@app.get("/api/lables")
def list_lables():
    """获取所有标签"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute("SELECT * FROM lable ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return {"code": 200, "data": rows}


@app.post("/api/lables")
def create_lable(body: LableCreate):
    """创建标签"""
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO lable(lname) VALUES(%s)", (body.lname,))
    lid = c.lastrowid
    conn.close()
    return {"code": 200, "data": {"id": lid, "lname": body.lname}}


# ====== 用户 API ======

@app.get("/api/users")
def list_users():
    """获取用户列表"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(
        "SELECT id, uname, phone, img, email, address, profession, createtime "
        "FROM user WHERE deleted=0"
    )
    rows = c.fetchall()
    conn.close()
    return {"code": 200, "data": rows}


@app.post("/api/users")
def create_user(body: UserCreate):
    """创建用户"""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO user(uname, phone, pwd, img, email, deleted, createtime) "
        "VALUES(%s, %s, %s, %s, %s, 0, NOW())",
        (body.uname, body.phone, body.pwd, body.img, body.email)
    )
    uid = c.lastrowid
    conn.close()
    return {"code": 200, "data": {"id": uid}}


# ====== 评论 API ======

@app.post("/api/comments")
def create_comment(body: CommentCreate):
    """发表评论"""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO comment(uid, aid, content, deleted, createtime) VALUES(%s, %s, %s, 0, NOW())",
        (body.uid, body.aid, body.content)
    )
    cid = c.lastrowid
    conn.close()
    return {"code": 200, "data": {"id": cid}}


@app.get("/api/comments/{aid}")
def list_comments(aid: int):
    """获取文章的评论列表"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(
        "SELECT c.*, u.uname, u.img FROM comment c "
        "LEFT JOIN user u ON c.uid=u.id "
        "WHERE c.aid=%s AND c.deleted=0 ORDER BY c.createtime DESC", (aid,)
    )
    rows = c.fetchall()
    conn.close()
    return {"code": 200, "data": rows}


@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int):
    """删除评论（软删除）"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE comment SET deleted=1 WHERE id=%s", (comment_id,))
    conn.close()
    return {"code": 200, "message": "评论已删除"}


# ====== 留言 API ======

@app.get("/api/messages")
def list_messages():
    """获取留言列表（含回复）"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(
        "SELECT m.*, u.uname, u.img FROM message m "
        "LEFT JOIN user u ON m.uid=u.id "
        "WHERE m.deleted=0 ORDER BY m.createtime DESC"
    )
    messages = c.fetchall()
    # 查每条留言的回复
    for msg in messages:
        c.execute(
            "SELECT m2.*, u.uname, u.img FROM message2 m2 "
            "LEFT JOIN user u ON m2.uid=u.id "
            "WHERE m2.mid=%s AND m2.deleted=0", (msg["id"],)
        )
        msg["replies"] = c.fetchall()
    conn.close()
    return {"code": 200, "data": messages}


@app.post("/api/messages")
def create_message(body: MessageCreate):
    """发表留言"""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO message(uid, content, deleted, createtime) VALUES(%s, %s, 0, NOW())",
        (body.uid, body.content)
    )
    mid = c.lastrowid
    conn.close()
    return {"code": 200, "data": {"id": mid}}


@app.post("/api/messages/reply")
def create_message_reply(body: Message2Create):
    """回复留言"""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO message2(uid, mid, content, deleted, createtime) VALUES(%s, %s, %s, 0, NOW())",
        (body.uid, body.mid, body.content)
    )
    rid = c.lastrowid
    conn.close()
    return {"code": 200, "data": {"id": rid}}


@app.delete("/api/messages/{message_id}")
def delete_message(message_id: int):
    """删除留言（软删除）"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE message SET deleted=1 WHERE id=%s", (message_id,))
    conn.close()
    return {"code": 200, "message": "留言已删除"}


# ====== 说说 API ======

@app.get("/api/moods")
def list_moods():
    """获取说说列表"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute("SELECT * FROM mood ORDER BY createtime DESC")
    rows = c.fetchall()
    conn.close()
    return {"code": 200, "data": rows}


@app.post("/api/moods")
def create_mood(body: MoodCreate):
    """发布说说"""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mood(title, content, src, createtime) VALUES(%s, %s, %s, NOW())",
        (body.title, body.content, body.src)
    )
    mid = c.lastrowid
    conn.close()
    return {"code": 200, "data": {"id": mid}}


@app.delete("/api/moods/{mood_id}")
def delete_mood(mood_id: int):
    """删除说说"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM mood WHERE id=%s", (mood_id,))
    conn.close()
    return {"code": 200, "message": "说说已删除"}


# ====== 前端页面 ======

# 允许的 HTML 标签白名单
_ALLOWED_TAGS = {
    "img", "video", "source", "p", "br", "hr", "div", "span", "a", "strong", "b",
    "em", "i", "u", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li",
    "blockquote", "pre", "code", "table", "thead", "tbody", "tr", "th", "td",
    "figure", "figcaption", "iframe",
}
# 允许的属性白名单
_ALLOWED_ATTRS = {"src", "href", "alt", "title", "width", "height", "style",
                  "controls", "autoplay", "loop", "muted", "preload", "poster",
                  "target", "rel", "class", "id", "colspan", "rowspan", "frameborder",
                  "allowfullscreen", "allow", "type"}


def _save_base64_image(data: str, fmt: str) -> str:
    """将 base64 图片数据保存为文件，返回 /uploads/xxx 路径"""
    import base64 as _b64
    try:
        # 补齐 padding
        missing = len(data) % 4
        if missing:
            data += '=' * (4 - missing)
        raw = _b64.b64decode(data)
        if len(raw) < 10:
            return ""  # 太小，可能不是有效图片
        ext = "jpg" if fmt in ("jpeg", "jpg") else fmt
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(save_path, "wb") as f:
            f.write(raw)
        return f"/uploads/{safe_name}"
    except Exception:
        return ""


def _process_base64_images(text: str) -> str:
    """检测内容中的 base64 图片，保存为文件并替换为 /uploads/ 路径"""
    def _replace_b64(m):
        fmt = m.group(1)
        data = m.group(2)
        url = _save_base64_image(data, fmt)
        if url:
            return f'src="{url}"'
        return m.group(0)
    # 匹配 src="data:image/xxx;base64,..." 格式
    return _re.sub(r'src=["\']data:image/(\w+);base64,([A-Za-z0-9+/=]+)["\']', _replace_b64, text)


def _download_external_media(url: str) -> str:
    """下载外部 URL 的视频/图片到 uploads 目录，返回 /uploads/xxx 路径"""
    import urllib.request as _urllib
    try:
        # 判断文件扩展名
        path_part = url.split("?")[0].split("#")[0]
        ext = os.path.splitext(path_part)[1].lower()
        if ext not in ALLOWED_FILE_EXT:
            ext = ".mp4"  # 默认按视频处理
        req = _urllib.Request(url, headers={"User-Agent": "BlogSystem/1.0"})
        with _urllib.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        if len(raw) < 100:
            return ""
        safe_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(save_path, "wb") as f:
            f.write(raw)
        return f"/uploads/{safe_name}"
    except Exception:
        return ""


def _process_external_media(text: str) -> str:
    """检测内容中的外部 URL 视频/图片，下载保存并替换为 /uploads/ 路径"""
    def _replace_ext(m):
        url = m.group(1)
        # 只处理 http/https 的外部 URL（非本站 /uploads/ 的）
        if "/uploads/" in url:
            return m.group(0)  # 已经是本站的，跳过
        local_url = _download_external_media(url)
        if local_url:
            return f'src="{local_url}"'
        return m.group(0)  # 下载失败保留原 URL
    # 匹配 src="http://..." 或 src="https://..." （非 /uploads/ 路径）
    return _re.sub(r'src="(https?://[^"]+)"', _replace_ext, text)


def _sanitize_html(text: str) -> str:
    """过滤 HTML，只允许白名单标签和属性，阻止 XSS。
    如果内容是完整 HTML 页面（含 <!DOCTYPE> 或 <html>），提取 body 内部内容。
    绝对 URL 转为相对路径，避免跨域部署图片不显示。
    base64 图片自动保存为文件。"""
    if not text:
        return ""
    # 将绝对URL转为相对路径（http://xxx:port/uploads/yyy → /uploads/yyy）
    text = _re.sub(r'https?://[^/\'"\s]+(/uploads/)', r'\1', text)
    # base64 图片自动保存为文件，替换为 /uploads/ 路径
    text = _process_base64_images(text)
    # 外部 URL 视频/图片自动下载保存，替换为 /uploads/ 路径
    text = _process_external_media(text)
    # 如果是完整 HTML 页面，提取 body 内容
    if "<!DOCTYPE" in text.upper()[:50] or "<html" in text.lower()[:50]:
        body_match = _re.search(r'<body[^>]*>(.*?)</body>', text, _re.DOTALL | _re.IGNORECASE)
        if body_match:
            text = body_match.group(1)
        else:
            # 没有 body 标签，尝试去掉 head 部分
            head_match = _re.search(r'<head[^>]*>.*?</head>', text, _re.DOTALL | _re.IGNORECASE)
            if head_match:
                text = text[:head_match.start()] + text[head_match.end():]
            # 去掉 DOCTYPE、html、head 标签
            text = _re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=_re.IGNORECASE)
            text = _re.sub(r'</?html[^>]*>', '', text, flags=_re.IGNORECASE)
            text = _re.sub(r'</?head[^>]*>', '', text, flags=_re.IGNORECASE)
            text = _re.sub(r'</?body[^>]*>', '', text, flags=_re.IGNORECASE)
            text = _re.sub(r'</?meta[^>]*/?>', '', text, flags=_re.IGNORECASE)
            text = _re.sub(r'</?title[^>]*>.*?</title>', '', text, flags=_re.DOTALL | _re.IGNORECASE)
            text = _re.sub(r'</?link[^>]*/?>', '', text, flags=_re.IGNORECASE)
    # 始终移除 <style> 标签（避免外部CSS污染页面布局）
    text = _re.sub(r'<style[^>]*>.*?</style>', '', text, flags=_re.DOTALL | _re.IGNORECASE)

    def _replace_tag(m):
        full = m.group(0)
        is_closing = m.group(1) == "/"
        tag_name = m.group(2).lower()
        if tag_name not in _ALLOWED_TAGS:
            # 对于不允许的标签，保留其内部文本内容（不丢弃内容）
            if not is_closing:
                return ""  # 丢弃开始标签
            return ""  # 丢弃闭合标签
        if is_closing:
            return f"</{tag_name}>"
        attrs_str = m.group(3) or ""
        clean_attrs = []
        for attr_match in _re.finditer(r'(\w[\w-]*)\s*=\s*"([^"]*)"|(\w[\w-]*)\s*=\s*\'([^\']*)\'|(\w[\w-]*)(?=\s|/?>)', attrs_str):
            attr_name = (attr_match.group(1) or attr_match.group(3) or attr_match.group(5) or "").lower()
            attr_val = attr_match.group(2) or attr_match.group(4) or ""
            if attr_name in _ALLOWED_ATTRS:
                if attr_name in ("src", "href") and attr_val.lower().strip().startswith("javascript:"):
                    continue
                clean_attrs.append(f'{attr_name}="{attr_val}"')
        self_close = " /" if full.rstrip().endswith("/>") else ""
        attr_part = (" " + " ".join(clean_attrs)) if clean_attrs else ""
        return f"<{tag_name}{attr_part}{self_close}>"

    pattern = _re.compile(r'<(/?)(\w[\w-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>', _re.DOTALL)
    result = pattern.sub(_replace_tag, text)
    return result


def _render_content(content: str) -> str:
    """渲染文章内容：保留安全 HTML（图片/视频等），转义裸文本"""
    if not content:
        return ""
    return _sanitize_html(content)

def _html_wrapper(title, body_html, nav_active="home"):
    """生成完整 HTML 页面"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — Blog System</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333;line-height:1.7}}
a{{text-decoration:none;color:#2563eb;transition:color .2s}}
a:hover{{color:#1d4ed8}}
.container{{max-width:1200px;margin:0 auto;padding:0 20px}}
/* Header */
.header{{background:#fff;border-bottom:1px solid #e5e7eb;position:sticky;top:0;z-index:100;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.header .container{{display:flex;align-items:center;justify-content:space-between;height:64px}}
.logo{{font-size:22px;font-weight:700;color:#111;display:flex;align-items:center;gap:8px}}
.logo span{{color:#2563eb}}
.nav{{display:flex;gap:28px}}
.nav a{{color:#666;font-size:14px;font-weight:500;transition:color .2s}}
.nav a:hover{{color:#2563eb}}
.nav a.active{{color:#2563eb}}
/* Layout */
.main{{display:flex;gap:24px;padding:30px 0;align-items:flex-start;flex-wrap:nowrap}}
.content{{flex:1 1 0;min-width:0;max-width:860px;overflow:hidden}}
.sidebar{{flex:0 0 300px;width:300px;max-width:300px;position:sticky;top:80px;max-height:calc(100vh - 100px);overflow-y:auto;align-self:flex-start}}
/* Article card */
.article-card{{background:#fff;border-radius:10px;padding:24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06);transition:box-shadow .2s,transform .2s}}
.article-card:hover{{box-shadow:0 4px 16px rgba(0,0,0,.08);transform:translateY(-1px)}}
.article-card h2{{font-size:20px;margin-bottom:8px;line-height:1.4}}
.article-card h2 a{{color:#111}}
.article-card h2 a:hover{{color:#2563eb}}
.article-card .meta{{display:flex;gap:14px;font-size:13px;color:#999;margin-bottom:10px;align-items:center;flex-wrap:wrap}}
.article-card .label-tag{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;background:#eff6ff;color:#2563eb}}
.article-card .excerpt{{color:#666;font-size:14px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word;max-width:100%}}
.article-card .cover{{width:100%;height:220px;object-fit:cover;border-radius:8px;margin-bottom:14px;display:block}}
.article-card .cover-wrap{{margin:-8px -8px 14px;border-radius:8px;overflow:hidden}}
.article-card .heat{{color:#f59e0b;font-size:13px}}
/* Sidebar widgets */
.widget{{background:#fff;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.widget h3{{font-size:16px;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #f0f0f0}}
.widget ul{{list-style:none}}
.widget li{{padding:8px 0;font-size:14px;border-bottom:1px dashed #f0f0f0}}
.widget li:last-child{{border-bottom:none}}
.widget li a{{color:#555}}
.widget li a:hover{{color:#2563eb}}
.heat-list li{{display:flex;justify-content:space-between;align-items:center}}
.heat-list .rank{{display:inline-block;width:20px;height:20px;border-radius:50%;background:#e5e7eb;color:#666;font-size:12px;text-align:center;line-height:20px;margin-right:8px;flex-shrink:0}}
.heat-list li:nth-child(1) .rank{{background:#ef4444;color:#fff}}
.heat-list li:nth-child(2) .rank{{background:#f59e0b;color:#fff}}
.heat-list li:nth-child(3) .rank{{background:#eab308;color:#fff}}
.label-cloud{{display:flex;flex-wrap:wrap;gap:8px}}
.label-cloud a{{padding:4px 12px;border-radius:4px;background:#f0f4ff;color:#2563eb;font-size:13px;transition:all .2s}}
.label-cloud a:hover{{background:#2563eb;color:#fff}}
/* Article detail */
.article-detail{{background:#fff;border-radius:10px;padding:40px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.article-detail h1{{font-size:30px;margin-bottom:14px;line-height:1.4;color:#111;font-weight:700}}
.article-detail .meta{{display:flex;gap:16px;font-size:14px;color:#999;margin-bottom:28px;padding-bottom:18px;border-bottom:1px solid #f0f0f0;flex-wrap:wrap}}
.article-detail .content-body{{font-size:16px;line-height:1.9;color:#444;word-break:break-word}}
.article-detail .content-body p{{margin:14px 0}}
.article-detail .content-body h1{{font-size:24px;margin:28px 0 14px;padding-bottom:8px;border-bottom:1px solid #f0f0f0}}
.article-detail .content-body h2{{font-size:22px;margin:28px 0 14px;color:#222;border-left:4px solid #2563eb;padding-left:12px}}
.article-detail .content-body h3{{font-size:19px;margin:24px 0 10px;color:#333}}
.article-detail .content-body h4{{font-size:17px;margin:20px 0 8px;color:#444}}
.article-detail .content-body ul,.article-detail .content-body ol{{margin:14px 0;padding-left:24px}}
.article-detail .content-body li{{margin:6px 0}}
.article-detail .content-body img{{max-width:100%;height:auto;border-radius:8px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.article-detail .content-body video{{width:100%;max-width:100%;height:auto;border-radius:8px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,.1);background:#000}}
.article-detail .content-body .video-container{{position:relative;width:100%;margin:20px 0;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
.article-detail .content-body .video-container video{{width:100%;display:block;border-radius:0;margin:0}}
.article-detail .content-body source{{display:none}}
.article-detail .content-body .figure{{margin:24px 0;text-align:center}}
.article-detail .content-body .figure img{{margin:0 auto;display:block}}
.article-detail .content-body .figcaption,.article-detail .content-body .caption{{font-size:13px;color:#999;margin-top:8px;text-align:center}}
.article-detail .content-body .highlight{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:24px 28px;border-radius:12px;margin:24px 0}}
.article-detail .content-body .highlight h3{{color:#fff;margin-top:0}}
.article-detail .content-body .highlight p{{color:rgba(255,255,255,.9)}}
.article-detail .content-body .highlight strong{{color:#fff}}
.article-detail .content-body blockquote{{margin:20px 0;padding:14px 20px;background:#f8f9fb;border-left:4px solid #2563eb;border-radius:0 6px 6px 0;color:#555;font-size:15px}}
.article-detail .content-body blockquote p{{margin:6px 0}}
.article-detail .content-body pre{{margin:16px 0;padding:16px;background:#1e293b;color:#e2e8f0;border-radius:8px;overflow-x:auto;font-size:14px;line-height:1.6}}
.article-detail .content-body code{{font-family:"Fira Code","Source Code Pro",Consolas,Monaco,monospace;font-size:14px;background:#f1f5f9;padding:2px 6px;border-radius:4px}}
.article-detail .content-body pre code{{background:transparent;padding:0;color:inherit}}
.article-detail .content-body table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}}
.article-detail .content-body th,.article-detail .content-body td{{border:1px solid #e5e7eb;padding:10px 14px;text-align:left}}
.article-detail .content-body th{{background:#f8f9fb;font-weight:600;color:#333}}
.article-detail .content-body tr:nth-child(even){{background:#fafbfc}}
.article-detail .content-body hr{{border:none;border-top:1px solid #e5e7eb;margin:28px 0}}
.article-detail .content-body .tag{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;background:#eff6ff;color:#2563eb;margin:2px 4px 2px 0}}
.article-detail .content-body .article{{max-width:100%}}
.article-detail .content-body .meta{{color:#999;font-size:14px;margin-bottom:20px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
.article-detail .content-body .footer{{margin-top:32px;padding-top:16px;border-top:1px solid #eee;font-size:14px;color:#999;text-align:center}}
.article-detail .content-body strong,.article-detail .content-body b{{font-weight:600;color:#222}}
.article-detail .content-body em,.article-detail .content-body i{{font-style:italic}}
.article-detail .content-body a{{color:#2563eb;text-decoration:underline;text-underline-offset:2px}}
.article-detail .content-body a:hover{{color:#1d4ed8}}
.article-detail .content-body iframe{{width:100%;max-width:100%;border-radius:8px;margin:16px 0;border:none;min-height:300px}}
/* Comments */
.comments-section{{margin-top:36px;padding-top:24px;border-top:1px solid #f0f0f0}}
.comments-section h3{{font-size:18px;margin-bottom:16px;color:#333}}
.comment-item{{background:#fafbfc;border-radius:8px;padding:16px;margin-bottom:10px;border:1px solid #f0f0f0}}
.comment-item .c-author{{font-weight:600;font-size:14px;color:#2563eb}}
.comment-item .c-time{{font-size:12px;color:#999;margin-left:8px}}
.comment-item .c-content{{margin-top:8px;font-size:14px;color:#555;line-height:1.7}}
.comment-form{{margin-top:20px}}
.comment-form textarea{{width:100%;padding:14px;border:1px solid #e5e7eb;border-radius:8px;font-size:14px;resize:vertical;min-height:90px;font-family:inherit;transition:border-color .2s}}
.comment-form textarea:focus{{border-color:#2563eb;outline:none;box-shadow:0 0 0 3px rgba(37,99,235,.1)}}
.comment-form button{{margin-top:10px;padding:8px 28px;background:#2563eb;color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer;transition:background .2s}}
.comment-form button:hover{{background:#1d4ed8}}
/* Pagination */
.pagination{{display:flex;justify-content:center;gap:6px;margin-top:28px}}
.pagination a,.pagination span{{padding:8px 14px;border-radius:6px;font-size:14px}}
.pagination a{{background:#fff;border:1px solid #e5e7eb;color:#555;transition:all .2s}}
.pagination a:hover{{background:#2563eb;color:#fff;border-color:#2563eb}}
.pagination .current{{background:#2563eb;color:#fff}}
/* Empty */
.empty{{text-align:center;padding:80px 20px;color:#999;font-size:16px}}
.empty a{{display:inline-block;margin-top:12px;padding:8px 24px;background:#2563eb;color:#fff;border-radius:6px;font-size:14px}}
/* Footer */
.footer{{text-align:center;padding:24px;color:#999;font-size:13px;border-top:1px solid #e5e7eb;margin-top:40px}}
/* Responsive */
@media(max-width:1024px){{
  .sidebar{{flex:0 0 260px;width:260px;max-width:260px;max-height:none;overflow:visible}}
  .content{{max-width:760px}}
}}
@media(max-width:768px){{
  .main{{flex-direction:column;padding:20px 0}}
  .sidebar{{width:100%;position:static;max-height:none;overflow:visible}}
  .content{{max-width:100%}}
  .article-detail{{padding:24px 20px}}
  .article-detail h1{{font-size:24px}}
  .article-detail .content-body h2{{font-size:19px}}
  .article-detail .content-body h3{{font-size:17px}}
  .article-detail .content-body video{{max-height:240px}}
  .article-card{{padding:18px}}
  .article-card .cover{{height:160px}}
}}
</style>
</head>
<body>
<div class="header">
<div class="container">
<a class="logo" href="/"><span>●</span>Blog System</a>
<nav class="nav">
<a href="/" class="{'active' if nav_active=='home' else ''}">首页</a>
<a href="/docs" class="{'active' if nav_active=='api' else ''}">API 文档</a>
<a href="/admin" class="{'active' if nav_active=='admin' else ''}">后台管理</a>
<a href="/health">健康检查</a>
</nav>
</div>
</div>
<div class="container">
<div class="main">
<div class="content">
{body_html}
</div>
<div class="sidebar">
{_render_sidebar()}
</div>
</div>
</div>
<div class="footer">Blog System API v1.0 · Powered by FastAPI + MySQL · 无需鉴权</div>
</body>
</html>"""


def _render_sidebar():
    """渲染侧边栏：热门文章 + 标签云"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    # 热门文章
    c.execute("SELECT id, title, heat FROM article WHERE deleted=0 ORDER BY heat DESC LIMIT 5")
    heat_articles = c.fetchall()
    # 标签
    c.execute("SELECT * FROM lable ORDER BY id")
    labels = c.fetchall()
    conn.close()

    heat_html = "<div class='widget'><h3>🔥 热门文章</h3><ul class='heat-list'>"
    if heat_articles:
        for i, a in enumerate(heat_articles):
            heat_html += f"<li><a href='/article/{a['id']}'><span class='rank'>{i+1}</span>{a['title']}</a><span class='heat'>{a['heat']}℃</span></li>"
    else:
        heat_html += "<li class='empty'>暂无热门文章</li>"
    heat_html += "</ul></div>"

    label_html = "<div class='widget'><h3>🏷 标签</h3><div class='label-cloud'>"
    if labels:
        for l in labels:
            label_html += f"<a href='/?lid={l['id']}'>{l['lname']}</a>"
    else:
        label_html += "暂无标签"
    label_html += "</div></div>"

    return heat_html + label_html


@app.get("/")
def blog_home(page: int = Query(1, ge=1), lid: int = 0, keyword: str = ""):
    """博客首页 — 文章列表"""
    size = 10
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    offset = (page - 1) * size
    sql = (
        "SELECT a.id, a.img, a.uid, a.title, a.lid, a.content, a.heat, "
        "a.createtime, u.uname, l.lname "
        "FROM article a LEFT JOIN user u ON a.uid=u.id LEFT JOIN lable l ON a.lid=l.id "
        "WHERE a.deleted=0"
    )
    params = []
    if lid > 0:
        sql += " AND a.lid=%s"
        params.append(lid)
    if keyword:
        sql += " AND a.title LIKE %s"
        params.append(f"%{keyword}%")
    sql += " ORDER BY a.createtime DESC LIMIT %s OFFSET %s"
    params.extend([size, offset])
    c.execute(sql, params)
    articles = c.fetchall()
    # 总数
    count_sql = "SELECT COUNT(*) as total FROM article WHERE deleted=0"
    count_params = []
    if lid > 0:
        count_sql += " AND lid=%s"
        count_params.append(lid)
    if keyword:
        count_sql += " AND title LIKE %s"
        count_params.append(f"%{keyword}%")
    c.execute(count_sql, count_params)
    total = c.fetchone()["total"]
    conn.close()

    total_pages = (total + size - 1) // size

    # 构建文章列表 HTML
    if articles:
        body = ""
        for a in articles:
            # 首页摘要：先清理HTML（移除style/head/meta等），再提取纯文本
            raw_content = a.get("content") or ""
            # 移除 base64 图片数据（避免摘要中出现大量乱码）
            raw_content = _re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '[图片]', raw_content)
            # 移除外部 URL（避免摘要中出现长 URL）
            raw_content = _re.sub(r'https?://[^\s"\'<>]+', '[链接]', raw_content)
            # 如果是完整HTML页面，先提取body
            if "<!DOCTYPE" in raw_content.upper()[:50] or "<html" in raw_content.lower()[:50]:
                body_m = _re.search(r'<body[^>]*>(.*?)</body>', raw_content, _re.DOTALL | _re.IGNORECASE)
                if body_m:
                    raw_content = body_m.group(1)
                else:
                    raw_content = _re.sub(r'<head[^>]*>.*?</head>', '', raw_content, flags=_re.DOTALL | _re.IGNORECASE)
                    raw_content = _re.sub(r'<!DOCTYPE[^>]*>', '', raw_content, flags=_re.IGNORECASE)
                    raw_content = _re.sub(r'</?html[^>]*>', '', raw_content, flags=_re.IGNORECASE)
            # 移除 style 标签及其内容（避免CSS代码出现在摘要中）
            raw_content = _re.sub(r'<style[^>]*>.*?</style>', '', raw_content, flags=_re.DOTALL | _re.IGNORECASE)
            # 移除 script 标签
            raw_content = _re.sub(r'<script[^>]*>.*?</script>', '', raw_content, flags=_re.DOTALL | _re.IGNORECASE)
            # 去掉所有HTML标签，只留纯文本
            plain_text = _re.sub(r'<[^>]+>', ' ', raw_content)
            plain_text = _re.sub(r'\s+', ' ', plain_text).strip()
            plain_excerpt = plain_text[:200]
            label = a.get("lname") or "未分类"
            heat = a.get("heat") or 0
            ct = str(a.get("createtime") or "")[:19]
            # 封面图：优先用 img 字段，其次从内容中提取第一张图
            cover_url = a.get("img") or ""
            # 绝对URL转相对路径
            cover_url = _re.sub(r'https?://[^/\'"\s]+(/uploads/)', r'\1', cover_url)
            if not cover_url:
                first_img = _re.search(r'<img[^>]+src=["\']([^"\']+)["\']', a.get("content") or "")
                if first_img:
                    cover_url = first_img.group(1)
            cover_html = ""
            if cover_url:
                cover_html = f'<div class="cover-wrap"><img class="cover" src="{cover_url}" alt="{a["title"]}"></div>'
            body += f"""
<div class="article-card">
{cover_html}
<h2><a href="/article/{a['id']}">{a['title']}</a></h2>
<div class="meta">
<span class="label-tag">{label}</span>
<span>👤 {a.get('uname') or '匿名'}</span>
<span>🕐 {ct}</span>
<span class="heat">🔥 {heat}℃</span>
</div>
<div class="excerpt">{plain_excerpt}...</div>
</div>"""
        # 分页
        if total_pages > 1:
            body += "<div class='pagination'>"
            if page > 1:
                body += f"<a href='/?page={page-1}&lid={lid}'>上一页</a>"
            for i in range(1, total_pages + 1):
                if i == page:
                    body += f"<span class='current'>{i}</span>"
                elif abs(i - page) <= 3:
                    body += f"<a href='/?page={i}&lid={lid}'>{i}</a>"
            if page < total_pages:
                body += f"<a href='/?page={page+1}&lid={lid}'>下一页</a>"
            body += "</div>"
    else:
        body = "<div class='empty'>暂无文章，请通过 API 发布第一篇博客吧！<br><br><a href='/docs'>前往 API 文档 →</a></div>"

    sidebar = _render_sidebar()
    title = "博客首页"
    if lid > 0:
        title += " — 筛选标签"
    if keyword:
        title += f" — 搜索: {keyword}"
    return HTMLResponse(_html_wrapper(title, body, "home"))


@app.get("/article/{article_id}")
def blog_article_detail(article_id: int):
    """文章详情页"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    # 热度+1
    c.execute("UPDATE article SET heat=heat+1 WHERE id=%s", (article_id,))
    # 查文章
    c.execute(
        "SELECT a.*, u.uname, l.lname FROM article a "
        "LEFT JOIN user u ON a.uid=u.id LEFT JOIN lable l ON a.lid=l.id "
        "WHERE a.id=%s", (article_id,)
    )
    article = c.fetchone()
    if not article:
        conn.close()
        raise HTTPException(status_code=404, detail="文章不存在")
    # 查评论
    c.execute(
        "SELECT c.*, u.uname FROM comment c "
        "LEFT JOIN user u ON c.uid=u.id "
        "WHERE c.aid=%s AND c.deleted=0 ORDER BY c.createtime DESC", (article_id,)
    )
    comments = c.fetchall()
    conn.close()

    # 构建详情 HTML
    ct = str(article.get("createtime") or "")[:19]
    content = _render_content(article.get("content") or "")
    body = f"""
<div class="article-detail">
<h1>{article['title']}</h1>
<div class="meta">
<span class="label-tag">{article.get('lname') or '未分类'}</span>
<span>👤 {article.get('uname') or '匿名'}</span>
<span>🕐 {ct}</span>
<span class="heat">🔥 {article.get('heat') or 0}℃</span>
</div>
<div class="content-body">{content}</div>
</div>"""

    # 评论区
    body += "<div class='comments-section'><h3>💬 评论"
    if comments:
        body += f" ({len(comments)})"
    body += "</h3>"
    if comments:
        for cm in comments:
            cm_time = str(cm.get("createtime") or "")[:19]
            cm_content = _render_content(cm.get("content") or "")
            body += f"""
<div class="comment-item">
<span class="c-author">{cm.get('uname') or '匿名'}</span>
<span class="c-time">{cm_time}</span>
<div class="c-content">{cm_content}</div>
</div>"""
    else:
        body += "<p style='color:#999;padding:10px 0'>暂无评论</p>"
    body += "</div>"

    sidebar = _render_sidebar()
    return HTMLResponse(_html_wrapper(article["title"], body, "home"))


# ====== 文件上传 ======


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传单个文件（图片/视频/文档），返回访问URL"""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_FILE_EXT:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}，允许: {', '.join(sorted(ALLOWED_FILE_EXT))}")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    file_type = "image" if ext in ALLOWED_IMAGE_EXT else ("video" if ext in ALLOWED_VIDEO_EXT else "file")
    url = f"/uploads/{safe_name}"
    return {"code": 200, "data": {"url": url, "filename": file.filename, "type": file_type, "size": os.path.getsize(save_path)}}


@app.post("/api/upload/multiple")
async def upload_files(files: List[UploadFile] = File(...)):
    """批量上传文件"""
    results = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_FILE_EXT:
            results.append({"filename": file.filename, "error": f"不支持的文件类型: {ext}"})
            continue
        safe_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_type = "image" if ext in ALLOWED_IMAGE_EXT else ("video" if ext in ALLOWED_VIDEO_EXT else "file")
        url = f"/uploads/{safe_name}"
        results.append({"url": url, "filename": file.filename, "type": file_type, "size": os.path.getsize(save_path)})
    return {"code": 200, "data": results}


@app.get("/api/uploads/list")
def list_uploads():
    """列出所有已上传文件"""
    files_list = []
    if os.path.isdir(UPLOAD_DIR):
        for fname in sorted(os.listdir(UPLOAD_DIR)):
            fpath = os.path.join(UPLOAD_DIR, fname)
            if os.path.isfile(fpath):
                ext = os.path.splitext(fname)[1].lower()
                file_type = "image" if ext in ALLOWED_IMAGE_EXT else ("video" if ext in ALLOWED_VIDEO_EXT else "file")
                files_list.append({
                    "filename": fname,
                    "url": f"/uploads/{fname}",
                    "type": file_type,
                    "size": os.path.getsize(fpath),
                })
    return {"code": 200, "data": files_list}


@app.delete("/api/uploads/{filename}")
def delete_upload(filename: str):
    """删除已上传文件"""
    safe_name = os.path.basename(filename)
    fpath = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.isfile(fpath):
        raise HTTPException(status_code=404, detail="文件不存在")
    os.remove(fpath)
    return {"code": 200, "message": "文件已删除"}


# ====== 后台管理 ======

ADMIN_USER = "admin"
ADMIN_PASS = "admin"
_admin_sessions = {}  # token -> expiry timestamp


def _admin_check(token: str) -> bool:
    """检查admin token是否有效"""
    import time
    if token in _admin_sessions:
        if _admin_sessions[token] > time.time():
            return True
        del _admin_sessions[token]
    return False


def _admin_login_html(error: str = ""):
    """后台登录页面"""
    err_html = f'<div class="login-error">{error}</div>' if error else ''
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>后台登录 — Blog System</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh}}
.login-box{{background:#fff;border-radius:12px;padding:40px;box-shadow:0 4px 20px rgba(0,0,0,.08);width:360px}}
.login-box h1{{font-size:24px;text-align:center;margin-bottom:8px;color:#111}}
.login-box .sub{{text-align:center;color:#999;font-size:13px;margin-bottom:28px}}
.login-box input{{width:100%;padding:12px 14px;border:1px solid #e5e7eb;border-radius:8px;font-size:14px;margin-bottom:14px;transition:border-color .2s}}
.login-box input:focus{{border-color:#2563eb;outline:none;box-shadow:0 0 0 3px rgba(37,99,235,.1)}}
.login-box button{{width:100%;padding:12px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:500;cursor:pointer;transition:background .2s}}
.login-box button:hover{{background:#1d4ed8}}
.login-error{{background:#fef2f2;color:#dc2626;padding:10px 14px;border-radius:6px;font-size:13px;margin-bottom:16px;text-align:center}}
.login-box .back{{text-align:center;margin-top:16px}}
.login-box .back a{{color:#999;font-size:13px}}
</style>
</head>
<body>
<div class="login-box">
<h1>Blog System</h1>
<p class="sub">后台管理系统</p>
{err_html}
<form method="POST" action="/admin/login">
<input type="text" name="username" placeholder="账号" required autofocus>
<input type="password" name="password" placeholder="密码" required>
<button type="submit">登 录</button>
</form>
<div class="back"><a href="/">← 返回首页</a></div>
</div>
</body>
</html>"""


def _admin_manage_html(token: str):
    """后台管理页面"""
    conn = get_db()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(
        "SELECT a.id, a.title, a.img, a.heat, a.createtime, u.uname, l.lname "
        "FROM article a LEFT JOIN user u ON a.uid=u.id LEFT JOIN lable l ON a.lid=l.id "
        "WHERE a.deleted=0 ORDER BY a.createtime DESC"
    )
    articles = c.fetchall()
    conn.close()

    rows = ""
    for a in articles:
        img_icon = "🖼️" if a.get("img") else "📝"
        ct = str(a.get("createtime") or "")[:19]
        heat = a.get("heat") or 0
        rows += f"""
<tr>
<td><input type="checkbox" class="del-checkbox" value="{a['id']}"></td>
<td>{a['id']}</td>
<td>{img_icon} {a['title'][:40]}</td>
<td>{a.get('lname') or '未分类'}</td>
<td>{a.get('uname') or '匿名'}</td>
<td>{heat}</td>
<td>{ct}</td>
<td><a href="/article/{a['id']}" target="_blank">查看</a></td>
</tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>后台管理 — Blog System</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333;line-height:1.6}}
.header{{background:#fff;border-bottom:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.header-inner{{max-width:1200px;margin:0 auto;padding:0 20px;height:60px;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:20px;color:#111}}
.header .actions{{display:flex;gap:12px;align-items:center}}
.header .user{{font-size:13px;color:#666}}
.btn{{padding:8px 18px;border:none;border-radius:6px;font-size:14px;cursor:pointer;transition:all .2s}}
.btn-danger{{background:#ef4444;color:#fff}}
.btn-danger:hover{{background:#dc2626}}
.btn-danger:disabled{{background:#ccc;cursor:not-allowed}}
.btn-outline{{background:#fff;border:1px solid #e5e7eb;color:#555}}
.btn-outline:hover{{border-color:#2563eb;color:#2563eb}}
.container{{max-width:1200px;margin:20px auto;padding:0 20px}}
.stats{{display:flex;gap:16px;margin-bottom:20px}}
.stat-card{{background:#fff;border-radius:8px;padding:16px 24px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.stat-card .num{{font-size:28px;font-weight:700;color:#2563eb}}
.stat-card .label{{font-size:13px;color:#999}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
th{{background:#f8f9fb;padding:12px 14px;text-align:left;font-size:13px;color:#666;font-weight:600;border-bottom:1px solid #e5e7eb}}
td{{padding:12px 14px;border-bottom:1px solid #f0f0f0;font-size:14px}}
tr:hover{{background:#fafbfc}}
.del-checkbox{{cursor:pointer;width:16px;height:16px}}
.toolbar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}}
.toolbar .select-info{{font-size:14px;color:#666}}
.logout{{font-size:13px;color:#999;text-decoration:none}}
.logout:hover{{color:#ef4444}}
</style>
</head>
<body>
<div class="header">
<div class="header-inner">
<h1>📊 博客后台管理</h1>
<div class="actions">
<span class="user">已登录: admin</span>
<a href="/" class="btn btn-outline">首页</a>
<a href="/admin/logout?t={token}" class="logout">退出登录</a>
</div>
</div>
</div>
<div class="container">
<div class="stats">
<div class="stat-card"><div class="num">{len(articles)}</div><div class="label">文章总数</div></div>
</div>
<div class="toolbar">
<div class="select-info" id="selInfo">未选择文章</div>
<button class="btn btn-danger" id="delBtn" onclick="deleteSelected()" disabled>删除选中</button>
</div>
<table>
<thead>
<tr>
<th><input type="checkbox" id="selectAll" onclick="toggleAll()"></th>
<th>ID</th>
<th>标题</th>
<th>标签</th>
<th>作者</th>
<th>热度</th>
<th>发布时间</th>
<th>操作</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<script>
function toggleAll() {{
    const checked = document.getElementById('selectAll').checked;
    document.querySelectorAll('.del-checkbox').forEach(cb => cb.checked = checked);
    updateInfo();
}}
function updateInfo() {{
    const checked = document.querySelectorAll('.del-checkbox:checked');
    const btn = document.getElementById('delBtn');
    const info = document.getElementById('selInfo');
    if (checked.length === 0) {{
        btn.disabled = true;
        info.textContent = '未选择文章';
    }} else {{
        btn.disabled = false;
        info.textContent = '已选择 ' + checked.length + ' 篇文章';
    }}
}}
document.querySelectorAll('.del-checkbox').forEach(cb => cb.addEventListener('change', updateInfo));
function deleteSelected() {{
    const checked = document.querySelectorAll('.del-checkbox:checked');
    if (checked.length === 0) return;
    if (!confirm('确定删除选中的 ' + checked.length + ' 篇文章吗？此操作不可恢复！')) return;
    const ids = Array.from(checked).map(cb => cb.value);
    fetch('/admin/api/delete', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{ids: ids, token: '{token}'}})
    }}).then(r => r.json()).then(data => {{
        if (data.code === 200) {{
            alert('删除成功：' + data.deleted + ' 篇文章');
            location.reload();
        }} else {{
            alert('删除失败：' + (data.message || '未知错误'));
        }}
    }}).catch(e => alert('请求失败: ' + e));
}}
</script>
</body>
</html>"""


@app.get("/admin")
def admin_page(request: Request):
    """后台管理入口（带 cookie 检查）"""
    token = request.cookies.get("admin_token", "")
    if _admin_check(token):
        return HTMLResponse(_admin_manage_html(token))
    return HTMLResponse(_admin_login_html())


@app.post("/admin/login")
async def admin_login(request: Request):
    """后台登录"""
    import time, secrets
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    if username == ADMIN_USER and password == ADMIN_PASS:
        token = secrets.token_hex(16)
        _admin_sessions[token] = time.time() + 7200
        resp = RedirectResponse(url="/admin", status_code=302)
        resp.set_cookie(key="admin_token", value=token, httponly=True, max_age=7200)
        return resp
    return HTMLResponse(_admin_login_html(error="账号或密码错误"))


@app.get("/admin/logout")
def admin_logout(t: str = ""):
    """退出登录"""
    if t and t in _admin_sessions:
        del _admin_sessions[t]
    resp = RedirectResponse(url="/admin", status_code=302)
    resp.delete_cookie(key="admin_token")
    return resp


@app.post("/admin/api/delete")
async def admin_delete_articles(request: Request):
    """后台批量删除文章"""
    body = await request.json()
    token = body.get("token", "")
    if not _admin_check(token):
        return {"code": 401, "message": "未登录或登录已过期"}
    ids = body.get("ids", [])
    if not ids:
        return {"code": 400, "message": "未选择文章"}
    conn = get_db()
    c = conn.cursor()
    deleted = 0
    for aid in ids:
        c.execute("DELETE FROM article WHERE id=%s", (int(aid),))
        if c.rowcount > 0:
            deleted += 1
    conn.close()
    return {"code": 200, "deleted": deleted, "message": f"成功删除 {deleted} 篇文章"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "blog-api", "version": "1.0.0"}


# ====== 启动 ======

def _find_available_port(default: int = 80, candidates: list = None) -> int:
    """查找可用端口：优先默认端口，被占则依次尝试候选端口"""
    import socket
    if candidates is None:
        candidates = [80, 8080, 8000, 8888, 18080, 3000, 5000, 9000]
    for port in candidates:
        if not isinstance(port, int) or port < 0 or port > 65535:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    # 所有候选端口都被占，让系统分配随机端口
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            return s.getsockname()[1]
    except OSError:
        return 18080


if __name__ == "__main__":
    import uvicorn
    configured_port = os.environ.get("BLOG_API_PORT")
    if configured_port:
        port = int(configured_port)
    else:
        port = _find_available_port()
        if port != 80:
            print(f"[提示] 80 端口被占用，自动使用 {port} 端口")
    print(f"[启动] 博客系统运行在 0.0.0.0:{port}")
    uvicorn.run("blog_api:app", host="0.0.0.0", port=port, log_level="info")
