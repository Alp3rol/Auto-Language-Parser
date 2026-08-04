import sys
import os


class ContextEngine:
    """
    Ekrandaki metni ve aktif uygulamayı inceleyerek bağlamı (Software, Gaming, Legal, Manga) algılayan ve
    jargona özel çeviri uyarlaması yapan akıllı zeka motoru.
    """
    SOFTWARE_TERMS = {
        "deprecated": "kullanımdan kaldırıldı (ömrü doldu)",
        "refactor": "kodu yeniden yapılandır",
        "override": "üzerine yaz (ezme)",
        "callback": "geri çağırma fonksiyonu",
        "thread": "iş parçacığı",
        "buffer": "arabellek",
        "pipeline": "işlem hattı",
        "array": "dizi",
        "stack trace": "hata izleme yığını",
        "repository": "kod deposu (repo)",
        "instance": "örnek / nesne örneği"
    }

    GAMING_TERMS = {
        "deprecated": "eski / kullanılmayan eşya",
        "buff": "güçlendirme",
        "debuff": "zayıflatma",
        "cooldown": "bekleme süresi",
        "quest": "görev",
        "inventory": "envanter",
        "durability": "dayanıklılık",
        "loot": "ganimet"
    }

    def detect_context(self, text: str) -> str:
        """
        Metindeki anahtar kelimelere göre alanı tespit eder: 'software', 'gaming', 'general'
        """
        text_lower = text.lower()

        sw_score = sum(1 for k in self.SOFTWARE_TERMS if k in text_lower)
        game_score = sum(1 for k in self.GAMING_TERMS if k in text_lower)

        if sw_score > game_score and sw_score >= 1:
            return "software"
        elif game_score > sw_score and game_score >= 1:
            return "gaming"

        return "general"

    def adapt_translation(self, original_text: str, default_translated: str) -> str:
        """
        Çeviriyi algılanan jargona göre zenginleştirir ve düzeltir.
        """
        context = self.detect_context(original_text)
        text_lower = original_text.lower().strip()

        if context == "software":
            for term, replacement in self.SOFTWARE_TERMS.items():
                if term in text_lower:
                    # Tek kelimelik eşleşmede doğrudan jargon karşılığını kullan
                    if text_lower in (term, f"({term})", f"[{term}]"):
                        return replacement.capitalize()
        elif context == "gaming":
            for term, replacement in self.GAMING_TERMS.items():
                if term in text_lower:
                    if text_lower in (term, f"({term})", f"[{term}]"):
                        return replacement.capitalize()

        return default_translated

    def process_ai_action(self, action_type: str, text: str, translate_service=None) -> str:
        """
        Seçilen metin üzerinde hızlı AI aksiyonları gerçekleştirir:
        - 'summarize': Metni özetler ve ana noktaları çıkarır.
        - 'explain_error': Kod/sistem hatalarının nedenini ve çözümünü açıklar.
        - 'draft_reply': Gelen mesaja uygun profesyonel yanıt taslağı oluşturur.
        """
        if not text or not text.strip():
            return "İşlenecek metin bulunamadı."

        text_clean = text.strip()

        if action_type == "summarize":
            return self._ai_summarize(text_clean, translate_service)
        elif action_type == "explain_error":
            return self._ai_explain_error(text_clean)
        elif action_type == "draft_reply":
            return self._ai_draft_reply(text_clean)

        return "Geçersiz AI aksiyonu."

    def _ai_summarize(self, text: str, translate_service=None) -> str:
        """Metni 3 ana maddede özetler."""
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip() and len(s.strip()) > 5]
        
        if not sentences:
            return f"📌 **Özet:** {text[:100]}..."

        # Metni Türkçe çevirisi ile özetle
        summary_bullets = []
        take_count = min(3, max(1, len(sentences)))
        
        # En önemli ilk, orta ve son cümleleri seç
        if len(sentences) <= 3:
            selected = sentences
        else:
            selected = [sentences[0], sentences[len(sentences)//2], sentences[-1]]

        for idx, stmt in enumerate(selected, 1):
            if translate_service:
                try:
                    tr_stmt, _, _ = translate_service.translate(stmt, target_lang="tr")
                    stmt = tr_stmt
                except Exception:
                    pass
            summary_bullets.append(f"• {stmt}")

        return "📝 **Hızlı Özet:**\n" + "\n".join(summary_bullets)

    def _ai_explain_error(self, text: str) -> str:
        """Ekrandaki kod/sistem hatasını analiz edip neden ve çözümünü sunar."""
        text_lower = text.lower()
        
        error_knowledge = {
            "typeerror": ("Veri Tipi Uyuşmazlığı", "Beklenen veri tipi yerine farklı bir nesne/tip gönderilmiş. Parametre tiplerini kontrol edin."),
            "attributeerror": ("Eksik/Hatalı Öznitelik", "Nesne üzerinde bulunmayan bir metod veya değişken çağrılmış. Nesnenin başlatıldığından (init) emin olun."),
            "indexerror": ("Dizi Sınır Aşımı", "Liste veya dizide mevcut olmayan bir indekse erişilmeye çalışılmış. Dizi uzunluğunu (len) kontrol edin."),
            "keyerror": ("Sözlükte Anahtar Bulunamadı", "Sözlük (dict) içinde aranan anahtar mevcut değil. `.get('key')` veya anahtar varlığını kontrol edin."),
            "syntaxerror": ("Sözdizimi Hatası", "Kod yazım kuralına uyulmamış (eksik parantez, tırnak veya iki nokta). Koddaki noktalama işaretlerini inceleyin."),
            "nullpointerexception": ("Boş Referans (Null Pointer)", "Henüz nesnesi oluşturulmamış (null) bir değişken dereferanse edilmiş. Null kontrolü ekleyin."),
            "connectionerror": ("Bağlantı Hatası", "Sunucuya veya API uç noktasına ulaşılamadı. İnternet bağlantınızı ve port ayarlarını kontrol edin."),
            "404": ("Sayfa/Kaynak Bulunamadı", "İstenen URL veya API rotası sunucuda mevcut değil. Adresi ve endpoint yolunu kontrol edin."),
            "500": ("Sunucu İç Hatası (Internal Server Error)", "Karşı sunucuda beklenmeyen bir hata oluştu. Sunucu loglarını inceleyin."),
            "permissiondenied": ("Yetki / Erişim Engeli", "İşlem yapılan dosya veya sistem kaynağı için yeterli yönetici izni yok.")
        }

        found_title = "Genel Yazılım/Sistem Hatası"
        found_desc = "Kod yürütme veya sistem çalışması sırasında aksama oluşmuş."
        found_fix = "Hata yığınını (stack trace) ve ilgili değişken tanımlarını inceleyin."

        for key, (title, fix) in error_knowledge.items():
            if key in text_lower:
                found_title = title
                found_fix = fix
                break

        return (
            f"🐞 **Hata Analizi: {found_title}**\n\n"
            f"🔍 **Girdi:** `{text[:80]}...`\n"
            f"💡 **Çözüm Önerisi:** {found_fix}"
        )

    def _ai_draft_reply(self, text: str) -> str:
        """Mesaja veya e-postaya uygun 2 farklı yanıt taslağı oluşturur."""
        return (
            "✉️ **Önerilen Yanıt Taslakları:**\n\n"
            "1️⃣ **Resmi / Profesyonel:**\n"
            "\"Bilgilendirme için teşekkür ederim. Detayları inceleyip en kısa sürede dönüş yapacağım.\"\n\n"
            "2️⃣ **Samimi / Hızlı:**\n"
            "\"Harika, mesajını aldım! Hemen bakıp sana yazıyorum 👍\""
        )

