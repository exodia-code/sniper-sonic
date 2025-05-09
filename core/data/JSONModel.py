import json

class AttrDict(dict):
    def __getattr__(self, item):
        value = self.get(item)
        if isinstance(value, dict):
            return AttrDict(value)
        return value

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, dict):
            return cls({k: cls.from_dict(v) for k, v in data.items()})
        elif isinstance(data, list):
            return [cls.from_dict(i) for i in data]
        else:
            return data
    
class Dex:
    def __init__(self):
        self.path = 'core/data/dex.json'
        self.data = self.load()

    def load(self):
        with open(self.path, "r") as file:
            return AttrDict.from_dict(json.load(file))
    
class Address:
    def __init__(self):
        self.path = 'core/data/address_data.json'
        self.data = self.load()

    def load(self):
        with open(self.path, "r") as file:
            return AttrDict.from_dict(json.load(file))