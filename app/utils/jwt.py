import jwt
import datetime
from typing import Optional, Dict

# JWT配置
SECRET_KEY = "your-secret-key-change-this-in-production"  # 在生产环境中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: Dict[str, str], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要存储在令牌中的数据
        expires_delta: 过期时间增量
        
    Returns:
        生成的JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, str]]:
    """
    解码JWT访问令牌
    
    Args:
        token: 要解码的JWT令牌
        
    Returns:
        解码后的数据，如果令牌无效则返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
