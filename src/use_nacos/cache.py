import json
import os


class BaseCache:
    def set(self, key, value):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def exists(self, key):
        raise NotImplementedError


class MemoryCache(BaseCache):
    def __init__(self):
        self.storage = {}

    def set(self, key, value):
        self.storage[key] = value

    def get(self, key):
        return self.storage.get(key)

    def exists(self, key):
        return key in self.storage


class FileCache(BaseCache):
    def __init__(self, file_path=None):
        self.file_path = file_path or '_nacos_config_cache.json'
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)

    def _read_file(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _write_file(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f)

    def set(self, key, value):
        data = self._read_file()
        data[key] = value
        self._write_file(data)

    def get(self, key):
        data = self._read_file()
        return data.get(key)

    def exists(self, key):
        data = self._read_file()
        return key in data


memory_cache = MemoryCache()
