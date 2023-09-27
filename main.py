import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout  # Import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.textinput import TextInput
import shutil
import os
import cv2
import numpy as np
import array as arr
import requests
from kivy.clock import Clock

class ChildApp(BoxLayout):
    def __init__(self, **kwargs):
        super(ChildApp, self).__init__(**kwargs)
        self.cols = 2

        self.add_widget(Label(text='Plant Image'))
        self.s_name = FileChooserListView()
        self.add_widget(self.s_name)

        self.add_widget(Label(text='Soil Image'))
        self.s_marks = FileChooserListView()
        self.add_widget(self.s_marks)

        self.add_widget(Label(text='Submit Button'))
        self.s_gender = Button(text='Save Images')
        self.s_gender.bind(on_press=self.save_images)
        self.add_widget(self.s_gender)

        # Add a TextInput widget to display messages
        self.log_output = TextInput(multiline=True, readonly=True, size_hint_y=None, height=400)
        self.add_widget(self.log_output)

        self.log_output.text = "Welcome to the Smart Agriculture App!\n"

    def calculate_fertilizer_amount(self, land_area, potassium_percent, nitrogen_percent, phosphorus_percent):
        # Define the desired ratio (4:2:1)
        desired_ratio = [4, 2, 1]

        # Calculate the sum of the desired ratio components
        total_ratio = sum(desired_ratio)

        # Calculate the nutrient amounts based on the desired ratio
        required_potassium = (land_area * potassium_percent * desired_ratio[0]) / (100 * total_ratio)
        required_nitrogen = (land_area * nitrogen_percent * desired_ratio[1]) / (100 * total_ratio)
        required_phosphorus = (land_area * phosphorus_percent * desired_ratio[2]) / (100 * total_ratio)

        return {
            'potassium': required_potassium,
            'nitrogen': required_nitrogen,
            'phosphorus': required_phosphorus,
        }

    def calculate_water_required(self, current_moisture_percentage, target_moisture_percentage, land_size_acres=1):
        # Calculate the water required to reach the target moisture percentage
        water_required = (land_size_acres * 43560) * (target_moisture_percentage - current_moisture_percentage) / 100
        return water_required  # in cubic feet

    def get_rain_forecast(self, api_key, city):
        base_url = "http://api.openweathermap.org/data/2.5/forecast"

        # Make the API request
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",  # You can change units to "imperial" for Fahrenheit
        }
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            print(f"Rain forecast for {city} in the next few days:")
            for forecast in data['list']:
                dt_txt = forecast['dt_txt']
                rain_info = forecast.get('rain', {})
                rain_3h = rain_info.get('3h', 0)
                print(f"Time: {dt_txt}, Rain (3h): {rain_3h} mm")
        else:
            print("Failed to fetch rain forecast data. Check your API key or city name.")

    def detect_bug(self, image):
        # Load the image
        # image = cv2.imread(image)

        # Convert the image to the HSV color space (Hue, Saturation, Value)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define the lower and upper bounds of the red color (you can adjust these values)
        lower_red = np.array([0, 100, 100])  # Lower bound for red color in HSV
        upper_red = np.array([10, 255, 255])  # Upper bound for red color in HSV

        # Create a mask to identify pixels within the specified color range
        mask = cv2.inRange(hsv_image, lower_red, upper_red)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Check if any contours were found (potential bugs)
        if len(contours) > 0:
            print("Bugs detected in the image!")
        else:
            print("No bugs detected in the image.")

        # Display the image with rectangles
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def estimate_soil_moisture(self, image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        average_intensity = np.mean(gray_image)

        wet_threshold = 100
        dry_threshold = 200

        if average_intensity <= wet_threshold:
            moisture_percentage = 100.0
        elif average_intensity >= dry_threshold:
            moisture_percentage = 0.0
        else:
            moisture_percentage = 100.0 - (
                    (average_intensity - wet_threshold) / (dry_threshold - wet_threshold)) * 100.0
        if (moisture_percentage <= 75):
            current_moisture_percentage = moisture_percentage
            target_moisture_percentage = 75.0  # You can change this to your desired target percentage
            land_size_acres = 1  # You can change this to your land size in acres

            water_required_cubic_feet = calculate_water_required(current_moisture_percentage,
                                                                 target_moisture_percentage,
                                                                 land_size_acres)
            water_required_gallons = water_required_cubic_feet * 7.48052  # Convert cubic feet to gallons

            print(
                f"Water required to raise the moisture percentage to {target_moisture_percentage}% for {land_size_acres} acre(s):")
            print(f"{water_required_gallons:.2f} gallons")
        else:
            print("No watering is required ")

        return moisture_percentage

    def calculate_percentage_in_range(self, image, color_range):
        # Convert the image to HSV color space
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create a binary mask for the pixels within the specified color range
        mask = cv2.inRange(hsv_image, color_range[0], color_range[1])

        # Count the number of pixels within the color range
        num_pixels_in_range = np.sum(mask > 0)

        # Total number of pixels in the image
        total_pixels = image.shape[0] * image.shape[1]

        # Calculate the percentage
        percentage = (num_pixels_in_range / total_pixels) * 100

        return percentage

    def draw_rectangles(self, image, contours, color):
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

    def print_to_log(self, message):
        current_text = self.log_output.text
        new_text = f"{current_text}\n{message}"
        self.log_output.text = new_text

    def save_images(self, instance):
        # Get the selected file paths
        plant_image_path = self.s_name.selection and self.s_name.selection[0] or None
        soil_image_path = self.s_marks.selection and self.s_marks.selection[0] or None

        if plant_image_path and soil_image_path:
            # Specify the destination folders where you want to save the images
            destination_folder1 = 'plant_images'
            destination_folder2 = 'soil_images'

            # Create the destination folders if they don't exist
            if not os.path.exists(destination_folder1):
                os.makedirs(destination_folder1)
            if not os.path.exists(destination_folder2):
                os.makedirs(destination_folder2)

            # Copy the selected images to both destination folders
            shutil.copy(plant_image_path, os.path.join(destination_folder1, 'plant_image.png'))
            shutil.copy(soil_image_path, os.path.join(destination_folder2, 'soil_image.png'))

            plant_message = f"Plant image saved to {destination_folder1}"
            soil_message = f"Soil image saved to {destination_folder2}"

            # Print messages to the log
            self.print_to_log(plant_message)
            self.print_to_log(soil_message)

            # Continue with the second part of your program
            api_key = "d850f7f52bf19300a9eb4b0aa6b80f0d"  # Replace with your OpenWeatherMap API key
            city = "Hyderabad"  # City name
            #self.get_rain_forecast(api_key, city)

            folderPath = "soil_images"
            mylist1 = os.listdir(folderPath)
            self.print_to_log(str(mylist1))

            for impath in mylist1:
                image = cv2.imread(f'{folderPath}/{impath}')
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                _, binary_image = cv2.threshold(gray_image, 100, 255, cv2.THRESH_BINARY)

                contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                moisture_percentage = self.estimate_soil_moisture(image)

                self.print_to_log(f'Moisture: {moisture_percentage:.2f}%')

                cv2.imshow("Webcam Feed", image)
                cv2.waitKey(1000)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

            a = arr.array('d', [])
            folderPath = "plant_images"
            mylist = os.listdir(folderPath)
            self.print_to_log(str(mylist))

            for impath in mylist:

                image = cv2.imread(f'{folderPath}/{impath}')
                self.detect_bug(image)

                color_range = np.array([(30, 0, 0), (90, 255, 255)])
                hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv_image, color_range[0], color_range[1])
                total_pixels = image.shape[0] * image.shape[1]

                n_deficiency_range = [(30, 0, 0), (90, 255, 255)]
                p_deficiency_range = [(120, 0, 0), (150, 255, 255)]
                k_deficiency_range = [(0, 0, 0), (30, 255, 255)]

                n_mask = cv2.inRange(hsv_image, *n_deficiency_range)
                p_mask = cv2.inRange(hsv_image, *p_deficiency_range)
                k_mask = cv2.inRange(hsv_image, *k_deficiency_range)

                n_pixels = cv2.countNonZero(n_mask)
                p_pixels = cv2.countNonZero(p_mask)
                k_pixels = cv2.countNonZero(k_mask)

                self.print_to_log(f'Pixels indicating N deficiency: {n_pixels}')
                self.print_to_log(f'Pixels indicating P deficiency: {p_pixels}')
                self.print_to_log(f'Pixels indicating K deficiency: {k_pixels}')
                a.append(n_pixels)
                a.append(p_pixels)
                a.append(k_pixels)
                n = len(a)
                max = a[0]

                for i in range(1, n):
                    if a[i] < max:
                        max = a[i]
                p = (p_pixels / total_pixels) * 100
                k = (k_pixels / total_pixels) * 100
                n = (n_pixels / total_pixels) * 100
                self.print_to_log(f'potassium defienecy  :- {k:.2f}%')
                self.print_to_log(f'phosphorus defienecy :- {p:.2f}%')
                self.print_to_log(f'nitrogen defienecy  :- {n:.2f}%')
                cv2.imshow("Webcam Feed", image)

                land_area = 1
                potassium_percent = k
                nitrogen_percent = n
                phosphorus_percent = p

                fertilizer_amounts = self.calculate_fertilizer_amount(land_area, potassium_percent, nitrogen_percent,
                                                                      phosphorus_percent)
                self.print_to_log("Fertilizer amounts (in kg) to maintain a 4:2:1 ratio:")
                self.print_to_log(f"Potassium: {fertilizer_amounts['potassium']:.2f} kg")
                self.print_to_log(f"Nitrogen: {fertilizer_amounts['nitrogen']:.2f} kg")
                self.print_to_log(f"Phosphorus: {fertilizer_amounts['phosphorus']:.2f} kg")

                contours1, _ = cv2.findContours(n_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours2, _ = cv2.findContours(p_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours3, _ = cv2.findContours(k_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                cv2.waitKey(1000)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    def __init__(self, **kwargs):
        super(ChildApp, self).__init__(**kwargs)
        self.orientation = 'vertical'  # Set the orientation to vertical
        self.spacing = 10  # Adjust the spacing between widgets
        self.padding = 10  # Add padding to the layout

        self.add_widget(Label(text='Plant Image'))
        self.s_name = FileChooserIconView()
        self.add_widget(self.s_name)

        self.add_widget(Label(text='Soil Image'))
        self.s_marks = FileChooserIconView()
        self.add_widget(self.s_marks)

        self.add_widget(Button(text='Save Images', on_press=self.save_images))

        # Add a TextInput widget to display messages
        self.log_output = TextInput(multiline=True, readonly=True, size_hint_y=None, height=400)
        self.add_widget(self.log_output)

        self.log_output.text = "Welcome to the Smart Agriculture App!\n"


class smartagricultureapp(App):
    def build(self):
        return ChildApp()


if __name__ == "__main__":
    smartagricultureapp().run()
