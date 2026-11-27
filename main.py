"""Draw a one-page newspaper front page summing up the world news of
Friday 27 November 2026, and write it to /output/entry.png.

Pure Python standard library only: the picture is rasterised into an RGB
buffer with a small built-in 5x7 bitmap font, then encoded as a PNG with
zlib. No network, no randomness, no time or date lookups, so two runs
write byte-identical files.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 768

CREAM = (246, 241, 229)
INK = (20, 32, 46)
NAVY = (15, 27, 45)
RED = (179, 38, 30)
BLUE = (29, 78, 137)
GOLD = (196, 144, 2)
GREY = (90, 96, 104)
LIGHT_LINE = (203, 196, 178)

# 5x7 bitmap font, uppercase ASCII plus digits and common punctuation.
# Each glyph is seven rows of five cells, "1" on and "0" off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", "01100", "01100"),
    ",": (".....", ".....", ".....", ".....", "01100", "00100", "01000"),
    ":": (".....", "01100", "01100", ".....", "01100", "01100", "....."),
    ";": (".....", "01100", "01100", ".....", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", ".....", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", ".....", "00100"),
    "'": ("00100", "00100", "01000", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "01110", ".....", ".....", "....."),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": (".....", "00100", "00100", "11111", "00100", "00100", "....."),
    "=": (".....", ".....", "11111", ".....", "11111", ".....", "....."),
    '"': ("01010", "01010", ".....", ".....", ".....", ".....", "....."),
}

STORIES = [
    (
        "EUROPE",
        BLUE,
        "EU LEADERS DEADLOCKED ON BUDGET",
        "After more than twelve hours of talks, EU leaders failed to "
        "agree on the budget and a new loan for Ukraine.",
    ),
    (
        "UNITED STATES",
        RED,
        "STORM LEAVES 724,000 WITHOUT POWER",
        "The Thanksgiving storm cancelled hundreds of flights and cut "
        "power across the East Coast, reports said.",
    ),
    (
        "UKRAINE",
        BLUE,
        "ZELENSKY WARNS OF NEW MASS STRIKE",
        "Ukraine's president said Russia was preparing a new mass strike "
        "in the coming days as attacks continued.",
    ),
    (
        "UNITED STATES",
        RED,
        "TRUMP CALLS GDP FIGURES FAKE",
        "The US president called official growth figures fake and "
        "demanded a probe of his own Commerce Department.",
    ),
    (
        "INDIA",
        BLUE,
        "DELHI POLICE FREE 164 IN CYBER SLAVERY RAID",
        "Police in Delhi rescued 164 foreign nationals from premises "
        "said to run an online scam racket.",
    ),
]


class Canvas:
    """A plain RGB pixel buffer with rectangle and bitmap-text drawing."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def rect(self, x, y, w, h, colour):
        r, g, b = colour
        for row in range(y, y + h):
            base = (row * self.width + x) * 3
            for col in range(w):
                off = base + col * 3
                self.pixels[off] = r
                self.pixels[off + 1] = g
                self.pixels[off + 2] = b

    def text(self, x, y, message, scale, colour):
        cursor = x
        for ch in message.upper():
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, cell in enumerate(row):
                    if cell == "1":
                        self.rect(
                            cursor + gx * scale,
                            y + gy * scale,
                            scale,
                            scale,
                            colour,
                        )
            cursor += 6 * scale
        return cursor

    def text_width(self, message, scale):
        return len(message) * 6 * scale - scale

    def centred(self, y, message, scale, colour):
        x = (self.width - self.text_width(message, scale)) // 2
        self.text(x, y, message, scale, colour)

    def wrap(self, message, scale, max_width):
        """Split a message into lines that fit max_width pixels."""
        words = message.split(" ")
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if self.text_width(trial, scale) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


def png_bytes(canvas):
    """Encode the canvas as a PNG: signature, IHDR, IDAT, IEND."""

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.width * 3
    for row in range(canvas.height):
        raw.append(0)
        start = row * stride
        raw += canvas.pixels[start:start + stride]
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def draw():
    canvas = Canvas(WIDTH, HEIGHT, CREAM)

    # Masthead: navy band with the paper name and the date it sums up.
    # A gold rule under the band sets this day's front page apart.
    canvas.rect(0, 0, WIDTH, 148, NAVY)
    canvas.rect(0, 148, WIDTH, 6, GOLD)
    canvas.centred(22, "THE WORLD IN ONE DAY", 6, (247, 242, 231))
    canvas.centred(104, "FRIDAY 27 NOVEMBER 2026", 3, GOLD)

    # Subhead strip.
    canvas.centred(168, "THE DAY IN FIVE STORIES", 2, GREY)
    canvas.rect(48, 196, WIDTH - 96, 3, LIGHT_LINE)

    # Five stories, each with a coloured kicker, a headline and a summary.
    y = 216
    for kicker, accent, headline, summary in STORIES:
        canvas.rect(48, y + 4, 10, 76, accent)
        canvas.text(76, y, kicker, 2, accent)
        headline_lines = canvas.wrap(headline, 3, WIDTH - 76 - 48)
        line_y = y + 24
        for line in headline_lines:
            canvas.text(76, line_y, line, 3, INK)
            line_y += 26
        summary_lines = canvas.wrap(summary, 2, WIDTH - 76 - 48)
        for line in summary_lines:
            canvas.text(76, line_y, line, 2, (52, 58, 66))
            line_y += 18
        y += 100
        if y < HEIGHT - 60:
            canvas.rect(48, y - 8, WIDTH - 96, 2, LIGHT_LINE)

    # Footer.
    canvas.centred(
        730, "DRAWN FROM REPORTS PUBLISHED ON 27 NOVEMBER 2026", 2, GREY
    )
    return canvas


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    with open(os.path.join(out_dir, "entry.png"), "wb") as handle:
        handle.write(data)


if __name__ == "__main__":
    main()
