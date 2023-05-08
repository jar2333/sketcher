from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

from numpy import argmax

from src.vision import *
from src.svg import *
from src.extraction import *
from src.database import *
from src.matching import *
from src.labels import LABELS

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

CANVAS_INPUT = 0
FILE_INPUT = 1

INPUT_MODE = None

def plot(window, paths):
    global PREVIOUS, MODE

    # Plot the extracted graph
    if INPUT_MODE.get() == CANVAS_INPUT:
        line_strings = get_line_strings(paths)
        step = 20
    else:
        line_strings = get_image_line_strings(load_image(SELECTED_FILE))
        step = 40

    if MODE.get() == GRAPH_MODE:
        fig = plot_graph(extract_graph(line_strings, 'label', check_area=False, step=step))
    elif MODE.get() == POLYGON_MODE:
        fig = plot_polygons(get_polygons(line_strings))
    else:
        fig = plot_line_strings(line_strings)

    # Destroy previous plot
    if PREVIOUS is not None:
        PREVIOUS.destroy()

    # create the canvas containing the figure
    canvas = FigureCanvasTkAgg(fig, master=window)  
    canvas.draw()

    # place the canvas on the Tkinter window
    canvas.get_tk_widget().grid(row = 2, column = 4, columnspan = 2, rowspan = 2)

    PREVIOUS = canvas.get_tk_widget()

"""
CLASSIFICATION
"""

MSG = None

def submit(window, line_strings):
    global PREVIOUS, MSG

    # PIPELINE

    g = extract_graph(line_strings, 'label', check_area=False)
    unrefined = query_database(DATABASE, g)

    results = 'default'
    if MSG is not None:
        MSG.destroy()

    # Add message to window
    message = Label(window, text=results, font=("Arial", 25))
    message.grid(row = 6, column = 4, columnspan = 2)

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
    canvas.get_tk_widget().grid(row = 2, column = 4, columnspan = 2, rowspan = 2)

    PREVIOUS = canvas.get_tk_widget()

"""
FILE SELECT
"""

SELECTED_FILE = 'assets/test.png'

def select_file():
    global SELECTED_FILE

    filetypes = (
        ('PNG files', '*.png'),
        ('JPG files', '*.jpg'),
        ('JPEG files', '*.jpeg')
    )

    filename = fd.askopenfilename(
        title='Open an image file',
        initialdir='.',
        filetypes=filetypes)

    showinfo(
        title='Selected File',
        message=filename
    )

    SELECTED_FILE = filename

"""
WINDOW AND CANVAS
"""

CANVAS_WIDTH  = 800
CANVAS_HEIGHT = 800

def create_window():
    global MODE, INPUT_MODE, PATHS, PREVIOUS

    # Create window
    master = Tk()
    master.title("Sketching!")

    # On window close, exit
    master.protocol("WM_DELETE_WINDOW", clean_exit)
    
    # ---------------
    # CANVAS
    # ---------------

    # Set default output mode
    MODE = IntVar(value=GRAPH_MODE)
    INPUT_MODE = IntVar(value=CANVAS_INPUT)

    # Create button to plot drawing
    b = Button(master, text="Plot", command=lambda: plot(master, PATHS))
    b.grid(row = 0, column = 0)

    # Create button to clear drawing
    cb = Button(master, text="Clear", command=lambda: clear(c))
    cb.grid(row = 0, column = 1)

    # Create button to exit 
    eb = Button(master, text="Submit", command=lambda: submit(master, get_line_strings(PATHS)))
    eb.grid(row = 0, column = 2)

    # Create canvas
    c = Canvas(master, 
               bg='white',
               width=CANVAS_WIDTH, 
               height=CANVAS_HEIGHT
               )
    c.grid(row = 2, column = 0, columnspan = 3, rowspan = 3)

    # Paint on canvas on mouse movement
    c.bind("<B1-Motion>", lambda e: paint(e, c))

    # Stop painting on canvas on mouse release
    c.bind("<ButtonRelease-1>", finalize)

    # Radio buttons for output window
    r1 = Radiobutton(master, text="Graph", variable=MODE, value=GRAPH_MODE)
    r1.grid(row = 1, column = 0)

    r2 = Radiobutton(master, text="Polygon", variable=MODE, value=POLYGON_MODE)
    r2.grid(row = 1, column = 1)

    r3 = Radiobutton(master, text="Linestring", variable=MODE, value=LINESTRING_MODE)
    r3.grid(row = 1, column = 2)

    # --------------------
    # File upload
    # --------------------

    # Add file upload button
    file_upload = ttk.Button(
        master,
        text='Open an image file',
        command=select_file
    )
    file_upload.grid(row = 0, column = 4)

    f = Label(master, text=SELECTED_FILE) #, font=("Times New Roman", 15))
    f.grid(row = 0, column = 5)

    # Radio buttons for output window
    o1 = Radiobutton(master, text="Canvas", variable=INPUT_MODE, value=CANVAS_INPUT)
    o1.grid(row = 1, column = 4)

    o2 = Radiobutton(master, text="File", variable=INPUT_MODE, value=FILE_INPUT)
    o2.grid(row = 1, column = 5)

    # Put empty placeholder canvas
    placeholder = Canvas(master, 
            bg='white',
            width=600, 
            height=500
            )
    placeholder.grid(row = 2, column = 4, columnspan = 2, rowspan = 2)

    PREVIOUS = placeholder

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
   