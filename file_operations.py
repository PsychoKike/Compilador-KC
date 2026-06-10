from tkinter import END, filedialog as FileDialog, ttk, Text
from io import open
from lexer import reset_lexer
from test_lexer import test_lexer
from sintac import calculate_levels, parse_code
from tab_widget import TabWithCloseButton
import tkinter as tk

ruta_archivos = {}

# ============================================
# OBTENER EDITOR ACTIVO
# ============================================

def obtener_texto_actual(editor_tabs):
    tab_id = editor_tabs.select()
    if not tab_id:
        return None
    tab = editor_tabs.nametowidget(tab_id)

    def buscar(widget):
        for child in widget.winfo_children():
            if isinstance(child, Text):
                return child
            resultado = buscar(child)
            if resultado:
                return resultado
        return None

    return buscar(tab)


# ============================================
# CREAR PESTAÑA
# ============================================

def crear_pestana(editor_tabs, nombre="Nuevo archivo", contenido="", actualizar=None):
    tab = TabWithCloseButton(editor_tabs, nombre, contenido, actualizar)
    editor_tabs.select(tab.main_frame)
    if actualizar:
        tab.main_frame.after(100, actualizar)
    tab.main_frame.after(3, lambda: tab.line_numbers.redraw() or tab.line_numbers.redraw())
    text_widget = tab.get_text_widget()
    text_widget.bind("<KeyRelease>", lambda e: highlight_syntax(text_widget))
    tab.main_frame.after(100, lambda: highlight_syntax(text_widget))


# ============================================
# CERRAR PESTAÑA ACTUAL
# ============================================

def cerrar_pestana_actual(editor_tabs, actualizar=None):
    if len(editor_tabs.tabs()) > 1:
        actual = editor_tabs.select()
        editor_tabs.forget(actual)
        if actualizar:
            actualizar()
        return True
    else:
        from tkinter import messagebox
        messagebox.showwarning(
            "Cerrar archivo",
            "No puedes cerrar todas las pestañas.\nDebe quedar al menos una abierta."
        )
        return False


# ============================================
# NUEVO / ABRIR / GUARDAR
# ============================================

def nuevo(editor_tabs, mensaje, actualizar=None):
    mensaje.set("Nuevo archivo")
    crear_pestana(editor_tabs, "Nuevo archivo", "", actualizar)


def abrir(editor_tabs, mensaje):
    ruta = FileDialog.askopenfilename(
        initialdir=".",
        title="Abrir archivo",
        filetypes=(("Archivos de texto", "*.txt"), ("Todos", "*.*"))
    )
    if not ruta:
        return
    with open(ruta, 'r', encoding='latin-1') as archivo:
        contenido = archivo.read()
    nombre = ruta.split("/")[-1]
    crear_pestana(editor_tabs, nombre, contenido)
    tab = editor_tabs.select()
    ruta_archivos[str(tab)] = ruta
    mensaje.set("Archivo abierto")


def guardar(editor_tabs, mensaje):
    texto = obtener_texto_actual(editor_tabs)
    if not texto:
        return
    tab = editor_tabs.select()
    ruta = ruta_archivos.get(str(tab))
    contenido = texto.get("1.0", "end-1c")
    if ruta:
        with open(ruta, 'w', encoding='utf-8') as archivo:
            archivo.write(contenido)
        mensaje.set("Archivo guardado")
    else:
        guardar_como(editor_tabs, mensaje)


def guardar_como(editor_tabs, mensaje):
    texto = obtener_texto_actual(editor_tabs)
    if not texto:
        return
    ruta = FileDialog.asksaveasfilename(
        title="Guardar archivo",
        defaultextension=".txt",
        filetypes=(("Archivos de texto", "*.txt"), ("Todos", "*.*"))
    )
    if not ruta:
        return
    contenido = texto.get("1.0", "end-1c")
    with open(ruta, 'w', encoding='utf-8') as archivo:
        archivo.write(contenido)
    tab = editor_tabs.select()
    ruta_archivos[str(tab)] = ruta
    nombre = ruta.split("/")[-1]
    editor_tabs.tab(tab, text=nombre)
    mensaje.set("Archivo guardado correctamente")


# ============================================
# PANEL GENÉRICO DE ERRORES (tabla con
# Tipo | Línea | Columna | Descripción)
# ============================================

def build_error_panel(frame, errors, titulo="⚠️  Errores"):
    """
    errors: lista de tuplas (tipo, linea, columna, descripcion)
    o lista de strings (se parsean automáticamente).
    """
    for child in frame.winfo_children():
        child.destroy()

    color_bg  = "#1e1e2e"
    color_fg  = "#f38ba8"
    color_ok  = "#a6e3a1"

    header = tk.Label(
        frame,
        text=f"{titulo}  ({len(errors)} encontrados)",
        font=("Consolas", 10, "bold"),
        bg=color_bg, fg=color_fg if errors else color_ok,
        pady=6, anchor="w", padx=8
    )
    header.pack(fill="x")

    cols = ("tipo", "linea", "columna", "descripcion")
    tree = ttk.Treeview(frame, columns=cols, show="headings")

    tree.heading("tipo",        text="Tipo")
    tree.heading("linea",       text="Línea")
    tree.heading("columna",     text="Columna")
    tree.heading("descripcion", text="Descripción")

    tree.column("tipo",        width=120, anchor="center")
    tree.column("linea",       width=70,  anchor="center")
    tree.column("columna",     width=70,  anchor="center")
    tree.column("descripcion", width=500, anchor="w")

    vsb = tk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    tree.tag_configure("err", foreground="#f38ba8")
    tree.tag_configure("ok",  foreground="#a6e3a1")

    if not errors:
        tree.insert("", "end",
                    values=("✓", "-", "-", "Sin errores detectados"),
                    tags=("ok",))
        return

    import re
    for err in errors:
        if isinstance(err, (tuple, list)):
            if len(err) == 4:
                # Léxico: (lexema, linea, col, mensaje)
                _, linea, col, desc = err
                tipo = "Léxico"
            elif len(err) == 3:
                # Sintáctico: (linea, col, mensaje)
                linea, col, desc = err
                tipo = "Sintáctico"
            else:
                linea, col, desc, tipo = "-", "-", str(err), "?"
        else:
            # String plano — intentar extraer línea y columna
            desc  = err
            linea = "-"
            col   = "-"
            tipo  = "Sintáctico"
            m = re.search(r'línea\s+(\d+),\s*columna\s+(\w+)', err)
            if m:
                linea = m.group(1)
                col   = m.group(2)

        tree.insert("", "end",
                    values=(tipo, linea, col, desc),
                    tags=("err",))


# ============================================
# ÁRBOL COLAPSABLE (AST)
# ============================================

def build_tree_view(frame, ast_root):
    for child in frame.winfo_children():
        child.destroy()

    color_bg = "#1e1e2e"

    header = tk.Label(
        frame,
        text="🌲  Árbol Sintáctico Abstracto (AST)",
        font=("Consolas", 10, "bold"),
        bg=color_bg, fg="#cdd6f4",
        pady=6, anchor="w", padx=8
    )
    header.pack(fill="x")

    vsb = tk.Scrollbar(frame, orient="vertical")
    hsb = tk.Scrollbar(frame, orient="horizontal")

    tree = ttk.Treeview(
        frame,
        columns=("tipo", "hoja", "nivel"),
        show="tree headings",
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
        selectmode="browse"
    )

    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    tree.heading("#0",    text="Nodo")
    tree.heading("tipo",  text="Tipo")
    tree.heading("hoja",  text="Lexema / Valor")
    tree.heading("nivel", text="Nivel")

    tree.column("#0",    width=220, stretch=True)
    tree.column("tipo",  width=140, anchor="center")
    tree.column("hoja",  width=140, anchor="center")
    tree.column("nivel", width=70,  anchor="center")

    tree.tag_configure("level1", background="#181825", foreground="#cba6f7")
    tree.tag_configure("level2", background="#1e1e2e", foreground="#89b4fa")
    tree.tag_configure("level3", background="#181825", foreground="#a6e3a1")
    tree.tag_configure("level4", background="#1e1e2e", foreground="#f9e2af")
    tree.tag_configure("levelN", background="#181825", foreground="#cdd6f4")

    def insert_node(parent_id, node):
        if node is None:
            return
        label = f"{node.type}: {node.leaf}" if node.leaf is not None else node.type
        level = node.level
        tag   = f"level{level}" if level <= 4 else "levelN"
        item_id = tree.insert(
            parent_id, "end",
            text=label,
            values=(node.type,
                    str(node.leaf) if node.leaf is not None else "",
                    str(level)),
            tags=(tag,),
            open=(level <= 2)
        )
        for child in node.children:
            if child is not None:
                insert_node(item_id, child)

    if ast_root:
        calculate_levels(ast_root)
        insert_node("", ast_root)

    # Botones expandir / colapsar
    btn_frame = tk.Frame(frame, bg="#313244")
    btn_frame.pack(fill="x", pady=2)

    def expandir_todo():
        def expand(item):
            tree.item(item, open=True)
            for c in tree.get_children(item):
                expand(c)
        for item in tree.get_children():
            expand(item)

    def colapsar_todo():
        def collapse(item):
            tree.item(item, open=False)
            for c in tree.get_children(item):
                collapse(c)
        for item in tree.get_children():
            collapse(item)

    btn_style = dict(bg="#45475a", fg="#cdd6f4", relief="flat",
                     padx=8, pady=2, font=("Consolas", 9))
    tk.Button(btn_frame, text="⊞ Expandir todo",
              command=expandir_todo, **btn_style).pack(side="left", padx=4, pady=2)
    tk.Button(btn_frame, text="⊟ Colapsar todo",
              command=colapsar_todo, **btn_style).pack(side="left", padx=4, pady=2)


def count_nodes(node):
    if node is None:
        return 0
    return 1 + sum(count_nodes(c) for c in node.children)


# ============================================
# ANÁLISIS LÉXICO + SINTÁCTICO
# ============================================

def run_command(editor_tabs, mensaje, frame_lexico,
                pantalla_errores, frame_sintactico,
                frame_err_sin=None, frame_err_lex=None):
    """
    Ejecuta léxico Y sintáctico siempre.
    Los errores léxicos van a frame_err_lex (o pantalla_errores).
    Los errores sintácticos van a frame_err_sin.
    Ambos paneles usan tabla con Tipo | Línea | Columna | Descripción.
    """
    texto = obtener_texto_actual(editor_tabs)
    if not texto:
        mensaje.set("No hay archivo abierto")
        return

    input_text = texto.get("1.0", "end-1c")
    reset_lexer()

    # ── LÉXICO ──────────────────────────────────
    mensaje.set("Ejecutando análisis léxico...")

    for child in frame_lexico.winfo_children():
        child.destroy()

    # Tabla de tokens reconocidos
    tok_tree = ttk.Treeview(
        frame_lexico,
        columns=('Token', 'Lexema', 'Línea', 'Columna'),
        show='headings'
    )
    tok_tree.heading('Token',   text='Token')
    tok_tree.heading('Lexema',  text='Lexema')
    tok_tree.heading('Línea',   text='Línea')
    tok_tree.heading('Columna', text='Columna')
    tok_tree.column('Token',   width=150, anchor='center')
    tok_tree.column('Lexema',  width=150, anchor='center')
    tok_tree.column('Línea',   width=70,  anchor='center')
    tok_tree.column('Columna', width=70,  anchor='center')

    vsb_lex = ttk.Scrollbar(frame_lexico, orient="vertical", command=tok_tree.yview)
    tok_tree.configure(yscrollcommand=vsb_lex.set)
    vsb_lex.pack(side="right", fill="y")
    tok_tree.pack(fill='both', expand=True)

    tokens, lex_errors = test_lexer(input_text, source='gui')

    for token in tokens:
        tok_tree.insert('', 'end',
                        values=(token.type, token.value,
                                token.lineno, token.lexpos))

    # Mostrar errores léxicos en su panel
    # lex_errors es lista de (lexema, linea, col, mensaje)
    if frame_err_lex is not None:
        build_error_panel(frame_err_lex, lex_errors, "⚠️  Errores Léxicos")
    else:
        # Fallback: pantalla_errores legacy (tk.Text)
        pantalla_errores.config(state='normal')
        pantalla_errores.delete("1.0", END)
        for err in lex_errors:
            mostrar_mensaje_en_rojo(pantalla_errores, err[3])
        pantalla_errores.config(state='disabled')

    if lex_errors:
        mensaje.set(f"⚠️  Análisis léxico: {len(lex_errors)} error(es) – continuando con sintáctico...")
    else:
        mensaje.set("✅ Análisis léxico completado – ejecutando análisis sintáctico...")

    # ── SINTÁCTICO (siempre se ejecuta) ─────────
    # Pasamos el código fuente ORIGINAL, no tokens reconstruidos,
    # para que PLY conserve líneas y columnas reales.
    run_syntax_analysis(
        mensaje,
        input_text,          # <-- código fuente original
        frame_sintactico,
        pantalla_errores,
        tokens,
        frame_err_sin=frame_err_sin,
        lex_had_errors=bool(lex_errors)
    )


def run_syntax_analysis(mensaje, texto, frame_sintactico,
                        pantalla_errores, tokens,
                        frame_err_sin=None, lex_had_errors=False):

    mensaje.set("Ejecutando análisis sintáctico...")

    for child in frame_sintactico.winfo_children():
        child.destroy()

    result, sin_errors = parse_code(texto)

    # Panel de errores sintácticos
    # sin_errors es lista de strings con "línea X, columna Y"
    if frame_err_sin is not None:
        build_error_panel(frame_err_sin, sin_errors, "⚠️  Errores Sintácticos")

    # result siempre existe (árbol completo o parcial con nodos de error)
    calculate_levels(result)
    build_tree_view(frame_sintactico, result)
    nodos = count_nodes(result)

    if sin_errors:
        mensaje.set(f"⚠️  AST parcial – {len(sin_errors)} error(es) | {nodos} nodos")
    elif lex_had_errors:
        mensaje.set(f"⚠️  AST construido con advertencias léxicas | {nodos} nodos")
    else:
        mensaje.set(f"✅ Análisis completo sin errores | {nodos} nodos en el AST")


# ============================================
# TOKENS A TEXTO
# ============================================

def tokens_to_text(tokens):
    return ' '.join(str(token.value) for token in tokens)


# ============================================
# MOSTRAR ERROR EN TEXT WIDGET (legacy)
# ============================================

def mostrar_mensaje_en_rojo(pantalla_errores, mensaje_txt):
    pantalla_errores.config(state='normal')
    pantalla_errores.insert(END, mensaje_txt + '\n')
    pantalla_errores.tag_add("error", "end-2l", "end-1l")
    pantalla_errores.tag_config("error", foreground="red")
    pantalla_errores.config(state='disabled')
    pantalla_errores.see(END)


# ============================================
# HIGHLIGHT SINTAXIS
# ============================================

def highlight_syntax(texto):
    import re

    content = texto.get("1.0", "end-1c")

    tags = ["number", "identifier", "comment",
            "keyword", "arith", "logic_rel",
            "symbol", "assign", "string"]

    for tag in tags:
        texto.tag_remove(tag, "1.0", "end")

    texto.tag_config("number",     foreground="#18B2CD")
    texto.tag_config("identifier", foreground="#343CDA")
    texto.tag_config("comment",    foreground="#A6A6A6")
    texto.tag_config("keyword",    foreground="#1D415E")
    texto.tag_config("arith",      foreground="#C97C34")
    texto.tag_config("logic_rel",  foreground="#C586C0")
    texto.tag_config("symbol",     foreground="#D4D4D4")
    texto.tag_config("assign",     foreground="#12390A")
    texto.tag_config("string",     foreground="#CE9178")

    keywords = [
        'main', 'if', 'else', 'then', 'end',
        'while', 'do', 'break',
        'int', 'float', 'bool',
        'true', 'false',
        'cin', 'cout',
        'and', 'or', 'not',
        'read', 'write',
    ]

    comment_ranges = []
    for match in re.finditer(r'//.*|/\*[\s\S]*?\*/', content):
        texto.tag_add("comment",
                      f"1.0 + {match.start()}c",
                      f"1.0 + {match.end()}c")
        comment_ranges.append((match.start(), match.end()))

    def in_comment(pos):
        return any(s <= pos < e for s, e in comment_ranges)

    for match in re.finditer(r'"[^"]*"', content):
        if not in_comment(match.start()):
            texto.tag_add("string",
                          f"1.0 + {match.start()}c",
                          f"1.0 + {match.end()}c")

    for kw in keywords:
        for match in re.finditer(r'\b' + kw + r'\b', content):
            if not in_comment(match.start()):
                texto.tag_add("keyword",
                              f"1.0 + {match.start()}c",
                              f"1.0 + {match.end()}c")

    patterns = [
        ("number",    r'\b\d+(\.\d+)?\b'),
        ("arith",     r'\+\+|--|\+|-|\*|/|%|\^'),
        ("logic_rel", r'<=|>=|==|!=|<|>|\|\||&&|!|<<|>>'),
        ("assign",    r'(?<!=)=(?!=)'),
        ("symbol",    r'[\(\)\{\},;]'),
    ]

    for tag, pattern in patterns:
        for match in re.finditer(pattern, content):
            if not in_comment(match.start()):
                texto.tag_add(tag,
                              f"1.0 + {match.start()}c",
                              f"1.0 + {match.end()}c")

    for match in re.finditer(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content):
        if not in_comment(match.start()):
            if match.group() not in keywords:
                texto.tag_add("identifier",
                              f"1.0 + {match.start()}c",
                              f"1.0 + {match.end()}c")