import cv2 as cv
import numpy as np

src = cv.imread("set.png", cv.IMREAD_GRAYSCALE)
cv.imshow("", src)
cv.waitKey()

canny_output = cv.Canny(src, 100, 200)
cv.imshow("", canny_output)
cv.waitKey()

contours, hierarchy = cv.findContours(canny_output, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
out = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

areas = []
for i in range(len(contours)):
    areas.append(cv.contourArea(contours[i]))
    cv.drawContours(out, contours, i, (100, 100, 100), 2, cv.LINE_8, hierarchy, 0)

cv.imshow("", out)

areas = sorted(areas)
for i in range(len(areas)):
    print(areas[i])

cv.waitKey()
