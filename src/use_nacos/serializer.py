"""Configuration content serializers for use-nacos.

This module provides serializers for parsing configuration content
from Nacos in various formats (JSON, YAML, TOML, plain text).
"""

import abc
import json
import sys
from typing import Any, Union

import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class Serializer(abc.ABC):
    """Abstract base class for configuration serializers.

    Serializers convert raw configuration strings into Python objects.
    """

    @abc.abstractmethod
    def __call__(self, data: str) -> Any:
        """Deserialize the configuration data.

        Args:
            data: Raw configuration string.

        Returns:
            Parsed configuration data.
        """
        raise NotImplementedError


class TextSerializer(Serializer):
    """Plain text serializer that returns the content unchanged.

    Example:
        >>> text = TextSerializer()
        >>> text('a = 1')
        'a = 1'
    """

    def __call__(self, data: str) -> str:
        """Return the input string unchanged.

        Args:
            data: Raw configuration string.

        Returns:
            The same string.
        """
        return data


class JsonSerializer(Serializer):
    """JSON configuration serializer.

    Example:
        >>> json_ = JsonSerializer()
        >>> json_('{"a": 1}')
        {'a': 1}
    """

    def __call__(self, data: str) -> dict:
        """Parse JSON configuration.

        Args:
            data: JSON string.

        Returns:
            Parsed dictionary.

        Raises:
            SerializerException: If the data cannot be parsed as JSON.
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise SerializerException(f"Cannot parse data: {data!r}")


class YamlSerializer(Serializer):
    """YAML configuration serializer.

    Example:
        >>> yaml_ = YamlSerializer()
        >>> yaml_('a: 1')
        {'a': 1}
    """

    def __call__(self, data: str) -> dict:
        """Parse YAML configuration.

        Args:
            data: YAML string.

        Returns:
            Parsed dictionary.

        Raises:
            SerializerException: If the data cannot be parsed as YAML.
        """
        try:
            return yaml.safe_load(data)
        except yaml.YAMLError:
            raise SerializerException(f"Cannot parse data: {data!r}")


class TomlSerializer(Serializer):
    """TOML configuration serializer.

    Example:
        >>> toml = TomlSerializer()
        >>> toml('a = 1')
        {'a': 1}
    """

    def __call__(self, data: str) -> dict:
        """Parse TOML configuration.

        Args:
            data: TOML string.

        Returns:
            Parsed dictionary.

        Raises:
            SerializerException: If the data cannot be parsed as TOML.
        """
        try:
            return tomllib.loads(data)
        except Exception:
            raise SerializerException(f"Cannot parse data: {data!r}")


class SerializerException(Exception):
    """Exception raised when serialization fails."""

    pass


class AutoSerializer(Serializer):
    """Automatic format detection serializer.

    Tries to parse configuration content in the following order:
    1. JSON
    2. TOML
    3. YAML
    4. Plain text (fallback)

    Example:
        >>> auto = AutoSerializer()
        >>> auto('{"a": 1}')  # JSON
        {'a': 1}
        >>> auto('a = 1')  # TOML
        {'a': 1}
        >>> auto('a: 1')  # YAML
        {'a': 1}
    """

    def __init__(self) -> None:
        """Initialize with the default serializer chain."""
        self.serializers: tuple[Serializer, ...] = (
            JsonSerializer(),
            TomlSerializer(),
            YamlSerializer(),
            TextSerializer(),
        )

    def __call__(self, data: str) -> Union[dict, str]:
        """Auto-detect format and parse configuration.

        Args:
            data: Configuration string in any supported format.

        Returns:
            Parsed configuration (dict for JSON/YAML/TOML, str for plain text).

        Raises:
            SerializerException: If no serializer can parse the data.
        """
        for serializer in self.serializers:
            try:
                return serializer(data)
            except SerializerException:
                pass
        raise SerializerException(f"Cannot parse data: {data!r}")
