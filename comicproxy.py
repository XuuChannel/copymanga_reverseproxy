#桀桀桀我又来写大便了
#能凑活用的半成品 是否继续写看心情
#我们懒狗从来不写错误处理和类型限制
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,FileResponse
import os,requests,json,re
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import binascii

#aes解密
def adecrypt(key, iv, ciphertext):
    return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext),AES.block_size)

#html爬取
def get_webpage_content(url):
    errstart = """
<!DOCTYPE html>
<html>
<head>
    <title>错误页面</title>
</head>
<body>
    <h1>抱歉，出现了错误。</h1>
    <p>"""
    errend="""</p>
</body>
</html>
"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return errstart+str(response)+errend
    except requests.exceptions.RequestException as e:
        return errstart+str(e)+errend
    
#在页面的footer中插入html标签
def insert_into_body(html_content, html_label):
    return html_content.split('<div class="footer">')[0]+'<div class="footer">'+html_label+html_content.split('<div class="footer">')[1]

app = FastAPI()

#一些画蛇添足的基本网页服务

@app.get("/favicon.ico",response_class=FileResponse)
def favreturn():
    return FileResponse("./favicon.png")

@app.get("/lib/{filename}",response_class=FileResponse)
def vfreturn(filename:str):
    return FileResponse("./lib/"+filename)

@app.get("/url")
def geturl(request:Request):
    domain = request.base_url.hostname
    return {"domain": domain}

#ENDOF 基本网页服务
#漫画代理相关

#两个地址按需切换
comicurl_oversea = "https://copymanga.tv"
comicurl = "https://mangacopy.com"

#缓存首页内容 搜索页也可以缓存但是懒得写
mangamainpage = get_webpage_content(comicurl)

#首页
@app.get("/",response_class=HTMLResponse)
def comicsresponse():
    return mangamainpage

#漫画详情
@app.get("/comic/{path}",response_class=HTMLResponse)
def comicdetail(path:str):
    global comicurl
    return get_webpage_content(comicurl+"/comic/"+path)

#漫画章节详情 懒得解密了
@app.get("/comicdetail/{path}/chapters",response_class=HTMLResponse)
def comicchapter(path:str):
    global comicurl
    return get_webpage_content(comicurl+"/comicdetail/"+path+"/chapters")

#漫画章节阅读 改写html页面添加下载按钮
@app.get("/comic/{path}/chapter/{id}",response_class=HTMLResponse)
def comiccontent(path:str,id:str):
    global comicurl
    content = get_webpage_content(comicurl+"/comic/"+path+"/chapter/"+id)
    imgkey = re.findall(r'<div\s+class="imageData"[^>]*\s+contentKey="([^"]*)"',content)[0]
    return insert_into_body(content,'<div class="comicContent-prev index"><a href="/decoder?content='+imgkey+'">下载</a></div>')

#搜索页面
@app.get("/search",response_class=HTMLResponse)
def comicsearch(q:str,request:Request):
    global comicurl
    domain = request.base_url.hostname
    port = request.base_url.port
    return get_webpage_content(comicurl+"/search?q="+q).replace("API_URL","'http://"+domain+":"+str(port)+"'")
    #未开启https的临时解决方案 开启后将replace去掉即可

#藏匿于阅读器和目录html中的加密数据通过url参数传递解密 返回json
@app.get("/decoder")
def decoder(content:str):
    return json.loads(adecrypt(b"xxxmanga.woo.key",content[0:16].encode("utf8"),binascii.unhexlify(content[16:])).decode("utf-8"))

#搜索api 返回json
@app.get("/api/kb/web/{searchtxt}/comics")
def comicsearchapi(searchtxt:str,offset:int,platform:int,limit:int,q:str):
    global comicurl
    offset=str(offset)
    platform=str(platform)
    limit=str(limit)
    return json.loads(get_webpage_content(comicurl+"/api/kb/web/"+searchtxt+"/comics?offset="+offset+"&platform="+platform+"&limit="+limit+"&q="+q+"&q_type="))

#ENDOF 漫画代理相关

if __name__ == "__main__":
    #启动服务器
    os.system("uvicorn web:app --reload --host 0.0.0.0")
