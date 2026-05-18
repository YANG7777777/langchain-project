from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field
from app.dependencies.database import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import bcrypt
import re

router = APIRouter(tags=["Employees"])


class EmployeeResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="员工数据")


class EmployeeListResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="员工列表")


class EmployeeAddRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[str] = Field(None, description="生日，格式: YYYY-MM-DD")
    phone: Optional[str] = Field(None, max_length=20, description="手机")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    dept_code: Optional[str] = Field(None, max_length=50, description="部门编码")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    hire_date: Optional[str] = Field(None, description="入职日期，格式: YYYY-MM-DD")
    confirmation_date: Optional[str] = Field(None, description="转正日期，格式: YYYY-MM-DD")
    status: Optional[int] = Field(None, ge=0, le=1, description="在职状态: 0-离职, 1-在职")
    salary: Optional[int] = Field(None, description="薪资")
    education: Optional[str] = Field(None, max_length=50, description="学历")
    role: Optional[int] = Field(2, ge=0, le=2, description="角色: 0-超管, 1-管理员, 2-员工")


class EmployeeUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[str] = Field(None, description="生日，格式: YYYY-MM-DD")
    phone: Optional[str] = Field(None, max_length=20, description="手机")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    dept_code: Optional[str] = Field(None, max_length=50, description="部门编码")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    hire_date: Optional[str] = Field(None, description="入职日期，格式: YYYY-MM-DD")
    confirmation_date: Optional[str] = Field(None, description="转正日期，格式: YYYY-MM-DD")
    resignation_date: Optional[str] = Field(None, description="离职日期，格式: YYYY-MM-DD")
    status: Optional[int] = Field(None, ge=0, le=1, description="在职状态: 0-离职, 1-在职")
    salary: Optional[int] = Field(None, description="薪资")
    education: Optional[str] = Field(None, max_length=50, description="学历")
    role_id: Optional[int] = Field(None, description="角色ID，关联角色表")


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def get_department_by_code(db: Session, dept_code: Optional[str]) -> Optional[str]:
    if not dept_code:
        return None
    result = db.execute(text("SELECT dept_name FROM departments WHERE dept_code = :dept_code LIMIT 1"), {"dept_code": dept_code})
    record = result.fetchone()
    return record.dept_name if record else None


def chinese_to_pinyin(name: str) -> str:
    """将中文姓名转换为拼音（简化版）"""
    pinyin_map = {
        '赵': 'zhao', '钱': 'qian', '孙': 'sun', '李': 'li', '周': 'zhou', '吴': 'wu', '郑': 'zheng', '王': 'wang',
        '冯': 'feng', '陈': 'chen', '褚': 'chu', '卫': 'wei', '蒋': 'jiang', '沈': 'shen', '韩': 'han', '杨': 'yang',
        '朱': 'zhu', '秦': 'qin', '尤': 'you', '许': 'xu', '何': 'he', '吕': 'lv', '施': 'shi', '张': 'zhang',
        '孔': 'kong', '曹': 'cao', '严': 'yan', '华': 'hua', '金': 'jin', '魏': 'wei', '陶': 'tao', '姜': 'jiang',
        '谢': 'xie', '宋': 'song', '庞': 'pang', '董': 'dong', '梁': 'liang', '邓': 'deng', '贾': 'jia', '郭': 'guo',
        '林': 'lin', '罗': 'luo', '高': 'gao', '殷': 'yin', '徐': 'xu', '马': 'ma', '蔡': 'cai', '胡': 'hu',
        '刘': 'liu', '关': 'guan', '张': 'zhang', '赵': 'zhao', '黄': 'huang', '吴': 'wu', '周': 'zhou', '徐': 'xu',
        '孙': 'sun', '马': 'ma', '朱': 'zhu', '胡': 'hu', '林': 'lin', '何': 'he', '郭': 'guo', '罗': 'luo',
        '梁': 'liang', '宋': 'song', '郑': 'zheng', '谢': 'xie', '韩': 'han', '唐': 'tang', '冯': 'feng', '于': 'yu',
        '董': 'dong', '萧': 'xiao', '程': 'cheng', '曹': 'cao', '袁': 'yuan', '邓': 'deng', '许': 'xu', '傅': 'fu',
        '沈': 'shen', '曾': 'zeng', '彭': 'peng', '吕': 'lv', '苏': 'su', '卢': 'lu', '蒋': 'jiang', '蔡': 'cai',
        '贾': 'jia', '丁': 'ding', '魏': 'wei', '薛': 'xue', '叶': 'ye', '阎': 'yan', '余': 'yu', '潘': 'pan',
        '杜': 'du', '戴': 'dai', '夏': 'xia', '钟': 'zhong', '汪': 'wang', '田': 'tian', '任': 'ren', '姜': 'jiang',
        '范': 'fan', '方': 'fang', '石': 'shi', '姚': 'yao', '谭': 'tan', '廖': 'liao', '邹': 'zou', '熊': 'xiong',
        '金': 'jin', '陆': 'lu', '郝': 'hao', '孔': 'kong', '白': 'bai', '崔': 'cui', '康': 'kang', '毛': 'mao',
        '邱': 'qiu', '秦': 'qin', '江': 'jiang', '史': 'shi', '顾': 'gu', '侯': 'hou', '邵': 'shao', '孟': 'meng',
        '龙': 'long', '万': 'wan', '段': 'duan', '雷': 'lei', '钱': 'qian', '汤': 'tang', '尹': 'yin', '易': 'yi',
        '常': 'chang', '武': 'wu', '乔': 'qiao', '贺': 'he', '赖': 'lai', '龚': 'gong', '文': 'wen', '王': 'wang',
        '明': 'ming', '伟': 'wei', '丽': 'li', '芳': 'fang', '强': 'qiang', '军': 'jun', '英': 'ying', '华': 'hua',
        '敏': 'min', '静': 'jing', '磊': 'lei', '勇': 'yong', '艳': 'yan', '杰': 'jie', '娜': 'na', '涛': 'tao',
        '涛': 'tao', '鹏': 'peng', '欣': 'xin', '亮': 'liang', '凯': 'kai', '佳': 'jia', '超': 'chao', '云': 'yun',
        '萍': 'ping', '燕': 'yan', '峰': 'feng', '婷': 'ting', '磊': 'lei', '琳': 'lin', '浩': 'hao', '宇': 'yu',
        '涛': 'tao', '洋': 'yang', '阳': 'yang', '雪': 'xue', '芳': 'fang', '丹': 'dan', '蕾': 'lei', '娜': 'na',
        '佳': 'jia', '琪': 'qi', '琳': 'lin', '婷': 'ting', '雅': 'ya', '琴': 'qin', '静': 'jing', '雯': 'wen',
        '妍': 'yan', '晴': 'qing', '萍': 'ping', '燕': 'yan', '妮': 'ni', '娜': 'na', '蓉': 'rong', '芳': 'fang',
        '婷': 'ting', '慧': 'hui', '敏': 'min', '娜': 'na', '琳': 'lin', '洁': 'jie', '燕': 'yan', '萍': 'ping',
        '霞': 'xia', '芳': 'fang', '婷': 'ting', '娜': 'na', '丽': 'li', '敏': 'min', '燕': 'yan', '琴': 'qin',
        '雪': 'xue', '梅': 'mei', '兰': 'lan', '竹': 'zhu', '菊': 'ju', '桂': 'gui', '花': 'hua', '叶': 'ye',
        '春': 'chun', '夏': 'xia', '秋': 'qiu', '冬': 'dong', '天': 'tian', '日': 'ri', '月': 'yue', '星': 'xing',
        '风': 'feng', '云': 'yun', '雨': 'yu', '雪': 'xue', '雷': 'lei', '电': 'dian', '山': 'shan', '水': 'shui',
        '江': 'jiang', '河': 'he', '湖': 'hu', '海': 'hai', '田': 'tian', '土': 'tu', '火': 'huo', '金': 'jin',
        '木': 'mu', '水': 'shui', '土': 'tu', '人': 'ren', '口': 'kou', '手': 'shou', '足': 'zu', '目': 'mu',
        '耳': 'er', '鼻': 'bi', '舌': 'she', '心': 'xin', '肝': 'gan', '脾': 'pi', '肺': 'fei', '肾': 'shen',
        '头': 'tou', '发': 'fa', '面': 'mian', '眉': 'mei', '眼': 'yan', '鼻': 'bi', '嘴': 'zui', '牙': 'ya',
        '王': 'wang', '李': 'li', '张': 'zhang', '刘': 'liu', '陈': 'chen', '杨': 'yang', '黄': 'huang', '赵': 'zhao',
        '周': 'zhou', '吴': 'wu', '徐': 'xu', '孙': 'sun', '马': 'ma', '朱': 'zhu', '胡': 'hu', '林': 'lin',
        '何': 'he', '郭': 'guo', '罗': 'luo', '高': 'gao', '梁': 'liang', '谢': 'xie', '宋': 'song', '唐': 'tang',
        '许': 'xu', '邓': 'deng', '冯': 'feng', '韩': 'han', '曹': 'cao', '曾': 'zeng', '彭': 'peng', '萧': 'xiao',
        '蔡': 'cai', '潘': 'pan', '田': 'tian', '董': 'dong', '袁': 'yuan', '于': 'yu', '余': 'yu', '叶': 'ye',
        '蒋': 'jiang', '杜': 'du', '苏': 'su', '魏': 'wei', '吕': 'lv', '丁': 'ding', '任': 'ren', '沈': 'shen',
        '姚': 'yao', '卢': 'lu', '傅': 'fu', '钟': 'zhong', '姜': 'jiang', '崔': 'cui', '谭': 'tan', '廖': 'liao',
        '范': 'fan', '汪': 'wang', '陆': 'lu', '金': 'jin', '石': 'shi', '戴': 'dai', '贾': 'jia', '韦': 'wei',
        '夏': 'xia', '邱': 'qiu', '方': 'fang', '侯': 'hou', '邹': 'zou', '熊': 'xiong', '孟': 'meng', '秦': 'qin',
        '白': 'bai', '江': 'jiang', '阎': 'yan', '薛': 'xue', '尹': 'yin', '段': 'duan', '雷': 'lei', '史': 'shi',
        '龙': 'long', '陶': 'tao', '黎': 'li', '贺': 'he', '顾': 'gu', '毛': 'mao', '郝': 'hao', '龚': 'gong',
        '邵': 'shao', '万': 'wan', '钱': 'qian', '严': 'yan', '赖': 'lai', '覃': 'qin', '洪': 'hong', '武': 'wu',
        '莫': 'mo', '孔': 'kong', '汤': 'tang', '向': 'xiang', '常': 'chang', '温': 'wen', '康': 'kang', '施': 'shi',
        '文': 'wen', '牛': 'niu', '樊': 'fan', '葛': 'ge', '邢': 'xing', '安': 'an', '齐': 'qi', '易': 'yi',
        '乔': 'qiao', '伍': 'wu', '庞': 'pang', '颜': 'yan', '倪': 'ni', '庄': 'zhuang', '聂': 'nie', '章': 'zhang',
        '鲁': 'lu', '岳': 'yue', '翟': 'zhai', '殷': 'yin', '詹': 'zhan', '申': 'shen', '欧': 'ou', '耿': 'geng',
        '关': 'guan', '兰': 'lan', '焦': 'jiao', '俞': 'yu', '左': 'zuo', '柳': 'liu', '甘': 'gan', '祝': 'zhu',
        '包': 'bao', '宁': 'ning', '尚': 'shang', '符': 'fu', '舒': 'shu', '阮': 'ruan', '柯': 'ke', '纪': 'ji',
        '梅': 'mei', '童': 'tong', '凌': 'ling', '毕': 'bi', '单': 'shan', '季': 'ji', '霍': 'huo', '涂': 'tu',
        '成': 'cheng', '苗': 'miao', '谷': 'gu', '盛': 'sheng', '曲': 'qu', '翁': 'weng', '冉': 'ran', '骆': 'luo',
        '蓝': 'lan', '路': 'lu', '游': 'you', '辛': 'xin', '靳': 'jin', '管': 'guan', '柴': 'chai', '蒙': 'meng',
        '鲍': 'bao', '华': 'hua', '喻': 'yu', '祁': 'qi', '蒲': 'pu', '房': 'fang', '滕': 'teng', '屈': 'qu',
        '饶': 'rao', '解': 'xie', '牟': 'mu', '艾': 'ai', '尤': 'you', '阳': 'yang', '时': 'shi', '穆': 'mu',
        '农': 'nong', '司': 'si', '卓': 'zhuo', '古': 'gu', '吉': 'ji', '缪': 'miao', '简': 'jian', '车': 'che',
        '项': 'xiang', '连': 'lian', '芦': 'lu', '麦': 'mai', '褚': 'chu', '娄': 'lou', '窦': 'dou', '戚': 'qi',
        '岑': 'cen', '景': 'jing', '党': 'dang', '宫': 'gong', '费': 'fei', '卜': 'bu', '冷': 'leng', '晏': 'yan',
        '席': 'xi', '卫': 'wei', '米': 'mi', '柏': 'bai', '宗': 'zong', '翟': 'zhai', '桂': 'gui', '全': 'quan',
        '佟': 'tong', '应': 'ying', '臧': 'zang', '闵': 'min', '苟': 'gou', '邬': 'wu', '边': 'bian', '卞': 'bian',
        '姬': 'ji', '师': 'shi', '和': 'he', '仇': 'qiu', '栾': 'luan', '隋': 'sui', '商': 'shang', '刁': 'diao',
        '沙': 'sha', '荣': 'rong', '巫': 'wu', '寇': 'kou', '桑': 'sang', '郎': 'lang', '甄': 'zhen', '丛': 'cong',
        '仲': 'zhong', '虞': 'yu', '敖': 'ao', '巩': 'gong', '明': 'ming', '佘': 'she', '池': 'chi', '查': 'zha',
        '麻': 'ma', '苑': 'yuan', '迟': 'chi', '邝': 'kuang', '官': 'guan', '封': 'feng', '谈': 'tan', '匡': 'kuang',
        '鞠': 'ju', '惠': 'hui', '荆': 'jing', '乐': 'le', '冀': 'ji', '郁': 'yu', '胥': 'xu', '南': 'nan',
        '班': 'ban', '储': 'chu', '原': 'yuan', '栗': 'li', '燕': 'yan', '楚': 'chu', '鄢': 'yan', '劳': 'lao',
        '谌': 'chen', '奚': 'xi', '皮': 'pi', '粟': 'su', '冼': 'xian', '蔺': 'lin', '楼': 'lou', '盘': 'pan',
        '满': 'man', '闻': 'wen', '位': 'wei', '厉': 'li', '伊': 'yi', '仇': 'qiu', '甘': 'gan', '牟': 'mu',
        '艾': 'ai', '阳': 'yang', '詹': 'zhan', '申': 'shen', '滕': 'teng', '屈': 'qu', '饶': 'rao', '解': 'xie',
        '牟': 'mu', '艾': 'ai', '尤': 'you', '阳': 'yang', '时': 'shi', '穆': 'mu', '农': 'nong', '司': 'si',
        '卓': 'zhuo', '古': 'gu', '吉': 'ji', '缪': 'miao', '简': 'jian', '车': 'che', '项': 'xiang', '连': 'lian',
        '芦': 'lu', '麦': 'mai', '褚': 'chu', '娄': 'lou', '窦': 'dou', '戚': 'qi', '岑': 'cen', '景': 'jing',
        '党': 'dang', '宫': 'gong', '费': 'fei', '卜': 'bu', '冷': 'leng', '晏': 'yan', '席': 'xi', '卫': 'wei',
        '米': 'mi', '柏': 'bai', '宗': 'zong', '翟': 'zhai', '桂': 'gui', '全': 'quan', '佟': 'tong', '应': 'ying',
        '臧': 'zang', '闵': 'min', '苟': 'gou', '邬': 'wu', '边': 'bian', '卞': 'bian', '姬': 'ji', '师': 'shi',
        '和': 'he', '仇': 'qiu', '栾': 'luan', '隋': 'sui', '商': 'shang', '刁': 'diao', '沙': 'sha', '荣': 'rong',
        '巫': 'wu', '寇': 'kou', '桑': 'sang', '郎': 'lang', '甄': 'zhen', '丛': 'cong', '仲': 'zhong', '虞': 'yu',
        '敖': 'ao', '巩': 'gong', '明': 'ming', '佘': 'she', '池': 'chi', '查': 'zha', '麻': 'ma', '苑': 'yuan',
        '迟': 'chi', '邝': 'kuang', '官': 'guan', '封': 'feng', '谈': 'tan', '匡': 'kuang', '鞠': 'ju', '惠': 'hui',
        '荆': 'jing', '乐': 'le', '冀': 'ji', '郁': 'yu', '胥': 'xu', '南': 'nan', '班': 'ban', '储': 'chu',
        '原': 'yuan', '栗': 'li', '燕': 'yan', '楚': 'chu', '鄢': 'yan', '劳': 'lao', '谌': 'chen', '奚': 'xi',
        '皮': 'pi', '粟': 'su', '冼': 'xian', '蔺': 'lin', '楼': 'lou', '盘': 'pan', '满': 'man', '闻': 'wen',
        '位': 'wei', '厉': 'li', '伊': 'yi', '仇': 'qiu', '甘': 'gan', '牟': 'mu', '艾': 'ai', '阳': 'yang',
        '明': 'ming', '伟': 'wei', '丽': 'li', '强': 'qiang', '军': 'jun', '勇': 'yong', '杰': 'jie', '磊': 'lei',
        '涛': 'tao', '鹏': 'peng', '超': 'chao', '亮': 'liang', '凯': 'kai', '鑫': 'xin', '欣': 'xin', '浩': 'hao',
        '宇': 'yu', '洋': 'yang', '阳': 'yang', '雪': 'xue', '婷': 'ting', '琳': 'lin', '静': 'jing', '雅': 'ya',
        '琴': 'qin', '雯': 'wen', '妍': 'yan', '晴': 'qing', '萍': 'ping', '燕': 'yan', '妮': 'ni', '娜': 'na',
        '蓉': 'rong', '洁': 'jie', '慧': 'hui', '敏': 'min', '芳': 'fang', '丹': 'dan', '蕾': 'lei', '梅': 'mei',
        '兰': 'lan', '竹': 'zhu', '菊': 'ju', '桂': 'gui', '花': 'hua', '叶': 'ye', '春': 'chun', '夏': 'xia',
        '秋': 'qiu', '冬': 'dong', '天': 'tian', '日': 'ri', '月': 'yue', '星': 'xing', '风': 'feng', '云': 'yun',
        '雨': 'yu', '雷': 'lei', '电': 'dian', '山': 'shan', '水': 'shui', '江': 'jiang', '河': 'he', '湖': 'hu',
        '海': 'hai', '田': 'tian', '土': 'tu', '火': 'huo', '金': 'jin', '木': 'mu', '人': 'ren', '口': 'kou',
        '手': 'shou', '足': 'zu', '目': 'mu', '耳': 'er', '鼻': 'bi', '舌': 'she', '心': 'xin', '肝': 'gan',
        '脾': 'pi', '肺': 'fei', '肾': 'shen', '头': 'tou', '发': 'fa', '面': 'mian', '眉': 'mei', '眼': 'yan',
        '嘴': 'zui', '牙': 'ya', '王': 'wang', '李': 'li', '张': 'zhang', '刘': 'liu', '陈': 'chen', '杨': 'yang',
        '黄': 'huang', '赵': 'zhao', '周': 'zhou', '吴': 'wu', '徐': 'xu', '孙': 'sun', '马': 'ma', '朱': 'zhu',
        '胡': 'hu', '林': 'lin', '何': 'he', '郭': 'guo', '罗': 'luo', '高': 'gao', '梁': 'liang', '谢': 'xie',
        '宋': 'song', '唐': 'tang', '许': 'xu', '邓': 'deng', '冯': 'feng', '韩': 'han', '曹': 'cao', '曾': 'zeng',
        '彭': 'peng', '萧': 'xiao', '蔡': 'cai', '潘': 'pan', '田': 'tian', '董': 'dong', '袁': 'yuan', '于': 'yu',
        '余': 'yu', '叶': 'ye', '蒋': 'jiang', '杜': 'du', '苏': 'su', '魏': 'wei', '吕': 'lv', '丁': 'ding',
        '任': 'ren', '沈': 'shen', '姚': 'yao', '卢': 'lu', '傅': 'fu', '钟': 'zhong', '姜': 'jiang', '崔': 'cui',
        '谭': 'tan', '廖': 'liao', '范': 'fan', '汪': 'wang', '陆': 'lu', '金': 'jin', '石': 'shi', '戴': 'dai',
        '贾': 'jia', '韦': 'wei', '夏': 'xia', '邱': 'qiu', '方': 'fang', '侯': 'hou', '邹': 'zou', '熊': 'xiong',
        '孟': 'meng', '秦': 'qin', '白': 'bai', '江': 'jiang', '阎': 'yan', '薛': 'xue', '尹': 'yin', '段': 'duan',
        '雷': 'lei', '史': 'shi', '龙': 'long', '陶': 'tao', '黎': 'li', '贺': 'he', '顾': 'gu', '毛': 'mao',
        '郝': 'hao', '龚': 'gong', '邵': 'shao', '万': 'wan', '钱': 'qian', '严': 'yan', '赖': 'lai', '覃': 'qin',
        '洪': 'hong', '武': 'wu', '莫': 'mo', '孔': 'kong', '汤': 'tang', '向': 'xiang', '常': 'chang', '温': 'wen',
        '康': 'kang', '施': 'shi', '文': 'wen', '牛': 'niu', '樊': 'fan', '葛': 'ge', '邢': 'xing', '安': 'an',
        '齐': 'qi', '易': 'yi', '乔': 'qiao', '伍': 'wu', '庞': 'pang', '颜': 'yan', '倪': 'ni', '庄': 'zhuang',
        '聂': 'nie', '章': 'zhang', '鲁': 'lu', '岳': 'yue', '翟': 'zhai', '殷': 'yin', '詹': 'zhan', '申': 'shen',
        '欧': 'ou', '耿': 'geng', '关': 'guan', '兰': 'lan', '焦': 'jiao', '俞': 'yu', '左': 'zuo', '柳': 'liu',
        '甘': 'gan', '祝': 'zhu', '包': 'bao', '宁': 'ning', '尚': 'shang', '符': 'fu', '舒': 'shu', '阮': 'ruan',
        '柯': 'ke', '纪': 'ji', '梅': 'mei', '童': 'tong', '凌': 'ling', '毕': 'bi', '单': 'shan', '季': 'ji',
        '霍': 'huo', '涂': 'tu', '成': 'cheng', '苗': 'miao', '谷': 'gu', '盛': 'sheng', '曲': 'qu', '翁': 'weng',
        '冉': 'ran', '骆': 'luo', '蓝': 'lan', '路': 'lu', '游': 'you', '辛': 'xin', '靳': 'jin', '管': 'guan',
        '柴': 'chai', '蒙': 'meng', '鲍': 'bao', '华': 'hua', '喻': 'yu', '祁': 'qi', '蒲': 'pu', '房': 'fang',
        '滕': 'teng', '屈': 'qu', '饶': 'rao', '解': 'xie', '牟': 'mu', '艾': 'ai', '尤': 'you', '阳': 'yang',
        '时': 'shi', '穆': 'mu', '农': 'nong', '司': 'si', '卓': 'zhuo', '古': 'gu', '吉': 'ji', '缪': 'miao',
        '简': 'jian', '车': 'che', '项': 'xiang', '连': 'lian', '芦': 'lu', '麦': 'mai', '褚': 'chu', '娄': 'lou',
        '窦': 'dou', '戚': 'qi', '岑': 'cen', '景': 'jing', '党': 'dang', '宫': 'gong', '费': 'fei', '卜': 'bu',
        '冷': 'leng', '晏': 'yan', '席': 'xi', '卫': 'wei', '米': 'mi', '柏': 'bai', '宗': 'zong', '翟': 'zhai',
        '桂': 'gui', '全': 'quan', '佟': 'tong', '应': 'ying', '臧': 'zang', '闵': 'min', '苟': 'gou', '邬': 'wu',
        '边': 'bian', '卞': 'bian', '姬': 'ji', '师': 'shi', '和': 'he', '仇': 'qiu', '栾': 'luan', '隋': 'sui',
        '商': 'shang', '刁': 'diao', '沙': 'sha', '荣': 'rong', '巫': 'wu', '寇': 'kou', '桑': 'sang', '郎': 'lang',
        '甄': 'zhen', '丛': 'cong', '仲': 'zhong', '虞': 'yu', '敖': 'ao', '巩': 'gong', '明': 'ming', '佘': 'she',
        '池': 'chi', '查': 'zha', '麻': 'ma', '苑': 'yuan', '迟': 'chi', '邝': 'kuang', '官': 'guan', '封': 'feng',
        '谈': 'tan', '匡': 'kuang', '鞠': 'ju', '惠': 'hui', '荆': 'jing', '乐': 'le', '冀': 'ji', '郁': 'yu',
        '胥': 'xu', '南': 'nan', '班': 'ban', '储': 'chu', '原': 'yuan', '栗': 'li', '燕': 'yan', '楚': 'chu',
        '鄢': 'yan', '劳': 'lao', '谌': 'chen', '奚': 'xi', '皮': 'pi', '粟': 'su', '冼': 'xian', '蔺': 'lin',
        '楼': 'lou', '盘': 'pan', '满': 'man', '闻': 'wen', '位': 'wei', '厉': 'li', '伊': 'yi', '仇': 'qiu',
        '甘': 'gan', '牟': 'mu', '艾': 'ai', '阳': 'yang', '詹': 'zhan', '申': 'shen', '滕': 'teng', '屈': 'qu',
        '饶': 'rao', '解': 'xie', '牟': 'mu', '艾': 'ai', '尤': 'you', '阳': 'yang', '时': 'shi', '穆': 'mu',
        '农': 'nong', '司': 'si', '卓': 'zhuo', '古': 'gu', '吉': 'ji', '缪': 'miao', '简': 'jian', '车': 'che',
        '项': 'xiang', '连': 'lian', '芦': 'lu', '麦': 'mai', '褚': 'chu', '娄': 'lou', '窦': 'dou', '戚': 'qi',
        '岑': 'cen', '景': 'jing', '党': 'dang', '宫': 'gong', '费': 'fei', '卜': 'bu', '冷': 'leng', '晏': 'yan',
        '席': 'xi', '卫': 'wei', '米': 'mi', '柏': 'bai', '宗': 'zong', '翟': 'zhai', '桂': 'gui', '全': 'quan',
        '佟': 'tong', '应': 'ying', '臧': 'zang', '闵': 'min', '苟': 'gou', '邬': 'wu', '边': 'bian', '卞': 'bian',
        '姬': 'ji', '师': 'shi', '和': 'he', '仇': 'qiu', '栾': 'luan', '隋': 'sui', '商': 'shang', '刁': 'diao',
        '沙': 'sha', '荣': 'rong', '巫': 'wu', '寇': 'kou', '桑': 'sang', '郎': 'lang', '甄': 'zhen', '丛': 'cong',
        '仲': 'zhong', '虞': 'yu', '敖': 'ao', '巩': 'gong', '明': 'ming', '佘': 'she', '池': 'chi', '查': 'zha',
        '麻': 'ma', '苑': 'yuan', '迟': 'chi', '邝': 'kuang', '官': 'guan', '封': 'feng', '谈': 'tan', '匡': 'kuang',
        '鞠': 'ju', '惠': 'hui', '荆': 'jing', '乐': 'le', '冀': 'ji', '郁': 'yu', '胥': 'xu', '南': 'nan',
        '班': 'ban', '储': 'chu', '原': 'yuan', '栗': 'li', '燕': 'yan', '楚': 'chu', '鄢': 'yan', '劳': 'lao',
        '谌': 'chen', '奚': 'xi', '皮': 'pi', '粟': 'su', '冼': 'xian', '蔺': 'lin', '楼': 'lou', '盘': 'pan',
        '满': 'man', '闻': 'wen', '位': 'wei', '厉': 'li', '伊': 'yi', '仇': 'qiu', '甘': 'gan', '牟': 'mu',
        '艾': 'ai', '阳': 'yang', '亮': 'liang', '军': 'jun', '伟': 'wei', '强': 'qiang', '杰': 'jie', '勇': 'yong',
        '涛': 'tao', '鹏': 'peng', '超': 'chao', '鑫': 'xin', '欣': 'xin', '浩': 'hao', '宇': 'yu', '洋': 'yang',
        '雪': 'xue', '婷': 'ting', '琳': 'lin', '静': 'jing', '雅': 'ya', '琴': 'qin', '雯': 'wen', '妍': 'yan',
        '晴': 'qing', '萍': 'ping', '妮': 'ni', '娜': 'na', '蓉': 'rong', '洁': 'jie', '慧': 'hui', '敏': 'min',
        '芳': 'fang', '丹': 'dan', '蕾': 'lei', '梅': 'mei', '兰': 'lan', '竹': 'zhu', '菊': 'ju', '桂': 'gui',
        '花': 'hua', '叶': 'ye', '春': 'chun', '夏': 'xia', '秋': 'qiu', '冬': 'dong', '天': 'tian', '日': 'ri',
        '月': 'yue', '星': 'xing', '风': 'feng', '云': 'yun', '雨': 'yu', '雷': 'lei', '电': 'dian', '山': 'shan',
        '水': 'shui', '江': 'jiang', '河': 'he', '湖': 'hu', '海': 'hai', '田': 'tian', '土': 'tu', '火': 'huo',
        '金': 'jin', '木': 'mu', '人': 'ren', '口': 'kou', '手': 'shou', '足': 'zu', '目': 'mu', '耳': 'er',
        '鼻': 'bi', '舌': 'she', '心': 'xin', '肝': 'gan', '脾': 'pi', '肺': 'fei', '肾': 'shen', '头': 'tou',
        '发': 'fa', '面': 'mian', '眉': 'mei', '眼': 'yan', '鼻': 'bi', '嘴': 'zui', '牙': 'ya',
    }
    
    result = []
    for char in name:
        if char in pinyin_map:
            result.append(pinyin_map[char])
        elif re.match(r'[a-zA-Z]', char):
            result.append(char.lower())
        elif re.match(r'[0-9]', char):
            result.append(char)
        else:
            result.append('')
    
    return ''.join(result)


# 获取所有员工（支持按 id 和 name 过滤）
@router.get("/employees/all")
async def employees_all(
    id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        where_clauses = []
        params = {}

        if id is not None:
            where_clauses.append("e.id = :id")
            params["id"] = id

        if name is not None:
            where_clauses.append("e.name LIKE :name")
            params["name"] = f"%{name}%"

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        result = db.execute(
            text(f"""
                SELECT e.id, e.name, e.gender,
                       DATE_FORMAT(e.birthday, '%Y-%m-%d') as birthday,
                       e.phone, e.email, e.dept_code,
                       COALESCE(d.dept_name, e.department_name) as department_name,
                       e.position,
                       DATE_FORMAT(e.hire_date, '%Y-%m-%d') as hire_date,
                       DATE_FORMAT(e.confirmation_date, '%Y-%m-%d') as confirmation_date,
                       DATE_FORMAT(e.resignation_date, '%Y-%m-%d') as resignation_date,
                       e.status, e.salary, e.education,
                       e.creator_id, e.updater_id,
                       DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(e.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at,
                       r.id as role_id,
                       u.role as role_code
                FROM employees e
                LEFT JOIN departments d ON e.dept_code = d.dept_code
                LEFT JOIN users u ON u.email = e.email
                LEFT JOIN roles r ON u.role = r.role_code
                {where_sql}
                ORDER BY e.id ASC
            """),
            params
        )
        records = result.fetchall()

        employee_list = []
        for record in records:
            employee_list.append({
                "id": record.id,
                "name": record.name,
                "gender": record.gender,
                "birthday": record.birthday,
                "phone": record.phone,
                "email": record.email,
                "dept_code": record.dept_code,
                "department_name": record.department_name,
                "position": record.position,
                "hire_date": record.hire_date,
                "confirmation_date": record.confirmation_date,
                "resignation_date": record.resignation_date,
                "status": record.status,
                "salary": record.salary,
                "education": record.education,
                "role_id": record.role_id,
                "role_code": record.role_code,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            })

        return {
            "status": "ok",
            "message": "All employees retrieved successfully",
            "data": {
                "list": employee_list,
                "total": len(employee_list)
            }
        }

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


# 获取员工详情
@router.get("/employees/detail/{id}")
async def employees_detail(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT e.id, e.name, e.gender,
                       DATE_FORMAT(e.birthday, '%Y-%m-%d') as birthday,
                       e.phone, e.email, e.dept_code,
                       COALESCE(d.dept_name, e.department_name) as department_name,
                       e.position,
                       DATE_FORMAT(e.hire_date, '%Y-%m-%d') as hire_date,
                       DATE_FORMAT(e.confirmation_date, '%Y-%m-%d') as confirmation_date,
                       DATE_FORMAT(e.resignation_date, '%Y-%m-%d') as resignation_date,
                       e.status, e.salary, e.education,
                       e.creator_id, e.updater_id,
                       DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(e.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM employees e
                LEFT JOIN departments d ON e.dept_code = d.dept_code
                WHERE e.id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = result.fetchone()

        if record is None:
            return {
                "status": "ok",
                "message": "Employee not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Employee retrieved successfully",
            "data": {
                "id": record.id,
                "name": record.name,
                "gender": record.gender,
                "birthday": record.birthday,
                "phone": record.phone,
                "email": record.email,
                "dept_code": record.dept_code,
                "department_name": record.department_name,
                "position": record.position,
                "hire_date": record.hire_date,
                "confirmation_date": record.confirmation_date,
                "resignation_date": record.resignation_date,
                "status": record.status,
                "salary": record.salary,
                "education": record.education,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            }
        }

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


# 新增员工
@router.post("/employees/add")
async def employees_add(
    request: EmployeeAddRequest,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()

        department_name = get_department_by_code(db, request.dept_code)
        if request.dept_code and not department_name:
            return {
                "status": "error",
                "message": f"Department with code {request.dept_code} not found",
                "data": None
            }

        # 检查邮箱是否已存在（在users表中）
        email_check = db.execute(
            text("SELECT id FROM users WHERE email = :email LIMIT 1"),
            {"email": request.email}
        )
        if email_check.fetchone():
            return {
                "status": "error",
                "message": f"Email '{request.email}' already exists",
                "data": None
            }

        updater_id = creator_id + 1 if creator_id is not None else None

        sql = text("""
            INSERT INTO employees (name, gender, birthday, phone, email, dept_code, department_name, position,
                                  hire_date, confirmation_date, status, salary, education,
                                  creator_id, updater_id, created_at, updated_at)
            VALUES (:name, :gender, :birthday, :phone, :email, :dept_code, :department_name, :position,
                    :hire_date, :confirmation_date, :status, :salary, :education,
                    :creator_id, :updater_id, :created_at, :updated_at)
        """)

        result = db.execute(sql, {
            "name": request.name,
            "gender": request.gender,
            "birthday": parse_date(request.birthday),
            "phone": request.phone,
            "email": request.email,
            "dept_code": request.dept_code,
            "department_name": department_name,
            "position": request.position,
            "hire_date": parse_date(request.hire_date),
            "confirmation_date": parse_date(request.confirmation_date),
            "status": request.status,
            "salary": request.salary,
            "education": request.education,
            "creator_id": creator_id,
            "updater_id": updater_id,
            "created_at": now,
            "updated_at": now
        })
        db.commit()

        new_id = result.lastrowid

        # 自动创建用户账号
        username = chinese_to_pinyin(request.name)
        if not username:
            username = f"user{new_id}"
        
        # 检查用户名是否已存在
        check_result = db.execute(
            text("SELECT id FROM users WHERE username = :username LIMIT 1"),
            {"username": username}
        )
        existing_user = check_result.fetchone()
        
        if not existing_user:
            # 创建密码哈希
            initial_password = "123456"
            truncated_password = initial_password[:72]
            password_hash = bcrypt.hashpw(truncated_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # 获取角色值，默认为2（员工）
            role_value = request.role if request.role is not None else 2
            
            # 插入用户数据
            db.execute(
                text("""
                    INSERT INTO users (username, password, email, role, created_at, updated_at)
                    VALUES (:username, :password, :email, :role, :created_at, :updated_at)
                """),
                {
                    "username": username,
                    "password": password_hash,
                    "email": request.email,
                    "role": role_value,
                    "created_at": now,
                    "updated_at": now
                }
            )
            db.commit()

        return {
            "status": "ok",
            "message": "Employee added successfully",
            "data": {
                "id": new_id,
                "name": request.name,
                "gender": request.gender,
                "birthday": request.birthday,
                "phone": request.phone,
                "email": request.email,
                "dept_code": request.dept_code,
                "department_name": department_name,
                "position": request.position,
                "hire_date": request.hire_date,
                "confirmation_date": request.confirmation_date,
                "status": request.status,
                "salary": request.salary,
                "education": request.education,
                "role": request.role if request.role is not None else 2,
                "creator_id": creator_id,
                "updater_id": updater_id,
                "username": username,
                "initial_password": "123456"
            }
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


# 修改员工
@router.put("/employees/update/{id}")
async def employees_update(
    id: int,
    request: EmployeeUpdateRequest,
    updater_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()

        check_result = db.execute(text("SELECT COUNT(*) as count FROM employees WHERE id = :id"), {"id": id})
        if check_result.fetchone().count == 0:
            return {
                "status": "ok",
                "message": "Employee not found",
                "data": None
            }

        department_name = None
        if request.dept_code is not None:
            department_name = get_department_by_code(db, request.dept_code)
            if request.dept_code and not department_name:
                return {
                    "status": "error",
                    "message": f"Department with code {request.dept_code} not found",
                    "data": None
                }

        update_data = {
            "name": request.name,
            "gender": request.gender,
            "birthday": parse_date(request.birthday) if request.birthday is not None else None,
            "phone": request.phone,
            "email": request.email,
            "dept_code": request.dept_code,
            "department_name": department_name,
            "position": request.position,
            "hire_date": parse_date(request.hire_date) if request.hire_date is not None else None,
            "confirmation_date": parse_date(request.confirmation_date) if request.confirmation_date is not None else None,
            "resignation_date": parse_date(request.resignation_date) if request.resignation_date is not None else None,
            "status": request.status,
            "salary": request.salary,
            "education": request.education,
            "updater_id": updater_id,
            "updated_at": now,
            "id": id
        }

        set_clauses = []
        values = {}
        for key, value in update_data.items():
            if value is not None and key != "id":
                set_clauses.append(f"{key} = :{key}")
                values[key] = value

        if not set_clauses:
            return {
                "status": "ok",
                "message": "No data to update",
                "data": None
            }

        values["id"] = id
        set_str = ", ".join(set_clauses)
        sql = f"UPDATE employees SET {set_str} WHERE id = :id"

        db.execute(text(sql), values)
        db.commit()

        if request.role_id is not None:
            role_result = db.execute(text("SELECT role_code FROM roles WHERE id = :role_id LIMIT 1"), {"role_id": request.role_id})
            role_record = role_result.fetchone()
            if role_record:
                emp_result = db.execute(text("SELECT email FROM employees WHERE id = :id LIMIT 1"), {"id": id})
                emp_record = emp_result.fetchone()
                if emp_record and emp_record.email:
                    db.execute(
                        text("UPDATE users SET role = :role, updated_at = :updated_at WHERE email = :email"),
                        {"role": role_record.role_code, "updated_at": now, "email": emp_record.email}
                    )
                    db.commit()

        select_result = db.execute(
            text("""
                SELECT e.id, e.name, e.gender,
                       DATE_FORMAT(e.birthday, '%Y-%m-%d') as birthday,
                       e.phone, e.email, e.dept_code,
                       COALESCE(d.dept_name, e.department_name) as department_name,
                       e.position,
                       DATE_FORMAT(e.hire_date, '%Y-%m-%d') as hire_date,
                       DATE_FORMAT(e.confirmation_date, '%Y-%m-%d') as confirmation_date,
                       DATE_FORMAT(e.resignation_date, '%Y-%m-%d') as resignation_date,
                       e.status, e.salary, e.education,
                       r.id as role_id,
                       u.role as role_code,
                       e.creator_id, e.updater_id,
                       DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(e.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM employees e
                LEFT JOIN departments d ON e.dept_code = d.dept_code
                LEFT JOIN users u ON u.email = e.email
                LEFT JOIN roles r ON u.role = r.role_code
                WHERE e.id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = select_result.fetchone()

        return {
            "status": "ok",
            "message": "Employee updated successfully",
            "data": {
                "id": record.id,
                "name": record.name,
                "gender": record.gender,
                "birthday": record.birthday,
                "phone": record.phone,
                "email": record.email,
                "dept_code": record.dept_code,
                "department_name": record.department_name,
                "position": record.position,
                "hire_date": record.hire_date,
                "confirmation_date": record.confirmation_date,
                "resignation_date": record.resignation_date,
                "status": record.status,
                "salary": record.salary,
                "education": record.education,
                "role_id": record.role_id,
                "role_code": record.role_code,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            }
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


# 删除员工
@router.delete("/employees/delete/{id}")
async def employees_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("DELETE FROM employees WHERE id = :id"), {"id": id})
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "ok",
                "message": "Employee not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Employee deleted successfully",
            "data": {"id": id}
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }
