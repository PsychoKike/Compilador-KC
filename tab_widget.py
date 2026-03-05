# tab_widget.py
from tkinter import Frame, Label, Text
from widgets import LineNumbers

class TabWithCloseButton:
    """Versión simple de pestaña con botón de cerrar"""
    
    def __init__(self, notebook, title="Nuevo archivo", content="", update_callback=None):
        self.notebook = notebook
        self.title = title
        self.content = content
        self.update_callback = update_callback
        
        # Frame principal que contendrá TODO
        self.main_frame = Frame(notebook)
        
        # ===== HEADER DE LA PESTAÑA (la parte de arriba con el título y X) =====
        self.header_frame = Frame(self.main_frame, bg='#f0f0f0', height=30)
        self.header_frame.pack(fill='x')
        self.header_frame.pack_propagate(False)
        
        # Título
        self.title_label = Label(
            self.header_frame,
            text=title,
            bg='#f0f0f0',
            font=('TkDefaultFont', 10)
        )
        self.title_label.pack(side='left', padx=10)
        
        # Botón X (siempre visible)
        self.close_button = Label(
            self.header_frame,
            text='✕',
            bg='#f0f0f0',
            fg='#666',
            font=('Arial', 12, 'bold'),
            cursor='hand2'
        )
        self.close_button.pack(side='right', padx=10)
        
        # Eventos del botón X
        self.close_button.bind('<Enter>', lambda e: self.close_button.config(fg='red'))
        self.close_button.bind('<Leave>', lambda e: self.close_button.config(fg='#666'))
        self.close_button.bind('<Button-1>', self.close_tab)
        
        # ===== EDITOR =====
        self.editor_frame = Frame(self.main_frame)
        self.editor_frame.pack(fill='both', expand=True)

        self.text = Text(
            self.editor_frame,
            wrap='word',
            font=('Consolas', 12),
            undo=True,
            padx=10,
            pady=5
        )
        
        # Vincular eventos para actualizar coordenadas
        if self.update_callback:
            self.text.bind("<KeyPress>", lambda e: self.after(1, self.update_callback)) # after(1) permite que el cursor se mueva antes de leer la posición
            self.text.bind("<Button-1>", lambda e: self.after(1, self.update_callback))
            # También actualizar cuando se mueve con las flechas
            self.text.bind("<Up>", lambda e: self.after(10, self.update_callback))
            self.text.bind("<Down>", lambda e: self.after(10, self.update_callback))
            self.text.bind("<Left>", lambda e: self.after(10, self.update_callback))
            self.text.bind("<Right>", lambda e: self.after(10, self.update_callback))
            # Actualizar inmediatamente
            self.after(10, self.update_callback)

        self.line_numbers = LineNumbers(self.editor_frame, self.text)

        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")

        self.editor_frame.grid_columnconfigure(1, weight=1)
        self.editor_frame.grid_rowconfigure(0, weight=1)
        
        # Insertar contenido si hay
        if content:
            self.text.insert('1.0', content)
        
        # Añadir la pestaña al notebook
        self.notebook.add(self.main_frame, text=title)
    
    def after(self, ms, func):
        """Método helper para usar after de tkinter"""
        return self.main_frame.after(ms, func)
    
    def close_tab(self, event):
        """Cerrar esta pestaña"""
        if len(self.notebook.tabs()) > 1:
            self.notebook.forget(self.main_frame)
    
    def get_text_widget(self):
        """Devolver el widget de texto"""
        return self.text