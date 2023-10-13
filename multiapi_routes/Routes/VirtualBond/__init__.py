# Importing necessary libraries and functions #
#=============================================#
# Typing
from typing  import Dict
# RestAPI Lib
from fastapi import APIRouter, Depends, HTTPException
# Functions
from vauth import login , VAuth
from multiapi_routes.Libs.check      import check_virtual_bond, check_rules

# DB 
from multiapi_routes.Libs.DB import VirtualBond

# Defining the VirtualBond class which inherits from APIRouter
class Virtual_Bond(APIRouter):
    # Initializing the class with necessary routes and variables
    def __init__(self, *args, **kwargs):
        self.name = "virtual_bond"
        self.global_local = "virtual_bond.*"
        super().__init__(*args, **kwargs)

        print(VAuth().register("virtual_bond",["read","create","update","delete"],True))
        # Adding routes for different HTTP methods
        self.add_api_route("/virtual/bonds", self.read_items, methods=["GET"], dependencies=[Depends(login)])
        self.add_api_route("/virtual/bonds", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/virtual/bonds", self.update_item, methods=["PUT"], dependencies=[Depends(login)])
        self.add_api_route("/virtual/bonds", self.delete_item, methods=["DELETE"], dependencies=[Depends(login)])

    # Defining the read_items method
    def read_items(self, token: str = Depends(login), id: str = "",model_type: str = ""):
        action = "read"
        global_local = "virtual_bond.read.*"
        # If id is not provided, return all items
        if id == "" and model_type == "":
            if VirtualBond.find().count() == 0:
                raise HTTPException(status_code=404, detail="No items found.")
            items = [_ for _ in VirtualBond.find().all() if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{_.id}"])]
            #print(item)
            if not items:
                raise HTTPException(status_code=404, detail="No items found.")
            return items
        elif id == "" and model_type != "":
            if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{model_type}"]):
                items = [_ for _ in VirtualBond.find(VirtualBond.type_model == model_type).all() if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{_.id}"] and _.id == id)]
                if not items:
                    raise HTTPException(status_code=404, detail="No items found.")
                return items
        # If id is provided, return the specific item
        elif id != "" and model_type == "":
            if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{id}"]):
                item = VirtualBond.find(VirtualBond.id == id)
                if item is None:
                    raise HTTPException(status_code=404,detail="No items found.")
                if item.count() == 0:
                    raise HTTPException(status_code=404,detail="No items found.")
                print(item)
                item = item.first()
                if not item:
                    raise HTTPException(status_code=404, detail=f"Item with id {id} not found.")
                return item
            else:
                raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
        elif id != "" and model_type != "":
            if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{model_type}"]):
                item = VirtualBond.find((VirtualBond.id == id) & (VirtualBond.type_model == model_type))
                if item is None:
                    raise HTTPException(status_code=404,detail="No items found.")
                if item.count() == 0:
                    raise HTTPException(status_code=404,detail="No items found.")
                return item.first()

    # Defining the create_item method
    def create_item(self, skeleton : Dict, token: str = Depends(login)):
        action = "create"
        global_local = "virtual_bond.create.*"
        # Define the rules for the skeleton model
        parameters = ["id","type_model","row_code"]
        # Check if all required parameters are skeleton
        rule_check = check_rules(rule_list=parameters, row_rest=skeleton)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        #self.apis.read_items(token,id=skeleton["id"])
        # If the token is allowed, create the skeleton model
        if token.is_allow([self.global_local, global_local, f"skeleton.create.{skeleton['id']}"]):
            try:
                new_skeleton = VirtualBond(**skeleton)
                new_skeleton.save()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            # If the token is not allowed, add permission
            if not token.is_allow(f"virtual_bond.{skeleton['id']}"):
                VAuth().add_permission_rg("SkeletonModel",skeleton["id"])
                token.add_permission(f"{self.name}.{skeleton['id']}")
            return {"info":f"Skeleton ({skeleton['id']}) Added!","status":"Success"}
        else:
            raise HTTPException(status_code=400, detail="Your token isn't allowed to perform this action.")

    # Defining the update_item method
    def update_item(self, item: Dict, token: str = Depends(login)):
        action = "update"
        global_local = "virtual_bond.update.*"
        # Define the rules for the skeleton model
        parameters = ["id","model_type","row_code"]
        # Check if all required parameters are skeleton
        rule_check = check_rules(rule_list=parameters, row_rest=item)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        # If the token is allowed, update the skeleton model
        if token.is_allow([self.global_local, global_local, f"skeleton.update.{item['id']}"]):
            try:
                skeleton_model = VirtualBond.find(VirtualBond.id == item['id']).first()
                if not skeleton_model:
                    raise HTTPException(status_code=404, detail=f"VirtualBond with id {item['id']} not found.")
                for key, value in item.items():
                    setattr(skeleton_model, key, value)
                skeleton_model.save()
                return {"info": f"VirtualBond {item['id']} updated", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error updating VirtualBond: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")

    # Defining the delete_item method
    def delete_item(self, id: str, token: str = Depends(login)):
        action = "delete"
        # If the token is allowed, delete the skeleton model
        if token.is_allow([f"{self.name}.{action}.{id}"]):
            if not check_virtual_bond(id):
                raise HTTPException(status_code=404, detail=f"VirtualBond with id {id} doesn't exist!")
            try:
                VirtualBond.delete(id)
                return {"info": f"VirtualBond {id} deleted", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error deleting VirtualBond: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
