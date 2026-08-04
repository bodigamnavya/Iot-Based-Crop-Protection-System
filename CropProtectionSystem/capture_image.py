import cv2
camera = cv2.VideoCapture(0)
while True:
    success, frame = camera.read()
    if not success:
        print("Camera not working")
        break
    cv2.imshow("Press 'S' to save the image",frame)
    key = cv2.waitKey(1)
    if key == ord('S'):
        cv2.imwrite("animal.jpg",frame)
        print("Image saved Successfully")
        break
    if key ==27:
        print("Program Closed")
        break
    
camera.release()
cv2.destroyAllWindows()