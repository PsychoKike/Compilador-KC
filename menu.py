import os
from tkinter import Menu, PhotoImage
import tkinter
from file_operations import nuevo, abrir, guardar, guardar_como
from text_operations import copiar, cortar, pegar, seleccionar_todo
from font_operations import aumentar_fuente, disminuir_fuente

# Lista para mantener referencias globales a las imágenes
images = []

def resize_image(image_path, width, height):
    original_image = tkinter.PhotoImage(file=image_path)
    resized_image = original_image.subsample(width, height)
    images.append(resized_image)  # Mantener referencia global
    return resized_image

def create_menu(root, mensaje, texto):

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
                         command=lambda: nuevo(root, mensaje, texto),
                         image=img_new,
                         compound=tkinter.LEFT)
    filemenu.add_command(label="Abrir", 
                         accelerator="Ctrl+O", 
                         command=lambda: abrir(root, mensaje, texto),
                         image=img_open,
                         compound=tkinter.LEFT)
    filemenu.add_command(label="Guardar", 
                         accelerator="Ctrl+S", 
                         command=lambda: guardar(root, mensaje, texto),
                         image=img_save,
                         compound=tkinter.LEFT)
    filemenu.add_command(label="Guardar como", 
                         accelerator="Ctrl+Shift+S", 
                         command=lambda: guardar_como(root, mensaje, texto),
                         image=img_save_as,
                         compound=tkinter.LEFT)
    filemenu.add_separator()
    filemenu.add_command(label="Salir", 
                         command=root.quit,
                         image=img_quit,
                         compound=tkinter.LEFT)
    
    # Menu de editar
    editmenu = Menu(menubar, tearoff=0)
    editmenu.add_command(label="Copiar",
                         accelerator="Ctrl+C",
                         command=lambda: copiar(root, mensaje, texto),
                         image=img_copy,
                         compound=tkinter.LEFT)
    editmenu.add_command(label="Cortar",
                         accelerator="Ctrl+X",
                         command=lambda: cortar(root, mensaje, texto),
                         image=img_cut,
                         compound=tkinter.LEFT)
    editmenu.add_command(label="Pegar",
                         accelerator="Ctrl+V",
                         command=lambda: pegar(root, mensaje, texto),
                         image=img_paste,
                         compound=tkinter.LEFT)
    editmenu.add_separator()
    editmenu.add_command(label="Seleccionar todo",
                         accelerator="Ctrl+A",
                         command=lambda: seleccionar_todo(root, mensaje, texto),
                         image=img_select_all,
                         compound=tkinter.LEFT)
    
    # Menu fuente
    toolmenu = Menu(menubar, tearoff=0)
    toolmenu.add_command(label="Aumentar tamaño",
                         command=lambda: aumentar_fuente(texto),
                         image=img_mas,
                         compound=tkinter.LEFT)
    toolmenu.add_command(label="Disminuir tamaño",
                         command= lambda: disminuir_fuente(texto),
                         image=img_menos,
                         compound=tkinter.LEFT)

    # Asociar el atajo del teclado del menu

    # Menu de archivos
    root.bind("<Control-n>", lambda event: nuevo(root, mensaje, texto))
    root.bind("<Control-o>", lambda event: abrir(root, mensaje, texto))
    root.bind("<Control-s>", lambda event: guardar(root, mensaje, texto))
    root.bind("<Control-S>", lambda event: guardar_como(root, mensaje, texto))

    menubar.add_cascade(menu=filemenu, label="Archivo")
    menubar.add_cascade(menu=editmenu, label="Editar")
    menubar.add_cascade(menu=toolmenu, label="Herramientas")

    root.config(menu=menubar)

