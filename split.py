import openai   
import psycopg2   
import requests   
from bs4 import BeautifulSoup   
from sshtunnel import SSHTunnelForwarder
EMBEDDING_MODEL = "text-embedding-ada-002"   

server = SSHTunnelForwarder(
    # 指定ssh登录的跳转机的address
    ssh_address_or_host=('192.168.195.129', 22),# 分别对应填写上图中的 1 ， 2 位置的参数
    ssh_username='root', # 对应上图的 3 位置的参数，即ssh用户名
    #设置密钥
    ssh_password = '123', # 对应上图的 4 位置的参数，即ssh用户密码
 
    # 设置数据库服务地址及端口
    remote_bind_address=('192.168.195.129' , 5432)) # 要连接的数据库地址、端口号，分别对应下图中的 1,2 位置的参数
server.start()
conn = psycopg2.connect(database = 'ai_emb', # 要连接的数据库名，对应下图的 3 位置的参数
                            user = 'ai',     # 要连接的数据库的用户名，对应下图的 4 位置的参数
                            password = '123', #要连接的数据库的用户密码，对应下图的 5 位置的参数
                            host = '127.0.0.1',    # 此处必须是是127.0.0.1
                            port = server.local_bind_port)

# 连接RDS PostgreSQL数据库   
# conn = psycopg2.connect(database="ai_emb",
#                         host="192.168.195.129",
#                         user="ai",
#                         password="123",
#                         port="5432")   
conn.autocommit = True   
            
# OpenAI的API Key   
openai.api_key = '111'   
   
# 自定义拆分方法（仅为示例）   
def get_text_chunks(content, max_chunk_size):   
    chunks_ = []   
   
    length = len(content)   
    start = 0   
    while start < length:
        end = start + max_chunk_size   
        if end >= length:
            end = length   
   
        chunk_ = content[start:end]   
        chunks_.append(chunk_)   
   
        start = end   
   
    return chunks_   
   
   
# 指定需要拆分的网页   
url = 'https://mp.weixin.qq.com/s/51ZcgCgWVsEUeBBJnw1-Ew'   
   
response = requests.get(url)   
if response.status_code == 200:   
    print(response.text)
    # 解析网页内容   
    web_html_data = response.text   
    soup = BeautifulSoup(web_html_data, 'html.parser')   
    # 获取标题（H1标签）   
    title = soup.find('h1').text.strip()   
    # 发布信息（div标签）   
    description = soup.find('div', class_='rich_media_meta_list').text.strip()   
    # 文章详情（div标签）   
    content = soup.find('div', class_='rich_media_content').text.strip()   
   
    # 拆分并存储   
    chunks = get_text_chunks(content, 500)   
    for chunk in chunks:   
        doc_item = {   
            'title': title,   
            'url': url,   
            'description': description,   
            'doc_chunk': chunk   
        }   
   
        query_embedding_response = openai.Embedding.create(   
            model=EMBEDDING_MODEL,   
            input=chunk,   
        )   
   
        doc_item['embedding'] = query_embedding_response['data'][0]['embedding']   
   
        cur = conn.cursor()   
        insert_query = '''   
        INSERT INTO documents    
            (title, url, description, doc_chunk, embedding) VALUES (%s, %s, %s, %s, %s);   
        '''   
   
        cur.execute(insert_query, (   
            doc_item['title'], doc_item['url'], doc_item['description'], doc_item['doc_chunk'],   
            doc_item['embedding']))   
   
        conn.commit()   
   
else:   
    print('网页加载失败')
