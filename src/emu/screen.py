import tkinter as tk
import threading
import pyglet
pyglet.font.add_file('fonts/VGA.ttf')


text_x = 0
text_y = 0
font_size = 20

rows = 80
columns = 40
text_colour = "white"


class App(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.configure(background="#000000")
        self.root.geometry("640x480")
        self.root.title("SP-8 Emulator")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, border="0",background=self.root["bg"], width=640, height=480, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        self.root.mainloop()


def writes(window: App, text: str):
    global text_x, text_y

    # Loop over every character
    for char in text:
        window.canvas.create_text(text_x * (font_size * 0.75), text_y * (font_size * 0.75), text=char, fill=text_colour, font=('8 x 8 Font',font_size // 2), anchor="nw")

        text_x += 1

        if char == "\n":
            scroll_up()

        if text_x > rows:
            scroll_up()

def scroll_up(lines: int = 1):
    global text_x, text_y
    text_y += lines
    text_x = 0

def reset_scroll():
    global text_x, text_y
    text_y = 0
    text_x = 0

def clear(window: App, colour: str = "black"):
    window.canvas.delete("all")
    window.canvas.configure(background=colour)
    window.root.configure(background=colour)

def draw_pix(window: App, pos: tuple, colour: str = "white"):
    window.canvas.create_rectangle(pos[0], pos[1], pos[0]+1, pos[1]+1, fill=colour, outline="")

def set_colour(colour: str = "white"):
    global text_colour
    text_colour = colour