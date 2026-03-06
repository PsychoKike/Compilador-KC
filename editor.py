import tkinter as tk
from tkinter import ttk, StringVar, Label

from file_operations import (
    obtener_texto_actual,
    crear_pestana,
    cerrar_pestana_actual,
)

from menu import create_menu
from buttons import create_buttons


# =========================
# VARIABLES GLOBALES
# =========================

root = None
editor_tabs = None
coord_label = None


# =========================
# ACTUALIZAR COORDENADAS
# =========================

def actualizar_coordenadas(texto, label):

    try:

        linea, columna = texto.index("insert").split(".")

        contenido = texto.get("1.0", "end-1c")

        total_lineas = contenido.count("\n") + 1

        caracteres = len(
            contenido.replace(" ", "")
                     .replace("\n", "")
                     .replace("\t", "")
        )

        label.config(
            text=f"Línea: {linea}   Col: {int(columna)+1}   Total líneas: {total_lineas}   Caracteres: {caracteres}"
        )

    except:
        pass


# =========================
# ACTUALIZACIÓN GENERAL
# =========================

def actualizar(event=None):

    texto_actual = obtener_texto_actual(editor_tabs)

    if texto_actual:
        actualizar_coordenadas(texto_actual, coord_label)


# =========================
# CERRAR PESTAÑA
# =========================

def cerrar_pestana(editor_tabs):
    # Obtenemos cuántas pestañas hay
    tabs = editor_tabs.tabs()
    
    if len(tabs) > 1:
        actual = editor_tabs.select()
        editor_tabs.forget(actual)
        # Después de cerrar, forzamos la actualización de coordenadas
        actualizar() 
    else:
        from tkinter import messagebox
        messagebox.showwarning("Cerrar archivo", "No puedes cerrar todas las pestañas. Debe quedar al menos una abierta.")


# =========================
# CREAR EDITOR PRINCIPAL
# =========================

def create_editor():

    global root, editor_tabs, coord_label

    root = tk.Tk()

    root.title("Compilador KC")
    root.geometry("1200x800")

    # =========================
    # FRAME BOTONES
    # =========================

    button_frame = tk.Frame(root)
    button_frame.pack(side="top", fill="x")

    # =========================
    # FRAME PRINCIPAL
    # =========================

    frame_principal = tk.Frame(root)
    frame_principal.pack(fill="both", expand=True)

    # =========================
    # FRAME EDITOR CON BOTÓN DE CERRAR
    # =========================

    frame_editor = tk.Frame(frame_principal)
    frame_editor.pack(side="left", fill="both", expand=True)

    # Frame superior para el notebook y botón de cerrar
    tab_frame = tk.Frame(frame_editor)
    tab_frame.pack(fill="x")

    # Notebook (pestañas)
    editor_tabs = ttk.Notebook(tab_frame)
    editor_tabs.pack(side="left", fill="x", expand=True)

    close_button = tk.Button(
        tab_frame,
        text="✖",
        font=("Arial", 12, "bold"),
        fg="red",
        bd=10,
        padx=10,
        command=lambda: cerrar_pestana_actual(editor_tabs, actualizar)
    )
    close_button.pack(side="right", padx=(5, 5), pady=5)

    # Bind para cambiar de pestaña
    editor_tabs.bind("<<NotebookTabChanged>>", actualizar)

    # Bind para cerrar con Ctrl+W
    root.bind("<Control-w>", lambda e: cerrar_pestana_actual(editor_tabs, actualizar))
    root.bind("<Control-W>", lambda e: cerrar_pestana_actual(editor_tabs, actualizar))

    # =========================
    # BARRA DE COORDENADAS
    # =========================

    coord_frame = tk.Frame(root, bg="#e0e0e0", height=25)
    coord_frame.pack(fill="x")

    coord_label = Label(
        coord_frame,
        text="Línea: 1   Col: 1   Total líneas: 1   Caracteres: 0",
        font=("Consolas", 9),
        bg="#e0e0e0",
        anchor="w"
    )

    coord_label.pack(side="left", padx=10)

    # =========================
    # CREAR PRIMER ARCHIVO
    # =========================

    crear_pestana(editor_tabs, "Nuevo archivo", "")
    
    # Actualizar coordenadas iniciales
    actualizar()

    # =========================
    # PANEL DERECHO (ANÁLISIS)
    # =========================

    frame_derecha = tk.Frame(frame_principal)
    frame_derecha.pack(side="right", fill="both", expand=True)

    analisis_tabs = ttk.Notebook(frame_derecha)

    frame_lexico = tk.Frame(analisis_tabs)
    frame_sintactico = tk.Frame(analisis_tabs)
    frame_semantico = tk.Frame(analisis_tabs)
    frame_hash = tk.Frame(analisis_tabs)
    frame_intermedio = tk.Frame(analisis_tabs)

    analisis_tabs.add(frame_lexico, text="Análisis Léxico")
    analisis_tabs.add(frame_sintactico, text="Análisis Sintáctico")
    analisis_tabs.add(frame_semantico, text="Semántico")
    analisis_tabs.add(frame_hash, text="Hash Table")
    analisis_tabs.add(frame_intermedio, text="Cód. Intermedio")

    analisis_tabs.pack(fill="both", expand=True)

    # =========================
    # MENSAJES
    # =========================

    mensaje = StringVar()
    mensaje.set("Bienvenido a Compilador KC")

    monitor = Label(root, textvariable=mensaje, font=("Consolas", 9))
    monitor.pack(side="bottom", anchor="w", padx=10)

    # =========================
    # NOTEBOOK DE SALIDA
    # =========================

    notebook_output = ttk.Notebook(root)
    notebook_output.config(height=180)
    notebook_output.pack(side="bottom", fill="x")

    frame_results = tk.Frame(notebook_output)
    frame_err_lex = tk.Frame(notebook_output)
    frame_err_sin = tk.Frame(notebook_output)
    frame_err_sem = tk.Frame(notebook_output)

    notebook_output.add(frame_results, text="Resultados")
    notebook_output.add(frame_err_lex, text="Err. Léxicos")
    notebook_output.add(frame_err_sin, text="Err. Sintácticos")
    notebook_output.add(frame_err_sem, text="Err. Semánticos")

    pantalla_resultados = tk.Text(frame_results)
    pantalla_resultados.pack(fill="both", expand=True)

    pantalla_errores = tk.Text(frame_err_lex)
    pantalla_errores.pack(fill="both", expand=True)

    # =========================
    # MENÚ
    # =========================

    create_menu(root, mensaje, editor_tabs)

    create_buttons(
        button_frame,
        editor_tabs,
        mensaje,
        pantalla_errores,
        frame_lexico,
        frame_sintactico,
        frame_semantico,
        frame_hash,
        frame_intermedio
    )

    # =========================
    # LOOP DE ACTUALIZACIÓN
    # =========================

    def loop_actualizacion():

        texto_actual = obtener_texto_actual(editor_tabs)

        if texto_actual:
            actualizar_coordenadas(texto_actual, coord_label)

        root.after(16, loop_actualizacion)

    loop_actualizacion()

    root.mainloop()


# =========================
# EJECUTAR
# =========================

if __name__ == "__main__":
    create_editor()