# -*- coding: utf-8 -*-

""" pyKwalify - Rule.py """

__author__ = 'Grokzen <grokzen@gmail.com>'

# python std lib
import os
import re

# python std logging
import logging
Log = logging.getLogger(__name__)

# pyKwalify imports
from pykwalify.types import DEFAULT_TYPE, typeClass, isBuiltinType, isCollectionType
from pykwalify.errors import SchemaConflict, RuleError


class Rule(object):
    """ Rule class that handles a rule constraint """

    def __init__(self, schema=None, parent=None):
        self._parent = None
        self._name = None
        self._desc = None
        self._required = False
        self._type = None
        self._type_class = None
        self._pattern = None
        self._pattern_regexp = None
        self._enum = None
        self._sequence = None
        self._mapping = None
        self._assert = None
        self._range = None
        self._length = None
        self._ident = None
        self._unique = None
        self._default = None
        self._allowempty_map = None
        self._matching_rule = None
        self._map_regex_rule = None
        self._regex_mappings = None

        self._parent = parent
        self._schema = schema
        self._schema_str = schema

        if isinstance(schema, dict):
            self.init(schema, "")

    def __str__(self):
        return "Rule: {}".format(str(self._schema_str))

    def init(self, schema, path):
        Log.debug("Init schema: {}".format(schema))

        if schema is not None:
            # assert isinstance(schema, dict), "schema is not a dict : {}".format(path)

            if "type" not in schema:
                raise RuleError("key 'type' not found in schema rule : {}".format(path))
            else:
                if not isinstance(schema["type"], str):
                    raise RuleError("key 'type' in schema rule is not a string type : {}".format(path))

                self._type = schema["type"]

        rule = self

        self._schema_str = schema

        t = schema["type"]
        self.initTypeValue(t, rule, path)

        func_mapping = {
            "type": lambda x, y, z: (),
            "name": self.initNameValue,
            "desc": self.initDescValue,
            "required": self.initRequiredValue,
            "pattern": self.initPatternValue,
            "enum": self.initEnumValue,
            "assert": self.initAssertValue,
            "range": self.initRangeValue,
            "length": self.initLengthValue,
            "ident": self.initIdentValue,
            "unique": self.initUniqueValue,
            "allowempty": self.initAllowEmptyMap,
            "default": self.initDefaultValue,
            "sequence": self.initSequenceValue,
            "mapping": self.initMappingValue,
            "matching-rule": self.initMatchingRule,
        }

        for k, v in schema.items():
            if k in func_mapping:
                func_mapping[k](v, rule, path)
            else:
                raise RuleError("Unknown key: {} found : {}".format(k, path))

        self.checkConfliction(schema, rule, path)

    def initMatchingRule(self, v, rule, path):
        Log.debug("Init matching-rule: {}".format(path))
        Log.debug("{} {}".format(v, rule))

        # Verify that the provided rule is part of one of the allowed one
        allowed = ["any"]
        # ["none", "one", "all"] Is currently awaiting proper implementation
        if v not in allowed:
            raise RuleError("Specefied rule in key : {} is not part of allowed rule set : {}".format(v, allowed))
        else:
            self._matching_rule = v

    def initAllowEmptyMap(self, v, rule, path):
        Log.debug("Init allow empty value: {}".format(path))
        Log.debug("Type: {} : {}".format(v, rule))

        self._allowempty_map = v

    def initTypeValue(self, v, rule, path):
        Log.debug("Init type value : {}".format(path))
        Log.debug("Type: {} {}".format(v, rule))

        if v is None:
            v = DEFAULT_TYPE

        if not isinstance(v, str):
            raise RuleError("type.nostr : {} : {}".format(v, path))

        self._type = v
        self._type_class = typeClass(v)

        if not isBuiltinType(self._type):
            raise RuleError("type.unknown : {} : {}".format(self._type, path))

    def initNameValue(self, v, rule, path):
        Log.debug("Init name value : {}".format(path))

        self._name = str(v)

    def initDescValue(self, v, rule, path):
        Log.debug("Init descr value : {}".format(path))

        self._desc = str(v)

    def initRequiredValue(self, v, rule, path):
        Log.debug("Init required value : {}".format(path))

        if not isinstance(v, bool):
            raise RuleError("required.notbool : {} : {}".format(v, path))
        self._required = v

    def initPatternValue(self, v, rule, path):
        Log.debug("Init pattern value : {}".format(path))

        if not isinstance(v, str):
            raise RuleError("pattern.notstr : {} : {}".format(v, path))

        self._pattern = v

        if self._schema_str["type"] == "map":
            raise RuleError("map.pattern : pattern not allowed inside map : {} : {}".format(v, path))

        # TODO: Some form of validation of the regexp? it exists in the source

        try:
            self._pattern_regexp = re.compile(self._pattern)
        except Exception:
            raise RuleError("pattern.syntaxerr : {} --> {} : {}".format(self._pattern_regexp, self._pattern_regexp, path))

    def initEnumValue(self, v, rule, path):
        Log.debug("Init enum value : {}".format(path))

        if not isinstance(v, list):
            raise RuleError("enum.notseq")
        self._enum = v

        if isCollectionType(self._type):
            raise RuleError("enum.notscalar")

        lookup = set()
        for item in v:
            if not isinstance(item, self._type_class):
                raise RuleError("enum.type.unmatch : {} --> {} : {}".format(item, self._type_class, path))

            if item in lookup:
                raise RuleError("enum.duplicate : {} : {}".format(item, path))

            lookup.add(item)

    def initAssertValue(self, v, rule, path):
        Log.debug("Init assert value : {}".format(path))

        if not isinstance(v, str):
            raise RuleError("assert.notstr : {}".format(path))

        self._assert = v

        raise RuleError("assert.NYI-Error : {}".format(path))

    def initRangeValue(self, v, rule, path):
        Log.debug("Init range value : {}".format(path))

        if not isinstance(v, dict):
            raise RuleError("range.notmap : {} : {}".format(v, path))
        if isCollectionType(self._type) or self._type == "bool":
            raise RuleError("range.notscalar : {} : {}".format(self._type, path))

        self._range = v  # dict that should contain min, max, min-ex, max-ex keys

        # This should validate that only min, max, min-ex, max-ex exists in the dict
        for k, v in self._range.items():
            if k == "max" or k == "min" or k == "max-ex" or k == "min-ex":
                if not isinstance(v, self._type_class):
                    raise RuleError("range.type.unmatch : {} --> {} : {}".format(v, self._type_class, path))
            else:
                raise RuleError("range.undefined key : {} : {}".format(k, path))

        if "max" in self._range and "max-ex" in self._range:
            raise RuleError("range.twomax : {}".format(path))
        if "min" in self._range and "min-ex" in self._range:
            raise RuleError("range.twomin : {}".format(path))

        max = self._range.get("max", None)
        min = self._range.get("min", None)
        max_ex = self._range.get("max-ex", None)
        min_ex = self._range.get("min-ex", None)

        if max is not None:
            if min is not None and max < min:
                raise RuleError("range.maxltmin : {} < {} : {}".format(max, min, path))
            elif min_ex is not None and max <= min_ex:
                raise RuleError("range.maxleminex : {} <= {} : {}".format(max, min_ex, path))
        elif max_ex is not None:
            if min is not None and max_ex < min:
                raise RuleError("range.maxexlemiin : {} < {} : {}".format(max_ex, min, path))
            elif min_ex is not None and max_ex <= min_ex:
                raise RuleError("range.maxexleminex : {} <= {} : {}".format(max_ex, min_ex, path))

    def initLengthValue(self, v, rule, path):
        Log.debug("Init length value : {}".format(path))

        if not isinstance(v, dict):
            raise RuleError("length.notmap : {} : {}".format(v, path))

        self._length = v

        if not (self._type == "str" or self._type == "text"):
            raise RuleError("length.nottext : {} : {}".format(self._type, path))

        # This should validate that only min, max, min-ex, max-ex exists in the dict
        for k, v in self._length.items():
            if k == "max" or k == "min" or k == "max-ex" or k == "min-ex":
                if not isinstance(v, int):
                    raise RuleError("length.notint : {} : {}".format(v, path))
            else:
                raise RuleError("length.undefined key : {} : {}".format(k, path))

        if "max" in self._length and "max-ex" in self._length:
            raise RuleError("length.twomax : {}".format(path))
        if "min" in self._length and "min-ex" in self._length:
            raise RuleError("length.twomin : {}".format(path))

        max = self._length.get("max", None)
        min = self._length.get("min", None)
        max_ex = self._length.get("max-ex", None)
        min_ex = self._length.get("min-ex", None)

        if max is not None:
            if min is not None and max < min:
                raise RuleError("length.maxltmin: {} < {} : {}".format(max, min, path))
            elif min_ex is not None and max <= min_ex:
                raise RuleError("length.maxleminex : {} <= {} : {}".format(max, min_ex, path))
        elif max_ex is not None:
            if min is not None and max_ex < min:
                raise RuleError("length.maxexlemiin : {} < {} : {}".format(max_ex, min, path))
            elif min_ex is not None and max_ex <= min_ex:
                raise RuleError("length.maxexleminex : {} <= {} : {}".format(max_ex, min_ex, path))

    def initIdentValue(self, v, rule, path):
        Log.debug("Init ident value : {}".format(path))

        if v is None or isinstance(v, bool):
            raise RuleError("ident.notbool : {} : {}".format(v, path))

        self._ident = bool(v)
        self._required = True

        if isCollectionType(self._type):
            raise RuleError("ident.notscalar : {} : {}".format(self._type, path))
        if path == "":
            raise RuleError("ident.onroot")
        if self._parent is None or not self._parent._type == "map":
            raise RuleError("ident.notmap : {}".format(path))

    def initUniqueValue(self, v, rule, path):
        Log.debug("Init unique value : {}".format(path))

        if not isinstance(v, bool):
            raise RuleError("unique.notbool : {} : {}".format(v, path))

        self._unique = v

        if isCollectionType(self._type):
            raise RuleError("unique.notscalar : {} : {}".format(self._type, path))
        if path == "":
            raise RuleError("unique.onroot")

    def initSequenceValue(self, v, rule, path):
        Log.debug("Init sequence value : {}".format(path))

        if v is not None and not isinstance(v, list):
            raise RuleError("sequence.notseq : {} : {}".format(v, path))

        self._sequence = v

        if self._sequence is None or len(self._sequence) == 0:
            raise RuleError("sequence.noelem : {} : {}".format(self._sequence, path))
        if len(self._sequence) > 1:
            raise RuleError("sequence.toomany : {} : {}".format(self._sequence, path))

        elem = self._sequence[0]
        if elem is None:
            elem = {}

        i = 0

        rule = Rule(None, self)
        rule.init(elem, "{}/sequence/{}".format(path, i))

        self._sequence = []
        self._sequence.append(rule)
        return rule

    def initMappingValue(self, v, rule, path):
        Log.debug("Init mapping value : {}".format(path))

        if v is not None and not isinstance(v, dict):
            raise RuleError("mapping.notmap : {} : {}".format(v, path))

        if v is None or len(v) == 0:
            raise RuleError("mapping.noelem : {} : {}".format(v, path))

        self._mapping = {}
        self._regex_mappings = []

        for k, v in v.items():
            if v is None:
                v = {}

            # Check if this is a regex rule. Handle specially
            if k.startswith("regex;"):
                Log.debug("Found regex map rule")
                regex = k.split(";", 1)
                if len(regex) != 2:
                    raise RuleError("Malformed regex key : {}".format(k))
                else:
                    regex = regex[1]
                    try:
                        re.compile(regex)
                    except Exception as e:
                        raise RuleError("Unable to compile regex '{}' '{}'".format(regex, e))

                    regex_rule = Rule(None, self)
                    regex_rule.init(v, "{}/mapping;regex/{}".format(path, regex[1:-1]))
                    regex_rule._map_regex_rule = regex[1:-1]
                    self._regex_mappings.append(regex_rule)
                    self._mapping[k] = regex_rule
            else:
                rule = Rule(None, self)
                rule.init(v, "{}/mapping/{}".format(path, k))
                self._mapping[k] = rule

        return rule

    def initDefaultValue(self, v, rule, path):
        Log.debug("Init default value : {}".format(path))
        self._default = v

        if isCollectionType(self._type):
            raise RuleError("default.notscalar : {} : {} : {}".format(rule, path, v))

        if self._type == "map" or self._type == "seq":
            raise RuleError("default.notscalar : {} : {} : {}".format(rule, os.path.dirname(path), v))

        if not isinstance(v, self._type_class):
            raise RuleError("default.type.unmatch : {} --> {} : {}".format(v, self._type_class, path))

    def checkConfliction(self, schema, rule, path):
        Log.debug("Checking for conflicts : {}".format(path))

        if self._type == "seq":
            if "sequence" not in schema:
                raise SchemaConflict("seq.nosequence")
            if self._enum is not None:
                raise SchemaConflict("seq.conflict :: enum: {}".format(path))
            if self._pattern is not None:
                raise SchemaConflict("seq.conflict :: pattern: {}".format(path))
            if self._mapping is not None:
                raise SchemaConflict("seq.conflict :: mapping: {}".format(path))
            if self._range is not None:
                raise SchemaConflict("seq.conflict :: range: {}".format(path))
            if self._length is not None:
                raise SchemaConflict("seq.conflict :: length: {}".format(path))
        elif self._type == "map":
            if "mapping" not in schema and not self._allowempty_map:
                raise SchemaConflict("map.nomapping")
            if self._enum is not None:
                raise SchemaConflict("map.conflict :: enum:")
            if self._sequence is not None:
                raise SchemaConflict("map.conflict :: mapping: {}".format(path))
            if self._range is not None:
                raise SchemaConflict("map.conflict :: range: {}".format(path))
            if self._length is not None:
                raise SchemaConflict("map.conflict :: length: {}".format(path))
        else:
            if self._sequence is not None:
                raise SchemaConflict("scalar.conflict :: sequence: {}".format(path))
            if self._mapping is not None:
                raise SchemaConflict("scalar.conflict :: mapping: {}".format(path))
            if self._enum is not None:
                if self._range is not None:
                    raise SchemaConflict("enum.conflict :: range: {}".format(path))
                if self._length is not None:
                    raise SchemaConflict("enum.conflict :: length: {}".format(path))
                if self._pattern is not None:
                    raise SchemaConflict("enum.conflict :: length: {}".format(path))
