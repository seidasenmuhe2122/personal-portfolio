import os, requests

def send_telegram_message(text, chat_id=None, token=None, photo_url=None):
    token=token or os.getenv('TELEGRAM_BOT_TOKEN'); chat_id=chat_id or os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return {'ok':False,'error':'TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not configured'}
    base=f'https://api.telegram.org/bot{token}'
    if photo_url:
        r=requests.post(base+'/sendPhoto',json={'chat_id':chat_id,'photo':photo_url,'caption':text[:1024]},timeout=20)
    else:
        r=requests.post(base+'/sendMessage',json={'chat_id':chat_id,'text':text[:4096],'disable_web_page_preview':False},timeout=20)
    data=r.json(); return data

def github_repo(repo, token=None):
    token=token or os.getenv('GITHUB_TOKEN')
    headers={'Accept':'application/vnd.github+json'}
    if token: headers['Authorization']=f'Bearer {token}'
    r=requests.get(f'https://api.github.com/repos/{repo}',headers=headers,timeout=20)
    return r.json()
