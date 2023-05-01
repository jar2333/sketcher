from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from extraction import extract_graph, plot_graph
from database import open_database, query_database, close_database

"""
Adapted from https://python-course.eu/tkinter/canvas-widgets-in-tkinter.php
"""

CANVAS_WIDTH = 500
CANVAS_HEIGHT = 500

PATHS = []

PATH = []

def paint(event, canvas, d=0.5):
   PATH.append((event.x, event.y))

   x1, y1 = (event.x - d), (event.y - d)
   x2, y2 = (event.x + d), (event.y + d)
   canvas.create_rectangle(x1, y1, x2, y2,
                           outline = "black", fill = "black"
                           )

def finalize(event):
    PATH.append((event.x, event.y))
    PATHS.append(tuple(PATH))
    PATH.clear()

def submit(window):
    g = extract_graph(PATHS, 'test')

    fig = plot_graph(g)

    # creating the Tkinter canvas
    # containing the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master=window)  
    canvas.draw()
  
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().pack()

def create_window():
    master = Tk()
    master.title("Sketching!")

    c = Canvas(master, 
               width=CANVAS_WIDTH, 
               height=CANVAS_HEIGHT
               )
    c.pack(expand=YES, fill=BOTH)

    # Bind the paint function to be called on Button1 movement
    c.bind("<B1-Motion>", lambda e: paint(e, c))

    # Bind the finalize function to be called on Button1 release
    c.bind("<ButtonRelease-1>", finalize)

    message = Label(master, text="Press and Drag the mouse to draw")
    message.pack(side=BOTTOM)
    
    B = Button(master, text ="Submit", command=lambda: submit(master))
    B.pack()

def main():
    create_window()

    mainloop()

if __name__ == "__main__":
    main()
   