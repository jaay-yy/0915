import os
import sqlite3
from functools import wraps

from flask import abort, Flask, flash, g, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


DATABASE = os.environ.get("DATABASE", "memo_service.db")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin1234")
CHALLENGE_FLAG = "SBOB{1234567890qwertyuiop}"

app = Flask(__name__)
# In production, always set SECRET_KEY to a long, unpredictable value.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-only-secret-key")
app.config["DATABASE"] = DATABASE


BASE_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>간단한 메모 서비스</title>
  <style>
    :root { --blue: #1d4ed8; --blue-dark: #163b9d; --ink: #111827; --muted: #667085; --line: #d9e1ee; --surface: #ffffff; --page: #f4f7fc; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--page); color: var(--ink); font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; font-size: 16px; line-height: 1.6; }
    a { color: inherit; text-decoration: none; }
    .site-header { background: var(--surface); border-bottom: 1px solid var(--line); }
    .header-inner { width: min(920px, calc(100% - 32px)); min-height: 72px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
    .brand { color: var(--blue); font-size: 25px; font-weight: 900; letter-spacing: -1.5px; }
    .brand-mark { display: inline-grid; width: 28px; height: 28px; margin-right: 7px; place-items: center; border-radius: 8px; background: var(--blue); color: #fff; font-size: 17px; vertical-align: -2px; }
    .global-nav { display: flex; align-items: center; gap: 16px; color: var(--muted); font-size: 14px; font-weight: 700; }
    .global-nav a:hover { color: var(--blue-dark); }
    .page-shell { width: min(920px, calc(100% - 32px)); margin: 32px auto 56px; }
    .content-card { padding: 32px; border: 1px solid var(--line); border-radius: 16px; background: var(--surface); box-shadow: 0 3px 12px rgba(0, 0, 0, .035); }
    h1, h2 { margin: 0; letter-spacing: -1px; line-height: 1.3; }
    h2 { font-size: 25px; }
    p { margin: 12px 0; }
    .kicker { margin: 0 0 5px; color: var(--blue-dark); font-size: 12px; font-weight: 800; letter-spacing: .08em; }
    .dashboard-heading { display: flex; align-items: end; justify-content: space-between; gap: 16px; padding-bottom: 24px; border-bottom: 1px solid var(--line); }
    .admin-shortcut { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 22px 0; padding: 15px 16px; border: 1px solid #b8cdf6; border-radius: 10px; background: #f5f8ff; }
    .admin-shortcut strong { color: var(--blue-dark); }
    .action-link, button { display: inline-flex; min-height: 42px; align-items: center; justify-content: center; padding: 9px 16px; border: 0; border-radius: 8px; background: var(--blue); color: #fff; cursor: pointer; font: inherit; font-weight: 800; }
    .action-link:hover, button:hover { background: var(--blue-dark); }
    button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible { outline: 3px solid rgba(29, 78, 216, .28); outline-offset: 2px; }
    .flash-list { margin: 0 0 16px; padding: 12px 16px 12px 34px; border-radius: 10px; background: #eff6ff; color: #1e40af; font-weight: 700; }
    .memo-list { margin: 16px 0 0; padding: 0; list-style: none; }
    .memo-list li { margin-top: 10px; border: 1px solid var(--line); border-radius: 10px; transition: border-color .15s, box-shadow .15s; }
    .memo-list li:hover { border-color: #9ab7f3; box-shadow: 0 4px 10px rgba(29, 78, 216, .08); }
    .memo-list a { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 15px 16px; font-weight: 800; }
    .memo-list time { flex: none; color: var(--muted); font-size: 13px; font-weight: 500; }
    .stack-form { max-width: 640px; margin-top: 22px; }
    .stack-form p { margin: 18px 0; }
    label { display: block; font-size: 14px; font-weight: 800; }
    input, textarea { width: 100%; margin-top: 7px; padding: 11px 12px; border: 1px solid #cfd4da; border-radius: 8px; background: #fff; color: var(--ink); font: inherit; font-weight: 400; }
    textarea { min-height: 180px; resize: vertical; }
    .sub-link { display: inline-block; margin-top: 18px; color: var(--muted); font-size: 14px; font-weight: 700; }
    .sub-link:hover { color: var(--blue-dark); text-decoration: underline; }
    .memo-detail { max-width: 720px; }
    .memo-meta { color: var(--muted); font-size: 14px; }
    .memo-body { margin: 24px 0; padding: 20px; border-radius: 10px; background: #f8faf9; white-space: pre-wrap; font: inherit; }
    .detail-actions { display: flex; gap: 10px; align-items: center; }
    .detail-actions form { margin: 0; }
    .button-secondary { background: #eaf1ff; color: #1e40af; }
    .button-danger { background: #f04452; }
    table { width: 100%; margin-top: 22px; border-collapse: collapse; font-size: 15px; }
    th, td { padding: 13px 12px; border-bottom: 1px solid var(--line); text-align: left; }
    th { background: #f8faf9; color: var(--muted); font-size: 13px; }
    @media (max-width: 600px) { .header-inner { min-height: 62px; } .global-nav { gap: 10px; font-size: 13px; } .page-shell { margin-top: 16px; } .content-card { padding: 22px 18px; border-radius: 12px; } .dashboard-heading, .admin-shortcut { display: block; } .dashboard-heading .action-link, .admin-shortcut .action-link { margin-top: 16px; } .memo-list a { align-items: flex-start; flex-direction: column; gap: 2px; } }
  </style>
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{{ url_for('index') }}"><span class="brand-mark">M</span>메모온</a>
      <nav class="global-nav" aria-label="주요 메뉴">
        {% if session.get('user_id') %}
          <a href="{{ url_for('index') }}">내 메모</a>
          <a href="{{ url_for('create_memo') }}">새 메모</a>
          <form action="{{ url_for('logout') }}" method="post"><button type="submit">로그아웃</button></form>
        {% else %}
          <a href="{{ url_for('login') }}">로그인</a>
          <a href="{{ url_for('register') }}">회원가입</a>
        {% endif %}
      </nav>
    </div>
  </header>
  <main class="page-shell">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul class="flash-list">
        {% for message in messages %}<li>{{ message }}</li>{% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <section class="content-card">{{ content|safe }}</section>
  </main>
</body>
</html>
"""


def get_db():
    """Return one SQLite connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        user_columns = {
            column["name"] for column in db.execute("PRAGMA table_info(users)").fetchall()
        }
        if "is_admin" not in user_columns:
            db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        admin = db.execute(
            "SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)
        ).fetchone()
        if admin is None:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)),
            )
            admin_id = cursor.lastrowid
        else:
            admin_id = admin["id"]
            db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (admin_id,))

        # Remove only the old app-generated seed record, not user-authored memos.
        db.execute(
            "DELETE FROM memos WHERE user_id = ? AND title = ?",
            (admin_id, "운영 기록"),
        )
        flag_memo = db.execute(
            "SELECT id FROM memos WHERE user_id = ? AND content = ?",
            (admin_id, CHALLENGE_FLAG),
        ).fetchone()
        if flag_memo is None:
            db.execute(
                "INSERT INTO memos (user_id, title, content) VALUES (?, ?, ?)",
                (admin_id, "주간 점검", CHALLENGE_FLAG),
            )
        db.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def api_error(status, message):
    return {"error": message}, status


def api_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return api_error(401, "authentication required")

        user = get_db().execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            session.clear()
            return api_error(401, "authentication required")
        return view(*args, **kwargs)

    return wrapped_view


def is_current_user_admin():
    if "user_id" not in session:
        return False
    user = get_db().execute(
        "SELECT is_admin FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    return user is not None and user["is_admin"] == 1


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))
        if not is_current_user_admin():
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view


def page(content, **context):
    return render_template_string(BASE_HTML, content=render_template_string(content, **context))


def get_memo_or_404(memo_id):
    """Return a memo only when it belongs to the signed-in user."""
    memo = get_db().execute(
        "SELECT id, title, content, created_at, updated_at FROM memos WHERE id = ? AND user_id = ?",
        (memo_id, session["user_id"]),
    ).fetchone()
    if memo is None:
        abort(404)
    return memo


def note_object(note):
    return {
        "id": note["id"],
        "title": note["title"],
        "body": note["content"],
        "created_at": note["created_at"],
        "updated_at": note["updated_at"],
    }


@app.route("/api/notes", methods=("GET", "POST"))
@api_login_required
def api_notes():
    db = get_db()
    if request.method == "GET":
        notes = db.execute(
            """
            SELECT id, title, content, created_at, updated_at
            FROM memos WHERE user_id = ? ORDER BY id DESC
            """,
            (session["user_id"],),
        ).fetchall()
        return {"notes": [note_object(note) for note in notes]}

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error(400, "JSON object with a title is required")

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return api_error(400, "title is required")

    body = payload.get("body", "")
    if not isinstance(body, str):
        return api_error(400, "body must be a string")

    cursor = db.execute(
        "INSERT INTO memos (user_id, title, content) VALUES (?, ?, ?)",
        (session["user_id"], title.strip(), body),
    )
    db.commit()
    note = db.execute(
        "SELECT id, title, content, created_at, updated_at FROM memos WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return note_object(note), 201


@app.route("/api/notes/<int:note_id>")
@api_login_required
def api_note_detail(note_id):
    note = get_db().execute(
        """
        SELECT id, title, content, created_at, updated_at
        FROM memos WHERE id = ? AND user_id = ?
        """,
        (note_id, session["user_id"]),
    ).fetchone()
    if note is None:
        return api_error(404, "note not found")
    return note_object(note)


@app.route("/")
@login_required
def index():
    memos = get_db().execute(
        "SELECT id, title, created_at FROM memos WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    return page(
        """
        <div class="dashboard-heading">
          <div>
            <p class="kicker">MY NOTES</p>
            <h2>{{ username }}님의 메모</h2>
          </div>
          <a class="action-link" href="{{ url_for('create_memo') }}">+ 새 메모 작성</a>
        </div>
        {% if is_admin %}
          <div class="admin-shortcut">
            <strong>관리자 전용 메뉴</strong>
            <a class="action-link" href="{{ url_for('admin_users') }}">전체 회원 목록 관리 →</a>
          </div>
        {% endif %}
        {% if memos %}
          <ul class="memo-list">
          {% for memo in memos %}
            <li><a href="{{ url_for('memo_detail', memo_id=memo['id']) }}"><span>{{ memo['title'] }}</span><time>{{ memo['created_at'] }}</time></a></li>
          {% endfor %}
          </ul>
        {% else %}
          <p>아직 작성한 메모가 없습니다. 첫 메모를 남겨보세요.</p>
        {% endif %}
        """,
        username=session["username"],
        memos=memos,
        is_admin=is_current_user_admin(),
    )


@app.route("/admin/users")
@admin_required
def admin_users():
    users = get_db().execute(
        "SELECT id, username, is_admin FROM users ORDER BY id ASC"
    ).fetchall()
    return page(
        """
        <p class="kicker">ADMIN</p>
        <h2>전체 회원 목록</h2>
        <table>
          <tr><th>ID</th><th>사용자 이름</th><th>권한</th></tr>
          {% for user in users %}
            <tr>
              <td>{{ user['id'] }}</td>
              <td>{{ user['username'] }}</td>
              <td>{% if user['is_admin'] %}관리자{% else %}일반 사용자{% endif %}</td>
            </tr>
          {% endfor %}
        </table>
        <p><a class="sub-link" href="{{ url_for('index') }}">내 메모 목록으로</a></p>
        """,
        users=users,
    )


@app.route("/memos/new", methods=("GET", "POST"))
@login_required
def create_memo():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("제목과 내용을 모두 입력하세요.")
        elif len(title) > 100:
            flash("제목은 100자 이하여야 합니다.")
        else:
            db = get_db()
            db.execute(
                "INSERT INTO memos (user_id, title, content) VALUES (?, ?, ?)",
                (session["user_id"], title, content),
            )
            db.commit()
            flash("메모를 저장했습니다.")
            return redirect(url_for("index"))

    return page(
        """
        <p class="kicker">WRITE</p>
        <h2>새 메모 작성</h2>
        <form class="stack-form" method="post">
          <p><label>제목 <input name="title" maxlength="100" required></label></p>
          <p><label>내용<br><textarea name="content" rows="10" cols="50" required></textarea></label></p>
          <button type="submit">저장</button>
        </form>
        <p><a class="sub-link" href="{{ url_for('index') }}">목록으로</a></p>
        """
    )


@app.route("/memos/<int:memo_id>")
@login_required
def memo_detail(memo_id):
    memo = get_memo_or_404(memo_id)
    return page(
        """
        <article class="memo-detail">
          <p class="kicker">NOTE</p>
          <h2>{{ memo['title'] }}</h2>
          <p class="memo-meta">작성 {{ memo['created_at'] }} · 수정 {{ memo['updated_at'] }}</p>
          <pre class="memo-body">{{ memo['content'] }}</pre>
          <div class="detail-actions">
            <a class="action-link button-secondary" href="{{ url_for('edit_memo', memo_id=memo['id']) }}">수정</a>
            <form action="{{ url_for('delete_memo', memo_id=memo['id']) }}" method="post">
              <button class="button-danger" type="submit">삭제</button>
            </form>
          </div>
          <p><a class="sub-link" href="{{ url_for('index') }}">목록으로</a></p>
        </article>
        """,
        memo=memo,
    )


@app.route("/memos/<int:memo_id>/edit", methods=("GET", "POST"))
@login_required
def edit_memo(memo_id):
    memo = get_memo_or_404(memo_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("제목과 내용을 모두 입력하세요.")
        elif len(title) > 100:
            flash("제목은 100자 이하여야 합니다.")
        else:
            db = get_db()
            db.execute(
                """
                UPDATE memos
                SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (title, content, memo_id, session["user_id"]),
            )
            db.commit()
            flash("메모를 수정했습니다.")
            return redirect(url_for("memo_detail", memo_id=memo_id))

    return page(
        """
        <p class="kicker">EDIT</p>
        <h2>메모 수정</h2>
        <form class="stack-form" method="post">
          <p><label>제목 <input name="title" value="{{ memo['title'] }}" maxlength="100" required></label></p>
          <p><label>내용<br><textarea name="content" rows="10" cols="50" required>{{ memo['content'] }}</textarea></label></p>
          <button type="submit">저장</button>
        </form>
        <p><a class="sub-link" href="{{ url_for('memo_detail', memo_id=memo['id']) }}">상세로</a></p>
        """,
        memo=memo,
    )


@app.route("/memos/<int:memo_id>/delete", methods=("POST",))
@login_required
def delete_memo(memo_id):
    get_memo_or_404(memo_id)
    db = get_db()
    db.execute("DELETE FROM memos WHERE id = ? AND user_id = ?", (memo_id, session["user_id"]))
    db.commit()
    flash("메모를 삭제했습니다.")
    return redirect(url_for("index"))


@app.route("/register", methods=("GET", "POST"))
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("사용자 이름과 비밀번호를 모두 입력하세요.")
        elif len(username) > 50:
            flash("사용자 이름은 50자 이하여야 합니다.")
        else:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("이미 사용 중인 사용자 이름입니다.")
            else:
                flash("회원가입이 완료되었습니다. 로그인해 주세요.")
                return redirect(url_for("login"))

    return page(
        """
        <p class="kicker">JOIN</p>
        <h2>회원가입</h2>
        <form class="stack-form" method="post">
          <p><label>사용자 이름 <input name="username" required></label></p>
          <p><label>비밀번호 <input type="password" name="password" required></label></p>
          <button type="submit">가입하기</button>
        </form>
        <p><a class="sub-link" href="{{ url_for('login') }}">이미 계정이 있나요? 로그인</a></p>
        """
    )


@app.route("/login", methods=("GET", "POST"))
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

    return page(
        """
        <p class="kicker">WELCOME</p>
        <h2>로그인</h2>
        <form class="stack-form" method="post">
          <p><label>사용자 이름 <input name="username" required></label></p>
          <p><label>비밀번호 <input type="password" name="password" required></label></p>
          <button type="submit">로그인</button>
        </form>
        <p><a class="sub-link" href="{{ url_for('register') }}">처음이신가요? 회원가입</a></p>
        """
    )


@app.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("로그아웃되었습니다.")
    return redirect(url_for("login"))


init_db()


if __name__ == "__main__":
#   app.run(debug=True)
    app.run(host="0.0.0.0", port=8000)
