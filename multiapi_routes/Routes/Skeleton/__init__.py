# Importing necessary libraries and functions #
#=============================================#
# Typing
from typing  import Dict
# RestAPI Lib
from fastapi import APIRouter, Depends, HTTPException
# Functions
from vauth import login , VAuth
from multiapi_routes.Libs.check      import check_skeleton, check_rules

# DB 
from multiapi_routes.Libs.DB import Skeletons

# Defining the skeletons class which inherits from APIRouter
class Skeleton(APIRouter):

    permissions = {
        "all"  : "skeleton.{}",
        "read" : "skeleton.read.{}",
        "create" : "skeleton.create.{}",
        "update" : "skeleton.update.{}",
        "delete" : "skeleton.delete.{}"
    }


    # Initializing the class with necessary routes and variables
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "skeleton"

        print(VAuth().register("skeleton",["read","create","update","delete"],True))
        # Adding routes for different HTTP methods
        self.add_api_route("/skeletons", self.read_items, methods=["GET"], dependencies=[Depends(login)])
        self.add_api_route("/skeletons", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/skeletons", self.update_item, methods=["PUT"], dependencies=[Depends(login)])
        self.add_api_route("/skeletons", self.delete_item, methods=["DELETE"], dependencies=[Depends(login)])

    # Defining the read_items method
    def read_items(self, token: str = Depends(login), id: str = "",model_type: str = ""):
        permission = [self.permissions["all"].format("*"),self.permissions["read"].format("*")]
        # If id is not provided, return all items
        if id == "" and model_type == "":
            if Skeletons.find().count() == 0:
                raise HTTPException(status_code=404, detail="No Skeleton Found!") # No Skeleton Found!
            items = []
            for _ in Skeletons.find().all():
                temp = permission.copy()
                temp.append(self.permissions["read"].format(_.id))
                temp.append(self.permissions["all"].format(_.id))
                if token.is_allow(temp):
                    items.append(_)
            if not items:
                raise HTTPException(status_code=404, detail="No Skeleton Found!")
            return items
        elif id == "" and model_type != "":
            permission.append(self.permissions["all"].format(model_type))
            items = []
            for _ in Skeletons.find(Skeletons.type_model == model_type).all():
                temp = permission.copy()
                temp.append(self.permissions["read"].format(_.id))
                temp.append(self.permissions["all"].format(_.id))
                if token.is_allow(temp):
                    items.append(_)
            if not items:
                raise HTTPException(status_code=404, detail="No Skeleton Found!")
            return items
        # If id is provided, return the specific item
        elif id != "" and model_type == "":
            permission.append(self.permissions["read"].format(id))
            if token.is_allow(permission):
                item = Skeletons.find(Skeletons.id == id)
                if item is None:
                    raise HTTPException(status_code=404,detail="No Skeleton Found!")
                if item.count() == 0:
                    raise HTTPException(status_code=404,detail="No Skeleton Found!")
                print(item)
                item = item.first()
                if not item:
                    raise HTTPException(status_code=404, detail=f"Item with id {id} not found.")
                return item
            else:
                raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
        elif id != "" and model_type != "":
            permission.append(self.permissions["read"].format(id))
            permission.append(self.permissions["all"].format(id))
            permission.append(self.permissions["all"].format(model_type))
            if token.is_allow(permission):
                item = Skeletons.find((Skeletons.id == id) & (Skeletons.type_model == model_type))
                if item is None:
                    raise HTTPException(status_code=404,detail="No Skeleton Found!")
                if item.count() == 0:
                    raise HTTPException(status_code=404,detail="No Skeleton Found!")
                return item.first()

    # Defining the create_item method
    def create_item(self, skeleton : Dict, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["create"].format("*")]
        # Define the rules for the skeleton model
        parameters = ["id","type_model","skeleton"]
        # Check if all required parameters are skeleton
        rule_check = check_rules(rule_list=parameters, row_rest=skeleton)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        #self.apis.read_items(token,id=skeleton["id"])
        # If the token is allowed, create the skeleton model
        permission.append(self.permissions["create"].format(skeleton["id"]))
        permission.append(self.permissions["all"].format(skeleton["id"]))
        if token.is_allow(permission):
            try:
                new_skeleton = Skeletons(**skeleton)
                new_skeleton.save()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            # If the token is not allowed, add permission
            if not token.is_allow(f"skeleton.{skeleton['id']}"):
                VAuth().add_permission_rg("SkeletonModel",skeleton["id"])
                token.add_permission(f"{self.name}.{skeleton['id']}")
            return {"info":f"Skeleton ({skeleton['id']}) Added!","status":"Success"}
        else:
            raise HTTPException(status_code=400, detail="Your token isn't allowed to perform this action.")

    # Defining the update_item method
    def update_item(self, item: Dict, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["update"].format("*")]
        # Define the rules for the skeleton model
        parameters = ["id","model_type","skeleton"]
        # Check if all required parameters are skeleton
        rule_check = check_rules(rule_list=parameters, row_rest=item)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        permission.append(self.permissions["update"].format(item["id"]))
        permission.append(self.permissions["all"].format(item["id"]))
        # If the token is allowed, update the skeleton model
        if token.is_allow(permission):
            try:
                skeleton_model = Skeletons.find(Skeletons.id == item['id']).first()
                if not skeleton_model:
                    raise HTTPException(status_code=404, detail=f"Skeletons with id {item['id']} not found.")
                for key, value in item.items():
                    setattr(skeleton_model, key, value)
                skeleton_model.save()
                return {"info": f"Skeletons {item['id']} updated", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error updating Skeletons: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")

    # Defining the delete_item method
    def delete_item(self, id: str, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["delete"].format("*")]
        permission.append(self.permissions["delete"].format(id))
        # If the token is allowed, delete the skeleton model
        if token.is_allow(permission):
            if not check_skeleton(id):
                raise HTTPException(status_code=404, detail=f"Skeletons with id {id} doesn't exist!")
            try:
                Skeletons.delete(id)
                return {"info": f"Skeletons {id} deleted", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error deleting Skeletons: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
