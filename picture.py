import cv2
import numpy as np
import imutils

# Load and resize images
img1 = cv2.imread("Assets/IMG_9599.JPG")
img2 = cv2.imread("Assets/IMG_9601.JPG")
img1 = cv2.resize(img1, (600, 360))
img2 = cv2.resize(img2, (600, 360))

# Convert to grayscale
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

# Absolute difference
diff = cv2.absdiff(gray1, gray2)
cv2.imshow("diff(img1, img2)", diff)

# Threshold the diff image
thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

# Dilation to combine adjacent differences
kernel = np.ones((5, 5), np.uint8)
dilate = cv2.dilate(thresh, kernel, iterations=2)
cv2.imshow("Dillation", dilate)

# Find contours
contours = cv2.findContours(dilate.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)

# Draw bounding boxes on a copy of the original
for contour in contours:
    if cv2.contourArea(contour) > 100:  # Filter small areas
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(img1, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.rectangle(img2, (x, y), (x + w, y + h), (0, 0, 255), 2)

# Display the result
x = np.zeros((360,10,3), np.uint8)
result = np.hstack((img1,x, img2))
cv2.imshow("Differences", result)

cv2.waitKey(0)
cv2.destroyAllWindows()
