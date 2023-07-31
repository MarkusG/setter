1. Edge detection to pick out cards
2. [inRange](https://docs.opencv.org/4.x/da/d97/tutorial_threshold_inRange.html) to determine color and shading
3. [Hough line transform](https://docs.opencv.org/4.x/d9/db0/tutorial_hough_lines.html) and [Hough circle transform](https://docs.opencv.org/4.x/d4/d70/tutorial_hough_circle.html) to detect shape
 * Diamonds are straight lines, pills are straight lines and semicircles, squiggles can be determined by elimination
 * Find diamonds by filtering on slope - need to adjust for possible rotation of card
  * Determine edges of card and apply affine transformation
4. something else to determine count and shape
5. Or perhaps just use Hough Ballard with a template for every card
 * This will probably be extremely slow, as we'd have to check against a template for all 81 cards in the game
6. Or we use a generalized contour detector to pick out the shapes
 * If shapes have distinct enough areas, we can use contour area to distinguish them
  * This would fail if the cards were of different sizes in the image (e.g. if the cards were to be held at different distances from the camera). Let's decide to assume that they won't be and not care.
