import openai               
import psycopg2
from psycopg2.extras import DictCursor       
from sshtunnel import SSHTunnelForwarder
GPT_MODEL = "gpt-3.5-turbo-16k-0613"  
EMBEDDING_MODEL = "text-embedding-ada-002"             
MAX_TOKENS = 1024  
  
# OpenAI的API Key  
openai.api_key = '111'   
  
prompt = '焦虑是怎么解决的'  
  
prompt_response = openai.Embedding.create(  
    model=EMBEDDING_MODEL,  
    input=prompt,  
)  
prompt_embedding = prompt_response['data'][0]['embedding']  
  
#ssh
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
#                         user="root",
#                         password="123",
#                         port="5432")  
conn.autocommit = True  
    
  
  
def answer(prompt_doc, prompt):  
    improved_prompt = f"""  
    按下面提供的文档和步骤来回答接下来的问题：  
    (1) 首先，分析文档中的内容，看是否与问题相关  
    (2) 其次，只能用文档中的内容进行回复,越详细越好,并且以markdown格式输出  
    (3) 最后，如果问题与提问不相关，请回复"我会努力学习的"  
  
    文档:  
    \"\"\"  
    {prompt_doc}  
    \"\"\"  
  
    问题: {prompt}  
    """  
    messages = [{"role":"user", "content":improved_prompt}]   
    # print(messages)  
    response = openai.ChatCompletion.create(  
        model=GPT_MODEL,  
        messages=messages,  
        temperature=0.2,  
        max_tokens=MAX_TOKENS  
    )  
  
    print(f"{response['choices'][0]['message']['content']}\n")  
  
similarity_threshold = 0.78  
max_matched_doc_counts = 2  
  
# 通过pgvector过滤出相似度大于一定阈值的文档块  
similarity_search_sql = f'''  
SELECT doc_chunk, 1 - (embedding <=> '{prompt_embedding}') AS similarity 
FROM documents WHERE 1 - (embedding <=> '{prompt_embedding}') > {similarity_threshold} ORDER BY id LIMIT {max_matched_doc_counts};  
'''  
  
cur = conn.cursor(cursor_factory=DictCursor)  
cur.execute(similarity_search_sql)  
matched_docs = cur.fetchall()  
  
prompt_doc = ''  
print(prompt)  
print('Answer: \n')  
for matched_doc in matched_docs:  
    prompt_doc += f"\n---\n{matched_doc['doc_chunk']}"  
  
  
  
answer(prompt_doc,prompt)
