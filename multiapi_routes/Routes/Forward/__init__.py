import asyncio
import threading
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

from celery.result import AsyncResult

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
                    var modelId = document.getElementById("modelId").value;
                    var token = document.getElementById("token").value;
                    var url = window.location.host;
                    ws = new WebSocket("ws://"+window.location.host+"/v1/multiapi/"+modelId+"/stream?token="+token);
                    ws.onmessage = function(event) {
                        var messages = document.getElementById('messages');
                        var message = document.createElement('li');
                        var content = document.createTextNode(event.data);
                        message.appendChild(content);
                        messages.appendChild(message);
                    };
                }
                function sendMessage(event) {
                    var input = document.getElementById("messageText");
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(input.value);
                        input.value = '';
                    } else {
                        alert("WebSocket connection is closed. Please connect first.");
                        ws.close();
                    }
                    event.preventDefault();
                }
            </script>
        </body>
    </html>
    """)

bk = os.environ['CELERY_BROKER_URL']

forward_ = forward()

def return_task(task: Any, websocket: WebSocket):
    while True:
        print(task.status())
        if task.ready():
            result = task.get()
            websocket.send_json(result)
            break

@forward_.websocket("/{model_id}/stream")
async def websocket_endpoint(websocket: WebSocket, model_id: str, token: str = Query(None)):
    print("start new WebSocket connection")
    forward_manager = ConnectionManager()
    celery = Celery('tasks', broker=bk, backend=bk)
    print("New Client")
    token = await forward_manager.connect(websocket, model_id, token)
    if token is not None:
        #Queue
        tasks = asyncio.Queue()
        async def rcv(websocket: WebSocket):
            while True:
                try:
                    data = await websocket.receive()
                    print(data)
                    if data["type"] == "websocket.disconnect":
                        await websocket.send_json({"status":"success","result":"Disconnected"})
                        forward_manager.disconnect(websocket)
                        break
                    elif data:
                        input_data = None
                        if data["type"] == "websocket.receive":
                            input_data = data["text"]
                        elif data["type"] == "bytes":
                            input_data = data["bytes"]
                        task = celery.send_task('multiapi.brain_task', args=(model_id,model_id, token.token, input_data))
                        await tasks.put(task)
                        #await websocket.send_json(task.get())
                except WebSocketDisconnect as e:
                    print("WebSocket Error",e)
                    await forward_manager.disconnect(websocket)

        async def send(websocket: WebSocket):
            while True:
                try:
                    task = await tasks.get()
                    while task.status() == "DONE":
                        pass
                    await websocket.send_json(task.get())
                except Exception as e:
                    print(e)
                    pass
        await asyncio.gather(send(websocket), rcv(websocket))
        '''try:
            print("Connected")
            while True:
                data = await websocket.receive()
                print(data)
                if data["type"] == "websocket.disconnect":
                    await websocket.send_json({"status":"success","result":"Disconnected"})
                    forward_manager.disconnect(websocket)
                    break
                elif data:
                    input_data = None
                    if data["type"] == "websocket.receive":
                        input_data = data["text"]
                    elif data["type"] == "bytes":
                        input_data = data["bytes"]
                    task = celery.send_task('multiapi.brain_task', args=(model_id,model_id, token.token, input_data))
                    thread = threading.Thread(target=return_task, args=(task,websocket))
                    thread.start()
                    #await websocket.send_json(task.get())
        except WebSocketDisconnect as e:
            print("WebSocket Error",e)
            await forward_manager.disconnect(websocket)'''
