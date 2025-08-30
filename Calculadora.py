#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import math
from fractions import Fraction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QMessageBox
)
from PySide6.QtGui import QAction


class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Científica Qt")

        # Estado da calculadora
        self.memory = 0
        self.fraction_mode = False

        # Campo de entrada
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("0")
        self.entry.setReadOnly(True)
        self.entry.setFixedHeight(40)

        # Layout principal
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.addWidget(self.entry)

        # Layout dos botões
        grid = QGridLayout()
        layout.addLayout(grid)

        # Botões básicos
        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2), ("/", 0, 3),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("*", 1, 3),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2), ("-", 2, 3),
            ("0", 3, 0), (".", 3, 1), ("=", 3, 2), ("+", 3, 3),
        ]

        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(60, 40)
            grid.addWidget(btn, row, col)
            btn.clicked.connect(self.on_button_clicked)

        # Botões de memória
        mem_buttons = ["MC", "MR", "MS", "M+"]
        for i, text in enumerate(mem_buttons):
            btn = QPushButton(text)
            btn.setFixedSize(60, 40)
            grid.addWidget(btn, 4, i)
            btn.clicked.connect(self.on_memory_clicked)

        # Botões científicos
        sci_buttons = ["sin", "cos", "tan", "log", "ln", "sqrt", "pi", "e"]
        for i, text in enumerate(sci_buttons):
            btn = QPushButton(text)
            btn.setFixedSize(60, 40)
            grid.addWidget(btn, 5 + i // 4, i % 4)
            btn.clicked.connect(self.on_sci_clicked)

        # Construir menu
        self._build_menus()

    # ---------------- Menu ----------------
    def _build_menus(self):
        menubar = self.menuBar()

        menu_file = menubar.addMenu("Arquivo")
        act_exit = QAction("Sair", self)
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        menu_opt = menubar.addMenu("Opções")
        act_frac = QAction("Modo Fração", self, checkable=True)
        act_frac.toggled.connect(self.toggle_fraction_mode)
        menu_opt.addAction(act_frac)

        menu_help = menubar.addMenu("Ajuda")
        act_about = QAction("Sobre", self)
        act_about.triggered.connect(
            lambda: QMessageBox.about(self, "Sobre", "Calculadora Científica Qt\nSuporta frações e funções científicas.")
        )
        menu_help.addAction(act_about)

    # ---------------- Entrada de botões ----------------
    def on_button_clicked(self):
        sender = self.sender().text()
        if sender == "=":
            self.calculate()
        elif sender == "C":
            self.entry.clear()
        else:
            self.entry.insert(sender)

    def on_memory_clicked(self):
        sender = self.sender().text()
        try:
            current = float(self.entry.text()) if self.entry.text() else 0
        except ValueError:
            current = 0

        if sender == "MC":
            self.memory = 0
        elif sender == "MR":
            self.entry.setText(str(self.memory))
        elif sender == "MS":
            self.memory = current
        elif sender == "M+":
            self.memory += current

    def on_sci_clicked(self):
        sender = self.sender().text()
        try:
            x = float(self.entry.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Entrada inválida.")
            return

        if sender == "sin":
            res = math.sin(math.radians(x))
        elif sender == "cos":
            res = math.cos(math.radians(x))
        elif sender == "tan":
            res = math.tan(math.radians(x))
        elif sender == "log":
            res = math.log10(x)
        elif sender == "ln":
            res = math.log(x)
        elif sender == "sqrt":
            res = math.sqrt(x)
        elif sender == "pi":
            res = math.pi
        elif sender == "e":
            res = math.e
        else:
            res = 0

        if self.fraction_mode:
            res = Fraction(res).limit_denominator()
        self.entry.setText(str(res))

    # ---------------- Cálculo ----------------
    def calculate(self):
        try:
            expr = self.entry.text()
            res = eval(expr, {"__builtins__": None}, math.__dict__)
            if self.fraction_mode:
                res = Fraction(res).limit_denominator()
            self.entry.setText(str(res))
        except Exception:
            QMessageBox.warning(self, "Erro", "Expressão inválida.")

    # ---------------- Frações ----------------
    def toggle_fraction_mode(self, checked):
        self.fraction_mode = checked


def main():
    app = QApplication(sys.argv)
    w = CalculatorWindow()
    w.resize(300, 400)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
