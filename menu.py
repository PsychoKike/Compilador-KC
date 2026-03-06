import os
from tkinter import Menu, PhotoImage
import tkinter
from file_operations import nuevo, abrir, guardar, guardar_como, cerrar_pestana_actual
from text_operations import copiar, cortar, pegar, seleccionar_todo
from font_operations import aumentar_fuente, disminuir_fuente

# Lista para mantener referencias globales a las imágenes
images = []

def resize_image(image_path, width, height):
    original_image = tkinter.PhotoImage(file=image_path)
    resized_image = original_image.subsample(width, height)
    images.append(resized_image)  # Mantener referencia global
    return resized_image

def get_current_text(editor_tabs):
    tab = editor_tabs.nametowidget(editor_tabs.select())
    for widget in tab.winfo_children():
        if isinstance(widget, tkinter.Frame):
            for child in widget.winfo_children():
                if isinstance(child, tkinter.Text):
                    return child
    return None

def create_menu(root, mensaje, editor_tabs):

    # Rutas de las imagenes
    img_new_path = os.path.abspath("img/new.png")
    img_open_path = os.path.abspath("img/open.png")
    img_save_path = os.path.abspath("img/save.png")
    img_save_as_path = os.path.abspath("img/save_as.png")
    img_quit_path = os.path.abspath("img/quit.png")

    img_copy_path = os.path.abspath("img/copiar.png")
    img_cut_path = os.path.abspath("img/cortar.png")
    img_paste_path = os.path.abspath("img/pegar.png")
    img_select_all_path = os.path.abspath("img/select_all.png")

    img_mas_path = os.path.abspath("img/mas.png")
    img_menos_path = os.path.abspath("img/menos.png")


    img_new = resize_image(img_new_path, 2, 2)
    img_open = resize_image(img_open_path, 2, 2)
    img_save = resize_image(img_save_path, 2, 2)
    img_save_as = resize_image(img_save_as_path, 2, 2)
    img_quit = resize_image(img_quit_path, 2, 2)

    img_copy = resize_image(img_copy_path, 2, 2)
    img_cut = resize_image(img_cut_path, 2, 2)
    img_paste = resize_image(img_paste_path, 2, 2)
    img_select_all = resize_image(img_select_all_path, 2, 2)

    img_mas = resize_image(img_mas_path, 2, 2)
    img_menos = resize_image(img_menos_path, 2, 2)

    # Menu superior
    menubar = Menu(root)

    # Menu de archivos
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Nuevo", 
                         accelerator="Ctrl+N",
                         command=lambda: nuevo(editor_tabs, mensaje),
                         image=img_new,
                         compound=tkinter.LEFT)
    filemenu.add_command(label="Abrir", 
                         accelerator="Ctrl+O", 
                         command=lambda: abrir(editor_tabs, mensaje),
                         image=img_open,
                         compound=tkinter.LEFT)
    filemenu.add_command(label="Guardar", 
                         accelerator="Ctrl+S", 
                         command=lambda: guardar(editor_tabs, mensaje),
                         image=img_save,
                         compound=tkinter.LEFT)
    filemenu.add_command(label="Guardar como", 
                         accelerator="Ctrl+Shift+S", 
                         command=lambda: guardar_como(editor_tabs, mensaje),
                         image=img_save_as,
                         compound=tkinter.LEFT)
    filemenu.add_separator()
    filemenu.add_command(label="Cerrar pestaña", 
                         accelerator="Ctrl+W", 
                         command=lambda: cerrar_pestana_actual(editor_tabs),
                         image=img_quit, # <--- Mismo símbolo
                         compound=tkinter.LEFT)

    filemenu.add_command(label="Salir", 
                         command=root.quit,
                         image=img_quit,
                         compound=tkinter.LEFT)
    # En menu.py, busca donde agregas la opción de cerrar:
        
    # Menu de editar
    editmenu = Menu(menubar, tearoff=0)
    editmenu.add_command(label="Copiar",
                         accelerator="Ctrl+C",
                         command=lambda: copiar(root, mensaje, get_current_text(editor_tabs)),
                         image=img_copy,
                         compound=tkinter.LEFT)
    editmenu.add_command(label="Cortar",
                         accelerator="Ctrl+X",
                         command=lambda: cortar(root, mensaje, get_current_text(editor_tabs)),
                         image=img_cut,
                         compound=tkinter.LEFT)
    editmenu.add_command(label="Pegar",
                         accelerator="Ctrl+V",
                         command=lambda: pegar(root, mensaje, get_current_text(editor_tabs)),
                         image=img_paste,
                         compound=tkinter.LEFT)
    editmenu.add_separator()
    editmenu.add_command(label="Seleccionar todo",
                         accelerator="Ctrl+A",
                         command=lambda: seleccionar_todo(root, mensaje, get_current_text(editor_tabs)),
                         image=img_select_all,
                         compound=tkinter.LEFT)

    
    # Menu fuente
    toolmenu = Menu(menubar, tearoff=0)
    toolmenu.add_command(label="Aumentar tamaño",
                         command=lambda: aumentar_fuente(get_current_text(editor_tabs)),
                         image=img_mas,
                         compound=tkinter.LEFT)
    toolmenu.add_command(label="Disminuir tamaño",
                         command= lambda: disminuir_fuente(get_current_text(editor_tabs)),
                         image=img_menos,
                         compound=tkinter.LEFT)

    # Asociar el atajo del teclado del menu

    # Menu de archivos
    root.bind("<Control-n>", lambda event: nuevo(editor_tabs, mensaje))
    root.bind("<Control-o>", lambda event: abrir(editor_tabs, mensaje))
    root.bind("<Control-s>", lambda event: guardar(editor_tabs, mensaje))
    root.bind("<Control-S>", lambda event: guardar_como(editor_tabs, mensaje))

    menubar.add_cascade(menu=filemenu, label="Archivo")
    menubar.add_cascade(menu=editmenu, label="Editar")
    menubar.add_cascade(menu=toolmenu, label="Herramientas")
    
    compilarmenu = Menu(menubar, tearoff=0)
    
    # Análisis Léxico
    compilarmenu.add_command(
        label="Análisis Léxico",
        accelerator="F5",
        command=lambda: run_command(
            editor_tabs, mensaje, 
            # Aquí pasas los frames/pantallas necesarios que requiere tu función run_command
            # Nota: Asegúrate de que estas variables estén disponibles en el scope o pasarlas como argumentos
            frame_lexico, pantalla_errores, frame_sintactico
        ),
        image=img_save, # Puedes reusar un icono o dejarlo sin image
        compound=tkinter.LEFT
    )
    
    # Análisis Sintáctico
    compilarmenu.add_command(
        label="Análisis Sintáctico",
        command=lambda: print("Ejecutando Sintáctico..."), # Aquí va tu función de sintaxis
        compound=tkinter.LEFT
    )
    
    # Análisis Semántico
    compilarmenu.add_command(
        label="Análisis Semántico",
        command=lambda: mensaje.set("Ejecutando análisis semántico..."),
        compound=tkinter.LEFT
    )
    
    compilarmenu.add_separator()
    
    # Generación de Código Intermedio
    compilarmenu.add_command(
        label="Generación de Código Intermedio",
        command=lambda: mensaje.set("Generando código intermedio..."),
        compound=tkinter.LEFT
    )
    
    # Ejecución
    compilarmenu.add_command(
        label="Ejecución",
        accelerator="F6",
        command=lambda: mensaje.set("Iniciando ejecución..."),
        image=img_new, # Ejemplo de reuso de icono
        compound=tkinter.LEFT
    )

    # =========================
    # Agregar las cascadas al menubar
    # =========================
    menubar.add_cascade(menu=filemenu, label="Archivo")
    menubar.add_cascade(menu=editmenu, label="Editar")
    menubar.add_cascade(menu=compilarmenu, label="Compilar") # <--- Nueva cascada
    menubar.add_cascade(menu=toolmenu, label="Herramientas")

    root.config(menu=menubar)

