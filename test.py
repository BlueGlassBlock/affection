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

            @Log.handle(i_h)
            def _(l: Log):
                print("Inner", l.content.lower())

            print(get_name("Ann"))
            print(get_name())


if __name__ == "__main__":
    main()
