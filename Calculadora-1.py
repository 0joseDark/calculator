import sys
import math
from fractions import Fraction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QMenuBar, QMenu, QAction, QMessageBox
)
from PySide6.QtCore import Qt

class Calculadora(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Qt — Multiplataforma")
        self.setGeometry(200, 200, 400, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.layout.addWidget(self.display)

        self.memory = 0  # memória da calculadora

        self.criar_menu()
        self.criar_botoes()

    def criar_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        menu_ajuda = QMenu("Ajuda", self)
        menubar.addMenu(menu_ajuda)

        sobre = QAction("Sobre", self)
        sobre.triggered.connect(self.mostrar_sobre)
        menu_ajuda.addAction(sobre)

    def mostrar_sobre(self):
        QMessageBox.information(self, "Sobre", "Calculadora Qt com memória e frações. Funciona em Windows, Ubuntu e Mac.")

    def criar_botoes(self):
        grid = QGridLayout()
        self.layout.addLayout(grid)

        botoes = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3), ('MC', 1, 4),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3), ('MR', 2, 4),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3), ('MS', 3, 4),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3), ('M+', 4, 4),
            ('C', 5, 0), ('√', 5, 1), ('x²', 5, 2), ('1/x', 5, 3), ('Frac', 5, 4)
        ]

        for texto, linha, coluna in botoes:
            botao = QPushButton(texto)
            botao.clicked.connect(lambda _, t=texto: self.on_click(t))
            grid.addWidget(botao, linha, coluna)

    def on_click(self, tecla):
        if tecla == 'C':
            self.display.clear()
        elif tecla == '=':
            self.calcular()
        elif tecla == '√':
            self.display.insert("sqrt(")
        elif tecla == 'x²':
            self.display.insert("**2")
        elif tecla == '1/x':
            self.display.insert("1/(")
        elif tecla == 'Frac':
            try:
                valor = eval(self.display.text())
                frac = Fraction(valor).limit_denominator()
                self.display.setText(str(frac))
            except Exception:
                self.display.setText("Erro")
        elif tecla == 'MC':
            self.memory = 0
        elif tecla == 'MR':
            self.display.setText(str(self.memory))
        elif tecla == 'MS':
            try:
                self.memory = eval(self.display.text())
            except Exception:
                self.display.setText("Erro")
        elif tecla == 'M+':
            try:
                self.memory += eval(self.display.text())
            except Exception:
                self.display.setText("Erro")
        else:
            self.display.insert(tecla)

    def calcular(self):
        try:
            expressao = self.display.text()
            resultado = eval(expressao, {"__builtins__": None}, {"sqrt": math.sqrt})
            self.display.setText(str(resultado))
        except Exception:
            self.display.setText("Erro")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    calc = Calculadora()
    calc.show()
    sys.exit(app.exec())
