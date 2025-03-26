import os
import logging
import pathlib
import hashlib  # ハッシュ化のために追加(4-4)
import shutil   # 画像の保存に使う(4-4)
import sqlite3
from fastapi import FastAPI, Form, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional

# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images" 
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"

def get_db():
    if not db.exists():
        setup_database()  # データベースがない場合は作成する

    conn = sqlite3.connect(db, check_same_thread=False)
    conn.row_factory = sqlite3.Row  
    try:
        yield conn
    finally:
        conn.close()


def setup_database():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # データベースファイル (mercari.sqlite3) がない場合、エラーを出す
    if not db.exists():
        raise FileNotFoundError("Error: mercari.sqlite3 が見つかりません")

    # itemsテーブルがあるかチェック
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
    table_exists = cursor.fetchone()

    # itemsテーブルがなかったらエラーを出す
    if not table_exists:
        raise RuntimeError("Error: 'items'テーブルが見つかりません")

    conn.close()



@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


class AddItemResponse(BaseModel):
    message: str


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
async def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(None),
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if not category:
        raise HTTPException(status_code=400, detail="category is required")

    if not images.exists():
        images.mkdir()

    image_filename = "default.jpg"

    if image:
        # 画像のデータを取得して SHA-256 でハッシュ化
        image_data = await image.read()
        hash_name = hashlib.sha256(image_data).hexdigest()
        image_filename = f"{hash_name}.jpg"
        image_path = images / image_filename

        # 画像を保存
        with open(image_path, "wb") as buffer:
            buffer.write(image_data)

    # 🔽 `category_id` を取得（なければ作成）
    category_query = "SELECT id FROM categories WHERE name = ?"
    category_id = db.execute(category_query, (category,)).fetchone()

    if category_id is None:
        db.execute("INSERT INTO categories (name) VALUES (?)", (category,))
        db.commit()
        category_id = db.execute(category_query, (category,)).fetchone()

    category_id = category_id["id"]  # `fetchone()` の結果から `id` を取得

    # 🔽 `items` テーブルに `category_id` を登録
    query = "INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)"
    db.execute(query, (name, category_id, image_filename))
    db.commit()

    return AddItemResponse(message=f"item received: {name}, category: {category}, image_name: {image_filename}")
    

@app.get("/items")
def get_items(db: sqlite3.Connection = Depends(get_db)):
    query = """
        SELECT items.id, items.name, categories.name AS category, items.image_name
        FROM items
        JOIN categories ON items.category_id = categories.id
    """
    items = db.execute(query).fetchall()
    return {"items": [dict(item) for item in items]}


@app.get("/items/{item_id}")
def get_item_by_id(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    item = db.execute("SELECT * FROM items WHERE id =?", (item_id,)).fetchone()

    if item is None:
        raise HTTPException(status_code=404, detail ="Item not found")
    return dict(item)

# 5-2追加部分
@app.get("/search")
def search_items(keyword: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
    query = """
        SELECT items.name, categories.name AS category, items.image_name
        FROM items
        JOIN categories ON items.category_id = categories.id
        WHERE items.name LIKE ?
    """
    items = db.execute(query, (f"%{keyword}%",)).fetchall()

    return {"items": [dict(item) for item in items]}


# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)



class Item(BaseModel):
    name: str
    category: str
    image_name: Optional[str] = None  # 画像のファイル名を保存

def insert_item_db(item: Item, db: sqlite3.Connection) -> int:
    cursor = db.cursor()
    query = """
        INSERT INTO items (name, category, image_name) VALUES (?, ?, ?);
        """
    cursor.execute(query, (item.name, item.category, item.image_name))

    db.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id

