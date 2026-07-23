"""Data provider registry and factory.

A lightweight plugin-style registry for data providers. Providers live in
``data/providers/`` and are registered via the ``@register(name)`` decorator.
``get_data_provider()`` resolves the configured provider name and instantiates
the corresponding class.

Lazy loading is used so importing this module does not eagerly import every
provider backend.
"""

from __future__ import annotations

import importlib
from typing import Type


_registry: dict[str, Type] = {}


def register(name: str):
    """Register a data-provider class under *name*.

    Example::

        @register("yfinance")
        class YFinanceProvider(BaseDataProvider):
            ...
    """
    def decorator(cls):
        _registry[name] = cls
        return cls
    return decorator


def get_data_provider(name: str | None = None) -> object:
    """Return an instance of the configured data provider.

    If *name* is omitted, the value of ``_config.DATA_PROVIDER`` is used.
    """
    from _config import DATA_PROVIDER

    name = name or DATA_PROVIDER
    cls = _registry.get(name)

    if cls is None:
        module_path = f"data.providers.{name}_provider"
        importlib.import_module(module_path)

    cls = _registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown data provider: {name}")

    return cls()
