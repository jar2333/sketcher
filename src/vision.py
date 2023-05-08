import cv2
import matplotlib.pyplot as plt

from src.extraction import snap_round, to_line_string

from numpy import resize


def load_image(filename):
    """
    Loads an image from the image library given its filename. 
    """
    img = cv2.imread(filename) 
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def display_image(img, text='test'):
    """
    Displays a provided image to the user, and wait for any input. Used for debugging.
    """
    imgplot = plt.imshow(img)

    plt.show()

def get_image_line_strings(img, step=40):
    contours, _ = get_contours(img)

    line_strings = []
    for c in contours:
        s = c.shape[0]
        if s > 1:
            points = resize(c, (s, 2))

            rounded = snap_round(points, step=step)

            ls = to_line_string(rounded) 

            line_strings.append(ls)

    return line_strings

def get_contours(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blur = cv2.medianBlur(gray, 7)

    ret, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
    # thresh = cv2.Canny(img,100,200)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy

def draw_contours(img, contours):
    for i in range(len(contours)):
        img2 = cv2.drawContours(img.copy(), contours, i, (0,255,0), 3)
        display_image(img2)