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
        p.parse(input_file_path="../Simpleton/input.txt")
        root = p.get_current_tree_dict()

        # the parse tree should be a dict
        self.assertEqual(type(root), dict)

        # ---------- ROOT ----------
        # the root node should be startRule and be of type rule
        self.assertEqual(root["node_type"], "rule")
        self.assertEqual(root["rule_name"], "startRule")
        self.assertEqual(root["token"], None)
        # only one child
        self.assertEqual(len(root["children"]), 1)

        # ---------- FIRST CHILD ----------
        first_and_only_child = root["children"][0]
        # all nodes have to have different ids
        self.assertNotEquals(root["id"], first_and_only_child["id"])

        # misleadingly, the rule "zwoelf" matches the string "123"
        self.assertEqual(first_and_only_child["rule_name"], "zwoelf")
        self.assertEqual(first_and_only_child["node_type"], "rule")
        self.assertEqual(first_and_only_child["token"], None)



if __name__ == '__main__':
    unittest.main()
