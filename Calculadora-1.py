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


class Calculadora(QMainWindow):
    def __init__(self):
        super().__init__()

        # Janela principal
        self.setWindowTitle("Calculadora Qt — PySide6")
        self.setGeometry(200, 200, 400, 400)

        # Visor
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setFixedHeight(40)

        # Memória da calculadora
        self.memory = 0

        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        v_layout = QVBoxLayout(central_widget)
        v_layout.addWidget(self.display)

        # Botões
        grid = QGridLayout()
        v_layout.addLayout(grid)

        botoes = [
            ["7", "8", "9", "/", "√"],
            ["4", "5", "6", "*", "^"],
            ["1", "2", "3", "-", "1/x"],
            ["0", ".", "=", "+", "Frac"],
            ["MC", "MR", "MS", "M+", "C"],
        ]

        for i, linha in enumerate(botoes):
            for j, texto in enumerate(linha):
                botao = QPushButton(texto)
                botao.setFixedSize(60, 40)
                botao.clicked.connect(lambda _, t=texto: self.on_click(t))
                grid.addWidget(botao, i, j)

        # Menu
        menu = self.menuBar()
        menu_ajuda = menu.addMenu("Ajuda")

        sobre_action = QAction("Sobre", self)
        sobre_action.triggered.connect(self.sobre)
        menu_ajuda.addAction(sobre_action)

        sair_action = QAction("Sair", self)
        sair_action.triggered.connect(self.close)
        menu_ajuda.addAction(sair_action)

    def on_click(self, texto):
        if texto == "C":
            self.display.clear()
        elif texto == "=":
            self.calcular()
        elif texto == "√":
            self.display.insert("sqrt(")
        elif texto == "^":
            self.display.insert("**")
        elif texto == "1/x":
            self.display.insert("1/(")
        elif texto == "Frac":
            try:
                valor = eval(self.display.text())
                self.display.setText(str(Fraction(valor).limit_denominator()))
            except Exception:
                self.display.setText("Erro")
        elif texto in ["MC", "MR", "MS", "M+"]:
            self.memoria(texto)
        else:
            self.display.insert(texto)

    def calcular(self):
        try:
            expressao = self.display.text()
            resultado = eval(
                expressao,
                {"__builtins__": None},
                {"sqrt": math.sqrt, "Fraction": Fraction}
            )
            self.display.setText(str(resultado))
        except Exception:
            self.display.setText("Erro")

    def memoria(self, acao):
        try:
            if acao == "MC":
                self.memory = 0
            elif acao == "MR":
                self.display.setText(str(self.memory))
            elif acao == "MS":
                self.memory = float(eval(self.display.text()))
            elif acao == "M+":
                self.memory += float(eval(self.display.text()))
        except Exception:
            self.display.setText("Erro")

    def sobre(self):
        QMessageBox.information(
            self,
            "Sobre",
            "Calculadora Qt — compatível com Windows, Ubuntu e Mac\n\n"
            "Inclui operações básicas, frações e memória de cálculo."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = Calculadora()
    janela.show()
    sys.exit(app.exec())
