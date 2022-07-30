"""Affection - Algebraic Effects for modern Python.

Licensed under MIT License.

Copyright (c) 2022 BlueGlassBlock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Here we use `annotations` feature to provide consistent type annotations
from __future__ import annotations

import inspect
from collections.abc import Coroutine
from typing import Any, Callable, Generic, TypeVar

from typing_extensions import Self


class EffectEscaped(RuntimeError):
    """A effect has not been handled, and yet escaped."""


class NoActiveHandle(RuntimeError):
    """You attempted to handle an effect without an active handle."""


class HandleConflict(RuntimeError):
    """You instantiated multiple handles in one frame."""


class __HandlerLookupChain:
    """A lookup chain for handlers, implemented like a stack."""

    def __init__(self):
        self.maps: list[dict[type[Effect[Any]], Callable[[Effect[Any]], Any]]] = [{}]

    def __getitem__(self, key) -> Callable[[Effect[Any]], Any]:
        for mapping in reversed(self.maps):  # iter from last
            if key in mapping:
                return mapping[key]
        raise EffectEscaped(key)

    def __contains__(self, handle: Handle) -> bool:
        return handle.record in self.maps

    def __setitem__(self, key, value) -> None:
        self.maps[-1][key] = value

    def pop(self) -> None:
        self.maps.pop()

    def append(self, d: dict[type[Effect[Any]], Callable[[Effect[Any]], Any]]) -> None:
        self.maps.append(d)


_lookup_chain = __HandlerLookupChain()


_T = TypeVar("_T")


class Effect(Generic[_T]):
    @classmethod
    def handle(
        cls, override: bool = False
    ) -> Callable[[Callable[[Self], _T]], Callable[[Self], _T]]:
        caller_frame = inspect.stack(1)[1]
        handle: Handle | None = None
        for v in caller_frame.frame.f_locals.values():
            if isinstance(v, Handle):
                if handle:
                    raise HandleConflict(HandleConflict.__doc__)
                handle = v
        if not handle:
            raise NoActiveHandle(NoActiveHandle.__doc__)

        def inner(func: Callable[[Self], _T]) -> Callable[[Self], _T]:
            if cls in handle.record and not override:
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
        self.record = {}

    def __enter__(self):
        _lookup_chain.append(self.record)

    def __exit__(self, *_):
        _lookup_chain.pop()
        return False

    def wipe(self, *effects: type[Effect] | Effect) -> None:
        if not effects:  # wipe out everything
            self.record.clear()
        for e in effects:
            if isinstance(e, Effect):
                e = e.__class__  # for dynamically created effects
            self.record.pop(e, None)  # ignore already wiped effects

    def __repr__(self):
        return f"Handle({self.record!r})"


def perform(effect: Effect[_T]) -> _T:
    return _lookup_chain[effect.__class__](effect)
