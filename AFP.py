import sys
import os
import numpy as np
from PIL import Image, ImageEnhance
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QFileDialog, QWidget, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt
import cv2

def auto_balance_color(image_array):
    """
    Automatically balance the color channels using the film's white border.
    :param image_array: Input image as a NumPy array
    :return: Color-balanced image as a NumPy array
    """
    border_height = int(image_array.shape[0] * 0.05)
    border_area = image_array[:border_height, :, :]

    mean_red = np.mean(border_area[:, :, 0])
    mean_green = np.mean(border_area[:, :, 1])
    mean_blue = np.mean(border_area[:, :, 2])

    mean_gray = (mean_red + mean_green + mean_blue) / 3
    red_correction = mean_gray / mean_red
    green_correction = mean_gray / mean_green
    blue_correction = mean_gray / mean_blue

    balanced_image = image_array.copy()
    balanced_image[:, :, 0] = np.clip(balanced_image[:, :, 0] * red_correction, 0, 255)
    balanced_image[:, :, 1] = np.clip(balanced_image[:, :, 1] * green_correction, 0, 255)
    balanced_image[:, :, 2] = np.clip(balanced_image[:, :, 2] * blue_correction, 0, 255)

    return balanced_image

def auto_adjust_exposure(image_array):
    """
    Automatically adjust the exposure of an image to correct overexposure or underexposure.
    :param image_array: Input image as a NumPy array
    :return: Exposure-adjusted image as a NumPy array
    """
    # Convert to grayscale to calculate brightness
    gray = np.mean(image_array, axis=2)
    mean_brightness = np.mean(gray)

    # Target brightness level (mid-gray)
    target_brightness = 128.0

    # Calculate adjustment factor
    adjustment_factor = target_brightness / mean_brightness

    # Apply adjustment to all channels
    adjusted_image = image_array * adjustment_factor
    adjusted_image = np.clip(adjusted_image, 0, 255)

    return adjusted_image.astype(np.uint8)

def auto_enhance_image(image_pil):
    """
    Automatically enhance the image by adjusting brightness, contrast, sharpness, and exposure.
    :param image_pil: Input image as a PIL Image object
    :return: Enhanced image as a PIL Image object
    """
    # Enhance brightness
    enhancer = ImageEnhance.Brightness(image_pil)
    image_enhanced = enhancer.enhance(1.2)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image_enhanced)
    image_enhanced = enhancer.enhance(1.3)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image_enhanced)
    image_enhanced = enhancer.enhance(1.5)

    return image_enhanced

class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Quartz_AutoFilmProc")
        self.setWindowIcon(QIcon("main_icon.png"))
        self.image = None
        self.processed_image = None

        self.initUI()

    def initUI(self):
        self.image_label = QLabel("尚未加载图像", self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; font-size: 18px; padding: 10px;")

        load_button = QPushButton("加载图像", self)
        load_button.setStyleSheet("background-color: #2196F3; color: white; font-size: 14px; padding: 8px;")
        load_button.clicked.connect(self.load_image)

        process_button = QPushButton("处理图像", self)
        process_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 8px;")
        process_button.clicked.connect(self.process_image)

        batch_button = QPushButton("批量处理", self)
        batch_button.setStyleSheet("background-color: #FFC107; color: white; font-size: 14px; padding: 8px;")
        batch_button.clicked.connect(self.batch_process_images)

        save_button = QPushButton("保存图像", self)
        save_button.setStyleSheet("background-color: #F44336; color: white; font-size: 14px; padding: 8px;")
        save_button.clicked.connect(self.save_image)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(load_button)
        button_layout.addWidget(process_button)
        button_layout.addWidget(batch_button)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Simplify the style for a modern, clean look
        self.setStyleSheet("background-color: #ffffff; font-family: Arial, sans-serif;")

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "打开图像文件", "", "Images (*.png *.jpg *.bmp)")
        if file_name:
            self.image = Image.open(file_name)
            self.display_image(self.image)

    def process_image(self):
        if self.image is None:
            QMessageBox.warning(self, "未加载图像", "请先加载图像。")
            return

        # Convert image to NumPy array
        image_array = np.array(self.image)

        # Step 1: Invert the colors of the negative
        inverted_image = 255 - image_array

        # Step 2: Apply auto-balance
        balanced_image = auto_balance_color(inverted_image)

        # Step 3: Adjust exposure
        exposure_adjusted_image = auto_adjust_exposure(balanced_image)

        # Step 4: Convert to PIL image
        exposure_adjusted_image_pil = Image.fromarray(exposure_adjusted_image)

        # Step 5: Enhance the image
        self.processed_image = auto_enhance_image(exposure_adjusted_image_pil)

        # Display the processed image
        self.display_image(self.processed_image)

    def batch_process_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder_path:
            return

        save_folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not save_folder:
            return

        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                continue

            # Open image and process
            try:
                image = Image.open(file_path)
                image_array = np.array(image)

                # Step 1: Invert the colors of the negative
                inverted_image = 255 - image_array

                # Step 2: Apply auto-balance
                balanced_image = auto_balance_color(inverted_image)

                # Step 3: Adjust exposure
                exposure_adjusted_image = auto_adjust_exposure(balanced_image)

                # Step 4: Convert to PIL image
                exposure_adjusted_image_pil = Image.fromarray(exposure_adjusted_image)

                # Step 5: Enhance the image
                enhanced_image = auto_enhance_image(exposure_adjusted_image_pil)

                # Save processed image
                save_path = os.path.join(save_folder, file_name)
                enhanced_image.save(save_path)

            except Exception as e:
                QMessageBox.warning(self, "处理错误", f"文件 {file_name} 处理失败: {e}")

        QMessageBox.information(self, "批量处理完成", "所有图像已成功处理并保存。")

    def save_image(self):
        if self.processed_image is None:
            QMessageBox.warning(self, "未处理图像", "请先处理图像。")
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "保存图像文件", "", "Images (*.png *.jpg *.bmp)")
        if file_name:
            self.processed_image.save(file_name)

    def display_image(self, image):
        image = image.convert("RGB")
        qimage = QImage(
            image.tobytes(), image.width, image.height, image.width * 3, QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimage)

        # Scale the image to fit the screen size
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        pixmap = pixmap.scaled(
            screen_width * 0.8, screen_height * 0.8, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec_())
