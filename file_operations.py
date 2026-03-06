from tkinter import END, filedialog as FileDialog, ttk, Text
from io import open
from lexer import reset_lexer
from test_lexer import test_lexer
from sintac import calculate_levels, parse_code
from tab_widget import TabWithCloseButton

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
    editor_tabs.add(tab.main_frame, text=nombre + " ✕")
    
    
    if actualizar:
        tab.main_frame.after(100, actualizar)
    
    # Forzar un redibujado de los números de línea después de crear la pestaña
    tab.main_frame.after(3, lambda: tab.line_numbers.redraw() or tab.line_numbers.redraw())
    
    return tab.get_text_widget()



# ============================================
# NUEVO
# ============================================

def nuevo(editor_tabs, mensaje, actualizar=None):

    mensaje.set("Nuevo archivo")

    crear_pestana(editor_tabs, "Nuevo archivo", "", actualizar)
    


# ============================================
# ABRIR
# ============================================

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

    texto = crear_pestana(editor_tabs, nombre, contenido)

    tab = editor_tabs.select()

    ruta_archivos[str(tab)] = ruta

    mensaje.set("Archivo abierto")


# ============================================
# GUARDAR
# ============================================

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


# ============================================
# GUARDAR COMO
# ============================================

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
# MENSAJES EN ROJO
# ============================================

def mostrar_mensaje_en_rojo(pantalla_errores, mensaje):

    pantalla_errores.config(state='normal')

    pantalla_errores.insert(END, mensaje + '\n')

    pantalla_errores.tag_add("error", "end-2l", "end-1l")

    pantalla_errores.tag_config("error", foreground="red")

    pantalla_errores.config(state='disabled')

    pantalla_errores.see(END)


# ============================================
# ANALISIS LEXICO
# ============================================

def run_command(editor_tabs, mensaje, frame_lexico,
                pantalla_errores, frame_sintactico):

    texto = obtener_texto_actual(editor_tabs)

    if not texto:
        mensaje.set("No hay archivo abierto")
        return

    input_text = texto.get("1.0", "end-1c")

    mensaje.set("Ejecutando análisis léxico...")

    reset_lexer()

    for child in frame_lexico.winfo_children():
        child.destroy()

    tree = ttk.Treeview(
        frame_lexico,
        columns=('Token', 'Lexema', 'Fila', 'Columna'),
        show='headings'
    )

    tree.heading('Token', text='Token')
    tree.heading('Lexema', text='Lexema')
    tree.heading('Fila', text='Fila')
    tree.heading('Columna', text='Columna')

    tree.column('Token', width=150, anchor='center')
    tree.column('Lexema', width=150, anchor='center')
    tree.column('Fila', width=60, anchor='center')
    tree.column('Columna', width=60, anchor='center')

    tree.pack(fill='both', expand=True)

    tokens, errors = test_lexer(input_text, source='gui')

    for token in tokens:
        tree.insert(
            '',
            'end',
            values=(token.type, token.value, token.lineno, token.lexpos)
        )

    pantalla_errores.config(state='normal')
    pantalla_errores.delete("1.0", END)

    if errors:

        for error in errors:
            mostrar_mensaje_en_rojo(pantalla_errores, error[3])

        mensaje.set("Error en análisis léxico")

    else:

        mensaje.set("Análisis léxico completado")

        texto_tokens = tokens_to_text(tokens)

        run_syntax_analysis(
            mensaje,
            texto_tokens,
            frame_sintactico,
            pantalla_errores,
            tokens
        )

    pantalla_errores.config(state='disabled')


# ============================================
# ANALISIS SINTACTICO
# ============================================

def run_syntax_analysis(mensaje, texto,
                        frame_sintactico,
                        pantalla_errores,
                        tokens):

    mensaje.set("Ejecutando análisis sintáctico...")

    for child in frame_sintactico.winfo_children():
        child.destroy()

    tree = ttk.Treeview(
        frame_sintactico,
        columns=('Nodo', 'Nivel'),
        show='headings'
    )

    tree.heading('Nodo', text='Nodo')
    tree.heading('Nivel', text='Nivel')

    tree.column('Nodo', width=200)
    tree.column('Nivel', width=100)

    tree.pack(fill='both', expand=True)

    result, errors = parse_code(texto)

    if result:

        calculate_levels(result)

        def add_nodes(node, parent=''):

            item = tree.insert(
                parent,
                'end',
                values=(node.type, node.level)
            )

            for child in node.children:
                add_nodes(child, item)

        add_nodes(result)

        mensaje.set("Análisis sintáctico completado")

    else:

        pantalla_errores.config(state='normal')

        for error in errors:
            mostrar_mensaje_en_rojo(pantalla_errores, error)

        pantalla_errores.config(state='disabled')

        mensaje.set("Análisis sintáctico fallido")


# ============================================
# TOKENS A TEXTO
# ============================================

def tokens_to_text(tokens):

    return ' '.join(str(token.value) for token in tokens)


# ============================================
# HIGHLIGHT SINTAXIS (VERSIÓN RÁPIDA)
# ============================================

def highlight_syntax(texto):

    if not texto:
        return

    keywords = ['int', 'float', 'if', 'else', 'for', 'while', 'do']

    texto.tag_remove("keyword", "1.0", END)

    for kw in keywords:

        start = "1.0"

        while True:

            pos = texto.search(
                r'\y' + kw + r'\y',
                start,
                stopindex=END,
                regexp=True
            )

            if not pos:
                break

            end = f"{pos}+{len(kw)}c"

            texto.tag_add("keyword", pos, end)

            start = end

    texto.tag_config("keyword", foreground="blue")