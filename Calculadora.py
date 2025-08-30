#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora Qt multiplataforma (Windows 10, Ubuntu, macOS)
---------------------------------------------------------
• Interface com menu + botões (teclado numérico, operações básicas, parênteses).
• Suporte a frações (modo dedicado) e números decimais com alta precisão (Decimal).
• Avaliador seguro de expressões (usa AST; apenas +, -, *, /, potência **, parênteses, sqrt).
• Resultado mostra forma exata (inteiro/fração) e aproximação decimal.
• Atalhos de teclado: dígitos e operadores, Enter (=), Backspace (⌫), Esc (C), Ctrl+C / Ctrl+V.

Dependências: PySide6 (Qt for Python).
    pip install pyside6

Como executar:
    python calculadora_qt.py

Notas sobre o modo Frações:
- Quando ativo, operações são feitas com Fraction (racionais). "1/3 + 1/6" retorna "1/2".
- Decimais no modo frações são convertidos para frações aproximadas (limit_denominator).
- A etiqueta inferior mostra a aproximação decimal (ex.: ≈ 0.5).

"""
from __future__ import annotations

import ast
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

# Aumentar precisão decimal para operações não fracionárias
getcontext().prec = 50


# =========================
# Avaliador seguro (AST)
# =========================
class SafeEvaluator:
    """Avaliador seguro de expressões matemáticas básicas usando AST.

    Suporta:
      - Literais numéricos
      - Operadores: +, -, *, /, **
      - Unários: +a, -a
      - Parênteses
      - Funções: sqrt(x)

    Dois modos de cálculo:
      - fraction_mode=False -> usa Decimal para precisão em base 10
      - fraction_mode=True  -> usa Fraction (racional exata quando possível)
    """

    def __init__(self, fraction_mode: bool = False):
        self.fraction_mode = fraction_mode

    # --- utilidades de conversão ---
    def _to_decimal(self, n: Any) -> Decimal:
        if isinstance(n, Decimal):
            return n
        if isinstance(n, int):
            return Decimal(n)
        if isinstance(n, float):
            # str(n) evita o ruído binário do float
            return Decimal(str(n))
        if isinstance(n, Fraction):
            return Decimal(n.numerator) / Decimal(n.denominator)
        raise TypeError(f"Tipo não suportado em Decimal: {type(n)}")

    def _to_fraction(self, n: Any) -> Fraction:
        if isinstance(n, Fraction):
            return n
        if isinstance(n, int):
            return Fraction(n, 1)
        if isinstance(n, float):
            # Aproxima a fração a um denominador razoável
            return Fraction(n).limit_denominator(1_000_000)
        if isinstance(n, Decimal):
            return Fraction(n)
        raise TypeError(f"Tipo não suportado em Fraction: {type(n)}")

    # --- operações ---
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
            # Divisão verdadeira
            return A / B
        if isinstance(op, ast.Pow):
            # Potências
            if self.fraction_mode:
                # Fraction ** inteiro funciona; para expoente não-inteiro, usa Decimal
                if isinstance(B, Fraction) and B.denominator == 1:
                    return A ** B.numerator
                else:
                    # converte para Decimal para expoentes fracionários
                    return self._to_decimal(A) ** self._to_decimal(B)
            else:
                return A ** B
        raise TypeError("Operador não suportado")

    def _unary(self, op, a):
        if self.fraction_mode:
            A = self._to_fraction(a)
        else:
            A = self._to_decimal(a)
        if isinstance(op, ast.UAdd):
            return +A
        if isinstance(op, ast.USub):
            return -A
        raise TypeError("Operador unário não suportado")

    # --- funções disponíveis ---
    def _call(self, func_name: str, args: list[Any]):
        if func_name == "sqrt":
            x = args[0]
            if self.fraction_mode:
                # sqrt exata se quadrado perfeito; caso contrário, Decimal
                X = self._to_fraction(x)
                num, den = X.numerator, X.denominator
                import math

                rn, rd = int(math.isqrt(num)), int(math.isqrt(den))
                if rn * rn == num and rd * rd == den:
                    return Fraction(rn, rd)
                return self._to_decimal(X).sqrt()
            else:
                return self._to_decimal(x).sqrt()
        raise NameError(f"Função não permitida: {func_name}")

    # --- avaliação recursiva ---
    def eval(self, text: str) -> Any:
        # limpeza e substituições amigáveis do UI -> expressão Python
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
        if isinstance(node, ast.Name):
            # bloquear variáveis
            raise NameError("Uso de nomes/variáveis não permitido")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise NameError("Chamada inválida")
            func_name = node.func.id
            args = [self._eval_node(a) for a in node.args]
            if len(args) != 1:
                raise TypeError("Apenas funções unárias são suportadas: p.ex. sqrt(x)")
            return self._call(func_name, args)
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        if isinstance(node, ast.Tuple):
            raise TypeError("Tuplos não são suportados")
        raise TypeError(f"Elemento da expressão não suportado: {type(node).__name__}")


# =========================
# Interface Qt
# =========================
class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Qt — Frações e Decimais")
        self.resize(420, 540)

        self.fraction_mode = False

        # Campo de expressão (apenas leitura; entrada via botões/teclado)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setPlaceholderText("Introduza a expressão…")
        self.display.setObjectName("display")
        self.display.setFocusPolicy(Qt.StrongFocus)
        self.display.setFixedHeight(48)

        # Etiqueta para resultado e aproximação
        self.result_label = QLabel("0")
        self.result_label.setAlignment(Qt.AlignRight)
        self.result_label.setObjectName("result")
        self.result_label.setFixedHeight(36)

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignRight)
        self.hint_label.setObjectName("hint")
        self.hint_label.setFixedHeight(24)

        # Grelha de botões
        grid = QGridLayout()
        buttons = [
            ["CE", "C", "⌫", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["(", ")", "a/b", "1/x"],
            ["±", "0", ".", "="] ,
            ["x²", "√", "^", "%"],
        ]
        # Mapeamento visual -> expressão
        self.ops_map = {"−": "-", "×": "*", "÷": "/"}

        # Criar botões
        for r, row in enumerate(buttons):
            for c, text in enumerate(row):
                if text == "":
                    continue
                btn = QPushButton(text)
                btn.setFixedHeight(56)
                btn.setObjectName("btn")
                btn.clicked.connect(self.on_button_clicked)
                grid.addWidget(btn, r, c)

        # Layout principal
        central = QWidget()
        v = QGridLayout(central)
        v.addWidget(self.display, 0, 0, 1, 1)
        v.addWidget(self.result_label, 1, 0, 1, 1)
        v.addWidget(self.hint_label, 2, 0, 1, 1)
        v.addLayout(grid, 3, 0, 1, 1)
        self.setCentralWidget(central)

        # Barra de estado
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()

        # Menus
        self._build_menus()

        # Estilo inicial (claro)
        self.apply_light_theme()

    # -----------------------
    # Construção de menus
    # -----------------------
    def _build_menus(self):
        menubar = self.menuBar()

        # Ficheiro
        m_file = menubar.addMenu("&Ficheiro")
        act_quit = QAction("Sair", self, shortcut=QKeySequence.Quit)
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        # Editar
        m_edit = menubar.addMenu("&Editar")
        act_copy = QAction("Copiar resultado", self, shortcut=QKeySequence.Copy)
        act_copy.triggered.connect(self.copy_result)
        m_edit.addAction(act_copy)

        act_paste = QAction("Colar na expressão", self, shortcut=QKeySequence.Paste)
        act_paste.triggered.connect(self.paste_to_expression)
        m_edit.addAction(act_paste)

        act_clear = QAction("Limpar (C)", self, shortcut=QKeySequence("Esc"))
        act_clear.triggered.connect(lambda: self._clear(all_=True))
        m_edit.addAction(act_clear)

        # Ver
        m_view = menubar.addMenu("&Ver")
        self.act_fraction = QAction("Modo &Frações", self, checkable=True)
        self.act_fraction.toggled.connect(self.toggle_fraction_mode)
        m_view.addAction(self.act_fraction)

        self.act_dark = QAction("Tema &Escuro", self, checkable=True)
        self.act_dark.toggled.connect(self.toggle_theme)
        m_view.addAction(self.act_dark)

        # Ajuda
        m_help = menubar.addMenu("A&juda")
        act_shortcuts = QAction("Teclas de atalho", self)
        act_shortcuts.triggered.connect(self.show_shortcuts)
        m_help.addAction(act_shortcuts)

        act_about = QAction("Sobre", self)
        act_about.triggered.connect(self.show_about)
        m_help.addAction(act_about)

    # -----------------------
    # Slots de menu
    # -----------------------
    def copy_result(self):
        QApplication.clipboard().setText(self.result_label.text())
        self.status.showMessage("Resultado copiado", 2000)

    def paste_to_expression(self):
        self._insert_text(QApplication.clipboard().text())

    def toggle_fraction_mode(self, checked: bool):
        self.fraction_mode = checked
        self._update_status()
        self.evaluate()

    def toggle_theme(self, dark: bool):
        if dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    # -----------------------
    # Botões
    # -----------------------
    def on_button_clicked(self):
        text = self.sender().text()
        if text == "C":
            self._clear(all_=True)
            return
        if text == "CE":
            self._clear(all_=False)
            return
        if text == "⌫":
            self._backspace()
            return
        if text == "=":
            self.evaluate()
            return
        if text == "±":
            self._toggle_sign_whole_expr()
            return
        if text == "1/x":
            self._wrap_current("1/(%s)")
            self.evaluate()
            return
        if text == "x²":
            self._wrap_current("(%s)**2")
            self.evaluate()
            return
        if text == "√":
            self._wrap_current("sqrt(%s)")
            self.evaluate()
            return
        if text == "a/b":
            self._insert_text("/")
            return
        if text == "%":
            # percentagem simples: divide por 100 o último termo (ou toda a expressão)
            self._wrap_current("(%s)/100")
            self.evaluate()
            return

        # Operadores visuais -> expressão interna
        mapped = self.ops_map.get(text, text)
        self._insert_text(mapped)

    def _insert_text(self, s: str):
        self.display.setText(self.display.text() + s)

    def _clear(self, all_: bool = True):
        if all_:
            self.display.clear()
            self.result_label.setText("0")
            self.hint_label.clear()
        else:
            # CE: limpa apenas o campo de expressão
            self.display.clear()
        self.status.clearMessage()

    def _backspace(self):
        t = self.display.text()
        if t:
            self.display.setText(t[:-1])

    def _toggle_sign_whole_expr(self):
        t = self.display.text().strip()
        if not t:
            return
        # alterna sinal do conjunto da expressão: -( expr )
        if t.startswith("-(") and t.endswith(")"):
            self.display.setText(t[2:-1])
        elif t.startswith("-") and (t.count("(") == t.count(")")):
            # aproximação: se já começa com -, remove
            self.display.setText(t[1:])
        else:
            self.display.setText(f"-({t})")
        self.evaluate()

    def _wrap_current(self, pattern: str):
        t = self.display.text().strip()
        if not t:
            return
        self.display.setText(pattern % t)

    # -----------------------
    # Avaliação
    # -----------------------
    def evaluate(self):
        text = self.display.text().strip()
        if not text:
            return
        try:
            evaluator = SafeEvaluator(self.fraction_mode)
            result = evaluator.eval(text)

            if self.fraction_mode:
                # Mostrar resultado preferindo forma inteira/fração
                if isinstance(result, Fraction):
                    if result.denominator == 1:
                        self.result_label.setText(str(result.numerator))
                    else:
                        self.result_label.setText(f"{result.numerator}/{result.denominator}")
                    # aproximação decimal
                    approx = Decimal(result.numerator) / Decimal(result.denominator)
                    self.hint_label.setText(f"≈ {approx}")
                elif isinstance(result, Decimal):
                    self.result_label.setText(str(result))
                    self.hint_label.setText("")
                else:
                    # fallback
                    self.result_label.setText(str(result))
                    self.hint_label.setText("")
            else:
                # modo decimal: sempre Decimal
                if not isinstance(result, Decimal):
                    # converter para Decimal para consistência
                    result = evaluator._to_decimal(result)
                self.result_label.setText(str(result.normalize()))
                self.hint_label.setText("")

            self.status.showMessage("OK", 800)
        except ZeroDivisionError:
            self.result_label.setText("Erro: divisão por zero")
            self.hint_label.setText("")
        except Exception as e:
            self.result_label.setText(f"Erro: {e.__class__.__name__}")
            self.hint_label.setText("")

    def _update_status(self):
        self.status.showMessage(
            "Modo frações: ON" if self.fraction_mode else "Modo frações: OFF"
        )

    # -----------------------
    # Ajuda / Sobre
    # -----------------------
    def show_shortcuts(self):
        QMessageBox.information(
            self,
            "Teclas de atalho",
            (
                """
                • Dígitos e operadores: teclas normais (0–9, + - * / ( ) .)
                • Enter / Return: calcular (=)
                • Backspace: apagar último (⌫)
                • Esc: limpar (C)
                • Ctrl+C: copiar resultado
                • Ctrl+V: colar na expressão
                • Ver → Modo Frações: alterna entre Decimal e Fração
                """
            ).strip(),
        )

    def show_about(self):
        QMessageBox.about(
            self,
            "Sobre",
            (
                """
Calculadora Qt — PySide6\n\n"
                "Funcionalidades:\n"
                "• Operações básicas (+ − × ÷), potência (^), parênteses\n"
                "• Funções: √x, 1/x, x², percentagem\n"
                "• Modo Frações com resultado exato\n\n"
                "Licença: MIT\nAutor: exemplo educativo"
                """
            ).strip(),
        )

    # -----------------------
    # Tema claro/escuro (stylesheets simples)
    # -----------------------
    def apply_dark_theme(self):
        self.setStyleSheet(
            """
            QMainWindow { background: #121212; }
            QLabel#result { font-size: 22px; color: #e8e8e8; }
            QLabel#hint { font-size: 13px; color: #c3c3c3; }
            QLineEdit#display { font-size: 20px; padding: 6px; background: #1e1e1e; color: #fafafa; border: 1px solid #333; border-radius: 8px; }
            QPushButton#btn { font-size: 16px; padding: 8px; border-radius: 10px; }
            QPushButton#btn { background: #2a2a2a; color: #f5f5f5; border: 1px solid #3a3a3a; }
            QPushButton#btn:hover { background: #333; }
            QPushButton#btn:pressed { background: #3b3b3b; }
            QStatusBar { color: #cccccc; }
            """
        )

    def apply_light_theme(self):
        self.setStyleSheet(
            """
            QMainWindow { background: #fafafa; }
            QLabel#result { font-size: 22px; color: #222; }
            QLabel#hint { font-size: 13px; color: #666; }
            QLineEdit#display { font-size: 20px; padding: 6px; background: white; color: #111; border: 1px solid #ccc; border-radius: 8px; }
            QPushButton#btn { font-size: 16px; padding: 8px; border-radius: 10px; }
            QPushButton#btn { background: #ffffff; color: #222; border: 1px solid #ddd; }
            QPushButton#btn:hover { background: #f3f3f3; }
            QPushButton#btn:pressed { background: #e9e9e9; }
            QStatusBar { color: #333; }
            """
        )

    # -----------------------
    # Teclado físico
    # -----------------------
    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.evaluate()
            return
        if key == Qt.Key_Escape:
            self._clear(all_=True)
            return
        if key == Qt.Key_Backspace:
            self._backspace()
            return

        # aceitar dígitos, operadores e parênteses
        if text and text in "0123456789+-*/().^":
            self._insert_text(text)
            return

        # ignorar o resto
        super().keyPressEvent(event)


def main():
    import sys

    app = QApplication(sys.argv)
    w = CalculatorWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
