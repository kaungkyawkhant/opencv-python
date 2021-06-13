import time
import cv2
import mediapipe as mp


class HandDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB).multi_hand_landmarks
        if self.results:
            for handLms in self.results:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findposition(self, img, handNo=0, draw=True):
        lmlist = []
        if self.results:
            myhand = self.results[handNo]
            for idx, lms in enumerate(myhand.landmark):
                high, width, channel = img.shape
                cx, cy = int(lms.x * width), int(lms.y * high)
                lmlist.append([idx, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 15, (255,0,0), cv2.FILLED)
        return lmlist


def main():
    cap = cv2.VideoCapture(0)
    currentTime = 0
    pastTime = 0
    detector = HandDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmlist = detector.findposition(img, 0, True)
        if len(lmlist)!=0:
            print(lmlist[4])

        currentTime = time.time()
        fps = (1 / (currentTime - pastTime))
        pastTime = currentTime

        cv2.putText(img, str(int(fps)), (60, 100), cv2.FONT_HERSHEY_PLAIN, 5, (255, 0, 0))
        cv2.imshow("Hands", img)
        cv2.waitKey(1)

if __name__ == "__main__":
    main()
