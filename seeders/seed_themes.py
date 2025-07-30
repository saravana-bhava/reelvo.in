# File: seeders/seed_themes.py

import os
import sys

# Adjust path for importing models and db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.theme import Theme
from models import db
from app import create_app

themes = [
    ("motivation", "en", "Don’t wait for the perfect moment. Start now. Even small steps matter. You’re not weak — you’re growing. Keep going. Greatness is built one rep at a time. No one starts perfect — they just start. Every legend once stood where you’re standing now. It’s your time."),
    ("motivation", "hi", "सही समय का इंतज़ार मत करो — अभी शुरू करो। हर छोटा कदम मायने रखता है। तुम कमज़ोर नहीं, बस बढ़ रहे हो। जारी रखो — यही सफलता का रास्ता है। कोई भी परफेक्ट नहीं शुरू करता — वो बस शुरू करता है। हर महान कहानी यहीं से शुरू होती है — अब तुम्हारी बारी है।"),
    ("success", "en", "Success doesn’t come overnight. It’s built on failure, grit, and relentless effort. Don’t chase money — chase excellence. The results will follow. Keep your focus, trust the process, and outwork yesterday. Even on tough days, progress is progress."),
    ("success", "hi", "सफलता एक दिन में नहीं मिलती। ये मेहनत, धैर्य और जुनून से बनती है। पैसे के पीछे मत भागो — कमाल करो, पैसा खुद आएगा। प्रक्रिया पर भरोसा रखो और हर दिन थोड़ा बेहतर बनो। मुश्किल दिनों में भी आगे बढ़ना ही जीत है।"),
    ("inspiration", "en", "Every great story begins with a dream. You don’t need permission to shine. Your journey is yours — embrace it. Light your own fire. And remember: stars shine brightest in the dark. So when it’s tough — that’s when you rise."),
    ("inspiration", "hi", "हर बड़ी कहानी एक सपने से शुरू होती है। चमकने के लिए किसी की इजाज़त मत लो। ये सफ़र तुम्हारा है — इसे अपनाओ। अपनी चिंगारी खुद बनो। और याद रखो — अंधेरे में ही सितारे सबसे तेज़ चमकते हैं। मुश्किल वक्त ही तुम्हारी असली पहचान बनाता है।"),
    ("life", "en", "Life isn’t a race. Breathe. Be present. The most beautiful moments are often quiet and simple. Don’t miss them chasing noise. Slow down and feel — joy lives in the now, not someday. Make time for what matters."),
    ("life", "hi", "ज़िंदगी कोई दौड़ नहीं है। सांस लो, अभी में जियो। सबसे खूबसूरत पल अक्सर सादे होते हैं — उन्हें मत खोना, भागदौड़ में। रुककर महसूस करो — सच्ची खुशी ’अभी’ में छुपी होती है, किसी भविष्य में नहीं। जो ज़रूरी है, उसके लिए वक़्त निकालो।"),
    ("confidence", "en", "Real confidence doesn’t shout. It shows. You don’t need to prove yourself to anyone. Walk your path. Your energy speaks louder than words. Trust your steps — the world adjusts when you do."),
    ("confidence", "hi", "सच्चा आत्मविश्वास चिल्लाता नहीं — दिखता है। किसी को कुछ साबित करने की ज़रूरत नहीं। अपना रास्ता चुनो — तुम्हारी ऊर्जा खुद बोलेगी। अपने फैसलों पर भरोसा रखो — जब तुम बदलते हो, दुनिया अपने आप रास्ता देती है।"),
    ("discipline", "en", "Motivation fades. But discipline? That’s your armor. Show up daily — even when it’s boring, even when it’s hard. That’s how champions are made. Greatness isn’t loud — it’s consistent."),
    ("discipline", "hi", "मोटिवेशन खत्म हो सकता है — लेकिन अनुशासन हमेशा साथ देता है। हर दिन डटे रहो — चाहे मन करे या नहीं। यहीं से चैंपियंस बनते हैं। महानता शोर नहीं मचाती — वो आदत बन जाती है।"),
    ("gratitude", "en", "Gratitude is a superpower. It grounds you. Reminds you of what you have, not what’s missing. Want to be happier? Start saying thank you more. Count blessings, not burdens — that’s real abundance."),
    ("gratitude", "hi", "कृतज्ञता ताकत देती है। ये तुम्हें जोड़ती है — जो है, उसे देखने की आदत डालती है। ज़्यादा खुश रहना है? रोज़ शुक्रिया कहना शुरू करो। कमियों पर नहीं — जो मिला है उस पर ध्यान दो। यही असली संपन्नता है।"),
    ("fear", "en", "Fear will always whisper — ’you can’t.’ But you’re stronger than your doubt. Take the step anyway. Your courage is louder than fear. Every bold action weakens fear’s grip. Keep moving forward."),
    ("fear", "hi", "डर हमेशा कहेगा — ’तू नहीं कर सकता।’ पर तुम उससे ज़्यादा ताकतवर हो। एक कदम बढ़ाओ — साहस की आवाज़ डर से ऊँची होती है। हर हिम्मती कदम डर की पकड़ को कमजोर करता है। चलते रहो।"),
    ("cosmetics", "en", "Does your skin feel tired and lifeless? It’s time to try something new! Introducing GlowMist — a hydrating facial spray that gives instant freshness and a natural glow. Infused with rose water, hyaluronic acid, and 100% cruelty-free. Just one spray… and your skin says WOW! ✨ Want glowing skin 24/7? This is your sign. Order now — link in bio!"),
    ("cosmetics", "hi", "क्या आपकी त्वचा थकी हुई और बेजान लगती है? अब वक्त है कुछ नया ट्राय करने का! पेश है GlowMist — एक हाइड्रेटिंग फेस स्प्रे जो देता है इंस्टेंट ताज़गी और नेचुरल ग्लो। गुलाब जल, हायालुरोनिक एसिड और 100% क्रूएल्टी-फ्री फॉर्मूला। बस एक स्प्रे… और आपकी त्वचा बोले – वॉव! ✨ 24x7 ग्लो चाहिए? तो बस ये इस्तेमाल करें — ऑर्डर करें अभी, लिंक बायो में है!"),
]

def seed_themes():
    """Seed default themes into the database if not already present."""
    app = create_app()
    with app.app_context():
        count_new = 0
        for name, lang, content in themes:
            if not Theme.query.filter_by(name=name, lang=lang).first():
                db.session.add(Theme(name=name, lang=lang, content=content))
                count_new += 1
        db.session.commit()
        if count_new:
            print(f"✅ Seeded {count_new} new themes.")
        else:
            print("⚠️ No new themes added — already up to date.")

if __name__ == "__main__":
    seed_themes()
