# buttons.py corregido
import os
from tkinter import Button
import tkinter as tk
from file_operations import nuevo, abrir, guardar, guardar_como, run_command
import tkinter

# Lista para mantener referencias globales a las imágenes
images = []

def resize_image(image_path, width, height):
    original_image = tkinter.PhotoImage(file=image_path)
    resized_image = original_image.subsample(width, height)
    images.append(resized_image)  
    return resized_image

def create_buttons(button_frame, editor_tabs, mensaje, pantalla_errores, frame_lexico, frame_sintactico,
                  frame_semantico, frame_hash, frame_intermedio):

    # --- ICONOS (Operaciones de Archivo) ---
    try:
        img_new = resize_image(os.path.abspath("img/new.png"), 2, 2)
        img_open = resize_image(os.path.abspath("img/open.png"), 2, 2)
        img_save = resize_image(os.path.abspath("img/save.png"), 2, 2)
        img_save_as = resize_image(os.path.abspath("img/save_as.png"), 2, 2)
        img_run = resize_image(os.path.abspath("img/run.png"), 2, 2)
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar las imágenes: {e}")
        # Definimos variables vacías para que no truene si no hay imágenes
        img_new = img_open = img_save = img_save_as = img_run = None

    # --- BOTONES DE ACCIÓN RÁPIDA ---
    Button(button_frame, image=img_new, command=lambda: nuevo(editor_tabs, mensaje)).pack(side='left', padx=2)
    Button(button_frame, image=img_open, command=lambda: abrir(editor_tabs, mensaje)).pack(side='left', padx=2)
    Button(button_frame, image=img_save, command=lambda: guardar(editor_tabs, mensaje)).pack(side='left', padx=2)
    Button(button_frame, image=img_save_as, command=lambda: guardar_como(editor_tabs, mensaje)).pack(side='left', padx=2)
    
    # Separador visual
    tk.Frame(button_frame, width=2, bd=1, relief="sunken").pack(side='left', padx=10, fill='y')

    # --- BOTONES DE ANÁLISIS ---
    btn_params = {
        "padx": 8, 
        "pady": 2, 
        "relief": "raised", 
        "bg": "#e1e1e1",
        "font": ("Segoe UI", 9, "bold")
    }

    # Botón Run (Léxico + Sintáctico por defecto)
    Button(button_frame, image=img_run, 
           command=lambda: run_command(editor_tabs, mensaje, frame_lexico, pantalla_errores, frame_sintactico),
           **btn_params).pack(side='left', padx=5)

    # Botón Semántico (Cambiamos 'container' por 'button_frame')
    tk.Button(button_frame, text="🧪 Semántico", 
              command=lambda: print("Ejecutando Semántico..."),
              **btn_params).pack(side="left", padx=2)

    # Botón Hash Table
    tk.Button(button_frame, text="📋 Hash Table", 
              command=lambda: print("Mostrando Tabla de Símbolos..."),
              **btn_params).pack(side="left", padx=2)

    # Botón Código Intermedio
    tk.Button(button_frame, text="⚙️ Cód. Intermedio", 
              command=lambda: print("Generando Código Intermedio..."),
              **btn_params).pack(side="left", padx=2)