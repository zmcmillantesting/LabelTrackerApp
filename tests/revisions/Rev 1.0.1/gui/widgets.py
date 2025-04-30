from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap

class ClickableImageLabel(QLabel):
    """A QLabel that displays an image and emits a clicked signal."""
    clicked = pyqtSignal() # Signal emitted when the label is clicked
    
    def __init__(self, image_path: str, status_value: str, parent=None):
        super().__init__(parent)
        self.status_value = status_value # "Pass" or "Fail"
        self._is_selected = False
        
        # Load and set the image
        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
             print(f"Warning: Could not load image at {image_path}")
             self.setText(f"Img Err ({self.status_value})") # Fallback text
        else:
             # Scale pixmap initially if needed (adjust size as desired)
             # self.pixmap = self.pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
             self.setPixmap(self.pixmap)
             
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("QLabel { border: 2px solid transparent; padding: 5px; }") # Basic styling

    def mousePressEvent(self, event):
        """Handle mouse press event to emit the clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        """Update the selection state and visual appearance."""
        self._is_selected = selected
        if selected:
            # Highlight when selected (e.g., border color)
            self.setStyleSheet("QLabel { border: 3px solid blue; padding: 5px; background-color: #E0E0FF; }") 
        else:
            # Default appearance
             self.setStyleSheet("QLabel { border: 2px solid transparent; padding: 5px; }")

    def is_selected(self):
        return self._is_selected 