import tkinter as tk


class LineNumbers(tk.Canvas):

    def __init__(self, master, text_widget):
        super().__init__(master, width=50, bg="#fafafa", highlightthickness=0)

        self.text_widget = text_widget
        self.font = ("Consolas", 11)

        # Enlazar eventos
        self.text_widget.bind("<KeyRelease>", self.redraw)
        self.text_widget.bind("<ButtonRelease>", self.redraw)
        self.text_widget.bind("<MouseWheel>", self.redraw)
        self.text_widget.bind("<Configure>", self.redraw)  
        
        # Dibujar inicialmente
        self.redraw()

    def redraw(self, event=None):
        # Actualizar la interfaz
        self.text_widget.update_idletasks()
        
        # Limpiar el canvas
        self.delete("all")
        
        # Obtener la primera línea visible
        first_line = self.text_widget.index("@0,0")
        
        # Obtener el desplazamiento actual del scroll
        scroll_offset = self.text_widget.yview()[0]
        
        i = first_line
        
        while True:
            # Obtener información de la línea
            dline = self.text_widget.dlineinfo(i)
            
            if dline is None:
                break
            
            # Obtener la posición Y de la línea
            x, y, width, height, baseline = dline
            
            # SOLUCIÓN: Ajustar la posición Y considerando el scroll
            # La línea 28 no es relevante aquí, el problema es el scroll
            
            # Obtener el número de línea
            line_number = str(i).split(".")[0]
            
            # Crear el texto en el canvas
            self.create_text(
                40,  # Posición X (ajústala según necesites)
                y,   # Usamos la Y que nos da dlineinfo directamente
                anchor="ne",
                text=line_number,
                font=self.font,
                fill="#010101"
            )
            
            # Mover a la siguiente línea
            i = self.text_widget.index(f"{i}+1line")
            
            # Opcional: prevenir bucle infinito
            if int(str(i).split(".")[0]) > 10000:  # Límite de seguridad
                break
    
    def sync_scroll(self, *args):
        """Sincronizar el scroll con el texto"""
        self.redraw()
        # Usar los argumentos para el scroll
        if args:
            self.text_widget.yview_moveto(args[0])
    
    def get_text_widget(self):
        return self.text_widget