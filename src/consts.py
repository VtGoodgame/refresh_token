from dotenv import load_dotenv
import os

load_dotenv()

#CryptoPro
Serial_number = os.getenv("")
The_print=os.getenv("The_print")
Key_ID=os.getenv("Key_ID")
number_certificate=os.getenv("Serial_number_certificate")
Path_to_certificates =os.getenv("Path_to_certificates")
certificates_path=os.getenv("User_certificates_path")
Cryptopro_path =os.getenv("Cryptopro_path")
launch_shortcut=os.getenv("launch_shortcut")

BASE_URL = "https://elk.prod.markirovka.ismet.kz/api/v3/true-api"; 
GET_KEY = "/auth/key"
URL_TOKEN = BASE_URL + "auth/token";