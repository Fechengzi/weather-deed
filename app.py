# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
# 允许跨域，方便小程序调用
CORS(app)


# ================= 配置区 =================

# 1. 填入你提供的 API KEY
API_KEY = "ca9ebd0dc8934321b31ff4edec55d3e9"

# 2. 设置 API 地址
# 如果你是免费订阅，必须用这个 devapi
WEATHER_URL = "https://devapi.qweather.com/v7/weather/7d"

# 如果上面的报错提示 Invalid Host，请尝试解开下面这行的注释，用你提供的那个特殊地址试试
# WEATHER_URL = "https://kx6k5mef4f.re.qweatherapi.com/v7/weather/7d" 

# ================= 核心规则库 (穿衣算法) =================
def analyze_clothing(min_temp, max_temp, feels_like, user_origin="south"):
    """
    根据体感温度和用户来源，返回穿衣建议
    """
    # 1. 修正算法：如果是南方人，体感温度自动减 3 度 (宁热勿冷)
    adjusted_feels_like = feels_like
    if user_origin == "south":
        adjusted_feels_like -= 3

    # 2. 规则匹配 (5级表)
    advice = {}
    
    if adjusted_feels_like < -20:
        advice = {
            "level": "Lv5 极寒",
            "title": "极地生存模式",
            "summary": "暴露皮肤10分钟可能冻伤，手机必贴暖宝宝。",
            "items": ["雷锋帽(护耳)", "长款羽绒(过膝)", "两双羊毛袜", "雪地靴", "防风手套"],
            "warning": "红色预警：这不是演习，命要紧！"
        }
    elif -20 <= adjusted_feels_like < -10:
        advice = {
            "level": "Lv4 酷寒",
            "title": "严冬防护模式",
            "summary": "鼻毛会结冰。室内外温差极大，内搭要方便脱。",
            "items": ["厚羽绒服(充绒200g+)", "围巾", "保暖内衣(非纯棉)", "毛线帽"],
            "warning": "橙色预警：千万别穿帆布鞋！"
        }
    elif -10 <= adjusted_feels_like < 0:
        advice = {
            "level": "Lv3 寒冷",
            "title": "常规冬装模式",
            "summary": "只要不刮风体感尚可，但早晚温差大。",
            "items": ["常规羽绒服", "羊毛大衣", "秋裤", "加绒卫衣"],
            "warning": "注意：风大时体感瞬间下降5度。"
        }
    elif 0 <= adjusted_feels_like < 15:
        advice = {
            "level": "Lv2 凉爽",
            "title": "深秋装扮模式",
            "summary": "适合洋葱穿衣法，随时增减。",
            "items": ["冲锋衣/夹克", "薄毛衣", "单层长裤"],
            "warning": "舒适，但早晚记得添衣。"
        }
    else:
        advice = {
            "level": "Lv1 舒适",
            "title": "温暖出行模式",
            "summary": "最舒服的季节，带件薄外套防风即可。",
            "items": ["卫衣/长袖T恤", "薄外套(备用)"],
            "warning": "无需特殊准备，享受旅程。"
        }
        
    return advice

# ================= 接口区 =================
# 1. 在文件顶部增加 GeoAPI 的地址
GEO_URL = "https://geoapi.qweather.com/v2/city/lookup"

@app.route('/get_advice', methods=['GET'])
def get_advice():
    city_name = request.args.get('city', '哈尔滨') 
    # 新增：获取前端传来的日期 (格式如 2023-12-25)
    target_date = request.args.get('date') 
    
    try:
        # 1. 城市转 ID (GeoAPI)
        geo_params = {'location': city_name, 'key': API_KEY}
        geo_res = requests.get(GEO_URL, params=geo_params).json()
        if geo_res.get('code') != '200':
            return jsonify({"error": f"找不到城市: {city_name}"}), 404
        
        top_city = geo_res['location'][0]
        location_id = top_city['id']
        actual_city_name = top_city['name']
        
        # 2. 获取 7 天预报
        weather_params = {'location': location_id, 'key': API_KEY}
        weather_res = requests.get(WEATHER_URL, params=weather_params).json()

        if weather_res.get('code') != '200':
            return jsonify({"error": "获取天气失败"}), 500
            
        # --- 核心逻辑：筛选日期 ---
        selected_day = None
        if target_date:
            # 在 7 天数据中找匹配的那一天
            for day in weather_res['daily']:
                if day['fxDate'] == target_date:
                    selected_day = day
                    break
        
        # 如果没传日期，或者日期超出了 7 天范围，默认给“明天” (daily[1])
        if not selected_day:
            selected_day = weather_res['daily'][1]
        
        # 3. 计算建议
        min_temp = int(selected_day['tempMin'])
        max_temp = int(selected_day['tempMax'])
        feels_like_est = (min_temp + max_temp) / 2 - 2
        
        suggestion = analyze_clothing(min_temp, max_temp, feels_like_est, user_origin="south")
        
        # 4. 返回
        return jsonify({
            "city_name": actual_city_name,
            "target_date": selected_day['fxDate'], # 告诉前端最终定在哪一天
            "location_temp": {
                "min": min_temp,
                "max": max_temp,
                "feels_like_est": int(feels_like_est)
            },
            "advice": suggestion,
            "chart_data": [
                {"date": day['fxDate'][5:], "temp": day['tempMax']} for day in weather_res['daily']
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True, port=5000)