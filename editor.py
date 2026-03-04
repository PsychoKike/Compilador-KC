from tkinter import Frame, Scrollbar, StringVar, Tk, Text, Label, ttk
from file_operations import highlight_syntax, run_syntax_analysis
from menu import create_menu
from buttons import create_buttons

class LineNumbers(Text):
    """Widget para mostrar números de línea"""
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.config(
            width=4,
            padx=4,
            pady=4,
            font=("Consolas", 12),
            bg='#f0f0f0',
            fg='gray',
            state='disabled',
            wrap='none',
            highlightthickness=0,
            bd=0,
            takefocus=0
        )
        self.attach()
    
    def attach(self):
        """Vincular eventos para actualizar números de línea"""
        self.text_widget.bind('<KeyRelease>', self.update_line_numbers)
        self.text_widget.bind('<MouseWheel>', self.update_line_numbers)
        self.text_widget.bind('<ButtonRelease-1>', self.update_line_numbers)
        self.text_widget.bind('<FocusIn>', self.update_line_numbers)
        self.update_line_numbers()
    
    def update_line_numbers(self, event=None):
        """Actualizar los números de línea"""
        try:
            # Obtener el número total de líneas
            total_lines = int(self.text_widget.index('end-1c').split('.')[0])
            
            # Generar los números
            line_numbers = '\n'.join(str(i) for i in range(1, total_lines + 1))
            
            # Actualizar el widget de números
            self.config(state='normal')
            self.delete(1.0, 'end')
            self.insert(1.0, line_numbers)
            self.config(state='disabled')
            
            # Sincronizar el scroll
            self.yview_moveto(self.text_widget.yview()[0])
        except:
            pass

def actualizar_coordenadas(event=None, texto=None, coord_label=None):
    """Actualizar todas las coordenadas: línea, columna, selección, líneas totales, longitud"""
    try:
        # Obtener posición actual del cursor
        pos = texto.index("insert")
        linea_actual, columna_actual = pos.split('.')
        
        # Obtener selección (si hay)
        try:
            sel_start = texto.index("sel.first")
            sel_end = texto.index("sel.last")
            # Calcular caracteres seleccionados
            seleccionados = len(texto.get(sel_start, sel_end))
        except:
            seleccionados = 0
        
        # Obtener total de líneas
        total_lineas = int(texto.index('end-1c').split('.')[0])
        
        # Obtener longitud total del texto
        texto_completo = texto.get(1.0, 'end-1c')
        longitud_total = len(texto_completo)
        
        # Modo inserción/sobreescritura (por defecto inserción)
        modo = "Insert"
        
        # Actualizar el label con formato similar a Dev-C++
        coord_label.config(
            text=f"Linea: {linea_actual}   Col: {int(columna_actual)+1:2d}   Sel: {seleccionados}   Lineas: {total_lineas}   Longitud: {longitud_total}   {modo}"
        )
    except Exception as e:
        print(f"Error actualizando coordenadas: {e}")

def create_editor():
    root = Tk()
    root.title("Compilador KC")

    # Configuracion de la ventana
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    ventana_ancho = int(width * 0.9)
    ventana_alto = int(height * 0.9)
    pos_x = int((width - ventana_ancho) / 2)
    pos_y = int((height - ventana_alto) / 2)
    root.geometry(f"{int(ventana_ancho)}x{int(ventana_alto)}+{int(pos_x)}+{int(pos_y)}")

    # Frame para los botones
    button_frame = Frame(root)
    button_frame.pack(side='top', fill='x', padx=20, pady=(10, 0))

    # Frame principal el cual sera dividido
    frame_principal = Frame(root)
    frame_principal.pack(fill='both', expand=True)

    margen_x = 20
    margen_y = 20

    # ============================================
    # PARTE IZQUIERDA: EDITOR CON NUMERACIÓN
    # ============================================
    frame_izquierda = Frame(frame_principal)
    frame_izquierda.pack(side='left', fill='both', expand=True)

    # Frame para contener el editor y los números
    editor_frame = Frame(frame_izquierda)
    editor_frame.pack(fill='both', expand=True, padx=margen_x, pady=(margen_y, 5))

    # Crear el widget de texto
    texto = Text(editor_frame, wrap='word', bd=0, padx=6, font=("Consolas", 12), undo=True)
    
    # Crear los números de línea
    line_numbers = LineNumbers(editor_frame, texto, width=4, bg='#f0f0f0')

    # Posicionar los números y el texto usando grid
    line_numbers.grid(row=0, column=0, sticky='ns')
    texto.grid(row=0, column=1, sticky='nsew')

    # Configurar el grid para que el texto se expanda
    editor_frame.grid_columnconfigure(1, weight=1)
    editor_frame.grid_rowconfigure(0, weight=1)

    # Sincronizar el scroll entre números y texto
    def sync_scroll(*args):
        line_numbers.yview(*args)
    texto['yscrollcommand'] = sync_scroll

    # ============================================
    # BARRA DE COORDENADAS (como Dev-C++)
    # ============================================
    coord_frame = Frame(frame_izquierda, bg='#e0e0e0', height=25)
    coord_frame.pack(fill='x', padx=margen_x, pady=(0, margen_y))
    coord_frame.pack_propagate(False)  # Mantener altura fija

    # Label para mostrar todas las coordenadas
    coord_label = Label(
        coord_frame, 
        text="Line: 1   Col: 1   Sel: 0   Lines: 1   Length: 0   Insert",
        font=("Consolas", 9),
        bg='#e0e0e0',
        anchor='w'
    )
    coord_label.pack(side='left', padx=10)

    # ============================================
    # PARTE DERECHA: ANÁLISIS
    # ============================================
    frame_derecha = Frame(frame_principal)
    frame_derecha.pack(side='right', fill='both', expand=True)
    
    tab_control_analisis = ttk.Notebook(frame_derecha)
    
    # Pestaña para Análisis Léxico
    frame_lexico = ttk.Frame(tab_control_analisis)
    tab_control_analisis.add(frame_lexico, text='Análisis Léxico')

    # Pestaña para Análisis Sintáctico
    frame_sintactico = ttk.Frame(tab_control_analisis)
    tab_control_analisis.add(frame_sintactico, text='Análisis Sintáctico')
        
    tab_control_analisis.pack(fill='both', expand=True, padx=margen_x, pady=margen_y)

    # ============================================
    # PARTE INFERIOR: MONITOR DE MENSAJES
    # ============================================
    frame_inferior = Frame(root)
    frame_inferior.pack(side='bottom', fill='x')

    # Monitor de mensajes (izquierda)
    mensaje = StringVar()
    mensaje.set("Bienvenido a Suavecito Compiler")
    monitor = Label(frame_inferior, textvar=mensaje, justify='left', font=("Consolas", 9))
    monitor.pack(side='left', padx=20, pady=2)

    # ============================================
    # NOTEBOOK PARA ERRORES Y RESULTADOS
    # ============================================
    # Frame para contener el notebook de errores/resultados
    frame_notebook = Frame(root)
    frame_notebook.pack(side='right', fill='both', expand=True, padx=margen_x, pady=margen_y)
    
    tab_control = ttk.Notebook(frame_notebook)
    
    # Pestaña de Errores
    frame_errors = ttk.Frame(tab_control)
    tab_control.add(frame_errors, text='Errores')
    
    # Pestaña de Resultados
    frame_results = ttk.Frame(tab_control)
    tab_control.add(frame_results, text='Resultados')
    
    tab_control.pack(fill='both', expand=True)

    # Pantalla de salida para errores
    pantalla_errores = Text(frame_errors, height=10, state='disabled', wrap='word', font=("Consolas", 10))
    pantalla_errores.pack(fill='both', expand=True, padx=6, pady=6)
    scrollbar_errores = Scrollbar(frame_errors, command=pantalla_errores.yview)
    scrollbar_errores.pack(side='right', fill='y')
    pantalla_errores['yscrollcommand'] = scrollbar_errores.set

    # Pantalla de salida para resultados
    pantalla_resultados = Text(frame_results, height=10, state='disabled', wrap='word', font=("Consolas", 10))
    pantalla_resultados.pack(fill='both', expand=True, padx=6, pady=6)
    scrollbar_resultados = Scrollbar(frame_results, command=pantalla_resultados.yview)
    scrollbar_resultados.pack(side='right', fill='y')
    pantalla_resultados['yscrollcommand'] = scrollbar_resultados.set

    # ============================================
    # EVENTOS Y BINDS
    # ============================================
    # Función combinada para actualizar todo
    def actualizar_todo(event=None):
        highlight_syntax(texto)
        line_numbers.update_line_numbers()
        actualizar_coordenadas(event, texto, coord_label)
    
    # Vincular eventos principales
    texto.bind('<KeyRelease>', actualizar_todo)
    texto.bind('<ButtonRelease-1>', lambda e: actualizar_coordenadas(e, texto, coord_label))
    texto.bind('<FocusIn>', lambda e: actualizar_coordenadas(e, texto, coord_label))
    texto.bind('<MouseWheel>', lambda e: line_numbers.update_line_numbers())
    
    # Vincular evento para selección con mouse
    texto.bind('<B1-Motion>', lambda e: actualizar_coordenadas(e, texto, coord_label))
    
    # Vincular evento para teclas de movimiento sin escribir
    for key in ['<Left>', '<Right>', '<Up>', '<Down>', '<Home>', '<End>', 
                '<Next>', '<Prior>', '<Control-Home>', '<Control-End>']:
        texto.bind(key, lambda e: [root.after(10, lambda: actualizar_coordenadas(e, texto, coord_label))])
    
    # Actualizar cuando se modifica el contenido
    texto.bind('<<Modified>>', lambda e: [line_numbers.update_line_numbers(), 
                                          actualizar_coordenadas(e, texto, coord_label),
                                          texto.tk.call(texto, 'edit', 'modified', 0)])

    # ============================================
    # MENÚ Y BOTONES
    # ============================================
    create_menu(root, mensaje, texto)
    create_buttons(button_frame, root, mensaje, texto, pantalla_errores, frame_lexico, frame_sintactico)

    # Actualizar coordenadas iniciales
    root.after(100, lambda: actualizar_coordenadas(None, texto, coord_label))

    # Bucle de la aplicacion
    root.mainloop()

if __name__ == "__main__":
    create_editor()