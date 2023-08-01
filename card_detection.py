import cv2 as cv
import numpy as np
# import matplotlib.pyplot as plt
import os


def draw_histogram(array):
    os.system('clear')
    for i in range(50):
        print("{0: >2d}: ".format(i), end='')
        for j in array:
            if j == i:
                print("#", end='')
        print()


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
    # cv.imshow("", canny_output)
    # cv.waitKey()

    # find contours
    contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return

    # show histogram of contour areas
    # areas = []
    # for c in contours:
    #     areas.append(cv.contourArea(c))
    #
    # fig, axs = plt.subplots(tight_layout=True)
    # axs.hist(areas, bins=20)
    # plt.show()

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
            if (current_area - child_area) / current_area < 0.01:
                cursor = current
                continue

            # at this point, there has been a significant change in contour area, so
            # we've moved from a card outline to a shape outline
            neighbors = get_neighbors(current, hierarchy)
            cards[i] = []
            for j in neighbors:
                cards[i].append(j)
            break

    polyPoints = []
    for c in cards:
        for s in cards[c]:
            epsilon = cv.getTrackbarPos("epsilon", "output") / 100
            approx = cv.approxPolyDP(contours[s], epsilon, True)
            polyPoints.append(len(approx))

    draw_histogram(polyPoints)

    out = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
    for c in cards:
        cv.drawContours(out, contours, c, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
        for s in cards[c]:
            cv.drawContours(out, contours, s, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
            # epsilon = 0.005 * cv.arcLength(contours[s], True)
            epsilon = cv.getTrackbarPos("epsilon", "output") / 100
            approx = cv.approxPolyDP(contours[s], epsilon, True)
            if len(approx) < 11:
                color = (0, 0, 255)
            elif len(approx) < 15:
                color = (0, 255, 0)
            else:
                color = (255, 0, 0)
            cv.drawContours(out, [approx], 0, color, 1, cv.LINE_8)

    cv.imshow("output", out)


def nothing(x):
    pass


cv.namedWindow("output")
cv.createTrackbar("epsilon", "output", 0, 300, nothing)

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
