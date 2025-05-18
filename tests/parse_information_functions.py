import unittest

"""
This module tests the interface to paredros. It especially tests, whether the
ParseInformation class is adequate and exposed.
"""
class InterfaceTest(unittest.TestCase):

    def check_ids(self, node):
        ids = {}
        def _check(n):
            # all nodes have to have different ids
            if n["id"] in ids:
                self.fail("[SIMPLETON] All nodes should have different ids")
            ids[n["id"]] = True
            for child in n["children"]:
                _check(child)
        _check(node)

    def check_lexeme(self, node:dict, token:str):
        self.assertEqual("token", node["node_type"], f"[SIMPLETON] {node['id']} should be of type lexeme")
        self.assertEqual(None, node["rule_name"],
                         f"[SIMPLETON] {node['id']} should be a lexer rule and not have a rule name")
        self.assertEqual(token, node["token"], f"[SIMPLETON] Lexeme {node['id']} should have a token")

    def check_rule(self, node:dict, rule_name:str):
        self.assertEqual("rule", node["node_type"], f"[SIMPLETON] {node['id']} should be of type rule")
        self.assertEqual(rule_name, node["rule_name"], f"[SIMPLETON] {node['id']} should be {rule_name}")
        self.assertEqual(None, node["token"], f"[SIMPLETON] {node['rule_name']} should not have a token")

    def test_simpleton_grammar_with_valid_input(self):
        """
        This method tests the Simpleton grammar with a valid input.
        It checks whether all node types, rule names and token consumptions are correct.
        """
        from paredros_debugger.ParseInformation import ParseInformation
        p = ParseInformation(grammar_file_path="../Simpleton/Simpleton_Reg.g4")
        p.generate_parser()
        p.parse(raw_input_content="123")
        root = p.get_current_tree_dict(verbose=True)

        # the parse tree should be a dict
        self.assertEqual(dict, type(root))

        # pass through the tree and check that all ids are unique
        self.check_ids(root)

        # ---------- ROOT ----------
        # the root node should be startRule and be of type rule
        self.check_rule(root, "startRule")
        # only one child
        self.assertEqual(1, len(root["children"]))

        # ---------- FIRST CHILD ----------
        rule_zwoelf = root["children"][0]
        # misleadingly, the rule "zwoelf" can be substituted to match the string "123"
        self.check_rule(root, "startRule")

        # 'zwoelf' can be superseded by:
        # zwoelf -> EINS X,
        # X -> X ZWEI | ZWEI,
        # X -> X DREI | DREI

        # For the input '123' there should now be three children of zwoelf:
        self.assertEqual(3, len(rule_zwoelf["children"]), "[SIMPLETON] Rule 'zwoelf' should have three children")


        # ---------- FIRST LEXEME ----------
        # the first lexeme should be "EINS"
        eins = rule_zwoelf["children"][0]
        self.check_lexeme(eins, "EINS ('1')")

        # ---------- SECOND LEXEME ----------
        # the second lexeme should be "ZWEI"
        zwei = rule_zwoelf["children"][1]
        self.check_lexeme(zwei, "ZWEI ('2')")

        # ---------- THIRD LEXEME ----------
        # the third lexeme should be "DREI"
        drei = rule_zwoelf["children"][2]
        self.check_lexeme(drei, "DREI ('3')")

    def test_simpleton_grammar_with_invalid_input(self):
        """
        This method tests the Simpleton grammar with an invalid input.
        It checks whether all node types, rule names and token consumptions are correct.
        """
        from paredros_debugger.ParseInformation import ParseInformation
        p = ParseInformation(grammar_file_path="../Simpleton/Simpleton_Reg.g4")
        p.generate_parser()
        # all invalid characters, which have no lexemes
        p.parse(raw_input_content="44440y0xaosiduouinmc")
        root = p.get_current_tree_dict(verbose=True)
        self.check_rule(root, "startRule")
        # no children
        self.assertEqual(0, len(root["children"]))

        # TODO add more assertions after discussion with the team

        # the parse tree should be a dict
        self.assertEqual(dict, type(root))

        # pass through the tree and check that all ids are unique
        self.check_ids(root)

if __name__ == '__main__':
    unittest.main()
