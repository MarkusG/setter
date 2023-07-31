1. Edge detection to pick out cards
2. [inRange](https://docs.opencv.org/4.x/da/d97/tutorial_threshold_inRange.html) to determine color and shading
3. [Hough line transform](https://docs.opencv.org/4.x/d9/db0/tutorial_hough_lines.html) and [Hough circle transform](https://docs.opencv.org/4.x/d4/d70/tutorial_hough_circle.html) to detect shape
    * Diamonds are straight lines, pills are straight lines and semicircles, squiggles can be determined by elimination
    * Find diamonds by filtering on slope - need to adjust for possible rotation of card
4. something else to determine count and shape
