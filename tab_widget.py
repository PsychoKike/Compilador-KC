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

        self.text.config(yscrollcommand=self.on_text_scroll)
        scrollbar.config(command=self.on_scrollbar_move)

        self.line_numbers.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="right", fill="both", expand=True)

        self.text.insert("1.0", content)

        if actualizar:
            
            self.text.bind("<ButtonRelease>", actualizar)

        notebook.add(self.main_frame, text=title)
        
        # IMPORTANTE: Vincular al evento <Map> que ocurre cuando la pestaña es visible
        self.main_frame.bind("<Map>", self.on_tab_mapped)
        
        # También vincular al cambio de tamaño del texto
        self.text.bind("<Configure>", lambda e: self.line_numbers.redraw())

    def on_tab_mapped(self, event):
        """Se llama cuando la pestaña se hace visible por primera vez"""
        # Esperar un poco más para asegurar que todo está renderizado
        self.text.after(2, self.line_numbers.redraw)
        
    def on_text_scroll(self, *args):
        """Cuando el texto se desplaza, actualizar números y scrollbar"""
        self.line_numbers.redraw()
        if args:
            self.text.yview_moveto(args[0])

    def on_scrollbar_move(self, *args):
        """Cuando se mueve el scrollbar, mover el texto"""
        self.text.yview(*args)
        self.line_numbers.redraw()

    def get_text_widget(self):
        return self.text