import os
from typing import Dict, Type, TypeVar, Optional, List
from engine.logger import Logger
from engine.core.resource import Resource
from engine.core.resource_format_loader import ResourceFormatLoader

T = TypeVar("T", bound=Resource)


class ResourceLoader:
    """
    Engine subsystem for loading and caching resources.
    """

    _CACHE: Dict[str, Resource] = {}
    _LOADERS: List[ResourceFormatLoader] = []

    @classmethod
    def add_resource_format_loader(cls, loader: ResourceFormatLoader) -> None:
        cls._LOADERS.append(loader)

    @classmethod
    def load(cls, path: str, type_hint: Type[T] = Resource) -> Optional[T]:
        if path in cls._CACHE:
            res = cls._CACHE[path]
            if isinstance(res, type_hint) or issubclass(type(res), type_hint):
                return res
            if type_hint is Resource:
                return res

            Logger.error(
                f"Resource at '{path}' exists but is {type(res).__name__}, expected {type_hint.__name__}",
                "ResourceLoader",
            )
            return None

        if not os.path.exists(path):
            Logger.error(
                f"Cannot load resource. File not found: {path}", "ResourceLoader"
            )
            return None

        _, ext = os.path.splitext(path)
        ext = ext.lower().strip(".")
        found_loader: Optional[ResourceFormatLoader] = None
        for loader in cls._LOADERS:
            if ext in loader.get_recognized_extensions():
                found_loader = loader
                break

        if not found_loader:
            Logger.error(f"No loader found for resource '{path}'", "ResourceLoader")
            return None

        try:
            loaded_res = found_loader.load(path, path)
            loaded_res.take_over_path(path)
            cls._CACHE[path] = loaded_res
            Logger.info(f"Loaded {loaded_res.get_class()}: {path}", "ResourceLoader")
            return loaded_res
        except Exception as e:
            Logger.error(f"Error loading resource '{path}': {e}", "ResourceLoader")
            return None
