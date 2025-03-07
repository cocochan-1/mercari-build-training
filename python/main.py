import os
import logging
import pathlib
import json #4-2(json)
import hashlib  # ハッシュ化のために追加(4-4)
import shutil   # 画像の保存に使う(4-4)

from fastapi import FastAPI, Form, HTTPException, Depends, UploadFile, File #画像を受け取る
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images" 
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
json_path = pathlib.Path(__file__).parent.resolve() / "items.json" # 4-2 ここから追加 

# 4-2 JSONファイルがなければ作成(最初に1回だけ実行)
if not json_path.exists():
    with open(json_path, "w") as file:
        json.dump([], file)

def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


# STEP 5-1: set up the database connection
def setup_database():
    pass


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
    image: UploadFile = File(None),  # 画像を受け取る
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if not category:
        raise HTTPException(status_code=400, detail="category is required")

    if not images.exists(): # 画像
        images.mkdir()

    image_filename = "default.jpg"  # 画像がない場合はdefault.jpg


    if image:
        # 画像のデータを取得して SHA-256 でハッシュ化
        image_data = await image.read()
        hash_name = hashlib.sha256(image_data).hexdigest()
        image_filename = f"{hash_name}.jpg"  # .jpg を付ける
        image_path = images / image_filename

        # 画像を保存
        with open(image_path, "wb") as buffer:
            buffer.write(image_data)

    # アイテムを追加
    insert_item(Item(name=name, category=category, image_name=image_filename))

    return AddItemResponse(**{"message": f"item received: {name}, category: {category}, image_name: {image_filename}"})

# 4-3 GET/itemsエンドポイント実装
@app.get("/items")
def get_items():
    with open(json_path, "r") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = {"items": []} # データが壊れていた場合の初期化
    return data

@app.get("/items/{item_id}")
def get_item(item_id: int):
    with open(json_path, "r") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = {"items": []}
    
    # アイテム一覧を取得
    items = data.get("items", [])

    # IDが範囲外ならエラーを返す
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 該当のアイテムを返す
    return items[item_id]


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
    image_name: str | None = None  # 画像のファイル名を保存

def insert_item(item: Item):
    # STEP 4-2: add an implementation to store an item
    with open(json_path, "r") as file:
        try:
            data = json.load(file)
            # もし data がリストだったら、辞書に変換
            if not isinstance(data, dict):  
                data = {"items": []}
        except json.JSONDecodeError:  # もし JSON が壊れていたら初期化
            data = {"items": []}
    #新しいアイテムを追加
    data["items"].append({"name": item.name, "category": item.category, "image_name": item.image_name})
    #上書き保存("w"を使用)
    with open(json_path, "w") as file:
        json.dump(data, file, indent=4)

