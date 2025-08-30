#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora Qt multiplataforma (Windows 10, Ubuntu, macOS)
---------------------------------------------------------
Versão corrigida — evita erros de conversão Decimal/Fraction.
"""

from __future__ import annotations

import ast
import math
from decimal import Decimal, getcontext
from fractions import Fraction
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QWidget,
)

# Aumentar precisão decimal
getcontext().prec = 50


class SafeEvaluator:
    def __init__(self, fraction_mode: bool = False):
        self.fraction_mode = fraction_mode

    def _to_decimal(self, n: Any) -> Decimal:
        if isinstance(n, Decimal):
            return n
        if isinstance(n, int):
            return Decimal(n)
        if isinstance(n, float):
            return Decimal(str(n))
        if isinstance(n, Fraction):
            return Decimal(n.numerator) / Decimal(n.denominator)
        return Decimal(str(n))

    def _to_fraction(self, n: Any) -> Fraction:
        if isinstance(n, Fraction):
            return n
        if isinstance(n, int):
            return Fraction(n, 1)
        if isinstance(n, float):
            return Fraction(n).limit_denominator(1_000_000)
        if isinstance(n, Decimal):
            return Fraction(str(n))
        return Fraction(n)

    def _binop(self, op, a, b):
        if self.fraction_mode:
            A, B = self._to_fraction(a), self._to_fraction(b)
        else:
            A, B = self._to_decimal(a), self._to_decimal(b)

        if isinstance(op, ast.Add):
            return A + B
        if isinstance(op, ast.Sub):
            return A - B
        if isinstance(op, ast.Mult):
            return A * B
        if isinstance(op, ast.Div):
            return A / B
        if isinstance(op, ast.Pow):
            if self.fraction_mode:
                if isinstance(B, Fraction) and B.denominator == 1:
                    return A ** B.numerator
                else:
                    return self._to_decimal(A) ** self._to_decimal(B)
            else:
                return A ** B
        raise TypeError("Operador não suportado")

    def _unary(self, op, a):
        A = self._to_fraction(a) if self.fraction_mode else self._to_decimal(a)
        if isinstance(op, ast.UAdd):
            return +A
        if isinstance(op, ast.USub):
            return -A
        raise TypeError("Operador unário não suportado")

    def _call(self, func_name: str, args: list[Any]):
        if func_name == "sqrt":
            x = args[0]
            if self.fraction_mode:
                X = self._to_fraction(x)
                num, den = X.numerator, X.denominator
                rn, rd = int(math.isqrt(num)), int(math.isqrt(den))
                if rn * rn == num and rd * rd == den:
                    return Fraction(rn, rd)
                return self._to_decimal(X).sqrt()
            else:
                return self._to_decimal(x).sqrt()
        raise NameError(f"Função não permitida: {func_name}")

    def eval(self, text: str) -> Any:
        expr = (
            text.replace("×", "*")
            .replace("÷", "/")
            .replace("^", "**")
            .replace("√", "sqrt")
        )
        node = ast.parse(expr, mode="eval")
        return self._eval_node(node.body)

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BinOp):
            return self._binop(type(node.op), self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            return self._unary(type(node.op), self._eval_node(node.operand))
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else ""
            args = [self._eval_node(a) for a in node.args]
            return self._call(func_name, args)
        raise TypeError(f"Elemento da expressão não suportado: {type(node).__name__}")


class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Qt")
        self.resize(400, 500)

        self.fraction_mode = False

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFixedHeight(48)

        self.result_label = QLabel("0")
        self.result_label.setAlignment(Qt.AlignRight)

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignRight)

        grid = QGridLayout()
        buttons = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"],
            ["(", ")", "C", "√"],
        ]

        for r, row in enumerate(buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedHeight(50)
                btn.clicked.connect(self.on_button_clicked)
                grid.addWidget(btn, r, c)

        central = QWidget()
        v = QGridLayout(central)
        v.addWidget(self.display, 0, 0, 1, 1)
        v.addWidget(self.result_label, 1, 0, 1, 1)
        v.addWidget(self.hint_label, 2, 0, 1, 1)
        v.addLayout(grid, 3, 0, 1, 1)
        self.setCentralWidget(central)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def on_button_clicked(self):
        text = self.sender().text()
        if text == "C":
            self.display.clear()
            self.result_label.setText("0")
            self.hint_label.clear()
            return
        if text == "=":
            self.evaluate()
            return
        if text == "√":
            self.display.setText(f"sqrt({self.display.text()})")
            return
        self.display.setText(self.display.text() + text)

    def evaluate(self):
        text = self.display.text().strip()
        if not text:
            return
        try:
            evaluator = SafeEvaluator(self.fraction_mode)
            result = evaluator.eval(text)
            if self.fraction_mode and isinstance(result, Fraction):
                if result.denominator == 1:
                    self.result_label.setText(str(result.numerator))
                else:
                    self.result_label.setText(f"{result.numerator}/{result.denominator}")
                approx = Decimal(result.numerator) / Decimal(result.denominator)
                self.hint_label.setText(f"≈ {approx}")
            else:
                result = evaluator._to_decimal(result)
                self.result_label.setText(str(result.normalize()))
                self.hint_label.clear()
        except Exception as e:
            self.result_label.setText(f"Erro: {e}")
            self.hint_label.clear()


def main():
    import sys
    app = QApplication(sys.argv)
    w = CalculatorWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
