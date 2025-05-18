import unittest


"""
This module tests the interface to paredros. It especially tests, whether the
ParseInformation class is adequate and exposed.
"""
class InterfaceTest(unittest.TestCase):
    def test_simpleton_grammar(self):
        """
        This method tests the Simpleton grammar with a valid input.
        It checks whether all node types, rule names and token consumptions are correct.
        """
        from paredros_debugger.ParseInformation import ParseInformation
        p = ParseInformation(grammar_file_path="../Simpleton/Simpleton_Reg.g4")
        p.generate_parser()
        p.parse(raw_input_content="123")
        root = p.get_current_tree_dict()

        # the parse tree should be a dict
        self.assertEqual(type(root), dict)

        # pass through the tree and check that all ids are unique
        ids = {}
        def check_ids(node):
            # all nodes have to have different ids
            if node["id"] in ids:
                self.fail("[SIMPLETON] All nodes should have different ids")
            ids[node["id"]] = True
            for child in node["children"]:
                check_ids(child)

        # ---------- ROOT ----------
        # the root node should be startRule and be of type rule
        self.assertEqual(root["node_type"], "rule", "[SIMPLETON] Root node should be of type rule")
        self.assertEqual(root["rule_name"], "startRule", "[SIMPLETON] Root node should be startRule")
        self.assertEqual(root["token"], None, "[SIMPLETON] 'startRule' should not have a token")
        # only one child
        self.assertEqual(len(root["children"]), 1)

        # ---------- FIRST CHILD ----------
        rule_zwoelf = root["children"][0]
        # all nodes have to have different ids
        self.assertNotEquals(root["id"], rule_zwoelf["id"])

        # misleadingly, the rule "zwoelf" matches the string "123"
        self.assertEqual(rule_zwoelf["rule_name"], "zwoelf", "[SIMPLETON] First child should be rule 'zwoelf'")
        self.assertEqual(rule_zwoelf["node_type"], "rule", "[SIMPLETON] First child should be of type rule")
        self.assertEqual(rule_zwoelf["token"], None,  "[SIMPLETON] Rule 'zwoelf' should not have a token")

        # 'zwoelf' can be superseded by:
        # zwoelf -> EINS X,
        # X -> X ZWEI | ZWEI,
        # X -> X DREI | DREI

        # ---------- FIRST LEXEME ----------
        # the first lexeme should be "EINS"
        eins = rule_zwoelf["children"][0]
        # all nodes have to have different ids
        self.assertNotEquals(rule_zwoelf["id"], eins["id"])
        self.assertEqual(eins["node_type"], "lexeme", "[SIMPLETON] First child should be of type lexeme")
        self.assertEqual(eins["rule_name"], "EINS", "[SIMPLETON] First child should be lexeme 'EINS'")
        self.assertEqual(eins["token"], "1", "[SIMPLETON] Lexeme 'EINS' should have a token")

        # ---------- SECOND LEXEME ----------
        # the second lexeme should be "ZWEI"
        zwei = rule_zwoelf["children"][1]
        # all nodes have to have different ids
        self.assertNotEquals(rule_zwoelf["id"], zwei["id"])
        self.assertNotEquals(eins["id"], zwei["id"])


if __name__ == '__main__':
    unittest.main()
