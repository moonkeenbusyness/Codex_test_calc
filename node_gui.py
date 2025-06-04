import time
import math
import uuid
from dearpygui import dearpygui as dpg


# containers for the graph system
nodes = {}
attr_owner = {}
links = []
node_count = 0
x_data = []
y_data = []
start_time = time.time()


def _register_attr(node, attr):
    """Register attribute ownership."""
    attr_owner[attr] = node


def _link_lookup(attr):
    for l in links:
        if l["dest"] == attr:
            return l["source"]
    return None


def _get_input_value(attr, widget=None):
    src = _link_lookup(attr)
    if src is not None and src in attr_owner:
        owner = attr_owner[src]
        if "value" not in nodes[owner]:
            _evaluate_node(owner)
        return nodes[owner].get("value", 0.0)
    if widget is not None and dpg.does_item_exist(widget):
        return dpg.get_value(widget)
    return 0.0


def _evaluate_node(tag):
    node = nodes[tag]
    ntype = node["type"]

    if ntype == "time":
        value = time.time() - start_time
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype == "const":
        value = dpg.get_value(node["widget"])
    elif ntype == "add":
        a = _get_input_value(node["a"], node["a_widget"])
        b = _get_input_value(node["b"], node["b_widget"])
        value = a + b
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype == "sub":
        a = _get_input_value(node["a"], node["a_widget"])
        b = _get_input_value(node["b"], node["b_widget"])
        value = a - b
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype == "mul":
        a = _get_input_value(node["a"], node["a_widget"])
        b = _get_input_value(node["b"], node["b_widget"])
        value = a * b
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype == "div":
        a = _get_input_value(node["a"], node["a_widget"])
        b = _get_input_value(node["b"], node["b_widget"])
        value = a / b if b else 0
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype in {"sin", "cos", "tan"}:
        a = _get_input_value(node["in"], node["in_widget"])
        fn = getattr(math, ntype)
        value = fn(a)
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype == "display":
        value = _get_input_value(node["in"])
        dpg.set_value(node["label"], f"{value:.2f}")
    elif ntype == "plot":
        value = _get_input_value(node["in"])
        x_data.append(time.time() - start_time)
        y_data.append(value)
        dpg.set_value(node["series"], [x_data, y_data])
    else:
        value = 0.0

    node["value"] = value


def _process_graph():
    for tag in list(nodes.keys()):
        _evaluate_node(tag)
    dpg.set_frame_callback(dpg.get_frame_count() + 1, _process_graph)


def link_callback(sender, app_data):
    link_id = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
    links.append({"id": link_id, "source": app_data[0], "dest": app_data[1]})
    dest_owner = attr_owner.get(app_data[1])
    if dest_owner:
        nodes[dest_owner].setdefault("links", {})[app_data[1]] = app_data[0]


def delink_callback(sender, app_data):
    dpg.delete_item(app_data)
    for link in links:
        if link["id"] == app_data:
            dest_owner = attr_owner.get(link["dest"])
            if dest_owner and link["dest"] in nodes[dest_owner].get("links", {}):
                del nodes[dest_owner]["links"][link["dest"]]
            links.remove(link)
            break


def delete_selected(sender, app_data):
    for l in dpg.get_selected_links("node_editor"):
        delink_callback("node_editor", l)
    for n in dpg.get_selected_nodes("node_editor"):
        dpg.delete_item(n)
        if n in nodes:
            for a in nodes[n].get("attrs", []):
                attr_owner.pop(a, None)
            nodes.pop(n)


def add_const_node(default=0.0, label="Const"):
    global node_count
    tag = f"const_{uuid.uuid4().hex[:6]}"
    node_count += 1
    with dpg.node(label=label, parent="node_editor", tag=tag):
        with dpg.node_attribute(tag=f"{tag}_out", attribute_type=dpg.mvNode_Attr_Output):
            dpg.add_input_float(default_value=default, width=100, tag=f"{tag}_val")
    nodes[tag] = {
        "type": "const",
        "out": f"{tag}_out",
        "widget": f"{tag}_val",
        "attrs": [f"{tag}_out"],
    }
    _register_attr(tag, f"{tag}_out")
    return tag


def add_arith_node(op):
    global node_count
    tag = f"{op}_{uuid.uuid4().hex[:6]}"
    node_count += 1
    with dpg.node(label=op.capitalize(), parent="node_editor", tag=tag):
        with dpg.node_attribute(tag=f"{tag}_a", attribute_type=dpg.mvNode_Attr_Input):
            dpg.add_input_float(width=80, tag=f"{tag}_a_val")
        with dpg.node_attribute(tag=f"{tag}_b", attribute_type=dpg.mvNode_Attr_Input):
            dpg.add_input_float(width=80, tag=f"{tag}_b_val")
        with dpg.node_attribute(tag=f"{tag}_out", attribute_type=dpg.mvNode_Attr_Output):
            dpg.add_text("0.0", tag=f"{tag}_label")
    nodes[tag] = {
        "type": op,
        "a": f"{tag}_a",
        "b": f"{tag}_b",
        "a_widget": f"{tag}_a_val",
        "b_widget": f"{tag}_b_val",
        "out": f"{tag}_out",
        "label": f"{tag}_label",
        "attrs": [f"{tag}_a", f"{tag}_b", f"{tag}_out"],
    }
    _register_attr(tag, f"{tag}_a")
    _register_attr(tag, f"{tag}_b")
    _register_attr(tag, f"{tag}_out")
    return tag


def add_trig_node(func):
    global node_count
    tag = f"{func}_{uuid.uuid4().hex[:6]}"
    node_count += 1
    with dpg.node(label=func.capitalize(), parent="node_editor", tag=tag):
        with dpg.node_attribute(tag=f"{tag}_in", attribute_type=dpg.mvNode_Attr_Input):
            dpg.add_input_float(width=80, tag=f"{tag}_val")
        with dpg.node_attribute(tag=f"{tag}_out", attribute_type=dpg.mvNode_Attr_Output):
            dpg.add_text("0.0", tag=f"{tag}_label")
    nodes[tag] = {
        "type": func,
        "in": f"{tag}_in",
        "in_widget": f"{tag}_val",
        "out": f"{tag}_out",
        "label": f"{tag}_label",
        "attrs": [f"{tag}_in", f"{tag}_out"],
    }
    _register_attr(tag, f"{tag}_in")
    _register_attr(tag, f"{tag}_out")
    return tag


def add_display_node():
    global node_count
    tag = f"display_{uuid.uuid4().hex[:6]}"
    node_count += 1
    with dpg.node(label="Display", parent="node_editor", tag=tag):
        with dpg.node_attribute(tag=f"{tag}_in", attribute_type=dpg.mvNode_Attr_Input):
            pass
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("0.0", tag=f"{tag}_label")
    nodes[tag] = {
        "type": "display",
        "in": f"{tag}_in",
        "out": f"{tag}_in",
        "label": f"{tag}_label",
        "attrs": [f"{tag}_in"],
    }
    _register_attr(tag, f"{tag}_in")
    return tag


def add_time_node():
    tag = f"time_{uuid.uuid4().hex[:6]}"
    with dpg.node(label="Time", parent="node_editor", tag=tag):
        with dpg.node_attribute(tag=f"{tag}_out", attribute_type=dpg.mvNode_Attr_Output):
            dpg.add_text("0.0", tag=f"{tag}_label")
    nodes[tag] = {
        "type": "time",
        "out": f"{tag}_out",
        "label": f"{tag}_label",
        "attrs": [f"{tag}_out"],
    }
    _register_attr(tag, f"{tag}_out")
    return tag


def add_plot_node():
    tag = f"plot_{uuid.uuid4().hex[:6]}"
    with dpg.node(label="Plot", parent="node_editor", tag=tag):
        with dpg.node_attribute(tag=f"{tag}_in", attribute_type=dpg.mvNode_Attr_Input):
            pass
    nodes[tag] = {
        "type": "plot",
        "in": f"{tag}_in",
        "out": f"{tag}_in",
        "series": "sine_series",
        "attrs": [f"{tag}_in"],
    }
    _register_attr(tag, f"{tag}_in")
    return tag


# Build UI

dpg.create_context()

with dpg.window(label="Node Editor"):
    with dpg.tab_bar():
        with dpg.tab(label="Arithmetic"):
            dpg.add_button(label="Add", callback=lambda: add_arith_node("add"))
            dpg.add_button(label="Sub", callback=lambda: add_arith_node("sub"))
            dpg.add_button(label="Mul", callback=lambda: add_arith_node("mul"))
            dpg.add_button(label="Div", callback=lambda: add_arith_node("div"))
        with dpg.tab(label="Trig"):
            dpg.add_button(label="Sin", callback=lambda: add_trig_node("sin"))
            dpg.add_button(label="Cos", callback=lambda: add_trig_node("cos"))
            dpg.add_button(label="Tan", callback=lambda: add_trig_node("tan"))
        with dpg.tab(label="Const"):
            dpg.add_button(label="Const", callback=add_const_node)
            dpg.add_button(label="Pi", callback=lambda: add_const_node(math.pi, "Pi"))
            dpg.add_button(label="E", callback=lambda: add_const_node(math.e, "E"))
        with dpg.tab(label="Display"):
            dpg.add_button(label="Number", callback=add_display_node)
            dpg.add_button(label="Plot", callback=add_plot_node)
    dpg.add_button(label="Delete Selected", callback=delete_selected)
    with dpg.node_editor(tag="node_editor", callback=link_callback, delink_callback=delink_callback):
        t = add_time_node()
        s = add_trig_node("sin")
        p = add_plot_node()
        dpg.add_node_link(nodes[t]["out"], nodes[s]["in"], parent="node_editor")
        dpg.add_node_link(nodes[s]["out"], nodes[p]["in"], parent="node_editor")

with dpg.window(label="Plot Window"):
    with dpg.plot(label="Sine", height=400, width=400):
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        with dpg.plot_axis(dpg.mvYAxis, label="y", tag="plot_yaxis"):
            dpg.add_line_series([], [], parent="plot_yaxis", tag="sine_series")


dpg.create_viewport(title="Node GUI", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()

dpg.set_frame_callback(dpg.get_frame_count() + 1, _process_graph)

dpg.start_dearpygui()
dpg.destroy_context()
