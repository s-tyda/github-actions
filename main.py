from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from mongoengine import connect, Document, StringField, DateTimeField
import jwt
from datetime import datetime, timedelta


app = FastAPI()
connect(db="techni_chat_1", host="mongodb://mongodb:27017/techni_chat_1")


class User(Document):
    username = StringField(required=True, unique=True)
    password = StringField(required=True)


class Message(Document):
    sender = StringField(required=True)
    receiver = StringField(required=True)
    content = StringField(required=True)
    timestamp = DateTimeField()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=45)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")


def verify_token(token: str):
    try:
        data = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return data.get("sub")


@app.post("/register")
def register(username: str, password: str):
    if User.objects(username=username).first():
        raise HTTPException(status_code=400, detail="User exists")
    user = User(username=username, password=password).save()
    return {"msg": "User registered"}


@app.post("/login")
def login(username: str, password: str):
    user = User.objects(username=username).first()
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token}


active_connections: dict[str, WebSocket] = {}

# http://127.0.0.1:8000/docs#/
# ws://127.0.0.1:8000/ws/
@app.websocket("/ws/{token}")
async def websocket(websocket: WebSocket, token: str):
    try:
        username = verify_token(token)
    except HTTPException:
        await websocket.close()
        return

    await websocket.accept()
    active_connections[username] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            # username:message
            # data.split(":", 1) -> (username, message)
            receiver, message = data.split(":", 1)
            receiver_user = User.objects(username=receiver).first()
            if receiver_user:
                Message(sender=username, receiver=receiver,
                        content=message, timestamp=datetime.utcnow()).save()
                if receiver in active_connections:
                    await active_connections[receiver].send_text(
                        f"{username}:{message}"
                    )

    except WebSocketDisconnect:
        del active_connections[username]


test_client = TestClient(app)


def test_root():
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "msg": "Hello World"
    }
