    
import os
from tkinter import Button
import tkinter
from file_operations import nuevo, abrir, guardar, guardar_como, run_command, run_syntax_analysis


# Lista para mantener referencias globales a las imágenes
images = []

def resize_image(image_path, width, height):
    original_image = tkinter.PhotoImage(file=image_path)
    resized_image = original_image.subsample(width, height)
    images.append(resized_image)  # Mantener referencia global
    return resized_image

def create_buttons(button_frame, root, mensaje, texto, pantalla_errores, frame_lexico, frame_sintactico):

    # Rutas de las imagenes
    img_new_path = os.path.abspath("img/new.png")
    img_open_path = os.path.abspath("img/open.png")
    img_save_path = os.path.abspath("img/save.png")
    img_save_as_path = os.path.abspath("img/save_as.png")
    img_run_path = os.path.abspath("img/run.png")
    
    img_new = resize_image(img_new_path, 2, 2)
    img_open = resize_image(img_open_path, 2, 2)
    img_save = resize_image(img_save_path, 2, 2)
    img_save_as = resize_image(img_save_as_path, 2, 2)
    img_run = resize_image(img_run_path, 2, 2)

    button_new = Button(button_frame, image=img_new, command=lambda: nuevo(root, mensaje, texto))
    button_new.pack(side='left', padx=5)
    button_open = Button(button_frame, image=img_open, command=lambda: abrir(root, mensaje, texto))
    button_open.pack(side='left', padx=5)
    button_save = Button(button_frame, image=img_save, command=lambda: guardar(root, mensaje, texto))
    button_save.pack(side='left', padx=5)
    button_save_as = Button(button_frame, image=img_save_as, command=lambda: guardar_como(root, mensaje, texto))
    button_save_as.pack(side='left', padx=5)
    button_run = Button(button_frame, image=img_run, command=lambda: run_command(root, mensaje, texto, frame_lexico, pantalla_errores, frame_sintactico))
    button_run.pack(side='left', padx=5)

    
 