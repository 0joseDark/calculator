__Calculadora Qt__ (Windows, Ubuntu, macOS) — PySide6 

# como instalar

1. ter Python 3.9+ instalado (Windows, Ubuntu, macOS).
2. instalar Qt for Python:

```
pip install pyside6
```

# como executar

```
python calculadora_qt.py
```

(se o ficheiro tiver outro nome no teu PC, usa esse nome)

# o que vem incluído

* janelas Qt nativas (PySide6), menu e barra de estado.
* botões: 0–9, +, −, ×, ÷, parênteses, “a/b”, 1/x, x², √, %, ., ±, C, CE, ⌫ e =.
* modo Frações (resultado exato, p.ex. `1/3 + 1/6 = 1/2`) e modo Decimal (alta precisão com `Decimal`).
* potência com `^` (internamente usa `**`) e parênteses.
* etiqueta extra com “≈” para a aproximação decimal quando estás em Frações.
* tema claro/escuro no menu Ver.
* atalhos: dígitos/operadores pelo teclado, Enter (=), Backspace (⌫), Esc (C), Ctrl+C (copiar resultado), Ctrl+V (colar para a expressão).

# passo a passo (como está construído)

1. **Evaluator seguro (AST)**

   * O código não usa `eval`. Analisa a expressão com `ast` e só permite: números, `+ − * / **`, unários `+a`/`-a`, `()` e `sqrt(x)`.
   * Dois modos:

     * **Decimal**: tudo convertido para `Decimal` com precisão alta (50 dígitos).
     * **Frações**: tudo convertido para `Fraction`. Decimais, se usados, são aproximados a uma fração com denominador limitado.

2. **UI Qt**

   * `QMainWindow` com `QLineEdit` (expressão), `QLabel` (resultado), `QLabel` (≈ aproximação).
   * Grelha de botões. Mapeamento visual → expressão interna (ex.: `×`→`*`, `÷`→`/`, `√`→`sqrt`).
   * Menu:

     * **Ficheiro**: Sair.
     * **Editar**: Copiar resultado, Colar na expressão, Limpar.
     * **Ver**: alternar **Modo Frações** e **Tema Escuro**.
     * **Ajuda**: Atalhos e Sobre.

3. **Fluxo principal**

   * Ao carregar nos botões, o texto entra no campo de expressão.
   * `=` (ou Enter) chama o avaliador; se Frações estiver ativo, mostra forma `num/den` quando aplicável e a aproximação “≈ …”.
   * Tratamento de erros com mensagens amigáveis (ex.: divisão por zero).

4. **Funções úteis nos botões**

   * **CE**: limpa a caixa de expressão. **C**: limpa tudo (inclui resultado). **⌫**: apaga último carácter.
   * **±**: muda o sinal da expressão inteira (prático para calcular `-(...)`).
   * **1/x**, **x²**, **√**: envolvem a expressão atual (podes escrever o número e depois clicar a função).
   * **a/b**: insere `/` para criar frações rapidamente.
   * **%**: divide por 100 (percentagem simples) a expressão atual.

# exemplos rápidos

* **Frações ON** → escreve `1/3 + 1/6` → `=` → resultado: `1/2`, e “≈ 0.5”.
* **Decimais** → escreve `12.5 * (3 - 1.2)` → `=` → resultado decimal preciso.
* **Raiz** → escreve `9` → `√` → `=` → `3`.
* **Potência** → escreve `2^10` → `=` → `1024`.

# notas e dicas

* Em modo Frações, se usares decimais (tipo `0.1`), o programa tenta aproximar a uma fração “limpa”. Para resultados exatamente racionais, prefere escrever como `1/10`.
* A tecla `^` no teclado é aceite e convertida para `**` internamente.
* Se quiseres que funções como `√` atuem só sobre o último número, diz e eu adapto a lógica para “token atual”.

# (opcional) criar executável

* **Windows**:

  ```
  pip install pyinstaller
  pyinstaller --noconfirm --windowed --name CalculadoraQt calculadora_qt.py
  ```

  O executável fica em `dist/CalculadoraQt/`.
* **Ubuntu/macOS**: o comando é semelhante; no macOS podes precisar assinar/notarizar se fores distribuir.
