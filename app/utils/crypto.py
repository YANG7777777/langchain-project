import rsa
import os

# 密钥文件路径
PRIVATE_KEY_PATH = "app/utils/rsa_private_key.pem"
PUBLIC_KEY_PATH = "app/utils/rsa_public_key.pem"

# 生成RSA密钥对
def generate_rsa_keys():
    """生成RSA密钥对并保存到文件"""
    if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
        print("生成RSA密钥对...")
        (pubkey, privkey) = rsa.newkeys(2048)
        
        # 保存私钥
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(privkey.save_pkcs1())
        
        # 保存公钥
        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(pubkey.save_pkcs1())
        
        print("RSA密钥对生成完成！")
    else:
        print("RSA密钥对已存在，跳过生成")

# 获取公钥
def get_public_key():
    """获取RSA公钥"""
    with open(PUBLIC_KEY_PATH, "rb") as f:
        pubkey = rsa.PublicKey.load_pkcs1(f.read())
    return pubkey

# 获取私钥
def get_private_key():
    """获取RSA私钥"""
    with open(PRIVATE_KEY_PATH, "rb") as f:
        privkey = rsa.PrivateKey.load_pkcs1(f.read())
    return privkey

# 加密数据
def rsa_encrypt(data):
    """使用RSA公钥加密数据"""
    pubkey = get_public_key()
    encrypted = rsa.encrypt(data.encode('utf-8'), pubkey)
    return encrypted.hex()

# 解密数据
def rsa_decrypt(encrypted_data):
    """使用RSA私钥解密数据
    支持十六进制和Base64两种编码格式
    """
    import base64
    privkey = get_private_key()
    
    # 尝试十六进制解码
    try:
        print(f"尝试十六进制解码: {encrypted_data[:20]}...")
        decrypted = rsa.decrypt(bytes.fromhex(encrypted_data), privkey)
        print("十六进制解码成功")
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"十六进制解码失败: {e}")
    
    # 尝试Base64解码
    try:
        print(f"尝试Base64解码: {encrypted_data[:20]}...")
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = rsa.decrypt(encrypted_bytes, privkey)
        print("Base64解码成功")
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Base64解码失败: {e}")
    
    # 两种解码方式都失败，抛出异常
    raise Exception("解密失败：既不是有效的十六进制格式，也不是有效的Base64格式")

# 获取公钥字符串
def get_public_key_string():
    """获取格式化的公钥字符串（用于前端）"""
    with open(PUBLIC_KEY_PATH, "rb") as f:
        pubkey_str = f.read().decode('utf-8')
    return pubkey_str

# 初始化密钥
def init_crypto():
    """初始化加密模块"""
    generate_rsa_keys()

# 测试加密解密功能
if __name__ == "__main__":
    # 初始化
    init_crypto()
    
    # 测试加密解密
    test_data = "123456"
    encrypted = rsa_encrypt(test_data)
    decrypted = rsa_decrypt(encrypted)
    
    print(f"原始数据: {test_data}")
    print(f"加密后: {encrypted}")
    print(f"解密后: {decrypted}")
    print(f"解密是否成功: {test_data == decrypted}")
