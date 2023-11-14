from fastapi import APIRouter, WebSocket ,Depends, HTTPException

from vauth import login , VAuth

from celery import Celery

from dotenv import load_dotenv

from typing import Any, Dict

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
        self.add_api_route("/froward", self.websocket, methods=["websocket"], dependencies=[Depends(login)])
        
    
    def create_item(self,model : str,arg : Dict , token: str = Depends(login)):
        self.vb.read_items(token=token,id=model)
        task = self.celery.send_task('__start__.brain_task', args=(arg))
        while task.status() == "DONE":
            pass
        return task.get()
    
    async def websocket(self,websocket: WebSocket,token: str = Depends(login)):
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