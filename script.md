Set is a card game in which players try to identify sets of cards that satisfy
certain conditions as quickly as possible. I bought the game on impulse after
watching a Numberphile video about it, but after a few rounds of playing it by
myself, I realized I had no way of telling whether there were no sets in the
hand that I'd dealt myself, or if I just couldn't find them. The only way to be
sure would be to check every possible combination of cards to see if they form a
set. This is a task I had no interest in doing myself, but spending a couple
weeks making the computer do it for me was a very attractive prospect. But
before I get into how I did that, let's get into how Set is actually played.

A card in Set has four features: quantity, shape, color, and shade. Each feature
has three possibilities: there can be between one and three shapes, shapes can
be either pils, squiggles, or diamonds, they can be red, green, or purple, and
they can be solid, striped, or empty. A "Set," as it's called in the game, is a
set of three cards in which each feature is either all the same or all different
across the three cards. For instance, these three cards form a set, while these
three do not, as **<REASON>**. The game is played by dealing out twelve cards,
and whoever correctly identifies a set wins a point. The three cards of the set
are removed, and three new ones are dealt in their place.

Before concerning ourselves with how to tell if three cards form a set, we first
have to figure out how to take the image of twelve cards and turn it into a
representation of those cards that we can work with. For this, I turned to
OpenCV, a computer vision library. OpenCV lets us capture frames from a webcam
and then do **things** to them! Let's start with identifying the shapes of the
twelve cards in the frame. The `cv.Canny()` function takes a grayscale image and
marks all of its edges in the output, and then we can use the
`cv.findContours()` function to get all the shapes in the image. It returns an
array of contours as well as a tree structure representing which contours are
inside which. In our case, these contours are the outlines of each card and the
shapes on them. This gives us duplicate contours, so we have to traverse the
hierarchy to get exactly one contour for each card or shape. We start at the top
level of the hierarchy, which contains the twelve outermost card outlines. For
each card, we mark the topmost contour as the outline of the card, and then
descend the hierarchy until we see a significant decrease in the areas of the
current and next contours. This indicates that we've moved from the outline of
the card to the outline of one of its shapes. Then, we take all the contours at
that level - the level of the first shape contour, and mark them as the contours
of the card's shapes. This gives us exactly one contour for each shape, and one
for the card's outline. We save the indices of each card and its shapes in a
dictionary, and the first step is done!
