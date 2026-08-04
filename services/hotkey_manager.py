import keyboard
from pynput import keyboard as pynput_keyboard
from PySide6.QtCore import QObject, Signal


def to_pynput_format(shortcut_str: str) -> str:
    """
    'Alt+S' -> '<alt>+s'
    'F8' -> '<f8>'
    'Ctrl+Alt+S' -> '<ctrl>+<alt>+s'
    'Ctrl+Shift+C' -> '<ctrl>+<shift>+c'
    'Alt+C' -> '<alt>+c'
    'F9' -> '<f9>'
    """
    if not shortcut_str:
        return "<alt>+s"
    parts = shortcut_str.split("+")
    formatted = []
    for p in parts:
        p_clean = p.strip().lower()
        if p_clean in ("ctrl", "control"):
            formatted.append("<ctrl>")
        elif p_clean == "alt":
            formatted.append("<alt>")
        elif p_clean == "shift":
            formatted.append("<shift>")
        elif p_clean.startswith("f") and p_clean[1:].isdigit():
            formatted.append(f"<{p_clean}>")
        else:
            formatted.append(p_clean)
    return "+".join(formatted)


class HotkeyManager(QObject):
    """
    Windows genelinde (Global) klavye tuş dinleme sağlayan hibrit kısayol yöneticisi.
    'keyboard' kütüphanesini birincil (Windows low-level hook), 'pynput' kütüphanesini yedek olarak kullanır.
    """

    triggered = Signal()
    selection_triggered = Signal()

    def __init__(self):
        super().__init__()
        self.listener = None
        self.keyboard_hooks = []

    def start(
        self, crop_preset: str = "Alt+S", selection_preset: str = "Alt+C"
    ):
        self.stop()

        def on_crop():
            print(f"[HOTKEY] Ekran Seçim Kısayolu ({crop_preset}) Algılandı!")
            self.triggered.emit()

        def on_selection():
            print(
                f"[HOTKEY] Seçili Metin Çevirme Kısayolu ({selection_preset}) Algılandı!"
            )
            self.selection_triggered.emit()

        # 1. Birincil Yöntem: 'keyboard' kütüphanesi (Windows low-level hook, Alt+Q, Alt+S, F8 vb. %100 kararlı)
        try:
            hk1 = keyboard.add_hotkey(crop_preset.lower().strip(), on_crop, suppress=False)
            hk2 = keyboard.add_hotkey(selection_preset.lower().strip(), on_selection, suppress=False)
            self.keyboard_hooks.extend([crop_preset.lower().strip(), selection_preset.lower().strip()])
            print(
                f"[BAŞARILI] Global Kısayol Dinleyicisi Aktif ({crop_preset}, {selection_preset})"
            )
            return
        except Exception as ke:
            print(f"[UYARI] 'keyboard' kısayol dinleyicisi başlatılamadı, pynput deneniyor: {ke}")

        # 2. Yedek Yöntem: 'pynput' kütüphanesi
        crop_pynput = to_pynput_format(crop_preset)
        sel_pynput = to_pynput_format(selection_preset)

        hotkeys = {crop_pynput: on_crop, sel_pynput: on_selection}

        try:
            self.listener = pynput_keyboard.GlobalHotKeys(hotkeys)
            self.listener.start()
            print(
                f"[BAŞARILI] Global Kısayol Dinleyicisi Aktif ({crop_preset}, {selection_preset})"
            )
        except Exception as e:
            print(
                f"[HATA] Global kısayol dinleyicisi başlatılamadı ({crop_preset}, {selection_preset}): {e}"
            )

    def stop(self):
        if self.keyboard_hooks:
            for hk in self.keyboard_hooks:
                try:
                    keyboard.remove_hotkey(hk)
                except Exception:
                    pass
            self.keyboard_hooks.clear()

        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
