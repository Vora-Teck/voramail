from root.models import *
from root.extensions import ma
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field, fields


class UserSchema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = auto_field()
    email = auto_field()
    first_name = auto_field()
    last_name = auto_field()
    #full_name = fields.Method("get_full_name")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

class AccountSchema(SQLAlchemySchema):
    class Meta:
        model = Account
        load_instance = True

    id = auto_field()
    account_id = auto_field()
    name = auto_field()
    smtp_username = auto_field()
    active = auto_field()
    created_at = auto_field()
    #user = ma.Nested(UserSchema)

class AccountDetailSchema(SQLAlchemySchema):
    class Meta:
        model = Account
        load_instance = True

    id = auto_field()
    account_id = auto_field()
    name = auto_field()
    smtp_username = auto_field()
    smtp_host = auto_field()
    encryption = auto_field()
    smtp_data = auto_field()
    ip_whitelist = auto_field()
    callback_url = auto_field()
    active = auto_field()
    created_at = auto_field()
    smtp_password = fields.fields.Method("get_password")

    def get_password(self, obj):
        return f"{obj.decrypt_password()}"

user_schema = UserSchema()
account_schema = AccountSchema()
account_detail_schema = AccountDetailSchema()
accounts_schema = AccountSchema(many=True)