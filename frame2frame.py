# version 1.0.0

import copy
import cv2

import torch

from modules import images
import modules.scripts as scripts
from modules import shared
from modules.processing import process_images

import gradio as gr

def get_min_frame_num(frame_list, enabled_list):
    min_frame_num = -1
    for index, frame in enumerate(frame_list):
        if frame is None or enabled_list[index] == False:
            print(f"ControlNet-{index} frame number: 0")
            continue
        else:
            frame_num = len(frame)
            print(f"ControlNet-{index} frame number: {frame_num}")
            if min_frame_num < 0:
                min_frame_num = frame_num
            elif frame_num < min_frame_num:
                min_frame_num = frame_num
    return min_frame_num

def get_all_frames(frames, enabled):
    if frames is None or enabled == False:
        return None

    frame_list = []

    for frame in frames:
        frame_list.append(cv2.imread(frame.name))

    return frame_list

class Script(scripts.Script):
    # def __init__(self) -> None:
    #     super().__init__()

    def title(self):
        return "ControlNet Frame2Frame"

    def show(self, is_img2img):
        return True
        # return scripts.AlwaysVisible

    def uigroup(self, tabname, is_img2img, elem_id_tabname):
        ctrls = ()

        with gr.Row():
            enabled = gr.Checkbox(label='Enable', value=False, elem_id=f"{tabname}_enabled")
            ctrls += (enabled,)
        with gr.Row():
            folder_input = gr.File(file_count="multiple", file_types=['image',], label="Select a input folder")
            ctrls += (folder_input,)

        return ctrls

    def ui(self, is_img2img):
        controls = ()
        max_models = shared.opts.data.get("control_net_max_models_num", 1)
        elem_id_tabname = ("img2img" if is_img2img else "txt2img") + "_controlnet_frame2frame"

        with gr.Group(elem_id=elem_id_tabname):
            with gr.Accordion("ControlNet Frame2Frame", open = False, elem_id="controlnet_frame2frame"):
                if max_models > 1:
                    with gr.Tabs(elem_id=f"{elem_id_tabname}_tabs"):
                        for i in range(max_models):
                            with gr.Tab(f"Control Model - {i}"):
                                controls += self.uigroup(f"ControlNet-{i}", is_img2img, elem_id_tabname)
                else:
                    with gr.Column():
                        controls += self.uigroup(f"ControlNet", is_img2img, elem_id_tabname)

        return controls

    def run(self, p, *args):
        print("ControlNet Frame2Frame")

        max_models = shared.opts.data.get("control_net_max_models_num", 1)
        arg_num = 2

        enabled_list = list(args[0:max_models * arg_num:2])
        frame_list = [get_all_frames(frames, enabled_list[index]) for index,frames in enumerate(args[1:max_models * arg_num:2])]

        frame_num = get_min_frame_num(frame_list, enabled_list)

        if frame_num > 0:
            output_image_list = []

            for frames_index in range(frame_num):
                copy_p = copy.copy(p)
                copy_p.control_net_input_image = []
                for frames in frame_list:
                    if frames is None:
                        continue
                    copy_p.control_net_input_image.append(frames[frames_index])
                proc = process_images(copy_p)
                img = proc.images[0]
                output_image_list.append(img)

                copy_p.close()

            proc.images = output_image_list

        else:
            proc = process_images(p)

        return proc