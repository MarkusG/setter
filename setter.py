import cv2 as cv
import numpy as np
import math


def distance_3d(a, b):
    dx = int(a[0]) - int(b[0])
    dy = int(a[1]) - int(b[1])
    dz = int(a[2]) - int(b[2])
    return int(math.sqrt(dx ** 2 + dy ** 2 + dz ** 2))


# given an index in the hierarchy, returns an array of all the contours at the
# same hierarchy level
def get_neighbors(idx, hierarchy):
    # idx might be the first top-level contour, or the last,
    # or somewhere in the middle, so we traverse both ways to get all of the
    # contours at this level
    neighbors = [idx]

    # go forward from top_idx
    cursor = idx
    while hierarchy[0][cursor][0] >= 0:
        neighbors.append(hierarchy[0][cursor][0])
        cursor = hierarchy[0][cursor][0]

    # go backward from top_idx
    cursor = idx
    while hierarchy[0][cursor][1] >= 0:
        neighbors.append(hierarchy[0][cursor][1])
        cursor = hierarchy[0][cursor][1]

    return neighbors


def recognize_cards(frame):

    # detect edges
    canny_output = cv.Canny(frame, 100, 200)

    # get blurred frame
    blur = cv.GaussianBlur(frame, (15, 15), 0)

    # dilate and erode, to clean up the edges for contour finding
    canny_output = cv.dilate(canny_output, np.ones((5, 5)), iterations=1)
    canny_output = cv.erode(canny_output, np.ones((5, 5)), iterations=1)

    # find contours
    contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return

    # get the index of a top-level contour (i.e. a card outline)
    top_idx = 0
    while hierarchy[0][top_idx][3] >= 0:
        top_idx = hierarchy[0][top_idx][3]

    card_idxs = get_neighbors(top_idx, hierarchy)

    # a dictionary with card outline indices as keys and arrays of shape
    # outline indices as values
    cards = {}

    for i in card_idxs:
        cursor = i
        while hierarchy[0][cursor][2] >= 0:
            current = hierarchy[0][cursor][2]
            current_area = cv.contourArea(contours[cursor])
            child_area = cv.contourArea(contours[current])
            # if the areas of the current contour and the next contour down in the
            # hierarchy are within 1%, then we consider them duplicates
            if (current_area - child_area) / current_area < 0.3:
                cursor = current
                continue

            # at this point, there has been a significant change in contour area, so
            # we've moved from a card outline to a shape outline
            neighbors = get_neighbors(current, hierarchy)
            cards[i] = []
            for j in neighbors:
                cards[i].append(j)
            break

    out = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
    for c in cards:
        [card_x, card_y, card_w, card_h] = cv.boundingRect(contours[c])
        card_background = blur[card_y + int(card_h / 10), card_x + int(card_w / 10)]

        count = len(cards[c])
        shape = ''
        color = ''
        shade = ''

        cv.drawContours(out, contours, c, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
        for s in cards[c]:
            # get polygon approximations
            # do two passes: one to distinguish diamonds from pills and
            # squiggles, and one to distinguish between pills and squiggles
            diamond_epsilon = (230 / 10000) * cv.arcLength(contours[s], True)
            diamond_approx = cv.approxPolyDP(contours[s], diamond_epsilon, True)

            pill_epsilon = (85 / 10000) * cv.arcLength(contours[s], True)
            pill_approx = cv.approxPolyDP(contours[s], pill_epsilon, True)

            if len(diamond_approx) < 5:
                shape = 'diamond'
            else:
                if len(pill_approx) > 12:
                    shape = 'squiggle'
                else:
                    shape = 'pill'

            # get the color of the shape (1997)
            # average all the colors of the contour points
            edge_points = contours[s][:, 0]
            edge_b = 0
            edge_g = 0
            edge_r = 0
            for p in edge_points:
                edge_b = edge_b + blur[p[1], p[0], 0]
                edge_g = edge_g + blur[p[1], p[0], 1]
                edge_r = edge_r + blur[p[1], p[0], 2]
            edge_b = int(edge_b / len(edge_points))
            edge_g = int(edge_g / len(edge_points))
            edge_r = int(edge_r / len(edge_points))
            [[[edge_h, edge_s, edge_v]]] = cv.cvtColor(np.uint8([[[edge_b, edge_g, edge_r]]]), cv.COLOR_BGR2HSV)

            [x, y, w, h] = cv.boundingRect(contours[s])

            # classify colors based on thresholds
            # these are user-defined, as they may vary with lighting conditions
            # perhaps we can make them adaptive in the future
            red_thresh = cv.getTrackbarPos("Red threshold", "output")
            green_thresh = cv.getTrackbarPos("Green threshold", "output")
            purple_thresh = cv.getTrackbarPos("Purple threshold", "output")

            if (edge_h < red_thresh):
                color = 'red'
            elif (edge_h > red_thresh and edge_h < green_thresh):
                color = 'green'
            elif (edge_h > green_thresh and edge_h < purple_thresh):
                color = 'purple'

            center_color = blur[int(y + h/2), int(x + w/2)]
            [[[center_h, center_s, center_v]]] = cv.cvtColor(np.uint8([[center_color]]), cv.COLOR_BGR2HSV)
            [[[card_h, card_s, card_v]]] = cv.cvtColor(np.uint8([[card_background]]), cv.COLOR_BGR2HSV)

            # it's been a while, metric spaces. i thought i'd never see you again
            d = distance_3d(center_color, card_background)

            if (d < 30):
                shade = 'empty'
            elif (d < 180):
                shade = 'striped'
            else:
                shade = 'solid'

        count_pos = (int(card_x + card_w / 10), int(card_y + card_h / 10) + 20)
        cv.putText(out, str(count), count_pos, cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
        shape_pos = (int(card_x + card_w / 10), int(card_y + card_h / 10) + 40)
        cv.putText(out, str(shape), shape_pos, cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
        color_pos = (int(card_x + card_w / 10), int(card_y + card_h / 10) + 60)
        cv.putText(out, str(color), color_pos, cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
        shade_pos = (int(card_x + card_w / 10), int(card_y + card_h / 10) + 80)
        cv.putText(out, str(shade), shade_pos, cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)

    cv.imshow("output", out)
    cv.imshow("frame", frame)


def nothing(x):
    pass


cv.namedWindow("output")
cv.createTrackbar("Red threshold", "output", 18, 360, nothing)
cv.createTrackbar("Green threshold", "output", 93, 360, nothing)
cv.createTrackbar("Purple threshold", "output", 220, 360, nothing)

while True:
    cap = cv.VideoCapture("/dev/video2")
    close = 0
    while True:
        ret, frame = cap.read()
        if ret:
            recognize_cards(frame)
            if cv.waitKey(1) == 27:
                close = 1
                break
        else:
            break
    if close:
        break
