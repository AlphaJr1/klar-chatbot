from typing import Dict, List

class TextNormalizer:
    def __init__(self):
        self.slang_map = {
            "udh": "sudah",
            "udah": "sudah", 
            "dah": "sudah",
            "blm": "belum",
            "blum": "belum",
            "gk": "gak",
            "ga": "gak",
            "ngga": "nggak",
            "tdk": "tidak",
            "bnr": "benar",
            "bgt": "banget",
            "bener": "benar",
            "gmn": "gimana",
            "gmna": "gimana",
            "bgmn": "bagaimana",
            "bgaimana": "bagaimana",
            "knp": "kenapa",
            "knapa": "kenapa",
            "mgkn": "mungkin",
            "krn": "karena",
            "karna": "karena",
            "trs": "terus",
            "trz": "terus",
            "hrs": "harus",
            "jg": "juga",
            "jgn": "jangan",
            "msh": "masih",
            "yg": "yang",
            "dgn": "dengan",
            "sm": "sama",
            "tp": "tapi",
            "klo": "kalau",
            "kl": "kalau",
            "ato": "atau",
            "atw": "atau",
            "bs": "bisa",
            "bsa": "bisa",
            "emg": "memang",
            "emang": "memang",
            "skrg": "sekarang",
            "skrang": "sekarang",
            "skg": "sekarang",
            "kmrn": "kemarin",
            "kyk": "kayak",
            "kaya": "kayak",
            "lg": "lagi",
            "lgi": "lagi",
            "pke": "pakai",
            "spt": "seperti",
            "ky": "kayak",
            "mksd": "maksud",
            "mksdnya": "maksudnya",
            "bbrp": "beberapa",
            "krng": "kurang",
            "jd": "jadi",
            "jdi": "jadi",
            "aj": "aja",
            "sy": "saya",
            "sy": "saya",
            "org": "orang",
            "nyala": "menyala",
            "gakbisa": "gak bisa",
            "gabisa": "ga bisa",
            "gatau": "ga tau",
            "gktau": "gak tau",
        }
        
        self.typo_map = {
            "suadh": "sudah",
            "sudha": "sudah",
            "bleum": "belum",
            "bunyii": "bunyi",
            "buniy": "bunyi",
            "bauu": "bau",
            "bua": "bau",
            "matii": "mati",
            "nyalaa": "nyala",
            "tiadk": "tidak",
            "tidka": "tidak",
            "tidaak": "tidak",
            "berisikk": "berisik",
            "berisiq": "berisik",
            "berisick": "berisik",
            "brisik": "berisik",
            "hidupp": "hidup",
            "idupp": "hidup",
            "rusaak": "rusak",
            "rusa k": "rusak",
            "normall": "normal",
            "norml": "normal",
            "sering": "sering",
            "seringg": "sering",
            "srng": "sering",
            "jarangg": "jarang",
            "jarng": "jarang",
            "kadangg": "kadang",
            "kdang": "kadang",
            "kadng": "kadang",
        }
    
    def normalize_word(self, word: str) -> str:
        word_lower = word.lower().strip()
        
        if word_lower in self.slang_map:
            return self.slang_map[word_lower]
        
        if word_lower in self.typo_map:
            return self.typo_map[word_lower]
        
        return word
    
    def normalize_text(self, text: str, preserve_case: bool = False) -> str:
        if not text:
            return text
        
        words = text.split()
        normalized_words = []
        
        for word in words:
            normalized = self.normalize_word(word)
            normalized_words.append(normalized)
        
        return " ".join(normalized_words)
    
    def normalize_for_intent(self, text: str) -> str:
        normalized = self.normalize_text(text)
        
        normalized = normalized.replace("  ", " ").strip()
        
        return normalized
