class Truncator:

    def __init__(self, text) -> None:
        self.text = text

    def chars(self, length: int) -> str:
        return f"{self.text[:length]}..."


def truncatechars(text, length):
    return Truncator(text).chars(length)
