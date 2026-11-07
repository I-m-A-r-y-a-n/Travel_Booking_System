"""A tiny, dependency-free PDF writer: one page, built-in fonts, text and shapes.

Enough for printable tickets and receipts without installing anything. Coordinates
are in points (1/72 inch) measured from the TOP-LEFT of the page, which is easier to
think about than PDF's bottom-left origin.
"""

# Helvetica / Helvetica-Bold glyph widths (1/1000 em) for ASCII 32..126, used to
# right-align, centre and wrap text.
_HELV = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]
_HELV_BOLD = [
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
    975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
    333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
    611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584,
]

# Characters the standard fonts can't show, swapped for close equivalents.
_REPLACEMENTS = {
    '₹': 'Rs. ', '→': '>', '←': '<', '×': 'x', '–': '-',
    '—': '-', '‘': "'", '’': "'", '“': '"', '”': '"',
    '•': '-', '…': '...', ' ': ' ',
}


def _clean(text):
    text = str(text)
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    # Anything else outside Latin-1 becomes '?', instead of breaking the file.
    return text.encode('latin-1', 'replace').decode('latin-1')


def hex_color(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _num(value):
    return f'{value:.2f}'.rstrip('0').rstrip('.') or '0'


def _rgb(color):
    return ' '.join(_num(c) for c in color)


class PDFPage:
    def __init__(self, width=595.28, height=841.89):
        self.width = width
        self.height = height
        self._ops = []

    # ------------------------------------------------------------------ text
    def text_width(self, text, size, bold=False):
        table = _HELV_BOLD if bold else _HELV
        total = 0
        for ch in _clean(text):
            code = ord(ch)
            total += table[code - 32] if 32 <= code <= 126 else 556
        return total * size / 1000

    def wrap(self, text, size, width, bold=False):
        """Split text into lines no wider than `width` points."""
        lines = []
        for paragraph in _clean(text).split('\n'):
            current = ''
            for word in paragraph.split():
                trial = f'{current} {word}'.strip()
                if current and self.text_width(trial, size, bold) > width:
                    lines.append(current)
                    current = word
                else:
                    current = trial
            lines.append(current)
        return lines

    def text(self, x, y, text, size=10, bold=False, color=(0, 0, 0), align='left', spacing=0):
        """Draw one line of text whose baseline is at y. align: left | right | center."""
        text = _clean(text)
        width = self.text_width(text, size, bold) + spacing * max(len(text) - 1, 0)
        if align == 'right':
            x -= width
        elif align == 'center':
            x -= width / 2
        safe = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        font = 'F2' if bold else 'F1'
        self._ops.append(
            f'BT /{font} {_num(size)} Tf {_rgb(color)} rg {_num(spacing)} Tc '
            f'{_num(x)} {_num(self.height - y)} Td ({safe}) Tj ET'
        )
        return width

    def paragraph(self, x, y, text, size, width, bold=False, color=(0, 0, 0), leading=None):
        """Wrapped text. Returns the y position after the last line."""
        leading = leading or size * 1.35
        for line in self.wrap(text, size, width, bold):
            self.text(x, y, line, size, bold, color)
            y += leading
        return y

    # ---------------------------------------------------------------- shapes
    def rect(self, x, y, w, h, fill=None, stroke=None, line_width=0.8, radius=0):
        top = self.height - y
        if radius:
            path = self._rounded(x, top - h, w, h, min(radius, w / 2, h / 2))
        else:
            path = f'{_num(x)} {_num(top - h)} {_num(w)} {_num(h)} re'
        self._paint(path, fill, stroke, line_width)

    def circle(self, cx, cy, r, fill=None, stroke=None, line_width=0.8):
        k = 0.5523 * r
        x, y = cx, self.height - cy
        path = (f'{_num(x + r)} {_num(y)} m '
                f'{_num(x + r)} {_num(y + k)} {_num(x + k)} {_num(y + r)} {_num(x)} {_num(y + r)} c '
                f'{_num(x - k)} {_num(y + r)} {_num(x - r)} {_num(y + k)} {_num(x - r)} {_num(y)} c '
                f'{_num(x - r)} {_num(y - k)} {_num(x - k)} {_num(y - r)} {_num(x)} {_num(y - r)} c '
                f'{_num(x + k)} {_num(y - r)} {_num(x + r)} {_num(y - k)} {_num(x + r)} {_num(y)} c h')
        self._paint(path, fill, stroke, line_width)

    def notch(self, cx, cy, r, side, fill, stroke, line_width=1):
        """Half-circle cut-out on the edge of a card. side='left' bulges to the right
        of cx (for a card's left edge); side='right' bulges to the left."""
        k = 0.5523 * r
        sign = 1 if side == 'left' else -1
        x, y = cx, self.height - cy
        arc = (f'{_num(x)} {_num(y + r)} m '
               f'{_num(x + sign * k)} {_num(y + r)} {_num(x + sign * r)} {_num(y + k)} {_num(x + sign * r)} {_num(y)} c '
               f'{_num(x + sign * r)} {_num(y - k)} {_num(x + sign * k)} {_num(y - r)} {_num(x)} {_num(y - r)} c')
        # Fill the half disc (erases the card border behind it), then stroke just the curved edge.
        self._ops.append(f'q {_rgb(fill)} rg {arc} h f Q')
        self._ops.append(f'q {_rgb(stroke)} RG {_num(line_width)} w {arc} S Q')

    def line(self, x1, y1, x2, y2, color=(0, 0, 0), width=0.8, dash=None):
        dash_op = f'[{_num(dash[0])} {_num(dash[1])}] 0 d ' if dash else '[] 0 d '
        self._ops.append(
            f'q {dash_op}{_rgb(color)} RG {_num(width)} w '
            f'{_num(x1)} {_num(self.height - y1)} m {_num(x2)} {_num(self.height - y2)} l S Q'
        )

    def gradient_bar(self, x, y, w, h, start, end, steps=90):
        """Left-to-right colour blend, drawn as thin vertical strips."""
        strip = w / steps
        for i in range(steps):
            t = i / (steps - 1)
            color = tuple(a + (b - a) * t for a, b in zip(start, end))
            self.rect(x + i * strip, y, strip + 0.6, h, fill=color)

    def _rounded(self, x, y, w, h, r):
        k = 0.5523 * r
        return (f'{_num(x + r)} {_num(y)} m {_num(x + w - r)} {_num(y)} l '
                f'{_num(x + w - r + k)} {_num(y)} {_num(x + w)} {_num(y + r - k)} {_num(x + w)} {_num(y + r)} c '
                f'{_num(x + w)} {_num(y + h - r)} l '
                f'{_num(x + w)} {_num(y + h - r + k)} {_num(x + w - r + k)} {_num(y + h)} {_num(x + w - r)} {_num(y + h)} c '
                f'{_num(x + r)} {_num(y + h)} l '
                f'{_num(x + r - k)} {_num(y + h)} {_num(x)} {_num(y + h - r + k)} {_num(x)} {_num(y + h - r)} c '
                f'{_num(x)} {_num(y + r)} l '
                f'{_num(x)} {_num(y + r - k)} {_num(x + r - k)} {_num(y)} {_num(x + r)} {_num(y)} c h')

    def _paint(self, path, fill, stroke, line_width):
        parts = ['q']
        if fill is not None:
            parts.append(f'{_rgb(fill)} rg')
        if stroke is not None:
            parts.append(f'{_rgb(stroke)} RG {_num(line_width)} w')
        parts.append(path)
        parts.append('B' if fill is not None and stroke is not None else 'f' if fill is not None else 'S')
        parts.append('Q')
        self._ops.append(' '.join(parts))

    # ---------------------------------------------------------------- output
    def render(self, title='Document', author='Wayfare'):
        """Return the finished PDF as bytes."""
        content = '\n'.join(self._ops).encode('latin-1', 'replace')
        objects = [
            b'<< /Type /Catalog /Pages 2 0 R >>',
            b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            (f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_num(self.width)} {_num(self.height)}] '
             f'/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>').encode(),
            b'<< /Length %d >>\nstream\n' % len(content) + content + b'\nendstream',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>',
            (f'<< /Title ({_clean(title)}) /Author ({_clean(author)}) /Producer (Wayfare) >>').encode('latin-1'),
        ]
        out = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += f'{number} 0 obj\n'.encode() + body + b'\nendobj\n'
        xref = len(out)
        out += f'xref\n0 {len(objects) + 1}\n'.encode()
        out += b'0000000000 65535 f \n'
        for offset in offsets:
            out += f'{offset:010d} 00000 n \n'.encode()
        out += (f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info 7 0 R >>\n'
                f'startxref\n{xref}\n%%EOF\n').encode()
        return bytes(out)
