"""Small, deterministic multilingual intent matching for check-ins."""

import re
import unicodedata
from typing import Literal


Language = Literal["en", "hi", "mr"]
Intent = Literal["unwell", "positive", "low_mood", "general"]

INTENT_PHRASES: dict[Language, dict[Intent, tuple[str, ...]]] = {
    "en": {
        "unwell": ("not feeling well", "unwell", "sick", "pain", "hurt", "ill"),
        "positive": ("okay", "good", "well", "fine", "great", "happy", "better"),
        "low_mood": ("tired", "sleep", "sad", "low", "worried", "anxious", "stress", "lonely"),
        "general": (),
    },
    "hi": {
        "unwell": ("ठीक नहीं", "अस्वस्थ", "बीमार", "दर्द", "तकलीफ़"),
        "positive": ("ठीक", "अच्छा", "अच्छी", "बढ़िया", "खुश"),
        "low_mood": ("थका", "थकी", "नींद", "उदास", "चिंता", "परेशान", "अकेला"),
        "general": (),
    },
    "mr": {
        "unwell": ("बरे नाही", "वाटत नाही", "ठीक नाही", "अस्वस्थ", "आजारी", "दुखत", "त्रास"),
        "positive": ("ठीक", "छान", "बरं", "बरा", "आनंदी", "चांगलं"),
        "low_mood": ("थकलो", "थकले", "झोप", "उदास", "काळजी", "एकटं", "तणाव"),
        "general": (),
    },
}

REPLIES: dict[Language, dict[Intent, str]] = {
    "en": {
        "unwell": (
            "I'm sorry you're not feeling well. Thank you for letting me know. "
            "We can keep this check-in simple or pause for today. If you are worried "
            "about your health, please contact someone you trust or a healthcare professional."
        ),
        "positive": (
            "Thanks for sharing that with me. What has been one small thing on your "
            "mind today? You can answer, or we can leave it here."
        ),
        "low_mood": (
            "Thank you for telling me. It sounds like today may be a little harder. "
            "Would you like to say a bit more, or would you rather pause here?"
        ),
        "general": (
            "Thank you for sharing that with me. I'm here to listen. Would you like "
            "to tell me a little more, or keep today's check-in short?"
        ),
    },
    "hi": {
        "unwell": (
            "आपकी तबीयत ठीक नहीं है, यह सुनकर दुख हुआ। बताने के लिए धन्यवाद। "
            "हम आज की बातचीत छोटी रख सकते हैं या आज के लिए रुक सकते हैं। "
            "अगर आपको अपनी सेहत की चिंता है, तो किसी भरोसेमंद व्यक्ति या स्वास्थ्यकर्मी से बात करें।"
        ),
        "positive": (
            "यह बताने के लिए धन्यवाद। आज आपके मन में कोई छोटी-सी बात है? "
            "आप बता सकते हैं, या हम यहीं रुक सकते हैं।"
        ),
        "low_mood": (
            "मुझे बताने के लिए धन्यवाद। लगता है आज का दिन थोड़ा मुश्किल हो सकता है। "
            "क्या आप थोड़ा और बताना चाहेंगे, या आज यहीं रुकें?"
        ),
        "general": (
            "यह साझा करने के लिए धन्यवाद। मैं सुनने के लिए यहाँ हूँ। "
            "क्या आप थोड़ा और बताना चाहेंगे, या आज की बातचीत छोटी रखें?"
        ),
    },
    "mr": {
        "unwell": (
            "तुम्हाला बरे वाटत नाही हे ऐकून वाईट वाटले. सांगितल्याबद्दल धन्यवाद. "
            "आजची नोंद थोडक्यात करू शकतो किंवा आज थांबू शकतो. "
            "आरोग्याबद्दल काळजी वाटत असल्यास, विश्वासू व्यक्तीशी किंवा आरोग्यसेवा व्यावसायिकाशी बोला."
        ),
        "positive": (
            "हे सांगितल्याबद्दल धन्यवाद. आज तुमच्या मनात एखादी छोटीशी गोष्ट आहे का? "
            "तुम्ही सांगू शकता किंवा आपण इथेच थांबू शकतो."
        ),
        "low_mood": (
            "मला सांगितल्याबद्दल धन्यवाद. आजचा दिवस थोडा कठीण वाटत असावा. "
            "तुम्हाला आणखी सांगायचे आहे का, की आज इथेच थांबूया?"
        ),
        "general": (
            "हे सांगितल्याबद्दल धन्यवाद. मी ऐकण्यासाठी इथे आहे. "
            "तुम्हाला आणखी सांगायचे आहे का, की आजची नोंद थोडक्यात ठेवूया?"
        ),
    },
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def classify_intent(text: str, language: Language) -> Intent:
    """Match simple phrases for the selected language; this is not clinical NLP."""
    normalized_text = f" {_normalize(text)} "
    phrases = INTENT_PHRASES[language]

    for intent in ("unwell", "low_mood", "positive"):
        if any(f" {_normalize(phrase)} " in normalized_text for phrase in phrases[intent]):
            return intent

    return "general"


def make_reply(text: str, language: Language) -> tuple[Intent, str]:
    intent = classify_intent(text, language)
    return intent, REPLIES[language][intent]
