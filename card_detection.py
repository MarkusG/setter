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
            # epsilon = (cv.getTrackbarPos("epsilon", "output") / 10000) * cv.arcLength(contours[s], True)
            diamond_epsilon = (230 / 10000) * cv.arcLength(contours[s], True)
            diamond_approx = cv.approxPolyDP(contours[s], diamond_epsilon, True)
            pill_epsilon = (85 / 10000) * cv.arcLength(contours[s], True)
            pill_approx = cv.approxPolyDP(contours[s], pill_epsilon, True)
            [x, y, w, h] = cv.boundingRect(contours[s])
            if len(diamond_approx) < 5:
                color = (0, 0, 255)
            else:
                if len(pill_approx) > 12:
                    color = (0, 255, 0)
                else:
                    color = (255, 0, 0)
            cv.drawContours(out, contours, s, color, 1, cv.LINE_8)

    cv.imshow("output", out)


def nothing(x):
    pass


cv.namedWindow("output")
cv.createTrackbar("epsilon", "output", 0, 1000, nothing)

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
