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
    canny_output = cv.dilate(canny_output, np.ones((5, 5)), iterations=1)
    canny_output = cv.erode(canny_output, np.ones((5, 5)), iterations=1)
    # cv.imshow("output", canny_output)
    # return

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

    # polyPoints = []
    # for c in cards:
    #     for s in cards[c]:
    #         epsilon = cv.getTrackbarPos("epsilon", "output") / 100
    #         approx = cv.approxPolyDP(contours[s], epsilon, True)
    #         polyPoints.append(len(approx))

    # draw_histogram(polyPoints)

    out = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
    for c in cards:
        cv.drawContours(out, contours, c, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
        for s in cards[c]:
            cv.drawContours(out, contours, s, (255, 255, 255), 1, cv.LINE_8, hierarchy, 0)
            # epsilon = (cv.getTrackbarPos("epsilon", "output") / 10000) * cv.arcLength(contours[s], True)
            epsilon = (230 / 10000) * cv.arcLength(contours[s], True)
            approx = cv.approxPolyDP(contours[s], epsilon, True)
            [x, y, w, h] = cv.boundingRect(contours[s])
            cv.putText(out, str(len(approx)), (x, y), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv.LINE_AA)
            if len(approx) < 5:
                color = (0, 0, 255)
            else:
                color = (255, 0, 0)
            cv.drawContours(out, [approx], 0, color, 1, cv.LINE_8)

    rows = canny_output.shape[0]
    circles = cv.HoughCircles(canny_output, cv.HOUGH_GRADIENT, 1, rows / 8, param1=100, param2=30, minRadius=1, maxRadius=30)

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            # circle center
            cv.circle(out, center, 1, (0, 100, 100), 3)
            # circle outline
            radius = i[2]
            cv.circle(out, center, radius, (255, 0, 255), 3)

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
