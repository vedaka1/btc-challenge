class TextMD:
    """A class that receives text and escapes all unwanted symbols in it"""

    _symbols_to_ignore: str = r"_*[]()~`>#+-=|{}.!"

    def __init__(self, value: str) -> None:
        sanitized_value = value.replace(r"\*", "*").replace(r"\`", "`")
        for symbol in self._symbols_to_ignore:
            sanitized_value = sanitized_value.replace(symbol, rf"\{symbol}")
        self.value = sanitized_value


class LinkMD:
    """A class that receives text and escapes all unwanted symbols in it"""

    _symbols_to_ignore: str = r"()"

    def __init__(self, value: str) -> None:
        self.value = value.replace(" ", "")
        for symbol in self._symbols_to_ignore:
            self.value = self.value.replace(symbol, rf"\{symbol}")
