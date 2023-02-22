import time
from multiprocessing import Process, Pipe, Event
from camera_process import camera_process, CameraProcessInfo


if __name__ == "__main__":
    cam_info = CameraProcessInfo(0)
    last_time = time.time()

    out_pipe_m, out_pipe_s = Pipe()
    in_pipe_m, in_pipe_s = Pipe()
    data_pipe_m, data_pipe_s = Pipe()
    kill_event = Event()

    p = Process(target=camera_process, args=(cam_info, out_pipe_s, in_pipe_s, data_pipe_s, kill_event,))
    p.start()

    out_pipe_m.send("list")
    cameras = in_pipe_m.recv()
    print(f"List of cameras: {cameras}")
    out_pipe_m.send("init")
    res = in_pipe_m.recv()
    print(f"Initialization: {res}")

    try:
        while True:
            # out_pipe_m.send("startexposure")
            # se = in_pipe_m.recv()
            # print(f"Received after starting exposure: {se}")
            # image_ready = False
            # while not image_ready:
            #     out_pipe_m.send("imageready")
            #     image_ready = in_pipe_m.recv()
            #     print(f"Received from image ready: {image_ready}")
            #     time.sleep(0.1)
            #
            # out_pipe_m.send("imagebytes")
            # should_ok = in_pipe_m.recv()
            # print(f"Should be ok = {should_ok}")

            # image_data, im_len = data_pipe_m.recv()
            print("Sending capture...")
            out_pipe_m.send("capture")
            image_data = data_pipe_m.recv()
            current_time = time.time()
            print(f"Received image data of length: {len(image_data)}. Took {current_time-last_time}s")
            last_time = current_time

    except KeyboardInterrupt:
        kill_event.set()

    p.join()
