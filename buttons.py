import os
import tkinter as tk
from tkinter import Button
from file_operations import (nuevo, abrir, guardar, guardar_como, run_command,
                             run_semantic_analysis)

images = []

def resize_image(image_path, width, height):
    import tkinter
    img = tkinter.PhotoImage(file=image_path)
    img = img.subsample(width, height)
    images.append(img)
    return img


def create_buttons(button_frame, editor_tabs, mensaje, pantalla_errores,
                   frame_lexico, frame_sintactico, frame_semantico,
                   frame_hash, frame_intermedio,
                   frame_err_sin=None, frame_err_lex=None, frame_err_sem=None):

    try:
        img_new     = resize_image(os.path.abspath("img/new.png"),     2, 2)
        img_open    = resize_image(os.path.abspath("img/open.png"),    2, 2)
        img_save    = resize_image(os.path.abspath("img/save.png"),    2, 2)
        img_save_as = resize_image(os.path.abspath("img/save_as.png"), 2, 2)
        img_run     = resize_image(os.path.abspath("img/run.png"),     2, 2)
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar imágenes: {e}")
        img_new = img_open = img_save = img_save_as = img_run = None

    # Botones de archivo
    Button(button_frame, image=img_new,
           command=lambda: nuevo(editor_tabs, mensaje)).pack(side='left', padx=2)
    Button(button_frame, image=img_open,
           command=lambda: abrir(editor_tabs, mensaje)).pack(side='left', padx=2)
    Button(button_frame, image=img_save,
           command=lambda: guardar(editor_tabs, mensaje)).pack(side='left', padx=2)
    Button(button_frame, image=img_save_as,
           command=lambda: guardar_como(editor_tabs, mensaje)).pack(side='left', padx=2)

    tk.Frame(button_frame, width=2, bd=1, relief="sunken").pack(
        side='left', padx=10, fill='y')

    btn_params = dict(padx=8, pady=2, relief="raised",
                      bg="#e1e1e1", font=("Segoe UI", 9, "bold"))

    # Botón Run → Léxico + Sintáctico + Semántico (llena todas las listas de errores)
    Button(
        button_frame,
        image=img_run,
        command=lambda: run_semantic_analysis(
            editor_tabs, mensaje,
            frame_lexico, pantalla_errores,
            frame_sintactico,
            frame_semantico, frame_hash,
            frame_err_sin=frame_err_sin,
            frame_err_lex=frame_err_lex,
            frame_err_sem=frame_err_sem,
            mostrar=False,
        ),
        **btn_params
    ).pack(side='left', padx=5)

    # Botón Semántico → Léxico + Sintáctico + Semántico (árbol anotado, tabla y errores)
    tk.Button(button_frame, text="🧪 Semántico",
              command=lambda: run_semantic_analysis(
                  editor_tabs, mensaje,
                  frame_lexico, pantalla_errores,
                  frame_sintactico,
                  frame_semantico, frame_hash,
                  frame_err_sin=frame_err_sin,
                  frame_err_lex=frame_err_lex,
                  frame_err_sem=frame_err_sem,
              ),
              **btn_params).pack(side="left", padx=2)

    tk.Button(button_frame, text="📋 Hash Table",
              command=lambda: mensaje.set("Hash Table: próximamente..."),
              **btn_params).pack(side="left", padx=2)

    tk.Button(button_frame, text="⚙️ Cód. Intermedio",
              command=lambda: mensaje.set("Código Intermedio: próximamente..."),
              **btn_params).pack(side="left", padx=2)