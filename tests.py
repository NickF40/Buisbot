"""
Tests of seconday functions with unittest module
"""

import unittest
import re


def validate_time(time, day):
    hour , mins = map(int, time.split(':'))
    if day <= 0:
        raise Exception('Error occurred : invalid day')
    if hour < 3 and day == 1:
        return None, None
    else:
        if hour >= 3:
            return ':'.join([str(hour - 3).rjust(2, '0'), str(mins).rjust(2, '0')]), day
        else:
            day -= 1
            hour = str(24 + hour - 3)
            return ':'.join([hour.rjust(2, '0'), str(mins).rjust(2, '0')]), day


def validate_link(link):
    regex = re.compile(
        r'^(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if re.match(regex, link):
        return True
    return False


class TestCase(unittest.TestCase):

    def test_exception(self):
        self.assertEqual(validate_time('02:00', 1), (None, None))

    def test_normal(self):
        self.assertEqual(validate_time('03:00', 2), ('00:00', 2))

    def test_day_decrement(self):
        self.assertEqual(validate_time('02:00', 2), ('23:00', 1))

    def test_link(self):
        self.assertEqual(validate_link('www.google.com'), True)

    def test_link2(self):
        self.assertEqual(validate_link('just.a.stupid_joke.com'), False)

    def test_link3(self):
        self.assertEqual(validate_link('www.vk.com/somegroup/inlink'), True)


unittest.main()