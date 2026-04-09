import tkinter as tk
from tkinter import ttk

class TabWithCloseButton:

    def __init__(self, notebook, title, content="", actualizar=None):

        self.notebook = notebook

        # Frame principal
        self.main_frame = tk.Frame(notebook)

        # Contenedor
        container = tk.Frame(self.main_frame)
        container.pack(fill="both", expand=True)

        # Números de línea
        self.line_numbers = tk.Text(
            container,
            width=4,
            padx=5,
            takefocus=0,
            border=0,
            background="#2b2b2b",
            foreground="gray",
            state="disabled"
        )
        self.line_numbers.pack(side="left", fill="y")

        # Editor principal
        self.text_widget = tk.Text(
            container,
            wrap="none",
            undo=True,
            background="#1e1e1e",
            foreground="white",
            insertbackground="white"
        )
        self.text_widget.pack(side="right", fill="both", expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(container, command=self._on_scroll)
        scrollbar.pack(side="right", fill="y")

        self.text_widget.config(yscrollcommand=scrollbar.set)

        # Insertar contenido
        self.text_widget.insert("1.0", content)

        # Eventos
        self.text_widget.bind("<KeyRelease>", self._update_line_numbers)
        self.text_widget.bind("<MouseWheel>", self._on_mouse_scroll)

        # Agregar al notebook
        self.notebook.add(self.main_frame, text=title)

        # Dibujar líneas
        self.redraw_line_numbers()


    # ============================================
    # OBTENER TEXT WIDGET
    # ============================================

    def get_text_widget(self):
        return self.text_widget


    # ============================================
    # SCROLL
    # ============================================

    def _on_scroll(self, *args):
        self.text_widget.yview(*args)
        self.line_numbers.yview(*args)


    def _on_mouse_scroll(self, event):
        self.text_widget.yview_scroll(int(-1*(event.delta/120)), "units")
        self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"


    # ============================================
    # LINE NUMBERS
    # ============================================

    def redraw_line_numbers(self):

        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")

        total_lines = int(self.text_widget.index("end-1c").split(".")[0])

        line_numbers_string = "\n".join(str(i) for i in range(1, total_lines + 1))

        self.line_numbers.insert("1.0", line_numbers_string)
        self.line_numbers.config(state="disabled")


    def _update_line_numbers(self, event=None):
        self.redraw_line_numbers()