<div align="center">

# Affection

> Algebraic Effect for modern Python.

</div>

Tips: I **strongly** recommend you to read [Algebraic Effects for the Rest of Us](https://overreacted.io/algebraic-effects-for-the-rest-of-us/)
before you start.

`Affection` is a small library that implements `Algebraic Effect` for Python.
It leverages `asyncio`, decorator and `with` syntax for a smooth experience.

Warning: Please note that until [Higher Rank Type Variants](https://github.com/python/typing/issues/548)
are supported in Python, the `Effect.handle` API will be quite ugly.

## Usage

This project is designed to be a single file project.

You can either directly copy it into your project, or add [`affection`](https://pypi.org/project/affection) from [`PyPI`](https://pypi.org/) with your favorite package manager. 

```py
from affection import Effect, Handle, effect, perform


class Log(Effect[None]):
    def __init__(self, content: str):
        self.content = content


def get_name(name: str | None = None) -> str:
    perform(Log(f"Getting name with {name}"))
    return perform(effect("ask_name", str)) if name is None else name


def main():
    with Handle() as h:

        @Log.handle(h)
        def _(l: Log):
            print(l.content)

        @effect("ask_name", str).handle(h)
        def _(_) -> str:
            return "Default"

        perform(Log("Test parent log"))

        with Handle() as i_h:
            @Log.handle(h)
            def _(l: Log):
                print("Inner", l.content.lower())
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