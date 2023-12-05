# Importing necessary libraries and functions #
#=============================================#
# Typing
from typing  import Dict
# RestAPI Lib
from fastapi import APIRouter, Depends, HTTPException
# Functions
from vauth import login , VAuth
from multiapi_routes.Libs.check      import check_config, check_rules

from multiapi_routes.Routes.Skeleton import Skeleton

# DB 
from multiapi_routes.Libs.DB import ConfigModel

# Defining the configs class which inherits from APIRouter
class Configs(APIRouter):

    permissions = {
        "all"  : "skeleton.{}",
        "read" : "configs.read.{}",
        "create" : "configs.create.{}",
        "update" : "configs.update.{}",
        "delete" : "configs.delete.{}"
    }
    # Initializing the class with necessary routes and variables
    def __init__(self, *args, **kwargs):
        self.name = "config"
        self.global_local = "config.*"
        super().__init__(*args, **kwargs)

        self.skeletons = Skeleton()

        print(VAuth().register("config",["read","create","update","delete"],True))
        # Adding routes for different HTTP methods
        self.add_api_route("/configs", self.read_items, methods=["GET"], dependencies=[Depends(login)])
        self.add_api_route("/configs", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/configs", self.update_item, methods=["PUT"], dependencies=[Depends(login)])
        self.add_api_route("/configs", self.delete_item, methods=["DELETE"], dependencies=[Depends(login)])

    # Defining the read_items method
    def read_items(self, token: str = Depends(login), id: str = ""):
        permission = [self.permissions["all"].format("*"),self.permissions["read"].format("*")]
        # If id is not provided, return all items
        if id == "":
            if ConfigModel.find().count() == 0:
                raise HTTPException(status_code=404, detail="No items found.")
            items = []
            for _ in ConfigModel.find().all():
                temp = permission.copy()
                temp.append(self.permissions["read"].format(_.id))
                temp.append(self.permissions["all"].format(_.id))
                if token.is_allow(temp):
                    items.append(_)
            if not items:
                raise HTTPException(status_code=404, detail="No items found.")
            return items
        # If id is provided, return the specific item
        else:
            permission.append(self.permissions["read"].format(id))
            permission.append(self.permissions["all"].format(id))
            if token.is_allow(permission):
                item = ConfigModel.find(ConfigModel.id == id)
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

    # Defining the create_item method
    def create_item(self, config : Dict, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["create"].format("*")]
        # Define the rules for the config model
        parameters = ["id","api_id", "function_name","config"]
        # Check if all required parameters are config
        rule_check = check_rules(rule_list=parameters, row_rest=config)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        check_function = self.skeletons.read_items(token,id=config["api_id"])
        if config["function_name"] not in [_ for _ in check_function.skeleton]:
            raise HTTPException(status_code=400, detail=f"Function name {config['function_name']} not found in api {config['api_id']}")
        # If the token is allowed, create the config model
        permission.append(self.permissions["create"].format(config["id"]))  
        if token.is_allow(permission):
            try:
                new_config = ConfigModel(**config)
                new_config.save()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            # If the token is not allowed, add permission
            if not token.is_allow(f"config.{config['id']}"):
                VAuth().add_permission_rg("ConfigModel",config["id"])
                token.add_permission(f"{self.name}.{config['id']}")
            return {"info":"ConfigModel Added!","status":"Success"}
        else:
            raise HTTPException(status_code=400, detail="Your token isn't allowed to perform this action.")

    # Defining the update_item method
    def update_item(self, item: Dict, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["update"].format("*")]
        # Define the rules for the config model
        parameters = ["id","api_id", "api_key", "config","model_type"]
        # Check if all required parameters are config
        rule_check = check_rules(rule_list=parameters, row_rest=item)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        permission.append(self.permissions["update"].format(item["id"]))
        permission.append(self.permissions["all"].format(item["id"]))
        # If the token is allowed, update the config model
        if token.is_allow(permission):
            try:
                config_model = ConfigModel.find(ConfigModel.id == item['id']).first()
                if not config_model:
                    raise HTTPException(status_code=404, detail=f"ConfigModel with id {item['id']} not found.")
                for key, value in item.items():
                    setattr(config_model, key, value)
                config_model.save()
                return {"info": f"ConfigModel {item['id']} updated", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error updating ConfigModel: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")

    # Defining the delete_item method
    def delete_item(self, id: str, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["delete"].format("*")]
        permission.append(self.permissions["delete"].format(id))
        permission.append(self.permissions["all"].format(id))
        # If the token is allowed, delete the config model
        if token.is_allow(permission):
            if not check_config(id):
                raise HTTPException(status_code=404, detail=f"ConfigModel with id {id} doesn't exist!")
            try:
                ConfigModel.delete(id)
                return {"info": f"ConfigModel {id} deleted", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error deleting ConfigModel: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
