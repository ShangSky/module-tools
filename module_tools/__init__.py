__version__ = "0.0.1"


import pkgutil
from typing import Callable, Iterable, Optional, Type, TypeVar, Any
from types import ModuleType
from importlib import import_module

T = TypeVar("T")


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "{}" does not define a "{}" attribute/class'.format(module_path, class_name)
        ) from err


def find_module_strings(pkg_name: str, *, recursive: bool = False) -> Iterable[str]:
    pkg = import_module(pkg_name)
    module_path = getattr(pkg, "__path__", None)
    if module_path is None:
        return [pkg_name]
    iter_modules_func = pkgutil.walk_packages if recursive else pkgutil.iter_modules
    return (
        module_info[1]
        for module_info in iter_modules_func(module_path, pkg.__name__ + ".")
        if not module_info[2]
    )


def find_modules(pkg_name: str, *, recursive: bool = False) -> Iterable[ModuleType]:
    return (
        import_module(module_string)
        for module_string in find_module_strings(pkg_name, recursive=recursive)
    )


def iter_objs_from_module(
    module: ModuleType, cls: Type[T], func: Optional[Callable[[Any, Any], bool]] = None
) -> Iterable[T]:
    for attr_name in dir(module):
        if not attr_name.startswith("__"):
            attr = getattr(module, attr_name)
            call = func or isinstance
            if call(attr, cls):
                yield attr


def iter_objs_from_modules(
    pkg_names: Iterable[str],
    cls: Type[T],
    *,
    recursive: bool = False,
    func: Optional[Callable[[Any, Any], bool]] = None
) -> Iterable[T]:
    obj_ids = set()
    for pkg_name in pkg_names:
        modules = find_modules(pkg_name, recursive=recursive)
        for module in modules:
            for obj in iter_objs_from_module(module, cls, func=func):
                obj_id = id(obj)
                if obj_id in obj_ids:
                    continue
                obj_ids.add(obj_id)
                yield obj
