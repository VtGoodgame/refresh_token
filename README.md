<!--
  ╔════╗ ╔═══╗ ╔═══╗   ╔════╗       🚀 Модуль автоматического обновления токенов
  ║    ║ ║   ║ ║   ║   ║    ║       🔗 Интеграция с True Api "Честный Знак"
  ╠══╦═╝ ║ ═╦╝ ║ ═╦╝   ║ ═╦═╝
  ║  ╚╗  ║  ║  ║  ║    ║  ║         💡 FastAPI • Docker • Redis
  ╚═══╝  ╚══╝  ╚══╝    ╚══╝
-->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python"/>
  <img src="https://img.shields.io/badge/Pytest-0.116-green?style=for-the-badge&logo=pytest&logoColor=white"/>
  <img src="https://img.shields.io/badge/Mocking-Fake-blue?style=for-the-badge&logo=mock&logoColor=white"/>
  <img src="https://img.shields.io/badge/Честный_Знак-True_Api-22B07D?style=for-the-badge&logo=chess&logoColor=white"/>
</p>
>  📌 Задание: автоматическое обновление токенов Честный знак с использованием документации к api - True Api 
## 📌 Описание

Проект представляет собой специальный модуль котоый:
- Отправляет get запрос к True Api для получения полей UUID и data.
- Переводит data в base64.
- Подписывает данные data с помощью приватного ключа открепленного сертификата(CryptoPro).
- Отправляет post запрос к True Api  и передает подписанные данные типа base64(data)
- Получает код авторизации, после чего можно получить токен с использованием сертификата и ИНН организации.
  
  ## 🔐 Конфигурация (`.env`)
Перед запуском создайте файл `.env` в корне проекта с переменными окружения:
```env
#Данные сертификата
Serial_number=""
The_print=""
Key_ID=""
Serial_number_certificate=""
Path_to_certificates =""

#Global URL
BASE_URL = "https://elk.prod.markirovka.ismet.kz/api/v3/true-api"
GET_KEY = "/auth/key"
URL_TOKEN = BASE_URL + "auth/token"
```
## 🎯 Инструкция по запуску

## Установка (Windows)
**1.Клонирование репозитория**
 ```bash
 git clone https://github.com/VtGoodgame/refresh_token.git
 ```
**2.Переход в директорию `FASTAPI_Tron`**
 ```bash
 cd refresh_token/
```
**3.Создание виртуального окружения**
 ```bash
python -m venv venv
```
**4.Активировать виртуальное окружение**
 ```bash
 .\venv\Scripts\activate
```
**5.Установить зависимости из файла `requirements.txt`**
 ```bash
pip install -r requirements.txt
```
## Запуск Тестов

**1. Перейти в папку проекта**
```bash
cd .\refresh_token\
```  
**Запустить тесты с подробным выводом**
```bash
pytest --v
```
### На данный момент проект остановлен на этапе тестирования и рефакторинга!

<p align="center"><i>Спасибо за использование моего проекта!</i></p>
