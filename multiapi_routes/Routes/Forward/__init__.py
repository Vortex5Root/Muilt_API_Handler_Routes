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
        self.vb = Virtual_Bond()

    async def connect(self, websocket: WebSocket,model_id : str, token: str):
        """connect event"""
        print("model:", model_id)
        print("Login Output:", token)
        await websocket.accept()
        try:
            token = login(token)
            
            vb = self.vb.read_items(token=token,id=model_id)
            #print(vb.status)
            if vb.status == "error":
                raise HTTPException(status_code=404, detail=vb.error)
            #print(vb)
            self.active_connections.append(websocket)
            await websocket.send_json({"status":"success","result":"Connected"})
            return token
        except HTTPException as e:
            print("HTTPException:",e)
            await websocket.send_json({"status":"error","result":str(e.detail)})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        except Exception as e:
            print("Exception:",e)
            await websocket.send_json({"status":"error","result":str(e)})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

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
        self.add_api_route("/forward", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/forward", self.Websocket_Example, methods=["GET"])
        
    
    def create_item(self,model : str,arg : Dict , token: str = Depends(login)):
        self.vb.read_items(token=token,id=model)
        task = self.celery.send_task('__start__.brain_task', args=(arg))
        while task.status() == "DONE":
            pass
        return task.get()

    def Websocket_Example(self):
        return HTMLResponse("""
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <label>Model ID: <input type="text" id="modelId" autocomplete="off" value="foo"/></label>
        <label>Token: <input type="text" id="token" autocomplete="off" value="some-key-token"/></label>
        <button onclick="connect(event)">Connect</button>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = null;
            function connect(event) {
                var modelId = document.getElementById("modelId")
                var token = document.getElementById("token")
                var ws = new WebSocket("ws://192.168.1.205:8000/v1/multiapi/"+modelId.value+"/stream?token="+token.value);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                function sendMessage(event) {
                    var input = document.getElementById("messageText")
                    ws.send(input.value)
                    input.value = ''
                    event.preventDefault()
                }
            }
        </script>
    </body>
</html>
""")

forward_ = forward()

@forward_.websocket("/{model_id}/stream")
async def websocket_endpoint(websocket: WebSocket, model_id: str, token: str = Query(None)):
    forward_manager = ConnectionManager()
    bk = os.environ['CELERY_BROKER_URL']
    celery = Celery('tasks', broker=bk)
    token = await forward_manager.connect(websocket, model_id, token)
    if token is not None:
        try:
            print("Connected")
            while True:
                data = await websocket.receive_text()
                print(data)
                if data["type"] == "websocket.disconnect":
                    websocket.send_json({"status":"success","result":"Disconnected"})
                    forward_manager.disconnect(websocket)
                    break
                elif data:
                    task = celery.send_task('__start__.brain_task', args=(model_id, data["arg"]))
                    while task.status() == "DONE":
                        await websocket.send_json({"status": task.status(), "result": task.get()})
                        pass
                    await websocket.send_json(task.get())
        except WebSocketDisconnect as e:
            forward_manager.disconnect(websocket)
