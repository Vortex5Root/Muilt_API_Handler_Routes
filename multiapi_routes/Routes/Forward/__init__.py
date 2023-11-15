from fastapi import APIRouter, WebSocket ,Depends, HTTPException,Cookie, Query,WebSocketException, status

from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse

from vauth import login , VAuth

from celery import Celery

from dotenv import load_dotenv

from typing import Any, Dict, Annotated

from fastapi_websocket_rpc import RpcMethodsBase, WebsocketRPCEndpoint

from multiapi_routes.Routes.VirtualBond import Virtual_Bond

import os

load_dotenv()

from fastapi import WebSocket

class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        """connect event"""
        print("Cookie:", websocket.cookies["token"])
        print("Login Output:", token)
        try:
            token = await login(websocket.cookies["token"])
            websocket.token = token
            await websocket.accept()
            self.active_connections.append(websocket)
        except Exception as e:
            print(e)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    async def return_task(self, output: Any, websocket: WebSocket):
        """Direct Message"""
        await websocket.send(output)
    
    def disconnect(self, websocket: WebSocket):
        """disconnect event"""
        self.active_connections.remove(websocket)

class forward(APIRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "froward"
        bk = os.environ['CELERY_BROKER_URL']
        self.vb = Virtual_Bond()
        if bk == None:
            raise HTTPException(status_code=404, detail="No CELERY_BROKER_URL Found")
        self.celery = Celery('tasks', broker=bk)
        self.add_api_route("/froward", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/froward", self.Websocket_Example, methods=["GET"])
        self.add_api_route("/froward/stream", self.websocket_endpoint, methods=["websocket"])
        endpoint = WebsocketRPCEndpoint(Steam())
        # add the endpoint to the app
        endpoint.register_route(self, "/ws")
        
    
    def create_item(self,model : str,arg : Dict , token: str = Depends(login)):
        self.vb.read_items(token=token,id=model)
        task = self.celery.send_task('__start__.brain_task', args=(arg))
        while task.status() == "DONE":
            pass
        return task.get()


    async def websocket_endpoint(websocket: WebSocket):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive()
                print(data)
                print(type(data))
                await manager.send_personal_message(f"Received:{data}",websocket)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            await manager.send_personal_message("Bye!!!",websocket)

    def Websocket_Example(self):
        return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Chat</title>
</head>
<body>
    <h1>WebSocket with FastAPI</h1>
    <form action="" onsubmit="sendMessage(event)">
        <input type="text" id="messageText" autocomplete="off" />
        <button>Send</button>
    </form>
    <ul id='messages'>
    </ul>
    <script>
        function getCookie(cname) {
            let name = cname + "=";
            let ca = document.cookie.split(';');
            for(let i = 0; i < ca.length; i++) {
                let c = ca[i];
                while (c.charAt(0) == ' ') {
                c = c.substring(1);
                }
                if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
                }
            }
            return "";
        }
        var ws = new WebSocket(`ws://`+ window.location.hostname +`:8000/v1/multiapi/froward/stream?token=`+getCookie("token")+``);
        console.log("Connected")
        ws.onmessage = function (event) {
            var messages = document.getElementById('messages')
            var message = document.createElement('li')
            var content = document.createTextNode(event.data)
            message.appendChild(content)
            messages.appendChild(message)
        };
        console.log("Send Mesage")
        function sendMessage(event) {
            var input = document.getElementById("messageText")
            ws.send(input.value)
            input.value = ''
            event.preventDefault()
        }
    </script>
</body>
</html>
""")


class Steam(RpcMethodsBase):
    async def stream(self,websocket: WebSocket,token: str = Depends(login)):
        print("stream")
        print(token.token)
        await websocket.accept()
        await websocket.send_json({"status":"connected"})
        while True:
            data = await websocket.receive_json()
            if data["type"] == "websocket.disconnect":
                await websocket.close()
                break
            else:
                task = self.celery.send_task('__start__.brain_task', args=(data["model"],data["arg"]))
                while task.status() == "DONE":
                    await websocket.send_json({"status":task.status(),"result":task.get()})
                    pass
                await websocket.send_json(task.get())
        return "froward"