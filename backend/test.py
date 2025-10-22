# from openai import OpenAI
# client = OpenAI(api_key="empty", base_url="http://172.27.221.3:12000/v1", timeout=10000)
# response = client.chat.completions.create(
#     model="Qwen3-14B",
#     messages=[
#                 {"role": "system", "content": "你是一个专业的SQL生成助手，根据用户的需求和提供的数据库信息生成准确的SQL查询语句。"},
#                 {"role": "user", "content": "hi"}
#             ]
#     )
# print(response)


# import os
# from volcenginesdkarkruntime import Ark

# client = Ark(
#     api_key="xxxxxxxxxxxxxxxxxxxxxxxxx
# ",
#     base_url="https://ark.cn-beijing.volces.com/api/v3/embeddings"
# )
# response = client.embeddings.create(
#     model="doubao-embedding-text-240715",
#     input="Function Calling 是一种将大模型与外部工具和 API 相连的关键功能",
#     encoding_format="float"  
# )
# # 打印结果
# print(f"向量维度: {len(response.data[0].embedding)}")
# print(f"前10维向量: {response.data[0].embedding[:10]}")


import os

from volcenginesdkarkruntime import Ark


client = Ark(api_key="xxxxxxxxxxxxxxxxxxxxxxxxx", base_url="https://ark.cn-beijing.volces.com/api/v3/embeddings")

resp = client.embeddings.create(
    model="doubao-embedding-text-240715",
    input=[
        " 天很蓝",
        "海很深",
    ],
    encoding_format="float",
)
print(resp)