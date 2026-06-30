"""Popup window for customizing traffic-light colors."""

from __future__ import annotations

import logging
from typing import Callable

import objc
from AppKit import (
    NSApp,
    NSApplicationActivationPolicyAccessory,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSBezelStyleRounded,
    NSButton,
    NSColor,
    NSColorPanel,
    NSColorSpace,
    NSEvent,
    NSFont,
    NSMakeRect,
    NSModalPanelWindowLevel,
    NSScreen,
    NSTextField,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSMakePoint, NSObject

from ..models import LightState
from ..settings import get_traffic_on_colors, set_traffic_on_colors
from ..traffic_colors import STATE_LABELS, STATE_ORDER, color_pairs_from_on, default_on_colors, normalize_hex

logger = logging.getLogger(__name__)

WINDOW_W = 420
WINDOW_H = 360


class ColorGodFlippedRootView(NSView):
    def isFlipped(self) -> bool:
        return True


class _ColorSwatchView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(_ColorSwatchView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setWantsLayer_(True)
        self._hex = "#ffffff"
        return self

    def setHex_(self, hex_value: str) -> None:
        self._hex = hex_value
        rgb = normalize_hex(hex_value)
        if rgb:
            raw = rgb[1:]
            r = int(raw[0:2], 16) / 255.0
            g = int(raw[2:4], 16) / 255.0
            b = int(raw[4:6], 16) / 255.0
            self.layer().setBackgroundColor_(
                NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0).CGColor()
            )
            self.layer().setCornerRadius_(6)


class ColorGodController(NSObject):
    def initWithOnChange_(self, on_change: Callable[[], None] | None):
        self = objc.super(ColorGodController, self).init()
        if self is None:
            return None
        self._on_change = on_change
        self._window: NSWindow | None = None
        self._draft: dict[str, str] = {}
        self._swatches: dict[str, _ColorSwatchView] = {}
        self._hex_fields: dict[str, NSTextField] = {}
        self._preview_dots: dict[LightState, _ColorSwatchView] = {}
        self._active_state: str | None = None
        return self

    def show(self) -> None:
        # The app normally runs as an accessory (no Dock icon). NSColorPanel is a
        # non-modal system panel that only appears when the app is a regular,
        # active app, so switch policy while this window is open.
        NSApp().setActivationPolicy_(NSApplicationActivationPolicyRegular)
        NSApp().activateIgnoringOtherApps_(True)
        if self._window is None:
            self._build_window()
        self._load_draft()
        self._position_near_mouse()
        self._window.orderFrontRegardless()
        self._window.makeKeyAndOrderFront_(None)

    def _restore_accessory_policy(self) -> None:
        NSColorPanel.sharedColorPanel().orderOut_(None)
        NSApp().setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    def _position_near_mouse(self) -> None:
        if self._window is None:
            return
        mouse = NSEvent.mouseLocation()  # screen coords, bottom-left origin
        screen = None
        for candidate in NSScreen.screens():
            frame = candidate.frame()
            if (
                frame.origin.x <= mouse.x <= frame.origin.x + frame.size.width
                and frame.origin.y <= mouse.y <= frame.origin.y + frame.size.height
            ):
                screen = candidate
                break
        if screen is None:
            screen = NSScreen.mainScreen()
        vis = screen.visibleFrame()

        # Place the window so its top-left sits a little below-right of the cursor.
        x = mouse.x - 40
        y = mouse.y - WINDOW_H + 20
        x = max(vis.origin.x, min(x, vis.origin.x + vis.size.width - WINDOW_W))
        y = max(vis.origin.y, min(y, vis.origin.y + vis.size.height - WINDOW_H))
        self._window.setFrameOrigin_(NSMakePoint(x, y))

    def _load_draft(self) -> None:
        self._draft = get_traffic_on_colors()
        self._refresh_ui_from_draft()

    def _refresh_ui_from_draft(self) -> None:
        for state in STATE_ORDER:
            key = state.value
            hex_value = self._draft[key]
            swatch = self._swatches.get(key)
            if swatch:
                swatch.setHex_(hex_value)
            field = self._hex_fields.get(key)
            if field:
                field.setStringValue_(hex_value)
        self._refresh_preview()

    def _build_window(self) -> None:
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, WINDOW_W, WINDOW_H),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_("颜色の神")
        window.setLevel_(NSModalPanelWindowLevel)
        window.setReleasedWhenClosed_(False)
        window.setDelegate_(self)

        root = ColorGodFlippedRootView.alloc().initWithFrame_(NSMakeRect(0, 0, WINDOW_W, WINDOW_H))
        y = 16

        hint = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, WINDOW_W - 40, 36))
        hint.setBezeled_(False)
        hint.setDrawsBackground_(False)
        hint.setEditable_(False)
        hint.setSelectable_(False)
        hint.setStringValue_("为交通灯模式的三种状态选择颜色（默认红 / 黄 / 绿）")
        hint.setFont_(NSFont.systemFontOfSize_(12))
        hint.setTextColor_(NSColor.secondaryLabelColor())
        root.addSubview_(hint)
        y += 44

        for state in STATE_ORDER:
            key = state.value
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, 150, 22))
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            label.setStringValue_(STATE_LABELS[state])
            label.setFont_(NSFont.systemFontOfSize_(13))
            root.addSubview_(label)

            swatch = _ColorSwatchView.alloc().initWithFrame_(NSMakeRect(180, y - 2, 36, 24))
            root.addSubview_(swatch)
            self._swatches[key] = swatch

            pick_btn = NSButton.alloc().initWithFrame_(NSMakeRect(224, y - 2, 64, 24))
            pick_btn.setBezelStyle_(NSBezelStyleRounded)
            pick_btn.setTitle_("选择…")
            pick_btn.setTag_(STATE_ORDER.index(state))
            pick_btn.setTarget_(self)
            pick_btn.setAction_("pickColor:")
            root.addSubview_(pick_btn)

            hex_field = NSTextField.alloc().initWithFrame_(NSMakeRect(296, y - 2, 96, 24))
            hex_field.setTag_(STATE_ORDER.index(state))
            hex_field.setTarget_(self)
            hex_field.setAction_("hexEdited:")
            root.addSubview_(hex_field)
            self._hex_fields[key] = hex_field
            y += 36

        preview_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, 120, 20))
        preview_label.setBezeled_(False)
        preview_label.setDrawsBackground_(False)
        preview_label.setEditable_(False)
        preview_label.setSelectable_(False)
        preview_label.setStringValue_("预览")
        preview_label.setFont_(NSFont.boldSystemFontOfSize_(12))
        root.addSubview_(preview_label)
        y += 28

        preview_x = 20
        for state in STATE_ORDER:
            dot = _ColorSwatchView.alloc().initWithFrame_(NSMakeRect(preview_x, y, 28, 28))
            dot.layer().setCornerRadius_(14)
            root.addSubview_(dot)
            self._preview_dots[state] = dot
            preview_x += 40

        y += 52
        reset_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 100, 28))
        reset_btn.setBezelStyle_(NSBezelStyleRounded)
        reset_btn.setTitle_("恢复默认")
        reset_btn.setTarget_(self)
        reset_btn.setAction_("resetDefaults:")
        root.addSubview_(reset_btn)

        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(WINDOW_W - 120, y, 100, 28))
        save_btn.setBezelStyle_(NSBezelStyleRounded)
        save_btn.setTitle_("保存")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        root.addSubview_(save_btn)

        window.setContentView_(root)
        self._window = window

    def _refresh_preview(self) -> None:
        pairs = color_pairs_from_on(self._draft)
        for state, dot in self._preview_dots.items():
            on_hex, _off_hex = pairs[state]
            dot.setHex_(on_hex)

    def _set_draft_color(self, state_key: str, hex_value: str) -> None:
        normalized = normalize_hex(hex_value)
        if not normalized:
            return
        self._draft[state_key] = normalized
        swatch = self._swatches.get(state_key)
        if swatch:
            swatch.setHex_(normalized)
        field = self._hex_fields.get(state_key)
        if field:
            field.setStringValue_(normalized)
        self._refresh_preview()

    def pickColor_(self, sender) -> None:
        logger.info("pickColor invoked, tag=%s", sender.tag())
        idx = sender.tag()
        if idx < 0 or idx >= len(STATE_ORDER):
            return
        state = STATE_ORDER[idx]
        key = state.value
        self._active_state = key

        try:
            NSApp().setActivationPolicy_(NSApplicationActivationPolicyRegular)
            NSApp().activateIgnoringOtherApps_(True)

            panel = NSColorPanel.sharedColorPanel()
            panel.setShowsAlpha_(False)
            hex_value = self._draft.get(key, "#ffffff")
            raw = normalize_hex(hex_value)
            if raw:
                rgb = raw[1:]
                color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    int(rgb[0:2], 16) / 255.0,
                    int(rgb[2:4], 16) / 255.0,
                    int(rgb[4:6], 16) / 255.0,
                    1.0,
                )
                panel.setColor_(color)
            # Wire the live-update callback only after the initial color is set,
            # so setColor_ above doesn't trigger a redundant (early) callback.
            panel.setTarget_(self)
            panel.setAction_("colorPanelChanged:")
            # The settings window sits at NSModalPanelWindowLevel; raise the color
            # picker above it, otherwise it opens hidden behind.
            panel.setLevel_(NSModalPanelWindowLevel + 2)
            panel.setFloatingPanel_(True)
            self._center_panel_near_window(panel)
            panel.orderFrontRegardless()
            panel.makeKeyAndOrderFront_(None)
            logger.info(
                "Color panel shown: visible=%s frame=%s",
                panel.isVisible(),
                tuple(panel.frame()),
            )
        except Exception:
            logger.exception("Failed to show color panel")

    def _center_panel_near_window(self, panel) -> None:
        if self._window is None:
            return
        wf = self._window.frame()
        pf = panel.frame()
        x = wf.origin.x + (wf.size.width - pf.size.width) / 2
        y = wf.origin.y - pf.size.height - 10
        screen = self._window.screen() or NSScreen.mainScreen()
        vis = screen.visibleFrame()
        x = max(vis.origin.x, min(x, vis.origin.x + vis.size.width - pf.size.width))
        y = max(vis.origin.y, min(y, vis.origin.y + vis.size.height - pf.size.height))
        panel.setFrameOrigin_(NSMakePoint(x, y))

    def colorPanelChanged_(self, sender) -> None:
        if not self._active_state:
            return
        color = NSColorPanel.sharedColorPanel().color()
        rgb = color.colorUsingColorSpace_(NSColorSpace.sRGBColorSpace())
        if rgb is None:
            rgb = color.colorUsingColorSpace_(NSColorSpace.genericRGBColorSpace())
        if rgb is None:
            return
        r = int(round(rgb.redComponent() * 255))
        g = int(round(rgb.greenComponent() * 255))
        b = int(round(rgb.blueComponent() * 255))
        hex_value = f"#{r:02x}{g:02x}{b:02x}"
        self._set_draft_color(self._active_state, hex_value)

    def hexEdited_(self, sender) -> None:
        idx = sender.tag()
        if idx < 0 or idx >= len(STATE_ORDER):
            return
        key = STATE_ORDER[idx].value
        self._set_draft_color(key, sender.stringValue())

    def resetDefaults_(self, sender) -> None:
        self._draft = default_on_colors()
        self._refresh_ui_from_draft()

    def save_(self, sender) -> None:
        set_traffic_on_colors(self._draft)
        if self._on_change:
            self._on_change()
        if self._window:
            self._window.orderOut_(None)
        self._restore_accessory_policy()
        logger.info("Traffic colors saved: %s", self._draft)

    def windowWillClose_(self, notification) -> None:
        self._restore_accessory_policy()


_manager: ColorGodController | None = None


def show_color_god(on_change: Callable[[], None] | None = None) -> None:
    global _manager
    if _manager is None:
        _manager = ColorGodController.alloc().initWithOnChange_(on_change)
    elif on_change:
        _manager._on_change = on_change
    _manager.show()
