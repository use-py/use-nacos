import abc
import json
import sys

import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class Serializer(abc.ABC):

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class TextSerializer(Serializer):
    """
    >>> text = TextSerializer()
    >>> text('a = 1')
    'a = 1'
    >>> text('a = 1\\n[foo]\\nb = 2')
    'a = 1\\n[foo]\\nb = 2'
    """

    def __call__(self, data) -> str:
        return data


class JsonSerializer(Serializer):
    """
    >>> json_ = JsonSerializer()
    >>> json_('{"a": 1}')
    {'a': 1}
    >>> json_('{"a": 1, "foo": {"b": 2}}')
    {'a': 1, 'foo': {'b': 2}}
    """

    def __call__(self, data) -> dict:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise SerializerException(f"Cannot parse data: {data!r}")


class YamlSerializer(Serializer):
    """
    >>> yaml_ = YamlSerializer()
    >>> yaml_('a: 1')
    {'a': 1}
    >>> yaml_('a: 1\\nfoo:\\n  b: 2')
    {'a': 1, 'foo': {'b': 2}}
    """

    def __call__(self, data) -> dict:
        try:
            return yaml.safe_load(data)
        except yaml.YAMLError:
            raise SerializerException(f"Cannot parse data: {data!r}")


class TomlSerializer(Serializer):
    """
    >>> toml = TomlSerializer()
    >>> toml('a = 1')
    {'a': 1}
    >>> toml('a = 1\\n[foo]\\nb = 2')
    {'a': 1, 'foo': {'b': 2}}
    """

    def __call__(self, data) -> dict:
        try:
            return tomllib.loads(data)
        except Exception:
            raise SerializerException(f"Cannot parse data: {data!r}")


class SerializerException(Exception):
    pass


class AutoSerializer(Serializer):
    """
    >>> auto = AutoSerializer()
    >>> auto('a = 1')
    {'a': 1}
    >>> auto('a = 1\\n[foo]\\nb = 2')
    {'a': 1, 'foo': {'b': 2}}
    >>> auto('{"a": 1}')
    {'a': 1}
    >>> auto('{"a": 1, "foo": {"b": 2}}')
    {'a': 1, 'foo': {'b': 2}}
    >>> auto('a: 1')
    {'a': 1}
    >>> auto('a: 1\\nfoo:\\n  b: 2')
    {'a': 1, 'foo': {'b': 2}}
    """

    def __init__(self):
        self.serializers = (
            JsonSerializer(),
            TomlSerializer(),
            YamlSerializer(),
            TextSerializer(),
        )

    def __call__(self, data) -> dict:
        for serializer in self.serializers:
            try:
                return serializer(data)
            except SerializerException:
                pass
        raise SerializerException(f"Cannot parse data: {data!r}")
