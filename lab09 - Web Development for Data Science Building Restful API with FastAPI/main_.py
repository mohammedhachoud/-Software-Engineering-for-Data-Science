#Your Solution
from fastapi import Depends,FastAPI, Path, Query, Body, Form, File, UploadFile, Header, Request, Response, HTTPException, status
from enum import Enum
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import json
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/", response_model=list[schemas.User])
async def get_users(skip: int = 0, limit: int = 100, db: Session =
Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/{user_id}/posts/", response_model=list[schemas.Post])
async def get_user_posts(user_id: int, skip: int = 0, limit: int = 100, db:Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    posts = crud.get_user_posts(db,user_id,skip, limit)
    return posts

@app.post("/users/new", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session =Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email alreadyregistered")
    return crud.create_user(db=db, user=user)

@app.post("/users/{user_id}/posts/new", response_model=schemas.Post)
async def create_post_for_user(user_id: int,
    post: schemas.PostCreate,
    db: Session = Depends(get_db)):
    return crud.create_user_post(db=db, post=post, user_id=user_id)

@app.delete("/users/{user_id}/delete_post/{post_id}")
async def delete_post_for_user(user_id: int,post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.author == user_id, models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="User or Post not found")
    crud.delete_user_post(db=db, post=db_post)
    return {"msg": "Successfully Deleted"}


@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}

# API that expects an integer in the last part of its path

@app.get("/users/{id}")
async def get_user(id: int):
    return {"id": id}

class UserType(str, Enum):
    STANDARD = "standard"
    ADMIN = "admin"

#specify the user types
@app.get("/users/{type}/{id}/")
async def get_user(type: UserType, id: int):
    return {"type": type, "id": id}

#greater than or equal to 1
@app.get("/users/{id}")
async def get_user(id: int = Path(..., ge=1)):
    return {"id": id}

@app.get("/license-plates/{license}")
async def get_license_plate(license: str = Path(...,regex=r"^\d{5}-\d{3}-\d{2}$")):
    return {"license": license}

@app.get("/users")
async def get_user(page: int = Query(1, gt = 0),size: int = Query(10, le = 100)):
    return {"page": page, "size": size}

@app.post("/users")
async def create_user(name: str = Body(...),age: int = Body(...)):
    return {"name": name, "age": age}

@app.post("/createUser")
async def create_user(name: str = Form(...),age: int = Form(...)):
    return {"name": name, "age": age}

@app.post("/files")
async def upload_file(file: bytes = File(...)):
    return {"file_size": len(file)}

@app.post("/uploadFile")
async def upload_file(file: UploadFile = File(...)):
    return {"file_name": file.filename,
            "content_type": file.content_type}

@app.post("/uploadMultipleFiles")
async def upload_multiple_files(files: List[UploadFile]=File(...)):
    return [
            {"file_name": file.filename,
             "content_type": file.content_type}
            for file in files
           ]

@app.get("/getHeader")
async def get_header(user_agent: str = Header(...)):
    return {"user_agent": user_agent}

@app.get("/request")
async def get_request_object(request: Request):
    return {"path": request.url.path}

@app.get("/setCookie")
async def custom_cookie(response: Response):
    response.set_cookie("cookie-name",
                        "cookie-value",
                        max_age=86400)
    return {"hello": "world"}

@app.post("/password")
async def check_password(password: str = Body(...), password_confirm: str = Body(...)):
    if password != password_confirm:
       raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Passwords don't match.",)
    return {"message": "Passwords match."}

templates = Jinja2Templates(directory="templates")
@app.get("/reply")
async def home(request: Request):
    return templates.TemplateResponse("/index.html",{"request":request})

@app.get("/houseprices")
async def home(request: Request):
    df = pd.read_csv("data/house_pricing.csv", nrows=25)
    js = df.to_json(orient="records")
    data=json.loads(js)
    return templates.TemplateResponse("/houseprices.html",
                                        {"request":request,
                                        "house_prices":data})

