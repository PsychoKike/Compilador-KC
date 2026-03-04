from tkinter import font, Tk, StringVar, OptionMenu

def aumentar_fuente(texto):
    actual_size = texto.cget("font").split()[1]
    nueva_size = int(actual_size) + 1
    texto.config(font=("Consolas", nueva_size))

def disminuir_fuente(texto):
    actual_size = texto.cget("font").split()[1]
    nueva_size = max(1, int(actual_size) - 1)
    texto.config(font=("Consolas", nueva_size))
