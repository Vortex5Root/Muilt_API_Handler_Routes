from fastapi import APIRouter, WebSocket ,Depends, HTTPException
from fastapi.responses import HTMLResponse

from vauth import login , VAuth

from celery import Celery

from dotenv import load_dotenv

from typing import Any, Dict

from fastapi_websocket_rpc import RpcMethodsBase, WebsocketRPCEndpoint

from multiapi_routes.Routes.VirtualBond import Virtual_Bond

import os

load_dotenv()

class froward(APIRouter):

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
        self.add_api_route("/froward/stream", self.stream, methods=["websocket"])
        endpoint = WebsocketRPCEndpoint(Steam())
        # add the endpoint to the app
        endpoint.register_route(self, "/ws")
        
    
    def create_item(self,model : str,arg : Dict , token: str = Depends(login)):
        self.vb.read_items(token=token,id=model)
        task = self.celery.send_task('__start__.brain_task', args=(arg))
        while task.status() == "DONE":
            pass
        return task.get()

    async def stream(self,websocket: WebSocket,token: str = Depends(login)):
        print("stream")
        print(token)
        print(websocket)
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

    def Websocket_Example(self):
        return HTMLResponse("""
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <label>ENDPOINT: <input type="text" id="itemId" autocomplete="off" value="foo"/></label>
            <label>Token: <input type="text" id="token" autocomplete="off" value="some-key-token"/></label>
            <button onclick="connect(event)">Connect</button>
            <hr>
            <label>Message: <input type="text" id="messageText" autocomplete="off"/></label>
            <button onclick="sendMessage(event)">Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
        var ws = null;
            function connect(event) {
                var itemId = document.getElementById("itemId")
                var token = document.getElementById("token")
                ws = new WebSocket("ws://"+ itemId.value +":8000/v1/multiapi/ws?token=" + token.value);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                event.preventDefault()
            }
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