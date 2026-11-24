#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import math
import os
import sys
import tempfile
import warnings
from pathlib import Path
from stat import S_ISREG

from PIL import Image, ImageEnhance, ImageOps
from PyQt5 import QtCore as C, QtGui as G, QtWidgets as W

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tif', '.tiff', '.ico'}
IMAGE_FORMATS = ('JPEG', 'PNG', 'WEBP', 'BMP', 'GIF', 'TIFF', 'ICO')
MAX_PIXELS = 32_000_000
NEUTRAL = (0, 0, 0)
ICON = 'jatayu-gallery'
VERSION = '0.3.4'

GUIDE_TOPICS = (
    ('Getting started', '''
        <ol>
          <li>Click <b>Open</b> in the top bar, or drag a photo from Dolphin onto Gallery.</li>
          <li>In the Open Image window, find the folder containing your photo, select the file, and click <b>Open</b>.</li>
          <li>Click another thumbnail below the photo, or use the left and right arrows in the footer to browse.</li>
        </ol>
        <p>Gallery browses supported images in the same folder. A counter of <b>2 of 7</b> means you are viewing the second file in a list of seven. Use <b>Thumbnails</b> to show or hide the strip.</p>
    '''),
    ('Zoom and Full Screen', '''
        <ol>
          <li>Move the pointer over the photo and scroll up to zoom in or down to zoom out.</li>
          <li>Once zoomed in, hold the left mouse button and drag to see a different part of the photo.</li>
          <li>Click <b>Fit to Window</b> to show the whole photo again.</li>
        </ol>
        <p>Click <b>Full Screen</b> or press <b>F11</b> to hide the editing panel, toolbar, and thumbnails. Move the mouse to reveal viewing controls. Press <b>Esc</b> or click <b>Exit Full Screen</b> to return.</p>
    '''),
    ('Play a slideshow', '''
        <ol>
          <li>Open a photo from a folder with at least two supported images.</li>
          <li>Click <b>Slideshow</b> to start from the current photo. Gallery advances every five seconds by default.</li>
          <li>Click the small menu beside <b>Slideshow</b> to change <b>Time per image</b> or turn on <b>Loop slideshow</b>.</li>
          <li>Click <b>Pause</b> or press <b>Space</b> to stop on the current photo. Press <b>Space</b> again to resume.</li>
        </ol>
        <p>On the last image, go back to an earlier photo or enable looping. Starting playback with unsaved edits opens a prompt. Choose <b>Save</b> to export a copy, <b>Discard</b> to drop pending edits, or <b>Cancel</b> to keep editing.</p>
    '''),
    ('Crop, rotate and flip', '''
        <h2>Keep only part of a photo</h2>
        <ol>
          <li>Click <b>Edit</b>, then <b>Crop</b>.</li>
          <li>Drag from one corner of the area you want to keep to the opposite corner.</li>
          <li>Check the outlined selection and click <b>Apply Crop</b>. If you cut too much, click <b>Undo</b>.</li>
        </ol>
        <h2>Fix the orientation</h2>
        <p>In <b>Edit → Rotate</b>, choose <b>Rotate Left</b> or <b>Rotate Right</b> to turn the photo by 90 degrees. Choose <b>Flip Horizontally</b> for a mirror image or <b>Flip Vertically</b> to flip it top to bottom.</p>
    '''),
    ('Adjust and resize', '''
        <h2>Adjust light and color</h2>
        <ol>
          <li>Click <b>Edit → Adjust</b>. Move <b>Exposure</b> right to brighten or left to darken.</li>
          <li>Increase <b>Contrast</b> to make light and dark areas more distinct. Move <b>Warmth</b> right for warmer tones or left for cooler tones.</li>
          <li>Click <b>Show Original</b> to compare your changes, or <b>Reset Adjustments</b> to return the sliders to zero. Turn off <b>Show Original</b> before cropping.</li>
        </ol>
        <h2>Change the pixel dimensions</h2>
        <p>Click <b>Edit → Resize</b>. Leave <b>Keep aspect ratio</b> checked and enter a width such as <b>1200 px</b>. Gallery calculates the height to preserve the photo’s shape. Click <b>Apply Resize</b>.</p>
        <p><b>Undo</b> steps back through edits on the current image. <b>Redo</b> reapplies an edit you just undid.</p>
    '''),
    ('Save your work', '''
        <ol>
          <li>Click <b>Save a Copy</b> when you are happy with the result.</li>
          <li>Choose a folder and a new filename, for example <b>holiday-edited.png</b>.</li>
          <li>Choose PNG, JPEG, or WebP, then click <b>Save</b>. Your original stays in its folder.</li>
        </ol>
        <p>Use PNG or WebP if you need to keep transparent areas. JPEG fills those areas with white. If a file already has the chosen name, use a new name such as <b>holiday-edited-2.png</b>.</p>
        <p>An asterisk (<b>*</b>) beside the filename means the current edits have yet to be exported. Gallery gives you a chance to save when you leave that image or close the app.</p>
    '''),
    ('Keyboard shortcuts', '''
        <table cellspacing="7">
          <tr><th align="left">Shortcut</th><th align="left">Action</th></tr>
          <tr><td>Ctrl+O</td><td>Open an image</td></tr>
          <tr><td>Left / Right</td><td>Previous or next image</td></tr>
          <tr><td>0</td><td>Fit the image to the window</td></tr>
          <tr><td>F11 / Esc</td><td>Toggle Full Screen / exit Full Screen</td></tr>
          <tr><td>Space</td><td>Play or pause the slideshow</td></tr>
          <tr><td>Ctrl+Z / Ctrl+Shift+Z</td><td>Undo / redo</td></tr>
          <tr><td>Ctrl+Shift+S</td><td>Save a Copy</td></tr>
          <tr><td>F1</td><td>Open this guide</td></tr>
        </table>
    '''),
    ('Troubleshooting', '''
        <h2>Edit or Save a Copy is unavailable</h2>
        <p>Open an image first. If you are in Full Screen, press <b>Esc</b> to restore the editing toolbar.</p>
        <h2>The slideshow will not start</h2>
        <p>Open a photo from a folder with at least two supported images. If the counter shows the final image, go back or turn on <b>Loop slideshow</b>.</p>
        <h2>A photo will not open</h2>
        <p>Gallery supports common JPEG, PNG, WebP, BMP, GIF, TIFF, and ICO files up to 32 megapixels. An incomplete download may fail to open. Animated and multipage images show the first frame or page.</p>
        <h2>The preview looks different from my edit</h2>
        <p>Turn off <b>Show Original</b> in the editing panel to return to the edited preview. If the image is enlarged, click <b>Fit to Window</b> to see the entire photo.</p>
    '''),
)


STYLE = """
QMainWindow, QWidget#tools { background: #102d20; color: #edf7f1; }
QLabel, QCheckBox { color: #edf7f1; }
QWidget#header, QWidget#footer { background: #102f21; }
QWidget#header { border-bottom: 1px solid #567568; }
QWidget#footer { border-top: 1px solid #567568; }
QWidget#tools { border-left: 1px solid #567568; }
QLabel#brand, QLabel#heading { font-size: 23px; font-weight: 700; }
QPushButton, QToolButton { color: #effbf5; background: #16382a; border: 1px solid #587869;
    border-radius: 6px; padding: 8px 12px; font-size: 14px; }
QPushButton:hover, QToolButton:hover { background: #23513c; }
QPushButton:checked, QToolButton:checked { background: #90f9c6; color: #09251a;
    border-color: #90f9c6; font-weight: 600; }
QPushButton:disabled { color: #9ab1a6; background: #142d22; }
QPushButton:focus, QToolButton:focus { border: 2px solid #a2ffd3; }
QScrollArea, QWidget#film, QWidget#canvas { background: #181b1a; border: 0; }
QScrollArea#filmstrip { border-top: 1px solid #567568; }
QFrame[frameShape="4"] { color: #587869; }
QSlider::groove:horizontal { height: 5px; background: #587869; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #90f9c6; border-radius: 2px; }
QSlider::handle:horizontal { background: #b8ffe1; width: 16px; margin: -6px 0; border-radius: 8px; }
QSpinBox { color: #effbf5; background: #16382a; border: 1px solid #587869; padding: 5px; }
"""


def load_image(path, thumbnail=False):
    # Check the opened handle so a path replacement cannot bypass the check.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream, warnings.catch_warnings():
        if not S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Choose a regular image file.')
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(stream, formats=IMAGE_FORMATS) as source:
            if source.width * source.height > MAX_PIXELS:
                raise ValueError('This image exceeds the 32 megapixel limit.')
            if thumbnail:
                source.draft('RGB', (192, 128))
                source.thumbnail((160, 160), Image.Resampling.BILINEAR)
            icc = source.info.get('icc_profile')
            result = ImageOps.exif_transpose(source).convert('RGBA')
            result.info.clear()
            if isinstance(icc, bytes) and icc:
                result.info['icc_profile'] = icc
            return result


def adjust(image, values):
    if values == NEUTRAL:
        return image
    exposure, contrast, warmth = values
    rgb = image.convert('RGB')
    if exposure:
        rgb = ImageEnhance.Brightness(rgb).enhance(2 ** (exposure / 100))
    if contrast:
        rgb = ImageEnhance.Contrast(rgb).enhance(2 ** (contrast / 100))
    if warmth:
        red, green, blue = rgb.split()
        offset = round(warmth * .45)
        rgb = Image.merge('RGB', (red.point([max(0, min(255, i + offset)) for i in range(256)]),
                                  green, blue.point([max(0, min(255, i - offset)) for i in range(256)])))
    rgb.putalpha(image.getchannel('A'))
    return rgb


def save_new(image, destination, icc=None):
    formats = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}
    kind = formats.get(destination.suffix.lower())
    if not kind:
        raise ValueError('Choose a filename ending in .png, .jpg or .webp.')
    params = {'icc_profile': icc} if icc else {}
    if kind == 'JPEG':
        flattened = Image.new('RGB', image.size, 'white')
        flattened.paste(image, mask=image.getchannel('A'))
        image = flattened
        params.update(quality=94)
    if kind == 'WEBP':
        params.update(lossless=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.jatayu-') as workspace:
        pending = Path(workspace) / 'export'
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            image.save(stream, format=kind, **params)
        os.link(pending, destination)


def pixmap(image):
    # Pillow may select a different Qt binding when several are installed.
    data = image.convert('RGBA').tobytes()
    return G.QPixmap.fromImage(G.QImage(data, image.width, image.height,
                                       image.width * 4, G.QImage.Format_RGBA8888).copy())


class Canvas(W.QWidget):
    pointer_moved = C.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName('canvas')
        self.setMinimumSize(120, 100)
        self.image = G.QPixmap()
        self.original = G.QPixmap()
        self.rect_image = C.QRect()
        self.scale = None
        self.offset = C.QPoint()
        self.crop_mode = False
        self.compare = False
        self.same_dimensions = True
        self.selection = C.QRect()
        self.anchor = None
        self.setMouseTracking(True)

    def fit(self):
        self.scale = None
        self.offset = C.QPoint()
        self.selection = C.QRect()
        self.update()

    def paintEvent(self, event):
        painter = G.QPainter(self)
        painter.fillRect(self.rect(), G.QColor('#181b1a'))
        if self.image.isNull():
            painter.setPen(G.QColor('#e0eee6'))
            font = painter.font()
            font.setPointSize(17)
            painter.setFont(font)
            painter.drawText(self.rect(), C.Qt.AlignCenter, 'Open an image or drop it here')
            return
        available = self.size() - C.QSize(44, 40)
        scale = self.scale or min(available.width() / self.image.width(),
                                  available.height() / self.image.height())
        size = C.QSize(max(1, round(self.image.width() * scale)),
                       max(1, round(self.image.height() * scale)))
        target = C.QRect(C.QPoint(), size)
        target.moveCenter(self.rect().center() + self.offset)
        self.rect_image = target
        painter.setRenderHint(G.QPainter.SmoothPixmapTransform)
        painter.fillRect(target, G.QColor('#303533'))
        painter.drawPixmap(target, self.image)
        painter.setPen(G.QColor('#b6c5bd'))
        painter.drawRect(target.adjusted(-1, -1, 0, 0))
        if self.compare:
            if self.same_dimensions:
                left = C.QRect(target.left(), target.top(), target.width() // 2, target.height())
                painter.save()
                painter.setClipRect(left)
                painter.drawPixmap(target, self.original)
                painter.restore()
                painter.drawLine(left.topRight(), left.bottomRight())
            else:
                size = self.original.size().scaled(available, C.Qt.KeepAspectRatio)
                before = C.QRect(C.QPoint(), size)
                before.moveCenter(self.rect().center())
                painter.fillRect(self.rect(), G.QColor('#181b1a'))
                painter.drawPixmap(before, self.original)
            badge = C.QRect(12, 12, 85, 28)
            painter.fillRect(badge, G.QColor('#102f21'))
            painter.setPen(G.QColor('#edf7f1'))
            painter.drawText(badge, C.Qt.AlignCenter, 'Original')
        if self.crop_mode and not self.selection.isNull():
            painter.fillRect(self.selection, G.QColor(145, 249, 198, 45))
            painter.setPen(G.QPen(G.QColor('#90f9c6'), 2, C.Qt.DashLine))
            painter.drawRect(self.selection)

    def wheelEvent(self, event):
        if self.image.isNull() or self.crop_mode or self.compare:
            return
        current = self.rect_image.width() / self.image.width()
        self.scale = min(8, max(.001, current * 1.18 ** (event.angleDelta().y() / 120)))
        self.update()

    def mousePressEvent(self, event):
        if event.button() != C.Qt.LeftButton or self.image.isNull() or self.compare:
            return
        if self.crop_mode:
            if self.rect_image.contains(event.pos()):
                self.anchor = event.pos()
                self.selection = C.QRect(self.anchor, self.anchor)
                self.update()
        else:
            self.anchor = event.pos() - self.offset

    def mouseMoveEvent(self, event):
        self.pointer_moved.emit()
        if self.anchor is None:
            return
        if self.crop_mode:
            self.selection = C.QRect(self.anchor, event.pos()).normalized().intersected(self.rect_image)
        elif self.scale is not None:
            self.offset = event.pos() - self.anchor
        self.update()

    def mouseReleaseEvent(self, event):
        self.anchor = None

    def resizeEvent(self, event):
        self.selection = C.QRect()


class Gallery(W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Jatayu Gallery')
        self.resize(1220, 760)
        self.setMinimumSize(720, 480)
        self.setAcceptDrops(True)
        self.files = []
        self.index = -1
        self.original = None
        self.history = []
        self.position = 0
        self.saved = None
        self.preview_timer = C.QTimer(self, interval=65, singleShot=True)
        self.preview_timer.timeout.connect(self.preview_adjustment)
        self.thumbnail_timer = C.QTimer(self, interval=1)
        self.thumbnail_timer.timeout.connect(self.load_thumbnail)
        self.thumb_buttons = {}
        self.thumb_pending = iter(())
        self.presentation = False
        self.windowed_state = self.windowState()
        self.slideshow_timer = C.QTimer(self, interval=5000, singleShot=True)
        self.slideshow_timer.timeout.connect(self.advance_slideshow)
        self.controls_timer = C.QTimer(self, interval=2500, singleShot=True)
        self.controls_timer.timeout.connect(self.hide_controls)
        self.shortcut_actions = []
        self.build_ui()
        self.refresh()

    @staticmethod
    def button(label, method, checkable=False):
        button = W.QPushButton(label)
        button.setCheckable(checkable)
        if method:
            button.clicked.connect(method)
        return button

    @staticmethod
    def divider(layout):
        line = W.QFrame()
        line.setFrameShape(W.QFrame.HLine)
        layout.addWidget(line)

    def shortcut(self, keys, action):
        shortcut = W.QShortcut(G.QKeySequence(keys), self)
        shortcut.activated.connect(action)
        self.shortcut_actions.append(shortcut)

    def build_ui(self):
        root = W.QWidget()
        self.setCentralWidget(root)
        layout = W.QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = W.QWidget(objectName='header')
        top = W.QHBoxLayout(header)
        top.setContentsMargins(15, 8, 15, 8)
        mark = W.QLabel()
        mark.setPixmap(self.windowIcon().pixmap(30, 30))
        top.addWidget(mark)
        top.addWidget(W.QLabel('Jatayu Gallery', objectName='brand'))
        top.addSpacing(12)
        self.view_button = self.button('View', lambda: self.set_edit(False), True)
        self.edit_button = self.button('Edit', lambda: self.set_edit(True), True)
        top.addWidget(self.view_button)
        top.addWidget(self.edit_button)
        top.addSpacing(8)
        top.addWidget(self.button('Open', self.choose))
        self.save_button = self.button('Save a Copy', self.save)
        top.addWidget(self.save_button)
        top.addStretch()
        help_button = self.button('Help', None)
        help_menu = W.QMenu(help_button)
        for label, action in (
            ('Help', self.show_help),
            ('About Jatayu Gallery', self.show_about),
            ('License', self.show_license),
            ('Credits', self.show_credits),
        ):
            help_menu.addAction(label, action)
        help_button.setMenu(help_menu)
        top.addWidget(help_button)
        layout.addWidget(header)
        self.header = header

        body = W.QHBoxLayout()
        body.setSpacing(0)
        layout.addLayout(body, 1)
        left = W.QVBoxLayout()
        left.setSpacing(0)
        body.addLayout(left, 1)
        self.canvas = Canvas()
        self.canvas.pointer_moved.connect(self.reveal_controls)
        left.addWidget(self.canvas, 1)
        self.film = W.QScrollArea(objectName='filmstrip')
        self.film.setFixedHeight(103)
        self.film.setWidgetResizable(True)
        self.film.setVerticalScrollBarPolicy(C.Qt.ScrollBarAlwaysOff)
        left.addWidget(self.film)

        self.tools = W.QWidget(objectName='tools')
        self.tools.setFixedWidth(324)
        tools = W.QVBoxLayout(self.tools)
        tools.setContentsMargins(14, 17, 14, 14)
        tools.setSpacing(14)
        title = W.QHBoxLayout()
        title.addWidget(W.QLabel('Editing Tools', objectName='heading'))
        title.addStretch()
        title.addWidget(self.button('Hide Tools', lambda: self.set_edit(False)))
        tools.addLayout(title)
        self.tabs = W.QButtonGroup(self)
        tab_row = W.QHBoxLayout()
        tab_row.setSpacing(3)
        for i, name in enumerate(('Crop', 'Rotate', 'Adjust', 'Resize')):
            button = self.button(name, None, True)
            self.tabs.addButton(button, i)
            tab_row.addWidget(button)
        self.tabs.button(2).setChecked(True)
        self.tabs.idClicked.connect(self.change_tool)
        tools.addLayout(tab_row)
        self.divider(tools)
        self.pages = W.QStackedWidget()
        tools.addWidget(self.pages)

        crop = W.QWidget()
        crop_layout = W.QVBoxLayout(crop)
        instruction = W.QLabel('Drag across the photo to select the area to keep.')
        instruction.setWordWrap(True)
        crop_layout.addWidget(instruction)
        crop_layout.addWidget(self.button('Apply Crop', self.crop))
        crop_layout.addStretch()
        self.pages.addWidget(crop)

        rotate = W.QWidget()
        rotate_layout = W.QVBoxLayout(rotate)
        for label, method in (('Rotate Left', Image.Transpose.ROTATE_90),
                              ('Rotate Right', Image.Transpose.ROTATE_270),
                              ('Flip Horizontally', Image.Transpose.FLIP_LEFT_RIGHT),
                              ('Flip Vertically', Image.Transpose.FLIP_TOP_BOTTOM)):
            rotate_layout.addWidget(self.button(label, lambda _, op=method: self.transform(op)))
        self.pages.addWidget(rotate)

        sliders = W.QWidget()
        slider_layout = W.QVBoxLayout(sliders)
        self.sliders = []
        self.values = []
        for name in ('Exposure', 'Contrast', 'Warmth'):
            slider = W.QSlider(C.Qt.Horizontal)
            slider.setAccessibleName(name)
            slider.setRange(-100, 100)
            value = W.QLabel('0.00')
            value.setMinimumWidth(41)
            slider.valueChanged.connect(self.queue_adjustment)
            slider.sliderReleased.connect(self.commit_adjustment)
            self.sliders.append(slider)
            self.values.append(value)
            slider_layout.addWidget(W.QLabel(name))
            row = W.QHBoxLayout()
            row.addWidget(slider, 1)
            row.addWidget(value)
            slider_layout.addLayout(row)
        slider_layout.addWidget(self.button('Reset Adjustments', self.reset_adjustment))
        self.pages.addWidget(sliders)

        resize = W.QWidget()
        resize_layout = W.QFormLayout(resize)
        self.width_input, self.height_input = W.QSpinBox(), W.QSpinBox()
        for control in (self.width_input, self.height_input):
            control.setRange(1, MAX_PIXELS)
            control.setSuffix(' px')
        resize_layout.addRow('Width', self.width_input)
        resize_layout.addRow('Height', self.height_input)
        self.lock_ratio = W.QCheckBox('Keep aspect ratio')
        self.lock_ratio.setChecked(True)
        resize_layout.addRow(self.lock_ratio)
        self.width_input.valueChanged.connect(lambda value: self.link_dimension(value, True))
        self.height_input.valueChanged.connect(lambda value: self.link_dimension(value, False))
        resize_layout.addRow(self.button('Apply Resize', self.resize_image))
        self.pages.addWidget(resize)
        self.pages.setCurrentIndex(2)
        self.divider(tools)
        history = W.QHBoxLayout()
        self.undo_button = self.button('↶  Undo', self.undo)
        self.redo_button = self.button('↷  Redo', self.redo)
        history.addWidget(self.undo_button)
        history.addWidget(self.redo_button)
        tools.addLayout(history)
        self.divider(tools)
        compare = W.QHBoxLayout()
        compare.addWidget(W.QLabel('Compare Lens'))
        compare.addStretch()
        self.compare_button = self.button('Show Original', self.set_compare, True)
        compare.addWidget(self.compare_button)
        tools.addLayout(compare)
        tools.addStretch()
        tools_scroll = W.QScrollArea()
        tools_scroll.setWidget(self.tools)
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setFixedWidth(324)
        tools_scroll.setHorizontalScrollBarPolicy(C.Qt.ScrollBarAlwaysOff)
        self.tools.setFixedWidth(320)
        body.addWidget(tools_scroll)
        self.tools_scroll = tools_scroll

        footer = W.QWidget(objectName='footer')
        self.footer = footer
        bottom = W.QHBoxLayout(footer)
        bottom.setContentsMargins(15, 8, 15, 8)
        self.filename = W.QLabel()
        self.filename.setTextFormat(C.Qt.PlainText)
        self.filename.setSizePolicy(W.QSizePolicy.Ignored, W.QSizePolicy.Preferred)
        self.previous = self.button('‹', lambda: self.navigate(-1, from_button=True))
        self.following = self.button('›', lambda: self.navigate(1, from_button=True))
        self.previous.setAccessibleName('Previous image')
        self.following.setAccessibleName('Next image')
        self.counter = W.QLabel()
        self.thumbs = self.button('Thumbnails', self.toggle_thumbs, True)
        bottom.addWidget(self.filename, 1)
        bottom.addWidget(self.previous)
        bottom.addWidget(self.counter)
        bottom.addWidget(self.following)
        bottom.addStretch(1)
        bottom.addWidget(self.button('Fit to Window', self.canvas.fit))
        self.fullscreen_button = self.button('Full Screen', self.fullscreen)
        self.fullscreen_button.setToolTip('Full Screen (F11)')
        bottom.addWidget(self.fullscreen_button)
        self.play_button = self.button('▶ Slideshow', self.toggle_slideshow)
        self.play_button.setToolTip('Play or pause slideshow (Space)')
        bottom.addWidget(self.play_button)
        options = W.QToolButton()
        options.setArrowType(C.Qt.DownArrow)
        options.setAccessibleName('Slideshow settings')
        options.setToolTip('Slideshow settings')
        self.slideshow_menu = W.QMenu(options)
        speed_menu = self.slideshow_menu.addMenu('Time per image')
        speeds = W.QActionGroup(speed_menu)
        for seconds in (2, 3, 5, 10, 15):
            action = speed_menu.addAction(f'{seconds} seconds')
            action.setCheckable(True)
            action.setChecked(seconds == 5)
            speeds.addAction(action)
            action.triggered.connect(lambda _, s=seconds: self.set_slideshow_speed(s))
        self.loop_action = self.slideshow_menu.addAction('Loop slideshow')
        self.loop_action.setCheckable(True)
        options.clicked.connect(lambda: self.slideshow_menu.popup(
            options.mapToGlobal(C.QPoint(0, -self.slideshow_menu.sizeHint().height()))))
        bottom.addWidget(options)
        bottom.addWidget(self.thumbs)
        layout.addWidget(footer)
        self.thumbs.setChecked(True)
        self.film.hide()
        self.set_edit(False)
        for key, callback in [('Ctrl+O', self.choose), ('Ctrl+Shift+S', self.save),
                              ('Ctrl+Z', self.undo), ('Ctrl+Shift+Z', self.redo),
                              ('Left', lambda: self.navigate(-1)), ('Right', lambda: self.navigate(1)),
                              ('0', self.canvas.fit), ('F11', self.fullscreen),
                              ('Esc', self.exit_fullscreen), ('F1', self.show_help),
                              ('Space', self.slideshow_shortcut)]:
            self.shortcut(key, callback)

    def set_edit(self, active):
        if active:
            self.stop_slideshow()
        self.commit_adjustment()
        self.tools_scroll.setVisible(active and not self.presentation)
        self.edit_button.setChecked(active)
        self.view_button.setChecked(not active)
        if not active:
            self.compare_button.setChecked(False)
            self.canvas.compare = False
        self.change_tool(self.tabs.checkedId())

    def change_tool(self, index):
        self.commit_adjustment()
        self.pages.setCurrentIndex(index)
        self.canvas.crop_mode = index == 0 and self.edit_button.isChecked()
        self.canvas.selection = C.QRect()
        self.canvas.update()
        self.sync_dimensions()

    def set_compare(self, checked):
        self.canvas.compare = checked and self.original is not None
        self.canvas.selection = C.QRect()
        self.canvas.update()

    def fullscreen(self):
        if self.presentation:
            self.exit_fullscreen()
            return
        if self.original is None:
            return
        self.commit_adjustment()
        self.presentation = True
        self.windowed_state = self.windowState()
        self.header.hide()
        self.tools_scroll.hide()
        self.film.hide()
        self.footer.hide()
        self.canvas.crop_mode = False
        self.canvas.compare = False
        self.canvas.fit()
        self.fullscreen_button.setText('Exit Full Screen')
        self.fullscreen_button.setToolTip('Exit Full Screen (Esc)')
        self.thumbs.hide()
        self.showFullScreen()

    def exit_fullscreen(self):
        if not self.presentation:
            return
        self.presentation = False
        self.controls_timer.stop()
        self.setWindowState(self.windowed_state)
        self.header.show()
        self.footer.show()
        self.thumbs.show()
        self.tools_scroll.setVisible(self.edit_button.isChecked())
        self.toggle_thumbs(self.thumbs.isChecked())
        self.canvas.compare = self.compare_button.isChecked()
        self.change_tool(self.tabs.checkedId())
        self.fullscreen_button.setText('Full Screen')
        self.fullscreen_button.setToolTip('Full Screen (F11)')
        self.canvas.fit()

    def reveal_controls(self):
        if self.presentation:
            self.footer.show()
            self.controls_timer.start()

    def hide_controls(self):
        if self.footer.underMouse() or W.QApplication.activePopupWidget():
            self.controls_timer.start()
        else:
            self.footer.hide()

    def toggle_thumbs(self, checked):
        self.film.setVisible(checked and bool(self.files) and not self.presentation)
        if self.film.isVisible():
            self.update_thumbnail_selection()

    def slideshow_shortcut(self):
        if not isinstance(self.focusWidget(), (W.QSlider, W.QSpinBox, W.QLineEdit)):
            self.toggle_slideshow()

    def toggle_slideshow(self):
        if self.slideshow_timer.isActive():
            self.stop_slideshow()
            return
        if len(self.files) < 2:
            return
        if self.index + 1 == len(self.files) and not self.loop_action.isChecked():
            W.QMessageBox.information(self, 'Slideshow',
                                      'You are on the last image. Go back or enable Loop slideshow.')
            return
        if not self.confirm_leave():
            return
        if self.history[self.position] is not self.saved:
            self.history = [self.saved]
            self.position = 0
            self.canvas.fit()
            self.refresh()
        self.set_edit(False)
        self.slideshow_timer.start()
        self.play_button.setText('Ⅱ Pause')

    def stop_slideshow(self):
        self.slideshow_timer.stop()
        self.play_button.setText('▶ Slideshow')

    def set_slideshow_speed(self, seconds):
        self.slideshow_timer.setInterval(seconds * 1000)

    def advance_slideshow(self):
        next_index = self.index + 1
        if next_index >= len(self.files):
            if not self.loop_action.isChecked():
                self.stop_slideshow()
                return
            next_index = 0
        self.open_path(self.files[next_index], self.files)
        if self.index == next_index:
            self.slideshow_timer.start()
            self.play_button.setText('Ⅱ Pause')

    def show_help(self):
        self.stop_slideshow()
        dialog = W.QDialog(self)
        dialog.setWindowTitle('Jatayu Gallery User Guide')
        dialog.setSizeGripEnabled(True)
        dialog.resize(830, 570)
        layout = W.QVBoxLayout(dialog)
        splitter = W.QSplitter(C.Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        topics = W.QListWidget()
        topics.setAccessibleName('Guide topics')
        topics.setMinimumWidth(195)
        topics.setStyleSheet('QListWidget::item { padding: 7px 9px; }')
        topic_font = topics.font()
        topic_font.setPointSizeF(max(11.0, topic_font.pointSizeF()))
        topics.setFont(topic_font)
        content = W.QTextBrowser()
        content.setAccessibleName('Topic instructions')
        content.document().setDocumentMargin(18)
        reading_font = content.font()
        reading_font.setPointSizeF(max(12.0, reading_font.pointSizeF()))
        content.document().setDefaultFont(reading_font)
        topics.addItems([title for title, _ in GUIDE_TOPICS])
        splitter.addWidget(topics)
        splitter.addWidget(content)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([195, 615])
        layout.addWidget(splitter, 1)
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        def show_topic(index):
            if index >= 0:
                title, body = GUIDE_TOPICS[index]
                content.setHtml(f'<h1>{title}</h1>{body}')
                content.moveCursor(G.QTextCursor.Start)

        topics.currentRowChanged.connect(show_topic)
        topics.setCurrentRow(0)
        topics.setFocus()
        dialog.exec()

    def show_about(self):
        dialog = W.QMessageBox(self)
        dialog.setWindowTitle('About Jatayu Gallery')
        dialog.setTextFormat(C.Qt.RichText)
        dialog.setTextInteractionFlags(C.Qt.TextBrowserInteraction)
        dialog.setText(f'<b>Jatayu Gallery {VERSION}</b><br>Image viewer and editor for JatayuOS.'
                       '<br><a href="https://jatayuos.in">jatayuos.in</a>')
        dialog.setIconPixmap(self.windowIcon().pixmap(48, 48))
        dialog.exec()

    def show_license(self):
        W.QMessageBox.information(self, 'License',
            'Jatayu Gallery source code is licensed under the GNU General Public License version 3 (GPL-3.0-only). See LICENSE in the source or the packaged copyright notice.\n\n'
            'Qt, PyQt5 and Pillow are distributed separately under their own terms. '
            'On Debian-based systems, see the copyright files in /usr/share/doc for the installed packages.')

    def show_credits(self):
        W.QMessageBox.information(self, 'Credits',
            'JatayuOS project — Anup Kumar Yadav\n\n'
            'Built with Python, Qt Widgets, PyQt5 and Pillow. '
            'Thanks to the contributors to those projects.')

    def choose(self):
        self.stop_slideshow()
        pattern = ' '.join('*' + suffix for suffix in sorted(EXTENSIONS))
        filename, _ = W.QFileDialog.getOpenFileName(self, 'Open Image', '', f'Images ({pattern});;All Files (*)')
        if filename:
            self.open_path(Path(filename))

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.open_path(Path(url.toLocalFile()))
                event.acceptProposedAction()
                break

    def confirm_leave(self):
        self.commit_adjustment()
        if not self.history or self.history[self.position] is self.saved:
            return True
        choice = W.QMessageBox.question(self, 'Unsaved Edits', 'Save a copy before leaving this image?',
                                        W.QMessageBox.Save | W.QMessageBox.Discard | W.QMessageBox.Cancel,
                                        W.QMessageBox.Save)
        return choice == W.QMessageBox.Discard or (choice == W.QMessageBox.Save and self.save())

    def closeEvent(self, event):
        self.stop_slideshow()
        if self.confirm_leave():
            event.accept()
        else:
            event.ignore()

    def show_file_error(self, title, error):
        dialog = W.QMessageBox(W.QMessageBox.Warning, title, '', W.QMessageBox.Ok, self)
        dialog.setTextFormat(C.Qt.PlainText)
        dialog.setText(str(error))
        dialog.exec()

    def open_path(self, path, files=None):
        self.stop_slideshow()
        try:
            path = path.absolute()
            image = load_image(path)
        except (OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
            self.show_file_error('Cannot Open Image', error)
            return
        if not self.confirm_leave():
            return
        if files is None:
            try:
                files = sorted((item for item in path.parent.iterdir()
                                if item.suffix.lower() in EXTENSIONS and item.is_file()),
                               key=lambda item: (item.name.casefold(), item.name))
            except OSError:
                files = []
            if path not in files:
                files.append(path)
        changed_folder = files != self.files
        self.files = files
        self.index = files.index(path)
        self.original = image
        self.preview_key = None
        self.history = [(image, NEUTRAL)]
        self.position = 0
        self.saved = self.history[0]
        self.canvas.original = G.QPixmap()
        self.canvas.fit()
        self.compare_button.setChecked(False)
        self.canvas.compare = False
        if changed_folder:
            self.rebuild_thumbnails()
        self.toggle_thumbs(self.thumbs.isChecked())
        self.refresh()

    def navigate(self, direction, from_button=False):
        if not from_button and isinstance(self.focusWidget(), (W.QSlider, W.QSpinBox, W.QLineEdit)):
            return
        index = self.index + direction
        if 0 <= index < len(self.files):
            self.open_path(self.files[index], self.files)

    def rebuild_thumbnails(self):
        self.thumbnail_timer.stop()
        self.thumb_buttons.clear()
        film = W.QWidget(objectName='film')
        row = W.QHBoxLayout(film)
        row.setContentsMargins(10, 6, 10, 6)
        # Keep the filmstrip bounded even in very large wallpaper directories.
        first = max(0, min(self.index - 30, len(self.files) - 61))
        indices = range(first, min(first + 61, len(self.files)))
        for index in indices:
            path = self.files[index]
            button = W.QToolButton()
            button.setFixedSize(88, 70)
            button.setIconSize(C.QSize(77, 58))
            button.setToolTip(path.name)
            button.setAccessibleName(path.name)
            button.setText(str(index + 1))
            button.setCheckable(True)
            button.clicked.connect(lambda _, i=index: self.select_thumbnail(i))
            self.thumb_buttons[index] = button
            row.addWidget(button)
        row.addStretch()
        self.film.setWidget(film)
        self.thumb_pending = iter(indices)
        self.thumbnail_timer.start()

    def select_thumbnail(self, index):
        if index != self.index:
            self.open_path(self.files[index], self.files)
        self.update_thumbnail_selection()

    def load_thumbnail(self):
        if not self.film.isVisible():
            self.thumbnail_timer.stop()
            return
        index = next(self.thumb_pending, None)
        if index is None:
            self.thumbnail_timer.stop()
            return
        try:
            icon = G.QIcon(pixmap(load_image(self.files[index], thumbnail=True)))
        except (OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
            return
        self.thumb_buttons[index].setIcon(icon)

    def update_thumbnail_selection(self):
        if self.index not in self.thumb_buttons:
            self.rebuild_thumbnails()
        for index, button in self.thumb_buttons.items():
            button.setChecked(index == self.index)
        if self.index in self.thumb_buttons and self.film.isVisible():
            self.film.ensureWidgetVisible(self.thumb_buttons[self.index], 25, 0)
        if self.film.isVisible() and not self.thumbnail_timer.isActive():
            self.thumbnail_timer.start()

    def refresh(self):
        enabled = bool(self.history)
        self.fullscreen_button.setEnabled(enabled)
        self.play_button.setEnabled(len(self.files) > 1)
        self.save_button.setEnabled(enabled)
        self.edit_button.setEnabled(enabled)
        self.previous.setEnabled(self.index > 0)
        self.following.setEnabled(enabled and self.index + 1 < len(self.files))
        self.undo_button.setEnabled(enabled and self.position > 0)
        self.redo_button.setEnabled(self.position + 1 < len(self.history))
        self.counter.setText(f'{self.index + 1} of {len(self.files)}' if enabled else '')
        if not enabled:
            return
        source, values = self.history[self.position]
        name = self.files[self.index].name
        dirty = self.history[self.position] is not self.saved
        self.filename.setToolTip('')
        self.filename.setText(name + (' *' if dirty else ''))
        self.setWindowTitle(f'{name}{" *" if dirty else ""} — Jatayu Gallery')
        for slider, value, label in zip(self.sliders, values, self.values):
            with C.QSignalBlocker(slider):
                slider.setValue(value)
            label.setText(f'{value / 100:.2f}')
        self.canvas.selection = C.QRect()
        self.render_preview(source, values)
        self.sync_dimensions()

    def render_preview(self, source, values):
        key = (source, values)
        if self.preview_key and self.preview_key[0] is source and self.preview_key[1] == values:
            return
        self.preview_key = key
        prepared = source.copy()
        prepared.thumbnail((2400, 2400), Image.Resampling.BILINEAR)
        if self.canvas.original.isNull():
            original = self.original.copy()
            original.thumbnail((2400, 2400), Image.Resampling.BILINEAR)
            self.canvas.original = pixmap(original)
        self.canvas.same_dimensions = source.size == self.original.size
        self.canvas.image = pixmap(adjust(prepared, values))
        self.canvas.update()

    def push(self, image, values=NEUTRAL):
        del self.history[self.position + 1:]
        self.history.append((image, values))
        while (len(self.history) > 20 or
               (len(self.history) > 1 and
                sum(item.width * item.height for item in {id(record[0]): record[0]
                    for record in self.history}.values()) > MAX_PIXELS * 2)):
            self.history.pop(0)
        self.position = len(self.history) - 1
        self.refresh()

    def queue_adjustment(self):
        if not self.history:
            return
        for slider, label in zip(self.sliders, self.values):
            label.setText(f'{slider.value() / 100:.2f}')
        self.preview_timer.start()

    def slider_values(self):
        return tuple(slider.value() for slider in self.sliders)

    def preview_adjustment(self):
        if any(slider.isSliderDown() for slider in self.sliders):
            self.render_preview(self.history[self.position][0], self.slider_values())
        else:
            self.commit_adjustment()

    def commit_adjustment(self):
        self.preview_timer.stop()
        if self.history:
            source, values = self.history[self.position]
            current = self.slider_values()
            if current != values:
                self.push(source, current)

    def reset_adjustment(self):
        self.commit_adjustment()
        if self.history and self.history[self.position][1] != NEUTRAL:
            self.push(self.history[self.position][0])

    def undo(self):
        self.commit_adjustment()
        if self.position > 0:
            if self.history[self.position][0] is not self.history[self.position - 1][0]:
                self.canvas.fit()
            self.position -= 1
            self.refresh()

    def redo(self):
        self.commit_adjustment()
        if self.position + 1 < len(self.history):
            if self.history[self.position][0] is not self.history[self.position + 1][0]:
                self.canvas.fit()
            self.position += 1
            self.refresh()

    def transform(self, operation):
        self.commit_adjustment()
        if self.history:
            source, values = self.history[self.position]
            self.canvas.fit()
            self.push(source.transpose(operation), values)

    def crop(self):
        self.commit_adjustment()
        selected = self.canvas.selection
        bounds = self.canvas.rect_image
        if not self.history or selected.width() < 2 or selected.height() < 2:
            return
        source, values = self.history[self.position]
        x_scale, y_scale = source.width / bounds.width(), source.height / bounds.height()
        box = (math.floor((selected.left() - bounds.left()) * x_scale),
               math.floor((selected.top() - bounds.top()) * y_scale),
               min(source.width, math.ceil((selected.right() + 1 - bounds.left()) * x_scale)),
               min(source.height, math.ceil((selected.bottom() + 1 - bounds.top()) * y_scale)))
        self.canvas.fit()
        self.push(source.crop(box), values)

    def sync_dimensions(self):
        if self.history:
            source, _ = self.history[self.position]
            with C.QSignalBlocker(self.width_input), C.QSignalBlocker(self.height_input):
                self.width_input.setValue(source.width)
                self.height_input.setValue(source.height)

    def link_dimension(self, value, width_changed):
        if self.history and self.lock_ratio.isChecked():
            source, _ = self.history[self.position]
            other, ratio = ((self.height_input, source.height / source.width) if width_changed
                            else (self.width_input, source.width / source.height))
            with C.QSignalBlocker(other):
                other.setValue(round(value * ratio))

    def resize_image(self):
        self.commit_adjustment()
        if not self.history:
            return
        size = self.width_input.value(), self.height_input.value()
        if math.prod(size) > MAX_PIXELS:
            W.QMessageBox.warning(self, 'Resize Image', 'Choose dimensions below 32 megapixels.')
            return
        source, values = self.history[self.position]
        if source.size != size:
            self.canvas.fit()
            self.push(source.resize(size, Image.Resampling.LANCZOS), values)

    def save(self):
        self.commit_adjustment()
        if not self.history:
            return False
        path = self.files[self.index]
        suggested = path.with_name(path.stem + '-edited.png')
        filename, selected = W.QFileDialog.getSaveFileName(
            self, 'Save a Copy', str(suggested), 'PNG (*.png);;JPEG (*.jpg);;WebP (*.webp)',
            options=W.QFileDialog.DontConfirmOverwrite)
        if not filename:
            return False
        destination = Path(filename)
        if not destination.suffix:
            destination = destination.with_suffix({'JPEG (*.jpg)': '.jpg', 'WebP (*.webp)': '.webp'}.get(selected, '.png'))
        source, values = self.history[self.position]
        try:
            save_new(adjust(source, values), destination, self.original.info.get('icc_profile'))
        except FileExistsError:
            W.QMessageBox.warning(self, 'Save a Copy', 'That filename already exists. Choose a new name.')
            return False
        except (OSError, ValueError) as error:
            self.show_file_error('Save a Copy', error)
            return False
        self.saved = self.history[self.position]
        self.refresh()
        return True


def main():
    app = W.QApplication(sys.argv[:1])
    app.setApplicationName('Jatayu Gallery')
    app.setApplicationVersion(VERSION)
    app.setDesktopFileName(ICON)
    app.setStyle('Fusion')
    local_icon = Path(__file__).with_name(ICON + '.png')
    if not local_icon.is_file():
        local_icon = Path('/usr/share/icons/hicolor/128x128/apps/jatayu-gallery.png')
    icon = G.QIcon.fromTheme(ICON, G.QIcon(str(local_icon)))
    app.setWindowIcon(icon)
    window = Gallery()
    window.centralWidget().setStyleSheet(STYLE)
    window.show()
    if len(sys.argv) > 1:
        from urllib.parse import unquote, urlparse
        argument = sys.argv[1]
        url = urlparse(argument)
        if url.scheme == 'file' and url.netloc in ('', 'localhost'):
            argument = unquote(url.path)
        C.QTimer.singleShot(0, lambda: window.open_path(Path(argument)))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
