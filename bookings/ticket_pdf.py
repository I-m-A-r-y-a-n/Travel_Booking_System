"""Builds the downloadable PDF ticket for a confirmed booking."""
from math import ceil

from travelbooking.pdf import PDFPage, hex_color

INK = hex_color('#1B1659')
BRAND = hex_color('#4B3FE0')
MUTED = hex_color('#6B6896')
LINE = hex_color('#E4E0F5')
LILAC = hex_color('#F1EFFC')
LILAC2 = hex_color('#DDD7F8')
OK = hex_color('#1E9E6A')
WHITE = (1, 1, 1)

TIPS = {
    'flight': [
        'Carry a valid government photo ID for every passenger.',
        'Reach the airport at least 2 hours before departure.',
        'Cabin baggage up to 7 kg and check-in baggage up to 15 kg per passenger, unless your airline says otherwise.',
    ],
    'bus': [
        'Carry a valid photo ID and show this ticket when boarding.',
        'Be at the boarding point 15 minutes before departure.',
        'Keep your phone charged for live bus tracking.',
    ],
    'hotel': [
        'Carry a valid government photo ID for every guest at check-in.',
        'Show this ticket at the front desk to collect your room key.',
        'Contact the hotel directly for early check-in or late check-out requests.',
    ],
}


def money(value):
    value = float(value)
    return f'Rs. {value:,.0f}' if value == int(value) else f'Rs. {value:,.2f}'


def _day(value):
    return value.strftime('%a, %d %b %Y') if value else ''


def _clock(value):
    return value.strftime('%H:%M') if value else ''


def _details(info):
    """(label, value) pairs for the details grid."""
    if info['kind'] == 'hotel':
        return [
            ('HOTEL', info['title']), ('LOCATION', info['origin']),
            ('ROOM', info['number']), ('GUESTS', str(info['passengers'])),
            ('NIGHTS', str(info['nights'] or '')), ('BOOKED ON', _day(info['booked_on'])),
        ]
    arrives = _clock(info['arrive'])
    if info['day_offset']:
        arrives += f' (+{info["day_offset"]} day)'
    carrier = 'AIRLINE' if info['kind'] == 'flight' else 'OPERATOR'
    number = 'FLIGHT NO.' if info['kind'] == 'flight' else 'BUS NO.'
    rows = [(carrier, info['title']), (number, info['number'])]
    if info['kind'] == 'bus':
        rows.append(('BUS TYPE', info['tag']))
    rows += [
        ('TRAVEL DATE', _day(info['depart'])), ('DEPARTS', _clock(info['depart'])), ('ARRIVES', arrives),
        ('PASSENGERS' if info['kind'] == 'flight' else 'SEATS', str(info['passengers'])),
        ('BOOKED ON', _day(info['booked_on'])),
    ]
    return rows


def build_ticket_pdf(info, user, payment=None):
    """Return PDF bytes for `info` (see bookings.tickets.ticket_info)."""
    page = PDFPage()
    left, width = 40, 515.28
    right = left + width
    pad = 24
    inner_l, inner_r = left + pad, right - pad
    details = _details(info)
    rows = ceil(len(details) / 2)

    # ---- layout (all y values measured from the top of the page)
    card_top = 112
    journey_y = card_top + 108
    details_y = journey_y + 96 + 28
    divider_y = details_y + rows * 38 + 6
    stub_y = divider_y + 30
    card_bottom = stub_y + 92
    card_h = card_bottom - card_top

    # ---- header band
    page.gradient_bar(0, 0, page.width, 150, hex_color('#3B2FD9'), hex_color('#7C5CF5'))
    page.circle(page.width - 30, 18, 78, fill=hex_color('#8869F7'))
    page.circle(page.width - 118, 120, 34, fill=hex_color('#7E5FF5'))
    page.text(left, 58, 'Wayfare', 26, True, WHITE)
    page.text(left, 76, 'E-TICKET  |  BOOKING CONFIRMATION', 8, True, LILAC2, spacing=1.1)
    page.text(right, 44, 'BOOKING REF', 8, True, LILAC2, align='right', spacing=1.1)
    page.text(right, 70, info['ref'], 22, True, WHITE, align='right')

    # ---- card
    page.rect(left, card_top, width, card_h, fill=WHITE, stroke=LINE, line_width=1, radius=16)

    pill_w = 92
    page.rect(inner_l, card_top + 20, pill_w, 22, fill=OK, radius=11)
    page.text(inner_l + pill_w / 2, card_top + 34.5, info['status_label'].upper(), 8.5, True, WHITE,
              align='center', spacing=1)
    caption = {'flight': 'FLIGHT TICKET', 'bus': 'BUS TICKET', 'hotel': 'HOTEL VOUCHER'}[info['kind']]
    page.text(inner_r, card_top + 34.5, caption, 8.5, True, MUTED, align='right', spacing=1.2)

    page.text(inner_l, card_top + 74, info['title'], 17, True, INK)
    sub = '  |  '.join(part for part in (info['number'], info['tag']) if part)
    page.text(inner_l, card_top + 91, sub, 10, False, MUTED)

    # ---- journey block
    page.rect(inner_l, journey_y, inner_r - inner_l, 96, fill=LILAC, radius=14)
    jl, jr = inner_l + 20, inner_r - 20
    mid = (inner_l + inner_r) / 2
    if info['kind'] == 'hotel':
        page.text(jl, journey_y + 26, 'CHECK-IN', 7.5, True, MUTED, spacing=1)
        page.text(jl, journey_y + 52, info['check_in'].strftime('%d %b %Y'), 18, True, INK)
        page.text(jl, journey_y + 70, info['check_in'].strftime('%A'), 9.5, False, MUTED)
        page.text(jr, journey_y + 26, 'CHECK-OUT', 7.5, True, MUTED, align='right', spacing=1)
        page.text(jr, journey_y + 52, info['check_out'].strftime('%d %b %Y'), 18, True, INK, align='right')
        page.text(jr, journey_y + 70, info['check_out'].strftime('%A'), 9.5, False, MUTED, align='right')
        middle_top = f'{info["nights"]} night{"s" if info["nights"] != 1 else ""}'
        middle_bottom = info['origin']
    else:
        page.text(jl, journey_y + 26, 'DEPARTURE', 7.5, True, MUTED, spacing=1)
        page.text(jl, journey_y + 50, info['origin'], 18, True, INK)
        page.text(jl, journey_y + 69, _clock(info['depart']), 12, True, BRAND)
        page.text(jl, journey_y + 83, _day(info['depart']), 8.5, False, MUTED)
        page.text(jr, journey_y + 26, 'ARRIVAL', 7.5, True, MUTED, align='right', spacing=1)
        page.text(jr, journey_y + 50, info['dest'], 18, True, INK, align='right')
        arrive = _clock(info['arrive']) + (f'  +{info["day_offset"]}' if info['day_offset'] else '')
        page.text(jr, journey_y + 69, arrive, 12, True, BRAND, align='right')
        page.text(jr, journey_y + 83, _day(info['arrive']), 8.5, False, MUTED, align='right')
        middle_top = info['duration']
        middle_bottom = info['tag']
    line_y = journey_y + 44
    page.text(mid, line_y - 8, middle_top, 10, True, INK, align='center')
    page.line(mid - 62, line_y, mid + 62, line_y, color=BRAND, width=1.2, dash=(4, 3))
    page.circle(mid - 62, line_y, 3.2, fill=BRAND)
    page.circle(mid + 62, line_y, 3.2, fill=BRAND)
    page.text(mid, line_y + 17, middle_bottom, 8.5, False, MUTED, align='center')

    # ---- details grid
    col_x = (inner_l, (inner_l + inner_r) / 2 + 10)
    for index, (label, value) in enumerate(details):
        x = col_x[index % 2]
        y = details_y + (index // 2) * 38
        page.text(x, y + 8, label, 7.5, True, MUTED, spacing=1)
        page.text(x, y + 24, value or '-', 11, True, INK)

    # ---- perforation
    page.line(inner_l - 8, divider_y, inner_r + 8, divider_y, color=LILAC2, width=1.2, dash=(5, 4))
    page.notch(left, divider_y, 11, 'left', fill=WHITE, stroke=LINE)
    page.notch(right, divider_y, 11, 'right', fill=WHITE, stroke=LINE)

    # ---- traveller and payment
    name = getattr(user, 'name', '') or getattr(user, 'get_full_name', lambda: '')() or getattr(user, 'email', '')
    page.text(inner_l, stub_y + 8, 'BOOKED BY', 7.5, True, MUTED, spacing=1)
    page.text(inner_l, stub_y + 27, name, 12.5, True, INK)
    page.text(inner_l, stub_y + 43, getattr(user, 'email', ''), 9.5, False, MUTED)
    mobile = getattr(user, 'mobile_number', '')
    if mobile:
        page.text(inner_l, stub_y + 57, mobile, 9.5, False, MUTED)

    pay_x = col_x[1]
    page.text(pay_x, stub_y + 8, 'AMOUNT PAID', 7.5, True, MUTED, spacing=1)
    page.text(pay_x, stub_y + 32, money(info['total']), 20, True, OK)
    if info['unit_price'] is not None:
        page.text(pay_x, stub_y + 48, f'{money(info["unit_price"])} x {info["qty_text"]}', 9, False, MUTED)
    if payment is not None:
        method = payment.get_payment_method_display()
        stamp = payment.created_at.strftime('%d %b %Y, %H:%M')
        page.text(pay_x, stub_y + 62, f'Paid by {method}  |  Payment #{payment.id}', 9, False, MUTED)
        page.text(pay_x, stub_y + 75, stamp, 9, False, MUTED)

    # ---- before you travel
    notes_y = card_bottom + 26
    page.text(left, notes_y, 'Before you travel', 12, True, INK)
    y = notes_y + 20
    for tip in TIPS[info['kind']]:
        page.circle(left + 4, y - 3, 2, fill=BRAND)
        y = page.paragraph(left + 16, y, tip, 9.5, width - 16, color=MUTED, leading=13) + 3

    # ---- footer
    foot_y = page.height - 62
    page.line(left, foot_y, right, foot_y, color=LINE, width=1)
    page.text(left, foot_y + 18, 'Wayfare is an academic project. Bookings and payments are simulated.', 8.5, False, MUTED)
    page.text(left, foot_y + 31, 'This ticket is not valid for real travel.', 8.5, True, MUTED)
    page.text(right, foot_y + 18, info['ref'], 8.5, True, MUTED, align='right')
    return page.render(title=f'Wayfare ticket {info["ref"]}')
