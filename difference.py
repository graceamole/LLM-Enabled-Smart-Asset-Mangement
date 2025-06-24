from skimage.metrics import structural_similarity
import imutils
import cv2
import numpy as np
#img1 = cv2.imread("/content/sample_data/objs456_dist1_U_scene2.jpg")
#img2 = cv2.imread("/content/sample_data/objs456_dist1_U_scene3.jpg")
img1= cv2.imread("Assets/IMG_9599.JPG")
img2= cv2.imread("Assets/IMG_9601.JPG")


# Convert to grayscale
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

(score, diff) = structural_similarity(gray1, gray2, full=True)
diff= (diff * 255) .astype ("uint8")
print("SSIM:{}".format(score))

thresh = cv2.threshold(diff, 0, 128,
    cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU) [1]
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
     cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)

no_of_differences = 0
for c in cnts :
  (x, y, w, h) = cv2.boundingRect(c)
  rect_area = w * h
  if rect_area > 10:
    no_of_differences += 1
    cv2.rectangle(img1, (x, y),(x + w, y + h), (0,0,255), 2)
    cv2.rectangle(img2, (x, y),(x + w, y + h), (0,0,255), 2)
print("No of Differences=", no_of_differences)
cv2.imshow("No of Differences",img1)
cv2.imshow("No of Differences",img2)
cv2.imshow("No of Differences",diff)
cv2.waitKey(0)