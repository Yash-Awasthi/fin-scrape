from verdict.core.primitive import Unit
from verdict.schema import Schema


class CoTUnit(Unit):
    _char: str = "CoT"

    class ResponseSchema(Schema):
        thinking: str
