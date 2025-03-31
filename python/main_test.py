from fastapi.testclient import TestClient
from main import app, get_db
import pytest
import sqlite3
import os
import pathlib
from unittest.mock import MagicMock  # STEP 6-3
from main import get_db, app         # STEP 6-3
from fastapi.testclient import TestClient  # STEP 6-3
from db_connection import shared_connection

# STEP 6-4: uncomment this test setup
test_db = pathlib.Path(__file__).parent.resolve() / "db" / "test_mercari.sqlite3"


def override_get_db():
    global shared_connection
    yield shared_connection

@pytest.fixture(autouse=True)
def db_connection():
    # Before the test is done, create a test database
    global shared_connection
    conn = sqlite3.connect(test_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    shared_connection = conn
    app.dependency_overrides[get_db] = override_get_db

    cursor = conn.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS items;
        DROP TABLE IF EXISTS categories;

        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        );

        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category_id INTEGER,
            image_name TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        """
    )
    conn.commit()

    shared_connection = conn
    yield conn

    conn.close()
    # After the test is done, remove the test database
    shared_connection = None
    if test_db.exists():
        test_db.unlink()  # Remove the file

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=False)

# GET / のテスト（Hello, world）
@pytest.mark.parametrize(
    "want_status_code, want_body",
    [
        (200, {"message": "Hello, world!"}),
    ],
)
def test_hello(want_status_code, want_body):
    response = client.get("/")  
    assert response.status_code == want_status_code
    assert response.json() == want_body

@pytest.mark.parametrize(
    "args, want_status_code",
    [
        ({"name": "テスト商品", "category": "テストカテゴリ"}, 200),
    ],
)
def test_add_item_basic(args, want_status_code):
    response = client.post("/items", data=args, files={})
    print("RESPONSE JSON:", response.json())  
    assert response.status_code == want_status_code
    json_data = response.json()
    assert "item received" in json_data["message"]
    assert args["name"] in json_data["message"]
    assert args["category"] in json_data["message"]

# モックDB（成功パターン）
def override_get_db_success():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = {"id": 1}
    yield mock_db

# モックDB（失敗パターン）
def override_get_db_failure():
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("DBエラー発生")
    yield mock_db

# モックDB（副作用チェック）
def override_get_db_side_effect_check():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = {"id": 1}
    mock_db.commit = MagicMock()
    override_get_db_side_effect_check.mock = mock_db
    yield mock_db

# 成功パターンのテスト
def test_add_item_mock_success():
    app.dependency_overrides[get_db] = override_get_db_success
    response = client.post(
        "/items",
        data={"name": "モック商品", "category": "モックカテゴリ"},
    )
    assert response.status_code == 200
    assert "モック商品" in response.json()["message"]

# 失敗パターンのテスト
def test_add_item_mock_failure():
    app.dependency_overrides[get_db] = override_get_db_failure
    response = client.post(
        "/items",
        data={"name": "エラー商品", "category": "カテゴリ"},
    )
    assert response.status_code == 500

# 副作用（execute/commit）が呼ばれたかの確認
def test_add_item_mock_side_effects():
    app.dependency_overrides[get_db] = override_get_db_side_effect_check
    response = client.post(
        "/items",
        data={"name": "副作用商品", "category": "副作用カテゴリ"},
    )
    mock_db = override_get_db_side_effect_check.mock
    assert mock_db.execute.called
    assert mock_db.commit.called


# STEP 6-4: uncomment this test
@pytest.mark.parametrize(
    "args, want_status_code",
    [
        ({"name":"used iPhone 16e", "category":"phone"}, 200),
        ({"name":"", "category":"phone"}, 400),
    ],
)
def test_add_item_e2e(args, want_status_code, db_connection):
    response = client.post("/items", data=args, files={})
    print("RESPONSE JSON:", response.json())
    assert response.status_code == want_status_code

    if want_status_code >= 400:
        return

    # Check if the response body is correct
    response_data = response.json()
    assert "message" in response_data

    # Check if the data was saved to the database correctly
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT items.name, categories.name AS category
        FROM items
        JOIN categories ON items.category_id = categories.id
        WHERE items.name = ?
    """, (args["name"],))
    db_item = cursor.fetchone()

    # デバッグ：DBの状態を見る
    all_items = cursor.execute("SELECT * FROM items").fetchall()
    all_categories = cursor.execute("SELECT * FROM categories").fetchall()
    print("ALL ITEMS:", [dict(row) for row in all_items])
    print("ALL CATEGORIES:", [dict(row) for row in all_categories])

    assert db_item is not None
    assert dict(db_item)["name"] == args["name"]
    assert dict(db_item)["category"] == args["category"]

