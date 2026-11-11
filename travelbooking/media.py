"""Photo and logo links for hotels, buses and flights, taken straight from the web.

Nothing is downloaded: the pages just point at the images. Photos come from Pexels
(free to use and link to); airline logos come from the Kiwi.com logo CDN. Every <img>
using these has an onerror fallback, so a missing image never breaks a page.
"""


def pexels(photo_id, width=900):
    return (f'https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg'
            f'?auto=compress&cs=tinysrgb&w={width}')


# Rooms, lobbies, pools and buildings, mixed so neighbours in a list look different.
HOTEL_PHOTOS = [pexels(i) for i in (
    5318066, 7031731, 17619969, 5157828, 34672504, 14024023, 10902407, 19988067,
    11437918, 6876590, 15273732, 35172686, 4946758, 10571080, 18285946, 14025913,
    6394574, 14442396, 5461582, 9788991, 6186819, 6127022,
)]

BUS_PHOTOS = [pexels(i) for i in (21620928, 18029613, 25793006, 17361247, 6307071)]

PLANE_PHOTOS = [pexels(i) for i in (
    5071151, 11618710, 38330309, 3884790, 36086229, 26545507, 13411556, 28152364,
)]

# Airline name (lower case) -> IATA code, used for the logo.
AIRLINE_CODES = {
    'air india': 'AI', 'indigo': '6E', 'vistara': 'UK', 'spicejet': 'SG',
    'akasa air': 'QP', 'air india express': 'IX', 'go first': 'G8', 'alliance air': '9I',
    'emirates': 'EK', 'qatar airways': 'QR', 'singapore airlines': 'SQ',
    'british airways': 'BA', 'lufthansa': 'LH',
}


def pick(photos, key):
    """A stable photo for an item: the same hotel/bus/flight always gets the same one."""
    return photos[(int(key or 0) * 7) % len(photos)]


def airline_logo(name):
    code = AIRLINE_CODES.get((name or '').strip().lower())
    return f'https://images.kiwi.com/airlines/64x64/{code}.png' if code else ''
