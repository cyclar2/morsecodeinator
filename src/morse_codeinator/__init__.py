from time import sleep
from typing import ClassVar, Final, Protocol

from gpiozero import LED


class Morse:
    """
    Represents a message in Morse code.
    """

    class MorseSignal(Protocol):
        pass

    class _Dot(MorseSignal):
        def __str__(self):
            return "."

    class _Dash(MorseSignal):
        def __str__(self):
            return "-"

    class _Space(MorseSignal):
        def __str__(self):
            return " "

    class _Slash(MorseSignal):
        def __str__(self):
            return " / "

    class _Invalid(MorseSignal):
        def __str__(self):
            return "?"

    Dot: Final[_Dot] = _Dot()
    """A short pulse."""

    Dash: Final[_Dash] = _Dash()
    """A long pulse."""

    Space: Final[_Space] = _Space()
    """A short space."""

    Slash: Final[_Slash] = _Slash()
    """A long space."""

    Invalid: Final[_Invalid] = _Invalid()
    """A segment that cannot be represented in Morse code."""

    LATIN_TO_MORSE: ClassVar[dict[str, list[MorseSignal]]] = {
        "A": [Dot, Dash],
        "B": [Dash, Dot, Dot, Dot],
        "C": [Dash, Dot, Dash, Dot],
        "D": [Dash, Dot, Dot],
        "E": [Dot],
        "F": [Dot, Dot, Dash, Dot],
        "G": [Dash, Dash, Dot],
        "H": [Dot, Dot, Dot, Dot],
        "I": [Dot, Dot],
        "J": [Dot, Dash, Dash, Dash],
        "K": [Dash, Dot, Dash],
        "L": [Dot, Dash, Dot, Dot],
        "M": [Dash, Dash],
        "N": [Dash, Dot],
        "O": [Dash, Dash, Dash],
        "P": [Dot, Dash, Dash, Dot],
        "Q": [Dash, Dash, Dot, Dash],
        "R": [Dot, Dash, Dot],
        "S": [Dot, Dot, Dot],
        "T": [Dash],
        "U": [Dot, Dot, Dash],
        "V": [Dot, Dot, Dot, Dash],
        "W": [Dot, Dash, Dash],
        "X": [Dash, Dot, Dot, Dash],
        "Y": [Dash, Dot, Dash, Dash],
        "Z": [Dash, Dash, Dot, Dot],
        "0": [Dash, Dash, Dash, Dash, Dash],
        "1": [Dot, Dash, Dash, Dash, Dash],
        "2": [Dot, Dot, Dash, Dash, Dash],
        "3": [Dot, Dot, Dot, Dash, Dash],
        "4": [Dot, Dot, Dot, Dot, Dash],
        "5": [Dot, Dot, Dot, Dot, Dot],
        "6": [Dash, Dot, Dot, Dot, Dot],
        "7": [Dash, Dash, Dot, Dot, Dot],
        "8": [Dash, Dash, Dash, Dot, Dot],
        "9": [Dash, Dash, Dash, Dash, Dot],
        ".": [Dot, Dash, Dot, Dash, Dot, Dash],
        ",": [Dash, Dash, Dot, Dot, Dash, Dash],
        "?": [Dot, Dot, Dash, Dash, Dot, Dot],
        "'": [Dot, Dash, Dash, Dash, Dash, Dot],
        "/": [Dash, Dot, Dot, Dash, Dot],
        "(": [Dash, Dot, Dash, Dash, Dot],
        ")": [Dash, Dot, Dash, Dash, Dot, Dash],
        ":": [Dash, Dash, Dash, Dot, Dot, Dot],
        "=": [Dash, Dot, Dot, Dot, Dash],
        "+": [Dot, Dash, Dot, Dash, Dot],
        "-": [Dash, Dot, Dot, Dot, Dot, Dash],
        '"': [Dot, Dash, Dot, Dot, Dash, Dot],
        "@": [Dot, Dash, Dash, Dot, Dash, Dot],
        "!": [Dash, Dot, Dash, Dot, Dash, Dash],
        "&": [Dot, Dash, Dot, Dot, Dot],
        ";": [Dash, Dot, Dash, Dot, Dash, Dot],
        "_": [Dot, Dot, Dash, Dash, Dot, Dash],
        "$": [Dot, Dot, Dot, Dash, Dot, Dot, Dash],
    }
    """A conversation table from Latin to Morse code."""

    _seq: list[MorseSignal]
    """Internal signal buffer."""

    def __init__(self, message: str):
        """
        Converts a message encoded in ASCII into Morse code.
        """

        self._seq = []

        add_space = False
        """Set to True when the next signal should be preceded by a space."""

        skip_whitespace = True
        """Set to true True if ASCII spaces should not be converted into a Morse slash."""

        in_prosign = False
        """Set to True when a prosign sequence is being processed (anything within square brackets)."""

        invalid_prosign = False
        """Set to True when a prosign sequence contains an invalid character."""

        prosign_buffer: list[str] = []
        """Prosign sequence buffer."""

        # Iterate through each character in the message.
        for char in message:
            # Normalise the characters to uppercase.
            char = char.upper()

            match char:
                # Normal whitespace characters will count as a space.
                case " " | "\n" | "\r":
                    # Ignore extra spaces.
                    if not skip_whitespace:
                        self._seq.append(Morse.Slash)
                        skip_whitespace = True
                        add_space = False

                # Left square bracket starts a prosign sequence.
                case "[":
                    if in_prosign:
                        # Prosign sequences cannot be nested.
                        in_prosign = False
                        prosign_buffer.clear()
                        self._seq.append(Morse.Invalid)
                    else:
                        in_prosign = True

                # Right square bracket ends a prosign sequence.
                case "]":
                    if len(prosign_buffer) == 0:
                        in_prosign = False
                        continue

                    if add_space:
                        self._seq.append(Morse.Space)

                    if invalid_prosign:
                        invalid_prosign = False
                        self._seq.append(Morse.Invalid)
                    else:
                        for ps_char in prosign_buffer:
                            self._seq.extend(Morse.LATIN_TO_MORSE[ps_char])

                    prosign_buffer.clear()

                    add_space = True
                    in_prosign = False
                    skip_whitespace = False

                # Normal characters.
                case _ if char in Morse.LATIN_TO_MORSE:
                    if in_prosign:
                        if not invalid_prosign:
                            prosign_buffer.append(char)
                        continue

                    if add_space:
                        self._seq.append(Morse.Space)

                    self._seq.extend(Morse.LATIN_TO_MORSE[char])
                    add_space = True
                    skip_whitespace = False

                # Invalid characters.
                case _:
                    if in_prosign:
                        invalid_prosign = True
                        continue

                    if add_space:
                        self._seq.append(Morse.Space)

                    self._seq.append(Morse.Invalid)
                    add_space = True
                    skip_whitespace = False

    def __str__(self):
        return "".join(str(x) for x in self._seq)

    def __iter__(self):
        return iter(self._seq)


class TransmissionSource(Protocol):
    def on(self) -> None:
        """
        Signal that a "1" should be transmitted.
        """
        ...

    def off(self) -> None:
        """
        Signal that a "2" should be transmitted.
        """
        ...


class LEDTransmission(TransmissionSource):
    def __init__(self, led: LED):
        self.led = led

    def on(self) -> None:
        self.led.on()

    def off(self) -> None:
        self.led.off()


class DebugTransmission(TransmissionSource):
    def on(self) -> None:
        print("ON ", end="", flush=True)

    def off(self) -> None:
        print(". ", end="", flush=True)


class Transmitter:
    def __init__(self, *transmission_sources: TransmissionSource, duration: int = 100):
        self.transmission_sources = transmission_sources
        self.duration = duration * 0.001

    def _on(self, duration: float) -> None:
        for source in self.transmission_sources:
            source.on()
        sleep(duration)

    def _off(self, duration: float) -> None:
        for source in self.transmission_sources:
            source.off()
        sleep(duration)

    def transmit(self, message: Morse) -> None:
        gap = False
        was_space = False
        for symbol in message:
            match symbol:
                case Morse.Dot:
                    if gap:
                        self._off(self.duration)
                    else:
                        gap = True
                    self._on(self.duration)
                    was_space = False
                case Morse.Dash:
                    if gap:
                        self._off(self.duration)
                    else:
                        gap = True
                    self._on(self.duration * 3)
                    was_space = False
                case Morse.Space | Morse.Invalid:
                    if was_space:
                        raise RuntimeError("wtf")
                    self._off(self.duration * 3)
                    gap = False
                    was_space = True
                case Morse.Slash:
                    if was_space:
                        raise RuntimeError("wtf")
                    self._off(self.duration * 7)
                    gap = False
                    was_space = True


def main() -> None:

    led = LED(17)
    transmitter = Transmitter(DebugTransmission(), LEDTransmission(led))
    input_message = input("Enter a message: ").strip()
    message = Morse(input_message)
    print(message)
    transmitter.transmit(message)
