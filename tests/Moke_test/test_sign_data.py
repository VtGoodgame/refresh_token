# Moke tests/test_cryptopro_signer.py

from unittest.mock import MagicMock, patch
from src.to_sign_data import CryptoProSigner  


class TestCryptoProSigner:
    def setup_method(self):
        """Выполняется перед каждым тестом"""
        self.signer = CryptoProSigner()

    @patch("win32com.client.Dispatch")
    def test_initialize_store_success(self, mock_dispatch):
        # Мокаем COM-объект Store
        mock_store = MagicMock()
        mock_dispatch.return_value = mock_store

        result = self.signer.initialize_store(store_location=3)

        assert result is True
        assert self.signer.store == mock_store
        mock_store.Open.assert_called_once_with(3)

    @patch("win32com.client.Dispatch")
    def test_initialize_store_failure(self, mock_dispatch):
        mock_dispatch.side_effect = Exception("COM error")

        result = self.signer.initialize_store()

        assert result is False
        assert self.signer.store is None

    @patch("win32com.client.Dispatch")
    def test_select_certificate_success_by_thumbprint(self, mock_dispatch):
        self.signer.initialize_store()  # предварительно инициализируем store

        mock_certificates = MagicMock()
        mock_cert = MagicMock()
        mock_cert.SubjectName = "CN=Test User"
        mock_certificates.Count = 1
        mock_certificates.Item.return_value = mock_cert

        # Мокаем Certificates и Find
        self.signer.store.Certificates = mock_certificates # type: ignore
        mock_certificates.Find.return_value = mock_certificates

        result = self.signer.select_certificate(thumbprint="ABC123")

        assert result is True
        assert self.signer.certificate == mock_cert
        mock_certificates.Find.assert_called_with(0, "ABC123", False)

    @patch("win32com.client.Dispatch")
    def test_select_certificate_first_available(self, mock_dispatch):
        self.signer.initialize_store()

        mock_certificates = MagicMock()
        mock_cert = MagicMock()
        mock_cert.SubjectName = "CN=Default User"
        mock_certificates.Count = 1
        mock_certificates.Item.return_value = mock_cert

        self.signer.store.Certificates = mock_certificates # type: ignore
        mock_certificates.Find.return_value = mock_certificates

        result = self.signer.select_certificate()

        assert result is True
        mock_certificates.Find.assert_called_with(1, "", False)


    @patch("win32com.client.Dispatch")
    def test_select_certificate_not_found(self, mock_dispatch):
        # Мокаем хранилище и сертификаты
        mock_store = MagicMock()
        mock_certificates = MagicMock()
        mock_filtered_certs = MagicMock()

        # Настраиваем цепочку вызовов
        mock_dispatch.return_value = mock_store
        mock_store.Certificates = mock_certificates

        # Find() возвращает другой объект — mock_filtered_certs
        mock_certificates.Find.return_value = mock_filtered_certs
        mock_filtered_certs.Count = 0  # ← сертификатов нет

        self.signer.store = mock_store

        result = self.signer.select_certificate()

        assert result is False
        assert self.signer.certificate is None


    @patch("win32com.client.Dispatch")
    def test_select_certificate_store_not_initialized(self, mock_dispatch):
        result = self.signer.select_certificate()

        assert result is False

    @patch("win32com.client.Dispatch")
    def test_sign_data_success(self, mock_dispatch):
        # Подготовка моков
        mock_certificate = MagicMock()
        self.signer.certificate = mock_certificate

        mock_signer = MagicMock()
        mock_signed_data = MagicMock()
        mock_signed_data.SignCades.return_value = "valid_signature"

        # Настраиваем Dispatch
        mock_dispatch.side_effect = [mock_signed_data, mock_signer]

        data = "Hello, World!"
        signature = self.signer.sign_data(data, detached=True)

        assert signature == "valid_signature"
        mock_signed_data.SignCades.assert_called_once_with(mock_signer, 0, True)

    @patch("win32com.client.Dispatch")
    def test_sign_data_no_certificate(self, mock_dispatch):
        result = self.signer.sign_data("data")

        assert result is None

    @patch("win32com.client.Dispatch")
    def test_verify_signature_valid(self, mock_dispatch):
        mock_signed_data = MagicMock()
        mock_dispatch.return_value = mock_signed_data

        result = self.signer.verify_signature("valid_sig", "original_data")

        assert result is True
        mock_signed_data.VerifyCades.assert_called_once_with("valid_sig", 0, False)

    @patch("win32com.client.Dispatch")
    def test_verify_signature_invalid(self, mock_dispatch):
        mock_signed_data = MagicMock()
        mock_signed_data.VerifyCades.side_effect = Exception("Invalid signature")
        mock_dispatch.return_value = mock_signed_data

        result = self.signer.verify_signature("invalid_sig", "data")

        assert result is False

    @patch("win32com.client.Dispatch")
    def test_close(self, mock_dispatch):
        # Имитируем инициализацию
        mock_store = MagicMock()
        self.signer.store = mock_store

        self.signer.close()
        mock_store.Close.assert_called_once()
        assert self.signer.store is None  # или оставить как есть — зависит от логики