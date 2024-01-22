import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from PIL import Image as PILImage
from urllib import request
import json
import sqlite3

class CocktailAPI:
    BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1"

    @classmethod
    def search_cocktail(cls, cocktail_name):
        try:
            url = f"{cls.BASE_URL}/search.php?s={cocktail_name}"
            with request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                return data['drinks'][0] if data['drinks'] else None
        except Exception as e:
            return None

    @classmethod
    def fetch_ingredient_images(cls, ingredients):
        ingredient_images = {}
        for ingredient in ingredients:
            # Construct URL for ingredient image (this will depend on the API you're using)
            url = f"https://some-image-api.com/search?query={ingredient}"
            try:
                with request.urlopen(url) as response:
                    data = json.loads(response.read().decode())
                    # Extract the image URL from the data (will depend on the API response structure)
                    image_url = data['images'][0]['url']
                    ingredient_images[ingredient] = image_url
            except Exception as e:
                print(f"Error fetching image for {ingredient}: {e}")
        return ingredient_images

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("cocktails.db")
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cocktails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                instructions TEXT,
                image_url TEXT
            )
        ''')
        self.conn.commit()

    def insert_cocktail(self, name, category, instructions, image_url):
        self.cursor.execute('''
            INSERT INTO cocktails (name, category, instructions, image_url)
            VALUES (?, ?, ?, ?)
        ''', (name, category, instructions, image_url))
        self.conn.commit()

class AdvancedCocktailApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cocktail Explorer")
        self.geometry("800x600")  # Set your desired window size

        # Background Image
        background_image_path = os.path.join(os.path.dirname(__file__), "bg.jpg")
        original_background_image = Image.open(background_image_path)
        resized_background_image = original_background_image.resize((800, 600), Image.BICUBIC)
        self.background_image = ImageTk.PhotoImage(resized_background_image)

        # Main Frame
        self.main_frame = tk.Frame(self, bg="goldenrod", bd=5)
        self.main_frame.place(relx=0.5, rely=0.1, relwidth=0.75, relheight=0.8, anchor="n")

        self.background_label = tk.Label(self.main_frame, image=self.background_image)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # New attribute
        self.uploaded_image_path = None

        # Widgets
        self.label = tk.Label(self.main_frame, text="Enter Cocktail Name:", font=('Arial', 14, 'bold'), bg="goldenrod", fg="white")
        self.label.pack(pady=10)

        self.entry = tk.Entry(self.main_frame, font=('Arial', 12))
        self.entry.pack(pady=10)

        self.search_button = tk.Button(self.main_frame, text="Search", command=self.search_cocktail, font=('Arial', 12, 'bold'), bg="green", fg="white")
        self.search_button.pack(pady=10)

        self.result_text = tk.Text(self.main_frame, height=8, width=50, font=('Arial', 12), bg="white", wrap=tk.WORD)
        self.result_text.pack(pady=20)

        self.cocktail_image_label = tk.Label(self.main_frame, bg="white")
        self.cocktail_image_label.pack(pady=20)

        # Ingredient Images Frame
        self.ingredient_images_frame = tk.Frame(self.main_frame, bg="white")
        self.ingredient_images_frame.pack(pady=20)

        # Initialize Database
        self.database = Database()

    def search_cocktail(self):
        cocktail_name = self.entry.get()
        if not cocktail_name:
            messagebox.showinfo("Error", "Please enter a cocktail name.")
            return

        cocktail_data = CocktailAPI.search_cocktail(cocktail_name)
        if cocktail_data:
            self.display_cocktail_info(cocktail_data)
            self.display_cocktail_image(cocktail_data['strDrinkThumb'])
            self.save_cocktail_to_database(cocktail_data)

            # Extract ingredients from cocktail_data
            ingredients = [cocktail_data[f'strIngredient{i}'] for i in range(1, 16) if cocktail_data[f'strIngredient{i}']]
            self.display_ingredient_images(ingredients)
        else:
            messagebox.showinfo("Error", "Cocktail not found.")

    def save_cocktail_to_database(self, cocktail_data):
        name = cocktail_data['strDrink']
        category = cocktail_data['strCategory']
        instructions = cocktail_data['strInstructions']
        image_url = cocktail_data['strDrinkThumb']
        
        # Download and save the image locally
        local_image_path = f"images/{name.replace('/', '')}.jpg"  # Replace '/' with '' to avoid path issues
        try:
            request.urlretrieve(image_url, local_image_path)
        except Exception as e:
            print(f"Error downloading image: {e}")
            local_image_path = None  # Set as None if download fails

        # Insert cocktail data into the database
        self.database.insert_cocktail(name, category, instructions, local_image_path)

    def display_cocktail_info(self, cocktail_data):
        info = f"Name: {cocktail_data['strDrink']}\n"
        info += f"Category: {cocktail_data['strCategory']}\n"
        info += f"Instructions: {cocktail_data['strInstructions']}\n"
        
        # Display information about Cocktails
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, info)

    def display_cocktail_image(self, image_url):
        if self.uploaded_image_path:
            # If an image is uploaded, use the uploaded image
            image_path = self.uploaded_image_path
        else:
            # Otherwise, use the image URL from the API
            # Download the image to a local file
            image_path = f"images/{image_url.split('/')[-1]}"  # Extract the filename and create a local path
            try:
                request.urlretrieve(image_url, image_path)
            except Exception as e:
                messagebox.showerror("Image Download Error", f"Failed to download the image: {e}")
                return

        # Load and display the image
        image = self.load_image(image_path)
        if image:
            self.cocktail_image_label.configure(image=image)
            self.cocktail_image_label.image = image  # Keep a reference to prevent garbage collection
        else:
            messagebox.showerror("Image Load Error", "Failed to load the image.")

    def display_ingredient_images(self, ingredients):
        ingredient_images = CocktailAPI.fetch_ingredient_images(ingredients)
        for ingredient, image_url in ingredient_images.items():
            image = self.load_image(image_url)
            if image:
                label = tk.Label(self.ingredient_images_frame, image=image, bg="white")
                label.image = image  # Keep a reference
                label.pack(side=tk.LEFT, padx=5, pady=5)  # Arrange horizontally

    def load_image(self, image_path):
        img = Image.open(image_path)
        img = img.resize((150, 150), Image.BICUBIC)  # Resize to a consistent size
        return ImageTk.PhotoImage(img)

myapp = AdvancedCocktailApp()
myapp.mainloop()