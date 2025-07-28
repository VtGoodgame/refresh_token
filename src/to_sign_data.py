import win32com.client
import base64

class CryptoProSigner:
    def __init__(self):
        self.store = None
        self.certificate = None
    
    def initialize_store(self, store_location=3):
        """
        Инициализация хранилища сертификатов для получения доступа к сертификатам
        store_location: 3 - Current User, 2 - Local Machine
        """
        try:
            self.store = win32com.client.Dispatch("CAdESCOM.Store")
            self.store.Open(store_location)
            return True
        except Exception as e:
            print(f"Ошибка инициализации хранилища: {e}")
            return False
    
    def select_certificate(self, thumbprint=None):
        """
        Выбор сертификата для подписания по отпечатку
        """
        try:
            if not self.store:
                raise Exception("Хранилище не инициализировано")
            
            certificates = self.store.Certificates
            
            if thumbprint:
                # Поиск по отпечатку
                certificates = certificates.Find(0, thumbprint, False)
            else:
                # Получение первого доступного сертификата
                certificates = certificates.Find(1, "", False)
            
            if certificates.Count == 0:
                raise Exception("Сертификат не найден")
            
            self.certificate = certificates.Item(1)
            print(f"Выбран сертификат: {self.certificate.SubjectName}")
            return True
            
        except Exception as e:
            print(f"Ошибка выбора сертификата: {e}")
            return False
    
    def sign_data(self, data_to_sign, detached=True):
        """
        Подписание данных
        """
        try:
            if not self.certificate:
                raise Exception("Сертификат не выбран")
            
            # Создание объекта для подписания
            signed_data = win32com.client.Dispatch("CAdESCOM.CadesSignedData")
            signed_data.Content = data_to_sign
            
            # Настройка подписи
            signer = win32com.client.Dispatch("CAdESCOM.CPSigner")
            signer.Certificate = self.certificate
            
            # Подписание
            # 0 - CAdES BES
            # 1 - CAdES-X Long Type 1  
            signature = signed_data.SignCades(signer, 0, detached)
            
            return signature
            
        except Exception as e:
            print(f"Ошибка подписания: {e}")
            return None
    
    def verify_signature(self, signature, original_data=None):
        """
        Проверка подписи
        """
        try:
            signed_data = win32com.client.Dispatch("CAdESCOM.CadesSignedData")
            
            if original_data:
                signed_data.Content = original_data
            
            signed_data.VerifyCades(signature, 0, False)
            print("Подпись действительна")
            return True
            
        except Exception as e:
            print(f"Подпись недействительна: {e}")
            return False
    
    def close(self):
        """
        Закрытие хранилища
        """
        if self.store:
            self.store.Close()

