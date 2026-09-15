import os
import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template_string, request, session, url_for
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


@app.route("/")
@login_required
def index():
    return page(
        """
        <p>{{ username }}님, 로그인되었습니다.</p>
        <p>메모 기능은 다음 단계에서 추가할 수 있습니다.</p>
        <form action="{{ url_for('logout') }}" method="post">
          <button type="submit">로그아웃</button>
        </form>
        """,
        username=session["username"],
    )


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
