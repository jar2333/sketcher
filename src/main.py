from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from extraction import extract_graph, plot_graph
from database import open_database, query_database, close_database

"""
Adapted from https://python-course.eu/tkinter/canvas-widgets-in-tkinter.php
"""

CANVAS_WIDTH  = 500
CANVAS_HEIGHT = 500

PATHS = []
PATH  = []

def paint(event, canvas, d=0.5):
   PATH.append((event.x, event.y))

   x1, y1 = (event.x - d), (event.y - d)
   x2, y2 = (event.x + d), (event.y + d)
   canvas.create_rectangle(x1, y1, x2, y2,
                           outline = "black", 
                           fill = "black"
                           )

def clear(canvas):
    canvas.delete('all')
    PATHS.clear()
    PATH.clear()

def finalize(event):
    PATH.append((event.x, event.y))
    PATHS.append(tuple(PATH))
    PATH.clear()

def submit(window):
    # Extract topology graph from drawn paths
    g = extract_graph(PATHS, 'test')

    # Plot the extracted graph
    fig = plot_graph(g)

    # create the canvas containing the figure
    canvas = FigureCanvasTkAgg(fig, master=window)  
    canvas.draw()
  
    # place the canvas on the Tkinter window
    canvas.get_tk_widget().pack(side=RIGHT)

def create_window():
    # Create window
    master = Tk()
    master.title("Sketching!")

    # Add message to window
    message = Label(master, text="Press and drag the mouse to draw")
    message.pack(side=BOTTOM)

    # Create canvas
    c = Canvas(master, 
               width=CANVAS_WIDTH, 
               height=CANVAS_HEIGHT
               )
    c.pack(expand=YES, fill=BOTH)

    # Paint on canvas on mouse movement
    c.bind("<B1-Motion>", lambda e: paint(e, c))

    # Stop painting on canvas on mouse release
    c.bind("<ButtonRelease-1>", finalize)
    
    # Create button to submit drawing
    B = Button(master, text="Submit", command=lambda: submit(master))
    B.pack()

    # Create button to clear drawing
    CB = Button(master, text="Clear", command=lambda: clear(c))
    CB.pack()


def main():
    # Create GUI window
    create_window()

    # Start GUI event loop
    mainloop()

if __name__ == "__main__":
    main()
   