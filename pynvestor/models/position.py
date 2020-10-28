from pynvestor.models.asset_type import AssetType
from marshmallow import Schema, fields
from marshmallow_enum import EnumField


class Position:
    def __init__(self, asset_type: AssetType, quantity: int, isin: str = None, mic: str = None):
        self.asset_type = AssetType(asset_type)
        self.quantity = quantity
        self.isin = isin
        self.mic = mic

    def __repr__(self):
        return f'{self.__class__.__name__} | {self.asset_type} | {self.isin}'

    def to_json(self):
        result = PositionSchema().dump(self)
        return result


class PositionSchema(Schema):
    asset_type = EnumField(AssetType, dump_by=EnumField.VALUE)
    quantity = fields.Float()
    isin = fields.Str()
    mic = fields.Str()
