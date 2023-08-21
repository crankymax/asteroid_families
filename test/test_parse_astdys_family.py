from unittest import TestCase
from parse_astdys_family import ast_proper_elements, ast_family_members


class Test(TestCase):
    def test_ast_proper_elements(self):
        data_dir = '../../asteroid_data'
        data = ast_proper_elements(data_dir)
        assert len(data) > 1

    def test_parse_tro_family_members(self):
        data_dir = '../../asteroid_data'
        data = ast_family_members(data_dir)
        assert len(data) > 1

