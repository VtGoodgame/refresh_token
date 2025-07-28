from src import to_sign_data as sign
from src import consts as c 
from src import send_request as send
import json

async def main():
    sign.get_certificates_list()
    
    # Подписание данных
    print("\n=== Подписание данных ===")
    signer = sign.CryptoProSigner()
    
    if signer.initialize_store():
        if signer.select_certificate(c.The_print):  # Можно указать отпечаток
            data_sign = send.AsyncAPIHandler._make_request()
            data_to_base64= send.AsyncAPIHandler.decode_data(data_sign)
            signature = signer.sign_data(data_to_base64["data"])
            
            if signature:
                print(f"Подпись создана успешно")
                
                # Проверка подписи
                print("\n=== Проверка подписи ===")
                signer.verify_signature(signature, data_sign)
            
            signer.close()
            response= send.AsyncAPIHandler.get_auth_token(data_sign["uuid"],signature)
            return await response.json()