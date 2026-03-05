# widgets.py
from tkinter import Text, Frame

class LineNumbers(Text):

    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)

        self.text_widget = text_widget
        self._last_update = 0
        self._update_job = None

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
            bd=0
        )

        self.attach()

    def attach(self):
        """Vincular eventos con debounce"""
        self.text_widget.bind('<KeyRelease>', self._schedule_update)
        self.text_widget.bind('<MouseWheel>', self._schedule_update)
        self.text_widget.bind('<ButtonRelease-1>', self._schedule_update)
        self.text_widget.bind('<Up>', self._schedule_update)
        self.text_widget.bind('<Down>', self._schedule_update)
        self.text_widget.bind('<Left>', self._schedule_update)
        self.text_widget.bind('<Right>', self._schedule_update)
        self.update_line_numbers()

    def _schedule_update(self, event=None):
        """Programar actualización con debounce"""
        if self._update_job:
            self.text_widget.after_cancel(self._update_job)
        
        self._update_job = self.text_widget.after(100, self._do_update)

    def _do_update(self):
        """Ejecutar la actualización"""
        self._update_job = None
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        """Versión optimizada de update_line_numbers"""
        try:
            total_lines = int(self.text_widget.index('end-1c').split('.')[0])
            
            current_numbers = self.get('1.0', 'end-1c')
            expected_numbers = "\n".join(str(i) for i in range(1, total_lines + 1))
            
            if current_numbers != expected_numbers:
                self.config(state='normal')
                self.delete(1.0, "end")
                self.insert(1.0, expected_numbers)
                self.config(state='disabled')
            
            self.yview_moveto(self.text_widget.yview()[0])
        except:
            pass