import tkinter as tk
from tkinter import ttk
from line_numbers import LineNumbers


class TabWithCloseButton:

    def __init__(self, notebook, title, content, actualizar):

        self.main_frame = tk.Frame(notebook)

        editor_frame = tk.Frame(self.main_frame)
        editor_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(editor_frame)

        self.text = tk.Text(
            editor_frame,
            wrap="none",
            undo=True,
            font=("Consolas", 11)
        )

        self.line_numbers = LineNumbers(editor_frame, self.text)

        # =========================
        # SCROLL
        # =========================

        self.text.config(yscrollcommand=self.on_text_scroll)
        scrollbar.config(command=self.on_scrollbar_move)

        self.line_numbers.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="right", fill="both", expand=True)

        self.text.insert("1.0", content)

        # =========================
        # REDIBUJAR LINE NUMBERS
        # =========================

        # Cuando se escribe
        self.text.bind("<KeyPress>", self.on_text_change)

        # Cuando se pega texto
        self.text.bind("<<Paste>>", self.on_text_change)

        # Cuando se borra
        self.text.bind("<BackSpace>", self.on_text_change)

        # Cuando cambia tamaño
        self.text.bind("<Configure>", lambda e: self.line_numbers.redraw())

        # =========================
        # AGREGAR PESTAÑA
        # =========================

        notebook.add(self.main_frame, text=title)

        # Cuando la pestaña aparece
        self.main_frame.bind("<Map>", self.on_tab_mapped)

    # =========================
    # EVENTOS
    # =========================

    def on_text_change(self, event=None):
        """Actualizar números después de que Tkinter termine de escribir"""
        self.text.after_idle(self.line_numbers.redraw)

    def on_tab_mapped(self, event):
        """Se ejecuta cuando la pestaña se vuelve visible"""
        self.text.after(10, self.line_numbers.redraw)

    def on_text_scroll(self, *args):
        """Scroll desde el texto"""
        self.line_numbers.redraw()
        if args:
            self.text.yview_moveto(args[0])

    def on_scrollbar_move(self, *args):
        """Scroll desde la barra"""
        self.text.yview(*args)
        self.line_numbers.redraw()

    # =========================
    # OBTENER TEXT WIDGET
    # =========================

    def get_text_widget(self):
        return self.text