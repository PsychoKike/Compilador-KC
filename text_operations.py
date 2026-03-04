from tkinter import TclError


def copiar(root, mensaje, texto):
    mensaje.set("Copiar")
    texto.event_generate("<<Copy>>")

def cortar(root, mensaje, texto):
    mensaje.set("Cortar")
    texto.event_generate("<<Cut>>")

def pegar(root, mensaje, texto):
    mensaje.set("Pegar")
    texto.event_generate("<<Paste>>")

def seleccionar_todo(root, mensaje, texto):
    mensaje.set("Seleccionar Todo")
    texto.tag_add("sel", "1.0", "end")