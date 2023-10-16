# Importing necessary libraries and functions #
#=============================================#
# Typing
from typing  import Dict
# RestAPI Lib
from fastapi import APIRouter, Depends, HTTPException
# Functions
from vauth import login , VAuth
from multiapi_routes.Libs.check      import check_config, check_rules

# DB 
from multiapi_routes.Libs.DB import ConfigModel

# Defining the configs class which inherits from APIRouter
class Configs(APIRouter):
    # Initializing the class with necessary routes and variables
    def __init__(self, *args, **kwargs):
        self.name = "config"
        self.global_local = "config.*"
        super().__init__(*args, **kwargs)

        print(VAuth().register("config",["read","create","update","delete"],True))
        # Adding routes for different HTTP methods
        self.add_api_route("/configs", self.read_items, methods=["GET"], dependencies=[Depends(login)])
        self.add_api_route("/configs", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/configs", self.update_item, methods=["PUT"], dependencies=[Depends(login)])
        self.add_api_route("/configs", self.delete_item, methods=["DELETE"], dependencies=[Depends(login)])

    # Defining the read_items method
    def read_items(self, token: str = Depends(login), id: str = ""):
        action = "read"
        global_local = "config.read.*"
        # If id is not provided, return all items
        if id == "":
            if ConfigModel.find().count() == 0:
                raise HTTPException(status_code=404, detail="No items found.")
            items = [_ for _ in ConfigModel.find().all() if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{_.id}"])]
            #print(item)
            if not items:
                raise HTTPException(status_code=404, detail="No items found.")
            return items
        # If id is provided, return the specific item
        else:
            if token.is_allow([self.global_local, global_local, f"{self.name}.{action}.{id}"]):
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
        action = "create"
        global_local = "config.create.*"
        # Define the rules for the config model
        parameters = ["id","api_id", "function_name","config"]
        # Check if all required parameters are config
        rule_check = check_rules(rule_list=parameters, row_rest=config)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        api = self.apis.read_items(token,id=config["api_id"])
        if config["function_name"] not in [_ for _ in api["skeleton"]]:
            raise HTTPException(status_code=400, detail=f"Function name {config['function_name']} not found in api {config['api_id']}")
        # If the token is allowed, create the config model
        if token.is_allow([self.global_local, global_local, f"config.create.{config['id']}"]):
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
        action = "update"
        global_local = "config.update.*"
        # Define the rules for the config model
        parameters = ["id","api_id", "api_key", "config","model_type"]
        # Check if all required parameters are config
        rule_check = check_rules(rule_list=parameters, row_rest=item)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        # If the token is allowed, update the config model
        if token.is_allow([self.global_local, global_local, f"config.update.{item['id']}"]):
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
        action = "delete"
        # If the token is allowed, delete the config model
        if token.is_allow([f"{self.name}.{action}.{id}"]):
            if not check_config(id):
                raise HTTPException(status_code=404, detail=f"ConfigModel with id {id} doesn't exist!")
            try:
                ConfigModel.delete(id)
                return {"info": f"ConfigModel {id} deleted", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error deleting ConfigModel: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
