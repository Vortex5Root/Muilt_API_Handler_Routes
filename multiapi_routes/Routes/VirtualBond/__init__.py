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

    permissions = {
        "all"  : "virtual_bond.{}",
        "read" : "virtual_bond.read.{}",
        "create" : "virtual_bond.create.{}",
        "update" : "virtual_bond.update.{}",
        "delete" : "virtual_bond.delete.{}"
    }

    # Initializing the class with necessary routes and variables
    def __init__(self, *args, **kwargs):
        self.name = "virtual_bond"
        self.global_local = "virtual_bond.*"

        print(VAuth().register("virtual_bond",["read","create","update","delete"],True))
        # Adding routes for different HTTP methods
        self.add_api_route("/virtual/bonds", self.read_items,  methods=["GET"], dependencies=[Depends(login)])
        self.add_api_route("/virtual/bonds", self.create_item, methods=["POST"], dependencies=[Depends(login)])
        self.add_api_route("/virtual/bonds", self.update_item, methods=["PUT"], dependencies=[Depends(login)])
        self.add_api_route("/virtual/bonds", self.delete_item, methods=["DELETE"], dependencies=[Depends(login)])
        super().__init__(*args, **kwargs)

    # Defining the read_items method
    def read_items(self, token: str = Depends(login), id: str = ""):
        permission = [self.permissions["all"].format("*"),self.permissions["read"].format("*")]
        # If id is not provided, return all items
        if id == "":
            if VirtualBond.find().count() == 0:
                raise HTTPException(status_code=404, detail="No items found.")
            items = []
            for _ in VirtualBond.find().all():
                temp = permission.copy()
                temp.append(self.permissions["read"].format(_.id))
                temp.append(self.permissions["all"].format(_.id))
                if token.is_allow(temp):
                    items.append(_) 
            if not items:
                raise HTTPException(status_code=404, detail="No items found.")
            return items
        else:
            try:
                if not check_virtual_bond(id):
                    raise HTTPException(status_code=404, detail=f"VirtualBond with id {id} doesn't exist!")
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"VirtualBond with id {id} doesn't exist!")
            temp = [self.permissions["all"].format(id),self.permissions["read"].format(id)]
            [permission.append(_) for _ in temp]
            # If id is provided, return the item with the given id
            item = VirtualBond.find(VirtualBond.id == id).first()
            if not token.is_allow(permission):
                raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
            return item

    # Defining the create_item method
    def create_item(self, virtual_bond : Dict, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["create"].format("*")]
        # Define the rules for the virtual_bond model
        parameters = ["id","row_code"]
        # Check if all required parameters are virtual_bond
        rule_check = check_rules(rule_list=parameters, row_rest=virtual_bond)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        #self.apis.read_items(token,id=virtual_bond["id"])
        # If the token is allowed, create the virtual_bond model
        if token.is_allow(permission):
            try:
                new_virtual_bond = VirtualBond(**virtual_bond)
                new_virtual_bond.save()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            # If the token is not allowed, add permission
            if not token.is_allow(f"virtual_bond.{virtual_bond['id']}"):
                VAuth().add_permission_rg("virtual_bond",virtual_bond["id"])
                token.add_permission(f"{self.name}.{virtual_bond['id']}")
            return {"info":f"virtual_bond ({virtual_bond['id']}) Added!","status":"Success"}
        else:
            raise HTTPException(status_code=400, detail="Your token isn't allowed to perform this action.")

    # Defining the update_item method
    def update_item(self, item: Dict, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["update"].format("*")]
        permission.append(self.permissions["update"].format(item["id"]))
        permission.append(self.permissions["all"].format(item["id"]))
        # Define the rules for the virtual_bond model
        parameters = ["id","row_code"]
        # Check if all required parameters are virtual_bond
        rule_check = check_rules(rule_list=parameters, row_rest=item)
        if rule_check is not True:
            raise HTTPException(status_code=400, detail=f"Missing or invalid parameters: {rule_check}")
        # If the token is allowed, update the virtual_bond model
        if token.is_allow(permission):
            try:
                virtual_bond_model = VirtualBond.find(VirtualBond.id == item['id']).first()
                if not virtual_bond_model:
                    raise HTTPException(status_code=404, detail=f"VirtualBond with id {item['id']} not found.")
                for key, value in item.items():
                    setattr(virtual_bond_model, key, value)
                virtual_bond_model.save()
                return {"info": f"VirtualBond {item['id']} updated", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error updating VirtualBond: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")

    # Defining the delete_item method
    def delete_item(self, id: str, token: str = Depends(login)):
        permission = [self.permissions["all"].format("*"),self.permissions["delete"].format("*"),self.permissions["delete"].format(id)]
        # If the token is allowed, delete the virtual_bond model
        if token.is_allow(permission):
            if not check_virtual_bond(id):
                raise HTTPException(status_code=404, detail=f"VirtualBond with id {id} doesn't exist!")
            try:
                VirtualBond.delete(id)
                return {"info": f"VirtualBond {id} deleted", "status": "Success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error deleting VirtualBond: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Your token isn't allowed to perform this action.")
