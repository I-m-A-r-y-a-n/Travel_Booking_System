"""Reading and checking the passenger details a person types into the booking form."""
import re

from .models import Passenger

GENDERS = Passenger.GENDER_CHOICES
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,59}$")
MAX_AGE = 120


def blank_rows(count, first_name=''):
    rows = [{'n': n, 'name': '', 'age': '', 'gender': '', 'errors': {}} for n in range(1, count + 1)]
    if rows and first_name:
        rows[0]['name'] = first_name
    return rows


def read_passengers(post, count):
    """Returns (rows, ok). Each row keeps what was typed plus an `errors` dict, so the
    form can be shown again with the mistakes marked."""
    rows, ok = [], True
    valid_genders = {value for value, _ in GENDERS}
    for n in range(1, count + 1):
        name = ' '.join((post.get(f'name_{n}') or '').split())
        age_text = (post.get(f'age_{n}') or '').strip()
        gender = (post.get(f'gender_{n}') or '').strip()
        errors = {}
        if not NAME_RE.match(name):
            errors['name'] = 'Enter the name as on the ID (letters only).'
        if not age_text.isdigit() or not 0 <= int(age_text) <= MAX_AGE:
            errors['age'] = 'Enter an age from 0 to 120.'
        if gender not in valid_genders:
            errors['gender'] = 'Choose a gender.'
        ok = ok and not errors
        rows.append({'n': n, 'name': name, 'age': age_text, 'gender': gender, 'errors': errors})
    return rows, ok
