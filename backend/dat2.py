from initial.config import get_embedding_config

try:
    config = get_embedding_config()
    print(f"API配置: {config}")
                
    # 测试API连接
    import requests
    test_response = requests.post(
        config["api_url"],
        headers={"Authorization": f"Bearer {config['api_key']}"},
        json={"input": ["test"], "model": config["model"]}
        )
    print(f"API测试状态码: {test_response.status_code}")
except Exception as e:
    print(f"配置错误: {e}")
