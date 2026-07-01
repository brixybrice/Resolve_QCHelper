#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys

resolve = bmd.scriptapp("Resolve")
fusion = resolve.Fusion()
ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

project = resolve.GetProjectManager().GetCurrentProject()
if not project:
    raise RuntimeError("No current project")

timeline = project.GetCurrentTimeline()
if not timeline:
    raise RuntimeError("No current timeline")

win_id = "com.be4post.reviewersnotes.grid"

# Resolve runs this script via exec(), so `__file__` is not defined here. Fall back
# to the known Workflow Integration Plugins install location on macOS.
DEFAULT_PLUGIN_DIR = (
    "/Library/Application Support/Blackmagic Design/DaVinci Resolve/"
    "Workflow Integration Plugins"
)


def get_script_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass

    try:
        candidate = os.path.dirname(os.path.abspath(sys.argv[0]))
        if candidate:
            return candidate
    except Exception:
        pass

    return DEFAULT_PLUGIN_DIR


BUTTONS_CONFIG_PATH = os.path.join(get_script_dir(), "QCHelper_settings", "buttons_config.json")


def load_buttons_config():
    try:
        with open(BUTTONS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load buttons config ({BUTTONS_CONFIG_PATH}): {e}")
        return {}


BUTTONS_CONFIG = load_buttons_config()


def get_button_label(n):
    entry = BUTTONS_CONFIG.get(str(n), {})
    return str(entry.get("btn", n))


def get_button_content(n):
    entry = BUTTONS_CONFIG.get(str(n), {})
    return str(entry.get("content", n))


def tc_to_frames(tc, fps):
    hh, mm, ss, ff = [int(x) for x in tc.replace(";", ":").split(":")]
    return (((hh * 60 + mm) * 60) + ss) * fps + ff


def frames_to_tc(frames, fps):
    if frames < 0:
        frames = 0
    hh = frames // (3600 * fps)
    frames %= (3600 * fps)
    mm = frames // (60 * fps)
    frames %= (60 * fps)
    ss = frames // fps
    ff = frames % fps
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def get_current_objects():
    project_now = resolve.GetProjectManager().GetCurrentProject()
    if not project_now:
        return None, None, None, None

    timeline_now = project_now.GetCurrentTimeline()
    if not timeline_now:
        return project_now, None, None, None

    item = timeline_now.GetCurrentVideoItem()
    if not item:
        return project_now, timeline_now, None, None

    media_pool_item = item.GetMediaPoolItem()
    if not media_pool_item:
        return project_now, timeline_now, item, None

    return project_now, timeline_now, item, media_pool_item


def get_source_tc_at_playhead():
    project_now, timeline_now, item, media_pool_item = get_current_objects()

    if not project_now:
        return "NO PROJECT"
    if not timeline_now:
        return "NO TIMELINE"
    if not item or not media_pool_item:
        return "--:--:--:--"

    source_start_tc = media_pool_item.GetClipProperty("Start TC")
    if not source_start_tc:
        return "--:--:--:--"

    fps_str = project_now.GetSetting("timelineFrameRate")
    if not fps_str:
        return "--:--:--:--"

    fps = int(round(float(str(fps_str).replace(" DF", "").strip())))

    timeline_tc = timeline_now.GetCurrentTimecode()
    timeline_now_frames = tc_to_frames(timeline_tc, fps)
    item_start_frames = int(item.GetStart())

    try:
        source_offset = int(item.GetSourceStartFrame())
    except Exception:
        source_offset = 0

    source_start_frames = tc_to_frames(source_start_tc, fps)
    source_now_frames = source_start_frames + source_offset + (timeline_now_frames - item_start_frames)

    return frames_to_tc(source_now_frames, fps)


def get_existing_reviewer_notes(media_pool_item):
    try:
        val = media_pool_item.GetMetadata("Reviewers Notes")
        if val:
            return str(val).strip()
    except Exception:
        pass

    try:
        val = media_pool_item.GetMetadata("Reviewer Notes")
        if val:
            return str(val).strip()
    except Exception:
        pass

    return ""


def append_reviewer_note(note_text):
    project_now, timeline_now, item, media_pool_item = get_current_objects()

    if not project_now:
        print("NO PROJECT")
        return "NO PROJECT"

    if not timeline_now:
        print("NO TIMELINE")
        return "NO TIMELINE"

    if not item:
        print("NO CURRENT VIDEO ITEM")
        return "NO CURRENT VIDEO ITEM"

    if not media_pool_item:
        print("NO MEDIA POOL ITEM")
        return "NO MEDIA POOL ITEM"

    existing = get_existing_reviewer_notes(media_pool_item)

    if existing:
        new_value = existing + "\n" + note_text
    else:
        new_value = note_text

    ok = False

    try:
        ok = media_pool_item.SetMetadata("Reviewers Notes", new_value)
    except Exception:
        ok = False

    if not ok:
        try:
            ok = media_pool_item.SetMetadata("Reviewer Notes", new_value)
        except Exception:
            ok = False

    if ok:
        print(note_text)
        return note_text

    print("FAILED TO WRITE REVIEWERS NOTES")
    try:
        print(media_pool_item.GetMetadata())
    except Exception:
        pass
    return "WRITE FAILED"


def save_button_number(button_number):
    note = f"{get_source_tc_at_playhead()} --> {get_button_content(button_number)}"
    return append_reviewer_note(note)


def save_free_text(text_value):
    text_value = str(text_value).strip()
    if not text_value:
        print("EMPTY TEXT")
        return "EMPTY TEXT"

    note = f"{get_source_tc_at_playhead()} --> {text_value}"
    return append_reviewer_note(note)


existing = ui.FindWindow(win_id)
if existing:
    existing.Show()
    existing.Raise()
else:
    button_w = 72
    button_h = 40
    spacing = 8

    def make_button(n):
        return ui.Button({
            "ID": f"Btn{n}",
            "Text": get_button_label(n),
            "MinimumSize": [button_w, button_h],
            "MaximumSize": [button_w, button_h],
        })

    row1 = [make_button(i) for i in range(1, 4)]
    row2 = [make_button(i) for i in range(4, 7)]
    row3 = [make_button(i) for i in range(7, 10)]

    free_field_width = (button_w * 2) + spacing

    window = dispatcher.AddWindow(
        {
            "ID": win_id,
            "WindowTitle": "Reviewers Notes",
            "Geometry": [1080, 140, 260, 245],
            "WindowFlags": {
                "Window": True,
                "WindowStaysOnTopHint": True,
            },
            "Events": {
                "Close": True,
                "KeyPress": True,
            }
        },
        ui.VGroup(
            {"Spacing": 10, "Weight": 1},
            [
                ui.HGroup({"Spacing": spacing, "Weight": 0}, row1),
                ui.HGroup({"Spacing": spacing, "Weight": 0}, row2),
                ui.HGroup({"Spacing": spacing, "Weight": 0}, row3),
                ui.HGroup(
                    {"Spacing": spacing, "Weight": 0},
                    [
                        ui.LineEdit(
                            {
                                "ID": "FreeText",
                                "Text": "",
                                "PlaceholderText": "Texte libre puis Enter ou Save",
                                "MinimumSize": [free_field_width, button_h],
                                "MaximumSize": [free_field_width, button_h],
                            }
                        ),
                        ui.Button(
                            {
                                "ID": "SaveButton",
                                "Text": "Save",
                                "MinimumSize": [button_w, button_h],
                                "MaximumSize": [button_w, button_h],
                            }
                        )
                    ]
                )
            ]
        )
    )

    items = window.GetItems()

    def OnSave(ev=None):
        text_value = items["FreeText"].Text
        result = save_free_text(text_value)

        if result not in (
            "EMPTY TEXT",
            "WRITE FAILED",
            "NO PROJECT",
            "NO TIMELINE",
            "NO CURRENT VIDEO ITEM",
            "NO MEDIA POOL ITEM",
        ):
            items["FreeText"].Text = ""

    # Letter row Q,W,E,R,T,Y,U,I,O maps to buttons 1-9. Qt key codes for letters
    # equal their uppercase ASCII code: Key_Q = ord('Q') = 0x51, etc.
    SHORTCUT_LETTERS = "QWERTYUIO"
    LETTER_SHORTCUT_KEYS = {ord(letter): n for n, letter in enumerate(SHORTCUT_LETTERS, start=1)}

    # Ctrl+W (no Alt) closes the window. Distinct from Ctrl+Option+W (button 2 note)
    # since it requires Alt to be absent.
    CLOSE_SHORTCUT_KEY = ord("W")

    # Confirmed live in Resolve (see debug trace): on this setup, Qt's default macOS
    # Ctrl/Cmd swap is active, so the physical Cmd key is reported as "ControlModifier"
    # and the physical Control key as "MetaModifier". We deliberately use physical
    # Ctrl+Option (not Cmd) here to avoid colliding with macOS system shortcuts
    # (e.g. Cmd+Shift+Q / Cmd+Option+Shift+Q = Log Out).
    CTRL_MODIFIER_INT_MASK = 0x10000000  # Qt MetaModifier
    CTRL_MODIFIER_NAME_HINTS = ("meta",)

    # Option/Alt is reported as AltModifier (0x08000000).
    ALT_MODIFIER_INT_MASK = 0x08000000
    ALT_MODIFIER_NAME_HINTS = ("alt", "option", "opt")

    def has_modifier(ev, name_hints, int_mask):
        modifiers = ev.get("Modifiers", None)

        if isinstance(modifiers, dict):
            for name, pressed in modifiers.items():
                if pressed and any(hint in str(name).lower() for hint in name_hints):
                    return True
            return False

        if isinstance(modifiers, int):
            return bool(modifiers & int_mask)

        return False

    def OnWindowKeyPress(ev):
        key = ev["Key"]
        print(f"[QCHelper][debug] KeyPress ev={ev}")

        if key == 16777216:  # Escape
            dispatcher.ExitLoop()
            return

        if key == 16777220:  # Enter
            OnSave(ev)
            return

        has_ctrl = has_modifier(ev, CTRL_MODIFIER_NAME_HINTS, CTRL_MODIFIER_INT_MASK)
        has_alt = has_modifier(ev, ALT_MODIFIER_NAME_HINTS, ALT_MODIFIER_INT_MASK)
        print(f"[QCHelper][debug] key={key} ctrl={has_ctrl} alt={has_alt}")

        if key == CLOSE_SHORTCUT_KEY and has_ctrl and not has_alt:
            dispatcher.ExitLoop()
            return

        if key in LETTER_SHORTCUT_KEYS and has_ctrl and has_alt:
            save_button_number(LETTER_SHORTCUT_KEYS[key])
            return

    def OnClose(ev):
        dispatcher.ExitLoop()

    def make_handler(n):
        def handler(ev):
            save_button_number(n)
        return handler

    window.On[win_id].KeyPress = OnWindowKeyPress
    window.On[win_id].Close = OnClose
    window.On["SaveButton"].Clicked = OnSave

    for n in range(1, 10):
        window.On[f"Btn{n}"].Clicked = make_handler(n)

    window.Show()

    try:
        items["FreeText"].SetFocus()
    except Exception:
        pass

    dispatcher.RunLoop()