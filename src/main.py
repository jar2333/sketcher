from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from extraction import extract_graph, plot_graph
from database import open_database, query_database, close_database, descriptor

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

"""
SUBMISSION TO BACKEND
"""

PREVIOUS = None

def submit(window):
    global PREVIOUS

    # Extract topology graph from drawn paths
    g = extract_graph(PATHS, 'test')
    print(descriptor(g))

    # Query database with the extracted graph
    neighbors = query_database(DATABASE, g, K=50)
    print(neighbors)

    # Plot the extracted graph
    fig = plot_graph(g)

    # Destroy previous plot
    if PREVIOUS is not None:
        PREVIOUS.destroy()

    # create the canvas containing the figure
    canvas = FigureCanvasTkAgg(fig, master=window)  
    canvas.draw()
  
    # place the canvas on the Tkinter window
    canvas.get_tk_widget().pack(side=LEFT)

    PREVIOUS = canvas.get_tk_widget()

"""
WINDOW AND CANVAS
"""

CANVAS_WIDTH  = 500
CANVAS_HEIGHT = 500

def create_window():
    # Create window
    master = Tk()
    master.title("Sketching!")

    # On window close, exit
    master.protocol("WM_DELETE_WINDOW", clean_exit)

    # Create button to submit drawing
    B = Button(master, text="Submit", command=lambda: submit(master))
    B.pack() #side=RIGHT)

    # Create button to clear drawing
    CB = Button(master, text="Clear", command=lambda: clear(c))
    CB.pack() #side=RIGHT)

    # Create button to exit 
    EB = Button(master, text="Exit", command=clean_exit)
    EB.pack() #side=RIGHT)

    # Add message to window
    message = Label(master, text="Press and drag the mouse to draw")
    message.pack(side=BOTTOM)

    # Create canvas
    c = Canvas(master, 
               width=CANVAS_WIDTH, 
               height=CANVAS_HEIGHT
               )
    c.pack(expand=YES, fill=BOTH, side=LEFT)

    # Paint on canvas on mouse movement
    c.bind("<B1-Motion>", lambda e: paint(e, c))

    # Stop painting on canvas on mouse release
    c.bind("<ButtonRelease-1>", finalize)

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
   