import time
import cv2
import HandTrackingModules as htm

cap = cv2.VideoCapture(0)

detector = htm.HandDetector()
ctime = 0
ptime = 0
while True:
    ref, img = cap.read()
    img = detector.findHands(img, draw=True)
    lmlist = detector.findposition(img, 1, True)
    ctime = time.time()
    fps = (1 / (ctime - ptime))
    ptime = ctime

    cv2.putText(img, str(int(fps)), (70, 100), cv2.FONT_HERSHEY_PLAIN, 5, (255, 0, 0))

    cv2.imshow("Hand Detection", img)
    cv2.waitKey(1)
