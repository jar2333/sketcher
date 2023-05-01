from tkinter import *

"""
Adapted from https://python-course.eu/tkinter/canvas-widgets-in-tkinter.php
"""

canvas_width = 500
canvas_height = 150

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

def main():
    master = Tk()
    master.title("Sketching!")

    c = Canvas(master, 
               width=canvas_width, 
               height=canvas_height
               )
    c.pack(expand=YES, fill=BOTH)

    # Bind the paint function to be called on Button1 movement
    c.bind("<B1-Motion>", lambda e: paint(e, c))

    # Bind the finalize function to be called on Button1 release
    c.bind("<ButtonRelease-1>", finalize)

    message = Label(master, text="Press and Drag the mouse to draw")
    message.pack(side=BOTTOM)
    
    B = Button(master, text ="Submit", command=lambda: print(SKETCH))
    B.pack()
        
    mainloop()

if __name__ == "__main__":
    main()
   