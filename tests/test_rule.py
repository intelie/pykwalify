# -*- coding: utf-8 -*-

""" Unit test for pyKwalify - Rule """

# python std lib
import unittest

# 3rd party imports
import pytest

# pyKwalify imports
import pykwalify
from pykwalify.errors import RuleError, SchemaConflict
from pykwalify.rule import Rule


class TestRule(unittest.TestCase):

    def setUp(self):
        pykwalify.partial_schemas = {}

    def testRuleClass(self):
        # this tests seq type with a internal type of str
        r = Rule(schema={"type": "seq", "sequence": [{"type": "str"}]})
        assert r._type is not None, "rule not contain type var"
        assert r._type == "seq", "type not 'seq'"
        assert r._sequence is not None, "rule not contain sequence var"
        assert isinstance(r._sequence, list), "rule is not a list"

        # this tests that the type key must be a string
        with pytest.raises(RuleError):
            Rule(schema={"type": 1}, parent=None)

        # this tests a invalid regexp pattern
        with pytest.raises(RuleError):
            Rule(schema={"type": "str", "pattern": "/@/\\"})

        # this tests the various valid enum types
        Rule(schema={"type": "int", "enum": [1, 2, 3]})
        Rule(schema={"type": "bool", "enum": [True, False]})
        r = Rule(schema={"type": "str", "enum": ["a", "b", "c"]})
        assert r._enum is not None, "enum var is not set proper"
        assert isinstance(r._enum, list), "enum is not set to a list"
        assert len(r._enum) == 3, "invalid length of enum entries"

        # this tests the missmatch between the type and the data inside a enum
        with pytest.raises(RuleError):
            Rule(schema={"type": "str", "enum": [1, 2, 3]})

        # this test the NYI exception for the assert key
        with pytest.raises(RuleError):
            Rule(schema={"type": "seq", "sequence": [{"type": "str", "assert": "foobar"}]})

        r = Rule(schema={"type": "int", "range": {"max": 10, "min": 1}})
        self.assertTrue(r._range is not None, msg="range var not set proper")
        self.assertTrue(isinstance(r._range, dict), msg="range var is not of dict type")

        # this tests that the range key must be a dict
        with pytest.raises(RuleError):
            Rule(schema={"type": "int", "range": []})

        with pytest.raises(RuleError):
            Rule(schema={"type": "str", "range": {"max": "z", "min": "a"}})

        # this tests that min is bigger then max that should not be possible
        with pytest.raises(RuleError):
            Rule(schema={"type": "int", "range": {"max": 10, "min": 11}})

        # test that min-ex is bigger then max-ex, that should not be possible
        with pytest.raises(RuleError):
            Rule(schema={"type": "int", "range": {"max-ex": 10, "min-ex": 11}})

        # this tests that this cannot be used in the root level
        with pytest.raises(RuleError):
            Rule(schema={"type": "str", "unique": True})

        # this tests that unique cannot be used at root level
        with pytest.raises(RuleError):
            Rule(schema={"type": "seq", "unique": True})

        # this tests map/dict but with no elements
        with pytest.raises(RuleError):
            Rule(schema={"type": "map", "mapping": {}})

        # This will test that a invalid regex will throw error when parsing rules
        with pytest.raises(RuleError):
            Rule(schema={"type": "map", "matching-rule": "any", "mapping": {"regex;(+": {"type": "seq", "sequence": [{"type": "str"}]}}})

        # Test that pattern keyword is not allowed when using a map
        with self.assertRaisesRegexp(RuleError, ".+map\.pattern.+"):
            Rule(schema={"type": "map", "pattern": "^[a-z]+$", "allowempty": True, "mapping": {"name": {"type": "str"}}})

        # Test that when only having a schema; rule it should throw error
        with pytest.raises(RuleError):
            Rule(schema={"schema;fooone": {"type": "map", "mapping": {"foo": {"type": "str"}}}})

        # Test that when using both schema; and include tag that it throw an error because schema; tags should be parsed via Core()
        with pytest.raises(RuleError):
            Rule(schema={"schema;str": {"type": "map", "mapping": {"foo": {"type": "str"}}}, "type": "map", "mapping": {"foo": {"include": "str"}}})

        # Test that exception is raised when a invalid matching rule is used
        with pytest.raises(RuleError) as ex:
            Rule(schema={"type": "map", "matching-rule": "foobar", "mapping": {"regex;.+": {"type": "seq", "sequence": [{"type": "str"}]}}})
        assert ex.value.msg.startswith("Specefied rule in key : foobar is not part of allowed rule set")

        # Test that providing an unknown key raises exception
        with pytest.raises(RuleError) as ex:
            Rule(schema={"type": "str", "foobar": True})
        assert ex.value.msg.startswith("Unknown key: foobar found")

        # Test that type key must be string otherwise exception is raised
        with pytest.raises(RuleError) as ex:
            Rule(schema={"type": 1})
        assert ex.value.msg.startswith("key 'type' in schema rule is not a string type")

        # Test that required value must be bool otherwise exception is raised
        with pytest.raises(RuleError) as ex:
            Rule(schema={"type": "str", "required": "foobar"})
        assert ex.value.msg.startswith("required.notbool : foobar")

        # Test that pattern value must be string otherwise exception is raised
        with pytest.raises(RuleError) as ex:
            Rule(schema={"type": "str", "pattern": 1})
        assert ex.value.msg.startswith("pattern.notstr : 1 :")

        with pytest.raises(RuleError) as ex:
            Rule(schema={"type": "str", "enum": True})
        assert ex.value.msg.startswith("enum.notseq")

        # Test that 'map' and 'mapping' can't be at the same level
        with pytest.raises(RuleError) as ex:
            Rule(schema={"map": {"stream": {"type": "any"}}, "mapping": {"seams": {"type": "any"}}})
        assert ex.value.msg.startswith("mapping.multiple-use")

    def test_matching_rule(self):
        pass

    def test_allow_empty_map(self):
        pass

    def test_type_value(self):
        pass

    def test_name_value(self):
        pass

    def test_desc_value(self):
        pass

    def test_required_value(self):
        pass

    def test_pattern_value(self):
        pass

    def test_enum_value(self):
        pass

    def test_assert_value(self):
        pass

    def test_range_value(self):
        pass

    def test_ident_value(self):
        pass

    def test_unique_value(self):
        pass

    def test_sequence(self):
        # Test basic sequence rule
        r = Rule(schema={"type": "seq", "sequence": [{"type": "str"}]})
        assert r._type == "seq"
        assert isinstance(r._sequence, list)
        assert isinstance(r._sequence[0], Rule)
        assert r._sequence[0]._type == "str"

        # Test sequence without explicit type
        r = Rule(schema={"sequence": [{"type": "str"}]})
        assert r._type == "seq"
        assert isinstance(r._sequence, list)
        assert isinstance(r._sequence[0], Rule)
        assert r._sequence[0]._type == "str"

        # Test short name 'seq'
        r = Rule(schema={"seq": [{"type": "str"}]})
        assert r._type == "seq"
        assert isinstance(r._sequence, list)
        assert isinstance(r._sequence[0], Rule)
        assert r._sequence[0]._type == "str"

        # Test error is raised when sequence key is missing
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "seq"})
        assert ex.value.msg.startswith("seq.nosequence"), "Wrong exception was raised"

        # sequence and pattern can't be used at same time
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "seq", "sequence": [{"type": "str"}], "pattern": "..."})
        assert ex.value.msg.startswith("seq.conflict :: pattern"), "Wrong exception was raised"

    def test_build_sequence_multiple_values(self):
        """
        Test with multiple values.
        """
        # Test basic sequence rule
        r = Rule(schema={'type': 'seq', 'sequence': [{'type': 'str'}, {'type': 'int'}]})
        assert r._type == "seq"
        assert r._matching == "any"
        assert len(r._sequence) == 2
        assert isinstance(r._sequence, list)
        assert all([isinstance(r._sequence[i], Rule) for i in range(len(r._sequence))])
        assert r._sequence[0]._type == "str"
        assert r._sequence[1]._type == "int"

        # Test sequence without explicit type
        r = Rule(schema={'sequence': [{'type': 'str'}, {'type': 'int'}]})
        assert r._type == "seq"
        assert r._matching == "any"
        assert len(r._sequence) == 2
        assert isinstance(r._sequence, list)
        assert all([isinstance(r._sequence[i], Rule) for i in range(len(r._sequence))])
        assert r._sequence[0]._type == "str"
        assert r._sequence[1]._type == "int"

        # Test adding matchin rules

    def test_mapping(self):
        # This tests mapping with a nested type and pattern
        r = Rule(schema={"type": "map", "mapping": {"name": {"type": "str", "pattern": ".+@.+"}}})
        assert r._type == "map", "rule type is not map"
        assert isinstance(r._mapping, dict), "mapping is not dict"
        assert r._mapping["name"]._type == "str", "nested mapping is not of string type"
        assert r._mapping["name"]._pattern is not None, "nested mapping has no pattern var set"
        assert r._mapping["name"]._pattern == ".+@.+", "pattern is not set to correct value"

        # when type is specefied, 'mapping' key must be present
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "map"})
        assert ex.value.msg.startswith("map.nomapping"), "Wrong exception was raised"

        # 'map' and 'enum' can't be used at same time
        # TODO: This do not work because it currently raises RuleError: <RuleError: error code 4: enum.notscalar>
        # with pytest.raises(SchemaConflict):
        #     r = Rule(schema={"type": "map", "enum": [1, 2, 3]})

    def test_default_value(self):
        pass

    def test_check_conflicts(self):
        # TODO: This do not work and enum schema conflict is not raised... RuleError: <RuleError: error code 4: enum.notscalar>
        # with pytest.raises(SchemaConflict) as ex:
        #     r = Rule(schema={"type": "seq", "sequence": [{"type": "str"}], "enum": [1, 2, 3]})
        # assert ex.value.msg.startswith("seq.conflict :: enum"), "Wrong exception was raised"

        # Test sequence and mapping can't be used at same level
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "seq", "sequence": [{"type": "str"}], "mapping": {"name": {"type": "str", "pattern": ".+@.+"}}})
        assert ex.value.msg.startswith("seq.conflict :: mapping"), "Wrong exception was raised"

        # Mapping and sequence can't used at same time
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "map", "mapping": {"foo": {"type": "str"}}, "sequence": [{"type": "str"}]})
        assert ex.value.msg.startswith("map.conflict :: mapping"), "Wrong exception was raised"

        # scalar type and sequence can't be used at same time
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "int", "sequence": [{"type": "str"}]})
        assert ex.value.msg.startswith("scalar.conflict :: sequence"), "Wrong exception was raised"

        # scalar type and mapping can't be used at same time
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "int", "mapping": {"foo": {"type": "str"}}})
        assert ex.value.msg.startswith("scalar.conflict :: mapping"), "Wrong exception was raised"

        # scalar type and enum can't be used at same time
        with pytest.raises(SchemaConflict) as ex:
            Rule(schema={"type": "int", "enum": [1, 2, 3], "range": {"max": 10, "min": 1}})
        assert ex.value.msg.startswith("enum.conflict :: range"), "Wrong exception was raised"
