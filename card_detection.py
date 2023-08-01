import cv2 as cv
import numpy as np

# load the image as grayscale
src = cv.imread("set.png", cv.IMREAD_GRAYSCALE)
cv.imshow("", src)
cv.waitKey()

# detect edges
canny_output = cv.Canny(src, 100, 200)
cv.imshow("", canny_output)
cv.waitKey()

# find contours
contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
out = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

# get the index of a top-level contour (i.e. a card outline)
top_idx = 0
while hierarchy[0][top_idx][3] >= 0:
    top_idx = hierarchy[0][top_idx][3]

# at this point, top_idx might be the first top-level contour, or the last,
# or somewhere in the middle, so we traverse both ways to get all of the
# contours at this level
card_outline_idxs = []
card_outline_idxs.append(top_idx)

# go forward from top_idx
cursor = top_idx
while hierarchy[0][cursor][0] >= 0:
    card_outline_idxs.append(hierarchy[0][cursor][0])
    cursor = hierarchy[0][cursor][0]

# go backward from top_idx
cursor = top_idx
while hierarchy[0][cursor][1] >= 0:
    card_outline_idxs.append(hierarchy[0][cursor][1])
    cursor = hierarchy[0][cursor][1]

print(card_outline_idxs)

# get the index of a contour that's one down from the top level. this should be
# where all of the outermost shape contours lie
shape_idx = hierarchy[0][top_idx][2]
cv.drawContours(out, contours, shape_idx, (255, 255, 255), 2, cv.LINE_8, hierarchy, 0)
cv.imshow("", out)
cv.waitKey()

for i in range(len(card_outline_idxs)):
    cv.drawContours(out, contours, card_outline_idxs[i], (255, 255, 255), 2, cv.LINE_8, hierarchy, 0)
    cv.imshow("", out)
    cv.waitKey()
