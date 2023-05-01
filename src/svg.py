import numpy as np

import svgpathtools
import drawsvg as draw

from xml.dom import minidom

import os

"""
----------------------------
-- SVG TO SHAPE CONVERSION
----------------------------
"""

def to_control_points(path):
    """
    Convert a path comprised of curves to an array of control points.
    """
    points = [[(point.real, point.imag) for point in b.bpoints()] for b in path]
    
    return np.array(sum(points, []))

"""
----------------------------
-- LOADING
----------------------------
"""

def load(filename):
    """
    Loads an svg image from the image library given its filename. 
    """
    doc = minidom.parse(filename)
    
    attribs = []
    for item in doc.getElementsByTagName('g'):
        attribs += [(a.name, a.value) for a in item.attributes.values()]
    attribs = dict(attribs)
    
    path_strings = []
    
    for path in doc.getElementsByTagName('path'):
        try:
            p = svgpathtools.parse_path(path.getAttribute('d'))
            path_strings.append(p)
        except:
            pass
    
    doc.unlink()
    
    return {'attrib': attribs, 'paths': path_strings, 'filename': filename}

"""
----------------------------
-- LOADING FILES
----------------------------
"""

IMAGE_DIRECTORY = os.sep.join(['assets', 'svg'])

def load_svg_files(ext='svg'):
    """
    Returns an iterator that yields the image file paths and their labels.
    """    
    def get_label(path):
        return path.split(os.sep)[-1]
    
    files = []
    
    for r, _, f in os.walk(IMAGE_DIRECTORY):
        for file in f:
            if file.endswith(f'.{ext}'):
                label = get_label(r)
                file_path = os.path.join(r, file)
                
                files.append((file_path, label))
                
    return files


def load_svg_images(files):
    """
    Returns an iterator that yields the image data and their labels.
    """
    for f, l in files:
        print(f)
        yield load(f), l

"""
----------------------------
-- DISPLAY SVG
----------------------------
"""

def display(img, text='test'):
    """
    Displays a provided image to the user, and wait for any input. Used for debugging.
    
    See svg reference to implement svg commands:
    https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/d
    """
    def draw_curve(command, args, drawn_path):
        if command == 'C':
            drawn_path.C(*args)
        elif command == 'L':
            drawn_path.L(*args)
            
    def draw_text(args, d, i):
        text = draw.Text(str(i), 8, args[0], args[1], fill='blue') # 8pt text
        d.append(text)
        
    def draw_intersections(paths, current_index):
        current_path = paths[current_index]
        for i, path in enumerate(paths):
            if i == current_index:
                continue
                
            for (T1, seg1, t1), (T2, seg2, t2) in current_path.intersect(path):
                point = current_path.point(T1)
                d.append(draw.Circle(point.real, point.imag, 10, fill='red', stroke_width=2, stroke='black'))
                d.append(draw.Text(str(current_index), 8, point.real-4, point.imag+3, fill='blue'))
        
    # Start canvas (hard coded to 800 by 800 in dataset)
    d = draw.Drawing(800, 800) 
    
    paths  = img['paths']
    attrib = img['attrib']
    
    for i, p in enumerate(paths):
        # Gets the d-string of the path
        path_string = p.d()
        
        # Start drawing path
        drawn_path = draw.Path(stroke_width=attrib['stroke-width'],
                               stroke=attrib['stroke'],
                               fill=attrib['fill'])
        
        coords = path_string.split()
        
        mx, my = coords[1].split(',')
        drawn_path.M(float(mx), float(my))  # Start path at point (-10, -20)
        
        # Draw each curve comprising the path
        command = ''
        args = []
        for c in coords[2:]:
            if c in ['C', 'L']:
                if not args:
                    continue
                    
                draw_curve(command, args, drawn_path)
                    
                command = c
                args.clear()
                
            elif len(c) > 1:
                args += [float(m) for m in c.split(',')]
                
            else:
                raise NotImplementedError("Unimplemented SVG command.") 

        # Draw the curve
        draw_curve(command, args, drawn_path)
        d.append(drawn_path)
        
        # Draw the index of the path just drawn
        draw_text(args, d, i)
        
        # Draw intersections with other paths
#         draw_intersections(paths, i)
    
    
    return d