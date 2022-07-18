"""Affection - Algebraic Effects for modern Python."""

# Here we use `annotations` feature to provide consistent type annotations
from __future__ import annotations

from collections.abc import Coroutine
from typing import Any, Callable, Generic, TypeVar

from typing_extensions import Self


class EffectEscaped(RuntimeError):
    """A effect has not been handled, and yet escaped."""


class InactiveHandle(RuntimeError):
    """The handle is inactive, and required to be used in `with` clause."""


class __HandlerLookupChain:
    """A lookup chain for handlers, implemented like a stack."""

    def __init__(self):
        self.maps: list[dict[type[Effect[Any]], Callable[[Effect[Any]], Any]]] = [{}]

    def __getitem__(self, key) -> Callable[[Effect[Any]], Any]:
        for mapping in reversed(self.maps):  # iter from last
            if key in mapping:
                return mapping[key]
        raise EffectEscaped(key)

    def __setitem__(self, key, value) -> None:
        self.maps[-1][key] = value

    def pop(self) -> None:
        self.maps.pop()

    def append(self) -> dict[type[Effect[Any]], Callable[[Effect[Any]], Any]]:
        d: dict[type[Effect[Any]], Callable[[Effect[Any]], Any]] = {}
        self.maps.append(d)
        return d


_lookup_chain = __HandlerLookupChain()


_T = TypeVar("_T")


class Effect(Generic[_T]):
    @classmethod
    def handle(
        cls, handle: Handle
    ) -> Callable[[Callable[[Self], _T]], Callable[[Self], _T]]:
        # TODO: Automatically determine handle nesting level
        def inner(func: Callable[[Self], _T]) -> Callable[[Self], _T]:
            if handle.record is None:
                raise InactiveHandle(handle)
            if cls in handle.record:
                raise KeyError(f"{cls} is already handled by {func} on this handler!")
            handle.record[cls] = func
            return func

        return inner


AsyncEffect = Effect[Coroutine[Any, Any, _T]]

_dynamic_effects: dict[tuple[str, type], type[Effect[Any]]] = {}


def effect(name: str, cls: type[_T] = type(None)) -> Effect[_T]:
    """Creates an effect instance dynamically.

    Created effects are distinguished by `name` and `cls`.

    Args:
        name (str): The name of the effect.
        cls (type, optional): The expected return type of the effect.

    Returns:

    """

    effect_cls = _dynamic_effects.setdefault((name, cls), type(name, (Effect,), {}))

    return effect_cls()


class Handle:
    def __init__(self):
        self.record = None

    def __enter__(self):
        self.record = _lookup_chain.append()
        return self

    def __exit__(self, *_):
        _lookup_chain.pop()
        return False

    def __repr__(self):
        return f"Handle({self.record!r})"


def perform(effect: Effect[_T]) -> _T:
    return _lookup_chain[effect.__class__](effect)
