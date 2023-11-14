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
        self.add_api_route("/froward", self.Websocket_Example, methods=["GET"], dependencies=[Depends(login)])
        endpoint = WebsocketRPCEndpoint(Steam())
        # add the endpoint to the app
        endpoint.register_route(self, "/ws")
        
    
    def create_item(self,model : str,arg : Dict , token: str = Depends(login)):
        self.vb.read_items(token=token,id=model)
        task = self.celery.send_task('__start__.brain_task', args=(arg))
        while task.status() == "DONE":
            pass
        return task.get()
    
    def Websocket_Example(self):
        return HTMLResponse("""
        <html>
            <head>
                <title>Websocket RPC</title>
            </head>
            <body>
                <h1>Websocket RPC</h1>
                <script>
                    var ws = new WebSocket("ws://localhost:8000/v1/multiapi/ws");
                    ws.onopen = function() {
                        console.log("Websocket connection established");
                        ws.send(JSON.stringify({
                            "type": "websocket.connect",
                            "id": "1"
                        }));
                    };
                    ws.onmessage = function(e) {
                        console.log("Message received:", e.data);
                    };
                    ws.onclose = function(e) {
                        console.log("Connection closed:", e);
                    };
                </script>
            </body>
        </html>
        """)


class Steam(RpcMethodsBase):
    async def stream(self,websocket: WebSocket,token: str = Depends(login)):
        await websocket.accept()
        while True:
            data = await websocket.receive_json()
            if data["type"] == "websocket.disconnect":
                await websocket.close()
                break
            else:
                task = self.celery.send_task('__start__.brain_task', args=(data["model"],data["arg"]))
                while task.status() == "DONE":
                    pass
                await websocket.send_json(task.get())
        return "froward"