import unittest

from nlp import classify_intent, make_reply


class IntentClassificationTests(unittest.TestCase):
    def test_detects_intents_in_all_supported_languages(self) -> None:
        examples = [
            ("I'm not feeling well today", "en", "unwell"),
            ("I feel happy today", "en", "positive"),
            ("I am feeling worried", "en", "low_mood"),
            ("आज मेरी तबीयत ठीक नहीं है", "hi", "unwell"),
            ("आज मैं अच्छा महसूस कर रहा हूँ", "hi", "positive"),
            ("आज मैं चिंतित हूँ", "hi", "low_mood"),
            ("आज मला बरं वाटत नाही", "mr", "unwell"),
            ("आज मला छान वाटत आहे", "mr", "positive"),
            ("आज मला काळजी वाटते", "mr", "low_mood"),
        ]

        for text, language, expected_intent in examples:
            with self.subTest(language=language, text=text):
                self.assertEqual(classify_intent(text, language), expected_intent)

    def test_unknown_text_uses_general_reply_in_selected_language(self) -> None:
        intent, reply = make_reply("We went for a walk.", "en")

        self.assertEqual(intent, "general")
        self.assertIn("I'm here to listen", reply)

        marathi_intent, marathi_reply = make_reply("आज पाऊस पडतो.", "mr")
        self.assertEqual(marathi_intent, "general")
        self.assertIn("मी ऐकण्यासाठी इथे आहे", marathi_reply)


if __name__ == "__main__":
    unittest.main()
