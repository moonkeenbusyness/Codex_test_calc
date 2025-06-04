import time
import math
from dearpygui import dearpygui as dpg

x_data = []
y_data = []
start_time = time.time()


def update_plot(sender, app_data):
    x = time.time() - start_time
    y = math.sin(x)
    x_data.append(x)
    y_data.append(y)
    dpg.set_value("sine_series", [x_data, y_data])
    dpg.set_value("time_label", f"{x:.2f}")
    dpg.set_value("sin_label", f"{y:.2f}")
    dpg.set_frame_callback(dpg.get_frame_count() + 1, update_plot)


# Build UI

dpg.create_context()

with dpg.window(label="Node Editor"):
    with dpg.node_editor(tag="node_editor"):
        with dpg.node(label="Time"):
            with dpg.node_attribute(tag="time_out", attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("0.0", tag="time_label")
        with dpg.node(label="Sin"):
            with dpg.node_attribute(tag="sin_in", attribute_type=dpg.mvNode_Attr_Input):
                pass
            with dpg.node_attribute(tag="sin_out", attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("0.0", tag="sin_label")
        with dpg.node(label="Plot"):
            with dpg.node_attribute(tag="plot_in", attribute_type=dpg.mvNode_Attr_Input):
                pass
    dpg.add_node_link("time_out", "sin_in", parent="node_editor")
    dpg.add_node_link("sin_out", "plot_in", parent="node_editor")

with dpg.window(label="Plot Window"):
    with dpg.plot(label="Sine", height=400, width=400):
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        with dpg.plot_axis(dpg.mvYAxis, label="y", tag="plot_yaxis"):
            dpg.add_line_series([], [], parent="plot_yaxis", tag="sine_series")


dpg.create_viewport(title="Node GUI", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()

dpg.set_frame_callback(dpg.get_frame_count() + 1, update_plot)

dpg.start_dearpygui()
dpg.destroy_context()
