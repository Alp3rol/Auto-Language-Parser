import os


class AnkiExportService:
    """
    VocabService veritabanındaki kelime kartlarını Anki Desktop / AnkiMobile / AnkiWeb
    tarafından doğrudan içe aktarılabilir (.txt / .csv / TSV) formatında dışa aktaran servis.
    """

    @staticmethod
    def export_to_tsv(cards: list[dict], output_filepath: str) -> bool:
        """
        Kelimeleri Anki Tab-Separated Values (TSV) formatında yazar:
        Front (English) \t Back (Turkish) \t Tags
        """
        if not output_filepath:
            return False

        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                # Anki Header
                f.write("#separator:tab\n")
                f.write("#html:false\n")
                f.write("#tags column:3\n")

                for card in cards:
                    word = (
                        card.get("word", "").replace("\t", " ").replace("\n", " ")
                    )
                    translation = (
                        card.get("translation", "")
                        .replace("\t", " ")
                        .replace("\n", " ")
                    )
                    tag = "ALP_Screen_Translator"

                    if word and translation:
                        f.write(f"{word}\t{translation}\t{tag}\n")

            return True
        except Exception as e:
            print(f"[ANKI EXPORT HATASI] {e}")
            return False
