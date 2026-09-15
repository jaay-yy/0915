import os
import sqlite3
from functools import wraps

from flask import abort, Flask, flash, g, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


DATABASE = "memo_service.db"

app = Flask(__name__)
# In production, always set SECRET_KEY to a long, unpredictable value.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-only-secret-key")
app.config["DATABASE"] = DATABASE


BASE_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>간단한 메모 서비스</title>
</head>
<body>
  <h1>간단한 메모 서비스</h1>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>
      {% for message in messages %}<li>{{ message }}</li>{% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  {{ content|safe }}
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
        db.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))
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


@app.route("/")
@login_required
def index():
    memos = get_db().execute(
        "SELECT id, title, created_at FROM memos WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    return page(
        """
        <p>{{ username }}님, 로그인되었습니다.</p>
        <p><a href="{{ url_for('create_memo') }}">새 메모 작성</a></p>
        <h2>내 메모</h2>
        {% if memos %}
          <ul>
          {% for memo in memos %}
            <li><a href="{{ url_for('memo_detail', memo_id=memo['id']) }}">{{ memo['title'] }}</a> ({{ memo['created_at'] }})</li>
          {% endfor %}
          </ul>
        {% else %}
          <p>작성한 메모가 없습니다.</p>
        {% endif %}
        <form action="{{ url_for('logout') }}" method="post">
          <button type="submit">로그아웃</button>
        </form>
        """,
        username=session["username"],
        memos=memos,
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
        <h2>새 메모</h2>
        <form method="post">
          <p><label>제목 <input name="title" maxlength="100" required></label></p>
          <p><label>내용<br><textarea name="content" rows="10" cols="50" required></textarea></label></p>
          <button type="submit">저장</button>
        </form>
        <p><a href="{{ url_for('index') }}">목록으로</a></p>
        """
    )


@app.route("/memos/<int:memo_id>")
@login_required
def memo_detail(memo_id):
    memo = get_memo_or_404(memo_id)
    return page(
        """
        <h2>{{ memo['title'] }}</h2>
        <p>작성: {{ memo['created_at'] }}</p>
        <p>수정: {{ memo['updated_at'] }}</p>
        <pre>{{ memo['content'] }}</pre>
        <p><a href="{{ url_for('edit_memo', memo_id=memo['id']) }}">수정</a></p>
        <form action="{{ url_for('delete_memo', memo_id=memo['id']) }}" method="post">
          <button type="submit">삭제</button>
        </form>
        <p><a href="{{ url_for('index') }}">목록으로</a></p>
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
        <h2>메모 수정</h2>
        <form method="post">
          <p><label>제목 <input name="title" value="{{ memo['title'] }}" maxlength="100" required></label></p>
          <p><label>내용<br><textarea name="content" rows="10" cols="50" required>{{ memo['content'] }}</textarea></label></p>
          <button type="submit">저장</button>
        </form>
        <p><a href="{{ url_for('memo_detail', memo_id=memo['id']) }}">상세로</a></p>
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
        <h2>회원가입</h2>
        <form method="post">
          <p><label>사용자 이름 <input name="username" required></label></p>
          <p><label>비밀번호 <input type="password" name="password" required></label></p>
          <button type="submit">가입하기</button>
        </form>
        <p><a href="{{ url_for('login') }}">로그인</a></p>
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
        <h2>로그인</h2>
        <form method="post">
          <p><label>사용자 이름 <input name="username" required></label></p>
          <p><label>비밀번호 <input type="password" name="password" required></label></p>
          <button type="submit">로그인</button>
        </form>
        <p><a href="{{ url_for('register') }}">회원가입</a></p>
        """
    )


@app.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("로그아웃되었습니다.")
    return redirect(url_for("login"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
