from Tkinter import *
import ScrolledText
from libcurvey import *
from util import *

class UI:
    default_control_points = """degree=3
dt=0.2
(1, 3)
(2, 4)
(6, 5)
(5, 1)
(2, 1)
(0, 2)
[0,0,0,1,3,4,4,4]"""

    def __init__(self, control_points=None, draw_points=None, degree=3,
            background_color="#cccccc", point_color="#ff0000",
            line_color="#009900",
            canvas_w=640, canvas_h=320):
        self.degree = degree
        self.dt = None
        self.control_points = control_points
        self.control_point_polars = []
        self.draw_points = draw_points
        self.background_color = background_color
        self.point_color = point_color
        self.line_color = line_color
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

        self.perpixel = 32
        self.radius = 4

        # Data structures

        # control points drawn on canvas
        self._canvas_moving_cp = -1 # cp being moved

        # Tk Widgets

        self.master = Tk()
        self.master.title("Curvey")

        self.frame = Frame(self.master)

        self.editbox = Text(self.frame, bg='#cccccc', borderwidth=4, width=20,
                height=30)
        self.editbox.insert('0.0', UI.default_control_points)
        
        self.renderbutton = Button(self.frame, text="Render")
        self.renderbutton.bind('<Button-1>', self.render_cb)

        self.drawing_labels = False
        self.draw_labels_checkbox = Checkbutton(self.frame, text="Control point labels")
        self.draw_labels_checkbox.bind('<Button-1>', self.draw_labels_cb)

        self.clearbutton = Button(self.frame, text="Clear")
        self.clearbutton.bind('<Button-1>', self.clear_cb)

        self.canvas = Canvas(self.frame, width=canvas_w, height=canvas_h, bd=4, background="#cccccc")
        self.image = PhotoImage(file='axis.gif')
        self.canvas.create_image(self.canvas_w/2, self.canvas_h/2, image=self.image)

        self.canvas.bind('<Button-1>', self._canvas_lclick_cb)
        self.canvas.bind('<Double-Button-1>', self._canvas_2lclick_cb)
        self.canvas.bind('<Button-2>', self._canvas_rclick_cb)

        # Grid placements.

        self.frame.grid(row=0, column=0)

        self.editbox.grid(row=2, column=0, columnspan=2)
        self.canvas.grid(row=2, column=3, columnspan=2)

        self.draw_labels_checkbox.grid(row=0, column=0, columnspan=2)
        self.renderbutton.grid(row=1, column=0)
        self.clearbutton.grid(row=1, column=1)

    def _canvas_2lclick_cb(self, event):
        closest = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(closest)
        if 'realcp' not in tags:
            return
        self.canvas.delete(closest)

    def _canvas_rclick_cb(self, event):
        """
        Right click on mouse.
        """
        self.move_cp(event)

    def _canvas_lclick_cb(self, event):
        """
        Left click on mouse.

        Add control point callback. Only add control point there is no control
        points nearby.
        """

        if self._canvas_moving_cp != -1:
            self.move_cp(event)
        else:
            overlapping = self.canvas.find_overlapping(event.x-self.radius,
                    event.y-self.radius,
                    event.x+self.radius, event.y+self.radius)
            cps = self.canvas.find_withtag('realcp')
            overlapping_cps = set(overlapping).intersection(set(cps))

            if not len(overlapping_cps):
                # No overlapping control points.
                self._create_cp(event.x, event.y)

    def move_cp(self, event):
        if self._canvas_moving_cp != -1:
            # Place control point.
            self.canvas.coords(self._canvas_moving_cp,
                    event.x-self.radius, event.y-self.radius,
                    event.x+self.radius, event.y+self.radius)
            self.canvas.itemconfigure(self._canvas_moving_cp, fill="#ff0000", outline="#000000")
            self.canvas.dtag(self._canvas_moving_cp, 'fakecp')
            self.canvas.addtag_withtag('realcp', self._canvas_moving_cp)
            self._canvas_moving_cp = -1
        else:
            # Start moving control point.
            closest = self.canvas.find_closest(event.x, event.y)[0]
            tags = self.canvas.gettags(closest)
            if 'realcp' not in tags:
                return
            self._canvas_moving_cp = closest
            coords = self.canvas.coords(closest)

            # show point as a 'temporary' point
            self.canvas.itemconfigure(closest, fill="#F5D5DD", outline="#C9A5AE")
            self.canvas.dtag(closest, 'realcp')
            self.canvas.addtag_withtag(closest, 'fakecp')

    def clear_cb(self, event=None):
        self.clear_lines()
        self.clear_cps()
        self.clear_labels()

    def clear_cps(self):
        self.canvas.delete('cp')

    def clear_lines(self):
        self.canvas.delete('line')

    def clear_labels(self):
        self.canvas.delete('text')

    def show(self):
        mainloop()

    def draw_labels_cb(self, event=None):
        self.drawing_labels = not self.drawing_labels

    def render_cb(self, event=None):
        # Grab data.
        s = self.editbox.get("0.0", "end")
        lines = s.split('\n')
        control_points, knotvec, self.degree, self.dt = parse_data(lines)

        if len(self.canvas.find_withtag('realcp')):
            control_points = self._cp_coords()
        print control_points

        # Build BSpline.
        bspline = BSpline(degree=self.degree,dt=self.dt)
        for cp in control_points:
            p = ControlPoint(Point(cp[0], cp[1]))
            bspline.insert_control_point(p)
        bspline.replace_knot_vector(knotvec)

        if bspline.is_valid():
            #self.clear_cb()
            self.clear_lines()
            self.clear_labels()

            # Run de Boor to find spline.
            bspline.render()

            # Scale and translate points for drawing.
            control_points, self.control_point_polars, points = bspline.render()

            self.control_points = world2canvas(control_points,
                    self.canvas_w, self.canvas_h, self.perpixel)
            self.draw_points = world2canvas(points, self.canvas_w,
                    self.canvas_h, self.perpixel)

            # Draw.
            self.draw()
        else:
            error_msg = "Invalid curve specified.\nMake sure you have the right number of points for the degree and knot vector specified."
            self.canvas.create_text(self.canvas_w/2, self.canvas_h/2-100,
                    text=error_msg, tags=('text','error'))

    def draw_labels(self):
        magic = -10

        for i, cp in enumerate(self.control_points):
            x, y = tuple(cp)
            
            polar = str(self.control_point_polars[i])
            label = "%d %s" % (i, polar)
            self.canvas.create_text(x, y+magic, text=label,
                    tags=('text', 'label'))

    def draw(self):
        # Draw line segments
        for i in range(len(self.draw_points)-1):
            x1, y1 = tuple(self.draw_points[i])
            x2, y2 = tuple(self.draw_points[i+1])
            self.canvas.create_line(x1, y1, x2, y2, fill="blue", tags=('line',))

        if self.drawing_labels:
            self.draw_labels()

    def _create_cp(self, x, y, tags=('cp','realcp'),
            color="#ff0000", outline="#000000"):
        oval = self.canvas.create_oval(x-self.radius, y-self.radius,
                x+self.radius, y+self.radius, fill=color, outline=outline, tags=tags)
        return oval

    def _cp_coords(self):
        """
        Return the control points draw on screen in world coordinates.
        """
        cps = self.canvas.find_withtag('realcp')
        cps_canvas = map(lambda obj : find_center(*(self.canvas.coords(obj))), cps)
        return canvas2world(cps_canvas, self.canvas_w, self.canvas_h,
                self.perpixel)

def main(argv):
    drawui = UI()
    drawui.show()

if __name__ == '__main__':
    main([])
