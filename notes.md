1. Edge detection to pick out cards
2. [inRange](https://docs.opencv.org/4.x/da/d97/tutorial_threshold_inRange.html) to determine color and shading
3. [Hough line transform](https://docs.opencv.org/4.x/d9/db0/tutorial_hough_lines.html) and [Hough circle transform](https://docs.opencv.org/4.x/d4/d70/tutorial_hough_circle.html) to detect shape
 * Diamonds are straight lines, pills are straight lines and semicircles, squiggles can be determined by elimination
 * Find diamonds by filtering on slope - need to adjust for possible rotation of card
  * Determine edges of card and apply affine transformation
4. something else to determine count and shape
5. Or perhaps just use Hough Ballard with a template for every card
 * This will probably be extremely slow, as we'd have to check against a template for all 81 cards in the game

Card outline detection:

We started off by copying the contour detection example from the docs.
It successfully recognizes the contours of the cards and the shapes inside them,
but has the issue of finding duplicate contours. We can either use the
RETR_EXTERNAL retrieval mode to only extract the outermost contours (the card
outlines), but then we have to run the contour finder again later to find the
shapes in each card. Let's see if we can find a way to remove duplicates based
on their similarity.

We could determine duplicates based on contour area. I initially thought of this
to distinguish which contours are card outlines and which are shape outlines, as
we should have exactly 12 cards and they will have a much greater area than the
shapes. This won't work for shapes though, as there will be a variable number of
shapes with the same area. We'll need to determine duplicity by the points of
the contours themselves, which I don't think will be too hard.

Actually, we don't even need to worry about determining similarity. We have
hierarchy data, and we're only concerned about two hierarchical levels - the
top one (where the card outlines lie) and the bottom one (where the shape
outlines lie). Thus, we should have exactly 12 card outlines at the top
hierarchy level, and a variable (but correct) number of shape outlines at the
bottom level.

Success! We can successfully determine which contours are card outlines based on
the fact that they're at the top of the hierarchy. Let's see if a similar method
is possible for the shape outlines. One problem could be that the "bottom" of
the hierarchy may not contain all the shape outlines, as different shapes may
have different numbers of duplicate outlines detected. On second thought, forget
the bottom of the hierarchy. Let's just start with a card outline, go one
hierarchy level down, and then we should have the correct number of contours...
except we might not be able to distinguish which shapes belong to which cards.
Let's play around with it and see.

Well, regardless of whether or not we can tell which card a shape belongs to
based on hierarchy data (I doubt we can), we should still get a set of contours
that's 1:1 with the actual shapes on the cards. We can check if a point on a
shape contour is inside a card to determine ownership.

Wow, that was completely wrong. The whole point of this is that we have
duplicate *nested* contours for everything, including card outlines. So the
contours that are one level down from the top will most likely be duplicate card
outlines, of which we have an unknown number.

Okay, so here's what we're gonna do: We'll fall back on area analysis. Let's
assume that, in our iamge, the card outlines are all roughly identical in area.
Under this assumption, for each card, we can walk down the hierarchy until we
find a contour with a significantly lesser area than that of a card outline.
That will be our shape outline, and then its neighbors should be the remaining
shapes on the card.

Just for fun, I plotted a histogram of all the contour areas to confirm that,
indeed, there is a large gap between our card outline areas and shape outline
areas. This is kind of obvious, but I just wanted to plot a histogram, okay?
I was also thinking this might give me an idea of how close two areas need to be
to be considered similar (e.g. +/- 5000 square units), but this will depend on
the image size, so it should be relative anyway.

Ooh! Maybe we can identify which shapes are which by contour perimeter, or by
approximating them to polygons. I'll worry about that once I'm done actually
getting the shape outlines.

It worked. And I think it solves our ownership issues too. I am 99% sure that
the hierarchy is in fact a tree structure, and we don't have to worry about
shapes from different cards getting mixed together. I'm going to whip up a quick
dummy image in GIMP to make sure.

Now for shape recognition. Let's see if the perimeters of each shape are
distinct enough to determine which is which. Oh yeah, it's histogram time again.

Well, the perimeters are too similar between shapes to be useful, as are the
areas. Onto other methods.

It looks like polygon approximation of each shape could be promising. If we
set the epsilon correctly, the number of points needed to approximate the
contour could tell us what kind of shape it is. Histogram time again.

It looks like an epsilon of 0.6% of the arc length gives us good enough data
*for this test image*. I'll have to see later on how it behaves on a more varied
data set.

Fuck it, trying to get a live histogram with matplotlib is way harder than it
needs to be. It seems like live updating any other plot is relatively
straightforward, but not for a histogram because we can't reset the underlying
data on it. I'll just draw it in the terminal.

My love of histograms has misled me. I might as well just try to classify the
shapes and highlight them in the video output accordingly, and then I can see
how accurate the polygon method is.

It's not very accurate. The squiggles can be consistently identified, but
diamonds and pills are a total toss-up. Maybe I can tweak the parameters and
make it more reliable.

Squiggles are the only shape that are non-convex. Now we just have to
distinguish between diamonds and pills, which we should be able to do reliably
with circle detection.

After dilating the edge detection output, our contours match a bit better and
polygon approximation works well enough. I think if we take one second of frames
and then take the most frequently occurring classifications, we'll get reliable
results.
