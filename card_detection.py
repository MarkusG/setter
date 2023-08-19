import cv2 as cv
import numpy as np
# import matplotlib.pyplot as plt


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

    # card_contours, _ = cv.findContours(canny_output, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    # out = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

    # for i in range(len(card_contours)):
    #     # cv.drawContours(out, card_contours, i, (255, 255, 255), 1, cv.LINE_8)
    #     [x, y, w, h] = cv.boundingRect(card_contours[i])
    #     x = x + 10
    #     y = y + 10
    #     w = w - 20
    #     h = h - 20
    #     out[y:y+h, x:x+w] = [255, 255, 255]
    #     shape_contours, _ = cv.findContours(canny_output[y:y+h, x:x+w], cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    #     print(shape_contours)
    #     for c in shape_contours:
    #         for p in c:
    #             p[0][0] = p[0][0] + x
    #             p[0][1] = p[0][1] + y
    #         cv.drawContours(out, [c], 0, (0, 0, 255), 1, cv.LINE_8)
    #     cv.rectangle(out, (int(x), int(y)), (int(x + w), int(y + h)), (255, 0, 0), 1)
    #     cv.putText(out, str(len(shape_contours)), (x, y), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv.LINE_AA)
    # cv.imshow("output", out)
    # return

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
        cv.drawContours(out, contours, c, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
        for s in cards[c]:
            cv.drawContours(out, contours, s, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
            # get polygon approximations
            # do two passes: one to distinguish diamonds from pills and
            # squiggles, and one to distinguish between pills and squiggles
            diamond_epsilon = (230 / 10000) * cv.arcLength(contours[s], True)
            diamond_approx = cv.approxPolyDP(contours[s], diamond_epsilon, True)

            pill_epsilon = (85 / 10000) * cv.arcLength(contours[s], True)
            pill_approx = cv.approxPolyDP(contours[s], pill_epsilon, True)

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
                out[y:y+h, x:x+w] = (0, 0, 255)
            elif (edge_h > red_thresh and edge_h < green_thresh):
                out[y:y+h, x:x+w] = (0, 255, 0)
            elif (edge_h > green_thresh and edge_h < purple_thresh):
                out[y:y+h, x:x+w] = (255, 0, 255)

            # out[y:y+h, x:x+w] = (edge_b, edge_g, edge_r)

            center_color = blur[int(y + h/2), int(x + w/2)]
            [[[center_h, center_s, center_v]]] = cv.cvtColor(np.uint8([[center_color]]), cv.COLOR_BGR2HSV)

            # out[y:y+h, x:x+w] = center_color

            cv.putText(out, "({}, {}, {})".format(center_h, center_s, center_v), (x, y), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv.LINE_AA)

            if (center_h > 10 and center_h < 100 and center_s < 100):
                cv.putText(out, "empty", (x + int(w / 2), y + int(h / 2)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)

            # if (center_s > 100):
            #     cv.putText(out, "solid", (x + int(w / 2), y + int(h / 2)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            # elif (center_s > 20 or (center_s > 10 and center_h > 100)):
            #     cv.putText(out, "striped", (x + int(w / 2), y + int(h / 2)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            # else:
            #     cv.putText(out, "empty", (x + int(w / 2), y + int(h / 2)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)

            if len(diamond_approx) < 5:
                color = (0, 0, 255)
            else:
                if len(pill_approx) > 12:
                    color = (0, 255, 0)
                else:
                    color = (255, 0, 0)
            cv.drawContours(out, contours, s, color, 1, cv.LINE_8)

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
