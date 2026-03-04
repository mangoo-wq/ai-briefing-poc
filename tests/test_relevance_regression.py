import unittest

from src.main import _is_relevant_title


class RelevanceRegressionTests(unittest.TestCase):
    def test_repairability_false_positive_is_blocked(self):
        title = "Lenovo's New ThinkPads Score 10/10 for Repairability"
        self.assertFalse(_is_relevant_title(title))

    def test_clickbait_stock_phrase_is_blocked(self):
        title = "This AI Stock Is Up 11% in Just 1 Week. Time to Buy?"
        self.assertFalse(_is_relevant_title(title))

    def test_core_ai_title_is_kept(self):
        title = "Gemini 3.1 Flash-Lite: Built for intelligence at scale"
        self.assertTrue(_is_relevant_title(title))

    def test_machine_learning_phrase_is_kept(self):
        title = "Machine learning operations at enterprise scale"
        self.assertTrue(_is_relevant_title(title))


if __name__ == '__main__':
    unittest.main()
