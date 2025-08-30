#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora científica Qt — PySide6
- Multiplataforma: Windows, Ubuntu, macOS
- Modo Frações (Fraction) e Modo Decimal (Decimal de alta precisão)
- Funções científicas: sin, cos, tan, asin, acos, atan, ln, log, exp, sqrt, factorial
- Constantes: pi, e
- Modo graus/radianos para trigonometria
- Memória: MC, MR, MS, M+
- Avaliador seguro usando AST (não usa eval para executar expressões arbitrárias)
"""

from __future__ import annotations
import ast
import math
from decimal import Decimal, getcontext
from fractions import Fraction
from typing import Any

# Qt imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QLabel, QStatusBar, QMessageBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

# Aumentar precisão decimal para resultados não-fracionários
getcontext().prec = 50


# -------------------------
# AVALIADOR SEGURO (AST)
# -------------------------
class SafeEvaluator:
    """
    Avaliador baseado em AST que aceita:
      - literais numéricos
      - operadores binários: + - * / % ** 
      - operadores unários: +a, -a
      - parênteses
      - chamadas de função (apenas de uma lista branca)
      - nomes constantes permitidos: pi, e
    Trabalha em dois modos:
      - fraction_mode = True: tenta usar Fraction sempre que possível
      - fraction_mode = False: usa Decimal para maior precisão decimal
    Além disso aceita flag degrees para funções trig (entrada/saída em graus quando True).
    """

    def __init__(self, fraction_mode: bool = False, degrees: bool = False):
        self.fraction_mode = fraction_mode
        self.degrees = degrees

    # ---------- conversões ----------
    def _to_decimal(self, n: Any) -> Decimal:
        """Converter vários tipos para Decimal de forma segura."""
        if isinstance(n, Decimal):
            return n
        if isinstance(n, int):
            return Decimal(n)
        if isinstance(n, float):
            return Decimal(str(n))
        if isinstance(n, Fraction):
            return Decimal(n.numerator) / Decimal(n.denominator)
        # fallback: converter pela string (cobre ex.: '3/2' não deveria acontecer)
        return Decimal(str(n))

    def _to_fraction(self, n: Any) -> Fraction:
        """Converter para Fraction quando possível."""
        if isinstance(n, Fraction):
            return n
        if isinstance(n, int):
            return Fraction(n, 1)
        if isinstance(n, Decimal):
            # construir Fraction a partir da string Decimal para evitar ruído binário
            return Fraction(str(n))
        if isinstance(n, float):
            return Fraction(n).limit_denominator(1_000_000)
        return Fraction(n)

    # ---------- operadores ----------
    def _binop(self, op, a, b):
        # decide o tipo de cálculo com base no modo
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
            # divisão verdadeira
            return A / B
        if isinstance(op, ast.Mod):
            return A % B
        if isinstance(op, ast.Pow):
            # potência: comportamento robusto para expoentes inteiros/fractionais
            if self.fraction_mode:
                # Fraction ** integer funciona, senão convertemos para Decimal
                if isinstance(B, Fraction) and B.denominator == 1:
                    return A ** B.numerator
                return self._to_decimal(A) ** self._to_decimal(B)
            else:
                return A ** B
        raise TypeError("Operador binário não suportado")

    def _unary(self, op, a):
        A = self._to_fraction(a) if self.fraction_mode else self._to_decimal(a)
        if isinstance(op, ast.UAdd):
            return +A
        if isinstance(op, ast.USub):
            return -A
        raise TypeError("Operador unário não suportado")

    # ---------- funções permitidas ----------
    def _call(self, func_name: str, args: list[Any]):
        """Mapa de funções seguras. Recebe argumentos como valores já avaliados (números)."""
        # auxiliar: converter para float para funções math (quando necessário)
        def to_float(x):
            if isinstance(x, Fraction):
                return x.numerator / x.denominator
            if isinstance(x, Decimal):
                return float(x)
            return float(x)

        # trig — respeita modo graus/radianos
        if func_name in ("sin", "cos", "tan"):
            x = args[0]
            val = to_float(x)
            if self.degrees:
                val = math.radians(val)
            if func_name == "sin":
                return Decimal(str(math.sin(val))) if not self.fraction_mode else Decimal(str(math.sin(val)))
            if func_name == "cos":
                return Decimal(str(math.cos(val)))
            if func_name == "tan":
                return Decimal(str(math.tan(val)))

        if func_name in ("asin", "acos", "atan"):
            x = args[0]
            val = to_float(x)
            if func_name == "asin":
                r = math.asin(val)
            elif func_name == "acos":
                r = math.acos(val)
            else:
                r = math.atan(val)
            if self.degrees:
                r = math.degrees(r)
            return Decimal(str(r))

        # raízes, exponenciais e logs
        if func_name == "sqrt":
            x = args[0]
            if self.fraction_mode:
                # tentar extrair raiz exata para Fraction quando possível
                X = self._to_fraction(x)
                num, den = X.numerator, X.denominator
                rn, rd = int(math.isqrt(num)), int(math.isqrt(den))
                if rn * rn == num and rd * rd == den:
                    return Fraction(rn, rd)
                # fallback: Decimal
                return self._to_decimal(X).sqrt()
            else:
                return self._to_decimal(x).sqrt()

        if func_name == "ln":
            # log natural
            x = self._to_decimal(args[0])
            return Decimal(str(math.log(float(x))))

        if func_name == "log":
            # log(x) -> base 10 ; log(x, base) -> custom base
            if len(args) == 1:
                x = float(args[0])
                return Decimal(str(math.log10(x)))
            elif len(args) == 2:
                x = float(args[0]); base = float(args[1])
                return Decimal(str(math.log(x, base)))
            else:
                raise TypeError("log() aceita 1 ou 2 argumentos")

        if func_name == "exp":
            x = float(args[0])
            return Decimal(str(math.exp(x)))

        if func_name in ("fact", "factorial"):
            # factorial: exige inteiro não negativo
            x = args[0]
            # aceitar Fraction/integer/Decimal coerente
            if isinstance(x, Fraction):
                if x.denominator != 1:
                    raise ValueError("factorial exige inteiro")
                n = x.numerator
            elif isinstance(x, Decimal):
                if x != x.to_integral_value():
                    raise ValueError("factorial exige inteiro")
                n = int(x)
            else:
                n = int(x)
            if n < 0:
                raise ValueError("factorial exige inteiro não negativo")
            return math.factorial(n)

        raise NameError(f"Função não permitida: {func_name}")

    # ---------- avaliação recursiva do AST ----------
    def eval(self, text: str) -> Any:
        """Converte a expressão textual para uma árvore AST e avalia-a."""
        # substituições amigáveis
        expr = (
            text.replace("×", "*")
                .replace("÷", "/")
                .replace("^", "**")
                .replace("√", "sqrt")
        )
        node = ast.parse(expr, mode="eval")
        return self._eval_node(node.body)

    def _eval_node(self, node: ast.AST) -> Any:
        # BinOp: expr op expr
        if isinstance(node, ast.BinOp):
            return self._binop(type(node.op), self._eval_node(node.left), self._eval_node(node.right))
        # UnaryOp: -expr
        if isinstance(node, ast.UnaryOp):
            return self._unary(type(node.op), self._eval_node(node.operand))
        # Numbers
        if isinstance(node, ast.Constant):
            return node.value
        # Parentheses handled by the tree structure
        # Names: permitir constantes como pi, e
        if isinstance(node, ast.Name):
            if node.id == "pi":
                return math.pi
            if node.id == "e":
                return math.e
            raise NameError(f"Nome não permitido: {node.id}")
        # Calls: func(arg, ...)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise NameError("Chamada inválida")
            func_name = node.func.id
            args = [self._eval_node(a) for a in node.args]
            return self._call(func_name, args)
        # Outros nós não permitidos
        raise TypeError(f"Elemento da expressão não suportado: {type(node).__name__}")


# -------------------------
# INTERFACE Qt (MAIN WINDOW)
# -------------------------
class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Científica — PySide6")
        self.resize(520, 680)

        # Estado global: memória, modos
        self.memory = 0.0
        self.fraction_mode = False
        self.degrees_mode = False

        # Widgets principais
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Visor de expressão (só leitura; input via botões/teclado)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFixedHeight(48)
        layout.addWidget(self.display)

        # Label do resultado (apresenta resultado/erros)
        self.result_label = QLabel("0")
        self.result_label.setAlignment(Qt.AlignRight)
        self.result_label.setFixedHeight(36)
        layout.addWidget(self.result_label)

        # Label de dica/approx (por ex. aproximação em modo frações)
        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignRight)
        self.hint_label.setFixedHeight(20)
        layout.addWidget(self.hint_label)

        # Grelha principal de botões (números / operações)
        grid_main = QGridLayout()
        layout.addLayout(grid_main)

        main_buttons = [
            ["MC", "MR", "MS", "M+", "CE", "C"],
            ["7", "8", "9", "÷", "(", ")"],
            ["4", "5", "6", "×", "^", "%"],
            ["1", "2", "3", "−", "1/x", "x²"],
            ["±", "0", ".", "=", "+", "a/b"],
        ]

        for r, row in enumerate(main_buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedHeight(48)
                btn.clicked.connect(lambda _, t=text: self.on_button_clicked(t))
                grid_main.addWidget(btn, r, c)

        # Grelha de funções científicas
        grid_sci = QGridLayout()
        layout.addLayout(grid_sci)

        sci_buttons = [
            ["sin", "cos", "tan", "asin", "acos", "atan"],
            ["ln", "log", "log(", "exp", "sqrt", "fact"],
            ["pi", "e", "Deg", "Rad", "FracMode", "Theme"]
        ]

        for r, row in enumerate(sci_buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedHeight(40)
                btn.clicked.connect(lambda _, t=text: self.on_sci_clicked(t))
                grid_sci.addWidget(btn, r, c)

        # Barra de estado
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_statusbar()

        # Menus: Ficheiro / Ver / Ajuda
        self._build_menus()

    # -----------------------
    # Menus
    # -----------------------
    def _build_menus(self):
        menubar = self.menuBar()

        # Ficheiro
        m_file = menubar.addMenu("&Ficheiro")
        act_quit = QAction("Sair", self)
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        # Ver: toggles
        m_view = menubar.addMenu("&Ver")
        act_frac = QAction("Modo Frações", self, checkable=True)
        act_frac.toggled.connect(self.toggle_fraction_mode)
        m_view.addAction(act_frac)

        act_deg = QAction("Usar Graus", self, checkable=True)
        act_deg.toggled.connect(self.toggle_degrees_mode)
        m_view.addAction(act_deg)

        # Ajuda
        m_help = menubar.addMenu("&Ajuda")
        act_about = QAction("Sobre", self)
        act_about.triggered.connect(self.show_about)
        m_help.addAction(act_about)

        act_shortcuts = QAction("Atalhos", self)
        act_shortcuts.triggered.connect(self.show_shortcuts)
        m_help.addAction(act_shortcuts)

    # -----------------------
    # Atualizar barra de estado
    # -----------------------
    def _update_statusbar(self):
        flags = []
        if self.fraction_mode:
            flags.append("Frações: ON")
        else:
            flags.append("Frações: OFF")
        flags.append("Graus" if self.degrees_mode else "Radianos")
        if abs(self.memory) > 1e-15:
            flags.append("M")
        self.status.showMessage(" | ".join(flags))

    # -----------------------
    # Interação Botões principais
    # -----------------------
    def on_button_clicked(self, text: str):
        # Funções de edição / especial
        if text == "C":
            self.display.clear()
            self.result_label.setText("0")
            self.hint_label.clear()
            return
        if text == "CE":
            self.display.clear()
            return
        if text == "⌫":
            self.display.setText(self.display.text()[:-1])
            return
        if text == "±":
            self._toggle_sign()
            return
        if text == "a/b":
            # inserir barra para criar fração rapidamente
            self._insert_text("/")
            return
        if text == "1/x":
            self._wrap_current("1/(%s)")
            return
        if text == "x²":
            self._wrap_current("(%s)**2")
            return
        if text == "%":
            self._wrap_current("(%s)/100")
            return
        if text == "=":
            self.evaluate()
            return

        # Memória
        if text in ("MC", "MR", "MS", "M+"):
            self._memory_action(text)
            return

        # operadores visuais -> expressão
        mapping = {"×": "*", "÷": "/", "−": "-"}
        mapped = mapping.get(text, text)
        self._insert_text(mapped)

    # -----------------------
    # Botões científicos
    # -----------------------
    def on_sci_clicked(self, text: str):
        if text == "Deg":
            # ligar modo graus
            self.degrees_mode = True
            self._update_statusbar()
            return
        if text == "Rad":
            self.degrees_mode = False
            self._update_statusbar()
            return
        if text == "FracMode":
            self.fraction_mode = not self.fraction_mode
            self._update_statusbar()
            return
        if text == "Theme":
            # placeholder para trocas de tema (poderás personalizar)
            self.status.showMessage("Tema: padrão", 2000)
            return

        # funções que inserem texto prontas para chamada
        if text in ("sin", "cos", "tan", "asin", "acos", "atan",
                    "ln", "log", "exp", "sqrt", "fact"):
            # inserir nome da função e parênteses para argumento
            if text == "fact":
                self._insert_text("factorial(")
            else:
                self._insert_text(text + "(")
            return

        if text == "log(":
            self._insert_text("log(")  # para log com base deixar inserir vírgula depois
            return

        if text in ("pi", "e"):
            self._insert_text(text)
            return

    # -----------------------
    # Inserção de texto no visor
    # -----------------------
    def _insert_text(self, s: str):
        self.display.setText(self.display.text() + s)

    def _wrap_current(self, pattern: str):
        t = self.display.text().strip()
        if not t:
            return
        self.display.setText(pattern % t)

    def _toggle_sign(self):
        t = self.display.text().strip()
        if not t:
            return
        if t.startswith("-(") and t.endswith(")"):
            self.display.setText(t[2:-1])
        elif t.startswith("-"):
            self.display.setText(t[1:])
        else:
            self.display.setText(f"-({t})")

    # -----------------------
    # Memória (MC, MR, MS, M+)
    # -----------------------
    def _memory_action(self, cmd: str):
        try:
            if cmd == "MC":
                self.memory = 0.0
            elif cmd == "MR":
                # mostrar memória no visor
                self.display.setText(str(self.memory))
            elif cmd == "MS":
                # guardar valor atual (avalia antes)
                val = self._safe_eval_display()
                self.memory = float(val)
            elif cmd == "M+":
                val = self._safe_eval_display()
                self.memory += float(val)
            self._update_statusbar()
        except Exception as e:
            self.result_label.setText("Erro Memória")
            self.hint_label.setText(str(e))

    # -----------------------
    # Avaliar expressão (usa SafeEvaluator)
    # -----------------------
    def _safe_eval_display(self):
        text = self.display.text().strip()
        if not text:
            return 0
        evaluator = SafeEvaluator(fraction_mode=self.fraction_mode, degrees=self.degrees_mode)
        return evaluator.eval(text)

    def evaluate(self):
        text = self.display.text().strip()
        if not text:
            return
        try:
            evaluator = SafeEvaluator(fraction_mode=self.fraction_mode, degrees=self.degrees_mode)
            result = evaluator.eval(text)

            # Apresentação do resultado dependendo do modo
            if self.fraction_mode and isinstance(result, Fraction):
                # exato como fração
                if result.denominator == 1:
                    self.result_label.setText(str(result.numerator))
                else:
                    self.result_label.setText(f"{result.numerator}/{result.denominator}")
                # aproximação decimal
                approx = Decimal(result.numerator) / Decimal(result.denominator)
                self.hint_label.setText(f"≈ {approx}")
            else:
                # normalizar e mostrar Decimal/float
                if isinstance(result, Fraction):
                    # converter para Decimal
                    result = Decimal(result.numerator) / Decimal(result.denominator)
                if isinstance(result, Decimal):
                    # retirar zeros finais quando possível
                    text_out = format(result.normalize(), 'f')
                else:
                    text_out = str(result)
                self.result_label.setText(text_out)
                self.hint_label.clear()

            self.status.showMessage("OK", 800)
        except ZeroDivisionError:
            self.result_label.setText("Erro: divisão por zero")
            self.hint_label.clear()
        except Exception as e:
            self.result_label.setText("Erro")
            self.hint_label.setText(type(e).__name__)

    # -----------------------
    # Ajuda / Sobre / Atalhos
    # -----------------------
    def show_about(self):
        QMessageBox.about(self, "Sobre",
                          "Calculadora Científica — PySide6\n\n"
                          "Operações básicas, frações, funções científicas e memória.\n"
                          "Modo Frações: armazena resultados racionais como Fraction.\n"
                          "Modo Graus: ativa conversão graus<->radianos para trigonometria.")

    def show_shortcuts(self):
        QMessageBox.information(self, "Atalhos",
                                "Teclas: números 0-9, operadores + - * / ( ) .\n"
                                "Enter = calcular, Esc = limpar, Backspace = apagar.\n"
                                "Ver -> Modo Frações / Usar Graus para alternar modos.")

# -------------------------
# Execução principal
# -------------------------
def main():
    import sys
    app = QApplication(sys.argv)
    w = CalculatorWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
