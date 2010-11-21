from curvey import *
from libcurvey import *


def main():
    control_points, knotvec, degree = parse_data(filename=sys.argv[1])
    printar("Parsed Control Points", control_points)
    printar("Parsed Knot Vector", knotvec)
    bspline = BSpline(degree=degree)
    for cp in control_points:
        bspline.insert_control_point(ControlPoint(Point(cp[0], cp[1])))
    bspline.replace_knot_vector(knotvec[0])

    control_points, points = bspline.render()
    print
    print "Parsed Degree", degree
    print
    print "Valid?", bspline.is_valid()
    printar("Control Points", control_points)
    printar("Draw Points", points)

if __name__ == '__main__':
    main()