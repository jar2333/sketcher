from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

from numpy import argmax

from extraction import extract_graph, plot_graph, get_line_strings, plot_line_strings, get_polygons, plot_polygons
from database import open_database, query_database, close_database, descriptor
from labels import LABELS

"""
Adapted from https://python-course.eu/tkinter/canvas-widgets-in-tkinter.php
"""

"""
DATABASE
"""

DATABASE = open_database()

def clean_exit():
    close_database(DATABASE)
    exit()

"""
DRAWN PATHS
"""

PATHS = []
PATH  = []

def paint(event, canvas, d=0.5):
   PATH.append((event.x, event.y))

   x1, y1 = (event.x - d), (event.y - d)
   x2, y2 = (event.x + d), (event.y + d)
   canvas.create_rectangle(x1, y1, x2, y2, outline = "black", fill = "black")

def clear(canvas):
    canvas.delete('all')
    PATHS.clear()
    PATH.clear()

def finalize(event):
    PATH.append((event.x, event.y))
    PATHS.append(tuple(PATH))
    PATH.clear()

"""
PLOTTING
"""
GRAPH_MODE      = 0
POLYGON_MODE    = 1
LINESTRING_MODE = 2

MODE = None
PREVIOUS = None

def plot(window):
    global PREVIOUS, MODE
    # Plot the extracted graph
    if MODE.get() == GRAPH_MODE:
        fig = plot_graph(extract_graph(PATHS, 'label', check_area=False))
    elif MODE.get() == POLYGON_MODE:
        fig = plot_polygons(get_polygons(get_line_strings(PATHS)))
    else:
        fig = plot_line_strings(get_line_strings(PATHS))

    # Destroy previous plot
    if PREVIOUS is not None:
        PREVIOUS.destroy()

    # create the canvas containing the figure
    canvas = FigureCanvasTkAgg(fig, master=window)  
    canvas.draw()

    # place the canvas on the Tkinter window
    canvas.get_tk_widget().grid(row = 2, column = 5, columnspan = 2, rowspan = 2)

    PREVIOUS = canvas.get_tk_widget()

"""
CLASSIFICATION
"""

MSG = None

def submit(window):
    global PREVIOUS, MSG

    g = extract_graph(PATHS, 'label', check_area=False)

    dist = query_database(DATABASE, g)

    # results = sorted(enumerate(LABELS), key=lambda l: dist[l[0]], reverse=True)
    # results = [f'{i}, {l}: {dist[i]}' for i, l in results]
    # results = '\n'.join(results[0:5])
    results = None

    if MSG is not None:
        MSG.destroy()

    # Add message to window
    message = Label(window, text=results, font=("Arial", 25))
    message.grid(row = 1, column = 5, columnspan = 3)

    MSG = message

    # Destroy previous plot
    if PREVIOUS is not None:
        PREVIOUS.destroy()

    # Figure Size
    fig = plt.figure()
    
    # Figure and axis
    # plt.bar(range(len(LABELS)), dist)
    # plt.xticks(range(0, len(LABELS), len(LABELS)//10))
    
    # create the canvas containing the figure
    canvas = FigureCanvasTkAgg(fig, master=window)  
    canvas.draw()

    # place the canvas on the Tkinter window
    canvas.get_tk_widget().grid(row = 2, column = 5, columnspan = 2, rowspan = 2)

    PREVIOUS = canvas.get_tk_widget()

"""
WINDOW AND CANVAS
"""

CANVAS_WIDTH  = 800
CANVAS_HEIGHT = 800

def create_window():
    global MODE

    # Create window
    master = Tk()
    master.title("Sketching!")

    # On window close, exit
    master.protocol("WM_DELETE_WINDOW", clean_exit)

    # Set default output mode
    MODE = IntVar(value=GRAPH_MODE)

    # Create button to plot drawing
    b = Button(master, text="Plot", command=lambda: plot(master))
    b.grid(row = 0, column = 0)

    # Create button to clear drawing
    cb = Button(master, text="Clear", command=lambda: clear(c))
    cb.grid(row = 0, column = 1)

    # Create button to exit 
    eb = Button(master, text="Submit", command=lambda: submit(master))
    eb.grid(row = 0, column = 2)

    # Create canvas
    c = Canvas(master, 
               bg='white',
               width=CANVAS_WIDTH, 
               height=CANVAS_HEIGHT
               )
    c.grid(row = 1, column = 0, columnspan = 3, rowspan = 3)

    # Paint on canvas on mouse movement
    c.bind("<B1-Motion>", lambda e: paint(e, c))

    # Stop painting on canvas on mouse release
    c.bind("<ButtonRelease-1>", finalize)

    # Radio buttons for output window
    r1 = Radiobutton(master, text="Graph", variable=MODE, value=GRAPH_MODE)
    r1.grid(row = 1, column = 4)

    r2 = Radiobutton(master, text="Polygon", variable=MODE, value=POLYGON_MODE)
    r2.grid(row = 2, column = 4)

    r3 = Radiobutton(master, text="Linestring", variable=MODE, value=LINESTRING_MODE)
    r3.grid(row = 3, column = 4)

"""
RUNNER
"""

def main():
    try:
        # Create GUI window
        create_window()

        # Start GUI event loop
        mainloop()

    except KeyboardInterrupt:
        clean_exit()


if __name__ == "__main__":
    main()
   