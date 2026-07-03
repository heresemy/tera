from flask import Flask, jsonify, request
import requests
import re
import json
from urllib.parse import urlparse

app = Flask(__name__)

def extract_terabox_id(url):
    """Terabox URL से ID निकालें"""
    # पैटर्न: https://www.terabox.tech/xxxxx
    pattern = r'terabox\.tech/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    # अगर सीधा ID दिया गया हो
    if len(url) == 16 and url.isalnum():
        return url
    
    return None

def fetch_terabox_data(video_id):
    """Terabox API से डेटा लाएं"""
    try:
        # पहला API - डेटा लाने के लिए
        api_url = f"https://wholly-api.skinnyrunner.com/get/website-data.php?get_html=https://www.terabox.tech/api/yttera?id={video_id}"
        
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('response'):
            return None
            
        video_data = data['response'][0]
        
        # स्ट्रीमिंग URL बनाएं
        stream_url = f"https://apis.forn.fun/tera/data.php?id={video_id}"
        
        return {
            'success': True,
            'video': {
                'id': video_id,
                'title': video_data.get('title', 'Unknown Title'),
                'thumbnail': video_data.get('thumbnail', ''),
                'stream_url': stream_url,
                'download_urls': {
                    'fast': video_data.get('resolutions', {}).get('Fast Download', ''),
                    'hd': video_data.get('resolutions', {}).get('HD Video', '')
                },
                'duration': video_data.get('duration', ''),
                'uploader': video_data.get('uploader', '')
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Invalid response: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

@app.route('/', methods=['GET'])
def home():
    """API होम पेज"""
    return jsonify({
        'name': 'Terabox Video API',
        'version': '1.0.0',
        'endpoints': {
            '/video': 'GET - Get video info (use ?url=TERABOX_URL)',
            '/video/<id>': 'GET - Get video info by ID',
            '/health': 'GET - Health check'
        },
        'example': 'https://your-api.vercel.app/video?url=https://www.terabox.tech/xxxxx'
    })

@app.route('/health', methods=['GET'])
def health():
    """हेल्थ चेक एंडपॉइंट"""
    return jsonify({
        'status': 'healthy',
        'message': 'Terabox API is running'
    })

@app.route('/video', methods=['GET'])
def get_video():
    """URL से वीडियो डेटा लाएं"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'success': False,
            'error': 'Missing "url" parameter'
        }), 400
    
    # ID निकालें
    video_id = extract_terabox_id(url)
    
    if not video_id:
        return jsonify({
            'success': False,
            'error': 'Invalid Terabox URL'
        }), 400
    
    # डेटा फेच करें
    result = fetch_terabox_data(video_id)
    
    if not result.get('success'):
        return jsonify(result), 404
    
    return jsonify(result)

@app.route('/video/<video_id>', methods=['GET'])
def get_video_by_id(video_id):
    """ID से वीडियो डेटा लाएं"""
    result = fetch_terabox_data(video_id)
    
    if not result.get('success'):
        return jsonify(result), 404
    
    return jsonify(result)

@app.route('/stream/<video_id>', methods=['GET'])
def get_stream_url(video_id):
    """सिर्फ स्ट्रीमिंग URL लाएं"""
    stream_url = f"https://apis.forn.fun/tera/data.php?id={video_id}"
    
    return jsonify({
        'success': True,
        'video_id': video_id,
        'stream_url': stream_url
    })

# Vercel के लिए
if __name__ == '__main__':
    app.run(debug=True)

# Vercel handler
def handler(event, context):
    return app
