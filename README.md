<div align="center">

# Affection

> Algebraic Effect for modern Python.

</div>

Tips: I **strongly** recommend you to read [Algebraic Effects for the Rest of Us](https://overreacted.io/algebraic-effects-for-the-rest-of-us/)
before you start.

`Affection` is a small library that brought `Algebraic Effect` to Python.
It leverages decorator and `with` syntax for a better experience.

## Usage

This project is designed to be a single file project.

You can either copy it directly into your project, or add [`affection`](https://pypi.org/project/affection) from [`PyPI`](https://pypi.org/) with your favorite package manager. 

```py
from affection import Effect, Handle, effect, perform


class Log(Effect[None]):
    def __init__(self, content: str):
        self.content = content


def get_name(name: str | None = None) -> str:
    perform(Log(f"Getting name with {name}"))
    return perform(effect("ask_name", str)) if name is None else name


def main():
    h = Handle() # you need one and only one handler for a "frame"

    @Log.handle()
    def _(l: Log):
        print(l.content)

    @effect("ask_name", str).handle()
    def _(_) -> str:
        return "Default"

    with h:
        perform(Log("Test parent log"))

    @Log.handle(override=True) # override the previously declared handler.
    def _(l: Log):
        print("Inner", l.content.lower())

    with h:
        print(get_name("Ann"))
        print(get_name())

if __name__ == "__main__":
    main()
    """
    Test parent log
    Inner getting name with ann
    Ann
    Inner getting name with none
    Default
    """
```

## Why does the API look like this?

Since Python don't have something like macros (which Rust nicely had), I reused the `with` clause
to limit the scope of effect handlers.


I used `@Effect.handle` syntax to register effect handlers just because (currently) it's the only way to ensure **type safety**.
Because `Effect` is a generic class,
so the `handle` clause / method must live in the `Effect` class,
or we can't use the sweet `Self` to annotate **both** the effect type and expected return type.

Allowing you to customize `Effect` by inheriting is great for anything that comes with a context.
However I kept the `effect` factory function just in case you just want a simple `ask_something`
and don't want to waste those previous lines to declare and instantiate a class.

Asynchronous support is done by simply annotating an `Awaitable` or a `Coroutine` for expected return type.
And I used `return` to pass the result instead of inventing `resume` just because it's a bit too complex (think about the original `resume` after a timeout example!)