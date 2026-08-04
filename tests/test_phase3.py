import sys
import os
import unittest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.radial_menu import RadialMenu


class TestPhase3Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_radial_menu_initialization(self):
        menu = RadialMenu(radius=60)
        self.assertIsNotNone(menu)
        self.assertEqual(len(menu.ACTIONS), 5)

    def test_radial_menu_show_at_position(self):
        menu = RadialMenu(radius=60)
        target_pos = QPoint(500, 400)
        menu.show_at_position(target_pos)
        self.assertTrue(menu.isVisible())
        menu.close()


if __name__ == '__main__':
    unittest.main()
