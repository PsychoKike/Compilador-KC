# file_operations.py
from tkinter import END, filedialog as FileDialog, ttk, Frame, Text
from io import open
from lexer import reset_lexer
from test_lexer import test_lexer
from sintac import calculate_levels, parse_code
from tab_widget import TabWithCloseButton
from widgets import LineNumbers  # Solo importar LineNumbers

ruta_archivos = {}  # guarda la ruta de cada pestaña

# ============================================
# OBTENER EDITOR ACTIVO
# ============================================
def obtener_texto_actual(editor_tabs):
    """Obtiene el widget Text de la pestaña activa"""
    tab_id = editor_tabs.select()
    if not tab_id:
        return None

    tab = editor_tabs.nametowidget(tab_id)

    def buscar_text(widget):
        for child in widget.winfo_children():
            if isinstance(child, Text):
                return child
            resultado = buscar_text(child)
            if resultado:
                return resultado
        return None

    return buscar_text(tab)

# ============================================
# CREAR NUEVA PESTAÑA
# ============================================
def crear_pestana(editor_tabs, nombre="Nuevo archivo", contenido="", actualizar=None):
    """Crear una nueva pestaña simple"""
    tab = TabWithCloseButton(editor_tabs, nombre, contenido, actualizar)
    editor_tabs.select(tab.main_frame)
    
    if actualizar:
        tab.main_frame.after(100, actualizar)
    
    return tab.get_text_widget()

# ============================================
# NUEVO ARCHIVO
# ============================================
def nuevo(editor_tabs, mensaje, actualizar=None):
    mensaje.set("Nuevo archivo")
    crear_pestana(editor_tabs, "Nuevo archivo", "", actualizar)

# ============================================
# ABRIR ARCHIVO
# ============================================
def abrir(editor_tabs, mensaje):
    ruta = FileDialog.askopenfilename(
        initialdir=".",
        filetypes=(("Archivos de texto", "*.txt"),),
        title="Abrir archivo")

    if ruta != "":
        archivo = open(ruta, 'r', encoding='utf-8')
        contenido = archivo.read()
        archivo.close()

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
    ruta = ruta_archivos.get(str(tab), "")

    contenido = texto.get(1.0, 'end-1c')

    if ruta != "":
        archivo = open(ruta, 'w+', encoding='utf-8')
        archivo.write(contenido)
        archivo.close()
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

    # 1. Pedimos la RUTA (no el objeto archivo)
    ruta = FileDialog.asksaveasfilename(
        title="Guardar archivo",
        defaultextension=".txt",
        filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*"))
    )

    # 2. Si el usuario no canceló (ruta no está vacía)
    if ruta:
        try:
            contenido = texto.get(1.0, 'end-1c')
            # Aquí es donde aplicamos el encoding correctamente
            with open(ruta, 'w', encoding='utf-8') as archivo:
                archivo.write(contenido)

            tab = editor_tabs.select()
            ruta_archivos[str(tab)] = ruta

            nombre = ruta.split("/")[-1]
            editor_tabs.tab(tab, text=nombre)

            mensaje.set("Archivo guardado exitosamente")
        except Exception as e:
            mensaje.set(f"Error al guardar: {e}")

# ============================================
# MOSTRAR MENSAJES EN ROJO
# ============================================
def mostrar_mensaje_en_rojo(pantalla_errores, mensaje):
    pantalla_errores.config(state='normal', fg='red')
    pantalla_errores.insert('end', mensaje + '\n')
    pantalla_errores.config(state='disabled')
    pantalla_errores.see('end')

# ============================================
# ANALISIS LEXICO
# ============================================
def run_command(editor_tabs, mensaje, frame_lexico,
                pantalla_errores, frame_sintactico):

    texto = obtener_texto_actual(editor_tabs)

    if not texto:
        mensaje.set("No hay archivo abierto")
        return

    input_text = texto.get(1.0, 'end-1c')

    mensaje.set("Ejecutando análisis léxico...")

    reset_lexer()

    for child in frame_lexico.winfo_children():
        child.destroy()

    tree = ttk.Treeview(frame_lexico,
                        columns=('Token', 'Lexema', 'Fila', 'Columna'),
                        show='headings')

    tree.heading('Token', text='Token')
    tree.heading('Lexema', text='Lexema')
    tree.heading('Fila', text='Fila')
    tree.heading('Columna', text='Columna')

    tree.pack(fill='both', expand=True)

    tree.column('Token', width=150, anchor='center')
    tree.column('Lexema', width=150, anchor='center')
    tree.column('Fila', width=50, anchor='center')
    tree.column('Columna', width=50, anchor='center')

    tokens, errors = test_lexer(input_text, source='gui')

    if tokens:
        for token in tokens:
            token_data = (token.type, token.value,
                          token.lineno, token.lexpos)
            tree.insert('', 'end', values=token_data)

    pantalla_errores.config(state='normal')
    pantalla_errores.delete(1.0, END)

    if errors:
        for error in errors:
            mostrar_mensaje_en_rojo(pantalla_errores, error[3])
        mensaje.set("Error en análisis léxico")
        pantalla_errores.config(state='disabled')
    else:
        mensaje.set("Análisis léxico completado")
        pantalla_errores.config(state='disabled')

        texto_tokens = tokens_to_text(tokens)
        run_syntax_analysis(mensaje, texto_tokens,
                            frame_sintactico,
                            pantalla_errores,
                            tokens)

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

    tree = ttk.Treeview(frame_sintactico,
                        columns=('Nodo', 'Nivel'),
                        show='headings')

    tree.heading('Nodo', text='Nodo')
    tree.heading('Nivel', text='Nivel')

    tree.pack(fill='both', expand=True)

    tree.column('Nodo', width=150, anchor='center')
    tree.column('Nivel', width=150, anchor='center')

    result, errors = parse_code(texto)

    if result:
        calculate_levels(result)

        def add_nodes(tree, node, parent=''):
            tree.insert(parent, 'end',
                        text=str(node),
                        values=(node.type, node.level))
            for child in node.children:
                add_nodes(tree, child, parent)

        add_nodes(tree, result)
        mensaje.set("Análisis sintáctico completado")
    else:
        pantalla_errores.config(state='normal')
        if errors:
            for error in errors:
                mostrar_mensaje_en_rojo(pantalla_errores, error)
        pantalla_errores.config(state='disabled')
        mensaje.set("Análisis sintáctico fallido")

# ============================================
# CONVERTIR TOKENS A TEXTO
# ============================================
def tokens_to_text(tokens):
    return ' '.join(str(token.value) for token in tokens)

# ============================================
# RESALTADO DE SINTAXIS
# ============================================
def highlight_syntax(texto):
    """Versión optimizada de highlight_syntax"""
    if not texto or not texto.winfo_exists():
        return
    
    keywords = ['int', 'float', 'if', 'else', 'for', 'while', 'do']
    
    try:
        texto.tag_configure('keyword', foreground='blue')
        texto.tag_configure('string', foreground='#ba6b2b')
        texto.tag_configure('comment_line', foreground='green')
        texto.tag_configure('comment_block', foreground='green')
    except:
        pass
    
    texto.tag_remove('keyword', '1.0', 'end')
    texto.tag_remove('string', '1.0', 'end')
    texto.tag_remove('comment_line', '1.0', 'end')
    texto.tag_remove('comment_block', '1.0', 'end')
    
    for kw in keywords:
        start = '1.0'
        while True:
            start = texto.search(r'\y' + kw + r'\y', start, stopindex='end', regexp=True)
            if not start:
                break
            end = f"{start}+{len(kw)}c"
            texto.tag_add('keyword', start, end)
            start = end

    texto.tag_configure('keyword', foreground='blue')
    texto.tag_configure('string', foreground='#ba6b2b')
    texto.tag_configure('comment_line', foreground='green')
    texto.tag_configure('comment_block', foreground='green')