from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests

def create_new_account():
    bsc_mainnet_rpc = 'https://bsc-dataseed.binance.org/'
    web3 = Web3(Web3.HTTPProvider(bsc_mainnet_rpc))

    # Bật middleware cho Binance Smart Chain
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # Tạo một ví mới
    new_account = web3.eth.account.create()

    return {
        "address": new_account.address,
        "private_key": new_account.key.hex()
    }
    
    
# Endpoint để lấy lịch sử giao dịch của tài khoản
def get_balance_deposit(address):
    url = f'https://api.bscscan.com/api?module=account&action=tokentx&address={address}&apikey=FT21DJ6VYJ54XG8BGG57ZHVE8UR3SYPK8E&offset=100&contractaddress=0x55d398326f99059ff775485246999027b3197955'
    # Gửi yêu cầu GET đến API
    transactions = requests.get(url)
    balance = 0
    for transaction in transactions.json()['result']:
        balance += int(transaction['value'])/10**18
    return balance

import qrcode

def generate_qr(wallet_address):
    # Tạo nội dung cho mã QR code (ví dụ: địa chỉ ví và số tiền)
    content = f"ethereum:{wallet_address}"

    # Tạo đối tượng QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Thêm nội dung vào QR code
    qr.add_data(content)
    qr.make(fit=True)

    # Tạo ảnh QR code
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Lưu ảnh QR code ra file
    qr_img.save(f"./qr_code/{wallet_address}.png")
    return qr_img

def gen_key():
    import random
    import string
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
    return key