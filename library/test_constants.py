import os
from unittest import TestCase

from library import constants


class get_uri(TestCase):
    def test_get_uri(self):
        # Make uri.ini and make sure stuff exists
        if not os.path.exists("uri.ini"):
            file = open("uri.ini", "w+")
            file.write("[URI]\n")
            file.write("#Put URI Here\n")
            file.write("uri=apple.net\n")
        config = constants.get_uri()
        assert "URI" in config
