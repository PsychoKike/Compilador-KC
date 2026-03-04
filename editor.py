from tkinter import Frame, Scrollbar, StringVar, Tk, Text, Label, ttk
from file_operations import highlight_syntax, run_syntax_analysis
from menu import create_menu
from buttons import create_buttons

def create_editor():
    root = Tk()
    root.title("Suavecito Compiler")

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

    # Parte izquierda: editor de texto
    frame_izquierda = Frame(frame_principal)
    frame_izquierda.pack(side='left', fill='both', expand=True)
    texto = Text(frame_izquierda, wrap='word', bd=0, padx=6, font=("Consolas", 12))
    texto.pack(fill="both", expand=True, padx=margen_x, pady=margen_y)
    
    # Vincular evento de cambio de texto a la función de resaltado de sintaxis
    texto.bind('<KeyRelease>', lambda event: highlight_syntax(texto))
    
    # Parte derecha: Analisis lexico y sintactico
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

    # Monitor inferior
    mensaje = StringVar()
    mensaje.set("Bienvenido a Suavecito Compiler")
    monitor = Label(root, textvar=mensaje, justify='left')
    monitor.pack(side='bottom', anchor='se', padx=20)

    # Crear Notebook para errores y resultados
    tab_control = ttk.Notebook(root)
    frame_errors = ttk.Frame(tab_control)
    tab_control.add(frame_errors, text='Errores')
    frame_results = ttk.Frame(tab_control)
    tab_control.add(frame_results, text='Resultados')
    tab_control.pack(side='right', fill='both', expand=True, padx=margen_x, pady=margen_y)

    # Pantalla de salida para errores
    pantalla_errores = Text(frame_errors, height=10, state='disabled', wrap='word')
    pantalla_errores.pack(fill='both', expand=True, padx=6, pady=6)
    scrollbar_errores = Scrollbar(frame_errors, command=pantalla_errores.yview)
    scrollbar_errores.pack(side='right', fill='y')
    pantalla_errores['yscrollcommand'] = scrollbar_errores.set

    # Pantalla de salida para resultados
    pantalla_resultados = Text(frame_results, height=10, state='disabled', wrap='word')
    pantalla_resultados.pack(fill='both', expand=True, padx=6, pady=6)
    scrollbar_resultados = Scrollbar(frame_results, command=pantalla_resultados.yview)
    scrollbar_resultados.pack(side='right', fill='y')
    pantalla_resultados['yscrollcommand'] = scrollbar_resultados.set

    # Menu superior y botones
    create_menu(root, mensaje, texto)
    create_buttons(button_frame, root, mensaje, texto, pantalla_errores, frame_lexico, frame_sintactico)

    # Bucle de la aplicacion
    root.mainloop()

if __name__ == "__main__":
    create_editor()