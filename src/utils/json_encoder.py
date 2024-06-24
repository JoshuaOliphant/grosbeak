from datetime import date
import json
from pydantic import BaseModel


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.dict()
        return super().default(obj)
